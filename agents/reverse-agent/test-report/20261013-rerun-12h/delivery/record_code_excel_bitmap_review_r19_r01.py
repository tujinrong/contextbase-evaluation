"""Metadata-only actual-pixel receipt; never mutate original candidates."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json
P=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
invpath=P/'excel-bitmap-code-design-r19-r01-tiles/inventory.json'
out=P/'code-design-excel-bitmap-r19-r01-actual-native-review.json'
assert not out.exists()
assert sha(invpath)=='2be2b7cf0559230ab1775d2bac62ed522f08e83873fb5c3737d633ba69339e3d'
inv=json.loads(invpath.read_text(encoding='utf8'));d=inv['documents'][0]
assert d['originalPreviewCount']==43 and len(d['captures'])==81
bp=P/'binding-assisted-code-design-r19-r01.json'
assert sha(bp)=='b2a7208d29a716fef3578c74cb2d55dcc516e6b2627efbfdc341cded46fd89ef'
b=json.loads(bp.read_text(encoding='utf8'));e=b['documents'][0]
pins=dict(inv['sourceBindings']);pins[str(invpath)]=sha(invpath);pins[str(bp)]=sha(bp)
pins[e['markdown']]=e['markdownSha256']
for name,value in [('render-pins.json',e['renderPinsSha256']),('manifest.json',e['renderManifestSha256'])]:
 pins[str(Path(e['renderDirectory'])/name)]=value
result=json.loads((P/'excel-bitmap-code-design-r19-r01/result.json').read_text(encoding='utf8'))
assert result['workbookBytesUnchanged'] and result['planBytesUnchanged'] and result['readOnly']
assert not result['saved'] and not result['pageSetupChanged'] and not result['cellsOrFormatsChanged']
plan=json.loads(Path(result['plan']).read_text(encoding='utf8'))
assert len(result['cells'])==len(plan['cells'])
for expected,actual in zip(plan['cells'],result['cells']):
 assert (expected['sheet'],expected['cell'])==(actual['sheet'],actual['cell'])
 assert actual['value2']==expected['value'] or (expected['value']=='' and actual['value2'] is None)
 if expected['value']!='':assert actual['value2Type']=='System.String'
views=[]
for index,c in enumerate(d['captures']):
 assert c['scale']==1 and c['pixelsEqualToOriginalRegion']
 pins[c['path']]=c['sha256'];pins[c['originalPath']]=c['originalSha256']
 views.append({**c,'captureIndexZeroBased':index,'actuallyReviewed':True,'actuallyViewedBy':'delivery_tools','view':'original pixels'})
assert all(sha(path)==value for path,value in pins.items())
c=d['captures'][13]
finding={'sheet':'イベント仕様','cell':'AO100','token':'1900-01-01','visibleRows':['1900-01-','01'],
 'finding':'Actual Excel wraps the ISO date at a hyphen; no month/day digit group is fragmented. Whole-date one-line acceptance remains pending root classification.',
 'captureIndexZeroBased':13,'path':c['path'],'sha256':c['sha256'],'range':c['range']}
record={'schema':'reverse-agent-owned-excel-actual-native-review/1','createdUtc':datetime.now(timezone.utc).isoformat(),
 'scope':'OWNED_READ_ONLY_EXCEL_BITMAP_GEOMETRY_ONLY','referenceMode':'training-assisted','documentId':e['documentId'],
 'canonicalDocumentPath':e['canonicalDocumentPath'],'markdownSha256':e['markdownSha256'],
 'xlsx':d['xlsx'],'xlsxSha256':d['xlsxSha256'],'inventory':str(invpath),'inventorySha256':sha(invpath),
 'actualOriginalPreviews':43,'actualOriginalTiles':81,'actuallyViewedZeroBasedIndices':list(range(81)),
 'views':views,'status':'HOLD_WHOLE_DATE_HYPHEN_WRAP_CLASSIFICATION','blocking':[finding],
 'literalDisplay':'PASS_EXACT_LEADING_ZERO_STRINGS','internalAsciiNumericWrap':'PASS',
 'notes':['All columns and full ranges, all 22 diagrams, blank continuation regions and full-pixel crops were actually viewed at original scale.',
 'Actual Excel correctly displays 01/02/03/04 and all other leading-zero initial codes; original Artifact-native literal-display HOLD is preserved.',
 'The Artifact AO100 internal numeric break is resolved in actual Excel; natural authored-hyphen date wrapping is retained explicitly above.',
 'Other citation line ranges may naturally wrap at authored hyphens; no hidden or missing values were observed.',
 'CopyPicture temporarily wrote the clipboard; prior clipboard content was neither read nor output. Only owned copied sequence content was read.',
 'Static derived workbook display only; ASP.NET application and business operations were not executed.'],
 'excelVersion':result['excelVersion'],'excelBuild':result['excelBuild'],'ownedReadOnly':True,'saved':False,
 'pageSetupChanged':False,'cellsOrFormatsChanged':False,'allPinnedBytesUnchanged':True,'afterHashes':pins,
 'historicalInventoryModified':False,'historicalArtifactHoldModified':False,'businessContentAuthored':False,
 'semanticApproval':False,'formalQualityApproval':False,'stateProjectionIncluded':False,'wholeDocumentApproval':False,
 'published':False,'originalApplicationExecuted':False}
out.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'path':str(out),'sha256':sha(out),'status':record['status'],'actualTiles':81,'cells':len(result['cells'])}))
