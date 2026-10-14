import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).parent
def load(name):
    return json.loads((OUT / name).read_bytes())
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
before, after = load('inventory-before.json'), load('inventory-after.json')
notes = load('observations.json')
assert before['files'] == after['files'] and after['immutableBeforeAfter'] is True
assert len(notes) == 50 and [x['page'] for x in notes] == list(range(1, 51))
assert all(x['status'] in ('PASS', 'PASS_WITH_NOTE') for x in notes)
pages = []
for item, note in zip(before['pages'], notes, strict=True):
    assert item['page'] == note['page']
    pages.append({**item, **note, 'actuallyViewedBy': '/root/source_pilot', 'viewDetail': 'original', 'coverage': 'COMPLETE_PAGE_IMAGE'})
report = {
    'schema': 'independent-pdf-native-visual-review/1',
    'createdAt': datetime.now(timezone.utc).isoformat(),
    'subject': 'training-assisted delivery',
    'documentId': before['documentId'], 'canonicalDocumentPath': before['canonicalDocumentPath'],
    'scope': 'PDF_GEOMETRY_ONLY', 'status': 'PASS_WITH_NOTES',
    'geometryApproval': True, 'blockingFindings': [], 'findings': [],
    'reviewer': '/root/source_pilot', 'reviewInheritedFromOthers': False,
    'actualPageCount': 50, 'actualImageCount': 50, 'expectedPageCount': 50,
    'actualViewingMethod': 'Ten ordered calls to view_image(detail=original), each returning five distinct original page PNGs. Every page 01 through 50 was actually inspected by this reviewer.',
    'pages': pages,
    'checks': {
        'unreadableShrinkObserved': False, 'clippedTextOrFigureObserved': False,
        'missingTableColumnObserved': False, 'diagramTextOverlapObserved': False,
        'numericOrAsciiTokenInternalBreakObserved': False,
        'whitespaceCausingLostContinuationObserved': False,
        'allImagesDecodeAndManifestShaMatch': True,
        'pdfMarkdownManifestRuntimeAnd50PngHashesUnchanged': True,
    },
    'nonblockingObservations': [
        {'pages': [1, 2], 'kind': 'SCREEN_PROJECTION_PAGE_CONTINUATION', 'description': 'The static screen is split between pages 1 and 2 at the sorting-control area. All controls and result columns remain visible across the pair; no control label or text is cut.'},
        {'pages': [4, 5], 'kind': 'NARROW_JAPANESE_TABLE_COLUMNS', 'description': 'Group, item and I/O columns stack Japanese text vertically. All ten columns and values remain readable. IDs wrap at a hyphen boundary with complete numeric suffixes, distinct from token-internal numeric splitting.'},
        {'pages': [2, 3, 6, 8, 9, 10, 12, 14, 16, 18, 19, 20, 22, 23, 24, 26, 28, 29, 30, 32, 33, 34, 35, 36, 37, 38, 40, 41, 42, 44, 45, 46, 47, 50], 'kind': 'SUBSTANTIAL_WHITESPACE', 'description': 'Many diagram/source pages have large blank remainders. Preceding text explicitly names the following figure or subflow, and visible source follows it. Content remains locatable and readable; no missing content is inferred from whitespace.'},
    ],
    'pins': {
        'manifestSha256': before['manifestSha256'], 'pdfSha256': before['pdfSha256'],
        'markdownSha256': before['markdownSha256'], 'sourceSnapshotManifestSha256': before['sourceSnapshotManifestSha256'],
        'rendererRuntimeLabel': before['rendererRuntimeLabel'],
        'rendererRuntimeReceipt': before['rendererRuntimeReceipt'], 'rendererRuntimeReceiptSha256': before['rendererRuntimeReceiptSha256'],
        'inventoryBefore': str(OUT / 'inventory-before.json'), 'inventoryBeforeSha256': sha(OUT / 'inventory-before.json'),
        'inventoryAfter': str(OUT / 'inventory-after.json'), 'inventoryAfterSha256': sha(OUT / 'inventory-after.json'),
        'observationsSha256': sha(OUT / 'observations.json'),
    },
    'sourceBindingBeforeAfterConfirmed': True,
    'textCoverage': {'statusAsRecordedByDelivery': before['textCoverageAsRecorded'], 'visibleStringsAsRecordedByDelivery': before['checkedVisibleStringsAsRecorded'], 'independentlyRecomputedHere': False},
    'semanticSourceFidelityAssessed': False, 'originalApplicationExecuted': False,
    'gradingAnswerExpectedOrOriginalReferenceBodyRead': False, 'providerExecuted': False,
    'existingCandidateImageHtmlMarkdownChanged': False, 'sourceOnlyBaseline': 'CLOSED',
    'formalQualityScore': None, 'formalRubricEvaluated': False,
    'stateProjectionReviewedHere': False, 'published': False,
}
path = OUT / 'review.json'
with path.open('x', encoding='utf-8', newline='\n') as handle:
    json.dump(report, handle, ensure_ascii=False, indent=2)
    handle.write('\n')
print(json.dumps({'report': str(path), 'sha256': sha(path), 'status': report['status'], 'actuallyViewed': len(pages), 'allInputPinsUnchanged': True}, ensure_ascii=False))
