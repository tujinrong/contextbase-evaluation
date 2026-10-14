"""Freeze the independently tested generic dotted/thick/bidirectional label support."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib, json, os, re, shutil, subprocess, sys

report=Path(__file__).resolve().parents[1]
agent=report.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def fresh(path,value):
    if path.exists(): raise FileExistsError(str(path))
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def inventory(root):
    return {p.relative_to(root).as_posix():sha(p) for p in root.rglob('*')
        if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
delivery_path=report/'delivery/core-r17-result.json'
if sha(delivery_path)!='05abe44fef6ad95f37cf9ab704b01a65dec473bac0276a3de96e6bbd918b28fc':
    raise ValueError('Independent r17 result changed')
delivery=load(delivery_path)
log=Path(delivery['suite']['log'])
if sha(log)!=delivery['suite']['logSha256']: raise ValueError('Test log changed')
match=re.search(r'Ran (\d+) tests in ([0-9.]+)s\s+OK',log.read_text(encoding='utf-8-sig'))
if not match or int(match[1])!=404: raise ValueError('404 passing tests required')
source=agent/'src'
files=inventory(source)
previous=load(report/'source-pilot/runtime-code-source-10.json')
if len(files)!=126 or files!=delivery['mainInventory'] or set(files)!=set(previous['files']):
    raise ValueError('Exact tested 126-file membership required')
changed={k for k in files if files[k]!=previous['files'][k]}
if changed!={'contextbase/ai/edge_label_projection.py','contextbase/tests/test_ai_edge_label_projection.py','contextbase/tests/test_ai_rendering.py'}:
    raise ValueError('Unexpected changes since r16')
receipts=[]
for mode,version,name,schema in (
    ('source-only','source-11','source-pilot/runtime-code-source-11.json','source-pilot-frozen-runtime/1'),
    ('training-assisted','assisted-09','training-assisted/runtime-code-assisted-09.json','training-assisted-frozen-runtime/1')):
    destination=agent/'.tmp/20261013-rerun-12h'/mode/'runtime-code'/version/'src'
    if destination.exists() or (report/name).exists(): raise FileExistsError('Fresh runtime required')
    destination.mkdir(parents=True)
    for relative,digest in files.items():
        original,target=source/relative,destination/relative
        if original.is_symlink(): raise ValueError('Linked trusted source refused')
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(original,target)
        if sha(original)!=digest or sha(target)!=digest: raise ValueError('Freeze byte-copy drift')
    names=list(previous['imports'])+['contextbase.ai.rendering','contextbase.ai.edge_label_projection']
    env=dict(os.environ)
    env['PYTHONPATH']=os.pathsep.join(map(str,(destination,agent/'.tmp/20261013-rerun-12h/engine-runtime-deps',agent/'.tmp/session-python-deps')))
    code='import importlib,json;names='+repr(names)+';print(json.dumps({n:importlib.import_module(n).__file__ for n in names}))'
    resolved=subprocess.run([sys.executable,'-X','utf8','-c',code],cwd=destination,env=env,capture_output=True,
        text=True,encoding='utf-8',check=True,timeout=60,creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=='win32' else 0)
    all_imports=json.loads(resolved.stdout)
    if any(not Path(p).resolve().is_relative_to(destination.resolve()) for p in all_imports.values()):
        raise ValueError('Imported code escaped frozen runtime')
    if inventory(source)!=files or inventory(destination)!=files: raise ValueError('Inventory drift during freeze')
    fresh(report/name,{'schema':schema,'createdAt':datetime.now(timezone.utc).isoformat(),'source':str(source),
        'destination':str(destination),'fileCount':126,'files':files,'sourceUnchangedDuringFreeze':True,
        'byteIdenticalCopy':True,'imports':{n:all_imports[n] for n in previous['imports']},
        'renderImports':{n:{'path':all_imports[n],'sha256':sha(Path(all_imports[n]))} for n in names[-2:]},
        'pythonExecutable':sys.executable,'verification':'engine/all-ai-r17-result.json',
        'scope':'trusted agent code only; no original application execution'})
    receipts.append({'path':name,'sha256':sha(report/name)})
created=datetime.now(timezone.utc).isoformat()
result={'schema':'reverse-ai-engine-verification/1','revision':'r17','status':'PASS','createdAt':created,
    'testsPassed':404,'seconds':float(match[2]),'scope':'generic Mermaid lexer support with literal/SVG semantic binding',
    'log':log.relative_to(report).as_posix(),'logSha256':sha(log),'files':files,
    'independentResult':delivery_path.relative_to(report).as_posix(),'independentResultSha256':sha(delivery_path),
    'frozenRuntimeReceipts':receipts,'activeJobRuntimesChanged':False,'businessExpectedAnswersIncluded':False,
    'originalApplicationExecuted':False,'modelWeightTrainingPerformed':False,'specificationQualityVerified':False}
fresh(report/'engine/all-ai-r17-result.json',result)
manifest_path=report/'run-manifest.json'
manifest=load(manifest_path)
fresh(report/'checkpoints/run-manifest-before-r17.json',manifest)
manifest['engineeringValidation']['previousFullSuiteReport']=manifest['engineeringValidation']['report']
manifest['engineeringValidation'].update(report='engine/all-ai-r17-result.json',passedTests=404)
manifest['updatedAt']=created
manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'testsPassed':404,'fileCount':126,'receipts':receipts}))
