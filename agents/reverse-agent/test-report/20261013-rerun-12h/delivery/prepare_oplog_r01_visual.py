"""Only lossless original-resolution QA crops from existing native output images."""
from pathlib import Path
from PIL import Image,ImageChops
import hashlib,json
ROOT=Path(__file__).resolve().parent
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 qa_path=ROOT/'assisted-operation-log-r01-mechanical-qa.json';qa=json.loads(qa_path.read_bytes());target=ROOT/'native-assisted-operation-log-r01';target.mkdir(exist_ok=False);pictures=[]
 for doc in qa['documents']:
  for kind,key in [('html','crops'),('pdf','pageImages')]:
   for picture in doc[kind][key]:
    assert digest(picture['path'])==picture['sha256'];pictures.append({'documentId':doc['documentId'],'format':kind,**picture})
  for source in doc['xlsx']['previews']:
   assert digest(source['path'])==source['sha256']
   with Image.open(source['path']) as original:
    end=0
    for ordinal,y in enumerate(range(0,original.height,1120),1):
     box=(0,y,original.width,min(y+1200,original.height));path=target/f"{Path(source['path']).stem}-{ordinal:02d}.png";original.crop(box).save(path)
     with Image.open(path) as actual:assert ImageChops.difference(original.crop(box),actual).getbbox() is None
     assert y<=end;end=max(end,box[3]);pictures.append({'documentId':doc['documentId'],'format':'xlsx','range':source['range'],'path':str(path),'sha256':digest(path),'sourcePng':source['path'],'sourcePngSha256':source['sha256'],'sourceRectangle':list(box),'dimensions':[box[2]-box[0],box[3]-box[1]],'pixelEqual':True,'actuallyViewed':False})
    assert end==original.height
 record={'schema':'original-resolution-qa-inventory/1','mechanicalQa':str(qa_path),'mechanicalQaSha256':digest(qa_path),'allOriginalPixelsCovered':True,'published':False,'visualReview':'PENDING','images':pictures}
 with (target/'inventory.json').open('x',encoding='utf8') as f:json.dump(record,f,ensure_ascii=False,indent=2)
 print(json.dumps({'images':len(pictures),'byFormat':{k:sum(x['format']==k for x in pictures) for k in ['html','pdf','xlsx']},'inventory':str(target/'inventory.json')},ensure_ascii=False))
if __name__=='__main__':main()
