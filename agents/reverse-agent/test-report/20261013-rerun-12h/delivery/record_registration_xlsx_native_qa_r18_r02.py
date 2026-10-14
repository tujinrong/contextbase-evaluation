"""Persist completed human viewing of original-scale Artifact previews, unchanged."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
P=Path(__file__).resolve().parent
INV=P/'xlsx-native-tiles-r18-r02/inventory.json';OUT=P/'registration-xlsx-r18-r02-actual-native-review.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not OUT.exists() and sha(INV)=='aed204b356031cdf61e6d61e551decbb657be17f03050a046e576116a8187e51'
inventory=json.loads(INV.read_text(encoding='utf8'))
doc=next(d for d in inventory['documents'] if d['documentId']=='CSHARP_ASPNET-BAS-STU-02')
assert len(doc['captures'])==127 and doc['originalPreviewCount']==64
assert doc['xlsxSha256']=='2ce2a9407f97a62c8869c1c4168628bc1b4a8dd397e08eef5868acf376d25191'
pins=dict(inventory['sourceBindings'])
pins[str(INV)]=sha(INV);pins[doc['xlsx']]=doc['xlsxSha256']
views=[]
for i,c in enumerate(doc['captures']):
 assert c['scale']==1 and c['pixelsEqualToOriginalRegion'] is True
 pins[c['path']]=c['sha256'];pins[c['originalPath']]=c['originalSha256']
 views.append({**c,'captureIndexZeroBased':i,'actuallyReviewed':True,'actuallyViewedBy':'delivery_tools','view':'original pixels'})
assert all(sha(Path(p))==s for p,s in pins.items())
findings=[
 {'captureIndexZeroBased':3,'sheet':'学生登録_概要','cell':'merged row43','token':'Busy','visibleRows':['Bu','sy']},
 {'captureIndexZeroBased':14,'sheet':'学生登録_項目','cell':'J2/J5/J9','tokens':['@student_no','Month','129-129'],'finding':'Identifier/number continuation occurs inside an individual cell; not capture-boundary cropping.'},
 {'captureIndexZeroBased':16,'sheet':'学生登録_項目','cell':'right LIST cells','tokens':['Input.EnrollmentStatusCode','@enrollment_status_code','EmergencyContactName'],'finding':'Identifiers wrap inside cell.'},
 {'captureIndexZeroBased':20,'sheet':'学生登録_項目','cell':'right LIST cells','tokens':['ExpectedVersion'],'finding':'Identifier and citation-path fragments inside cell.'},
 {'captureIndexZeroBased':22,'sheet':'学生登録_項目','cell':'right LIST cells','token':'EV-REG-004','visibleRows':['EV-R','EG-004']},
 {'captureIndexZeroBased':65,'sheet':'学生登録_イベント','cell':'merged row955','token':'OperationCanceledException','visibleRows':['OperationCanceledExcepti','on']},
 {'captureIndexZeroBased':75,'sheet':'学生登録_イベント','cell':'row1203','token':'DBConcurrencyException','finding':'Latin token inside cell breaks before its continuation; all characters remain in the pinned XML.'},
 {'captureIndexZeroBased':103,'sheet':'学生登録_イベント','cell':'row1834','token':'updated_by','visibleRows':['up','dated_by']}
]
for f in findings:
 c=doc['captures'][f['captureIndexZeroBased']];f.update(path=c['path'],sha256=c['sha256'],range=c['range'])
record={'schema':'reverse-agent-xlsx-actual-native-review/1','createdUtc':datetime.now(timezone.utc).isoformat(),'scope':'XLSX_ARTIFACT_NATIVE_GEOMETRY_ONLY','referenceMode':'training-assisted','documentId':doc['documentId'],'canonicalDocumentPath':doc['canonicalDocumentPath'],'markdownSha256':doc['markdownSha256'],'xlsx':doc['xlsx'],'xlsxSha256':doc['xlsxSha256'],'inventory':str(INV),'inventorySha256':sha(INV),'actualOriginalPreviews':64,'actualOriginalTiles':127,'actuallyViewedZeroBasedIndices':list(range(127)),'views':views,'status':'HOLD','blocking':findings,'notes':['All declared columns and all crop regions were actually viewed. Diagram labels remain legible; diagrams spanning preview row ranges have complete exact-RGBA region coverage.','Saved XLSX literal strings/formula rejection passed separate XML verification; native in-cell wrapping is a geometry failure and is not treated as missing source content.','Blank right-side continuation crops were also viewed at original scale.'], 'allPinnedBytesUnchanged':True,'afterHashes':pins,'historicalInventoryModified':False,'businessContentAuthored':False,'semanticApproval':False,'formalQualityApproval':False,'stateProjectionIncluded':False,'wholeDocumentApproval':False,'published':False,'applicationExecuted':False}
OUT.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'path':str(OUT),'sha256':sha(OUT),'status':'HOLD','actualTiles':127,'blockingGroups':len(findings)}))
