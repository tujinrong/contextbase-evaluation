"""Record actually completed graph/layout and full-body geometry review only."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json
P=Path(__file__).resolve().parent
R=P.parent
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
render=R/'render/assisted-registration-detail-r01-delivery-r19'
pinpath=render/'render-pins.json'
assert sha(pinpath)=='1684f46d512528883842d65d6fc7ebb464c63062a3649efa639a5f6ea0cdc9e1'
pins=json.loads(pinpath.read_text(encoding='utf8'))
receiptpath=Path(pins['rendererRuntimeReceipt'])
assert sha(receiptpath)=='56c8d76fdbab9717a7bfa3f2b1bdc9800b7b03cdc7d495d1d3f920e528598308'
receipt=json.loads(receiptpath.read_text(encoding='utf8'))
frozen=Path(receipt['destination'])
inventory={p.relative_to(frozen).as_posix():sha(p) for p in frozen.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.pyo'}}
assert len(inventory)==128 and inventory==receipt['files']
assert pins['sourceSha256']=='ecc68152d691076da8cc95c49387928d9e4f89d0f52aaaa5859708b547474cbd'
pins['documentSha256']=pins['sourceSha256']
assert len(pins['diagrams'])==21 and len(pins['layouts'])==3
checks=dict(pins['inputPins'])
checks.update({str(p):sha(p) for p in render.iterdir() if p.is_file()})
groups=[]
for name,count in [('native-assisted-registration-detail-r19-r01',28),('native-assisted-registration-detail-r19-r01-full-document',40)]:
 path=P/name/'inventory.json'; data=json.loads(path.read_text(encoding='utf8'))
 assert len(data['captures'])==count
 checks[str(path)]=sha(path)
 for index,c in enumerate(data['captures']):
  assert c['scale']==1 and c['pixelsEqualToOriginalRegion']
  checks[c['path']]=c['sha256']; checks[c['originalPath']]=c['originalSha256']
  c.update(actuallyViewed=True,actuallyViewedBy='delivery_tools',captureIndexZeroBased=index,view='original pixels')
 groups.append({'inventory':str(path),'inventorySha256':sha(path),'captureCount':count,'actuallyViewedZeroBasedIndices':list(range(count)),'captures':data['captures']})
assert all(sha(p)==s for p,s in checks.items())
full=groups[1]['captures']
finding={'category':'WHOLE_HYPHENATED_IDENTIFIER_WRAP','finding':'Plain first-column IDs UI-DELETE/UI-MESSAGE, OPT-PREFECTURE/OPT-RELATIONSHIP and INT-* wrap at their hyphens. Latin words remain intact but the complete identifier crosses visible rows.','sampleCaptureIndicesZeroBased':[4,5],'samples':[full[i] for i in [4,5]],'bodyChanged':False,'geometryProjectionPending':True}
record={'schema':'screen-native-review/3','createdUtc':datetime.now(timezone.utc).isoformat(),'scope':'STATIC_DERIVED_GEOMETRY_ONLY','status':'HOLD_FULL_BODY_IDENTIFIER_WRAP','graphAndLayoutStatus':'PASS_NATIVE_GEOMETRY_ONLY','documentId':pins['documentId'],'canonicalDocumentPath':pins['canonicalDocumentPath'],'documentSha256':pins['documentSha256'],'referenceMode':'training-assisted','rendererRuntimeReceipt':str(receiptpath),'rendererRuntimeReceiptSha256':sha(receiptpath),'renderPins':str(pinpath),'renderPinsSha256':sha(pinpath),'canonicalHtmlSha256':pins['canonicalHtmlSha256'],'diagramCount':21,'layoutCount':3,'actualGraphLayoutTileCount':28,'fullDocumentOriginalPageCount':14,'actualFullDocumentTileCount':40,'groups':groups,'blocking':[finding],'notes':['All 68 exact RGBA crops were actually viewed at original scale. Graph/layout pixels and complete body coverage were inspected separately.','Graph labels preserve whole ASCII identifiers and numeric tokens; no overlapping or hidden labels were observed.','The first-column hyphen wrap is retained as a display HOLD. Canonical Markdown/HTML and all source assets remain unchanged.'],'allPinnedBytesUnchanged':True,'frozenRuntimeAll128FilesUnchanged':True,'afterHashes':checks,'stateProjectionIncluded':False,'semanticApproval':False,'formalQualityApproval':False,'wholeDocumentApproval':False,'published':False,'applicationExecuted':False}
out=P/'assisted-registration-detail-r01-delivery-r19-native-qa.json'; assert not out.exists()
out.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'path':str(out),'sha256':sha(out),'status':record['status'],'actualTiles':68},ensure_ascii=False))
