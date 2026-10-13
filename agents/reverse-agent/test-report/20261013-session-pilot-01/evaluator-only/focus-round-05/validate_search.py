"""Validate immutable new search report, originals and completed raw proof.

This checker has no semantic scoring rules and never reads earlier reports.
"""
from pathlib import Path
import sys, datetime, hashlib, json, re
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from artifact_store import exclusive_json
import row_context_guard as guard
OUT=Path(__file__).resolve().parent
F=OUT/'frozen'
ROOT=OUT
while not (ROOT/'test-project1/srcs/CSharp_ASPNET').is_dir(): ROOT=ROOT.parent
read=guard.read
sha=guard.sha
manifest=read(OUT/'frozen-manifest.json')
inputs=read(OUT/'frozen-input-manifest.json')
pins={p['snapshotPath']:p for p in manifest['pins']}
assert len(pins)==128 and len(inputs['pins'])==88
assert manifest['allCandidatesComplete'] is True
assert manifest['selectedMaximum']==316 and manifest['selectedRows']==281
assert manifest['inputManifestSha256']==sha(OUT/'frozen-input-manifest.json')
assert manifest['generationBindingScope']=='legacy-v1-raw-indexed-metadata-revalidated-unsealed-manifest'
live=[]
for pin in pins.values():
    frozen=F/pin['snapshotPath']
    assert sha(frozen)==pin['sha256'] and frozen.stat().st_size==pin['bytes']
    original=Path(pin['originalPath'])
    if not original.is_absolute():original=ROOT/original
    assert sha(original)==pin['sha256'],('Launch/origin drift',original)
    live.append({'path':pin['originalPath'],'sha256':pin['sha256'],'kind':pin['kind']})
selected=read(OUT/'selected-rows.json')
by_id={r['evaluationId']:r for r in selected}
assert len(by_id)==len(selected)==281 and sum(r['originalPoints'] for r in selected)==316
assert sha(OUT/'selected-rows.json')==manifest['selectedRowsSha256']
report=read(OUT/'search-evaluation.json')
assert report['generatedVersion']=='5.0' and report['originalSpecificationVersion']=='8.0' and report['evaluationVersion']=='7.4'
assert report['oldMatchScoresReused'] is False and report['frozenManifestSha256']==sha(OUT/'frozen-manifest.json')
assert report['inputManifestSha256']==sha(OUT/'frozen-input-manifest.json')
review=read(OUT/'search-row-context-review.json')
context_validation=read(OUT/'search-row-context-validation-final.json')
assert review['reportSha256']==context_validation['reportSha256']==sha(OUT/'search-evaluation.json')
assert context_validation['reviewSha256']==sha(OUT/'search-row-context-review.json')
reviewed={r['evaluationId']:r for r in review['rows']}
ref_count=0
for row in report['rows']:
    original=by_id[row['evaluationId']]
    assert row['index']==original['index'] and row['documentId']==original['documentId']
    assert row['originalPoints']==original['originalPoints'] and row['originalCriticalClassification']==original['criticalClassification']
    assert row['originalExpectationSha256']==hashlib.sha256(original['originalCells'][4].encode('utf-8')).hexdigest()
    assert row['awardedPoints']==(original['originalPoints'] if row['judgement']=='match' else None if row['judgement']=='hold' else 0)
    item=reviewed[row['evaluationId']]
    assert item['originalRowContext']==guard.context(original)
    assert item['finalReasonSha256']==guard.reason_hash(row) and item['finalEvidenceSha256']==guard.evidence_hash(row)
    assert item['reasonAndEvidenceRecheckedAgainstOriginalContext'] is True and item['adjacentRowMappingUsedAsSemanticProof'] is False
    assert item['reviewedGeneratedContext']['meaning'] and all(e in row['evidence'] for e in item['reviewedGeneratedContext']['evidence'])
    for evidence in row['evidence']:
        assert evidence['path'].startswith('frozen/')
        key=evidence['path'][7:]
        assert key in pins and sha(F/key)==evidence['sha256']==pins[key]['sha256']
        count=len((F/key).read_text(encoding='utf-8-sig').splitlines())
        assert 1<=evidence['startLine']<=evidence['endLine']<=count
        ref_count+=1
