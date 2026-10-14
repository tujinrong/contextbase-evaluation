"""Freeze generic table readability CSS after the full suite and independent native QA."""
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
code_path=report/'delivery/core-r18-independent-integration-qa.json'
native_path=report/'delivery/core-r18-independent-native-qa.json'
if sha(code_path)!='997e9c4e80e15a16e292eb75b9e265f8148e55f6a4524a1a10b8f9d9f0d16f98' or \
   sha(native_path)!='fcfef577ff3dfd7e176864d85b248b6655dd6219e1750b10e57188c1a4b0c9aa':
    raise ValueError('Independent code/native QA changed')
code,native=load(code_path),load(native_path)
if code['status']!='PASS_CODE_DELTA_ONLY' or native['status']!='PASS_SYNTHETIC_NATIVE_GEOMETRY_ONLY':
    raise ValueError('Independent generic rendering QA required')
for item in native['images']:
    if item['actuallyViewed'] is not True or sha(Path(item['path']))!=item['sha256'] or (item['name']!='table-css-baseline' and item['candidateFindings']):
        raise ValueError('Actual native image verification changed')
log=report/'engine/all-ai-r18-root-r01.log'
match=re.search(r'Ran (\d+) tests in ([0-9.]+)s\s+OK',log.read_text(encoding='utf-8-sig'))
if not match or int(match[1])!=408: raise ValueError('408 passing tests required')
source=agent/'src'
files=inventory(source)
previous=load(report/'source-pilot/runtime-code-source-11.json')
if len(files)!=126 or set(files)!=set(previous['files']): raise ValueError('Exact 126-file membership required')
changed={k for k in files if files[k]!=previous['files'][k]}
if changed!=set(code['modifiedFiles']) or changed!={'contextbase/ai/rendering.py','contextbase/tests/test_ai_rendering.py'}:
    raise ValueError('Unexpected changes since r17')
for relative,item in code['modifiedFiles'].items():
    if previous['files'][relative]!=item['old'] or files[relative]!=item['new']:
        raise ValueError('Tested/reviewed code hash differs')
receipts=[]
for mode,version,name,schema in (
    ('source-only','source-12','source-pilot/runtime-code-source-12.json','source-pilot-frozen-runtime/1'),
    ('training-assisted','assisted-10','training-assisted/runtime-code-assisted-10.json','training-assisted-frozen-runtime/1')):
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
    code_string='import importlib,json;names='+repr(names)+';print(json.dumps({n:importlib.import_module(n).__file__ for n in names}))'
    resolved=subprocess.run([sys.executable,'-X','utf8','-c',code_string],cwd=destination,env=env,capture_output=True,
        text=True,encoding='utf-8',check=True,timeout=60,creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=='win32' else 0)
    all_imports=json.loads(resolved.stdout)
    if any(not Path(p).resolve().is_relative_to(destination.resolve()) for p in all_imports.values()):
        raise ValueError('Imported code escaped frozen runtime')
    if inventory(source)!=files or inventory(destination)!=files: raise ValueError('Inventory drift during freeze')
    fresh(report/name,{'schema':schema,'createdAt':datetime.now(timezone.utc).isoformat(),'source':str(source),
        'destination':str(destination),'fileCount':126,'files':files,'sourceUnchangedDuringFreeze':True,
        'byteIdenticalCopy':True,'imports':{n:all_imports[n] for n in previous['imports']},
        'renderImports':{n:{'path':all_imports[n],'sha256':sha(Path(all_imports[n]))} for n in names[-2:]},
        'pythonExecutable':sys.executable,'verification':'engine/all-ai-r18-result.json',
        'scope':'trusted agent code only; no original application execution'})
    receipts.append({'path':name,'sha256':sha(report/name)})
created=datetime.now(timezone.utc).isoformat()
result={'schema':'reverse-ai-engine-verification/1','revision':'r18','status':'PASS','createdAt':created,
    'testsPassed':408,'seconds':float(match[2]),'scope':'generic marked-table readability without DOM/text/embedded-view changes',
    'log':log.relative_to(report).as_posix(),'logSha256':sha(log),'files':files,
    'independentCodeReview':code_path.relative_to(report).as_posix(),'independentCodeReviewSha256':sha(code_path),
    'independentNativeReview':native_path.relative_to(report).as_posix(),'independentNativeReviewSha256':sha(native_path),
    'frozenRuntimeReceipts':receipts,'activeJobRuntimesChanged':False,'businessExpectedAnswersIncluded':False,
    'originalApplicationExecuted':False,'modelWeightTrainingPerformed':False,'specificationQualityVerified':False}
fresh(report/'engine/all-ai-r18-result.json',result)
manifest_path=report/'run-manifest.json'
manifest=load(manifest_path)
fresh(report/'checkpoints/run-manifest-before-r18.json',manifest)
manifest['engineeringValidation']['previousFullSuiteReport']=manifest['engineeringValidation']['report']
manifest['engineeringValidation'].update(report='engine/all-ai-r18-result.json',passedTests=408)
manifest['updatedAt']=created
manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'testsPassed':408,'fileCount':126,'receipts':receipts}))
