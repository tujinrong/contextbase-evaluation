"""Independent contract gates and a subprocess proof of source-free P3 replay."""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from contextbase.shared.store import safe,read,write,verify,digest,tree_hashes
from contextbase.shared.schemas import validate


def check(root: Path) -> dict:
    root=root.resolve();checks=[]
    def expect(name, condition):
        checks.append({'check':name,'pass':bool(condition)})
    p1=safe(root,'ContextBase/01-foundation');p2=safe(root,'ContextBase/02-detailed')
    b=verify(p1);d=verify(p2)
    expect('P1-P2 generation pinned',d['foundation_generation']==b['generation'])
    expect('source snapshot pinned',d['source_snapshot']==b['snapshot'])
    features=read(p1/'catalogs/features.json');ids={f['id'] for f in features}
    expect('unique foundation IDs',len(ids)==len(features))
    method_ids={m['id'] for m in read(p2/'common/methods.json')}
    database=read(p1/'database/catalog.json')
    expect('DTO/table identities separate',not ({o['id'] for o in database['data_objects']}&{t['id'] for t in database['tables']}))
    catalog=read(p2/'resolved/catalog.json');validate('resolved',catalog)
    doc_paths=[x['path'] for x in catalog['documents']]
    expect('unique document paths',len(doc_paths)==len(set(doc_paths)))
    models={fid:read(p2/f'functions/{fid}/feature.json') for fid in d['feature_ids']}
    for fid,model in models.items():
        validate('feature',model)
        expect(fid+' has foundation',fid in ids)
        expect(fid+' unique items',len(model['items'])==len({i['id'] for i in model['items']}))
        for e in model['events']:
            expect(fid+'/'+e['id']+' method refs',set(e.get('related_method_ids',[])).issubset(method_ids))
            for method in e.get('methods',[]):
                expect(fid+'/'+method['name']+' source dependency',method['path'] in model['dependencies'])
                expect(fid+'/'+method['name']+' ordered steps',[n['line'] for n in method['steps']]==sorted(n['line'] for n in method['steps']))
    from contextbase.itemlist import HEADERS
    from contextbase.shared.identities import resolve as resolve_identity
    from contextbase.detail.semantics import OPS
    for doc in catalog['documents']:
        safe(root/'output/md',doc['path'])
        if doc.get('feature_id'):
            model=models[doc['feature_id']]
            if doc['path'].startswith('基本設計書/'):
                document_text=json.dumps(doc['model'],ensure_ascii=False)
                expect(model['id']+' readable public ID',not re.fullmatch(r'[FC]-[A-F0-9]{10}',model['id']))
                for alias in model.get('aliases',[]):
                    expect(alias+' resolves public ID',resolve_identity(alias,features)==model['id'])
                if model['kind']=='screen' and not model.get('reviewed'):
                    images=[b for section in doc['model']['sections'] for b in section['blocks'] if b['kind']=='image']
                    expected_images=model.get('layout',{}).get('images',[])
                    expect(model['id']+' static screen generated',bool(expected_images))
                    expect(model['id']+' screen images projected',all(b in images for b in expected_images))
                for event in model['events']:
                    for effect in event.get('storage_effects',[]):
                        expect(model['id']+'/'+event['id']+' storage operation projected',
                               effect['store'] in document_text and OPS.get(effect['operation'],effect['operation']) in document_text)
                        expect(model['id']+'/'+event['id']+' storage operation has evidence',bool(effect.get('evidence')))
                        if effect['kind']=='memory':
                            expect(model['id']+' memory is not physical DB',not effect.get('physical_table_verified',False) and 'メモリー' in document_text)
            for section in doc['model']['sections']:
                for block in section['blocks']:
                    if block['kind']=='table' and block['value'][0]==list(HEADERS):
                        rows=block['value'][1:]
                        expect(doc['path']+' item count',len(rows)==len(model['items']))
                        expect(doc['path']+' item order',[r[2] for r in rows]==[i['name'] for i in model['items']])
    result={'status':'pass' if all(c['pass'] for c in checks) else 'fail','checks':checks,
            'checks_count':len(checks),'errors':sum(not c['pass'] for c in checks),
            'scope':'Schema, generation, references, item/screen/storage projection, readable IDs and lexical-order contracts; not full business equivalence.'}
    write(safe(root,'report/two-stage/contracts.json'),result)
    if result['errors']:raise ValueError('Two-stage contract validation failed')
    return result


def source_free_replay(root: Path) -> dict:
    root=root.resolve()
    with tempfile.TemporaryDirectory(prefix='contextbase-source-free-') as tmp:
        target=Path(tmp)
        shutil.copytree(root/'ContextBase/02-detailed',target/'ContextBase/02-detailed')
        # Audit opens as well as asserting no original source/P1/dynamic material was copied.
        script=r'''
import pathlib,sys
root=pathlib.Path(sys.argv[1]).resolve()
forbidden=[pathlib.Path(sys.argv[2]).resolve()/p for p in ('input','src-dynamic','ContextBase/01-foundation')]
def audit(event,args):
    if event=='open' and isinstance(args[0],(str,bytes)):
        p=pathlib.Path(args[0].decode() if isinstance(args[0],bytes) else args[0]).resolve()
        if any(p==x or p.is_relative_to(x) for x in forbidden):
            raise RuntimeError('P3 attempted forbidden read: '+str(p))
sys.addaudithook(audit)
from contextbase.specification.core import run
run(root)
'''
        env={**os.environ,'PYTHONPATH':str(Path(__file__).resolve().parents[2]),'PYTHONUTF8':'1','PYTHONDONTWRITEBYTECODE':'1'}
        proc=subprocess.run([sys.executable,'-c',script,str(target),str(root)],env=env,capture_output=True,text=True,timeout=120)
        if proc.returncode:raise ValueError('Source-free P3 replay failed: '+proc.stderr[-2000:])
        original=tree_hashes(root/'output/md');replayed=tree_hashes(target/'output/md')
        result={'status':'pass' if original==replayed else 'fail','read_input':False,'read_dynamic':False,'read_P1':False,
                'files':len(replayed),'matching_files':sum(original.get(k)==v for k,v in replayed.items()),
                'output_sha256':digest(replayed),'subprocess_exit':proc.returncode}
        write(safe(root,'report/two-stage/source-free-replay.json'),result)
        if result['status']!='pass':raise ValueError('P3 output differs from sealed replay')
        return result


def run(root: Path, *, feature=None,cold=False,config_file='config/project.toml'):
    result=check(root)
    if (root/'output/md').exists():
        from .quality import enforce
        result['quality']=enforce(root)
        result['replay']=source_free_replay(root)
    return {k:v for k,v in result.items() if k!='checks'}
