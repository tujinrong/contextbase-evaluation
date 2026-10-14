"""Seal current scores and actual image inspections; never author specification prose."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json

report = Path(__file__).resolve().parents[1]
created = datetime.now(timezone.utc).isoformat()
load = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def fresh(path, value):
    if path.exists():
        raise ValueError('Immutable evidence already exists: ' + str(path))
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

evaluation = report/'evaluator-only'
if sha(evaluation/'grader.py') != '83390d439db12119fa7f82cfb48672105488ccb748ca960c68ff918112190bb7':
    raise ValueError('Frozen grader changed')
results = []
for name in ('source-m-code-category-r03-r6-n2', 'source-table-index-r04-r6',
             'source-m-code-r04-r6', 'assisted-m-code-category-r01-r6',
             'assisted-m-class-r02-r6', 'assisted-m-student-r01-r6',
             'assisted-m-code-r02-r6', 'assisted-table-index-r03-r6'):
    batch = evaluation/'batches'/name
    score, pin = load(batch/'score.json'), load(batch/'canonical-pin.json')
    complete = [d for d in score['documents'] if d['complete']]
    if len(complete) != 1 or complete[0]['documentId'] != pin['documentId']:
        raise ValueError('One completed document required')
    if score['total']['percentage'] is not None or sha(Path(pin['canonicalPath'])) != pin['canonicalSha256']:
        raise ValueError('Whole-set score must remain unknown; canonical must be unchanged')
    results.append({'batch': batch.relative_to(report).as_posix(),
        'scoreSha256': sha(batch/'score.json'), 'pinSha256': sha(batch/'canonical-pin.json'),
        'referenceMode': pin['referenceMode'], 'canonicalPath': pin['canonicalPath'],
        'canonicalSha256': pin['canonicalSha256'], 'document': complete[0],
        'criticalRows': score['criticalRows'], 'mandatoryMissingRows': score['mandatoryMissingRows'],
        'wholeSetPercentage': None, 'finalQualified': False})

inventory_path = report/'visual-review/search-basic-r07-tiles/inventory.json'
inventory = load(inventory_path)
capture = next(c for c in inventory['captures'] if Path(c['path']).name == 'diagram-013-0000-0000.png')
if sha(Path(capture['path'])) != capture['sha256'] or not capture['pixelsEqualToOriginalRegion']:
    raise ValueError('Actually inspected source native tile changed')
probe_path = report/'render/cluster-label-probe-r02/probe.json'
probe = load(probe_path)
images = [r for r in probe['results'] if r['case'] in ('stroke-only', 'overlay')]
if len(images) != 2 or any(sha(Path(r['path'])) != r['sha256'] for r in images):
    raise ValueError('Actually inspected nonsemantic probe images changed')
record_path = report/'visual-review/cluster-label-root-native-r01.json'
fresh(record_path, {'schema': 'reverse-agent-native-technical-review/1', 'reviewedAt': created,
    'reviewer': '/root', 'scope': 'NONSEMANTIC_CLUSTER_TITLE_DISPLAY_ONLY',
    'inventorySha256': sha(inventory_path), 'probeSha256': sha(probe_path),
    'sourceTile': {**capture, 'actuallyReviewed': True},
    'probeImages': [{**r, 'actuallyViewed': True} for r in images],
    'findings': ['Baseline title crosses a connecting edge; stroke-only did not resolve it. Overlay cleared crossing while retaining title position and text.'],
    'businessMeaningApproved': False, 'formalQualityGatePassed': False,
    'originalApplicationExecuted': False, 'published': False})
fresh(report/'render/cluster-label-probe-r01/incomplete-process-record.json', {
    'schema': 'reverse-agent-interrupted-technical-probe/1', 'recordedAt': created,
    'status': 'STOPPED_AFTER_STATIC_BASELINE_DYNAMIC_STYLE_STAGE_DID_NOT_COMPLETE',
    'ownedPythonPid': 111648, 'descendantsAfterStop': 0,
    'finalProbeResultProduced': False, 'finalQualified': False,
    'replacementProbe': 'render/cluster-label-probe-r02/probe.json'})

rubric = load(evaluation/'fixed-rubric/seal.json')
for mode, suffix, snapshot in (
    ('training-assisted', 'assisted', 'e76a6c40e8927011fff9145d5f5ab2fa94ad89acefc9a03bbad0cbf09b85a0e7'),
    ('source-only', 'source', '2f64e2211b1fcd7850203927fc75b5a7f2ce37457cc2afe88c8065d9f931273b')):
    entries=[]
    for item in results:
        if item['referenceMode'] != mode:
            continue
        batch = report/item['batch']
        entries.append({'documentId': item['document']['documentId'], 'batchPath': str(batch.resolve()),
            'normalizationPath': str((batch/'defect-normalization.json').resolve()),
            'canonicalPath': item['canonicalPath'], 'canonicalSha256': item['canonicalSha256'],
            'roundId': batch.name})
    fresh(evaluation/f'selection-{suffix}-partial-r03.json', {
        'schema': 'independent-evaluation-batch-selection/1', 'projectId': 'test-project1',
        'profile': 'CSharp_ASPNET', 'referenceMode': mode, 'createdAt': created,
        'rubricSha256': rubric['effectiveItemsSha256'], 'sourceSnapshotSha256': snapshot,
        'documents': entries})

fresh(report/'checkpoints/status-1405.json', {'schema': 'reverse-agent-status-checkpoint/1',
    'createdAt': created, 'deadline': '2026-10-13T20:15:58Z', 'formalDocumentResults': results,
    'wholeSetScore': None, 'qualifiedDocumentsPublished': 0, 'rootActualImagesViewed': 93,
    'engineeringValidation': 'engine/all-ai-r15-result.json', 'engineeringTestsPassed': 340,
    'fourStateScreenReviewsComplete': False, 'inputSpecificationsStarted': False,
    'generalizationVerified': False, 'modelWeightTrainingPerformed': False,
    'originalApplicationExecuted': False,
    'remainingEdgeLabelDisplayIssue': 'Mermaid public node width does not override its edge-label 200px default; insert-only derived layout prototype is in independent development.'})
manifest_path = report/'run-manifest.json'
manifest = load(manifest_path)
fresh(report/'checkpoints/run-manifest-before-1405.json', manifest)
manifest.update(updatedAt=created, formalScore=None, formalDocumentResults=results,
    currentFormalGrading={'status': 'EIGHT_DOCUMENT_SCORES_ACCEPTED', 'formalScore': None,
        'wholeSetComplete': False, 'qualified': False, 'sourceOnlyCompletedDocuments': 3,
        'trainingAssistedCompletedDocuments': 5})
manifest['nativeVisualReview']['records'].append(record_path.relative_to(report).as_posix())
manifest['nativeVisualReview'].update(imagesActuallyReviewed=93, approved=False)
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'acceptedDocuments': len(results), 'rootActuallyViewedImages': 93,
    'globalPercentage': None, 'percentages': [r['document']['percentage'] for r in results]}))
