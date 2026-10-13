"""Freeze evaluator input and completed candidate documents without scoring.

Rerunning only adds newly completed document snapshots. Existing snapshots are
never overwritten. A final union manifest is created after BOTH jobs finish.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,shutil

OUT=Path(__file__).resolve().parent
ROOT=OUT
while not (ROOT/'test-project1/srcs/CSharp_ASPNET').is_dir():
    assert ROOT.parent!=ROOT
    ROOT=ROOT.parent
F=OUT/'frozen'
CAP=ROOT/'agents/reverse-agent/.tmp/20261013-tuning-01/capsules/CSharp_ASPNET-assisted'
JOB=ROOT/'agents/reverse-agent/.tmp/20261013-session-pilot-01/focus-round-04'
SCOPE=ROOT/'agents/reverse-agent/test-report/20261013-session-pilot-01/focus-round-04/scope.json'
CONFIG=ROOT/'agents/reverse-agent/.tmp/20261013-session-pilot-01/focus-round-04-config.json'
RUNNER=ROOT/'agents/reverse-agent/.tmp/20261013-session-pilot-01/focus_cycle.py'
BRIDGE=ROOT/'agents/reverse-agent/test-report/20261013-tuning-01/evaluator-only/bridge-CSharp_ASPNET.json'
IDS={'DET-CSharp_ASPNET-SCR-STU-001','DET-CSharp_ASPNET-SCR-STU-002'}
JOB_IDS={'488af9821732c8f6':'student-search.md','eebb51fa1eb2da8f':'student-editor.md'}

def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def add(src,target,kind,expected=None):
    src=Path(src)
    actual=sha(src)
    assert expected is None or actual==expected,(src,actual,expected)
    dst=F/target
    if dst.exists():
        assert sha(dst)==actual,('frozen drift',target)
    else:
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(src,dst)
    try:origin=src.relative_to(ROOT).as_posix()
    except ValueError:origin=str(src)
    return dict(originalPath=origin,snapshotPath=target,kind=kind,sha256=actual,bytes=src.stat().st_size)

capsule=read(CAP/'manifest.json')
scope=read(SCOPE)
RUNNER=ROOT/scope['preservedRunnerPath']
bridge=read(BRIDGE)
assert scope['snapshot']['manifestSha256']==sha(CAP/'manifest.json')
assert scope['inputMode']=='training-assisted' and scope['freshAnalysisRequired'] is True
assert scope['expectedAnswersProvided'] is False and scope['runtimeFrozenAtLaunch'] is True
assert len(scope['runtimeFiles'])==13
input_manifest_path=OUT/'frozen-input-manifest.json'
if not input_manifest_path.exists():
    pins=[]
    for entry in capsule['files']:
        pins.append(add(CAP/'sources'/entry['path'],'sources/'+entry['path'],'source',entry['sha256']))
        assert sha(ROOT/'test-project1/srcs/CSharp_ASPNET'/entry['path'])==entry['sha256']
    for entry in capsule['referenceFiles']:
        cap_path=entry.get('path') or entry.get('capsulePath')
        assert cap_path and cap_path.startswith('reference-designs/')
        pins.append(add(CAP/cap_path,cap_path,'authorized-reference',entry['sha256']))
        assert sha(Path(entry['originalPath']))==entry['sha256']
    for doc in bridge['documents']:
        if doc['documentId'] not in IDS:continue
        pins.append(add(ROOT/doc['currentPath'],'current-reference/'+doc['currentPath'],'current-original',doc['currentSha256']))
        pins.append(add(ROOT/doc['evaluationChecklist'],'evaluation/'+doc['evaluationChecklist'],'current-checklist',doc['evaluationSha256']))
    pins.append(add(BRIDGE,'evaluation/bridge-CSharp_ASPNET.json','evaluation-bridge'))
    pins.append(add(CAP/'manifest.json','provenance/source-capsule-manifest.json','capsule-manifest'))
    pins.append(add(SCOPE,'provenance/scope.json','launch-scope'))
    pins.append(add(CONFIG,'provenance/launch-config.json','launch-config',scope['configSha256']))
    pins.append(add(RUNNER,'provenance/launch-runner.py','launch-runner',scope['runnerSha256']))
    for ordinal,entry in enumerate(scope['inputPins']):
        pins.append(add(ROOT/entry['path'],'provenance/safe-launch-inputs/'+str(ordinal)+'-'+Path(entry['path']).name,'prior-writer-safe-launch-input',entry['sha256']))
    # Resolve the exact plan from launch scope, independent of working tree code.
    plan_verified=ROOT/read(CONFIG)['plan']
    if not plan_verified.exists():
        matches=list((ROOT/'agents/reverse-agent/.tmp').rglob('plan-verified.json'))
        matches=[p for p in matches if sha(p)==scope['planSha256']]
        assert len(matches)>=1,'launch plan not found'
        plan_verified=matches[0]
    assert sha(plan_verified)==scope['planSha256']
    pins.append(add(plan_verified,'provenance/plan/plan-verified.json','launch-plan',scope['planSha256']))
    handoff=plan_verified.with_name('plan-handoff.json')
    if handoff.exists():pins.append(add(handoff,'provenance/plan/plan-handoff.json','launch-plan-handoff'))
    for entry in scope['runtimeFiles']:
        pins.append(add(JOB/entry['runtimePath'],'provenance/'+entry['runtimePath'],'runtime-at-launch',entry['sha256']))
    for job_id in JOB_IDS:
        rev=JOB/(job_id+'-revision-context.json')
        if rev.exists():pins.append(add(rev,'provenance/jobs/'+job_id+'/revision-context.json','writer-safe-revision-input'))
    rows=[dict(row,scoreStatus='UNSCORED_NEW_FOCUS_ROUND_04',awardedPoints=None) for row in bridge['items'] if row['documentId'] in IDS]
    assert len(rows)==281 and sum(r['originalPoints'] for r in rows)==316
    (OUT/'selected-rows.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    snapshot=dict(schema='independent-focus-input-snapshot/2',classification='EVALUATOR_ONLY',generatorMayRead=False,
      frozenAt=datetime.now(timezone.utc).isoformat(),iteration='20261013-focus-round-04',attempt='focus-round-04',
      selectedDocumentIds=sorted(IDS),selectedRows=281,selectedMaximum=316,minimumFor95=301,
      mode='training-assisted',sourceCount=43,authorizedReferenceCount=11,runtimeAtLaunchFiles=13,
      sourceCapsuleManifestSha256=sha(CAP/'manifest.json'),selectedRowsSha256=sha(OUT/'selected-rows.json'),
      generationBindingScope=scope['snapshot']['scope'],runtimeFrozenAtLaunch=True,oldMatchScoresReused=False,
      pins=pins,candidateDocumentsIncluded=False)
    input_manifest_path.write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
input_manifest=read(input_manifest_path)
for pin in input_manifest['pins']:assert sha(F/pin['snapshotPath'])==pin['sha256']

newly_frozen=[]
ready=[]
for job_id,name in JOB_IDS.items():
    snapshot_path=OUT/(name.replace('.md','')+'-snapshot.json')
    if snapshot_path.exists():
        document=read(snapshot_path)
        for pin in document['pins']:assert sha(F/pin['snapshotPath'])==pin['sha256']
        ready.append(document)
        continue
    result_path=JOB/job_id/'draft-result.json'
    published=ROOT/'test-project1/spec-analysis/CSharp_ASPNET/20261013-focus-round-04/spec/detail'/name
    if not (result_path.exists() and published.exists()):continue
    result=read(result_path)
    assert sha(published)==result['contentSha256'],('incomplete candidate bytes',published)
    pins=[add(published,'generated/spec/detail/'+name,'new-generated-document',result['contentSha256'])]
    filenames=['analysis-handoff.json','analysis-verified.json','analysis-snapshot-before.json','analysis-snapshot-after.json',
      'draft-result.json','draft-snapshot-before.json','draft-snapshot-after.json',
      'analysis/prompt.txt','analysis/schema.json','analysis/result.json','analysis/answer.txt',
      'draft/prompt.txt','draft/schema.json','draft/result.json','draft/answer.txt',
      'analysis/events.jsonl','analysis/stderr.log','draft/events.jsonl','draft/stderr.log']
    for filename in filenames:
        p=JOB/job_id/filename
        assert p.exists(),('missing completed provenance',p)
        pins.append(add(p,'provenance/jobs/'+job_id+'/'+filename,'generation-job-proof'))
    document=dict(schema='independent-focus-document-snapshot/1',classification='EVALUATOR_ONLY',generatorMayRead=False,
      frozenAt=datetime.now(timezone.utc).isoformat(),iteration='20261013-focus-round-04',attempt='focus-round-04',
      generatedPath='frozen/generated/spec/detail/'+name,generatedSha256=result['contentSha256'],jobId=job_id,
      inputManifestSha256=sha(input_manifest_path),oldMatchScoresReused=False,pins=pins,
      generatedBytesMatchDraftContent=True,generationBindingScope=scope['snapshot']['scope'],runtimeAtLaunchFiles=13)
    snapshot_path.write_text(json.dumps(document,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    ready.append(document)
    newly_frozen.append(name)
if len(ready)==2:
    final_path=OUT/'frozen-manifest.json'
    combined=dict(input_manifest,candidateDocumentsIncluded=True,allCandidatesComplete=True,
      frozenAt=datetime.now(timezone.utc).isoformat(),inputManifestSha256=sha(input_manifest_path),
      documentSnapshotSha256s={name.replace('.md',''):sha(OUT/(name.replace('.md','')+'-snapshot.json')) for name in JOB_IDS.values()},
      pins=input_manifest['pins']+[p for document in ready for p in document['pins']])
    assert len({p['snapshotPath'] for p in combined['pins']})==len(combined['pins'])
    if not final_path.exists():final_path.write_text(json.dumps(combined,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    else:
        for pin in read(final_path)['pins']:assert sha(F/pin['snapshotPath'])==pin['sha256']
print(json.dumps(dict(preparedInputPins=len(input_manifest['pins']),runtimeAtLaunchFiles=13,
  selectedRows=281,selectedMaximum=316,newlyFrozen=newly_frozen,readyDocuments=[d['generatedPath'] for d in ready],
  completeUnionManifest=(OUT/'frozen-manifest.json').exists()),ensure_ascii=False))
