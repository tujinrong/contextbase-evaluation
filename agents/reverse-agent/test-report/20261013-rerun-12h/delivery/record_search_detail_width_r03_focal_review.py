"""Metadata-only binding for one personally inspected actual Excel range."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

P = Path(__file__).resolve().parent
ID = 'CSHARP_ASPNET-DET-CSharp_ASPNET-SCR-STU-001'

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))

fixed = {
    'excel-bitmap-search-detail-r18-r03-widthonly-tiles/inventory.json': 'c753a6159c9785214eab41ec7356a6ce933cc453b53d8b5d66a0232625a0e7ec',
    'excel-bitmap-search-detail-r18-r03-widthonly/result.json': '0249ce5ca5ff90df4540309332189b0eed11f030168372fe80b3eb9fe1322f09',
    'search-detail-xlsx-r18-r03-widthonly-xml-delta.json': '1778e312e3ae12f7eda227860face8544c9e96128ab998a9f3ed7ee72b1c4350',
    'search-detail-width-r03-code-model-independent-review-r01.json': '8d9b2ef12f7d1e28812a542e62b726abf44c3b190cefc469dac10403cc1b414e',
    'search-detail-excel-bitmap-r18-r02-actual-native-review.json': '869a7d0cb0e049a7ca0b3c97a6e00055fb1a836772527c8c6b98d552dcb5838f',
    'model-assisted-search-detail-r18-r03-widthonly.json': '1bc286d0c846bde2416651f85850c80ed58256dbe8f89198899354439b6fed42',
    'binding-assisted-screens-r18-r01.json': 'f3afbafde2153a94194d4cc9048aff6ad0f11cf73bbfc2aec3b758308eb458c9',
}
pins = {}
def add(path, expected):
    path = str(Path(path))
    assert path not in pins or pins[path] == expected, ('conflicting pin', path)
    pins[path] = expected

for rel, expected in fixed.items():
    add(P / rel, expected)
inv = read(P / next(iter(fixed)))
doc = inv['documents'][0]
assert doc['documentId'] == ID and doc['originalPreviewCount'] == 47 and len(doc['captures']) == 89
for path, expected in inv['sourceBindings'].items():
    add(path, expected)
for c in doc['captures']:
    add(c['path'], c['sha256'])
    add(c['originalPath'], c['originalSha256'])
old = read(P / 'search-detail-excel-bitmap-r18-r02-actual-native-review.json')
assert old['status'] == 'HOLD_ACTUAL_EXCEL_INTERNAL_IDENTIFIER_WRAP'
for path, expected in old['afterHashes'].items():
    add(path, expected)
binding = read(P / 'binding-assisted-screens-r18-r01.json')
entry = next(e for e in binding['documents'] if e['documentId'] == ID)
assert entry['markdownSha256'] == doc['markdownSha256'] == '9a49fb5a1d22094db7c57fdaf751807dd2f69c12367973ea839bc5ff9b037696'
resultpath = P / 'excel-bitmap-search-detail-r18-r03-widthonly/result.json'
result = read(resultpath)
workerpath = resultpath.parent / 'worker.json'
assert read(workerpath)['status'] == 'COMPLETE'
assert result['readOnly'] and result['macrosDisabled'] and result['updateLinks'] == 0 and not result['visible']
assert result['workbookBytesUnchanged'] and result['planBytesUnchanged']
assert not any(result[k] for k in ('saved', 'pageSetupChanged', 'cellsOrFormatsChanged', 'originalApplicationExecuted'))
plan = read(result['plan'])
assert len(plan['cells']) == len(result['cells']) == 1242
for e, a in zip(plan['cells'], result['cells']):
    assert (e['sheet'], e['cell']) == (a['sheet'], a['cell'])
    assert a['value2'] == e['value'] or (e['value'] == '' and a['value2'] is None)
    assert e['value'] == '' or a['value2Type'] == 'System.String'
add(workerpath, sha(workerpath))
add(P / 'xlsx-assisted-search-detail-r18-r03-widthonly/delivery-manifest.json', sha(P / 'xlsx-assisted-search-detail-r18-r03-widthonly/delivery-manifest.json'))
assert all(sha(path) == expected for path, expected in pins.items())
c = doc['captures'][20]
assert c['sheet'] == '04_内部項目一覧' and c['range'] == 'A1:F12'
assert c['sha256'] == 'e51a060079cffdd36477827a0019550e42a4d4da59c189c732cf9e5ba6605ead'
cell = next(v for v in result['cells'] if v['sheet'] == '04_内部項目一覧' and v['cell'] == 'B11')
assert 'prefecture' in cell['value2'] and cell['text'] == cell['value2']
record = {
    'schema': 'reverse-agent-actual-excel-focal-native-review/1',
    'createdUtc': datetime.now(timezone.utc).isoformat(),
    'scope': 'OWNED_READ_ONLY_EXCEL_SINGLE_RANGE_GEOMETRY_ONLY',
    'referenceMode': 'training-assisted', 'documentId': ID,
    'canonicalDocumentPath': entry['canonicalDocumentPath'], 'markdownSha256': doc['markdownSha256'],
    'xlsx': doc['xlsx'], 'xlsxSha256': doc['xlsxSha256'],
    'status': 'FOCAL_RANGE_PASS_FULL_INDEPENDENT_REVIEW_PENDING',
    'actuallyViewedBy': 'delivery_tools', 'actuallyViewedZeroBasedIndices': [20],
    'views': [{**c, 'captureIndexZeroBased': 20, 'actuallyReviewed': True}],
    'finding': {'sheet': c['sheet'], 'cell': 'B11', 'token': 'prefecture',
                'wholeTokenVisible': True, 'notCaptureBoundary': True},
    'literalCellsVerified': 1242, 'candidateColumnWidthOnly': {'sheet': '04_内部項目一覧', 'column': 'B', 'before': 28, 'after': 48},
    'allPinnedBytesUnchanged': True, 'afterHashes': pins,
    'oldActualHoldModified': False, 'oldArtifactHoldModified': False,
    'ownedReadOnly': True, 'saved': False, 'cellsOrFormatsChangedByExcel': False,
    'clipboardTemporaryOwnWrite': True, 'previousClipboardRead': False,
    'businessContentAuthored': False, 'semanticApproval': False, 'formalQualityApproval': False,
    'stateProjectionIncluded': False, 'wholeDocumentApproval': False, 'adoptionApproval': False,
    'published': False, 'originalApplicationExecuted': False,
}
out = P / 'search-detail-excel-width-r03-focal-native-review-r01.json'
assert not out.exists()
out.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'path': str(out), 'sha256': sha(out), 'status': record['status'], 'pins': len(pins)}, ensure_ascii=False))
