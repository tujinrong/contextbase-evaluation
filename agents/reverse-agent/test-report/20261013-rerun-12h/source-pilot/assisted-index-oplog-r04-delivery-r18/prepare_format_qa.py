"""Hash-only canonical binding, native PDF pages, exact-RGBA XLSX crops."""
import hashlib,json,os
from pathlib import Path
from datetime import datetime,timezone
from PIL import Image,ImageDraw
HERE=Path(__file__).absolute().parent
def safe(p):
 p=Path(os.path.abspath(p))
 for a in (p,*p.parents):
  if a.is_symlink() or (a.exists() and getattr(a.lstat(),'st_file_attributes',0)&0x400):raise ValueError('Linked input refused before read')
 return p
def sha(p):return hashlib.sha256(safe(p).read_bytes()).hexdigest()
def load(p):return json.loads(safe(p).read_bytes())
binding=HERE/'binding.json';model=HERE/'model-r01.json';pdfmanifest=HERE/'pdf-r01/delivery-manifest.json';xlmanifest=HERE/'xlsx-r01/delivery-manifest.json'
b=load(binding);pdf=load(pdfmanifest);xl=load(xlmanifest)
assert sha(binding)=='f35938dea33a2abec797c06ecee0039cb031193a1e616f7647918a841ccbe366'
assert pdf['bindingSha256']==sha(binding) and pdf['referenceMode']=='training-assisted'
pins={str(p):sha(p) for p in [binding,model,pdfmanifest,xlmanifest,HERE/'native-review.json']}
docs={d['documentId']:d for d in b['documents']}
for d in b['documents']:
 for p,k in [(d['markdown'],'markdownSha256'),(d['draftResult'],'draftResultSha256'),(d['rootReviewedPin'],'rootReviewedPinSha256')]:
  assert sha(p)==d[k];pins[p]=d[k]
 for key in ['handoff','review']:
  p=d['separateApprovedReview'][key];assert sha(p)==d['separateApprovedReview'][key+'Sha256'];pins[p]=sha(p)
 for file,key in [('render-pins.json','renderPinsSha256'),('manifest.json','renderManifestSha256')]:
  p=safe(Path(d['renderDirectory'])/file);assert sha(p)==d[key];pins[str(p)]=sha(p)
pages=[]
for d in pdf['documents']:
 parent=docs[d['documentId']];assert d['markdownSha256']==parent['markdownSha256'] and d['textCoverage']=='PASS'
 assert sha(d['pdf'])==d['pdfSha256'];pins[d['pdf']]=d['pdfSha256']
 for i,page in enumerate(d['pageImages'],1):
  assert sha(page['path'])==page['sha256'];pins[page['path']]=page['sha256']
  with Image.open(safe(page['path'])) as im:sz=list(im.size)
  pages.append({'documentId':d['documentId'],'page':i,'path':page['path'],'sha256':page['sha256'],'nativeSize':sz,'scale':1,'actuallyViewed':False})
assert len(pages)==49
out=HERE/'xlsx-native-r01';assert not out.exists();out.mkdir();captures=[];preview_counts={}
for d in xl['documents']:
 assert d['markdownSha256']==docs[d['documentId']]['markdownSha256']
 assert sha(d['xlsx'])==d['xlsxSha256'];pins[d['xlsx']]=d['xlsxSha256']
 target=out/d['documentId'];target.mkdir();preview_counts[d['documentId']]=len(d['previews'])
 for ordinal,preview in enumerate(d['previews'],1):
  assert sha(preview['path'])==preview['sha256'];pins[preview['path']]=preview['sha256']
  with Image.open(safe(preview['path'])) as im:
   im.load();image=im.convert('RGBA');mask=Image.new('L',image.size,0);draw=ImageDraw.Draw(mask)
   for y in range(0,image.height,1700):
    for x in range(0,image.width,1700):
     box=(x,y,min(x+1800,image.width),min(y+1800,image.height));crop=image.crop(box)
     p=target/f'preview-{ordinal:03}-{x:04}-{y:04}.png';crop.save(p)
     with Image.open(p) as saved:assert saved.convert('RGBA').tobytes()==crop.tobytes() and saved.size==crop.size
     draw.rectangle((box[0],box[1],box[2]-1,box[3]-1),fill=255)
     captures.append({'documentId':d['documentId'],'previewIndex':ordinal,'sheet':preview['sheet'],'range':preview['range'],'path':str(p),'sha256':sha(p),'originalPath':preview['path'],'originalSha256':preview['sha256'],'wholeOriginalSize':list(image.size),'sourceRectangle':{'x':x,'y':y,'width':box[2]-x,'height':box[3]-y},'scale':1,'exactRGBA':True,'actuallyViewed':False})
   assert mask.histogram()[255]==image.width*image.height
for p,v in pins.items():assert sha(p)==v
report={'schema':'own-r04-assisted-format-native-inventory/1','createdUtc':datetime.now(timezone.utc).isoformat(),'subject':'training-assisted derived geometry only','pages':pages,'xlsxCaptures':captures,'xlsxPreviewCounts':preview_counts,'immutablePins':pins,'allSourcePinsUnchanged':True,'allXlsxPreviewPixelsCovered':True,'sourceOnlyBaseline':'CLOSED','canonicalContentAuthoredOrModified':False,'semanticFormalApproval':False}
p=HERE/'format-inventory-before.json';assert not p.exists();p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'inventorySha256':sha(p),'pdfPages':len(pages),'xlsxPreviews':preview_counts,'xlsxTiles':len(captures)}))
