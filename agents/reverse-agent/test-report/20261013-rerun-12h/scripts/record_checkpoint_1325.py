"""Record immutable evaluation and actual display inspections, without drafting specifications."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json

report = Path(__file__).resolve().parents[1]
load = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
created = datetime.now(timezone.utc).isoformat()

def fresh(path, value):
    if path.exists():
        raise ValueError('Existing immutable evidence: ' + str(path))
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

evaluation = report/'evaluator-only'
if sha(evaluation/'grader.py') != '83390d439db12119fa7f82cfb48672105488ccb748ca960c68ff918112190bb7':
    raise ValueError('Frozen grader changed')
results = []
for name in ('source-m-code-category-r03-r6-n2', 'source-table-index-r04-r6',
             'assisted-m-code-category-r01-r6', 'assisted-m-class-r02-r6',
             'assisted-m-student-r01-r6', 'assisted-m-code-r02-r6'):
    batch = evaluation/'batches'/name
    score, pin = load(batch/'score.json'), load(batch/'canonical-pin.json')
    completed = [d for d in score['documents'] if d['complete']]
    if len(completed) != 1 or completed[0]['documentId'] != pin['documentId']:
        raise ValueError('Expected one complete document')
    if score['total']['percentage'] is not None or sha(Path(pin['canonicalPath'])) != pin['canonicalSha256']:
        raise ValueError('Unknown whole-set score and unchanged canonical required')
    results.append({'batch': batch.relative_to(report).as_posix(), 'scoreSha256': sha(batch/'score.json'),
        'pinSha256': sha(batch/'canonical-pin.json'), 'referenceMode': pin['referenceMode'],
        'canonicalPath': pin['canonicalPath'], 'canonicalSha256': pin['canonicalSha256'],
        'document': completed[0], 'criticalRows': score['criticalRows'],
        'mandatoryMissingRows': score['mandatoryMissingRows'],
        'wholeSetPercentage': None, 'finalQualified': False})

records = []
for folder, expected, count, filename, status in (
    ('assisted-search-basic-r04-tiles', '5cc65ffde0748795ae10c5e02c6a5f4d785d85f9f4f17b7aeec091395918e8b9',
     10, 'assisted-search-basic-r04-root-partial-native.json', 'TOKEN_WRAP_REMAINS'),
    ('assisted-search-basic-r05-tiles', '5cc65ffde0748795ae10c5e02c6a5f4d785d85f9f4f17b7aeec091395918e8b9',
     28, 'assisted-search-basic-r05-root-native.json', 'DISPLAY_READABILITY_PASS'),
):
    inventory_path = report/'visual-review'/folder/'inventory.json'
    inventory = load(inventory_path)
    if inventory['documentSha256'] != expected or len(inventory['captures']) < count:
        raise ValueError('Actual inspected capture set differs')
    captures = inventory['captures'][:count]
    for capture in captures:
        if sha(Path(capture['path'])) != capture['sha256'] or not capture['pixelsEqualToOriginalRegion']:
            raise ValueError('Inspected image bytes changed')
    render_pins_path = report/'render'/folder.removesuffix('-tiles')/'render-pins.json'
    pins = load(render_pins_path)
    if sha(Path(pins['source'])) != expected:
        raise ValueError('Canonical changed since rendering')
    path = report/'visual-review'/filename
    fresh(path, {'schema': 'reverse-agent-native-visual-review/1', 'reviewedAt': created,
        'documentId': inventory['documentId'], 'referenceMode': inventory['referenceMode'],
        'documentSha256': expected, 'sourceSnapshotSha256': inventory['sourceSnapshotSha256'],
        'inventorySha256': sha(inventory_path), 'renderPinsSha256': sha(render_pins_path),
        'reviewScope': 'DISPLAY_READABILITY_ONLY', 'reviewer': '/root',
        'reviewedImages': [{**c, 'actuallyReviewed': True} for c in captures],
        'coverageComplete': count == len(inventory['captures']), 'displayStatus': status,
        'findings': [] if status == 'DISPLAY_READABILITY_PASS' else ['Identifiers and numeric codes wrap inside tokens in inspected diagrams.'],
        'modesReviewed': [], 'fourStateMeaningReviewComplete': False, 'formalQualityGatePassed': False,
        'originalApplicationExecuted': False, 'pixelEquivalenceToRunningApplicationVerified': False,
        'finalQualified': False, 'published': False})
    records.append(path.relative_to(report).as_posix())

probe_path = report/'render/mermaid-width-probe-r01/probe.json'
probe = load(probe_path)
probe_images = [r for r in probe['results'] if r['requestedWrappingWidth'] == 240]
if len(probe_images) != 3 or any(sha(Path(r['png'])) != r['pngSha256'] for r in probe_images):
    raise ValueError('Actually inspected configuration experiment changed')
probe_record = report/'visual-review/mermaid-width-probe-r01-root-native.json'
fresh(probe_record, {'schema': 'reverse-agent-configuration-native-review/1', 'reviewedAt': created,
    'reviewer': '/root', 'scope': 'NONSEMANTIC_CONFIG_EXPERIMENT_ONLY', 'probeSha256': sha(probe_path),
    'actuallyViewedImages': [{'path': r['png'], 'sha256': r['pngSha256'], 'role': r['role'],
        'requestedWrappingWidth': 240, 'actuallyReviewed': True} for r in probe_images],
    'displayStatus': 'INTACT_TOKENS_OBSERVED', 'businessMeaningApproved': False,
    'formalQualityGatePassed': False, 'published': False})
records.append(probe_record.relative_to(report).as_posix())

freeze = load(evaluation/'fixed-rubric/seal.json')
entries = []
for item in results:
    if item['referenceMode'] != 'training-assisted':
        continue
    batch = report/item['batch']
    entries.append({'documentId': item['document']['documentId'], 'batchPath': str(batch.resolve()),
        'normalizationPath': str((batch/'defect-normalization.json').resolve()),
        'canonicalPath': item['canonicalPath'], 'canonicalSha256': item['canonicalSha256'], 'roundId': batch.name})
fresh(evaluation/'selection-assisted-partial-r02.json', {
    'schema': 'independent-evaluation-batch-selection/1', 'projectId': 'test-project1',
    'profile': 'CSharp_ASPNET', 'referenceMode': 'training-assisted', 'createdAt': created,
    'rubricSha256': freeze['effectiveItemsSha256'],
    'sourceSnapshotSha256': 'e76a6c40e8927011fff9145d5f5ab2fa94ad89acefc9a03bbad0cbf09b85a0e7', 'documents': entries})
fresh(report/'checkpoints/status-1325.json', {'schema': 'reverse-agent-status-checkpoint/1',
    'createdAt': created, 'deadline': '2026-10-13T20:15:58Z', 'formalDocumentResults': results,
    'wholeSetScore': None, 'qualifiedDocumentsPublished': 0, 'rootActualImagesViewed': 90,
    'rootNewInspectionRecords': records, 'engineeringValidation': 'engine/all-ai-r14-result.json',
    'engineeringTestsPassed': 339, 'fourStateScreenReviewsComplete': False,
    'inputSpecificationsStarted': False, 'generalizationVerified': False,
    'modelWeightTrainingPerformed': False, 'originalApplicationExecuted': False})
manifest_path = report/'run-manifest.json'
manifest = load(manifest_path)
fresh(report/'checkpoints/run-manifest-before-1325.json', manifest)
manifest.update(updatedAt=created, formalScore=None, formalDocumentResults=results,
    currentFormalGrading={'status': 'SIX_DOCUMENT_SCORES_ACCEPTED', 'formalScore': None,
        'wholeSetComplete': False, 'qualified': False, 'sourceOnlyCompletedDocuments': 2,
        'trainingAssistedCompletedDocuments': 4},
    latestProtectedInputVerification='checkpoints/protected-inputs-04.json')
manifest['nativeVisualReview']['records'].extend(records)
manifest['nativeVisualReview'].update(imagesActuallyReviewed=90, approved=False)
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'acceptedDocumentPercentages': [r['document']['percentage'] for r in results],
    'rootActuallyViewedImages': 90, 'globalPercentage': None}))
