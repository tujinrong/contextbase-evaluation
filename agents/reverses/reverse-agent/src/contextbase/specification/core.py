"""P3: deterministic Markdown publication from sealed ContextBase2 ONLY.

No source inventory, language adapter, dynamic plugin or P1 is imported here.
"""
from __future__ import annotations
import html
import re
from pathlib import Path
import shutil
from contextbase.shared.schemas import validate
from contextbase.shared.identities import resolve as resolve_identity
from contextbase.shared.store import safe, read, write, verify, digest, staged, locked


def escape(value):
    return html.escape(str(value).replace('\r\n','\n').replace('\r','\n'),quote=False).replace('|','&#124;').replace('`','&#96;').replace('\n','<br>')


def render(model: dict) -> str:
    text='# '+escape(model['title'])+'\n'
    for section in model['sections']:
        text+='\n## '+escape(section['title'])+'\n\n'
        for b in section['blocks']:
            kind=b['kind']
            if kind=='heading':text+='#'*max(3,min(6,b.get('level',3)))+' '+escape(b['value'])+'\n\n'
            elif kind=='paragraph':text+=html.escape(str(b['value']),quote=False)+'\n\n'
            elif kind=='table':
                rows=b['value'];n=len(rows[0])
                if any(len(r)!=n for r in rows):raise ValueError('Ragged document table')
                text+='| '+' | '.join(map(escape,rows[0]))+' |\n'
                text+='| '+' | '.join('---' for _ in range(n))+' |\n'
                text+=''.join('| '+' | '.join(map(escape,r))+' |\n' for r in rows[1:])+'\n'
            elif kind=='image':
                if re.search(r'^[a-zA-Z][\w+.-]*:',b['path']):raise ValueError('External images prohibited')
                text+='!['+escape(b.get('alt',''))+']('+b['path']+')\n\n'
            elif kind=='code':
                fence='`'*max(3,max((len(m[0])+1 for m in re.finditer(r'`+',b['value'])),default=3))
                text+=fence+'text\n'+b['value']+'\n'+fence+'\n\n'
            else:raise ValueError('Unsupported resolved block: '+str(kind))
    return text


def run(root: Path, *, feature=None, cold=False, config_file='config/project.toml') -> dict:
    root=root.resolve()
    with locked(root,'contextbase-phases'):
        p2=safe(root,'ContextBase/02-detailed');manifest=verify(p2)
        resolved=read(safe(p2,'resolved/catalog.json'))
        validate('resolved',resolved)
        if resolved['foundation_generation']!=manifest['foundation_generation']:raise ValueError('Mixed ContextBase generations')
        feature=resolve_identity(feature,resolved['features'])
        documents=[d for d in resolved['documents'] if not feature or d.get('feature_id')==feature]
        if not documents:raise ValueError('No resolved documents for '+str(feature))
        report=safe(root,'report/specification');report.mkdir(parents=True,exist_ok=True)
        original=read(report/'manifest.json') if (report/'manifest.json').exists() else None
        if feature and (root/'output/md').exists() and not original:
            raise ValueError('Targeted publication requires a managed MD generation; run all P3 first')
        records=[]
        with staged(root,'output/md') as stage:
            if feature and original:
                for item in original['documents']:
                    if item.get('feature_id')!=feature:
                        old=safe(root/'output/md',item['path'])
                        if digest(old.read_bytes())!=item['sha256']:raise ValueError('Edited MD requires reconciliation')
                        dest=safe(stage,item['path']);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(old,dest)
                        records.append(item)
            for d in documents:
                path=safe(stage,d['path'])
                if path.suffix!='.md':raise ValueError('Expected Markdown path')
                value=render(d['model']);write(path,value)
                records.append({'path':d['path'],'feature_id':d.get('feature_id'),'sha256':digest(value),
                                'model_sha256':digest(d['model'])})
            for asset in resolved['assets']:
                source=safe(p2/'resolved',asset['source'])
                if digest(source.read_bytes())!=asset['sha256']:raise ValueError('Resolved asset mismatch')
                target=safe(stage,asset['destination']);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
            listing='# 機能一覧\n\n画面機能と共通処理を分離して記載する。\n\n'
            for d in sorted(records,key=lambda r:r['path']):
                if d['path'].startswith(('基本設計書/','共通/共通仕様書_')):
                    label=next((f['name'] for f in resolved['features'] if f['id']==d.get('feature_id')),Path(d['path']).stem)
                    listing+='- ['+str(d.get('feature_id'))+' '+label+']('+d['path']+')\n'
            write(stage/'機能一覧.md',listing)
            records=[r for r in records if r['path']!='機能一覧.md']
            records.append({'path':'機能一覧.md','feature_id':None,'sha256':digest(listing)})
        result={'schema':'contextbase.specification.v1','status':'verified','count':len(records),'documents':records,
                'detail_generation':manifest['generation'],'source_accessed':False,'dynamic_code_accessed':False,'errors':0}
        write(report/'manifest.json',result);write(report/'validation.json',result)
        return {k:v for k,v in result.items() if k!='documents'}
