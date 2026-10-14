"""Preserve source-only projection failures and immutable provenance; no HTML edits."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from contextbase.ai import capsule

report = Path(__file__).resolve().parent
repo = report.parents[4]
scope = repo / 'agents/reverse-agent/.tmp/20261013-rerun-12h/source-only'
snapshot = scope / 'snapshot'
sha = lambda b: hashlib.sha256(b).hexdigest()
fixed = '2f64e2211b1fcd7850203927fc75b5a7f2ce37457cc2afe88c8065d9f931273b'
assert sha(capsule.safe_path(snapshot/'manifest.json').read_bytes()) == fixed
manifest = capsule.verify(snapshot)
state = capsule.verification_state(snapshot)
assert state['manifestSha256'] == fixed and state['mode'] == 'source-only'
allowed = workflow_materials = {'manifest.json'}
for entry in manifest['files']:
    allowed.update((entry['path'], 'sources/'+entry['path'], entry['indexed']))
    assert sha(capsule.safe_path(Path(manifest['sourceRoot'])/entry['path']).read_bytes()) == entry['sha256']
receipt = report/'runtime-code-source-07.json'
receipt_bytes = receipt.read_bytes()
assert sha(receipt_bytes) == '0b2f2aff745a7e32394ecc5cde4c1a849ad2d5a32c7fa4339af2e7cdecd48906'
freeze = json.loads(receipt_bytes)
runtime = capsule.safe_path(Path(freeze['destination']))
inventory = {p.relative_to(runtime).as_posix():sha(capsule.safe_path(p).read_bytes()) for p in runtime.rglob('*')
             if p.is_file() and '__pycache__' not in p.parts and p.suffix.lower() not in {'.pyc','.pyo'}}
assert inventory == freeze['files']

def pin(path):
    data = capsule.safe_path(path).read_bytes()
    return {'file':str(path.resolve()), 'sha256':sha(data), 'bytes':len(data)}

basic_job = scope/'jobs/search-basic-08-state-01-meaning-review'
basic_handoff = json.loads((basic_job/'meaning-review-handoff.json').read_bytes())
basic_raw = json.loads((basic_job/'review/answer.txt').read_bytes())
detail_job = scope/'jobs/search-detail-09-state-01'
detail_raw = json.loads((detail_job/'projection/answer.txt').read_bytes())
detail_input = json.loads((detail_job/'projection-input-pin.json').read_bytes())
detail_paths = []
for declared in detail_raw['sourcePathsRead']:
    path = capsule.safe_path(Path(declared))
    relative = path.relative_to(capsule.safe_path(snapshot)).as_posix()
    assert relative in allowed
    detail_paths.append({'declaredPath':declared, 'snapshotRelativeAlias':relative, 'registeredInFixedCapsule':True})
for doc in detail_input['documents']:
    assert sha(capsule.safe_path(Path(doc['file'])).read_bytes()) == doc['sha256']
assert basic_handoff['allPinnedInputsAndOriginalSourceAndRuntimeUnchanged'] is True
assert basic_handoff['approved'] is False and basic_handoff['requiresCanonicalRevision'] is True
assert not (detail_job/'projection-handoff.json').exists()
basic_provider = json.loads((basic_job/'review/result.json').read_bytes())
detail_provider = json.loads((detail_job/'projection/result.json').read_bytes())
record = {
    'classification':'SOURCE_ONLY_STATE_FAILURE_BASELINE_PRESERVED_NO_NEW_AI_JOB',
    'createdAt':datetime.now(timezone.utc).isoformat(),
    'snapshot':state, 'original41SourcesStillMatchSealedBaseline':True,
    'runtimeReceipt':pin(receipt), 'runtime124FilesStillMatchReceipt':True,
    'basic08':{
        'parentSha256':basic_handoff['documentSha256'], 'handoff':pin(basic_job/'meaning-review-handoff.json'),
        'rawReviewAnswer':pin(basic_job/'review/answer.txt'), 'providerResult':pin(basic_job/'review/result.json'),
        'providerSeconds':basic_provider['metadata']['seconds'], 'approved':False, 'requiresCanonicalRevision':True,
        'findings':basic_raw['findings'],
        'cause':'Reviewer distinguishes projection-only inert forms and removed href from canonical fragment links and original active/disabled behavior. Business state classifications, texts, columns and disabled conditions were otherwise judged consistent.',
        'actions':pin(report/'search-basic08-state01-meaning-provider-actions.json'),
        'observedActionScope':'23 successful reads/inventory commands remain in sealed manifest/sources/indexed; two relative manifest reads failed, then absolute NoProfile reads succeeded. Filename inventory contains only sealed materials.',
        'allPinnedInputsAndOriginalSourceAndRuntimeUnchanged':True},
    'detail09':{
        'parentSha256':detail_input['documents'][0]['sha256'],
        'rawProjectionAnswer':pin(detail_job/'projection/answer.txt'), 'providerResult':pin(detail_job/'projection/result.json'),
        'providerExitCode':detail_provider['exit_code'], 'providerStatus':detail_provider['metadata']['status'],
        'providerSeconds':detail_provider['metadata']['seconds'],
        'helperExitCode':1, 'handoffCreated':False, 'postAnswerGateCompleted':False,
        'cause':'workflow.references_valid rejects absolute sourcePathsRead even when every path maps exactly into allowed fixed snapshot materials. Raw answer is preserved; no metadata normalization or HTML correction was performed.',
        'declaredAbsolutePaths':detail_paths, 'rawStatesRequireCanonicalRevision':[s['requiresCanonicalRevision'] for s in detail_raw['states']],
        'actions':pin(report/'search-detail09-state01-provider-actions.json'),
        'observedActionScope':'All 21 recorded commands read/list/hash fixed snapshot manifest and registered indexed source files; zero failed commands.'},
    'parentPriority':'Preserve clean source-only baseline; do not start basic09 or fresh source-only state jobs. Existing register writers continue naturally.',
    'rawAnswersModified':False, 'canonicalDocumentsModified':False, 'businessHtmlAssembledByPython':False,
    'commandAuditIsOsIsolationProof':False, 'allStateNativeApproved':False, 'formalApproval':False, 'adopted':False,
    'applicationDatabaseBuildOrInputTestsExecuted':False}
output = report/'search-source-state-failures-1428.json'
with output.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(record,stream,ensure_ascii=False,indent=2);stream.write('\n')
assert sha((snapshot/'manifest.json').read_bytes()) == fixed and receipt.read_bytes() == receipt_bytes
print(json.dumps({'file':str(output),'sha256':sha(output.read_bytes()),'basicReviewSeconds':record['basic08']['providerSeconds'],
                  'detailProjectionSeconds':record['detail09']['providerSeconds']},ensure_ascii=False))
