"""Lossless comparison crops for actual original-scale visual review."""
from pathlib import Path
import hashlib
import json
from PIL import Image

PARENT=Path(__file__).resolve().parent.parent
records=[]
for version in ('r01','r02','r03'):
 root=PARENT/('table-css-prototype-'+version)
 dest=root/'native-comparison-tiles';dest.mkdir(exist_ok=False)
 images=[]
 for case in ('baseline-1440','candidate-1440','baseline-800','candidate-800'):
  source=root/case/'document.png'
  raw=source.read_bytes()
  with Image.open(source) as image:
   image.load();tiles=[];height=image.height
   cursor=0;number=1
   while cursor<height:
    bottom=min(cursor+1600,height)
    path=dest/(case+'-'+str(number).zfill(2)+'.png')
    image.crop((0,cursor,image.width,bottom)).save(path)
    with Image.open(path) as saved:
     if saved.size!=(image.width,bottom-cursor) or saved.convert('RGBA').tobytes()!=image.crop((0,cursor,image.width,bottom)).convert('RGBA').tobytes():
      raise ValueError('Lossless comparison region mismatch')
    tile={'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
          'sourceRectangle':{'x':0,'y':cursor,'width':image.width,'height':bottom-cursor},'scale':1,'pixelExact':True}
    tiles.append(tile)
    if bottom==height:break
    cursor=bottom-100;number+=1
   images.append({'case':case,'source':str(source),'sourceSha256':hashlib.sha256(raw).hexdigest(),
                 'sourceSize':[image.width,image.height],'tiles':tiles,'fullPixelCoverage':True})
 data={'schema':'synthetic-comparison-native-inventory/1','version':version,'images':images,
       'tileCount':sum(len(x['tiles']) for x in images),'actualVisualReview':'PENDING'}
 out=dest/'inventory.json';out.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
 records.append({'version':version,'inventory':str(out),'tileCount':data['tileCount'],
                 'images':[{'case':x['case'],'size':x['sourceSize']} for x in images]})
print(json.dumps(records,ensure_ascii=False))
