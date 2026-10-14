"""Fresh hash/pixel-only recheck; does not add or repeat an actual visual review."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
from PIL import Image,ImageChops
from contextbase.ai import capsule

ROOT=Path(__file__).resolve().parent
PR=ROOT.parent
EXPECTED={
 'category':'f5be5e1122a73d0a3d3b57a19cca7be68f9b34b010bfc232c2f437ef0bebf6a0',
 'mclass':'172952d5edc69f4f409c28aff4d441425e495c973fda110ba80794f1b0ebd4c5',
 'mcode':'47fb16612d0345745d011827699528add7064f34ef0f7678b95a0a788a1bd99c',
 'mstudent':'03de50f75a17dfc1588b00a2de14c5bf8572fcb87df7774ff7202d18fbfe660d',
 'oplog':'15e2045c0439e96ebff9f1b6a56e9ed117312f944814fc583f8c4a6e315aa02a',
 'tableindex':'b1ac08680118e034fa9a614b43366081d707f9969f100f65b2f918cdaf4d7aac',
 'codedesign':'b075197ff182e630bdd2fd26ad814cbc2789f4cb452724206f039b2e2a4b39c6',
}
sha=lambda b:hashlib.sha256(b).hexdigest()
def safe(path,root):
 p=capsule.safe_path(Path(path))
 if not p.is_relative_to(root.resolve()):raise ValueError('Unexpected recheck path')
 return p

rows=[];sources={};receipts=[]
for name,expected in EXPECTED.items():
 report=safe(ROOT/f'source-{name}-r15-02-native-review.json',ROOT)
 raw=report.read_bytes()
 if sha(raw)!=expected:raise ValueError('Previous actual review receipt drift: '+name)
 data=json.loads(raw)
 pin=safe(data['renderPinsFile'],PR/'render')
 if sha(pin.read_bytes())!=data['renderPinsSha256']:raise ValueError('Render pin drift')
 doc=capsule.safe_path(Path(data['documentFile']))
 allowed=Path(r'D:\開発\contextbase-evaluation\test-project1\spec-analysis\CSharp_ASPNET\20261013-rerun-12h\source-only\drafts').resolve()
 if not doc.is_relative_to(allowed) or sha(doc.read_bytes())!=data['documentSha256']:raise ValueError('Canonical parent drift')
 if data['sourceSnapshotSha256']!='2f64e2211b1fcd7850203927fc75b5a7f2ce37457cc2afe88c8065d9f931273b':raise ValueError('Source mode pin differs')
 receipts.append({'case':name,'path':str(report),'sha256':expected,'priorNativeReviewCount':data['captureCount'],
                  'documentSha256':data['documentSha256']})
 for record in data['captures']:
  original=safe(record['originalPath'],PR/'render');tile=safe(record['path'],PR/'visual-review')
  if sha(original.read_bytes())!=record['originalSha256'] or sha(tile.read_bytes())!=record['sha256']:raise ValueError('Native image byte drift')
  r=record['sourceRectangle']
  if record['scale']!=1:raise ValueError('Scaled tile')
  with Image.open(original) as source,Image.open(tile) as crop:
   if source.size!=tuple(record['wholeOriginalSize']) or r['x']<0 or r['y']<0 or r['x']+r['width']>source.width or r['y']+r['height']>source.height:raise ValueError('Invalid original extent')
   region=source.crop((r['x'],r['y'],r['x']+r['width'],r['y']+r['height'])).convert('RGBA')
   actual=crop.convert('RGBA')
   if region.size!=actual.size or region.tobytes()!=actual.tobytes():raise ValueError('Exact RGBA region mismatch')
   pixel_sha=sha(actual.tobytes())
   sources[str(original)]={'path':str(original),'sha256':record['originalSha256'],'size':source.size}
  rows.append({'case':name,'path':str(tile),'pngSha256':record['sha256'],'originalPath':str(original),
    'originalSha256':record['originalSha256'],'sourceRectangle':r,'scale':1,
    'exactRgbaBytesEqual':True,'rgbaRegionSha256':pixel_sha,'additionalActualVisualReviewPerformed':False})
if len(rows)!=129 or len(sources)!=52:raise ValueError('Unexpected complete review inventory')
red=Image.new('RGBA',(1,1),(255,0,0,255));blue=Image.new('RGBA',(1,1),(0,0,255,255))
negative={'differentOpaqueRgbRejected':red.tobytes()!=blue.tobytes(),
          'alphaOnlyGetbboxWouldMissRgbDifference':ImageChops.difference(red,blue).getbbox() is None}
if not negative['differentOpaqueRgbRejected']:raise ValueError('Opaque mismatch not rejected')
result={'schema':'source-native-exact-rgba-recheck/1','createdAt':datetime.now(timezone.utc).isoformat(),
 'scope':'PRIOR_SOURCE_ONLY_129_NATIVE_TILES_HASH_AND_EXACT_PIXEL_REGION_RECHECK',
 'allPass':True,'priorActualReviews':receipts,'originalImages':list(sources.values()),'crops':rows,
 'originalImageCount':len(sources),'recheckedPixelRegionCount':len(rows),
 'additionalActualNativeViews':0,'priorActualNativeViewsStill':129,
 'additionalRenderJobs':0,'additionalProviderJobs':0,'negative':negative,
 'oldReportsModified':False,'originalImagesModified':False,'canonicalModified':False,
 'newSemanticApproval':False,'newGeometryApproval':False,'adopted':False}
out=ROOT/'source-table-code129-exact-rgba-recheck-r01.json'
with out.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps({'path':str(out),'sha256':sha(out.read_bytes()),'images':len(sources),'regions':len(rows),'allPass':True},ensure_ascii=False))
