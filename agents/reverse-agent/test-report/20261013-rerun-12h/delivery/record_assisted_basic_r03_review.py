"""Record images actually seen, geometry-only findings and unchanged byte pins."""
from __future__ import annotations
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
HERE=Path(__file__).resolve().parent;REPORT=HERE.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
SEARCH_FINDINGS={7:['Applied','finally'],8:['DivideByZeroException'],10:['/students/options','ModelState'],11:['m_code_category'],13:['LastResult'],14:['Status'],15:['m_code_category'],16:['NULL'],17:['m_code_category'],18:['Form','Lookups','Snapshot'],19:['StudentSaveInput.Form','Lookups','Original'],20:['m_code_category'],21:['Resume'],24:['m_code_category'],25:['student_id','class_id','m_code_category'],26:['Message']}
REGISTER_FINDINGS={1:['Snapshot'],2:['m_code_category'],3:['Snapshot'],4:['StudentSaveInput','m_code_category'],6:['disabled'],7:['SaveRequest'],8:['SaveRequest','ArgumentException','ReadCommitted'],10:['NULL'],11:['writeStarted=true','DBConcurrencyException','commitAttempted=true'],12:['InputValidationException','DBConcurrencyException','SqlException','OperationCanceledException','writeStarted=true','commitAttempted=true','NULL'],13:['422','WebFault','ModelState'],14:['m_code_category'],15:['UPDATE'],17:['NULL','commit','finally'],20:['ReadCommitted','writeStarted=true','DBConcurrencyException','commitAttempted=true'],21:['DBConcurrencyException','OperationCanceledException','writeStarted=true','commitAttempted=true','SystemError'],22:['Snapshot'],24:['Snapshot','SnapshotId'],26:['LastResult'],27:['Applied'],28:['Gate','SearchAsync','LastResult'],29:['Revision','JOIN','FlashMessageStore']}
def main():
 search_path=REPORT/'visual-review/assisted-search-basic-r03-tiles/inventory.json';register_path=HERE/'assisted-register-basic-r03-tiles/inventory.json'
 docs=[]
 for name,path,findings,root_reviewed in [('search',search_path,SEARCH_FINDINGS,6),('registration',register_path,REGISTER_FINDINGS,0)]:
  inventory=json.loads(path.read_text(encoding='utf-8'));reviewed=[]
  for i,c in enumerate(inventory['captures']):
   assert sha(Path(c['path']))==c['sha256'] and sha(Path(c['originalPath']))==c['originalSha256']
   record={**c,'actuallyReviewed':True,'reviewedAtOriginalScale':True,'reviewer':'root firsthand review' if i<root_reviewed else 'delivery_tools firsthand view_image original',
           'mechanicalCaptureOnly':True,'review':'GEOMETRY_ONLY'}
   record['nativeGeometryFindings']=findings.get(int(c['imageId'].split('-')[1]),[]) if c['imageId'].startswith('diagram') else []
   reviewed.append(record)
  pins_path=REPORT/('render/assisted-search-basic-r03/render-pins.json' if name=='search' else 'render/assisted-register-basic-r03-delivery/render-pins.json')
  pins=json.loads(pins_path.read_text(encoding='utf-8'));assert sha(Path(pins['source']))==pins['sourceSha256']
  assert sha(pins_path)==inventory['renderPinsSha256']
  defects=[{'imageId':f'diagram-{i:03d}','finding':'Identifier/number breaks inside token at native size','examples':labels} for i,labels in findings.items()]
  if name=='search':
   defects.insert(0,{'imageId':'diagrams-001-to-006','finding':'Root firsthand review recorded LastResult/m_code_category/Page=1/10001/exception-identifier internal wrapping; delivery review did not re-inspect these six.'})
  else:deffects_extra=None
  if name=='registration':
   defects.append({'imageId':'diagram-014','finding':'Central parallel relationship labels sit adjacent and read as one run; increase spacing while preserving labels, nodes and relationships.'})
   defects.append({'imageId':'diagram-019','finding':'1052x3028 native image requires print projection/review; if geometry manuscript is revised, preserve complete graph and explicit continuation.'})
  docs.append({'name':name,'documentSha256':pins['sourceSha256'],'renderPinsPath':str(pins_path),'renderPinsSha256':sha(pins_path),'canonicalHtmlSha256':pins['canonicalHtmlSha256'],
   'draftResultSha256':pins['draftResultSha256'],'sourceSnapshotManifestSha256':pins['sourceSnapshotManifestSha256'],'referenceMode':'training-assisted',
   'status':'GEOMETRY_REVIEW_REQUIRED','actualImageCount':len({c['imageId'] for c in reviewed}),'actuallyViewedTiles':len(reviewed),'deliveryFirsthandViewedTiles':len(reviewed)-root_reviewed,'rootFirsthandViewedTiles':root_reviewed,
   'findings':defects,'reviewedImages':reviewed,'observations':{'cropConnectionLossObserved':False,'clippedDiagramTextObserved':False,'edgeLabelTransparencyObserved':False,'layoutTextClippingObserved':False},
   'diagramMaximumHeight':max(c['wholeOriginalSize'][1] for c in reviewed if c['imageId'].startswith('diagram'))})
 record={'schema':'assisted-basic-native-geometry-review/1','createdUtc':datetime.now(timezone.utc).isoformat(),'status':'GEOMETRY_REVIEW_REQUIRED',
  'documents':docs,'allNativeTilesActuallyViewed':True,'totalViewedTiles':sum(d['actuallyViewedTiles'] for d in docs),'mechanicalEvidence':str(HERE/'assisted-basic-r03-mechanical-geometry.json'),
  'mechanicalEvidenceSha256':sha(HERE/'assisted-basic-r03-mechanical-geometry.json'),'inputManuscriptsRendererAndImagesUnchanged':True,
  'originalSourceSpecEvalRead':False,'originalApplicationExecuted':False,'manuscriptAuthoredOrEdited':False,'formalRubricEvaluated':False,'finalQualityApproved':False,
  'fullPdfOrXlsxExportPerformed':False,'auxiliaryStateQualityApproved':False,'coreRendererSha256':'0c87df73032d812a3e646ff2846c5daa6b3053472a52dc2b1f78d0c13d41f902',
  'nextStep':'Assisted author should consolidate geometry-only revisions with complete normalized label/node/edge/condition preservation, then rerender and repeat native QA.'}
 path=HERE/'assisted-basic-r03-native-geometry-review.json';path.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 report=HERE/'ASSISTED-BASIC-R03-GEOMETRY-QA.md';report.write_text('''# Assisted basic r03 native geometry QA

Status: GEOMETRY_REVIEW_REQUIRED. This is a display QA candidate; no final quality or rubric approval.

Search: source SHA ab84038bc61a3ed4fac0093067c0c28007d75a72dd5f48528d8887043ead8bec. All 29 native tiles (26 diagrams and 1 layout) were actually seen: root first 6, delivery_tools remaining 23. Internal token wrapping remains in root findings and diagrams 7,8,10,11,13,14,15,16,17,18,19,20,21,24,25,26. Longest image 1779px.

Registration: source SHA efba87eb3db5f99a4df0afba2e607ccc9a36cf3fb2f3e3c615f63d20f3763e44. Fresh r12 render completed in 54.89s. All 40 native tiles of 29 diagrams and 2 layouts were actually seen by delivery_tools. Internal token/number wrapping remains in diagrams 1,2,3,4,6,7,8,10,11,12,13,14,15,17,20,21,22,24,26,27,28,29. ER diagram14 adjacent parallel-edge labels need more space. Diagram19 is 1052x3028; diagrams1,7,9,10,12 also exceed 2000px and require print projection QA.

Both image sets mechanically cover every original pixel with no scaling, and every crop exactly matches the corresponding original region. Original SHA and crop geometry are recorded per actual view in assisted-basic-r03-native-geometry-review.json. No crop connection loss, diagram text clipping, edge-label transparency or layout clipping was observed. These observations do not establish semantic correctness.

The first registration wrapper failed before renderer import due to a receipt-key mistake; failed logs are preserved. Fresh log r02 completed after metadata-key correction. Input manuscript, renderer and immutable image SHA checks passed. No original application, source/spec/eval, full PDF/XLSX export or formal grading was run.

Next: author one consolidated geometry revision preserving text meaning, normalized identifiers, nodes, edges and conditions. Rerender the new SHA and repeat original-scale QA before exports. Detailed screen state quality remains a separate unapproved gate.
''',encoding='utf-8')
 print(json.dumps({'report':str(path),'sha256':sha(path),'summary':str(report),'summarySha256':sha(report),'tilesSeen':record['totalViewedTiles'],'status':record['status']}))
if __name__=='__main__':main()
