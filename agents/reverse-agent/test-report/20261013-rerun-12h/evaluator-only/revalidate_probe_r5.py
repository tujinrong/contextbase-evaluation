"""Check a preserved R4 response against stricter evidence gates, without regrading it."""
from datetime import datetime, timezone
from pathlib import Path
import grader

here = Path(__file__).resolve().parent
batch = here / 'batches/search-basic-r04-probe-40-r4'
seal = grader.load(batch / 'batch.json')
archive = here / 'code-history/grader-before-safety-evidence-r5.py'
if grader.digest(archive) != seal['graderSha256']:
    raise ValueError('Historical evaluator implementation is not preserved')
capsule = batch / 'capsule'
if grader.digest(capsule / 'manifest.json') != seal['capsuleManifestSha256']:
    raise ValueError('Historical capsule manifest drift')
manifest = grader.load(capsule / 'manifest.json')
for entry in manifest['files']:
    if grader.digest(grader.safe(capsule / entry['path'], capsule)) != entry['sha256']:
        raise ValueError('Historical capsule evidence drift')
job = seal['jobs'][0]
target = batch / 'jobs' / job['shardId']
receipt = grader.load(target / 'result.json')
if receipt['status'] != 'PASSED' or grader.digest(target / 'answer.txt') != receipt['answerSha256']:
    raise ValueError('Historical raw accepted response changed')
grader.validate_answer(grader.load(target / 'answer.txt'), grader.load(capsule / job['requestPath']), capsule)
grader.save(here / 'probe-r4-revalidated-safety-r5.json', {
    'schema': 'historical-probe-evidence-compatibility/1', 'status': 'PASS',
    'verifiedAt': datetime.now(timezone.utc).isoformat(), 'rows': receipt['requestedRows'],
    'historicalGraderSha256': grader.digest(archive), 'currentGraderSha256': grader.digest(here / 'grader.py'),
    'historicalBatchSha256': grader.digest(batch / 'batch.json'), 'answerSha256': receipt['answerSha256'],
    'newInferencePerformed': False, 'rawAnswerRewritten': False, 'deductionsChanged': False,
    'fullDocumentEvaluated': False, 'formalScore': None,
    'scope': 'Evidence acceptance only; old raw response stays bound to its original R4 receipt',
})
print({'evidenceCompatibility': 'PASS', 'formalScore': None})
