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
MODES = {'initial', 'normal', 'error', 'view-edit'}

def safe(path):
    path = capsule.safe_path(Path(path))
    if not path.is_relative_to(REPO):
        raise ValueError('Evidence leaves the repository')
    return path

def sha(path):
    return hashlib.sha256(safe(path).read_bytes()).hexdigest()

def load(path):
    return json.loads(safe(path).read_text(encoding='utf-8-sig'))

def pinned(path, digest):
    if sha(path) != digest:
        raise ValueError('Changed evidence: ' + str(path))

def tile_review(path, digest, canonical, document_id):
    pinned(path, digest)
    qa = load(path)
    if (qa['schema'] != 'screen-native-review/2' or qa['status'] != 'PASS_NATIVE_GEOMETRY_ONLY'
        or qa['findings'] or qa['documentId'] != document_id
        or qa['documentSha256'] != sha(canonical) or qa['referenceMode'] != 'training-assisted'
        or qa['sourceSnapshotManifestSha256'] != CAP_SHA
        or qa['frozenRuntimeAll128FilesUnchanged'] is not True
        or qa['inputBeforeAfterPinsUnchanged'] is not True
        or qa['exactRgbaComparisonAndCompletePixelCoverage'] is not True
        or qa['rendererRuntimeReceiptSha256'] != RUNTIME_SHA):
        raise ValueError('Incomplete r19 native review')
    pinned(qa['rendererRuntimeReceipt'], RUNTIME_SHA)
    runtime = load(qa['rendererRuntimeReceipt'])
    root = safe(runtime['destination'])
    actual = {p.relative_to(root).as_posix(): sha(p) for p in root.rglob('*')
              if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
    if len(actual) != 128 or actual != runtime['files']:
        raise ValueError('Frozen runtime membership or bytes changed')
    pinned(qa['renderPins'], qa['renderPinsSha256'])
    pins = load(qa['renderPins'])
    if (pins['documentId'] != document_id or pins['sourceSha256'] != sha(canonical)
        or safe(pins['source']) != canonical or pins['sourceSnapshotManifestSha256'] != CAP_SHA
        or pins['inputBeforeAfterUnchanged'] is not True):
        raise ValueError('Native render belongs to another canonical')
    pinned(qa['tileInventory'], qa['tileInventorySha256'])
    index_path = Path(qa['actuallyViewedIndexRecord'])
    if not index_path.is_absolute():
        index_path = REPO / index_path
    pinned(index_path, qa['actuallyViewedIndexRecordSha256'])
    originals, images = {}, []
    for entry in qa['captures']:
        if (entry['actuallyViewed'] is not True or entry['actuallyViewedBy'] != 'delivery_tools'
            or entry['pixelsEqualToOriginalRegion'] is not True or entry['scale'] != 1):
            raise ValueError('Tile lacks an explicit actual inspection')
        pinned(entry['originalPath'], entry['originalSha256'])
        pinned(entry['path'], entry['sha256'])
        rect = entry['sourceRectangle']
        box = (rect['x'], rect['y'], rect['x'] + rect['width'], rect['y'] + rect['height'])
        with Image.open(safe(entry['originalPath'])) as original, Image.open(safe(entry['path'])) as tile:
            if (list(original.size) != entry['wholeOriginalSize']
                or tile.size != (rect['width'], rect['height'])
                or original.convert('RGBA').crop(box).tobytes() != tile.convert('RGBA').tobytes()):
                raise ValueError('Tile does not match exact original RGBA pixels')
        originals.setdefault(entry['originalPath'], (entry['wholeOriginalSize'], []))[1].append(box)
        images.append({**entry, 'actuallyReviewed': True, 'reviewer': '/root/delivery_tools',
                       'inspectionEvidenceField': 'actuallyViewed',
                       'inheritedActualInspectionRecord': str(safe(path)),
                       'inheritedActualInspectionRecordSha256': digest})
    if len({e['path'] for e in images}) != len(images):
        raise ValueError('Duplicate tile inspection')
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
              'completeDocumentVisualReview': True, 'findings': [], 'fourStateMeaningReviewComplete': True,
              'reviewedImages': tiles + actual['reviewedImages'], 'reviewedSourceResources': resources,
              'modesReviewed': sorted(MODES), 'rootActuallyViewedNewStateImages': 4,
              'deliveryActuallyViewedTiles': len(tiles), 'independentMeaningReviewSha256': pin['independentReviewSha256'],
              'projectionSha256': pin['projectionSha256'], 'captureReceiptSha256': sha(args.capture),
              'rootInspectionSha256': args.root_inspection_sha256, 'inheritedDiagramReviewSha256': args.native_review_sha256,
              'originalApplicationExecuted': False, 'pixelEquivalenceToRunningApplicationVerified': False,
              'formalQualityGatePassed': False, 'finalQualified': False, 'published': False,
              'limitations': ['Static offline source-backed projection only; original application was not executed.',
                              'Delivery actual tile inspections were inherited; root reverified unchanged exact RGBA coverage.']}
    output = safe(args.output)
    if not output.is_relative_to(REPORT / 'visual-review') or output.exists():
        raise ValueError('Fresh visual evidence output required')
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'path': str(output), 'sha256': sha(output), 'images': len(result['reviewedImages']), 'finalQualified': False}))

if __name__ == '__main__':
    main()
