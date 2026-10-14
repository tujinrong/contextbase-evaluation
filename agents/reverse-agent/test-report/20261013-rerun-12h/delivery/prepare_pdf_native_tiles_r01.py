"""Lossless original-scale PDF page crops; no content or PDF authoring."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
from PIL import Image
from pypdf import PdfReader
from delivery_model_r18 import safe_path

def sha(p): return hashlib.sha256(safe_path(p).read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    manifest_path = safe_path(args.manifest)
    output = safe_path(args.output)
    assert not output.exists()
    manifest = json.loads(manifest_path.read_text(encoding='utf8'))
    assert manifest['status'] == 'TEXT_VERIFIED_VISUAL_REVIEW_PENDING'
    assert manifest['originalApplicationExecuted'] is False and manifest['inputJavaScriptEnabled'] is False
    binding_path = safe_path(manifest['binding'])
    assert sha(binding_path) == manifest['bindingSha256']
    binding = json.loads(binding_path.read_text(encoding='utf8'))
    by_id = {entry['documentId']: entry for entry in binding['documents']}
    pins = {str(manifest_path): sha(manifest_path), str(binding_path): sha(binding_path), str(Path(__file__).resolve()): sha(__file__)}
    for entry in binding['documents']:
        pins[entry['markdown']] = entry['markdownSha256']
        root = safe_path(entry['renderDirectory'])
        pins[str(root / 'render-pins.json')] = entry['renderPinsSha256']
        pins[str(root / 'manifest.json')] = entry['renderManifestSha256']
    assert all(sha(p) == value for p, value in pins.items())
    output.mkdir()
    records = []
    for document in manifest['documents']:
        assert document['textCoverage'] == 'PASS'
        entry = by_id[document['documentId']]
        assert document['markdownSha256'] == entry['markdownSha256']
        assert sha(document['pdf']) == document['pdfSha256']
        assert len(PdfReader(document['pdf'], strict=True).pages) == document['pages'] == len(document['pageImages'])
        pins[document['pdf']] = document['pdfSha256']
        target = output / document['documentId']
        target.mkdir()
        captures = []
        for ordinal, page in enumerate(document['pageImages'], 1):
            assert sha(page['path']) == page['sha256']
            pins[page['path']] = page['sha256']
            with Image.open(page['path']) as original:
                original.load()
                rectangles = []
                for y in range(0, original.height, 1700):
                    for x in range(0, original.width, 1700):
                        box = (x, y, min(x + 1800, original.width), min(y + 1800, original.height))
                        crop = original.crop(box)
                        name = f'page-{ordinal:03d}-{x:04d}-{y:04d}.png'
                        dest = target / name
                        crop.save(dest)
                        with Image.open(dest) as saved:
                            assert saved.size == crop.size and saved.convert('RGBA').tobytes() == crop.convert('RGBA').tobytes()
                        rectangles.append(box)
                        captures.append({'page': ordinal, 'originalPath': page['path'], 'originalSha256': page['sha256'],
                            'path': str(dest), 'sha256': sha(dest), 'sourceRectangle': {'x': x, 'y': y, 'width': box[2]-x, 'height': box[3]-y},
                            'wholeOriginalSize': list(original.size), 'scale': 1, 'pixelsEqualToOriginalRegion': True, 'actuallyReviewed': False})
                for row in range(original.height):
                    intervals = sorted((left, right) for left, top, right, bottom in rectangles if top <= row < bottom)
                    cursor = 0
                    for left, right in intervals:
                        assert left <= cursor
                        cursor = max(cursor, right)
                    assert cursor == original.width
        records.append({'documentId':document['documentId'], 'canonicalDocumentPath':document['canonicalDocumentPath'],
            'markdownSha256':document['markdownSha256'], 'pdf':document['pdf'], 'pdfSha256':document['pdfSha256'],
            'originalPageCount':document['pages'], 'captures':captures, 'nativeApproval':False})
    assert all(sha(p) == value for p, value in pins.items())
    result = {'schema':'pdf-native-review-tile-inventory/1', 'createdUtc':datetime.now(timezone.utc).isoformat(),
        'scope':'PDF_GEOMETRY_ONLY', 'sourceBindings':pins, 'pixelComparator':'exact RGBA bytes',
        'coverage':'all original pixels; original scale; up to 100px overlap', 'documents':records,
        'formalApproval':False, 'semanticApproval':False, 'applicationExecuted':False, 'published':False}
    dest = output / 'inventory.json'
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps({'inventory':str(dest), 'sha256':sha(dest), 'counts':[(d['documentId'],d['originalPageCount'],len(d['captures'])) for d in records]}, ensure_ascii=False))

if __name__ == '__main__': main()
