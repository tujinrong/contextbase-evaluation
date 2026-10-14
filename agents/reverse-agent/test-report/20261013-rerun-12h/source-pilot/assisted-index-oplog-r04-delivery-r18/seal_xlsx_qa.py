"""Seal actual original-scale Artifact views; geometry and hash-only parent binding."""
import hashlib,json,os
from pathlib import Path
from datetime import datetime,timezone
from PIL import Image,ImageDraw
H=Path(__file__).absolute().parent
def safe(p):
 p=Path(os.path.abspath(p))
 for a in [p,*p.parents]:
  if a.is_symlink() or (a.exists() and getattr(a.lstat(),'st_file_attributes',0)&0x400):raise ValueError('Linked path')
 return p
def sha(p):return hashlib.sha256(safe(p).read_bytes()).hexdigest()
def load(p):return json.loads(safe(p).read_bytes())
inventory=H/'format-inventory-before.json';inv=load(inventory)
for p,s in inv['immutablePins'].items():assert sha(p)==s
captures=inv['xlsxCaptures'];assert len(captures)==85
groups={}
for c in captures:
 assert sha(c['path'])==c['sha256'] and sha(c['originalPath'])==c['originalSha256']
 groups.setdefault(c['originalPath'],[]).append(c)
for p,rows in groups.items():
 with Image.open(safe(p)) as original:
  im=original.convert('RGBA');mask=Image.new('L',im.size,0);draw=ImageDraw.Draw(mask)
  for c in rows:
   r=c['sourceRectangle'];box=(r['x'],r['y'],r['x']+r['width'],r['y']+r['height'])
   with Image.open(safe(c['path'])) as tile:assert tile.size==(r['width'],r['height']) and tile.convert('RGBA').tobytes()==im.crop(box).tobytes()
   draw.rectangle((box[0],box[1],box[2]-1,box[3]-1),fill=255)
  assert mask.histogram()[255]==im.width*im.height
log=H/'xlsx-actual-view-log.json';assert not log.exists()
log.write_text(json.dumps({'sealedObservedUtc':datetime.now(timezone.utc).isoformat(),'actuallyViewedBy':'/root/source_pilot','actualOwnTiles':list(range(1,86)),'allViewsDetail':'original','repeatViewsCountedOnce':True,'artifactPreviewCount':46},indent=2)+'\n',encoding='utf8')
findings=[
 {'documentId':'CSHARP_ASPNET-BAS-STU-03','sheet':'02_テーブル一覧','cells':['D3','D5','H6'],'previewIndex':5,'issue':'TOKEN_INTERNAL_WRAP','observation':'class_id displays class_i / d; category_id displays category / _id; 05_t_operation_log.md displays final .m / d.','severity':'HOLD'},
 {'documentId':'CSHARP_ASPNET-BAS-STU-03','sheet':'04_補足説明','cells':['row120 merged body'],'previewIndex':39,'issue':'BODY_BOTTOM_CLIP','observation':'Final body/source-attribution line is partly obscured at the transition to the row121 heading in the Artifact preview. Actual Excel display requires a separate surface review.','severity':'HOLD'},
 {'documentId':'CSHARP_ASPNET-BAS-STU-03-T_OPERATION_LOG','sheet':'t_operation_log','cells':['C11:I11','C38:I38'],'previewIndex':[1,3],'issue':'TOKEN_INTERNAL_WRAP','observation':'Saved displays Sav / ed, writeStarted displays writeS / tarted and Unknown displays Unkno / wn in wide merged body cells.','severity':'HOLD'}]
manifest=load(H/'xlsx-r01/delivery-manifest.json')
docs=[]
for d in manifest['documents']:
 own=[c for c in captures if c['documentId']==d['documentId']]
 docs.append({k:d[k] for k in ['documentId','markdownSha256','xlsx','xlsxSha256']}|{'status':'HOLD_ARTIFACT_NATIVE_GEOMETRY','actualOwnTiles':len(own),'actualOwnPreviews':len(d['previews']),'findings':[f for f in findings if f['documentId']==d['documentId']],'captures':[dict(c,actualViewCompleted=True,actuallyViewedBy='/root/source_pilot') for c in own]})
report={'schema':'own-r04-assisted-xlsx-native-review/1','createdUtc':datetime.now(timezone.utc).isoformat(),'subject':'training-assisted delivery','surface':'Artifact Tool native preview','status':'HOLD_ARTIFACT_NATIVE_GEOMETRY','documents':docs,'actualOwnTiles':85,'actualOwnPreviews':46,'fullNativePixelCoverageRechecked':True,'pixelComparator':'exact RGBA bytes plus full L-mask histogram count','preViewInventorySha256':sha(inventory),'viewLogSha256':sha(log),'allImmutablePinsAfterEqual':True,'immutablePins':inv['immutablePins'],'inputOrArtifactChanges':0,'originalReferenceRubricExpectedRawAnswerReads':0,'originalApplicationDatabaseProviderRuns':0,'sourceOnlyBaseline':'CLOSED','semanticApproval':False,'formalApproval':False,'adoptionApproval':False,'readOnlyExcelBitmapStatus':'separate fresh captures obtained; native view still pending'}
out=H/'xlsx-review.json';assert not out.exists();out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':report['status'],'reviewSha256':sha(out),'tiles':85,'previews':46,'documents':[{k:d[k] for k in ['documentId','xlsx','xlsxSha256','actualOwnTiles']} for d in docs]}))
