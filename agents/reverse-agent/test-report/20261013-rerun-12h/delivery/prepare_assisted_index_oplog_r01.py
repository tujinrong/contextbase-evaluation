"""Fresh metadata-pinned r14 derivation, no business or original-reference reads."""
from __future__ import annotations
import argparse,faulthandler,json,subprocess,sys,time,importlib
from datetime import datetime,timezone
from pathlib import Path
from PIL import Image,ImageChops
from delivery_model import load_bound,safe_path,sha
HERE=Path(__file__).resolve().parent;REPORT=HERE.parent;REPO=HERE.parents[4]
MDROOT=REPO/'test-project1/spec-analysis/CSharp_ASPNET/20261013-rerun-12h/training-assisted/drafts'
CAP='e76a6c40e8927011fff9145d5f5ab2fa94ad89acefc9a03bbad0cbf09b85a0e7'
CASES=[('table-index','reviewed-table-index-r11-pin.json','ae577fa6d45350b3fbf7f2676591412f3ab82a033d05a6e4ded535924fb09f1f'),('operation-log','reviewed-operation-log-r11-pin.json','2c0d9eaff9aceb6fb58f7a3271b090e8b2555d8d4dc7e487db56fba3d81b9613')]
RUNTIME=REPO/'agents/reverse-agent/.tmp/20261013-rerun-12h/training-assisted/runtime-code/assisted-06/src'
RUNTIME_RECEIPT=REPORT/'training-assisted/runtime-code-assisted-06.json'
RUNTIME_RECEIPT_SHA='9ef12bc2f6412bddfd9f4d8de45d25f9e5eff1ab31402808d97023aaf6a846e3'
CORE=RUNTIME/'contextbase/ai/rendering.py';CORE_SHA='5202a097b51e2a511b2209c19019f552d43b8eabfac6db0a018ba99d224f7be7'
def digest(p):return sha(safe_path(p).read_bytes())
def read(p):return json.loads(safe_path(p).read_bytes())
def write(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def log(stage,**kw):print(json.dumps({'stage':stage,'utc':datetime.now(timezone.utc).isoformat(),**kw},ensure_ascii=False),flush=True)
def inventory():
 assert digest(RUNTIME_RECEIPT)==RUNTIME_RECEIPT_SHA
 receipt=read(RUNTIME_RECEIPT);assert safe_path(receipt['destination'])==safe_path(RUNTIME)
 actual={}
 for item in safe_path(RUNTIME).rglob('*'):
  safe_path(item)
  if item.is_file() and '__pycache__' not in item.parts and item.suffix!='.pyc':actual[item.relative_to(RUNTIME).as_posix()]=digest(item)
 assert actual==receipt['files'] and len(actual)==receipt['fileCount']==124
 return actual
def worker():
 faulthandler.enable();faulthandler.dump_traceback_later(90,repeat=True)
 before_inventory=inventory();rendering=importlib.import_module('contextbase.ai.rendering')
 assert safe_path(rendering.__file__)==safe_path(CORE) and digest(CORE)==CORE_SHA
 render_document=rendering.render_document;documents=[];qa_docs=[];before={str(RUNTIME_RECEIPT):RUNTIME_RECEIPT_SHA}
 for name,pinname,pinsha in CASES:
  rootpin=REPORT/'training-assisted'/pinname;assert digest(rootpin)==pinsha;pin=read(rootpin)
  md=safe_path(pin['canonicalMarkdown']);receipt=safe_path(pin['draftResult']);review=safe_path(pin['independentReview']);handoff=review.with_name('review-handoff.json')
  assert md.is_relative_to(safe_path(MDROOT)) and digest(md)==pin['sha256'] and digest(receipt)==pin['draftResultSha256'] and digest(review)==pin['independentReviewSha256']
  assert pin['capsule']['mode']=='training-assisted' and pin['capsule']['manifestSha256']==CAP and pin['independentReviewApproved'] is True and pin['noFurtherTextRevisionPlanned'] is True
  assert pin['structureStatus']=='STRUCTURE_VALID' and pin['structureFindings']==[]
  draft=read(receipt);approval=read(handoff);verified=read(review)
  assert draft['contentSha256']==approval['documentSha256']==pin['sha256'] and verified['approved'] is True and verified['findings']==[]
  assert approval['approved'] is True and approval['reviewSha256']==digest(review) and safe_path(approval['documentFile'])==md
  assert draft['referenceMode']==approval['referenceMode']=='training-assisted' and approval['snapshot']['manifestSha256']==draft['snapshot']['manifestSha256']==CAP
  for p in [rootpin,md,receipt,review,handoff,CORE]:before[str(p)]=digest(p)
  for role in ['generationRuntime','reviewRuntime','structureRuntime']:
   p=safe_path(pin[role]['record']);assert digest(p)==pin[role]['recordSha256'];before[str(p)]=digest(p)
  for item in pin['frozenImports'].values():
   p=safe_path(item['path']);assert digest(p)==item['sha256'];before[str(p)]=digest(p)
  render=REPORT/'render'/('assisted-'+name+'-r01-delivery-r14');assert not render.exists();log('render-start',documentId=pin['documentId'],render=str(render))
  result=render_document(md,render,document_path=pin['path'],asset_root=safe_path(pin['outputRoot']),mermaid_package=REPO/'agents/reverse-agent/.tmp/render-tools/node_modules/mermaid',chromium_executable=Path('C:/Users/tujin/AppData/Local/ms-playwright/chromium-1223/chrome-win64/chrome.exe'))
  assert result['structure']['status']=='PASS' and result['display']['status']=='PASS' and result['safety']['removed']==[] and not result['safety']['inputJavaScriptEnabled']
  canonical=render/(Path(pin['path']).stem+'.html');canonical.write_bytes((render/'document.html').read_bytes())
  result.update({'documentId':pin['documentId'],'canonicalDocumentPath':pin['path'],'canonicalHtmlFilename':canonical.name,'canonicalHtmlSha256':digest(canonical),'sourceSnapshotManifestSha256':CAP,'draftResultSha256':digest(receipt),'referenceMode':'training-assisted','originalApplicationExecuted':False,'visualFidelityVerified':False,'formalRubricEvaluated':False,'rendererCodeSha256':CORE_SHA,'frozenRenderRuntimeReceipt':str(RUNTIME_RECEIPT),'frozenRenderRuntimeReceiptSha256':RUNTIME_RECEIPT_SHA,'separateReviewedPin':str(rootpin),'separateReviewedPinSha256':pinsha,'createdAt':datetime.now(timezone.utc).isoformat()})
  write(render/'render-pins.json',result)
  documents.append({'documentId':pin['documentId'],'canonicalDocumentPath':pin['path'],'markdown':str(md),'markdownSha256':pin['sha256'],'renderDirectory':str(render),'renderPinsSha256':digest(render/'render-pins.json'),'renderManifestSha256':digest(render/'manifest.json'),'draftResult':str(receipt),'draftResultSha256':digest(receipt),'rootReviewedPin':str(rootpin),'rootReviewedPinSha256':pinsha,'separateApprovedReview':{'handoff':str(handoff),'handoffSha256':digest(handoff),'review':str(review),'reviewSha256':digest(review),'approved':True,'scope':'text-source-and-structure; no original rubric/runtime review'}})
  qa_docs.append({'documentId':pin['documentId'],'canonicalDocumentPath':pin['path'],'markdownSha256':pin['sha256'],'canonicalHtmlSha256':digest(canonical),'crops':[],'visualReview':'PENDING','formalQualityGatePassed':False,'published':False});log('render-complete',documentId=pin['documentId'],htmlSha256=digest(canonical))
 binding=HERE/'binding-assisted-index-oplog-r01.json';write(binding,{'schema':'reverse-agent-delivery-binding/1','referenceMode':'training-assisted','permittedMarkdownRoot':str(MDROOT),'permittedRenderRoot':str(REPORT/'render'),'sourceSnapshotManifestSha256':CAP,'formalQualityGatePassed':False,'documents':documents});load_bound(binding)
 qa_dir=HERE/'html-assisted-index-oplog-r01';qa_dir.mkdir()
 for document,record in zip(documents,qa_docs,strict=True):
  render=Path(document['renderDirectory']);meta=read(render/'render-pins.json');target=qa_dir/Path(document['canonicalDocumentPath']).stem;target.mkdir()
  capture=meta['display'].get('documentCapture') or meta['display']['documentPng'];chunks=capture['pages'] if capture.get('mode')=='complete-vertical-tiles' else [{'path':'document.png','sourceRectangle':{'x':0,'y':0,'width':capture['width'],'height':capture['height']}}]
  record['dimensions']=[capture['width'],capture['height']];record['originalCapturePages']=[];covered=0;ordinal=0
  for chunk in chunks:
   source=render/chunk['path'];r=chunk['sourceRectangle'];assert r['x']==0 and r['y']==covered;covered+=r['height'];record['originalCapturePages'].append({'path':str(source),'sha256':digest(source),'sourceRectangle':r})
   with Image.open(source) as im:
    assert list(im.size)==[r['width'],r['height']];end=0
    for y in range(0,im.height,1120):
     ordinal+=1;box=(0,y,im.width,min(y+1200,im.height));crop=target/f'document-{ordinal:03d}.png';im.crop(box).save(crop)
     with Image.open(crop) as actual:assert ImageChops.difference(im.crop(box),actual).getbbox() is None
     assert y<=end;end=max(end,box[3]);record['crops'].append({'path':str(crop),'sha256':digest(crop),'sourcePng':str(source),'sourcePngSha256':digest(source),'sourceRectangle':list(box),'absoluteCanvasRectangle':[box[0],r['y']+box[1],box[2],r['y']+box[3]],'overlapPixels':80,'actuallyViewed':False})
    assert end==im.height
  assert covered==capture['height'];record['cropFullCanvasCoverage']=True;record['cropPixelEquality']=True
 assert inventory()==before_inventory and all(digest(Path(p))==v for p,v in before.items())
 write(qa_dir/'qa.json',{'schema':'reverse-agent-pinned-html-preparation/3','createdUtc':datetime.now(timezone.utc).isoformat(),'binding':str(binding),'bindingSha256':digest(binding),'referenceMode':'training-assisted','sourceSnapshotManifestSha256':CAP,'rendererCoreAtPreparationSha256':CORE_SHA,'frozenRenderRuntimeReceipt':str(RUNTIME_RECEIPT),'frozenRenderRuntimeReceiptSha256':RUNTIME_RECEIPT_SHA,'frozenRuntime124FilesUnchanged':True,'mainRendererReadOrUsed':False,'originalsModified':False,'specAndSpecEvalRead':False,'applicationExecuted':False,'visualReview':'PENDING','formalQualityGatePassed':False,'published':False,'allInputHashes':before,'allInputsUnchanged':True,'documents':qa_docs});log('preparation-complete',bindingSha256=digest(binding),documents=len(documents),htmlCrops=sum(len(d['crops']) for d in qa_docs))
def main():
 p=argparse.ArgumentParser();p.add_argument('--worker',action='store_true');args=p.parse_args()
 if args.worker:return worker()
 out=HERE/'assisted-index-oplog-r01-render-stage.log';err=HERE/'assisted-index-oplog-r01-render-stderr.log';started=time.monotonic();status='UNKNOWN';code=None
 with out.open('xb') as stdout,err.open('xb') as stderr:
  process=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--worker'],stdout=stdout,stderr=stderr);log('owned-worker',pid=process.pid,timeoutSeconds=240)
  try:code=process.wait(timeout=240);status='COMPLETE' if code==0 else 'FAILED'
  except subprocess.TimeoutExpired:
   status='TIMED_OUT';subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True,timeout=20);process.wait(timeout=15)
 record={'status':status,'ownedWorkerPid':process.pid,'exitCode':code,'elapsedSeconds':round(time.monotonic()-started,3),'applicationExecuted':False};write(HERE/'assisted-index-oplog-r01-render-worker.json',record);log('worker-final',**record);return 0 if status=='COMPLETE' else 1
if __name__=='__main__':sys.exit(main() or 0)
