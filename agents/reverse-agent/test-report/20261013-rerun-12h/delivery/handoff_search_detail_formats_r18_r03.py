"""Bound metadata handoff only; no body construction, conversions or approvals."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json

P = Path(__file__).resolve().parent
ID = 'CSHARP_ASPNET-DET-CSharp_ASPNET-SCR-STU-001'
MD = '9a49fb5a1d22094db7c57fdaf751807dd2f69c12367973ea839bc5ff9b037696'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
fixed = {
    P / 'search-detail-excel-r18-r03-independent-review-r01/review.json': 'dfbc2c4e41fb937ba14a01e623682351b9cb16e162c66e209f2d38203c547a68',
    P.parent / 'source-pilot/pdf-assisted-detail50-r18-r01/review.json': '434023e8373a9993d019693733c0d8a88c57eee1a854ae12d1b8ae9358b79dae',
    P / 'search-detail-excel-width-r03-focal-native-review-r01.json': 'a61b8a4634337c96442d461f3ecbab2e53aa73024de06100cc2484fe548c7ad3',
    P / 'xlsx-assisted-search-detail-r18-r03-widthonly/delivery-manifest.json': '7c16d1d4acbe4787849966a860110c678a9f2e13249c48f13176d2694cbfb204',
    P / 'pdf-assisted-screens-r18-r01/delivery-manifest.json': 'e9cf4a92d25aad8b07a23939c4627bcdef929bcdea2d375f8dbb455fefc7f7fc',
}
pins = {}
def add(p, h):
    p = str(Path(p))
    assert p not in pins or pins[p] == h, ('conflicting pin', p)
    pins[p] = h
for p, h in fixed.items(): add(p, h)
assert all(sha(p) == h for p, h in pins.items())
xreview = read(next(iter(fixed)))
assert xreview['document']['documentId'] == ID and xreview['document']['markdownSha256'] == MD
assert xreview['status'] == 'PASS_WITH_NOTES_INDEPENDENT_EXCEL_BITMAP_GEOMETRY_ONLY'
assert xreview['blockerCount'] == 0 and xreview['actualReview']['actualTileIndices'] == list(range(89))
assert xreview['actualReview']['originalImageCount'] == 47 and xreview['actualReview']['borrowedVisualCoverage'] == 0
assert not any(xreview[k] for k in ('formal', 'semantic', 'state', 'whole', 'adoption', 'publication', 'published', 'applicationExecuted'))
assert not xreview['freshArtifactNativePreviewsReviewed'] and not xreview['freshArtifactNativePreviewApproval']
for k in ('before', 'after', 'historicalBefore', 'historicalAfter'):
    ref = xreview['integrity'][k]
    add(ref['path'], ref['sha256'])
    for p, h in read(ref['path'])['pins'].items(): add(p, h)
pre = read(xreview['integrity']['before']['path'])['pins']
post = read(xreview['integrity']['after']['path'])['pins']
assert pre == post and xreview['integrity']['allBeforeAfterHashesEqual']
pdfpath = P.parent / 'source-pilot/pdf-assisted-detail50-r18-r01/review.json'
preview = read(pdfpath)
assert preview['documentId'] == ID and preview['scope'] == 'PDF_GEOMETRY_ONLY'
assert preview['status'] == 'PASS_WITH_NOTES' and preview['geometryApproval']
assert preview['actualPageCount'] == preview['actualImageCount'] == preview['expectedPageCount'] == 50
assert not preview['blockingFindings'] and not preview['reviewInheritedFromOthers']
assert preview['pins']['markdownSha256'] == MD
for k in ('inventoryBefore', 'inventoryAfter'):
    add(preview['pins'][k], preview['pins'][k + 'Sha256'])
    for p, h in read(preview['pins'][k])['files'].items(): add(p, h)
xmanifest = read(P / 'xlsx-assisted-search-detail-r18-r03-widthonly/delivery-manifest.json')
xdoc = xmanifest['documents'][0]
pmanifest = read(P / 'pdf-assisted-screens-r18-r01/delivery-manifest.json')
pdoc = next(d for d in pmanifest['documents'] if d['documentId'] == ID)
assert xdoc['documentId'] == ID and xdoc['markdownSha256'] == pdoc['markdownSha256'] == MD
assert xdoc['xlsxSha256'] == xreview['document']['xlsxSha256'] == '47cd77ca1ecf27b57cb31dd6b250beea158acc42df8a0149a35c2eedbf2d544e'
assert pdoc['pdfSha256'] == preview['pins']['pdfSha256'] == '0fda56bfd072c1de3fd07e5b74b27e3dcb4068122e7204a6e0a8c2d922d4789c'
assert pdoc['pages'] == 50 and pdoc['textCoverage'] == 'PASS'
add(xdoc['xlsx'], xdoc['xlsxSha256']); add(pdoc['pdf'], pdoc['pdfSha256'])
binding = xreview['rendererBinding']
assert binding['runtimeReceiptSha256'] == preview['pins']['rendererRuntimeReceiptSha256'] == '54e693b2382e1520710d192e8a8b0b6b6eb97bbae1e70c1dbc36ff1e36f279be'
rp = read(binding['renderPins'])
assert rp['sourceSha256'] == MD and rp['rendererRuntimeLabel'] == 'r18' and rp['rendererRuntimeFileCount'] == 126
html = Path(binding['renderPins']).parent / rp['canonicalHtmlFilename']
add(html, rp['canonicalHtmlSha256'])
assert html.stem == Path(xdoc['xlsx']).stem == Path(pdoc['pdf']).stem == '01_学生検索画面'
assert all(sha(p) == h for p, h in pins.items())
out = P / 'search-detail-r18-r03-derived-format-handoff-r01.json'
assert not out.exists()
record = {
    'schema': 'reverse-agent-derived-format-metadata-handoff/1', 'createdUtc': datetime.now(timezone.utc).isoformat(),
    'scope': 'DERIVED_PDF_AND_READONLY_EXCEL_GEOMETRY_ONLY',
    'status': 'BOUND_SCOPED_GEOMETRY_RESULTS_AWAITING_PARENT_FULL_GATES',
    'referenceMode': 'training-assisted', 'documentId': ID,
    'canonicalDocumentPath': xdoc['canonicalDocumentPath'], 'markdownSha256': MD,
    'html': {'path': str(html), 'sha256': rp['canonicalHtmlSha256'],
             'rendererReceipt': binding['runtimeReceipt'], 'rendererReceiptSha256': binding['runtimeReceiptSha256'],
             'fullHtmlBodyIndependentlyReviewedInThisHandoff': False},
    'pdf': {'path': pdoc['pdf'], 'sha256': pdoc['pdfSha256'], 'actualPages': 50,
            'visualReviewer': preview['reviewer'], 'review': str(pdfpath), 'reviewSha256': fixed[pdfpath],
            'textCoverageAsRecorded': 'PASS', 'textCoverageIndependentlyRecomputedHere': False},
    'xlsx': {'path': xdoc['xlsx'], 'sha256': xdoc['xlsxSha256'], 'actualExcelOriginalRanges': 47,
             'actualExcelOriginalTiles': 89, 'visualReviewer': xreview['reviewer'],
             'review': str(next(iter(fixed))), 'reviewSha256': fixed[next(iter(fixed))],
             'literalCoordinates': 1242, 'nonemptyValue2TextExact': 1240, 'blankEquivalence': 2,
             'publicArtifactAuthoringOnly': True, 'authorMarkerReexecuted': False,
             'onlyGeometryChange': {'sheet': '04_内部項目一覧', 'column': 'B', 'before': 28, 'after': 48},
             'actualExcelReadOnly': True, 'savedByExcel': False, 'freshArtifactNativePreviewApproval': False},
    'historicalArtifactHoldPreserved': True, 'historicalActualExcelHoldPreserved': True,
    'currentPinnedFileCount': len(pins), 'allCurrentPinnedBytesUnchanged': True, 'afterHashes': pins,
    'sourceOrCanonicalBodyModified': False, 'businessContentAuthored': False,
    'semanticApproval': False, 'formalQualityApproval': False, 'stateProjectionIncluded': False,
    'wholeDocumentApproval': False, 'adoptionApproval': False, 'published': False, 'originalApplicationExecuted': False,
    'remaining': ['Parent composite/formal/state/whole document gates and final eleven-document collection are outside this handoff.',
                  'Artifact native previews retain their separate unapproved scope; actual Excel bitmap qualification does not rewrite that result.'],
}
out.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'path': str(out), 'sha256': sha(out), 'status': record['status'], 'pins': len(pins)}, ensure_ascii=False))
