"""Record completed actual native viewing of an immutable CSS-only projection."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

P = Path(__file__).resolve().parent
def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

invpath = P / 'registration-detail-columns-probe-r03-tiles/inventory.json'
assert sha(invpath) == '8510137da698a842707a1418733e52747b1c09a18bd6ea7f30238e2dd1d2229b'
inv = json.loads(invpath.read_text(encoding='utf8'))
resultpath = P / 'registration-detail-columns-probe-r03/result.json'
assert sha(resultpath) == '7cd560c3b679f4739df7a01fcc60507c2c5fb3dbf6e53ec2bb6c323066e74d2b'
result = json.loads(resultpath.read_text(encoding='utf8'))
assert len(inv['captures']) == 76 and inv['originalPages'] == 13
assert all(result[k] is True for k in ['bodyDomBytesEqual', 'bodyTextEqual', 'allTablesEqual', 'allImageElementsEqual', 'allPinnedBytesUnchanged'])
assert result['wholeHyphenDotTokenWrapDiagnostics'] == []
assert result['javascriptEnabled'] is False and result['networkRequests'] == []
checks = dict(inv['sourceBindings'])
checks[str(invpath)] = sha(invpath)
checks[str(resultpath)] = sha(resultpath)
checks[result['projectionHtml']] = result['projectionHtmlSha256']
csspath = P / 'registration-detail-columns-probe-r03/candidate.css'
assert sha(csspath) == result['cssSha256']
checks[str(csspath)] = result['cssSha256']
for i, capture in enumerate(inv['captures']):
    assert capture['scale'] == 1 and capture['pixelsEqualToOriginalRegion']
    checks[capture['path']] = capture['sha256']
    checks[capture['originalPath']] = capture['originalSha256']
    capture.update(actuallyViewed=True, actuallyViewedBy='delivery_tools', captureIndexZeroBased=i, view='original exact RGBA pixels')
renderroot = Path(result['sourceHtml']).parent
pins = json.loads((renderroot / 'render-pins.json').read_text(encoding='utf8'))
for artifact in pins['artifacts']:
    checks[str(renderroot / artifact['path'])] = artifact['sha256']
receiptpath = Path(pins['rendererRuntimeReceipt'])
assert sha(receiptpath) == pins['rendererRuntimeReceiptSha256'] == '56c8d76fdbab9717a7bfa3f2b1bdc9800b7b03cdc7d495d1d3f920e528598308'
checks[str(receiptpath)] = sha(receiptpath)
receipt = json.loads(receiptpath.read_text(encoding='utf8'))
assert receipt['fileCount'] == len(receipt['files']) == 128
for relative, expected in receipt['files'].items():
    checks[str(Path(receipt['destination']) / relative)] = expected
assert all(sha(path) == expected for path, expected in checks.items())
record = {
    'schema': 'css-only-native-review/1',
    'createdUtc': datetime.now(timezone.utc).isoformat(),
    'scope': 'STATIC_DERIVED_CSS_GEOMETRY_ONLY',
    'status': 'PASS_WITH_NOTES_DERIVED_CSS_NATIVE_GEOMETRY_ONLY',
    'documentId': 'CSHARP_ASPNET-DET-CSharp_ASPNET-SCR-STU-002',
    'documentSha256': 'ecc68152d691076da8cc95c49387928d9e4f89d0f52aaaa5859708b547474cbd',
    'sourceHtmlSha256': result['sourceHtmlSha256'],
    'projectionHtml': result['projectionHtml'],
    'projectionHtmlSha256': result['projectionHtmlSha256'],
    'css': result['css'], 'cssSha256': result['cssSha256'],
    'sourceBodyDomExact': True, 'sourceBodyTextExact': True,
    'sourceTablesExact': True, 'sourceImagesExact': True,
    'mainModified': False, 'sourceModified': False,
    'rendererRuntimeReceipt': str(receiptpath),
    'rendererRuntimeReceiptSha256': sha(receiptpath),
    'rendererRuntimeFileCount': 128,
    'inventory': str(invpath), 'inventorySha256': sha(invpath),
    'captureResult': str(resultpath), 'captureResultSha256': sha(resultpath),
    'fullDocumentSize': inv['fullDocumentSize'],
    'originalPageCount': 13, 'actualTileCount': 76,
    'actuallyViewedZeroBasedIndices': list(range(76)), 'captures': inv['captures'],
    'resolved': [
        'The first-column UI/OPT/INT identifiers and the second-column REG identifiers remain whole in this viewing projection.',
        'The group and required columns now have readable Japanese labels and all table columns and complete cell text remain visible.'
    ],
    'blocking': [],
    'notes': [
        'This projection uses a 2400-pixel viewport, a generic 8em minimum for all cells of marked tables with at least three columns, and a 12em minimum for the first column.',
        'The original 21 graph images and three embedded static layouts are unchanged. Original-size graph labels and all text/table/image content were viewed across all 76 exact RGBA crops.',
        'The wide viewport leaves horizontal white space beside some diagrams. The complete document is covered by 13 contiguous captures; each is covered losslessly by overlapping native crops.',
        'The browser Range whole-hyphen/dot-token diagnostic has no findings; the actual visual review is independent of that diagnostic.',
        'Original r19 full-body HOLD and r02 CSS-only HOLD are preserved. This is a derived viewing candidate; it does not establish PDF, Excel, semantic, formal or whole-document approval.'
    ],
    'wholeHyphenDotTokenWrapDiagnostics': [],
    'allPinnedBytesUnchanged': True, 'afterHashes': checks,
    'javascriptEnabled': False, 'networkRequests': [],
    'businessContentAuthored': False, 'applicationExecuted': False,
    'semanticApproval': False, 'formalApproval': False,
    'wholeDocumentApproval': False, 'published': False,
}
out = P / 'registration-detail-columns-probe-r03-actual-native-review.json'
assert not out.exists()
out.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print(json.dumps({'path': str(out), 'sha256': sha(out), 'status': record['status'], 'actualTiles': 76, 'verifiedPins': len(checks)}, ensure_ascii=False))
