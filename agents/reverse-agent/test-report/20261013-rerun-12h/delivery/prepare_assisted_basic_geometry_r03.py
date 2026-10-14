"""Create lossless original-pixel viewing crops; no manuscript synthesis."""
from __future__ import annotations
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
from PIL import Image,ImageChops
HERE=Path(__file__).resolve().parent;REPORT=HERE.parent;REPO=HERE.parents[4]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check_captures(captures):
 by={}
 for cap in captures:by.setdefault(cap['imageId'],[]).append(cap)
 for key,items in by.items():
  source=Path(items[0]['originalPath']);im=Image.open(source).convert('RGB');coverage=Image.new('1',im.size,0)
  for c in items:
   assert sha(source)==c['originalSha256'] and sha(Path(c['path']))==c['sha256']
   r=c['sourceRectangle'];box=(r['x'],r['y'],r['x']+r['width'],r['y']+r['height']);tile=Image.open(c['path']).convert('RGB')
   assert im.size==tuple(c['wholeOriginalSize']) and ImageChops.difference(tile,im.crop(box)).getbbox() is None
   coverage.paste(1,box)
  assert coverage.getextrema()==(1,1)
 return {'originalImageCount':len(by),'tileCount':len(captures),'allPixelsCovered':True,'allCropsEqualOriginalPixels':True,'scalingUsed':False}
def main():
 search_inventory=REPORT/'visual-review/assisted-search-basic-r03-tiles/inventory.json'
 search=json.loads(search_inventory.read_text(encoding='utf-8'));search_check=check_captures(search['captures'])
 render=REPORT/'render/assisted-register-basic-r03-delivery';pins=render/'render-pins.json';meta=json.loads(pins.read_text(encoding='utf-8'))
 assert meta['sourceSha256']=='efba87eb3db5f99a4df0afba2e607ccc9a36cf3fb2f3e3c615f63d20f3763e44' and sha(Path(meta['source']))==meta['sourceSha256']
 assert meta['referenceMode']=='training-assisted' and meta['rendererCodeSha256']=='0c87df73032d812a3e646ff2846c5daa6b3053472a52dc2b1f78d0c13d41f902'
 target=HERE/'assisted-register-basic-r03-tiles';target.mkdir(exist_ok=False);captures=[]
 for obj in [*meta['diagrams'],*meta['layouts']]:
  assert obj['status']=='PASS';source=render/(obj['id']+'.png');source_sha=sha(source);assert source_sha==obj['png']['sha256']
  im=Image.open(source).convert('RGB');w,h=im.size
  for x in range(0,w,1700):
   for y in range(0,h,1700):
    cw=min(1800,w-x);ch=min(1800,h-y);path=target/(obj['id']+f'-{x:04d}-{y:04d}.png');im.crop((x,y,x+cw,y+ch)).save(path)
    captures.append({'imageId':obj['id'],'originalPath':str(source),'originalSha256':source_sha,'path':str(path),'sha256':sha(path),
     'sourceRectangle':{'x':x,'y':y,'width':cw,'height':ch},'wholeOriginalSize':[w,h],'scale':1,'pixelsEqualToOriginalRegion':True,'actuallyReviewed':False})
 check=check_captures(captures);record={'schema':'native-review-tile-inventory/1','createdUtc':datetime.now(timezone.utc).isoformat(),'documentId':meta['documentId'],'documentSha256':meta['sourceSha256'],
  'renderPinsSha256':sha(pins),'sourceSnapshotManifestSha256':meta['sourceSnapshotManifestSha256'],'draftResultSha256':meta['draftResultSha256'],'referenceMode':'training-assisted',
  'rendererCodeSha256':meta['rendererCodeSha256'],'coverage':check,'captures':captures,'businessOrFormalQualityVerified':False,'separateBodyReview':'IN_PROGRESS_AT_RENDER_START'}
 (target/'inventory.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 audit={'schema':'assisted-basic-geometry-mechanical/1','search':{'inventory':str(search_inventory),'inventorySha256':sha(search_inventory),**search_check},'registration':{'inventory':str(target/'inventory.json'),'inventorySha256':sha(target/'inventory.json'),**check},'originalApplicationExecuted':False,'actuallyViewed':'PENDING_RECORD'}
 path=HERE/'assisted-basic-r03-mechanical-geometry.json';path.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(audit,ensure_ascii=False))
if __name__=='__main__':main()
