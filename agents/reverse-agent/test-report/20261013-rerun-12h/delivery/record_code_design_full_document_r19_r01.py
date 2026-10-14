"""Metadata-only receipt of actual views of immutable full static capture PNGs."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json
from PIL import Image, ImageChops

P = Path(__file__).resolve().parent
R = P.parent / 'render/assisted-code-design-r01-delivery-r19'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
pins = {}
def add(path, expected):
    path = str(Path(path))
    assert path not in pins or pins[path] == expected, ('conflicting pin', path)
    pins[path] = expected

invpath = P / 'code-design-r19-full-document-tiles-r01/inventory.json'
add(invpath, '062f9e821a196cf78eda3186b4129242326f52463524fc5dc929a27e98f77d95')
add(R / 'render-pins.json', 'a426bb3c83c832e776ab3121b7ddc32c111e6e62b7e8f95348d3b793b9b4d5d7')
add(R / 'manifest.json', '3fbf55ad26a6f1b945dfd82f381883f033627027dc37810b0acedafbb0964a29')
add(P / 'binding-assisted-code-design-r19-r01.json', 'b2a7208d29a716fef3578c74cb2d55dcc516e6b2627efbfdc341cded46fd89ef')
add(P / 'r19-two-doc-derived-final-handoff-r01.json', '8e054c02a35f6352a3fcc9713d7a2af1e21944b0d0bd43b0f00d5939e52b4258')
inv = read(invpath)
rp = read(R / 'render-pins.json')
assert inv['documentId'] == rp['documentId'] == 'CSHARP_ASPNET-BAS-STU-04'
assert inv['documentSha256'] == rp['sourceSha256'] == '7a4ab1da290ae076e29a7ec558b6f63fc0a41ee0052315ea3bd9fc93b6dda4a8'
assert inv['fullDocumentSize'] == [1440, 45164] and len(inv['captures']) == 34
assert rp['rendererRuntimeFileCount'] == 128 and rp['rendererRuntimeLabel'] == 'r19'
assert rp['inputBeforeAfterUnchanged'] and not rp['originalModified'] and not rp['originalApplicationExecuted']
for path, expected in inv['beforeAfterPins'].items(): add(path, expected)
for path, expected in rp['inputPins'].items(): add(path, expected)
for a in rp['artifacts']: add(R / a['path'], a['sha256'])
add(R / rp['canonicalHtmlFilename'], rp['canonicalHtmlSha256'])
add(rp['rendererRuntimeReceipt'], rp['rendererRuntimeReceiptSha256'])
rt = read(rp['rendererRuntimeReceipt'])
assert rt['fileCount'] == len(rt['files']) == 128
for rel, expected in rt['files'].items(): add(Path(rt['destination']) / rel, expected)
for a in rp['frozenRenderImports'].values(): add(a['path'], a['sha256'])
assert all(sha(path) == expected for path, expected in pins.items())
manifest = read(R / 'manifest.json')
capture = manifest['display']['documentCapture']
assert capture['complete'] and capture['width'] == 1440 and capture['height'] == 45164
assert len(capture['pages']) == 12
views = []
by_original = {}
for index, c in enumerate(inv['captures']):
    assert c['scale'] == 1 and c['pixelsEqualToOriginalRegion']
    add(c['path'], c['sha256']); add(c['originalPath'], c['originalSha256'])
    rect = c['sourceRectangle']
    with Image.open(c['originalPath']) as original, Image.open(c['path']) as tile:
        original = original.convert('RGBA'); tile = tile.convert('RGBA')
        crop = original.crop((rect['x'], rect['y'], rect['x'] + rect['width'], rect['y'] + rect['height']))
        assert crop.size == tile.size
        assert all(channel.getbbox() is None for channel in ImageChops.difference(crop, tile).split())
    by_original.setdefault(c['originalPath'], []).append(c)
    views.append({**c, 'captureIndexZeroBased': index, 'actuallyReviewed': True,
                  'actuallyViewedBy': 'delivery_tools', 'view': 'original pixels'})
assert len(by_original) == 12
for name, items in by_original.items():
    items.sort(key=lambda c: c['sourceRectangle']['y'])
    assert all(c['sourceRectangle']['x'] == 0 and c['sourceRectangle']['width'] == 1440 for c in items)
    end = 0
    for c in items:
        r = c['sourceRectangle']; assert r['y'] <= end; end = max(end, r['y'] + r['height'])
    assert end == items[0]['wholeOriginalSize'][1]
assert all(sha(path) == expected for path, expected in pins.items())
out = P / 'code-design-r19-full-document-actual-native-review-r01.json'
assert not out.exists()
record = {
    'schema': 'reverse-agent-full-static-document-actual-native-review/1',
    'createdUtc': datetime.now(timezone.utc).isoformat(),
    'scope': 'FULL_STATIC_HTML_DOCUMENT_GEOMETRY_ONLY', 'referenceMode': 'training-assisted',
    'documentId': rp['documentId'], 'canonicalDocumentPath': rp['canonicalDocumentPath'],
    'markdownSha256': rp['sourceSha256'], 'canonicalHtmlFilename': rp['canonicalHtmlFilename'],
    'canonicalHtmlSha256': rp['canonicalHtmlSha256'],
    'rendererRuntimeReceipt': rp['rendererRuntimeReceipt'],
    'rendererRuntimeReceiptSha256': rp['rendererRuntimeReceiptSha256'],
    'inventory': str(invpath), 'inventorySha256': sha(invpath),
    'originalDocumentCapturePages': 12, 'actualOriginalTiles': 34,
    'fullDocumentSize': [1440, 45164], 'actuallyViewedZeroBasedIndices': list(range(34)),
    'views': views, 'unseen': [], 'status': 'PASS_FULL_STATIC_HTML_GEOMETRY_WITH_NOTES',
    'blocking': [],
    'notes': [
        'All table columns, values, headings, prose, raw Mermaid text and graph continuations were inspected at original pixels.',
        'Some table headings and Japanese text use multiple lines; no internal ASCII identifier or numeric fragmentation, hidden cells, or label overlap was observed.',
        'Tall graphs and tables cross the original static capture boundaries; adjacent ranges were inspected together and all pixels are covered.',
        'This fresh receipt fills the prior handoff declaration that full static HTML body capture had not yet been viewed; historical handoff is unchanged.',
        'No HTML/MD/CSS/diagram was changed or rerendered for this review.'
    ],
    'allPinnedBytesUnchanged': True, 'afterHashes': pins,
    'historicalHandoffModified': False, 'sourceOrCanonicalBodyModified': False,
    'businessContentAuthored': False, 'semanticApproval': False, 'formalQualityApproval': False,
    'stateProjectionIncluded': False, 'wholeDocumentApproval': False, 'adoptionApproval': False,
    'published': False, 'originalApplicationExecuted': False,
}
out.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'path': str(out), 'sha256': sha(out), 'status': record['status'], 'actualTiles': 34, 'pins': len(pins)}, ensure_ascii=False))
