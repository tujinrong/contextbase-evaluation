"""Freeze the reviewed node-literal visibility gate after full regression checks."""
from datetime import datetime, timezone
from pathlib import Path
import argparse, hashlib, json, os, re, shutil, subprocess, sys

report=Path(__file__).resolve().parents[1]
agent=report.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def fresh(p,obj):
    if p.exists(): raise FileExistsError(str(p))
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def inventory(root):
    return {p.relative_to(root).as_posix():sha(p) for p in root.rglob('*')
            if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}

parser=argparse.ArgumentParser()
parser.add_argument('--audit',required=True)
parser.add_argument('--audit-sha256',required=True)
args=parser.parse_args()
audit_path=(report/args.audit).resolve()
if not audit_path.is_relative_to((report/'delivery').resolve()) or sha(audit_path)!=args.audit_sha256:
    raise ValueError('Exact independent review is required')
audit=load(audit_path)
if audit.get('schema')!='independent-generic-code-integration-audit/2' or \
   audit.get('status')!='PASS_INDEPENDENT_CODE_ONLY_INTEGRATION_SCOPE' or \
   audit.get('findings')!=[] or audit.get('visibilityGapClosedByExactR06Candidate') is not True or \
   audit.get('inputCodeBeforeAfterUnchanged') is not True:
    raise ValueError('Independent code review has not cleared the integration scope')
source=agent/'src'
files=inventory(source)
previous_path=report/'training-assisted/runtime-code-assisted-10.json'
previous=load(previous_path)
added=set(files)-set(previous['files'])
removed=set(previous['files'])-set(files)
modified={k for k in set(files)&set(previous['files']) if files[k]!=previous['files'][k]}
if len(files)!=128 or removed or added!={'contextbase/ai/node_label_row_gate.py','contextbase/tests/test_ai_node_label_rows.py'} or \
   modified!={'contextbase/ai/rendering.py','contextbase/tests/test_ai_rendering.py'}:
    raise ValueError('The exact reviewed 128-file integration membership is required')
if audit.get('afterInventory',audit.get('currentInventory'))!=files:
    raise ValueError('Reviewed full code inventory differs')
if files['contextbase/ai/node_label_row_gate.py']!='5f9d192749643ba16bc5334eccff175616277befdd28c373ae8524f998f51b68':
    raise ValueError('Reviewed pure gate module differs')
log=report/'engine/all-ai-r19-root-r02.log'
match=re.search(r'Ran (\d+) tests in ([0-9.]+)s\s+OK',log.read_text(encoding='utf-8-sig'))
if not match or int(match[1])!=452: raise ValueError('452 passing regression tests required')
native_path=report/'engine/r19-root-synthetic-native-r01.json'
native=load(native_path)
if sha(native_path)!='c268dc3f1fb2b56fbe03231ff3e2f1041677df483aebd9ab05b59f740f5bb58d':
    raise ValueError('Actually viewed synthetic native record differs')
for item in native['images']:
    if item['actuallyViewed'] is not True or item['blockingFindings'] or sha(Path(item['path']))!=item['sha256']:
        raise ValueError('Actual native image proof has changed')
measure_path=report/'delivery/measure_node_rows_r06.js'
if sha(measure_path)!='9e83c258eca0b0f0a3f0cba3007e8c64945e920286db9ec39bdcf2563689967e':
    raise ValueError('Reviewed effective fill measurement differs')
receipts=[]
for mode,version,name,schema in (
    ('source-only','source-13','source-pilot/runtime-code-source-13.json','source-pilot-frozen-runtime/1'),
    ('training-assisted','assisted-11','training-assisted/runtime-code-assisted-11.json','training-assisted-frozen-runtime/1')):
    destination=agent/'.tmp/20261013-rerun-12h'/mode/'runtime-code'/version/'src'
    if destination.exists() or (report/name).exists(): raise FileExistsError('Fresh runtime required')
    destination.mkdir(parents=True)
    for relative,digest in files.items():
        original,target=source/relative,destination/relative
        if original.is_symlink(): raise ValueError('Linked source refused')
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(original,target)
        if sha(original)!=digest or sha(target)!=digest: raise ValueError('Freeze byte-copy drift')
    render_names=['contextbase.ai.rendering','contextbase.ai.edge_label_projection','contextbase.ai.node_label_row_gate']
    names=list(previous['imports'])+render_names
    env=dict(os.environ)
    env['PYTHONPATH']=os.pathsep.join(map(str,(destination,agent/'.tmp/20261013-rerun-12h/engine-runtime-deps',agent/'.tmp/session-python-deps')))
    code='import importlib,json;names='+repr(names)+';print(json.dumps({n:importlib.import_module(n).__file__ for n in names}))'
    resolved=subprocess.run([sys.executable,'-X','utf8','-c',code],cwd=destination,env=env,capture_output=True,
        text=True,encoding='utf-8',check=True,timeout=60,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=='win32' else 0)
    imports=json.loads(resolved.stdout)
    if any(not Path(p).resolve().is_relative_to(destination.resolve()) for p in imports.values()):
        raise ValueError('Imported code escaped frozen runtime')
    if inventory(source)!=files or inventory(destination)!=files: raise ValueError('Code inventory drift')
    fresh(report/name,{'schema':schema,'createdAt':datetime.now(timezone.utc).isoformat(),'source':str(source),
        'destination':str(destination),'fileCount':128,'files':files,'sourceUnchangedDuringFreeze':True,
        'byteIdenticalCopy':True,'imports':{n:imports[n] for n in previous['imports']},
        'renderImports':{n:{'path':imports[n],'sha256':sha(Path(imports[n]))} for n in render_names},
        'pythonExecutable':sys.executable,'verification':'engine/all-ai-r19-result.json',
        'scope':'trusted agent code only; no original application execution'})
    receipts.append({'path':name,'sha256':sha(report/name)})
created=datetime.now(timezone.utc).isoformat()
result={'schema':'reverse-ai-engine-verification/1','revision':'r19','status':'PASS','createdAt':created,
    'testsPassed':452,'seconds':float(match[2]),'files':files,'log':log.relative_to(report).as_posix(),
    'logSha256':sha(log),'independentCodeReview':audit_path.relative_to(report).as_posix(),
    'independentCodeReviewSha256':sha(audit_path),'rootSyntheticNativeReview':native_path.relative_to(report).as_posix(),
    'rootSyntheticNativeReviewSha256':sha(native_path),'frozenRuntimeReceipts':receipts,
    'preservedFirstRegressionFailure':'engine/all-ai-r19-root-r01.log',
    'scope':'generic public-parser literal binding, whole-token row visibility, and strict-security diagnostic retention',
    'activeJobRuntimesChanged':False,'businessExpectedAnswersIncluded':False,
    'originalApplicationExecuted':False,'modelWeightTrainingPerformed':False,'specificationQualityVerified':False}
fresh(report/'engine/all-ai-r19-result.json',result)
manifest_path=report/'run-manifest.json'
manifest=load(manifest_path)
fresh(report/'checkpoints/run-manifest-before-r19.json',manifest)
manifest['engineeringValidation']['previousFullSuiteReport']=manifest['engineeringValidation']['report']
manifest['engineeringValidation'].update(report='engine/all-ai-r19-result.json',passedTests=452)
manifest['latestProtectedInputVerification']='checkpoints/protected-inputs-07.json'
manifest.pop('protectedInputVerification',None)
manifest['updatedAt']=created
manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'testsPassed':452,'fileCount':128,'receipts':receipts}))
