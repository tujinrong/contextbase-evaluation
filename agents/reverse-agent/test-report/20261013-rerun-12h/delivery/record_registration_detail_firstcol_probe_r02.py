"""Record actually viewed immutable CSS-only viewing projection; no content authoring."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json
P=Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
invpath=P/'registration-detail-firstcol-probe-r02-tiles/inventory.json'
assert sha(invpath)=='fe1c282669f9ce8ce1072a71ea41875e3da6a13a7f38e4bc0abbd8f0a1a73f6c'
inv=json.loads(invpath.read_text(encoding='utf8'))
resultpath=P/'registration-detail-firstcol-probe-r02/result.json'
assert sha(resultpath)=='ca2d566392ae3db9e7045cb9133d378b3c4a51d9b73a1c9bf6dbf2419e5abfd4'
result=json.loads(resultpath.read_text(encoding='utf8'))
assert len(inv['captures'])==41 and inv['originalPages']==14
assert all(result[k] is True for k in ['bodyDomBytesEqual','bodyTextEqual','allTablesEqual','allImageElementsEqual','allPinnedBytesUnchanged'])
checks=dict(inv['sourceBindings']);checks[str(invpath)]=sha(invpath)
for i,c in enumerate(inv['captures']):
 assert c['scale']==1 and c['pixelsEqualToOriginalRegion']
 checks[c['path']]=c['sha256']; checks[c['originalPath']]=c['originalSha256']
 c.update(actuallyViewed=True,actuallyViewedBy='delivery_tools',captureIndexZeroBased=i,view='original exact RGBA pixels')
assert all(sha(p)==s for p,s in checks.items())
record={'schema':'css-only-native-review/1','createdUtc':datetime.now(timezone.utc).isoformat(),'scope':'STATIC_DERIVED_CSS_GEOMETRY_ONLY','status':'HOLD_SECOND_COLUMN_WHOLE_IDENTIFIER_WRAP',
 'documentId':'CSHARP_ASPNET-DET-CSharp_ASPNET-SCR-STU-002','documentSha256':'ecc68152d691076da8cc95c49387928d9e4f89d0f52aaaa5859708b547474cbd',
 'sourceHtmlSha256':result['sourceHtmlSha256'],'projectionHtmlSha256':result['projectionHtmlSha256'],'css':result['css'],'cssSha256':result['cssSha256'],
 'sourceBodyDomExact':True,'sourceBodyTextExact':True,'sourceTablesExact':True,'sourceImagesExact':True,'mainModified':False,'sourceModified':False,
 'inventory':str(invpath),'inventorySha256':sha(invpath),'fullDocumentSize':inv['fullDocumentSize'],'originalPageCount':14,'actualTileCount':41,
 'actuallyViewedZeroBasedIndices':list(range(41)),'captures':inv['captures'],
 'resolved':['First-column UI-DELETE/UI-MESSAGE, OPT-PREFECTURE/OPT-RELATIONSHIP and INT-SNAPSHOT identifiers remain whole after the 12em minimum width.'],
 'blocking':[{'kind':'WHOLE_HYPHENATED_IDENTIFIER_WRAP','column':'種類','examples':['REG-002','REG-003'],'visibleRowsExample':['REG-','002'],'captureIndexZeroBased':3,'evidence':inv['captures'][3]}],
 'notes':['The group and required columns in the ten-column item table are narrow and some Japanese labels occupy one character per visible line. All letters remain visible, but this is a readability limitation.','All 41 exact RGBA crops were actually viewed. The remaining ten crops introduce no additional blocking findings.','The original failed r01 capture and original r19 full-body HOLD remain unchanged. This CSS projection is a candidate only.'],
 'allPinnedBytesUnchanged':True,'afterHashes':checks,'javascriptEnabled':False,'networkRequests':[],
 'businessContentAuthored':False,'applicationExecuted':False,'semanticApproval':False,'formalApproval':False,'wholeDocumentApproval':False,'published':False}
out=P/'registration-detail-firstcol-probe-r02-actual-native-review.json';assert not out.exists()
out.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'path':str(out),'sha256':sha(out),'status':record['status'],'actualTiles':41},ensure_ascii=False))
