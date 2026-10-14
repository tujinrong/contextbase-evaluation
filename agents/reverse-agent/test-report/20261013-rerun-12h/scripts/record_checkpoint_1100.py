"""Update run metadata from completed verification receipts; no grading or spec authoring."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json

report = Path(__file__).resolve().parents[1]
load = lambda path: json.loads(path.read_text(encoding='utf-8-sig'))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
path = report / 'run-manifest.json'
manifest = load(path)
with (report / 'checkpoints/run-manifest-before-1100.json').open('x', encoding='utf-8') as stream:
    json.dump(manifest, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
probe_path = report / 'evaluator-only/batches/search-basic-r04-probe-40-r4/jobs/CSHARP_ASPNET-BAS-STU-01-S001/result.json'
probe = load(probe_path)
if probe['status'] != 'PASSED' or sha(probe_path.parent / 'answer.txt') != probe['answerSha256']:
    raise ValueError('Probe is not a sealed accepted raw answer')
probe_record = {'schema': 'reverse-agent-grader-probe/1', 'status': 'PASSED',
    'formalEvaluation': False, 'scope': 'one 36-row integrity probe, not complete document evaluation',
    'completedAt': datetime.now(timezone.utc).isoformat(), 'result': str(probe_path.relative_to(report)),
    'resultSha256': sha(probe_path), 'answerSha256': probe['answerSha256'],
    'seconds': probe['seconds'], 'requestedRows': probe['requestedRows'],
    'graderSha256': probe['graderSha256'], 'formalScore': None}
with (report / 'evaluator-only/probe-r4-accepted.json').open('x', encoding='utf-8') as stream:
    json.dump(probe_record, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
manifest['updatedAt'] = datetime.now(timezone.utc).isoformat()
manifest['activeGenerationJobs'] = ['search-basic-06', 'search-detail-05', 'remaining-batch-03',
    'training-assisted/batch-01', 'training-assisted/revision-search-basic-r02',
    'training-assisted/revision-registration-basic-r02']
manifest['engineeringValidation']['latestFormatRevision'] = 'r9'
manifest['engineeringValidation']['latestFormatReport'] = 'engine/static-format-r9-result.json'
manifest['engineeringValidation']['latestFormatTestsPassed'] = 131
manifest['gradingProbe']['status'] = 'PASSED'
manifest['gradingProbe']['receipt'] = 'evaluator-only/probe-r4-accepted.json'
manifest['evaluationWorkerPolicy'] = {'maximumConcurrentWorkers': 8, 'maximumRowsPerShard': 80,
    'deadline': manifest['deadline'], 'rule': 'Only pinned completed drafts; preserve every failed raw answer'}
manifest['nativeVisualReview']['records'].append('visual-review/assisted-search-basic-r01-partial.json')
manifest['nativeVisualReview']['imagesActuallyReviewed'] = 6
manifest['nativeVisualReview']['approved'] = False
manifest['deliveryChecks'].update({'xlsx': 'MECHANICALLY_VERIFIED_VISUAL_REVIEW_REQUIRED',
    'pdf': 'TEXT_VERIFIED_VISUAL_REVIEW_FAILED', 'pdfPagesActuallyReviewed': 106,
    'xlsxTilesActuallyReviewed': 42, 'repairQaReport': 'delivery/repair-qa-final-r09.json',
    'nativeReadabilityImprovement': 'AI_SUBFLOW_REVISION_IN_PROGRESS', 'formalPublication': False})
manifest['latestProtectedInputVerification'] = 'checkpoints/protected-inputs-03.json'
manifest['sourceCandidateInventory'] = 'source-pilot/candidate-inventory-1059.json'
with path.open('w', encoding='utf-8', newline='\n') as stream:
    json.dump(manifest, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps({'probe': 'PASSED', 'formalScore': None, 'qualifiedDocuments': 0}))
