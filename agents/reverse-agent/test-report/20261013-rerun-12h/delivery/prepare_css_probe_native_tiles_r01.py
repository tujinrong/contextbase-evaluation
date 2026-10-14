"""Exact RGBA full-pixel crops of a bounded CSS-only native probe."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json
from PIL import Image
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
q=argparse.ArgumentParser();q.add_argument('--result',type=Path,required=True);q.add_argument('--output',type=Path,required=True);a=q.parse_args()
assert not a.output.exists();r=json.loads(a.result.read_text(encoding='utf8'))
assert r['bodyDomBytesEqual'] and r['bodyTextEqual'] and r['allTablesEqual'] and r['allImageElementsEqual']
assert r['allPinnedBytesUnchanged'] and not r['javascriptEnabled'] and not r['networkRequests']
pins=dict(r['sourceBindings']);pins[str(a.result.resolve())]=sha(a.result);pins[r['projectionHtml']]=r['projectionHtmlSha256']
capture=r['documentCapture'];pages=capture['pages'];expected_y=0
for page in pages:
 assert page['x']==0 and page['y']==expected_y and page['width']==capture['width'];expected_y+=page['height'];pins[page['path']]=page['sha256']
assert expected_y==capture['height'] and all(sha(p)==h for p,h in pins.items());a.output.mkdir();views=[]
for page in pages:
 with Image.open(page['path']) as im:
  im.load();assert im.size==(page['width'],page['height']);rectangles=[]
  for y in range(0,im.height,1700):
   for x in range(0,im.width,1700):
    box=(x,y,min(x+1800,im.width),min(y+1800,im.height));part=im.crop(box);out=a.output/f'{Path(page["path"]).stem}-{x:04}-{y:04}.png';part.save(out)
    with Image.open(out) as saved:assert saved.size==part.size and saved.convert('RGBA').tobytes()==part.convert('RGBA').tobytes()
    rectangles.append(box)
    views.append({'originalPath':page['path'],'originalSha256':page['sha256'],'path':str(out.resolve()),'sha256':sha(out),'sourceRectangle':{'x':x,'y':y,'width':box[2]-x,'height':box[3]-y},'fullDocumentRectangle':{'x':x,'y':page['y']+y,'width':box[2]-x,'height':box[3]-y},'wholeOriginalSize':list(im.size),'scale':1,'pixelsEqualToOriginalRegion':True,'actuallyReviewed':False})
  for y in range(im.height):
   intervals=sorted((x0,x1) for x0,y0,x1,y1 in rectangles if y0<=y<y1);cursor=0
   for left,right in intervals:assert left<=cursor;cursor=max(cursor,right)
   assert cursor==im.width
assert all(sha(p)==h for p,h in pins.items())
inv={'schema':'reverse-agent-css-probe-native-inventory/1','createdUtc':datetime.now(timezone.utc).isoformat(),'scope':'DERIVED_CSS_ONLY_NATIVE_GEOMETRY','sourceBindings':pins,'fullDocumentSize':[capture['width'],capture['height']],'originalPages':len(pages),'pixelComparator':'exact RGBA bytes','coverage':'all original pixels, 100px overlap within pages','captures':views,'nativeApproval':False,'businessContentAuthored':False,'published':False}
dest=a.output/'inventory.json';dest.write_text(json.dumps(inv,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'path':str(dest),'sha256':sha(dest),'tiles':len(views)}))
