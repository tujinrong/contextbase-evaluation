"""Record inspected images and normalization retry integrity; no spec text changes."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import re

report = Path(__file__).resolve().parents[1]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
write = lambda p, v: p.write_text(json.dumps(v, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
created = datetime.now(timezone.utc).isoformat()
evaluation = report/'evaluator-only'
if sha(evaluation/'grader.py') != '83390d439db12119fa7f82cfb48672105488ccb748ca960c68ff918112190bb7':
    raise ValueError('Accepted R6 grader must remain immutable')
log = evaluation/'normalization-retry-infrastructure-n2.log'
match = re.search(r'Ran (\d+) tests in ([0-9.]+)s\s+OK', log.read_text(encoding='utf-8-sig'))
if not match or int(match[1]) != 64:
    raise ValueError('Complete 64-test passing receipt required')
retry = load(evaluation/'batches/source-m-code-category-r03-r6-n2/retry-provenance.json')
if not retry['normalizationOnlyRetry'] or len(retry['reusedAcceptedJobs']) != 2 or retry['retryJobs']:
    raise ValueError('Only unchanged accepted grading answers may be reused')
infrastructure = {'schema': 'normalization-retry-infrastructure/1', 'createdAt': created,
    'status': 'PASS', 'testsPassed': int(match[1]), 'seconds': float(match[2]),
    'log': log.relative_to(report).as_posix(), 'logSha256': sha(log),
    'normalizerSha256': sha(evaluation/'normalize_defects.py'),
    'retryHelperSha256': sha(evaluation/'retry_batch.py'),
    'graderSha256': sha(evaluation/'grader.py'), 'rubricChanged': False,
    'rawAnswerRepairPerformed': False, 'previousFailedNormalizationPreserved': True,
    'reusedAcceptedJobs': retry['reusedAcceptedJobs'],
    'scope': 'immutable normalization-only retry and complete grader/combiner regressions'}
write(evaluation/'normalization-retry-infrastructure-n2.json', infrastructure)
records = []
for name, image_name, expected, finding, filename in (
    ('search-detail-r03', 'diagram-025.png', 'fbe553c538dcc395f2f5425e67d66f22cf883b10e02ea2cb1c26ea21367e1f7f',
     'Full original-size 1835x322 diagram inspected. Lines pass through partially transparent edge labels and some identifiers wrap mid-word. Trusted opaque-label rendering and author geometry revision are pending.',
     'source-search-detail-r03-readability.json'),
    ('assisted-register-basic-r02', 'diagram-019.png', 'de75049fe88d059310f658850f7689e280848f48843682ab6da7ddca6d7c578e',
     'Full original-size 1049x3043 diagram inspected. Branches remain readable at original scale, but height requires a separate print readability check. This partial view does not approve the document or its pending semantic revision.',
     'assisted-register-basic-r02-readability.json'),
):
    render = report/'render'/name
    pins = load(render/'render-pins.json')
    md, image = Path(pins['source']), render/image_name
    if sha(md) != expected or sha(image) not in json.dumps(pins):
        raise ValueError('Actually inspected parent/image drift')
    target = report/'visual-review'/filename
    if target.exists():
        raise ValueError('Fresh immutable inspection record required')
    write(target, {'schema': 'reverse-agent-native-visual-review/1',
        'documentId': pins['documentId'], 'referenceMode': pins['referenceMode'],
        'canonicalDocumentPath': str(md.resolve()), 'canonicalRelativePath': pins['canonicalDocumentPath'],
        'documentSha256': expected, 'sourceSnapshotSha256': pins['sourceSnapshotManifestSha256'],
        'reviewScope': 'DISPLAY_READABILITY_ONLY', 'reviewer': '/root', 'reviewedAt': created,
        'reviewedImages': [{'path': str(image.resolve()), 'sha256': sha(image)}],
        'reviewedSourceResources': [], 'modesReviewed': [], 'findings': [finding],
        'approved': False, 'originalApplicationExecuted': False,
        'pixelEquivalenceToRunningApplicationVerified': False, 'formalQualityGatePassed': False})
    records.append(target.relative_to(report).as_posix())
path = report/'run-manifest.json'
old = path.read_bytes()
(report/'checkpoints/run-manifest-before-1210.json').write_bytes(old)
manifest = json.loads(old)
manifest['updatedAt'] = created
manifest['nativeVisualReview']['records'].extend(records)
manifest['nativeVisualReview']['imagesActuallyReviewed'] = 10
manifest['nativeVisualReview']['approved'] = False
manifest['currentFormalGrading'].update(
    batch='evaluator-only/batches/source-m-code-category-r03-r6-n2',
    status='GRADING_ACCEPTED_INDEPENDENT_NORMALIZATION_RUNNING', formalScore=None,
    rowsAccepted=112, reusedGradingShards=2,
    previousNormalizationBatch='evaluator-only/batches/source-m-code-category-r03-r6',
    previousNormalizationStatus='FAILED_READ_BOUNDARY',
    normalizationRetryReport='evaluator-only/normalization-retry-infrastructure-n2.json')
manifest['activeGenerationJobs'] = ['source-only/search-basic-07', 'source-only/search-detail-07',
    'source-only/register-basic-04', 'source-only/remaining-batch-03-and-r11-revisions',
    'training-assisted/batch-01-and-r11-revisions', 'training-assisted/search-basic-r03',
    'training-assisted/registration-basic-r03']
write(path, manifest)
print(json.dumps({'infrastructureTests': 64, 'rootPartialImagesViewed': 10, 'formalScore': None}))
