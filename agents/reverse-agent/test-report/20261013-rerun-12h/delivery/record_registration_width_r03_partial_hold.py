"""Retain the known-failed candidate and the exact partial viewing boundary."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
ip=H/'excel-bitmap-registration-r18-r03-widthonly-tiles/inventory.json';assert sha(ip)=='a557b7325beb454297108b0c9600b1e6f8ddf0f01d073c383b743ce2744a8ef7'
j=json.loads(ip.read_text(encoding='utf8'));d=j['documents'][0];assert len(d['captures'])==127
checks=dict(j['sourceBindings']);checks[str(ip)]=sha(ip);views=[]
for i,c in enumerate(d['captures']):
 checks[c['path']]=c['sha256'];checks[c['originalPath']]=c['originalSha256']
 views.append({**c,'actuallyViewed':i<40,'captureIndexZeroBased':i,'actuallyViewedBy':'delivery_tools' if i<40 else None})
assert all(sha(p)==s for p,s in checks.items())
f={'sheet':'学生登録_項目','cell':'J47','token':'EV-REG-006','visibleRows':['EV-REG-','006'],'captureIndexZeroBased':22,'path':d['captures'][22]['path'],'sha256':d['captures'][22]['sha256'],'finding':'Column J=60 resolves J41 but moves a natural hyphen break into the J47 complete identifier.'}
record={'schema':'owned-readonly-excel-partial-review/1','createdUtc':datetime.now(timezone.utc).isoformat(),'scope':'STATIC_DERIVED_GEOMETRY_ONLY','status':'HOLD_KNOWN_IDENTIFIER_WRAP_PARTIAL_REVIEW','documentId':d['documentId'],'xlsx':d['xlsx'],'xlsxSha256':d['xlsxSha256'],'inventory':str(ip),'inventorySha256':sha(ip),'actuallyViewedZeroBasedIndices':list(range(40)),'actualTileCount':40,'totalTileCount':127,'unviewedTileCount':87,'views':views,'blocking':[f],'reasonForStoppingThisCandidateReview':'A visible blocking failure is confirmed; remaining full-range review is reserved for the fresh width160 candidate.','allPinnedBytesUnchanged':True,'afterHashes':checks,'oldArtifactAndExcelHoldsPreserved':True,'wholeDocumentApproval':False,'formalApproval':False,'published':False,'businessContentAuthored':False,'applicationExecuted':False}
out=H/'registration-excel-width-r03-partial-native-hold.json';assert not out.exists();out.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'path':str(out),'sha256':sha(out),'status':record['status'],'actualTileCount':40},ensure_ascii=False))
