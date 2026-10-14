"""Record actual partial visual inspections and sealed infrastructure progress."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json

report = Path(__file__).resolve().parents[1]
load = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
created = datetime.now(timezone.utc).isoformat()
records = []
for render_name, image_name, expected_md, finding, output_name in (
    ('source-m-code-category-r03', 'document.png', 'c43b8c5de33de810413b9b5cf306f1fd60ae4a9d054fd2be7c1a7bd6f6adab46',
     'The full original-size image was inspected. Markdown table labels wrap vertically and borders are absent. Renderer r10 correction is undergoing separate review.',
     'source-m-code-category-r03-readability.json'),
    ('search-basic-r04', 'diagram-010.png', '8751f6474def2b8bbfe5c29fedfcb8418368cb2d703845611ca2f957fd3a2463',
     'The original-size 665x1306 subflow was inspected. Branch lines can be traced, but automatic line wrapping splits GET and some Japanese words. Only this diagram was inspected; final revision and all states remain pending.',
     'source-search-basic-r04-readability.json'),
):
    render = report / 'render' / render_name
    pins = load(render / 'render-pins.json')
    image = render / image_name
    md = Path(pins['source'])
    if sha(md) != expected_md or sha(image) not in json.dumps(pins, ensure_ascii=False):
        raise ValueError('Actually viewed image or parent draft drift')
    output = report / 'visual-review' / output_name
    if output.exists():
        raise ValueError('Partial visual records are immutable')
    record = {'schema': 'reverse-agent-native-visual-review/1', 'documentId': pins['documentId'],
        'referenceMode': pins['referenceMode'], 'canonicalDocumentPath': str(md.resolve()),
        'canonicalRelativePath': pins['canonicalDocumentPath'], 'documentSha256': expected_md,
        'sourceSnapshotSha256': pins['sourceSnapshotManifestSha256'],
        'reviewScope': 'DISPLAY_READABILITY_ONLY', 'reviewer': '/root', 'reviewedAt': created,
        'reviewedImages': [{'path': str(image.resolve()), 'sha256': sha(image)}],
        'reviewedSourceResources': [], 'modesReviewed': [], 'findings': [finding],
        'approved': False, 'originalApplicationExecuted': False,
        'pixelEquivalenceToRunningApplicationVerified': False, 'formalQualityGatePassed': False}
    output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    records.append(output.relative_to(report).as_posix())

path = report / 'run-manifest.json'
old = path.read_bytes()
(report / 'checkpoints/run-manifest-before-1138.json').write_bytes(old)
manifest = json.loads(old)
manifest['updatedAt'] = created
manifest['activeGenerationJobs'] = ['search-detail-06', 'remaining-batch-03',
    'training-assisted/batch-01', 'training-assisted/revision-search-basic-r02',
    'training-assisted/revision-registration-basic-r02']
manifest['currentReviewJobs'] = ['search-basic-06', 'source-only/m_student-batch03',
                               'training-assisted/table-index-batch01', 'training-assisted/m_class-batch01']
manifest['nativeVisualReview']['records'].extend(records)
manifest['nativeVisualReview']['imagesActuallyReviewed'] = 8
manifest['nativeVisualReview']['approved'] = False
manifest['currentFormalGrading'] = {'batch': 'evaluator-only/batches/source-m-code-category-r03-r6',
    'referenceMode': 'source-only', 'status': 'RUNNING', 'documentId': 'CSHARP_ASPNET-BAS-STU-03-M_CODE_CATEGORY',
    'canonicalSha256': 'c43b8c5de33de810413b9b5cf306f1fd60ae4a9d054fd2be7c1a7bd6f6adab46',
    'rows': 112, 'shards': 2, 'previousBatch': 'evaluator-only/batches/source-m-code-category-r03-r5',
    'previousStatus': 'INVALID_ZERO_DEFECT_DEDUCTIONS_AND_PROVIDER_FAILURE', 'formalScore': None}
manifest['evaluatorInfrastructure'] = {'revision': 'r6',
    'report': 'evaluator-only/infrastructure-verification-raw-deduction-r6.json', 'testsPassed': 29,
    'combinerReport': 'evaluator-only/combiner-verification-raw-deduction-r6.json', 'combinerTestsPassed': 29,
    'rubricChanged': False, 'rawAnswerRepairPerformed': False}
manifest['sourceAudit'] = {'documentComparison': 'source-audit/document-comparison-03.json',
    'personalDataFlow': 'source-audit/personal-data-flow-audit-01.json',
    'scope': 'source-only basic05/detail04; newer drafts and running app not audited'}
manifest['deliveryChecks']['excelLiteralDisplay'] = {'report': 'delivery/excel-literal-application-r01/result.json',
    'status': 'PASS_READ_ONLY_ACTUAL_EXCEL_VALUE_AND_TEXT_1.0',
    'scope': 'old search-basic03 export, cover X18 only; not full-workbook or final-draft approval'}
path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'partialRootImagesActuallyReviewed': 8, 'formalScore': None, 'qualifiedDocuments': 0}))
