"""Mechanical original-resolution crops of Artifact preview, never author workbook."""
from pathlib import Path
from PIL import Image,ImageChops
import json,hashlib
HERE=Path(__file__).resolve().parent
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 root=HERE/'assisted-tables-r02-native-crops';root.mkdir(exist_ok=False)
 qa_path=HERE/'assisted-tables-r02-mechanical-qa.json';qa=json.loads(qa_path.read_bytes());inventory=[]
 for d in qa['documents']:
  for kind,key in [('html','crops'),('pdf','pageImages')]:
   for p in d[kind][key]:inventory.append({'documentId':d['documentId'],'format':kind,**p})
  target=root/Path(d['canonicalDocumentPath']).stem;target.mkdir();cuts=[]
  for source in d['xlsx']['previews']:
   assert digest(source['path'])==source['sha256']
   with Image.open(source['path']) as original:
    end=0
    for i,y in enumerate(range(0,original.height,1120),1):
     box=(0,y,original.width,min(y+1200,original.height));p=target/f"{Path(source['path']).stem}-{i:02d}.png";original.crop(box).save(p)
     with Image.open(p) as cut:assert ImageChops.difference(original.crop(box),cut).getbbox() is None
     assert y<=end;end=max(end,box[3]);cuts.append({'documentId':d['documentId'],'format':'xlsx','range':source['range'],'path':str(p),'sha256':digest(p),'sourcePng':source['path'],'sourcePngSha256':source['sha256'],'sourceRectangle':list(box),'dimensions':[box[2]-box[0],box[3]-box[1]],'overlapPixels':80,'pixelEqual':True,'actuallyViewed':False})
    assert end==original.height
  inventory.extend(cuts)
 report={'schema':'reverse-agent-original-resolution-visual-inventory/1','mechanicalQa':str(qa_path),'mechanicalQaSha256':digest(qa_path),'allOriginalPixelsCovered':True,'visualReview':'PENDING','images':inventory}
 with (root/'inventory.json').open('x',encoding='utf8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
 print(json.dumps({'images':len(inventory),'byFormat':{k:sum(x['format']==k for x in inventory) for k in ['html','pdf','xlsx']},'inventory':str(root/'inventory.json'),'sha256':digest(root/'inventory.json')},ensure_ascii=False))
if __name__=='__main__':main()
