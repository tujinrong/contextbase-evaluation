"""Lossless exact-RGBA native XLSX preview crops and width-only model proof."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
from PIL import Image
HERE=Path(__file__).resolve().parent
ROOT=HERE/'xlsx-assisted-screens-r18-r02'
OUT=HERE/'xlsx-native-tiles-r18-r02'
MODEL=HERE/'model-assisted-screens-r18-r02.json'
OLD=HERE/'model-assisted-screens-r18-r01.json'
MANIFEST=ROOT/'delivery-manifest.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def compact(sheet):return {k:v for k,v in sheet.items() if k not in {'columnWidths','geometryProjection','rowHeights','previewTiles'}}
assert not OUT.exists()
new=json.loads(MODEL.read_text(encoding='utf8'));old=json.loads(OLD.read_text(encoding='utf8'));manifest=json.loads(MANIFEST.read_text(encoding='utf8'))
assert len(new['documents'])==len(old['documents'])==len(manifest['documents'])==2
checks=[]
for current,previous in zip(new['documents'],old['documents']):
 assert current['documentId']==previous['documentId']
 assert len(current['sheets'])==len(previous['sheets'])
 for a,b in zip(current['sheets'],previous['sheets']):
  assert compact(a)==compact(b),'Literal/source/image/table/range/model drift'
  if a['role']!='list':assert a==b,'Non-LIST geometry drift'
  checks.append({'documentId':current['documentId'],'sheet':a['name'],'role':a['role'],'literalOperationsEqual':True,'tableHeaderOrderAndBlankEqual':True,'imageBindingsEqual':True,'nonListUnchanged':a['role']!='list','widths':a.get('columnWidths')})
before={str(p):sha(p) for p in [MODEL,OLD,MANIFEST,Path(new['binding'])]}
for doc in manifest['documents']:
 before[doc['xlsx']]=sha(Path(doc['xlsx']));assert before[doc['xlsx']]==doc['xlsxSha256']
 for preview in doc['previews']:before[preview['path']]=sha(Path(preview['path']));assert before[preview['path']]==preview['sha256']
OUT.mkdir();documents=[]
for doc in manifest['documents']:
 target=OUT/doc['documentId'];target.mkdir();captures=[]
 for ordinal,preview in enumerate(doc['previews']):
  path=Path(preview['path'])
  with Image.open(path) as source:
   source.load()
   for y in range(0,source.height,1700):
    for x in range(0,source.width,1700):
     bounds=(x,y,min(x+1800,source.width),min(y+1800,source.height));crop=source.crop(bounds)
     filename=target/f'preview-{ordinal+1:03}-{x:04}-{y:04}.png';crop.save(filename)
     with Image.open(filename) as saved:assert saved.convert('RGBA').tobytes()==crop.convert('RGBA').tobytes() and saved.size==crop.size
     captures.append({'originalPreviewIndex':ordinal,'sheet':preview['sheet'],'range':preview['range'],'originalPath':str(path),'originalSha256':preview['sha256'],'path':str(filename),'sha256':sha(filename),'sourceRectangle':{'x':x,'y':y,'width':bounds[2]-x,'height':bounds[3]-y},'wholeOriginalSize':list(source.size),'scale':1,'pixelsEqualToOriginalRegion':True,'actuallyReviewed':False})
 documents.append({'documentId':doc['documentId'],'canonicalDocumentPath':doc['canonicalDocumentPath'],'markdownSha256':doc['markdownSha256'],'xlsx':doc['xlsx'],'xlsxSha256':doc['xlsxSha256'],'originalPreviewCount':len(doc['previews']),'captures':captures,'nativeApproval':False})
assert all(sha(Path(path))==value for path,value in before.items())
report={'schema':'xlsx-native-review-tile-inventory/1','createdUtc':datetime.now(timezone.utc).isoformat(),'manifestSha256':sha(MANIFEST),'modelSha256':sha(MODEL),'bindingSha256':sha(Path(new['binding'])),'pixelComparator':'exact RGBA bytes','coverage':'all original preview pixels with up to 100px overlap','projectionChecks':checks,'sourceBindings':before,'documents':documents,'formalApproval':False,'published':False}
(OUT/'inventory.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'documents':[(d['documentId'],d['originalPreviewCount'],len(d['captures'])) for d in documents],'inventorySha256':sha(OUT/'inventory.json'),'nativeApproval':False}))
