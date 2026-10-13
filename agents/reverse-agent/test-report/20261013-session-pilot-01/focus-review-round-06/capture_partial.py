"""Save truthful partial review evidence exclusively; never manufactures approval."""
from pathlib import Path
import json,hashlib,sys,subprocess
from datetime import datetime,timezone
ROOT=Path(r'D:\開発\contextbase-evaluation').resolve()
REPORT=Path(__file__).resolve().parent
CAP=ROOT/'agents/reverse-agent/.tmp/20261013-tuning-01/capsules/CSharp_ASPNET-assisted'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
name=sys.argv[1]
target=(REPORT/name).resolve();assert target.parent==REPORT
assert not target.exists()
observe=json.loads(subprocess.check_output([sys.executable,'-X','utf8',str(REPORT/'observe_current.py')],text=True,encoding='utf-8'))
pins=read(REPORT/'preparation-validation.json')['pins']
caps=read(REPORT/'capsule-material-pins.json')['files']
source=read(REPORT/'source-pins-before.json')['files']
pin_drift=[p['path'] for p in pins if sha(ROOT/p['path'])!=p['sha256']]
cap_drift=[p['path'] for p in caps if sha(CAP/p['path'])!=p['sha256']]
source_drift=[p['path'] for p in source if sha(CAP/p['path'])!=p['sha256']]
read_records=[{'record':p.name,'sha256':sha(p),'references':read(p)['references']} for p in sorted(REPORT.glob('source-read-*.json'))]
reference_records=[{'record':p.name,'sha256':sha(p),'references':read(p)['references'],'scope':'Authorized design intention; separate from observed source behavior'} for p in sorted(REPORT.glob('reference-read-*.json'))]
viewed_path=REPORT/'viewed-images.jsonl'
viewed=[json.loads(s) for s in viewed_path.read_text(encoding='utf-8').splitlines() if s.strip()] if viewed_path.exists() else []
for batch in sorted(REPORT.glob('viewed-batch-*.json')):
    viewed.extend(read(batch)['images'])
assert len({v['path'] for v in viewed})==len(viewed)
frozen=[{'record':p.name,'sha256':sha(p),'documentId':read(p)['documentId'],'publishedMdSha256':read(p)['publishedMdSha256'],'imagesFrozen':read(p)['imagesFrozen'],'currentPinsMatch':all(sha(ROOT/x['sourcePath'])==x['sha256']==sha(ROOT/x['frozenPath']) for x in read(p)['pins'])} for p in sorted(REPORT.glob('*-frozen-inputs.json')) if '-text-frozen-' not in p.name]
result={'schema':'reverse-independent-source-native-partial-manifest/1','round':6,'savedAt':datetime.now(timezone.utc).isoformat(),'status':'PARTIAL','approval':None,'sourceReviewCompleted':None,'visualReviewCompleted':None,'referenceIntentComparisonCompleted':None,'formalGradingCompleted':None,'imagesActuallyViewed':len(viewed),'viewedImages':viewed,'sourceReadEvidence':read_records,'frozenCompletedInputs':frozen,'currentObservation':observe,'launchPins':len(pins),'launchPinDrift':pin_drift,'source32PinDrift':source_drift,'capsule43source11referencePinDrift':cap_drift,'retainedUnassessedScopes':['Undrawn complete mode combinations','Narrow width','Live HTTP/binder/application/DB/concurrency/cancellation/response delivery','Authorized-reference design intent semantic comparison until separately completed','Formal grading'],'priorApprovalOrImageReused':False,'duplicateAiOrRenderStarted':False,'sourceOrMdOrProductionEdited':False,'evaluationExpectationsRead':False,'protectedSemanticContentsRead':False}
result['authorizedDesignReadEvidence']=reference_records
result['completedTextInputFreeze']=[{'record':p.name,'sha256':sha(p),'documentId':read(p)['documentId'],'publishedMdSha256':read(p)['publishedMdSha256'],'pins':read(p)['pins']} for p in sorted(REPORT.glob('*-text-frozen-inputs.json'))]
result['currentMdTextReadEvidence']=[{'record':p.name,'sha256':sha(p),'read':read(p)} for p in sorted(REPORT.glob('md-read-*.json'))]
with target.open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'path':str(target),'sha256':sha(target),'imagesActuallyViewed':len(viewed),'approval':None,'launchPinDrift':pin_drift,'source32PinDrift':source_drift,'capsulePinDrift':cap_drift}))
