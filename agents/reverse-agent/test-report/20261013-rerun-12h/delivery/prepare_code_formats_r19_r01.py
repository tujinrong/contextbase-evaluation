"""Bind already-viewed immutable code-design geometry, no business authoring."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
from delivery_model import safe_path,load_bound
P=Path(__file__).resolve().parent;REPORT=P.parent;A=P.parents[2];REPO=P.parents[4]
RECEIPT=REPORT/'training-assisted/runtime-code-assisted-11.json';RECEIPT_SHA='56c8d76fdbab9717a7bfa3f2b1bdc9800b7b03cdc7d495d1d3f920e528598308'
R=REPORT/'render/assisted-code-design-r01-delivery-r19';INV=P/'native-assisted-code-design-r19-r01/inventory.json'
NATIVE=P/'assisted-code-design-r01-delivery-r19-native-qa.json';BIND=P/'binding-assisted-code-design-r19-r01.json'
ASSISTED=A/'.tmp/20261013-rerun-12h/training-assisted';DOCROOT=REPO/'test-project1/spec-analysis/CSharp_ASPNET/20261013-rerun-12h/training-assisted/drafts'
MD_SHA='7a4ab1da290ae076e29a7ec558b6f63fc0a41ee0052315ea3bd9fc93b6dda4a8';CAP='e76a6c40e8927011fff9145d5f5ab2fa94ad89acefc9a03bbad0cbf09b85a0e7'
def sha(p):return hashlib.sha256(safe_path(p).read_bytes()).hexdigest()
def read(p):return json.loads(safe_path(p).read_text(encoding='utf8'))
def write(p,d):
 assert not p.exists();p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def inv(root):return {p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.pyo'}}
assert sha(RECEIPT)==RECEIPT_SHA
receipt=read(RECEIPT);frozen=Path(receipt['destination']);assert len(receipt['files'])==128 and inv(frozen)==receipt['files']
pins=read(R/'render-pins.json');inventory=read(INV);source=Path(pins['source']);assert sha(source)==MD_SHA==pins['sourceSha256']==inventory['documentSha256']
assert pins['referenceMode']=='training-assisted' and pins['rendererRuntimeLabel']=='r19' and pins['rendererRuntimeReceiptSha256']==RECEIPT_SHA
assert len(pins['diagrams'])==22 and not pins['layouts'] and all(d['status']=='PASS' for d in pins['diagrams']) and pins['display']['status']=='PASS'
assert len(inventory['captures'])==28
before={str(RECEIPT):RECEIPT_SHA,str(INV):sha(INV),str(R/'render-pins.json'):sha(R/'render-pins.json'),str(source):MD_SHA}
before.update(pins['inputPins'])
manifest=read(R/'manifest.json')
for asset in manifest['artifacts']:before[str(R/asset['path'])]=asset['sha256']
captures=[]
for i,c in enumerate(inventory['captures']):
 assert c['pixelsEqualToOriginalRegion'] is True
 before[c['path']]=c['sha256'];before[c['originalPath']]=c['originalSha256']
 captures.append({**c,'actuallyViewed':True,'actuallyViewedBy':'delivery_tools','captureIndexZeroBased':i,'view':'original pixels'})
assert all(sha(Path(p))==s for p,s in before.items())
native={'schema':'screen-native-review/2','createdUtc':datetime.now(timezone.utc).isoformat(),'status':'PASS_NATIVE_GEOMETRY_ONLY','documentId':pins['documentId'],'documentSha256':MD_SHA,'canonicalDocumentPath':pins['canonicalDocumentPath'],'canonicalHtmlSha256':pins['canonicalHtmlSha256'],'renderPins':str(R/'render-pins.json'),'renderPinsSha256':sha(R/'render-pins.json'),'rendererRuntimeReceipt':str(RECEIPT),'rendererRuntimeReceiptSha256':RECEIPT_SHA,'frozenRuntimeAll128FilesUnchanged':True,'inputBeforeAfterPinsUnchanged':True,'tileInventory':str(INV),'tileInventorySha256':sha(INV),'actuallyViewedTileCount':28,'actuallyViewedImageCount':22,'diagramCount':22,'layoutCount':0,'exactRgbaComparisonAndCompletePixelCoverage':True,'captures':captures,'findings':[],'notes':['Former r18 diagram014 split numeric422 is resolved in the same canonical MD by trusted r19 width400 and whole-token proof; actual original-scale diagram014 was viewed.','All22 diagrams/28 exact-RGBA tiles actually viewed; continuation overlaps preserve complete diagram pixels. No hidden labels, identifier/number fragmentation or blocking overlap observed.'],'beforeAfterPins':before,'formalQualityApproval':False,'wholeDocumentApproval':False,'published':False,'applicationExecuted':False,'stateProjectionIncluded':False}
write(NATIVE,native)
draft=ASSISTED/'jobs/revision-code-design-r04/draft-result.json';h=ASSISTED/'jobs/revision-code-design-r04-independent-review/review-handoff.json';review=h.with_name('review-verified.json');handoff=read(h);ver=read(review)
assert handoff['approved'] is True and handoff['referenceMode']=='training-assisted' and handoff['documentSha256']==MD_SHA and handoff['reviewSha256']==sha(review)
assert handoff['snapshot']['manifestSha256']==CAP and ver['approved'] is True and not ver['findings'] and not ver['unresolved']
entry={'documentId':pins['documentId'],'canonicalDocumentPath':pins['canonicalDocumentPath'],'markdown':str(source),'markdownSha256':MD_SHA,'renderDirectory':str(R),'renderPinsSha256':sha(R/'render-pins.json'),'renderManifestSha256':sha(R/'manifest.json'),'draftResult':str(draft),'draftResultSha256':sha(draft),'nativeGeometryReview':str(NATIVE),'nativeGeometryReviewSha256':sha(NATIVE),'separateApprovedReview':{'handoff':str(h),'handoffSha256':sha(h),'review':str(review),'reviewSha256':sha(review),'approved':True,'scope':'text-source-and-structure'},'stateProjectionIncluded':False}
write(BIND,{'schema':'reverse-agent-delivery-binding/1','referenceMode':'training-assisted','permittedMarkdownRoot':str(DOCROOT),'permittedRenderRoot':str(REPORT/'render'),'sourceSnapshotManifestSha256':CAP,'formalQualityGatePassed':False,'documents':[entry],'wholeQualityApproved':False,'published':False})
load_bound(BIND);assert inv(frozen)==receipt['files'] and all(sha(Path(p))==s for p,s in before.items())
print(json.dumps({'native':str(NATIVE),'nativeSha256':sha(NATIVE),'binding':str(BIND),'bindingSha256':sha(BIND),'status':native['status'],'actualTiles':28}))
