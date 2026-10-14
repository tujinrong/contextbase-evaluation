"""Finalize the actually viewed immutable operation-log derivative scope only."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
from delivery_model import load_bound,safe_path
from prepare_assisted_index_oplog_r01 import inventory
HERE=Path(__file__).resolve().parent
def digest(p):return hashlib.sha256(safe_path(p).read_bytes()).hexdigest()
def read(p):return json.loads(safe_path(p).read_bytes())
def main():
 qa_path=HERE/'assisted-operation-log-r01-mechanical-qa.json';qa=read(qa_path)
 inv_path=HERE/'native-assisted-operation-log-r01/inventory.json';inv=read(inv_path)
 prep=read(qa['rendererPreparation']['qa']);before=prep['allInputHashes']
 assert all(digest(p)==s for p,s in before.items()) and len(inventory())==124
 load_bound(HERE/'binding-assisted-index-oplog-r01.json')
 counts={f:sum(i['format']==f for i in inv['images']) for f in ['html','pdf','xlsx']}
 assert counts=={'html':7,'pdf':35,'xlsx':13} and inv['allOriginalPixelsCovered'] is True
 images=[]
 for item in inv['images']:
  assert digest(item['path'])==item['sha256']
  if 'sourcePng' in item:assert digest(item['sourcePng'])==item['sourcePngSha256']
  images.append({**item,'actuallyViewed':True,'visualReview':'PASS','scale':'original pixels'})
 doc=qa['documents'][0];artifacts=[]
 for folder in ['html-assisted-index-oplog-r01','pdf-assisted-index-oplog-r01','xlsx-assisted-index-oplog-r01']:
  for p in (HERE/folder).rglob('05_t_operation_log.*'):
   if p.suffix in ['.html','.pdf','.xlsx']:artifacts.append({'path':str(p),'sha256':digest(p)})
 assert sorted(Path(x['path']).suffix for x in artifacts)==['.html','.pdf','.xlsx']
 result={'schema':'reverse-agent-native-delivery-final-qa/1','createdUtc':datetime.now(timezone.utc).isoformat(),
  'status':'DERIVED_FORMATS_VERIFIED_NATIVE_55_IMAGES_REVIEWED','referenceMode':'training-assisted',
  'documentId':doc['documentId'],'canonicalDocumentPath':doc['canonicalDocumentPath'],
  'markdown':doc['markdown'],'markdownSha256':doc['markdownSha256'],
  'mechanicalQa':str(qa_path),'mechanicalQaSha256':digest(qa_path),'nativeInventory':str(inv_path),'nativeInventorySha256':digest(inv_path),
  'artifacts':artifacts,'actuallyViewedCounts':counts,'images':images,
  'visualFindings':[],'layoutNotes':['PDF pagination conservatively uses two source body rows per page and leaves whitespace.','Long identifiers within table cells may soft-wrap; full literal values and empty-cell positions are preserved.','Artifact native previews precede the permitted print-metadata connection; strict saved XLSX XML is separately verified.'],
  'frozenRendererRevision':'assisted06-r14','frozenRendererSha256':prep['rendererCoreAtPreparationSha256'],
  'runtimeReceipt':prep['frozenRenderRuntimeReceipt'],'runtimeReceiptSha256':prep['frozenRenderRuntimeReceiptSha256'],
  'frozenRuntime124FilesUnchanged':True,'allInputHashesRechecked':before,'inputsAndReceiptsUnchanged':True,
  'indexKnownFailCandidate':'index-oplog-r01-native-failure.json','index152PdfPagesViewed':False,
  'formalQualityGatePassed':False,'published':False,'formalScoring':'PARENT_CONTROLLED_SEPARATE_GATE',
  'originalMarkdownEdited':False,'originalApplicationOrDbExecuted':False,'specOrSpecEvalRead':False,'mainRendererReadOrEdited':False,
  'artifactToolAuthoringMarkerReexecuted':False,'liveExcelWholeWorkbookDisplayOrPrinting':'NOT_EXECUTED'}
 out=HERE/'assisted-operation-log-r01-final-qa.json'
 with out.open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps({'path':str(out),'sha256':digest(out),'actualImages':counts,'artifacts':artifacts},ensure_ascii=False))
if __name__=='__main__':main()
