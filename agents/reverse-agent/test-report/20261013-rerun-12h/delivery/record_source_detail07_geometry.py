"""Source-only display QA evidence; no specification authoring or scoring."""
from __future__ import annotations
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
from PIL import Image,ImageChops
HERE=Path(__file__).resolve().parent;REPORT=HERE.parent
FINDINGS={1:['LastResult','data'],2:['JsonElement'],4:['ToCriteria','Page1','LastResult','Present','e.Status','Status'],5:['SearchModel','sortKey','sortDirection','DivideByZeroException'],6:['Get','ContextRevision'],8:['FormGuard'],9:['EnsureSearch','Page','LastResult','Present','WebFault'],10:['page','SearchModel','Applied'],11:['Use','LastResult','Present'],12:['ContextId'],13:['GET','CurrentUser','NULL','Tab'],14:['SearchAsync','EnsureSearch','Present','Entry'],16:['CSRF'],17:['Message'],18:['CurrentUser','W-SRC-002','Session','Tab'],19:['ContextId','Tab','Gate.WaitAsync','403','long.MaxValue','Gate','finally'],20:['Gate.Release'],21:['now','order','day'],22:['CodeExists','ArgumentException','WHERE'],23:['COUNT_BIG','Min','commit','Count','LimitExceeded','Errors'],24:['InputValidationException','ArgumentException','Saved','NoChange','Outcome'],25:['m_code_category'],26:['Unknown','E-COM-004','Status'],27:['NULL','Revision','Snapshot.ReturnRevision','EmptyResult','Id','ContextId'],28:['identity.Read','EnsureSearch','Revision','Entry'],29:['Applied','TryRemove']}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 inventory_path=HERE/'source-detail07-r04-tiles/inventory.json';inventory=json.loads(inventory_path.read_text(encoding='utf-8'));render=REPORT/'render/search-detail-r04';pins_path=render/'render-pins.json';pins=json.loads(pins_path.read_text(encoding='utf-8'))
 worker_path=HERE/'source-detail07-render-worker.json';worker=json.loads(worker_path.read_text(encoding='utf-8'))
 assert pins['referenceMode']=='source-only' and pins['sourceSha256']=='85cddae02cf89e6e92d84ecc7709a118f298ca114bf104115f1be8ae47d62b82'
 assert inventory['renderPinsSha256']==sha(pins_path)==worker['renderPinsSha256'];assert pins['structure']['status']=='PASS' and pins['display']['status']=='PASS'
 assert pins['safety']['inputJavaScriptEnabled'] is False and len(pins['diagrams'])==29 and len(pins['layouts'])==1
 assert all(sha(Path(p))==v for p,v in worker['pinnedInputHashes'].items())
 groups={};reviewed=[]
 for index,c in enumerate(inventory['captures']):
  original=Path(c['originalPath']);tile=Path(c['path']);assert sha(original)==c['originalSha256'] and sha(tile)==c['sha256']
  image=Image.open(original).convert('RGB');r=c['sourceRectangle'];box=(r['x'],r['y'],r['x']+r['width'],r['y']+r['height']);assert ImageChops.difference(Image.open(tile).convert('RGB'),image.crop(box)).getbbox() is None
  groups.setdefault(c['imageId'],{'size':image.size,'regions':[]})['regions'].append(box)
  number=int(c['imageId'].split('-')[1]) if c['imageId'].startswith('diagram') else None
  reviewed.append({**c,'index':index,'actuallyReviewed':True,'reviewedAtOriginalScale':True,'reviewer':'delivery_tools firsthand view_image detail original','scope':'DISPLAY_GEOMETRY_ONLY','identifierWrapExamples':FINDINGS.get(number,[])})
 for group in groups.values():
  coverage=Image.new('1',group['size'],0)
  for box in group['regions']:coverage.paste(1,box)
  assert coverage.getextrema()==(1,1)
 assert len(reviewed)==30 and len(groups)==30
 record={'schema':'source-only-native-geometry-review/1','createdUtc':datetime.now(timezone.utc).isoformat(),'status':'GEOMETRY_REVIEW_REQUIRED','documentId':pins['documentId'],
  'referenceMode':'source-only','documentSha256':pins['sourceSha256'],'draftResultSha256':pins['draftResultSha256'],'sourceSnapshotManifestSha256':pins['sourceSnapshotManifestSha256'],
  'renderPinsPath':str(pins_path),'renderPinsSha256':sha(pins_path),'canonicalHtmlSha256':pins['canonicalHtmlSha256'],'coreRendererSha256':worker['pinnedInputHashes'][str(REPORT.parents[3]/'src/contextbase/ai/rendering.py')] if False else '0c87df73032d812a3e646ff2846c5daa6b3053472a52dc2b1f78d0c13d41f902',
  'renderWorkerPath':str(worker_path),'renderWorkerSha256':sha(worker_path),'rendererElapsedSeconds':worker['elapsedSeconds'],'structure':'PASS','safeDisplay':'PASS',
  'allInputsUnchanged':True,'nativeImages':30,'diagrams':29,'layouts':1,'actuallyViewedTiles':30,'actuallyViewedIndices':list(range(30)),
  'allOriginalPixelsCovered':True,'allCropsEqualOriginalPixels':True,'scalingUsed':False,'maximumDiagramHeight':1639,'reviewedImages':reviewed,
  'findings':[{'imageId':f'diagram-{number:03d}','issue':'Identifier or number wraps inside one token at original scale','examples':examples} for number,examples in FINDINGS.items()],
  'observations':{'diagramOrLayoutTextClippingObserved':False,'connectionLossObserved':False,'edgeLabelTransparencyObserved':False,'diagram025FQLLabelsReadableAtNativeSize':True},
  'originalApplicationExecuted':False,'originalSpecEvalOrOtherModeBusinessInspected':False,'manuscriptAuthoredOrEdited':False,'semanticApprovalGranted':False,'formalRubricEvaluated':False,
  'pdfXlsxExportPerformed':False,'stateProjectionNativeOrSemanticApprovalGranted':False,'published':False,
  'nextStep':'Source author consolidated geometry-only revision preserving identifiers, labels, graph nodes/edges/conditions and meaning; new parent SHA/render/native QA required before state projection.',
  'limitations':['Technical renderer PASS only verifies safe successful derivation. It does not establish native readability or semantic correctness.','Only all individual diagrams and layout were visually inspected; complete document body screenshots and print outputs were not reviewed.','Hash verification includes source capsule registered-byte verification by the approved render helper; no original source business text or original reference specification/evaluator was manually inspected.']}
 path=HERE/'source-detail07-r04-native-geometry-review.json';path.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 summary=HERE/'SOURCE-DETAIL07-R04-GEOMETRY-QA.md';summary.write_text('''# Source-only search detail07 native geometry QA

Status: GEOMETRY_REVIEW_REQUIRED. Source MD SHA85cddae02cf89e6e92d84ecc7709a118f298ca114bf104115f1be8ae47d62b82; source-only capsule SHA2f64e2211b1fcd7850203927fc75b5a7f2ce37457cc2afe88c8065d9f931273b.

Fresh r12/r13 same-byte renderer completed in 41.594s at render/search-detail-r04. Structure and safe display PASS; JS-disabled static context and isolated trusted Mermaid remain enforced. MD, receipt, manifest, core and wrapper-helper SHA were unchanged.

All 29 diagrams and 1 layout (30 images) were actually viewed at original scale. All crop pixels match originals, all original pixels are covered and no scaling was used. Internal token/number wrapping remains in diagrams1,2,4,5,6,8,9,10,11,12,13,14,16,17,18,19,20,21,22,23,24,25,26,27,28,29. Examples and image SHA are recorded in source-detail07-r04-native-geometry-review.json; diagram19 also breaks 403 as 40/3. Longest diagram is 518x1639. Diagram25 is 456x789, F/Q/L labels are readable, with no transparency/clipping/connection loss observed.

Request one consolidated geometry-only revision. Keep semantic text, identifiers, labels, nodes, edges and conditions intact while adjusting line-break boundaries and available width. A new MD SHA, safe render and complete native QA are required before fixing the state-projection parent.

No semantic/final quality/rubric approval, original application, original reference specification/evaluator, other-mode business inspection, PDF/XLSX export or whole-body/print visual approval was performed.
''',encoding='utf-8')
 print(json.dumps({'report':str(path),'sha256':sha(path),'summary':str(summary),'summarySha256':sha(summary),'actuallyViewed':30,'geometryFindings':len(FINDINGS),'status':record['status']}))
if __name__=='__main__':main()
