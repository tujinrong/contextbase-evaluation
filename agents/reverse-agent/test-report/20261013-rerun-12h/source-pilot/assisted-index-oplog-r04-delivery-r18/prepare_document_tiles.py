"""Exact RGBA native crops of only the two pinned derived document captures."""
import argparse,hashlib,json,os
from pathlib import Path
from datetime import datetime,timezone
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;REPORT=HERE.parents[1]
CASES={'table-index':('assisted-table-index-r04-delivery-r18','d328d6a6f42f201b8d4026aa091b123a84ecd36fe8ae70729fd20b8dd6872eb7'),
       'operation-log':('assisted-operation-log-r04-delivery-r18','7067c165e324756fb909048d2f3c6735ed3824bb6512c66155015ba6c5703b48')}
def safe(p):
 p=Path(os.path.abspath(p))
 for item in (p,*p.parents):
  if item.is_symlink() or (item.exists() and getattr(item.lstat(),'st_file_attributes',0)&0x400):raise ValueError('Linked path rejected')
 return p
def sha(p):return hashlib.sha256(safe(p).read_bytes()).hexdigest()
parser=argparse.ArgumentParser();parser.add_argument('case',choices=CASES);a=parser.parse_args()
name,expected=CASES[a.case];render=safe(REPORT/'render'/name);pin=safe(render/'render-pins.json')
pins=json.loads(pin.read_bytes());source=safe(pins['source']);before={str(pin):sha(pin),str(source):sha(source)}
assert pins['sourceSha256']==expected==sha(source) and pins['referenceMode']=='training-assisted'
assert pins['display']['status']=='PASS' and pins['safety']['inputJavaScriptEnabled'] is False
assert pins['rendererRuntimeReceiptSha256']=='54e693b2382e1520710d192e8a8b0b6b6eb97bbae1e70c1dbc36ff1e36f279be'
dst=safe(HERE/(a.case+'-document-native'));assert not dst.exists();dst.mkdir()
capture=pins['display'].get('documentCapture') or pins['display']['documentPng']
chunks=capture['pages'] if capture.get('mode')=='complete-vertical-tiles' else [{'path':'document.png','sourceRectangle':{'x':0,'y':0,'width':capture['width'],'height':capture['height']}}]
records=[];coverage=[];absolute_y=0
for ordinal,chunk in enumerate(chunks,1):
 p=safe(render/chunk['path']);before[str(p)]=sha(p);r=chunk['sourceRectangle']
 assert r['x']==0 and r['y']==absolute_y;absolute_y+=r['height']
 if chunk.get('sha256'):assert chunk['sha256']==sha(p)
 elif len(chunks)==1:assert capture['sha256']==sha(p)
 im=Image.open(p).convert('RGBA');assert list(im.size)==[r['width'],r['height']]
 mask=Image.new('L',im.size,0);draw=ImageDraw.Draw(mask)
 for y in range(0,im.height,1700):
  for x in range(0,im.width,1700):
   box=(x,y,min(x+1800,im.width),min(y+1800,im.height))
   target=dst/f'document-{ordinal:03d}-{x:04d}-{y:04d}.png';im.crop(box).save(target)
   actual=Image.open(target).convert('RGBA');assert actual.tobytes()==im.crop(box).tobytes()
   draw.rectangle((box[0],box[1],box[2]-1,box[3]-1),fill=255)
   records.append({'viewIndex':len(records)+1,'path':str(target),'sha256':sha(target),'originalPath':str(p),'originalSha256':sha(p),
     'sourceRectangle':{'x':x,'y':y,'width':box[2]-x,'height':box[3]-y},'absoluteY':r['y']+y,
     'wholeOriginalSize':list(im.size),'scale':1,'exactRGBA':True,'actuallyViewed':False})
 assert mask.histogram()[255]==im.width*im.height
 coverage.append({'originalPath':str(p),'wholePixels':im.width*im.height,'allCovered':True})
assert absolute_y==capture['height']
assert all(sha(Path(p))==v for p,v in before.items())
out=dst/'inventory.json';out.write_text(json.dumps({'schema':'native-document-tile-inventory/1','createdUtc':datetime.now(timezone.utc).isoformat(),
 'documentId':pins['documentId'],'referenceMode':'training-assisted','documentSha256':expected,'sourceSnapshotSha256':pins['sourceSnapshotManifestSha256'],
 'renderPinsSha256':sha(pin),'pins':before,'captures':records,'coverage':coverage,'fullPixelCoverage':True,
 'nativeApproval':False,'canonicalModified':False,'providerOrApplicationRun':0},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'path':str(out),'sha256':sha(out),'captureCount':len(records)},ensure_ascii=False))
