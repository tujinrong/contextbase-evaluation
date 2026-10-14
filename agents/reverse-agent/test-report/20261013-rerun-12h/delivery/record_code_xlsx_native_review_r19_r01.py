"""Record completed Artifact-native viewing and prepare metadata-only Excel QA."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json
P = Path(__file__).resolve().parent
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
ip = P / 'xlsx-native-tiles-code-r19-r01/inventory.json'
assert sha(ip) == '677686b337e2b80886b7fa5f139982bfeca349b4448bee4dc26be79f189446d5'
i = json.loads(ip.read_text(encoding='utf8')); d = i['documents'][0]
assert d['originalPreviewCount'] == 43 and len(d['captures']) == 81
mp = P / 'xlsx-assisted-code-design-r19-r01/delivery-manifest.json'
m = json.loads(mp.read_text(encoding='utf8')); md = m['documents'][0]
assert d['documentId'] == md['documentId'] == 'CSHARP_ASPNET-BAS-STU-04'
bp = P / 'binding-assisted-code-design-r19-r01.json'
assert sha(bp) == 'b2a7208d29a716fef3578c74cb2d55dcc516e6b2627efbfdc341cded46fd89ef'
b = json.loads(bp.read_text(encoding='utf8')); e = b['documents'][0]
pins = dict(i['sourceBindings']); pins[str(ip)] = sha(ip); pins[str(mp)] = sha(mp); pins[str(bp)] = sha(bp)
pins[e['markdown']] = e['markdownSha256']
for name, digest in [('render-pins.json', e['renderPinsSha256']), ('manifest.json', e['renderManifestSha256'])]:
    pins[str(Path(e['renderDirectory']) / name)] = digest
views = []
for n, c in enumerate(d['captures']):
    assert c['scale'] == 1 and c['pixelsEqualToOriginalRegion']
    pins[c['path']] = c['sha256']; pins[c['originalPath']] = c['originalSha256']
    views.append({**c, 'captureIndexZeroBased': n, 'actuallyReviewed': True, 'actuallyViewedBy': 'delivery_tools', 'view': 'original pixels'})
assert all(sha(path) == digest for path, digest in pins.items())
findings = [
    {'sheet': '初期コード一覧', 'cells': ['B6','B7','B8','B9'], 'captureIndexZeroBased': 5,
     'path': d['captures'][5]['path'], 'sha256': d['captures'][5]['sha256'],
     'finding': 'Artifact preview displays literal leading-zero code values 01/02/03/04 as 1/2/3/4. Saved XML remains literal; actual Excel display is not yet reviewed.'},
    {'sheet': 'イベント仕様', 'cell': 'AO100', 'token': '1900-01-01', 'captureIndexZeroBased': 13,
     'path': d['captures'][13]['path'], 'sha256': d['captures'][13]['sha256'],
     'visibleRows': ['1900-0','1-01'], 'finding': 'Artifact preview splits the numeric date token inside the same cell. Saved XML remains literal; actual Excel display is not yet reviewed.'}
]
record = {'schema': 'reverse-agent-artifact-actual-native-review/1', 'createdUtc': datetime.now(timezone.utc).isoformat(),
 'scope': 'ARTIFACT_NATIVE_GEOMETRY_ONLY', 'referenceMode': 'training-assisted',
 'documentId': d['documentId'], 'canonicalDocumentPath': d['canonicalDocumentPath'], 'markdownSha256': d['markdownSha256'],
 'xlsx': d['xlsx'], 'xlsxSha256': d['xlsxSha256'], 'inventory': str(ip), 'inventorySha256': sha(ip),
 'actualOriginalPreviews': 43, 'actualOriginalTiles': 81, 'actuallyViewedZeroBasedIndices': list(range(81)), 'views': views,
 'status': 'HOLD_NATIVE_LITERAL_DISPLAY_AND_TOKEN_WRAP', 'blocking': findings,
 'notes': ['All 81 original-scale exact RGBA tiles were actually viewed, including all columns and blank continuation regions.',
           'All diagram labels were readable with no hidden labels or overlaps observed. Successful image export does not resolve the two native display findings.',
           'The saved workbook passes independent literal, blank, formula rejection, border, image and print metadata checks. Native and actual Excel display scopes remain separate.'],
 'allPinnedBytesUnchanged': True, 'afterHashes': pins, 'businessContentAuthored': False,
 'semanticApproval': False, 'formalQualityApproval': False, 'stateProjectionIncluded': False,
 'wholeDocumentApproval': False, 'published': False, 'originalApplicationExecuted': False}
op = P / 'code-design-xlsx-r19-r01-actual-native-review.json'; assert not op.exists()
op.write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
plan = {'workbook': md['xlsx'], 'workbookSha256': md['xlsxSha256'], 'manifest': str(mp),
 'documentId': md['documentId'], 'canonicalDocumentPath': md['canonicalDocumentPath'], 'markdownSha256': md['markdownSha256'],
 'sheets': list(dict.fromkeys(c['sheet'] for c in md['writtenCells'])),
 'cells': [{'sheet': c['sheet'], 'cell': c['cell'], 'value': c['value']} for c in md['writtenCells']],
 'previews': [{'sheet': c['sheet'], 'range': c['range']} for c in md['previews']]}
pp = P / 'code-design-xlsx-r19-r01-excel-bitmap-plan.json'; assert not pp.exists()
pp.write_text(json.dumps(plan, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
print(json.dumps({'record':str(op),'recordSha256':sha(op),'status':record['status'],'actualTiles':81,'plan':str(pp),'planSha256':sha(pp)}))
