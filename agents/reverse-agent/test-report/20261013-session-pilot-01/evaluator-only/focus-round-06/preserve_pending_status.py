"""Preserve already observed frozen preparation/proof; do not observe live jobs.

No semantic decision is made here. This records only the still-unscored scope.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from artifact_store import exclusive_json
parser=argparse.ArgumentParser()
parser.add_argument('--output',required=True,type=Path)
parser.add_argument('--raw-proof',required=True,type=Path)
parser.add_argument('--boundary-status',required=True)
args=parser.parse_args()
args.raw_proof=args.raw_proof.resolve()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
rows=read(HERE/'selected-rows.json');inputs=read(HERE/'frozen-input-manifest.json')
proof=read(args.raw_proof)
assert args.raw_proof.resolve().is_relative_to(HERE)
assert len(rows)==281 and sum(r['originalPoints'] for r in rows)==316
assert all(r['awardedPoints'] is None for r in rows)
snapshots=[]
for p in sorted(HERE.glob('student-*-snapshot.json')):
    body=read(p)
    snapshots.append({'path':p.relative_to(HERE).as_posix(),'sha256':sha(p),
        'generatedSha256':body['generatedSha256'],'candidatePins':len(body['pins'])})
payload={'schema':'unscored-focus-boundary-status/1','classification':'EVALUATOR_ONLY','generatorMayRead':False,
 'preservedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'iteration':'20261013-focus-round-06',
 'boundaryStatus':args.boundary_status,'originalRows':281,'originalMaximum':316,
 'selectedRowsSha256':sha(HERE/'selected-rows.json'),'inputManifestSha256':sha(HERE/'frozen-input-manifest.json'),
 'originalWeightsChanged':False,'oldMatchScoresReused':False,'inputPins':len(inputs['pins']),
 'completedInferencePhasesAlreadyVerified':len(proof['checks']),'pendingInferencePhasesAtRecordedObservation':proof['pending'],
 'rawProvenanceProof':{'path':args.raw_proof.relative_to(HERE).as_posix(),'sha256':sha(args.raw_proof),'verifiedAt':proof['verifiedAt']},
 'candidateSnapshotsAlreadyFrozen':snapshots,'newLiveJobObservationPerformedByThisScript':False,
 'newSemanticJudgementPerformedByThisScript':False,'allSelectedRowsUnscored':True,
 'confirmedScore':None,'completeScore':None,'completePercent':None,'formal95Result':None,
 'deadline':'2026-10-13T03:20:58Z','sourceMode':inputs['mode'],
 'generationBindingScope':inputs['generationBindingScope'],'sourceExecutionOrVisualAcceptanceInferred':False,
 'rows':[{'evaluationId':r['evaluationId'],'documentId':r['documentId'],'index':r['index'],
    'originalPoints':r['originalPoints'],'status':'UNSCORED','awardedPoints':None} for r in rows]}
assert not (HERE/'search-evaluation.json').exists() and not (HERE/'editor-evaluation.json').exists(), 'Use the completed component reports; do not erase their independently scored scope.'
saved=exclusive_json(args.output,payload)
print(json.dumps({'sha256':saved['sha256'],'originalRows':281,'originalMaximum':316,'allUnscored':True,
 'alreadyVerifiedCalls':len(proof['checks']),'alreadyFrozenCandidates':len(snapshots),'formal95Result':None},ensure_ascii=False))
