"""Record completed projection provenance without assembling or changing HTML."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--job', required=True, type=Path)
p.add_argument('--output', required=True, type=Path)
p.add_argument('--meaning-review-job', required=True, type=Path)
p.add_argument('--actions', required=True, type=Path)
a = p.parse_args()
sha = lambda b: hashlib.sha256(b).hexdigest()
handoff_file = a.job / 'projection-handoff.json'
handoff_bytes = handoff_file.read_bytes()
handoff = json.loads(handoff_bytes)
answer_file = Path(handoff['rawAnswer'])
answer_bytes = answer_file.read_bytes()
assert sha(answer_bytes) == handoff['rawAnswerSha256']
result_file = a.job / 'projection' / 'result.json'
result_bytes = result_file.read_bytes()
result = json.loads(result_bytes)
assert result['exit_code'] == 0 and result['metadata']['status'] == 'passed'
assert result['metadata']['reference_mode'] == 'source-only'
assert not result['metadata']['training_reference_authorized']
assert {s['id'] for s in handoff['states']} == {'normal', 'empty', 'tooMany', 'viewer'}
assert len(handoff['states']) == 4
assert not any(s['requiresCanonicalRevision'] for s in handoff['states'])
for item in handoff['documents']:
    assert sha(Path(item['file']).read_bytes()) == item['sha256']
actions_bytes = a.actions.read_bytes()
actions = json.loads(actions_bytes)
record = {
    'classification': 'SOURCE_ONLY_STATIC_PROJECTION_SAVED_NOT_MEANING_OR_NATIVE_APPROVAL',
    'observedAt': datetime.now(timezone.utc).isoformat(),
    'projectionJob': str(a.job.resolve()),
    'projectionHandoff': str(handoff_file.resolve()),
    'projectionHandoffSha256': sha(handoff_bytes),
    'rawAnswer': str(answer_file.resolve()),
    'rawAnswerSha256': sha(answer_bytes),
    'rawAnswerBytes': len(answer_bytes),
    'providerResult': str(result_file.resolve()),
    'providerResultSha256': sha(result_bytes),
    'providerExitCode': result['exit_code'],
    'providerStatus': result['metadata']['status'],
    'providerSeconds': result['metadata']['seconds'],
    'providerSchemaTransportAccepted': True,
    'modelSelection': result['metadata']['model_selection'],
    'actualModelExposed': False,
    'documents': handoff['documents'],
    'snapshot': handoff['snapshot'],
    'states': handoff['states'],
    'helperSha256': handoff['helperSha256'],
    'helperUnchanged': handoff['helperUnchanged'],
    'runtimeReceiptSha256': handoff['runtimeReceiptSha256'],
    'runtimeReceiptUnchanged': handoff['runtimeReceiptUnchanged'],
    'approvedCanonicalReview': handoff['approvedCanonicalReview'],
    'providerActions': str(a.actions.resolve()),
    'providerActionsSha256': sha(actions_bytes),
    'observedCommands': actions['completedCommands'],
    'failedObservedCommands': actions['failedCommands'],
    'observedActionReview': 'all recorded commands inspect sealed manifest or allowed indexed source files',
    'commandAuditIsOsReadIsolationProof': False,
    'meaningReviewJob': str(a.meaning_review_job.resolve()),
    'meaningReviewStatus': 'RUNNING_OR_PENDING',
    'staticMeaningApproved': False,
    'allStateNativeApproved': False,
    'adopted': False,
    'applicationExecuted': False,
    'businessHtmlAssembledByPython': False,
}
with a.output.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps({'output': str(a.output.resolve()), 'sha256': sha(a.output.read_bytes()), 'providerSeconds': record['providerSeconds']}, ensure_ascii=False))
