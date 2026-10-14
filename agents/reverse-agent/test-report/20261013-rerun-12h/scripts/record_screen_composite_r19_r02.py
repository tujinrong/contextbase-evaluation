"""Bind existing actual inspections to one immutable r19 static document review."""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import json
from PIL import Image
from contextbase.ai import capsule

REPORT = Path(__file__).resolve().parents[1]
REPO = REPORT.parents[3]
CAP_SHA = 'e76a6c40e8927011fff9145d5f5ab2fa94ad89acefc9a03bbad0cbf09b85a0e7'
RUNTIME_SHA = '56c8d76fdbab9717a7bfa3f2b1bdc9800b7b03cdc7d495d1d3f920e528598308'
TRACKED_PINS = {}
RUNTIME_ROOTS = {}
MODES = {'initial', 'normal', 'error', 'view-edit'}

def safe(path):
    path = capsule.safe_path(Path(path))
    if not path.is_relative_to(REPO):
        raise ValueError('Evidence leaves the repository')
    return path

def sha(path):
    path = safe(path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if str(path) in TRACKED_PINS and TRACKED_PINS[str(path)] != digest:
        raise ValueError('Evidence changed during verification: ' + str(path))
    TRACKED_PINS[str(path)] = digest
    return digest

def load(path):
    path = safe(path)
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if str(path) in TRACKED_PINS and TRACKED_PINS[str(path)] != digest:
        raise ValueError('Evidence changed before metadata read: ' + str(path))
    TRACKED_PINS[str(path)] = digest
    return json.loads(raw.decode('utf-8-sig'))

def pinned(path, digest):
    if sha(path) != digest:
        raise ValueError('Changed evidence: ' + str(path))

def verify_pin_map(pins, required):
    if not isinstance(pins, dict) or not pins:
        raise ValueError('Nonempty immutable input pins required')
    normalized = {}
    for path, digest in pins.items():
        key = str(safe(path))
        if key in normalized or not isinstance(digest, str) or len(digest) != 64:
            raise ValueError('Duplicate or invalid immutable pin')
        pinned(path, digest)
        normalized[key] = digest
    for path, digest in required.items():
        if normalized.get(str(safe(path))) != digest:
            raise ValueError('Required native evidence absent from before/after pins')

def verify_runtime(root, files):
    root = safe(root)
    actual = {p.relative_to(root).as_posix(): sha(p) for p in root.rglob('*')
              if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
    if len(actual) != 128 or actual != files:
        raise ValueError('Frozen runtime membership or bytes changed')
    RUNTIME_ROOTS[str(root)] = dict(files)

def recheck_all_inputs():
    for path, digest in list(TRACKED_PINS.items()):
        pinned(path, digest)
    for root, files in list(RUNTIME_ROOTS.items()):
        verify_runtime(root, files)

def tile_review(path, digest, canonical, document_id):
    canonical = safe(canonical)
    pinned(path, digest)
    qa = load(path)
    if (qa['schema'] != 'screen-native-review/2' or qa['status'] != 'PASS_NATIVE_GEOMETRY_ONLY'
        or qa['findings'] or qa['documentId'] != document_id
        or qa['documentSha256'] != sha(canonical) or safe(qa['canonicalDocumentPath']) != canonical
        or qa['frozenRuntimeAll128FilesUnchanged'] is not True
        or qa['inputBeforeAfterPinsUnchanged'] is not True
        or qa['exactRgbaComparisonAndCompletePixelCoverage'] is not True
        or qa['rendererRuntimeReceiptSha256'] != RUNTIME_SHA):
        raise ValueError('Incomplete r19 native review')
    for field in ('actuallyViewedTileCount', 'actuallyViewedImageCount'):
        if type(qa[field]) is not int or qa[field] <= 0:
            raise ValueError('Positive actual inspection counts required')
    pinned(qa['rendererRuntimeReceipt'], RUNTIME_SHA)
    runtime = load(qa['rendererRuntimeReceipt'])
    root = safe(runtime['destination'])
    verify_runtime(root, runtime['files'])
    pinned(qa['renderPins'], qa['renderPinsSha256'])
    pins = load(qa['renderPins'])
    if (pins['documentId'] != document_id or pins['sourceSha256'] != sha(canonical)
        or safe(pins['source']) != canonical or pins['sourceSnapshotManifestSha256'] != CAP_SHA
        or pins['referenceMode'] != 'training-assisted' or pins['inputBeforeAfterUnchanged'] is not True
        or pins['rendererRuntimeReceiptSha256'] != RUNTIME_SHA
        or safe(pins['rendererRuntimeReceipt']) != safe(qa['rendererRuntimeReceipt'])
        or pins['rendererRuntimeFileCount'] != 128):
        raise ValueError('Native render belongs to another canonical or runtime')
    pinned(qa['tileInventory'], qa['tileInventorySha256'])
    inventory = load(qa['tileInventory'])
    if (inventory['schema'] != 'native-review-tile-inventory/1'
        or inventory['documentId'] != document_id or inventory['documentSha256'] != sha(canonical)
        or inventory['referenceMode'] != 'training-assisted'
        or inventory['sourceSnapshotSha256'] != CAP_SHA
        or inventory['renderPinsSha256'] != qa['renderPinsSha256']
        or not isinstance(inventory['captures'], list) or not inventory['captures']
        or len(inventory['captures']) != len(qa['captures'])):
        raise ValueError('Incomplete or mismatched native tile inventory')
    required = {str(canonical): sha(canonical), str(safe(qa['renderPins'])): qa['renderPinsSha256'],
                str(safe(qa['tileInventory'])): qa['tileInventorySha256'],
                str(safe(qa['rendererRuntimeReceipt'])): RUNTIME_SHA}
    artifact_map = {}
    for artifact in pins['artifacts']:
        relative = Path(artifact['path'])
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Invalid rendered artifact path')
        target = safe(safe(qa['renderPins']).parent / relative)
        if not target.is_relative_to(safe(qa['renderPins']).parent) or str(target) in artifact_map:
            raise ValueError('Duplicate or escaped rendered artifact')
        pinned(target, artifact['sha256'])
        artifact_map[str(target)] = artifact['sha256']
    required.update(artifact_map)
    expected_originals = {}
    for record in pins['diagrams'] + pins['layouts']:
        target = safe(safe(qa['renderPins']).parent / (record['id'] + '.png'))
        png = record['png']
        if (record['status'] != 'PASS' or str(target) in expected_originals
            or artifact_map.get(str(target)) != png['sha256']):
            raise ValueError('Missing or duplicate canonical diagram/layout artifact')
        expected_originals[str(target)] = (png['sha256'], [png['width'], png['height']])
    if not expected_originals or qa['diagramCount'] != len(pins['diagrams']) or qa['layoutCount'] != len(pins['layouts']):
        raise ValueError('Positive complete diagram/layout set required')
    originals, images = {}, []
    core = {'imageId', 'originalPath', 'originalSha256', 'path', 'sha256', 'sourceRectangle',
            'wholeOriginalSize', 'scale', 'pixelsEqualToOriginalRegion'}
    for index, (entry, base) in enumerate(zip(qa['captures'], inventory['captures'])):
        if (not core.issubset(base) or any(entry.get(key) != value for key, value in base.items())
            or type(entry['captureIndexZeroBased']) is not int or entry['captureIndexZeroBased'] != index
            or entry['actuallyViewed'] is not True or entry['actuallyViewedBy'] != 'delivery_tools'
            or entry['pixelsEqualToOriginalRegion'] is not True or type(entry['scale']) not in (int, float)
            or entry['scale'] != 1):
            raise ValueError('Tile inventory order or explicit actual inspection differs')
        original_key, tile_key = str(safe(entry['originalPath'])), str(safe(entry['path']))
        if expected_originals.get(original_key) != (entry['originalSha256'], entry['wholeOriginalSize']):
            raise ValueError('Tile original is outside the complete canonical image set')
        pinned(entry['originalPath'], entry['originalSha256'])
        pinned(entry['path'], entry['sha256'])
        required[tile_key] = entry['sha256']
        rect = entry['sourceRectangle']
        if any(type(rect[key]) is not int for key in ('x', 'y', 'width', 'height')):
            raise ValueError('Integer source rectangles required')
        box = (rect['x'], rect['y'], rect['x'] + rect['width'], rect['y'] + rect['height'])
        with Image.open(safe(entry['originalPath'])) as original, Image.open(safe(entry['path'])) as tile:
            if (list(original.size) != entry['wholeOriginalSize']
                or tile.size != (rect['width'], rect['height'])
                or original.convert('RGBA').crop(box).tobytes() != tile.convert('RGBA').tobytes()):
                raise ValueError('Tile does not match exact original RGBA pixels')
        originals.setdefault(original_key, (entry['wholeOriginalSize'], []))[1].append(box)
        images.append({**entry, 'actuallyReviewed': True, 'reviewer': '/root/delivery_tools',
                       'inspectionEvidenceField': 'actuallyViewed',
                       'inheritedActualInspectionRecord': str(safe(path)),
                       'inheritedActualInspectionRecordSha256': digest})
    if len({str(safe(e['path'])) for e in images}) != len(images) or set(originals) != set(expected_originals):
        raise ValueError('Duplicate tiles or omitted canonical diagram/layout')
    for (width, height), boxes in originals.values():
        xs = sorted({0, width, *[v for b in boxes for v in (b[0], b[2])]})
        for x0, x1 in zip(xs, xs[1:]):
            if x0 < 0 or x1 > width or x1 <= x0:
                raise ValueError('Tile bounds leave original')
            covered = 0
            for y0, y1 in sorted((b[1], b[3]) for b in boxes if b[0] <= x0 and b[2] >= x1):
                if y0 < 0 or y1 > height or y1 <= y0 or y0 > covered:
                    raise ValueError('Native pixel coverage gap')
                covered = max(covered, y1)
            if covered != height:
                raise ValueError('Native pixel coverage gap')
    if len(images) != qa['actuallyViewedTileCount'] or len(originals) != qa['actuallyViewedImageCount']:
        raise ValueError('Native inspection counts differ')
    verify_pin_map(pins['inputPins'], {str(canonical): sha(canonical), str(safe(qa['rendererRuntimeReceipt'])): RUNTIME_SHA})
    verify_pin_map(qa['beforeAfterPins'], required)
    recheck_all_inputs()
    return images

def main():
    parser = argparse.ArgumentParser()
    for name in ('state-pin', 'capture', 'root-inspection', 'native-review', 'source-review', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('parent-sha256', 'document-id', 'root-inspection-sha256', 'native-review-sha256', 'source-review-sha256'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    pin, capture = load(args.state_pin), load(args.capture)
    pinned(args.root_inspection, args.root_inspection_sha256)
    actual = load(args.root_inspection)
    canonical = safe(pin['canonicalMarkdown'])
    pinned(canonical, args.parent_sha256)
    if (pin['documentId'] != args.document_id or pin['parentSha256'] != args.parent_sha256
        or pin['mode'] != 'training-assisted' or pin['capsuleManifestSha256'] != CAP_SHA
        or pin['independentReviewApproved'] is not True or pin['findings'] or pin['unresolved']
        or capture['documentId'] != args.document_id or capture['documentSha256'] != args.parent_sha256
        or capture['exportPinSha256'] != sha(args.state_pin) or capture['sourceSnapshotSha256'] != CAP_SHA
        or capture['javaScriptEnabled'] is not False or capture['externalRequests']
        or capture['inputHashesUnchanged'] is not True or capture['originalApplicationExecuted'] is not False
        or actual['documentId'] != args.document_id or actual['documentSha256'] != args.parent_sha256
        or actual['captureReceiptSha256'] != sha(args.capture) or actual['reviewer'] != '/root'
        or actual['approved'] is not True or actual['findings']):
        raise ValueError('State capture or actual root inspection is not bound and approved')
    for path_key, hash_key in [('projectionFile', 'projectionSha256'), ('independentReview', 'independentReviewSha256'),
                              ('result', 'resultSha256'), ('before', 'beforeSha256'), ('after', 'afterSha256')]:
        pinned(pin[path_key], pin[hash_key])
    if len(capture['images']) != 4 or {e['stateId'] for e in capture['images']} != MODES:
        raise ValueError('Exactly four states required')
    expected = {(e['stateId'], e['path'], e['sha256']) for e in capture['images']}
    if (len(actual['reviewedImages']) != 4
        or {(e['stateId'], e['path'], e['sha256']) for e in actual['reviewedImages']} != expected
        or any(e['actuallyReviewed'] is not True or e['scale'] != 1 for e in actual['reviewedImages'])):
        raise ValueError('Every captured state needs an actual original-scale root inspection')
    for e in capture['images']:
        for path_key, hash_key in [('path', 'sha256'), ('aiHtmlPath', 'aiHtmlSha256'), ('sanitizedHtmlPath', 'sanitizedHtmlSha256')]:
            pinned(e[path_key], e[hash_key])
        if e['sanitizerRemoved'] or e['textAndControlStructureUnchanged'] is not True or e['scale'] != 1:
            raise ValueError('State content changed or was scaled')
    tiles = tile_review(args.native_review, args.native_review_sha256, canonical, args.document_id)
    pinned(args.source_review, args.source_review_sha256)
    source_prior = load(args.source_review)
    snapshot = REPO / 'agents/reverse-agent/.tmp/20261013-rerun-12h/training-assisted/snapshot'
    source = capsule.verify(snapshot)
    pinned(snapshot / 'manifest.json', CAP_SHA)
    source_hashes = {e['path']: e['sha256'] for e in source['files']}
    resources = []
    for e in source_prior['reviewedSourceResources']:
        pinned(e['path'], e['sha256'])
        relative = safe(e['path']).relative_to(REPO / 'test-project1/srcs/CSharp_ASPNET').as_posix()
        if e['actuallyRead'] is not True or source_hashes[relative] != e['sha256']:
            raise ValueError('Source resource was not actually read or changed')
        resources.append({**e, 'actualReadEvidence': str(safe(args.source_review)),
                          'actualReadEvidenceSha256': args.source_review_sha256, 'newSourceReadPerformed': False})
    if not resources:
        raise ValueError('Actual source-resource inspection required')
    result = {'schema': 'reverse-agent-native-visual-review/1', 'reviewedAt': datetime.now(timezone.utc).isoformat(),
              'reviewer': '/root and /root/delivery_tools', 'referenceMode': 'training-assisted',
              'documentId': args.document_id, 'canonicalDocumentPath': str(canonical),
              'documentSha256': args.parent_sha256, 'sourceSnapshotSha256': CAP_SHA,
              'reviewScope': 'STATIC_PROJECTION_VS_SOURCE_RESOURCES', 'approved': True,
              'completeDocumentVisualReview': True, 'documentBodyTilesActuallyReviewed': False, 'findings': [], 'fourStateMeaningReviewComplete': True,
              'reviewedImages': tiles + actual['reviewedImages'], 'reviewedSourceResources': resources,
              'modesReviewed': sorted(MODES), 'rootActuallyViewedNewStateImages': 4,
              'deliveryActuallyViewedTiles': len(tiles), 'independentMeaningReviewSha256': pin['independentReviewSha256'],
              'projectionSha256': pin['projectionSha256'], 'captureReceiptSha256': sha(args.capture),
              'rootInspectionSha256': args.root_inspection_sha256, 'inheritedDiagramReviewSha256': args.native_review_sha256,
              'originalApplicationExecuted': False, 'pixelEquivalenceToRunningApplicationVerified': False,
              'formalQualityGatePassed': False, 'finalQualified': False, 'published': False,
              'limitations': ['Static offline source-backed projection only; original application was not executed.',
                              'Delivery diagram/layout tile inspections were inherited; exact full diagram/layout pixels were reverified. Document-body tiles are hashed as artifacts but not newly claimed as actually viewed.']}
    output = safe(args.output)
    if not output.is_relative_to(REPORT / 'visual-review') or output.exists():
        raise ValueError('Fresh visual evidence output required')
    recheck_all_inputs()
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'path': str(output), 'sha256': sha(output), 'images': len(result['reviewedImages']), 'finalQualified': False}))

if __name__ == '__main__':
    main()
