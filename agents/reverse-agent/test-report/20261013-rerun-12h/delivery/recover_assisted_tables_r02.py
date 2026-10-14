"""Read immutable completed renders and recover only fresh QA crops after failed adapter."""
from datetime import datetime,timezone
from pathlib import Path
import json
from PIL import Image,ImageChops
from delivery_model import load_bound,safe_path,sha
HERE=Path(__file__).resolve().parent
def digest(p):return sha(safe_path(p).read_bytes())
def read(p):return json.loads(safe_path(p).read_bytes())
def main():
 binding=HERE/'binding-assisted-tables-r02.json';bound,entries,prov=load_bound(binding)
 qa=HERE/'html-assisted-tables-r02b';qa.mkdir(exist_ok=False);docs=[];inputs={}
 for e in entries:
  rootpin=Path(e['rootReviewedPin']);pin=read(rootpin)
  assert digest(rootpin)==e['rootReviewedPinSha256']
  for p in [rootpin,Path(e['markdown']),Path(e['draftResult']),Path(e['separateApprovedReview']['handoff']),Path(e['separateApprovedReview']['review'])]:inputs[str(p)]=digest(p)
  for role in ['generationRuntime','reviewRuntime','structureRuntime']:
   p=Path(pin[role]['record']);assert digest(p)==pin[role]['recordSha256'];inputs[str(p)]=digest(p)
  for item in pin['frozenImports'].values():
   p=Path(item['path']);assert digest(p)==item['sha256'];inputs[str(p)]=digest(p)
  render=Path(e['renderDirectory']);meta=read(render/'render-pins.json')
  inputs[str(render/'render-pins.json')]=digest(render/'render-pins.json');inputs[str(render/'manifest.json')]=digest(render/'manifest.json')
  capture=meta['display'].get('documentCapture') or meta['display']['documentPng']
  chunks=capture['pages'] if capture.get('mode')=='complete-vertical-tiles' else [{'path':'document.png','sourceRectangle':{'x':0,'y':0,'width':capture['width'],'height':capture['height']}}]
  target=qa/Path(e['canonicalDocumentPath']).stem;target.mkdir()
  record={'documentId':e['documentId'],'canonicalDocumentPath':e['canonicalDocumentPath'],'markdownSha256':e['markdownSha256'],'canonicalHtmlSha256':digest(e['canonicalHtml']),'dimensions':[capture['width'],capture['height']],'originalCapturePages':[],'crops':[],'visualReview':'PENDING','formalQualityGatePassed':False,'published':False}
  covered=0;ordinal=0
  for chunk in chunks:
   source=render/chunk['path'];r=chunk['sourceRectangle'];assert r['x']==0 and r['y']==covered;covered+=r['height'];inputs[str(source)]=digest(source)
   record['originalCapturePages'].append({'path':str(source),'sha256':digest(source),'sourceRectangle':r})
   with Image.open(source) as image:
    assert list(image.size)==[r['width'],r['height']];end=0
    for y in range(0,image.height,1120):
     ordinal+=1;box=(0,y,image.width,min(y+1200,image.height));crop=target/f'document-{ordinal:03d}.png';image.crop(box).save(crop)
     with Image.open(crop) as actual:assert ImageChops.difference(image.crop(box),actual).getbbox() is None
     assert y<=end;end=max(end,box[3]);record['crops'].append({'path':str(crop),'sha256':digest(crop),'sourcePng':str(source),'sourcePngSha256':digest(source),'sourceRectangle':list(box),'absoluteCanvasRectangle':[box[0],r['y']+box[1],box[2],r['y']+box[3]],'overlapPixels':80,'actuallyViewed':False})
    assert end==image.height
  assert covered==capture['height'];record.update(cropFullCanvasCoverage=True,cropPixelEquality=True);docs.append(record)
 load_bound(binding);assert all(digest(p)==h for p,h in inputs.items())
 report={'schema':'reverse-agent-table-html-preparation/2','createdUtc':datetime.now(timezone.utc).isoformat(),'binding':str(binding),'bindingSha256':digest(binding),'referenceMode':bound['referenceMode'],'sourceSnapshotManifestSha256':bound['sourceSnapshotManifestSha256'],'rendererCoreAtPreparationSha256':meta['rendererCodeSha256'],'originalsModified':False,'specAndSpecEvalRead':False,'applicationExecuted':False,'visualReview':'PENDING','formalQualityGatePassed':False,'published':False,'allInputHashes':inputs,'allInputsUnchanged':True,'documents':docs,'recovery':{'failedScript':str(HERE/'prepare_assisted_tables_r02.py'),'failedScriptSha256':digest(HERE/'prepare_assisted_tables_r02.py'),'reason':'single full-height capture is display.documentPng, not documentCapture','failedWorkerRecord':str(HERE/'assisted-tables-r02-render-worker.json'),'priorFailedCandidatePreserved':True,'rendersAndBindingReusedReadOnly':True}}
 with (qa/'qa.json').open('x',encoding='utf8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
 print(json.dumps({'qa':str(qa/'qa.json'),'sha256':digest(qa/'qa.json'),'crops':sum(len(d['crops']) for d in docs)},ensure_ascii=False))
if __name__=='__main__':main()
