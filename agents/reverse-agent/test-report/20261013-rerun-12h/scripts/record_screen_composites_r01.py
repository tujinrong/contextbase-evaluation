"""Seal actual team inspections; never alter prose, HTML, images, or old evidence."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import sys
from PIL import Image
from contextbase.ai import capsule

report = Path(__file__).resolve().parents[1]
agent = report.parents[1]
repo = agent.parents[1]
sys.path.insert(0, str(report / 'evaluator-only'))
import grader

def load(path):
    path = Path(path).absolute()
    grader.safe(path, repo)
    return json.loads(path.read_text(encoding='utf-8-sig'))

def digest(path):
    path = Path(path).absolute()
    grader.safe(path, repo)
    return hashlib.sha256(path.read_bytes()).hexdigest()

def pinned(path, expected):
    if digest(path) != expected:
        raise ValueError(f'Changed evidence: {path}')

def write_fresh(path, record):
    if path.exists():
        raise FileExistsError(path)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

created = datetime.now(timezone.utc).isoformat()
snapshot = agent / '.tmp/20261013-rerun-12h/training-assisted/snapshot'
manifest = capsule.verify(snapshot)
snapshot_sha = digest(snapshot / 'manifest.json')
assert snapshot_sha == 'e76a6c40e8927011fff9145d5f5ab2fa94ad89acefc9a03bbad0cbf09b85a0e7'
source_hashes = {e['path']: e['sha256'] for e in manifest['files']}

def verified_tiles(qa_path, qa_sha, canonical, doc_id):
    pinned(qa_path, qa_sha)
    qa = load(qa_path)
    if (qa['status'] != 'PASS_NATIVE_GEOMETRY_ONLY' or qa['findings'] or
        qa['documentId'] != doc_id or qa['documentSha256'] != digest(canonical) or
        qa['sourceSnapshotManifestSha256'] != snapshot_sha or
        qa['referenceMode'] != 'training-assisted' or
        qa['frozenRuntimeAll126FilesUnchanged'] is not True or
        qa['inputBeforeAfterPinsUnchanged'] is not True or
        qa['exactRgbaComparisonAndCompletePixelCoverage'] is not True):
        raise ValueError('Native QA is incomplete or belongs to another document')
    pins_path = Path(qa['renderPins'])
    pinned(pins_path, qa['renderPinsSha256'])
    pins = load(pins_path)
    if (pins['documentId'] != doc_id or pins['sourceSha256'] != digest(canonical) or
        Path(pins['source']).absolute() != canonical or
        not str(canonical).replace('\\','/').endswith('/' + pins['canonicalDocumentPath'].replace('\\','/')) or
        pins['sourceSnapshotManifestSha256'] != snapshot_sha or
        pins['inputBeforeAfterUnchanged'] is not True):
        raise ValueError('Render/document binding differs')
    runtime_path = Path(qa['rendererRuntimeReceipt'])
    pinned(runtime_path, qa['rendererRuntimeReceiptSha256'])
    runtime = load(runtime_path)
    runtime_root = Path(runtime['destination'])
    for relative, expected in runtime['files'].items():
        pinned(runtime_root / relative, expected)
    assert len(runtime['files']) == 126
    pinned(qa['tileInventory'], qa['tileInventorySha256'])
    index_path = Path(qa['actuallyViewedIndexRecord'])
    if not index_path.is_absolute():
        index_path = repo / index_path
    pinned(index_path, qa['actuallyViewedIndexRecordSha256'])
    images = []
    originals = {}
    for e in qa['captures']:
        if (e['actuallyReviewed'] is not True or e['pixelsEqualToOriginalRegion'] is not True or
            e['scale'] != 1 or e['geometryFindings']):
            raise ValueError('Unreviewed tile or unresolved native finding')
        pinned(e['originalPath'], e['originalSha256'])
        pinned(e['path'], e['sha256'])
        rect = e['sourceRectangle']
        box = (rect['x'], rect['y'], rect['x'] + rect['width'], rect['y'] + rect['height'])
        with Image.open(e['originalPath']) as original, Image.open(e['path']) as tile:
            if (list(original.size) != e['wholeOriginalSize'] or
                tile.size != (rect['width'], rect['height']) or
                original.convert('RGBA').crop(box).tobytes() != tile.convert('RGBA').tobytes()):
                raise ValueError('Tile is not the exact original RGBA region')
        originals.setdefault(e['originalPath'], (e['wholeOriginalSize'], []))[1].append(box)
        images.append({**e, 'reviewer': '/root/delivery_tools',
                       'inheritedActualInspectionRecord': str(qa_path),
                       'inheritedActualInspectionRecordSha256': qa_sha})
    for size, boxes in originals.values():
        width, height = size
        xs = sorted({0, width, *[v for box in boxes for v in (box[0], box[2])]})
        for x0, x1 in zip(xs, xs[1:]):
            if x0 < 0 or x1 > width:
                raise ValueError('Tile bounds exceed original')
            intervals = sorted((b[1], b[3]) for b in boxes if b[0] <= x0 and b[2] >= x1)
            covered = 0
            for y0, y1 in intervals:
                if y0 < 0 or y1 > height or y0 > covered:
                    raise ValueError('Original pixels have a coverage gap')
                covered = max(covered, y1)
            if covered != height:
                raise ValueError('Original pixels have a coverage gap')
    if len(images) != qa['actuallyViewedTileCount'] or len(originals) != qa['actuallyViewedImageCount']:
        raise ValueError('Native review counts differ')
    return images

def resources_from_prior(path):
    prior = load(path)
    result = []
    for e in prior['reviewedSourceResources']:
        pinned(e['path'], e['sha256'])
        relative = Path(e['path']).relative_to(repo / 'test-project1/srcs/CSharp_ASPNET').as_posix()
        if source_hashes[relative] != e['sha256'] or e.get('actuallyRead') is not True:
            raise ValueError('Prior actual source read does not bind the fixed capsule')
        result.append({**e, 'actualReadEvidence': str(path), 'actualReadEvidenceSha256': digest(path),
                       'sha256ReverifiedAt': created, 'newSourceReadPerformed': False})
    return result

search_pin_path = report / 'training-assisted/state-detail-search-r02-v02-root-normalized-pin.json'
search_pin = load(search_pin_path)
capture_path = report / 'render/assisted-search-detail-r02-state-r02/capture.json'
capture = load(capture_path)
canonical = Path(search_pin['canonicalMarkdown']).absolute()
if (search_pin['independentReviewApproved'] is not True or search_pin['findings'] or search_pin['unresolved'] or
    search_pin['capsuleManifestSha256'] != snapshot_sha or search_pin['parentSha256'] != digest(canonical) or
    capture['exportPinSha256'] != digest(search_pin_path) or capture['documentSha256'] != digest(canonical) or
    capture['externalRequests'] or capture['javaScriptEnabled'] is not False or capture['inputHashesUnchanged'] is not True):
    raise ValueError('Search detail state capture is not approved and exactly bound')
for path_key, hash_key in [('projectionFile','projectionSha256'), ('independentReview','independentReviewSha256'),
                          ('result','resultSha256'), ('before','beforeSha256'), ('after','afterSha256')]:
    pinned(search_pin[path_key], search_pin[hash_key])
states = []
for e in capture['images']:
    for path_key, hash_key in [('path','sha256'), ('aiHtmlPath','aiHtmlSha256'),
                              ('sanitizedHtmlPath','sanitizedHtmlSha256')]:
        pinned(e[path_key], e[hash_key])
    if e['sanitizerRemoved'] or e['textAndControlStructureUnchanged'] is not True:
        raise ValueError('State projection text/control changed')
    states.append({**e, 'actuallyReviewed': True, 'reviewer': '/root',
                   'viewMethod': 'view_image original detail', 'scale': 1})
assert {e['stateId'] for e in states} == {'initial','normal','error','view-edit'}
search_qa_path = report / 'delivery/assisted-search-detail-r04-delivery-r18-native-qa.json'
search_tiles = verified_tiles(search_qa_path,
    '457f9c7680fc8c4447bded4bdc01218a25d01b55a4b735e39f50175f446a7c5f',
    canonical, search_pin['documentId'])
common = {'schema':'reverse-agent-native-visual-review/1', 'reviewedAt':created,
    'reviewer':'/root and /root/delivery_tools', 'referenceMode':'training-assisted',
    'sourceSnapshotSha256':snapshot_sha, 'reviewScope':'STATIC_PROJECTION_VS_SOURCE_RESOURCES',
    'approved':True, 'completeDocumentVisualReview':True, 'findings':[],
    'fourStateMeaningReviewComplete':True, 'originalApplicationExecuted':False,
    'pixelEquivalenceToRunningApplicationVerified':False, 'formalQualityGatePassed':False,
    'finalQualified':False, 'published':False,
    'limitations':['Static offline projection only; demonstration values are labelled.',
                  'Original application, Razor, source JavaScript, SQL, and HTTP requests were not executed.',
                  'Razor/TagHelper runtime output and pixel equivalence to a running application remain unavailable.',
                  'Inherited tile inspections were actually performed by the delivery agent; root reverified their unchanged exact RGBA coverage.']}
search_target = report / 'visual-review/assisted-search-detail-r02-states-root-native-r01.json'
search_record = {**common, 'documentId':search_pin['documentId'], 'canonicalDocumentPath':str(canonical),
    'documentSha256':digest(canonical), 'reviewedImages':search_tiles + states,
    'reviewedSourceResources':resources_from_prior(report / 'visual-review/assisted-search-basic-r04-states-root-native-r01.json'),
    'modesReviewed':['initial','normal','error','view-edit','viewer','staff','admin'],
    'independentMeaningReviewSha256':search_pin['independentReviewSha256'],
    'projectionSha256':search_pin['projectionSha256'], 'captureReceiptSha256':digest(capture_path),
    'inheritedDiagramReviewSha256':digest(search_qa_path),
    'rootActuallyViewedNewStateImages':4, 'deliveryActuallyViewedTiles':len(search_tiles),
    'checks':['All four complete state PNGs were actually viewed by root at original size before sealing this receipt.',
              'Fields, all eleven result columns, pager, era/date/status, warning/error panel, and role-dependent links are readable.',
              'view-edit contains three labelled same-search role comparison panels; all three were inspected.',
              'The error example explicitly discloses its pre-JavaScript input snapshot; no running-application behavior is inferred.',
              'All canonical diagram/layout pixels were reviewed by delivery at original scale, with exact RGBA and complete coverage reverified by root.']}
write_fresh(search_target, search_record)

registration_prior_path = report / 'visual-review/assisted-registration-basic-r05-states-root-native-r01.json'
prior = load(registration_prior_path)
if prior['stateOnlyApproved'] is not True or prior['findings'] or prior['fourStateMeaningReviewComplete'] is not True:
    raise ValueError('Registration four-state actual inspection is incomplete')
canonical = Path(prior['canonicalDocumentPath']).absolute()
pinned(canonical, prior['documentSha256'])
for e in prior['reviewedImages']:
    if e['actuallyReviewed'] is not True:
        raise ValueError('Registration state was not actually inspected')
    pinned(e['path'], e['sha256'])
registration_qa_path = report / 'delivery/assisted-registration-basic-r07-delivery-r18-native-qa.json'
registration_tiles = verified_tiles(registration_qa_path,
    '68fd61d7f911154cfc82489e6272a0b9eeedf33bb0bde4853193d14f385fbf18',
    canonical, prior['documentId'])
registration_target = report / 'visual-review/assisted-registration-basic-r05-complete-static-r02.json'
registration_record = {**prior, **common, 'reviewedImages':registration_tiles + prior['reviewedImages'],
    'reviewedSourceResources':resources_from_prior(registration_prior_path),
    'inheritedStateReviewPath':str(registration_prior_path), 'inheritedStateReviewSha256':digest(registration_prior_path),
    'inheritedDiagramReviewSha256':digest(registration_qa_path),
    'rootActuallyViewedNewStateImages':0, 'deliveryActuallyViewedTiles':len(registration_tiles),
    'stateOnlyApproved':False,
    'checks':prior['checks'] + ['All 42 diagrams and two embedded layouts passed the fresh r18 native review; root reverified all 46 exact RGBA tiles and complete pixel coverage.']}
write_fresh(registration_target, registration_record)

run_path = report / 'run-manifest.json'
run = load(run_path)
write_fresh(report / 'checkpoints/run-manifest-before-screen-composites-r01.json', run)
run['nativeVisualReview']['records'].extend([search_target.relative_to(report).as_posix(), registration_target.relative_to(report).as_posix()])
run['nativeVisualReview'].update(imagesActuallyReviewed=107, approved=False)
run['screenStateReviewProgress'].update(trainingAssistedDetailSearch=search_target.relative_to(report).as_posix(),
    trainingAssistedBasicRegistration=registration_target.relative_to(report).as_posix(),
    completedScreenDocuments=3, wholeSetComplete=False,
    completionScope='Three complete static document reviews with four-state independent meaning, canonical diagram/layout coverage, and source bindings; global qualification pending')
run['updatedAt'] = created
run_path.write_text(json.dumps(run, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'records':[{'path':str(p),'sha256':digest(p)} for p in (search_target,registration_target)],
                  'rootActualImagesViewed':107,'screenDocumentsComplete':3,'finalQualified':False}))
