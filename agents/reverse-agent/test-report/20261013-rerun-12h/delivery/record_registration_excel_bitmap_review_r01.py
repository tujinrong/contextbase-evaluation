"""Record completed original-pixel viewing; never mutate the candidate."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json
P=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
invpath=P/'excel-bitmap-registration-r18-r01-tiles/inventory.json'
out=P/'registration-excel-bitmap-r18-r01-actual-native-review.json'
assert not out.exists()
assert sha(invpath)=='9b2b8973c040f954ff3184a6258551418f320b45b3951a8ab3dd62199279039f'
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
resultpath=P/'excel-bitmap-registration-r18-r01/result.json'
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
c=d['captures'][22]
finding={'sheet':'学生登録_項目','cell':'J41','token':'EV-REG-004','visibleRows':['EV-','REG-004'],'finding':'Natural hyphen wrapping still splits the whole identifier in the saved workbook viewed by actual Excel.','captureIndexZeroBased':22,'path':c['path'],'sha256':c['sha256'],'range':c['range']}
record={'schema':'reverse-agent-owned-excel-actual-native-review/1','createdUtc':datetime.now(timezone.utc).isoformat(),
 'scope':'OWNED_READ_ONLY_EXCEL_BITMAP_GEOMETRY_ONLY','referenceMode':'training-assisted','documentId':entry['documentId'],
 'canonicalDocumentPath':entry['canonicalDocumentPath'],'markdownSha256':entry['markdownSha256'],
 'xlsx':d['xlsx'],'xlsxSha256':d['xlsxSha256'],'inventory':str(invpath),'inventorySha256':sha(invpath),
 'actualOriginalPreviews':64,'actualOriginalTiles':127,'actuallyViewedZeroBasedIndices':list(range(127)),
 'views':views,'status':'HOLD_WHOLE_IDENTIFIER_WRAP','blocking':[finding],
 'notes':['All columns, full ranges, exact RGBA crops and blank continuation regions were actually viewed at original scale.',
 'The eight earlier Artifact-native wrap groups remain preserved in their original HOLD record. Actual Excel resolves their internal Latin/numeric splits except the hyphenated EV-REG-004 identifier.',
 'Value2 readback exactly preserves all 1205 strings/empty values. Bitmap success is separate from geometry acceptance.',
 'Excel CopyPicture temporarily writes the clipboard; prior clipboard content was neither read nor output. Only the owned copied sequence was read.',
 'Static Excel display was inspected; the original ASP.NET application and business operations were not executed.'],
 'excelVersion':result['excelVersion'],'excelBuild':result['excelBuild'],'ownedReadOnly':True,'saved':False,
 'pageSetupChanged':False,'cellsOrFormatsChanged':False,'allPinnedBytesUnchanged':True,'afterHashes':pins,
 'historicalInventoryModified':False,'historicalArtifactHoldModified':False,'businessContentAuthored':False,
 'semanticApproval':False,'formalQualityApproval':False,'stateProjectionIncluded':False,'wholeDocumentApproval':False,
 'published':False,'originalApplicationExecuted':False}
out.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'path':str(out),'sha256':sha(out),'status':record['status'],'actualTiles':127,'blocking':1}))
