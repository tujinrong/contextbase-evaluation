"""Freeze the tested insert-only edge-label renderer for future jobs."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

report = Path(__file__).resolve().parents[1]
agent = report.parents[1]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
def fresh(path, value):
    if path.exists():
        raise ValueError('Fresh immutable receipt required: '+str(path))
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

delivery_path=report/'delivery/core-r16-result-r02.json'
if sha(delivery_path) != 'ca1fd28c216b6fe60f52f113b7b412631c7d55fb2aa21fed8ba8c9454f23bc44':
    raise ValueError('The final independent full-suite receipt is required')
delivery=load(delivery_path)
log=Path(delivery['suite']['log'])
if sha(log)!=delivery['suite']['logSha256']:
    raise ValueError('Full-suite log drift')
match=re.search(r'Ran (\d+) tests in ([0-9.]+)s\s+OK',log.read_text(encoding='utf-8-sig'))
if not match or int(match[1]) != 394:
    raise ValueError('Full passing 394-test result required')
previous=load(report/'source-pilot/runtime-code-source-09.json')
source=agent/'src'
def inventory(root):
    return {p.relative_to(root).as_posix():sha(p) for p in root.rglob('*')
            if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
files=inventory(source)
new={'contextbase/ai/edge_label_projection.py','contextbase/tests/test_ai_edge_label_projection.py'}
if len(files)!=126 or set(files)-set(previous['files'])!=new or set(previous['files'])-set(files):
    raise ValueError('Exact 126-file inventory with two new trusted files required')
if {k for k in previous['files'] if files[k]!=previous['files'][k]} != {
    'contextbase/ai/rendering.py','contextbase/ai/prompts.py','contextbase/tests/test_ai_rendering.py'}:
    raise ValueError('Unexpected change since the r15 freeze')
if files!=delivery['mainInventory']:
    raise ValueError('Current code differs from the tested independent inventory')
receipts=[]
for mode,version,name,schema in (
    ('source-only','source-10','source-pilot/runtime-code-source-10.json','source-pilot-frozen-runtime/1'),
    ('training-assisted','assisted-08','training-assisted/runtime-code-assisted-08.json','training-assisted-frozen-runtime/1')):
    destination=agent/'.tmp/20261013-rerun-12h'/mode/'runtime-code'/version/'src'
    if destination.exists() or (report/name).exists():
        raise ValueError('Fresh runtime destination required')
    destination.mkdir(parents=True)
    for relative,digest in files.items():
        original,target=source/relative,destination/relative
        if original.is_symlink():
            raise ValueError('Linked trusted code refused')
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(original,target)
        if sha(original)!=digest or sha(target)!=digest:
            raise ValueError('Freeze byte copy drift')
    names=list(previous['imports'])+['contextbase.ai.rendering','contextbase.ai.edge_label_projection']
    environment=dict(os.environ)
    environment['PYTHONPATH']=os.pathsep.join(map(str,(destination,
        agent/'.tmp/20261013-rerun-12h/engine-runtime-deps',agent/'.tmp/session-python-deps')))
    code='import importlib,json;names='+repr(names)+';print(json.dumps({n:importlib.import_module(n).__file__ for n in names}))'
    resolved=subprocess.run([sys.executable,'-X','utf8','-c',code],cwd=destination,env=environment,
        capture_output=True,text=True,encoding='utf-8',check=True,timeout=60,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=='win32' else 0)
    all_imports=json.loads(resolved.stdout)
    if any(not Path(p).resolve().is_relative_to(destination.resolve()) for p in all_imports.values()):
        raise ValueError('Import escaped the frozen runtime')
    if inventory(source)!=files or inventory(destination)!=files:
        raise ValueError('Code changed during freeze')
    imports={n:all_imports[n] for n in previous['imports']}
    render_imports={n:{'path':all_imports[n],'sha256':sha(Path(all_imports[n]))}
        for n in ('contextbase.ai.rendering','contextbase.ai.edge_label_projection')}
    fresh(report/name,{'schema':schema,'createdAt':datetime.now(timezone.utc).isoformat(),
        'source':str(source),'destination':str(destination),'fileCount':len(files),'files':files,
        'sourceUnchangedDuringFreeze':True,'byteIdenticalCopy':True,'imports':imports,
        'renderImports':render_imports,'pythonExecutable':sys.executable,
        'verification':'engine/all-ai-r16-result.json',
        'scope':'full trusted agent source excluding bytecode; not application source'})
    receipts.append({'path':name,'sha256':sha(report/name)})
result={'schema':'reverse-ai-engine-verification/1','revision':'r16','status':'PASS',
    'createdAt':datetime.now(timezone.utc).isoformat(),'testsPassed':394,'seconds':float(match[2]),
    'scope':'full AI regression suite; insert-only edge-label projection bound to original literal text, SVG semantic signatures, and whole visible tokens; all-section original-reference fidelity guidance',
    'log':log.relative_to(report).as_posix(),'logSha256':sha(log),'files':files,
    'independentResult':delivery_path.relative_to(report).as_posix(),
    'independentResultSha256':sha(delivery_path),'frozenRuntimeReceipts':receipts,
    'activeJobRuntimesChanged':False,'businessExpectedAnswersIncluded':False,
    'originalApplicationExecuted':False,'modelWeightTrainingPerformed':False,'specificationQualityVerified':False}
fresh(report/'engine/all-ai-r16-result.json',result)
path=report/'run-manifest.json'
manifest=load(path)
fresh(report/'checkpoints/run-manifest-before-r16.json',manifest)
manifest['engineeringValidation']['previousFullSuiteReport']=manifest['engineeringValidation']['report']
manifest['engineeringValidation'].update(report='engine/all-ai-r16-result.json',passedTests=394)
manifest['updatedAt']=result['createdAt']
path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'testsPassed':394,'filesPerRuntime':126,'importsPerRuntime':len(imports),
    'renderImportPins':len(render_imports),'receipts':receipts}))
