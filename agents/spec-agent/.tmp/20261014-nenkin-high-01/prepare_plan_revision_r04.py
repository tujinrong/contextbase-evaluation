"""Preserve complete current AI planning/review data as revision feedback."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json
RUN = Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/.tmp/20261014-nenkin-high-01')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
paths = {
    'plan': (RUN / 'jobs/plan-03/plan-verified.json', 'f302f6d345e87add5a9ac4ef6b0d19f9708dfcb9bdd3c92e3d411795e9d8146d'),
    'executionContext': (RUN / 'execution-context-input-02.json', '8966757e00954241029817027efa85bafeb859beee5105b05c7c939c84470605'),
    'unverifiedReview': (RUN / 'jobs/independent-plan-review-03/answer.txt', 'fe4e1f4b659281e4a16fdc679cdfd6c4484264064374a98c64043b4fdcebdc15'),
    'reviewTerminal': (RUN / 'jobs/independent-plan-review-03-plan-review-after.json', None)
}
data, pins = {}, {}
for name, (path, expected) in paths.items():
    actual = sha(path)
    if expected is not None and actual != expected: raise ValueError('Pinned input differs: ' + name)
    data[name] = json.loads(path.read_text(encoding='utf-8-sig'))
    pins[name] = {'path': str(path), 'sha256': actual}
if data['reviewTerminal']['status'] != 'REVIEW_NOT_VERIFIED': raise ValueError('Terminal state differs')
target = RUN / 'plan-semantic-feedback-r04.json'
record = {
    'schema': 'spec-agent-complete-plan-revision-data/1', 'createdUtc': datetime.now(timezone.utc).isoformat(),
    'scope': 'source-only current-run AI feedback, not original specifications or evaluation expectations',
    'sourceCapsuleManifestSha256': 'f074529043ff1c25ea53be34c16ae3a4788f137a1e3afb33c6214de7bf4c7445',
    'completeData': data, 'originalBytePins': pins,
    'unverifiedReviewIsNotApproval': True, 'unverifiedReviewIsNotFormalScoring': True,
    'request': 'Create a fresh complete plan from the current sealed sources. Reassess all claims in the full raw review, correct substantiated responsibility/source-path/identity coverage gaps, preserve current document IDs/paths/canonical kinds and distinguish declared but disconnected resources from current user functions. Do not invent new functions/tables from declarations. Include full metadata, feature and table format responsibilities. Keep unknown deployed behavior explicit. The review failed evidence consistency validation and cannot be adopted as an approved or formal evaluation; reconsider its claims against source evidence rather than copying them blindly. Return the complete original plan schema, not a patch or abbreviated plan.',
    'businessFieldsManuallyAuthored': False
}
for name, (path, _) in paths.items():
    if sha(path) != pins[name]['sha256']: raise ValueError('Input drift: ' + name)
with target.open('xb') as stream:
    stream.write((json.dumps(record, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
print(json.dumps({'feedback': str(target), 'sha256': sha(target)}, ensure_ascii=False))
