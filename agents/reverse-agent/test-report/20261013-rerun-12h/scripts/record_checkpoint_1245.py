"""Record accepted scores and actual native inspections; never author spec prose."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json

report = Path(__file__).resolve().parents[1]
load = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def fresh(path, value):
    if path.exists():
        raise ValueError('Immutable checkpoint already exists: ' + str(path))
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

created = datetime.now(timezone.utc).isoformat()
evaluation = report/'evaluator-only'
if sha(evaluation/'grader.py') != '83390d439db12119fa7f82cfb48672105488ccb748ca960c68ff918112190bb7':
    raise ValueError('Accepted grader changed')
results = []
for name in ('source-m-code-category-r03-r6-n2', 'assisted-m-code-category-r01-r6', 'assisted-m-class-r02-r6'):
    batch = evaluation/'batches'/name
    score = load(batch/'score.json')
    pin = load(batch/'canonical-pin.json')
    completed = [d for d in score['documents'] if d['complete']]
    if len(completed) != 1 or completed[0]['documentId'] != pin['documentId'] or score['total']['percentage'] is not None:
        raise ValueError('One-document score with unknown whole-set score required')
    if sha(Path(pin['canonicalPath'])) != pin['canonicalSha256']:
        raise ValueError('Accepted canonical changed')
    results.append({'batch': batch.relative_to(report).as_posix(), 'scoreSha256': sha(batch/'score.json'),
        'pinSha256': sha(batch/'canonical-pin.json'), 'referenceMode': pin['referenceMode'],
        'canonicalPath': pin['canonicalPath'], 'canonicalSha256': pin['canonicalSha256'],
        'document': completed[0], 'criticalRows': score['criticalRows'],
        'mandatoryMissingRows': score['mandatoryMissingRows'],
        'wholeSetPercentage': None, 'finalQualified': False})

new_records = []
for folder, expected, count, filename, finding in (
    ('search-basic-r05-tiles', '54c23006ba114f83bb74349a6ace7d7691ee333588eb03802e4ca4fcd8d26294', 33,
     'source-search-basic-r05-native-readability.json',
     'All 25 diagrams and one layout were inspected through 33 lossless original-scale tiles. Several English identifiers and numeric error codes wrap internally. Opaque edge labels are readable; no missing crop or connection was observed. The author is revising geometry in a fresh draft.'),
    ('assisted-search-basic-r03-tiles', 'ab84038bc61a3ed4fac0093067c0c28007d75a72dd5f48528d8887043ead8bec', 6,
     'assisted-search-basic-r03-root-partial-native.json',
     'Root inspected only the first six diagram tiles. Internal token wrapping remains. Separate delivery_tools evidence covers the remaining tiles; this root record does not claim that review.'),
):
    inventory_path = report/'visual-review'/folder/'inventory.json'
    inventory = load(inventory_path)
    if inventory['documentSha256'] != expected or len(inventory['captures']) < count:
        raise ValueError('Actual native-review inventory differs')
    captures = inventory['captures'][:count]
    for capture in captures:
        if sha(Path(capture['path'])) != capture['sha256'] or not capture['pixelsEqualToOriginalRegion']:
            raise ValueError('Actually inspected pixels changed')
    path = report/'visual-review'/filename
    fresh(path, {'schema': 'reverse-agent-native-visual-review/1', 'reviewedAt': created,
        'documentId': inventory['documentId'], 'referenceMode': inventory['referenceMode'],
        'documentSha256': expected, 'sourceSnapshotSha256': inventory['sourceSnapshotSha256'],
        'inventorySha256': sha(inventory_path), 'reviewScope': 'DISPLAY_READABILITY_ONLY',
        'reviewer': '/root', 'reviewedImages': [{**c, 'actuallyReviewed': True} for c in captures],
        'modesReviewed': [], 'findings': [finding], 'approved': False,
        'originalApplicationExecuted': False, 'pixelEquivalenceToRunningApplicationVerified': False,
        'formalQualityGatePassed': False})
    new_records.append(path.relative_to(report).as_posix())

freeze = load(evaluation/'fixed-rubric'/'seal.json')
if freeze is None:
    raise ValueError('Fixed rubric freeze missing')
assisted_entries = []
for item in results[1:]:
    batch = report/item['batch']
    assisted_entries.append({'documentId': item['document']['documentId'], 'batchPath': str(batch.resolve()),
        'normalizationPath': str((batch/'defect-normalization.json').resolve()),
        'canonicalPath': item['canonicalPath'], 'canonicalSha256': item['canonicalSha256'],
        'roundId': batch.name})
fresh(evaluation/'selection-assisted-partial-r01.json', {
    'schema': 'independent-evaluation-batch-selection/1', 'projectId': 'test-project1',
    'profile': 'CSharp_ASPNET', 'referenceMode': 'training-assisted', 'createdAt': created,
    'rubricSha256': freeze['effectiveItemsSha256'],
    'sourceSnapshotSha256': 'e76a6c40e8927011fff9145d5f5ab2fa94ad89acefc9a03bbad0cbf09b85a0e7',
    'documents': assisted_entries})

agent = report.parents[1]
input_root = agent/'input'
input_summary = []
for folder in sorted(input_root.iterdir()):
    if not folder.is_dir():
        continue
    files = [p for p in folder.rglob('*') if p.is_file()]
    extensions = {}
    for path in files:
        extensions[path.suffix.lower() or '(none)'] = extensions.get(path.suffix.lower() or '(none)', 0)+1
    input_summary.append({'directory': str(folder.resolve()), 'files': len(files),
        'bytes': sum(p.stat().st_size for p in files), 'extensions': extensions})
fresh(report/'checkpoints/status-1245.json', {'schema': 'reverse-agent-status-checkpoint/1',
    'createdAt': created, 'deadline': '2026-10-13T20:15:58Z', 'formalDocumentResults': results,
    'wholeSetScore': None, 'qualifiedDocumentsPublished': 0, 'rootActualImagesViewed': 49,
    'rootNewInspectionRecords': new_records,
    'deliveryNativeBasicReview': 'delivery/assisted-basic-r03-native-geometry-review.json',
    'deliveryTableReview': 'delivery/assisted-tables-r01-final-qa.json',
    'inputNextStageMetadataOnly': input_summary,
    'inputSpecificationsStarted': False, 'generalizationVerified': False,
    'modelWeightTrainingPerformed': False, 'originalApplicationExecuted': False})
manifest_path = report/'run-manifest.json'
fresh(report/'checkpoints/run-manifest-before-1245.json', load(manifest_path))
manifest = load(manifest_path)
manifest['updatedAt'] = created
manifest['status'] = 'PARTIAL_FORMAL_SCORES_ACCEPTED_REMAINING_DRAFTS_AND_NATIVE_GEOMETRY_IN_PROGRESS'
manifest['formalScore'] = None
manifest['formalDocumentResults'] = results
manifest['currentFormalGrading'] = {'status': 'THREE_DOCUMENT_SCORES_ACCEPTED',
    'formalScore': None, 'wholeSetComplete': False, 'qualified': False,
    'sourceOnlyCompletedDocuments': 1, 'trainingAssistedCompletedDocuments': 2}
manifest['nativeVisualReview']['records'].extend(new_records)
manifest['nativeVisualReview']['imagesActuallyReviewed'] = 49
manifest['nativeVisualReview']['reviewer'] = '/root'
manifest['nativeVisualReview']['approved'] = False
manifest['nativeVisualReview']['separateDeliveryRecords'] = [
    'delivery/assisted-basic-r03-native-geometry-review.json', 'delivery/assisted-tables-r01-final-qa.json']
manifest['activeGenerationJobs'] = ['source-only/search-basic-08', 'source-only/remaining-register-basic-05',
    'source-only/remaining-register-detail-04', 'source-only/remaining-repair-04-and-independent-reviews',
    'training-assisted/remaining-r11-revisions-and-independent-reviews',
    'training-assisted/search-basic-r04-geometry', 'training-assisted/registration-basic-next-geometry']
manifest['nextInputStage'] = {'metadataInventory': 'checkpoints/status-1245.json',
    'status': 'WAITING_FOR_PILOT_AND_GENERALIZATION_STAGES', 'specificationsStarted': False}
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'acceptedFormalDocumentScores': [r['document']['percentage'] for r in results],
    'rootActuallyViewedImages': 49, 'globalPercentage': None}, ensure_ascii=False))
