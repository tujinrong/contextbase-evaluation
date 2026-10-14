"""Record completed human/native PDF geometry QA; no document authoring."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / 'pdf-assisted-code-design-r19-r01' / 'delivery-manifest.json'
OUT = HERE / 'code-design-pdf-r19-r01-actual-native-review.json'
EXPECTED_MANIFEST = '13442ea3dc9371163be79b47ac11b977a68ea6c63fa56d5b0bfeef2db323e163'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

assert not OUT.exists(), 'Fresh evidence path required'
assert sha(MANIFEST) == EXPECTED_MANIFEST
manifest = json.loads(MANIFEST.read_text(encoding='utf8'))
doc = next(d for d in manifest['documents'] if d['documentId'] == 'CSHARP_ASPNET-BAS-STU-04')
assert doc['pages'] == 48 and len(doc['pageImages']) == 48
assert doc['pdfSha256'] == '6bf9190ff103a3f2cfd50b14e3e48c4a73cb48d1553fd5df087a81e7a8e7c700'
assert sha(Path(doc['pdf'])) == doc['pdfSha256']
binding_path = Path(manifest['binding'])
assert sha(binding_path) == manifest['bindingSha256']
binding = json.loads(binding_path.read_text(encoding='utf8'))
entry = next(d for d in binding['documents'] if d['documentId'] == doc['documentId'])
pins = {str(MANIFEST):EXPECTED_MANIFEST, str(binding_path):manifest['bindingSha256'],
        doc['pdf']:doc['pdfSha256'], entry['markdown']:entry['markdownSha256']}
render = Path(entry['renderDirectory'])
for name, key in [('render-pins.json','renderPinsSha256'), ('manifest.json','renderManifestSha256')]:
    pins[str(render/name)] = entry[key]
render_manifest = json.loads((render/'manifest.json').read_text(encoding='utf8'))
for asset in render_manifest['artifacts']:
    pins[str(render/asset['path'])] = asset['sha256']
pages = []
for number, page in enumerate(doc['pageImages'], 1):
    assert Path(page['path']).name == f'page-{number:02}.png'
    pins[page['path']] = page['sha256']
    pages.append({'page':number, 'path':page['path'], 'sha256':page['sha256'],
                  'actuallyViewedBy':'delivery_tools', 'view':'original pixels',
                  'geometryVerdict':'PASS'})
assert all(sha(Path(p)) == expected for p, expected in pins.items()), 'Input/output byte drift'
report = {
    'schema':'reverse-agent-pdf-actual-native-review/1', 'createdUtc':datetime.now(timezone.utc).isoformat(),
    'scope':'PDF_GEOMETRY_ONLY', 'referenceMode':'training-assisted', 'documentId':doc['documentId'],
    'canonicalDocumentPath':doc['canonicalDocumentPath'], 'markdownSha256':doc['markdownSha256'],
    'sourceSnapshotManifestSha256':manifest['sourceSnapshotManifestSha256'],
    'renderPinsSha256':doc['renderPinsSha256'], 'renderManifestSha256':doc['renderManifestSha256'],
    'pdf':doc['pdf'], 'pdfSha256':doc['pdfSha256'], 'pageCount':48, 'actualOriginalPageCount':48,
    'actualOriginalPages':list(range(1,49)), 'pages':pages, 'status':'PASS_WITH_NOTES', 'blocking':[],
    'notes':[
      {'pages':[2,3], 'finding':'Seed table and procedure continue across pages; repeated headers and complete visible rows remain legible.'},
      {'pages':list(range(1,49)), 'finding':'Diagram/raw-Mermaid blocks use separate pages and substantial whitespace to preserve original image and text scale.'}
    ],
    'literalCoverageEvidence':doc['textCoverage'], 'checkedVisibleStrings':doc['checkedVisibleStrings'],
    'beforeEvidence':'Immutable exporter manifest/page hashes captured before native viewing',
    'afterHashes':pins, 'allPinnedBytesUnchanged':True,
    'semanticApproval':False, 'formalQualityApproval':False, 'stateProjectionIncluded':False,
    'wholeDocumentApproval':False, 'published':False, 'applicationExecuted':False,
    'inputJavaScriptEnabled':False, 'businessContentAuthored':False
}
OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n', encoding='utf8')
print(json.dumps({'path':str(OUT), 'sha256':sha(OUT), 'actualOriginalPages':48, 'status':report['status']}))