assert len(report['rows'])==len(reviewed)==120 and sum(r['originalPoints'] for r in report['rows'])==147
scope=read(F/'provenance/scope.json')
assert scope['runtimeFrozenAtLaunch'] is True and len(scope['runtimeFiles'])==13
for pin in scope['runtimeFiles']:assert sha(F/'provenance'/pin['runtimePath'])==pin['sha256']
assert scope['planSha256']==sha(F/'provenance/plan/plan-verified.json')
assert scope['expectedAnswersProvided'] is False and scope['inputMode']=='training-assisted'
runner=next(p for p in pins.values() if p['kind']=='launch-runner')
assert runner['originalPath']==scope['preservedRunnerPath']
assert runner['sha256']==scope['runnerSha256']==sha(F/'provenance/launch-runner.py')
proof=read(OUT/'raw-provenance-final.json')
assert proof['allFourInferencePhasesComplete'] and len(proof['checks'])==4 and not proof['pending']
assert proof['driverFreshFlagsUsedAsProof'] is False
generation=[]
for stem,job,docid in [('student-search','488af9821732c8f6','SM-DET-STUDENT-SEARCH'),('student-editor','eebb51fa1eb2da8f','SM-DET-STUDENT-EDITOR')]:
    snapshot=read(OUT/(stem+'-snapshot.json'))
    assert len(snapshot['pins'])==20 and manifest['documentSnapshotSha256s'][stem]==sha(OUT/(stem+'-snapshot.json'))
    draft=read(F/'provenance/jobs'/job/'draft-result.json')
    frozen=F/'generated/spec/detail'/(stem+'.md')
    published=ROOT/'test-project1/spec-analysis/CSharp_ASPNET/20261013-focus-round-05/spec/detail'/(stem+'.md')
    assert draft['contentSha256']==snapshot['generatedSha256']==sha(frozen)==sha(published)
    raw=read(F/'provenance/jobs'/job/'draft/result.json')
    answer=read(F/'provenance/jobs'/job/'draft/answer.txt')
    assert answer==raw['answer']
    assert hashlib.sha256(raw['answer']['content'].encode('utf-8')).hexdigest()==sha(frozen)
    meta=json.loads(re.fullmatch(r'<!-- spec-meta: (.+) -->',frozen.read_text(encoding='utf-8-sig').splitlines()[0]).group(1))
    assert meta['documentId']==docid and meta['version']=='5.0'
    generation.append({'document':stem,'sha256':sha(frozen),'publishedFrozenCompletedDraftRawContentEqual':True,'candidatePins':20})
capsule=read(F/'provenance/source-capsule-manifest.json')
live_originals=[]
for entry in capsule['files']:
    p=ROOT/'test-project1/srcs/CSharp_ASPNET'/entry['path']
    assert sha(p)==entry['sha256']
    live_originals.append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'kind':'source'})
for entry in capsule['referenceFiles']:
    p=Path(entry['originalPath'])
    assert sha(p)==entry['sha256']
    live_originals.append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'kind':'authorized-reference'})
bridge=read(F/'evaluation/bridge-CSharp_ASPNET.json')
for doc in bridge['documents']:
    if doc['documentId'] in {r['documentId'] for r in selected}:
        for pk,hk,kind in [('currentPath','currentSha256','target-original'),('evaluationChecklist','evaluationSha256','target-checklist')]:
            p=ROOT/doc[pk];assert sha(p)==doc[hk]
            live_originals.append({'path':doc[pk],'sha256':sha(p),'kind':kind})
assert len(live_originals)==58
result={'schema':'independent-search-evidence-validation/2','classification':'EVALUATOR_ONLY','generatorMayRead':False,
 'validatedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'IDENTITIES_POINTS_EVIDENCE_AND_HASHES_VERIFIED',
 'semanticAcceptanceInferredFromMechanicalValidation':False,'searchEvaluationSha256':sha(OUT/'search-evaluation.json'),
 'frozenManifestSha256':sha(OUT/'frozen-manifest.json'),'selectedRowsSha256':sha(OUT/'selected-rows.json'),
 'validatedRows':120,'originalMaximum':147,'evidenceReferencesValidated':ref_count,
 'fullSnapshotPinsVerified':128,'inputPinsVerified':88,'eachCandidatePinsVerified':20,
 'liveLaunchOrCapsulePinChecks':live,'liveOriginalInputFilesVerified':58,'liveOriginalInputChecks':live_originals,
 'originalInputDrift':[],'runtimeAtLaunchFilesVerified':13,'laterWorkingRuntimeRequiredToMatch':False,
 'preservedRunnerSha256':runner['sha256'],'workingDriverExcludedFromInputAndDriftComparison':True,
 'completedDraftPublicationChecks':generation,'actualRawInferencePhasesVerified':4,
 'rawInferenceProvenanceSha256':sha(OUT/'raw-provenance-final.json'),'driverFreshFlagsUsedAsExecutionProof':False,
 'rowContextReviewSha256':sha(OUT/'search-row-context-review.json'),
 'rowContextValidationSha256':sha(OUT/'search-row-context-validation-final.json'),
 'summary':report['summary'],'aggregateNotYetCreated':True,'actualApplicationOrDbTestPerformed':False,
 'artifactWriteMode':'artifact_store.exclusive_json'}
exclusive_json(OUT/'search-validation-final.json',result)
print(json.dumps({'summary':report['summary'],'validationSha256':sha(OUT/'search-validation-final.json'),
 'searchSha256':sha(OUT/'search-evaluation.json'),'referencesVerified':ref_count,'pins':len(pins)},ensure_ascii=False))
