"""Metadata-only receipt for 89 actual original-pixel views of frozen output."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json
from PIL import Image, ImageChops

P = Path(__file__).resolve().parent
ID = 'CSHARP_ASPNET-DET-CSharp_ASPNET-SCR-STU-001'

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))

invpath = P / 'excel-bitmap-search-detail-r18-r02-tiles/inventory.json'
out = P / 'search-detail-excel-bitmap-r18-r02-actual-native-review.json'
assert not out.exists()
assert sha(invpath) == '8adc6403e7744e44cccf2e0bd2570db825ab243342b9469de8c3defc5d2b9493'
inv = read(invpath)
d = inv['documents'][0]
assert d['documentId'] == ID and d['originalPreviewCount'] == 47 and len(d['captures']) == 89
bp = P / 'binding-assisted-screens-r18-r01.json'
assert sha(bp) == 'f3afbafde2153a94194d4cc9048aff6ad0f11cf73bbfc2aec3b758308eb458c9'
b = read(bp)
e = next(v for v in b['documents'] if v['documentId'] == ID)
assert e['markdownSha256'] == '9a49fb5a1d22094db7c57fdaf751807dd2f69c12367973ea839bc5ff9b037696'
rp = Path(e['renderDirectory']) / 'render-pins.json'
assert sha(rp) == e['renderPinsSha256']
render = read(rp)
pins = dict(inv['sourceBindings'])
pins.update(render['inputPins'])
pins.update({str(invpath): sha(invpath), str(bp): sha(bp), str(rp): sha(rp)})
pins[str(Path(e['renderDirectory']) / 'manifest.json')] = e['renderManifestSha256']
runtime = read(render['rendererRuntimeReceipt'])
assert runtime['fileCount'] == 126 and len(runtime['files']) == 126
for name, value in runtime['files'].items():
    pins[str(Path(runtime['destination']) / name)] = value
for v in render['frozenRenderImports'].values():
    pins[v['path']] = v['sha256']
resultpath = P / 'excel-bitmap-search-detail-r18-r02/result.json'
workerpath = resultpath.parent / 'worker.json'
result = read(resultpath)
assert read(workerpath)['status'] == 'COMPLETE'
assert result['workbookBytesUnchanged'] and result['planBytesUnchanged'] and result['readOnly']
assert result['macrosDisabled'] and result['updateLinks'] == 0 and not result['visible']
assert not result['saved'] and not result['pageSetupChanged'] and not result['cellsOrFormatsChanged']
assert not result['originalApplicationExecuted']
plan = read(result['plan'])
assert len(result['cells']) == len(plan['cells']) == 1242
for expected, actual in zip(plan['cells'], result['cells']):
    assert (expected['sheet'], expected['cell']) == (actual['sheet'], actual['cell'])
    assert actual['value2'] == expected['value'] or (expected['value'] == '' and actual['value2'] is None)
    if expected['value'] != '':
        assert actual['value2Type'] == 'System.String'
pins.update({str(resultpath): sha(resultpath), str(workerpath): sha(workerpath)})
oldhold = P.parent / 'source-pilot/xlsx-assisted-detail89-r18-r02/review.json'
assert sha(oldhold) == 'a738385f0f5cdfffd55de9db645ec0e01b90ac48cba49ec1398c18a5323567b4'
pins[str(oldhold)] = sha(oldhold)
views = []
for index, c in enumerate(d['captures']):
    assert c['scale'] == 1 and c['pixelsEqualToOriginalRegion']
    pins[c['path']] = c['sha256']
    pins[c['originalPath']] = c['originalSha256']
    r = c['sourceRectangle']
    with Image.open(c['originalPath']) as original, Image.open(c['path']) as tile:
        crop = original.convert('RGBA').crop((r['x'], r['y'], r['x'] + r['width'], r['y'] + r['height']))
        diff = ImageChops.difference(crop, tile.convert('RGBA'))
        assert all(channel.getbbox() is None for channel in diff.split())
    views.append({**c, 'captureIndexZeroBased': index, 'actuallyReviewed': True,
                  'actuallyViewedBy': 'delivery_tools', 'view': 'original pixels'})
assert all(sha(path) == value for path, value in pins.items())
cell = next(c for c in plan['cells'] if c['sheet'] == '04_内部項目一覧' and c['cell'] == 'B11')
assert 'prefecture' in cell['value']
c = d['captures'][20]
finding = {'sheet': '04_内部項目一覧', 'cell': 'B11', 'token': 'prefecture',
           'visibleRows': ['prefe', 'cture'], 'captureIndexZeroBased': 20,
           'path': c['path'], 'sha256': c['sha256'], 'range': c['range'],
           'finding': 'Actual Excel fragments this Latin token inside the cell; this is not a capture boundary.'}
record = {'schema': 'reverse-agent-owned-excel-actual-native-review/1',
          'createdUtc': datetime.now(timezone.utc).isoformat(),
          'scope': 'OWNED_READ_ONLY_EXCEL_BITMAP_GEOMETRY_ONLY',
          'referenceMode': 'training-assisted', 'documentId': ID,
          'canonicalDocumentPath': e['canonicalDocumentPath'], 'markdownSha256': e['markdownSha256'],
          'xlsx': d['xlsx'], 'xlsxSha256': d['xlsxSha256'],
          'inventory': str(invpath), 'inventorySha256': sha(invpath),
          'actualOriginalPreviews': 47, 'actualOriginalTiles': 89,
          'actuallyViewedZeroBasedIndices': list(range(89)), 'views': views, 'unseen': [],
          'status': 'HOLD_ACTUAL_EXCEL_INTERNAL_IDENTIFIER_WRAP', 'blocking': [finding],
          'notes': ['All original ranges and columns, all 22 diagrams and the static screen layout were viewed at original scale.',
                    'Artifact fragments 20, studentNo, code_value, admissionDate, string, NULL, Options, string[], DateOnly and ModelState are resolved in actual Excel; original Artifact HOLD is unchanged.',
                    'Citation line ranges naturally wrap after authored hyphens (for example 110-/110 and 150-/150); all groups remain visible.',
                    'Long graph images continue in adjacent vertical ranges; continuation and rightmost strips were all inspected.',
                    'CopyPicture temporarily wrote the clipboard; previous clipboard content was not read or output.',
                    'Static derived workbook display only; the ASP.NET application and business operations were not executed.'],
          'literalCellsVerified': 1242, 'excelVersion': result['excelVersion'], 'excelBuild': result['excelBuild'],
          'ownedReadOnly': True, 'saved': False, 'pageSetupChanged': False, 'cellsOrFormatsChanged': False,
          'allPinnedBytesUnchanged': True, 'afterHashes': pins, 'historicalInventoryModified': False,
          'historicalArtifactHoldModified': False, 'businessContentAuthored': False,
          'semanticApproval': False, 'formalQualityApproval': False, 'stateProjectionIncluded': False,
          'wholeDocumentApproval': False, 'adoptionApproval': False, 'published': False,
          'originalApplicationExecuted': False}
out.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print(json.dumps({'path': str(out), 'sha256': sha(out), 'status': record['status'],
                  'actualTiles': 89, 'pins': len(pins)}, ensure_ascii=False))
