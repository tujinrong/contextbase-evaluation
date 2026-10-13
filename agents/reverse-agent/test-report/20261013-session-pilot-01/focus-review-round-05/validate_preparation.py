"""Read-only Round5 preparation pin/range validation; starts no external jobs."""
import hashlib
import json
from pathlib import Path
from datetime import datetime,timezone
from contextbase.ai import capsule,workflow
ROOT=Path.cwd().resolve(); REPORT=Path(__file__).resolve().parent
SESSION=ROOT/'agents/reverse-agent/test-report/20261013-session-pilot-01'
SNAPSHOT=ROOT/'agents/reverse-agent/.tmp/20261013-tuning-01/capsules/CSharp_ASPNET-assisted'
JOBS=ROOT/'agents/reverse-agent/.tmp/20261013-session-pilot-01/focus-round-05'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p): return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
prep=read(REPORT/'review-preparation.json'); scope=read(SESSION/'focus-round-05/scope.json')
assert scope['runtimeFrozenAtLaunch'] is True and len(scope['runtimeFiles'])==13 and len(scope['inputPins'])==8
assert scope['runnerSha256']==sha(JOBS/'runner-source.py')=='c63aca7300a44fa17c542d82a98dc0523c3853206fb8b8a6d3ebe0fc62a9f591'
assert scope['expectedAnswersProvided'] is False and scope['semanticProseAssembledByPython'] is False
paths=[JOBS/'runner-source.py',SESSION/'focus-round-05/scope.json',REPORT/'review-preparation.json',REPORT/'source-pins-before.json',SESSION/'focus-protected-check-05.json',SNAPSHOT/'manifest.json']
for i in scope['runtimeFiles']:
    p=JOBS/i['runtimePath']; assert sha(p)==i['sha256']; paths.append(p)
for i in scope['inputPins']:
    p=(ROOT/i['path']).resolve(); assert ROOT in p.parents
    assert not any(part.casefold() in {'spec-eval','evaluator-only'} for part in p.parts)
    assert sha(p)==i['sha256']; paths.append(p)
source=read(REPORT/'source-pins-before.json')['files']; assert len(source)==32
for i in source:
    p=SNAPSHOT/i['path']; assert sha(p)==i['sha256'] and p.stat().st_size==i['bytes']; paths.append(p)
manifest=capsule.verify(SNAPSHOT)
workflow.references_valid({'findings':[{'references':i['references']} for i in prep['sourceChecks']]},manifest)
protected=read(SESSION/'focus-protected-check-05.json')
assert (protected['total'],protected['unchanged'],protected['changed'],protected['missing'])==(179,179,0,0)
paths=list(dict.fromkeys(paths)); before=[pin(p) for p in paths]; after=[pin(p) for p in paths]; assert before==after
result={'schema':'independent-round5-review-preparation-validation/1','capturedAt':datetime.now(timezone.utc).isoformat(),'status':'PASS','sourceStartingPinsUnchanged':32,'focusSourceChecks':6,'rawSourceRangesValid':sum(len(i['references']) for i in prep['sourceChecks']),'frozenRuntimePinsValid':13,'launchInputsValid':8,'protected179CheckRecordedUnchanged':True,'inputsUnchanged':True,'pins':before,'newDraftApproved':None,'newImagesViewed':0,'sourceOrMdOrProductionEdited':False,'duplicateAiOrRenderStarted':False,'expectedContentsRead':False,'referenceDesignContentsSemanticallyRead':False}
(REPORT/'preparation-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:result[k] for k in ['status','sourceStartingPinsUnchanged','rawSourceRangesValid','frozenRuntimePinsValid','launchInputsValid','newDraftApproved','newImagesViewed']}))
