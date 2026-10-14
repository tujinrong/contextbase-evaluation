"""Full static capture pages, exact RGBA overlapping crops; no authoring/approval."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json
from PIL import Image
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
q=argparse.ArgumentParser();q.add_argument('--render',type=Path,required=True);q.add_argument('--output',type=Path,required=True);a=q.parse_args()
assert not a.output.exists();pins=json.loads((a.render/'render-pins.json').read_text(encoding='utf8'))
manifest=json.loads((a.render/'manifest.json').read_text(encoding='utf8'));source=Path(pins['source'])
capture=manifest['display']['documentCapture'];assert capture['complete'] is True
before={str(source):pins['sourceSha256'],str(a.render/'manifest.json'):sha(a.render/'manifest.json'),str(a.render/'render-pins.json'):sha(a.render/'render-pins.json')}
pages=capture['pages'];expected_y=0
for page in pages:
 rect=page['sourceRectangle'];assert rect['x']==0 and rect['y']==expected_y and rect['width']==capture['width'];expected_y+=rect['height']
 before[str(a.render/page['path'])]=page['png']['sha256']
assert expected_y==capture['height'] and all(sha(Path(p))==h for p,h in before.items());a.output.mkdir()
captures=[]
for page in pages:
 original=a.render/page['path'];rect=page['sourceRectangle']
 with Image.open(original) as im:
  im.load();assert im.size==(rect['width'],rect['height'])
  for y in range(0,im.height,1700):
   for x in range(0,im.width,1700):
    box=(x,y,min(x+1800,im.width),min(y+1800,im.height));part=im.crop(box);p=a.output/f'{original.stem}-{x:04}-{y:04}.png';part.save(p)
    with Image.open(p) as test:assert test.convert('RGBA').tobytes()==part.convert('RGBA').tobytes() and test.size==part.size
    captures.append({'imageId':original.stem,'originalPath':str(original.resolve()),'originalSha256':page['png']['sha256'],'path':str(p.resolve()),'sha256':sha(p),'sourceRectangle':{'x':x,'y':y,'width':box[2]-x,'height':box[3]-y},'fullDocumentRectangle':{'x':rect['x']+x,'y':rect['y']+y,'width':box[2]-x,'height':box[3]-y},'wholeOriginalSize':list(im.size),'scale':1,'pixelsEqualToOriginalRegion':True,'actuallyReviewed':False})
assert all(sha(Path(p))==h for p,h in before.items())
r={'schema':'native-review-tile-inventory/1','scope':'FULL_STATIC_DOCUMENT_GEOMETRY_ONLY','createdAt':datetime.now(timezone.utc).isoformat(),'documentId':pins['documentId'],'documentSha256':pins['sourceSha256'],'renderPinsSha256':before[str(a.render/'render-pins.json')],'sourceSnapshotSha256':pins['sourceSnapshotManifestSha256'],'coverage':'all complete document-capture pages/pixels, 100px overlap within original pages, exact RGBA','fullDocumentSize':[capture['width'],capture['height']],'beforeAfterPins':before,'captures':captures,'nativeApproval':False,'businessContentAuthored':False}
p=a.output/'inventory.json';p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'size':r['fullDocumentSize'],'originalPages':len(pages),'tiles':len(captures),'inventory':str(p),'sha256':sha(p)}))
