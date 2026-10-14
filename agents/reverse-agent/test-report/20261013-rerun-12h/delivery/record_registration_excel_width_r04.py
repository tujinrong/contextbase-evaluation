"""Metadata-only receipt for 127 actual original-pixel views of fresh J-width160."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json
P=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
invpath=P/'excel-bitmap-registration-r18-r04-widthonly-tiles/inventory.json'
out=P/'registration-excel-width-r04-actual-native-review.json'
assert not out.exists()
assert sha(invpath)=='12816aea6245b19f53185fd75fb0254d3ccd0bb1ba074b1f19f238c4b8c80af6'
inv=json.loads(invpath.read_text(encoding='utf8'));d=inv['documents'][0]
assert d['originalPreviewCount']==64 and len(d['captures'])==127
bindingpath=P/'binding-assisted-screens-r18-r01.json'
assert sha(bindingpath)=='f3afbafde2153a94194d4cc9048aff6ad0f11cf73bbfc2aec3b758308eb458c9'
binding=json.loads(bindingpath.read_text(encoding='utf8'))
entry=next(x for x in binding['documents'] if x['documentId']=='CSHARP_ASPNET-BAS-STU-02')
pins=dict(inv['sourceBindings']);pins[str(invpath)]=sha(invpath);pins[str(bindingpath)]=sha(bindingpath)
pins[entry['markdown']]=entry['markdownSha256']
for name,s in [('render-pins.json',entry['renderPinsSha256']),('manifest.json',entry['renderManifestSha256'])]:
 pins[str(Path(entry['renderDirectory'])/name)]=s
for name,expected in [
 ('model-assisted-registration-r18-r04-widthonly.json','dee1a027b501b08caeaf5c07212ef19eec10e3c9e2936d80571961d02222089d'),
 ('registration-xlsx-r18-r04-widthonly-xml-delta.json','b88e1f8d340fb04e6accdd632f289b21ec6583c149658306386661b0dd576c94')]:
 assert sha(P/name)==expected;pins[str(P/name)]=expected
resultpath=P/'excel-bitmap-registration-r18-r04-widthonly/result.json'
result=json.loads(resultpath.read_text(encoding='utf8'))
assert result['workbookBytesUnchanged'] and result['planBytesUnchanged']
assert not result['saved'] and not result['pageSetupChanged'] and not result['cellsOrFormatsChanged']
plan=json.loads(Path(result['plan']).read_text(encoding='utf8'))
assert len(result['cells'])==len(plan['cells'])==1205
for expected,actual in zip(plan['cells'],result['cells']):
 assert (expected['sheet'],expected['cell'])==(actual['sheet'],actual['cell'])
 assert actual['value2']==expected['value'] or (expected['value']=='' and actual['value2'] is None)
 if expected['value']!='':assert actual['value2Type']=='System.String'
views=[]
for index,c in enumerate(d['captures']):
 assert c['scale']==1 and c['pixelsEqualToOriginalRegion']
 pins[c['path']]=c['sha256'];pins[c['originalPath']]=c['originalSha256']
 views.append({**c,'captureIndexZeroBased':index,'actuallyReviewed':True,'actuallyViewedBy':'delivery_tools','view':'original pixels'})
assert all(sha(path)==s for path,s in pins.items())
notes=[]
for index,description in [
 (18,'Source citation line range is visibly wrapped at the authored hyphen, e.g. 87-/94; neither digit sequence is fragmented.'),
 (20,'Source citation range 8-8 is visibly wrapped at the authored hyphen as 8-/8.'),
 (124,'Supplement source citation ranges include a hyphen-boundary line break, e.g. 303-/318 and 158-/159.')]:
 c=d['captures'][index];notes.append({'captureIndexZeroBased':index,'path':c['path'],'sha256':c['sha256'],'sheet':c['sheet'],'range':c['range'],'finding':description})
record={'schema':'reverse-agent-owned-excel-actual-native-review/1','createdUtc':datetime.now(timezone.utc).isoformat(),
 'scope':'OWNED_READ_ONLY_EXCEL_BITMAP_GEOMETRY_ONLY','referenceMode':'training-assisted','documentId':entry['documentId'],
 'canonicalDocumentPath':entry['canonicalDocumentPath'],'markdownSha256':entry['markdownSha256'],
 'xlsx':d['xlsx'],'xlsxSha256':d['xlsxSha256'],'inventory':str(invpath),'inventorySha256':sha(invpath),
 'actualOriginalPreviews':64,'actualOriginalTiles':127,'actuallyViewedZeroBasedIndices':list(range(127)),
 'views':views,'status':'PASS_WHOLE_IDENTIFIERS_WITH_CITATION_WRAP_NOTES','wholeIdentifierGeometry':'PASS',
 'citationWrapClassification':'OBSERVED_ROOT_ACCEPTANCE_PENDING','blockingWholeIdentifierFindings':[],
 'citationWrapNotes':notes,'notes':[
 'All columns, ranges, blank continuation areas, diagrams and layouts were actually viewed at original scale. No hidden, truncated or missing values were observed.',
 'EV-REG-004/-005/-006/-007 and earlier Artifact-native internal Latin/numeric wrap groups are resolved in this actual Excel projection.',
 'Only J column width changes from 44 to 160. Independent literal, empty-cell, image, order, row-height, style and package XML comparison is preserved separately.',
 'The older Artifact and actual-Excel HOLD candidates remain immutable; this receipt does not reclassify them.',
 'Citation hyphen-boundary wrapping is explicitly retained for root acceptance; complete document approval is not granted here.',
 'CopyPicture temporarily wrote the clipboard; prior content was neither read nor output. Only the owned copied sequence was read.',
 'The ASP.NET application and business operations were not executed.'],
 'excelVersion':result['excelVersion'],'excelBuild':result['excelBuild'],'ownedReadOnly':True,'saved':False,
 'pageSetupChanged':False,'cellsOrFormatsChanged':False,'allPinnedBytesUnchanged':True,'afterHashes':pins,
 'historicalInventoryModified':False,'historicalArtifactHoldModified':False,'businessContentAuthored':False,
 'semanticApproval':False,'formalQualityApproval':False,'stateProjectionIncluded':False,'wholeDocumentApproval':False,
 'published':False,'originalApplicationExecuted':False}
out.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'path':str(out),'sha256':sha(out),'status':record['status'],'actualTiles':127}))
