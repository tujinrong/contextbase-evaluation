import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image

ROOT = Path(r'D:\開発\contextbase-evaluation')
REPORT = ROOT / 'agents/reverse-agent/test-report/20261013-rerun-12h'
DELIVERY = REPORT / 'delivery/pdf-assisted-screens-r18-r01'
OUT = Path(__file__).parent
MANIFEST = DELIVERY / 'delivery-manifest.json'
DOC_ID = 'CSHARP_ASPNET-DET-CSharp_ASPNET-SCR-STU-001'
MANIFEST_PIN = 'e9cf4a92d25aad8b07a23939c4627bcdef929bcdea2d375f8dbb455fefc7f7fc'
PDF_PIN = '0fda56bfd072c1de3fd07e5b74b27e3dcb4068122e7204a6e0a8c2d922d4789c'
MD_PIN = '9a49fb5a1d22094db7c57fdaf751807dd2f69c12367973ea839bc5ff9b037696'
CAP_PIN = 'e76a6c40e8927011fff9145d5f5ab2fa94ad89acefc9a03bbad0cbf09b85a0e7'

def safe(path):
    path = Path(path)
    if not path.is_absolute() or not path.is_relative_to(ROOT):
        raise ValueError('Outside review root')
    for parent in reversed((path, *path.parents)):
        if parent.is_symlink() or parent.is_junction():
            raise ValueError('Linked path')
    return path

def digest(path):
    h = hashlib.sha256()
    with safe(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def load_metadata(path):
    return json.loads(safe(path).read_bytes())

assert digest(MANIFEST) == MANIFEST_PIN
m = load_metadata(MANIFEST)
assert m['referenceMode'] == 'training-assisted' and m['sourceSnapshotManifestSha256'] == CAP_PIN
d = next(x for x in m['documents'] if x['documentId'] == DOC_ID)
assert d['pages'] == 50 and d['markdownSha256'] == MD_PIN and d['pdfSha256'] == PDF_PIN
b_path = safe(m['binding'])
assert digest(b_path) == m['bindingSha256']
b = load_metadata(b_path)
assert b['referenceMode'] == 'training-assisted' and b['sourceSnapshotManifestSha256'] == CAP_PIN
bd = next(x for x in b['documents'] if x['documentId'] == DOC_ID)
assert bd['markdownSha256'] == MD_PIN and bd['canonicalDocumentPath'] == d['canonicalDocumentPath']
md = safe(bd['markdown'])
assert md.is_relative_to(Path(b['permittedMarkdownRoot']))
assert digest(md) == MD_PIN
pdf = safe(d['pdf'])
assert pdf.is_relative_to(DELIVERY / 'PDF') and digest(pdf) == PDF_PIN
rd = safe(bd['renderDirectory'])
assert rd.is_relative_to(Path(b['permittedRenderRoot']))
pins_path = rd / 'render-pins.json'
assert digest(pins_path) == d['renderPinsSha256'] == bd['renderPinsSha256']
pins = load_metadata(pins_path)
assert pins['referenceMode'] == 'training-assisted' and pins['documentId'] == DOC_ID
assert pins['sourceSnapshotManifestSha256'] == CAP_PIN and pins['sourceSha256'] == MD_PIN
assert pins['source'] == str(md) and pins['inputBeforeAfterUnchanged'] is True
receipt = safe(pins['rendererRuntimeReceipt'])
assert digest(receipt) == pins['rendererRuntimeReceiptSha256']
render_manifest = rd / 'render-manifest.json'
if not render_manifest.exists():
    render_manifest = rd / 'manifest.json'
assert digest(render_manifest) == d['renderManifestSha256'] == bd['renderManifestSha256']
coverage = DELIVERY / 'qa/詳細仕様書/CSharp_ASPNET/01_学生検索画面/text-coverage.json'
files = {}
for path in (MANIFEST, b_path, md, pdf, pins_path, render_manifest, receipt, coverage):
    files[str(path)] = digest(path)
pages = []
assert len(d['pageImages']) == 50
for index, item in enumerate(d['pageImages'], 1):
    path = safe(item['path'])
    assert path == DELIVERY / f'qa/詳細仕様書/CSharp_ASPNET/01_学生検索画面/page-{index:02d}.png'
    h = digest(path)
    assert h == item['sha256']
    with Image.open(path) as image:
        image.load()
        size = list(image.size)
    files[str(path)] = h
    pages.append({'page': index, 'path': str(path), 'sha256': h, 'size': size})
snapshot = {
    'schema': 'independent-pdf-visual-review-inventory/1',
    'createdAt': datetime.now(timezone.utc).isoformat(),
    'reviewer': '/root/source_pilot', 'subject': 'training-assisted delivery',
    'scope': 'PDF_GEOMETRY_ONLY', 'documentId': DOC_ID,
    'canonicalDocumentPath': d['canonicalDocumentPath'], 'markdownSha256': MD_PIN,
    'pdfSha256': PDF_PIN, 'sourceSnapshotManifestSha256': CAP_PIN,
    'rendererRuntimeLabel': pins['rendererRuntimeLabel'],
    'rendererRuntimeReceipt': str(receipt), 'rendererRuntimeReceiptSha256': files[str(receipt)],
    'manifestSha256': MANIFEST_PIN, 'files': files, 'pages': pages,
    'sourceOnlyBaseline': 'CLOSED', 'textCoverageAsRecorded': d['textCoverage'],
    'checkedVisibleStringsAsRecorded': d['checkedVisibleStrings'],
    'canonicalBodyInterpreted': False, 'sourceFidelityAssessed': False,
    'originalReferenceOrExpectedOrGradingAnswerRead': False,
}
if len(sys.argv) > 1 and sys.argv[1] == 'after':
    before = load_metadata(OUT / 'inventory-before.json')
    assert snapshot['files'] == before['files'] and snapshot['pages'] == before['pages']
    snapshot['immutableBeforeAfter'] = True
    target = OUT / 'inventory-after.json'
else:
    target = OUT / 'inventory-before.json'
with target.open('x', encoding='utf-8', newline='\n') as handle:
    json.dump(snapshot, handle, ensure_ascii=False, indent=2)
    handle.write('\n')
print(json.dumps({'file': str(target), 'sha256': digest(target), 'pages': len(pages), 'size': pages[0]['size'], 'renderer': snapshot['rendererRuntimeLabel']}, ensure_ascii=False))
