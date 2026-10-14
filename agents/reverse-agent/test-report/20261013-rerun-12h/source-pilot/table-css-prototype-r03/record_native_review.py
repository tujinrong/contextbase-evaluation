"""Record completed actual native review and recheck every reviewed lossless pixel region."""
from pathlib import Path
import hashlib,json
from PIL import Image
from datetime import datetime,timezone

PARENT=Path(__file__).resolve().parent.parent
all_records=[]
for version,expected in (('r01',12),('r02',14),('r03',9)):
 root=PARENT/('table-css-prototype-'+version)
 invpath=root/'native-comparison-tiles/inventory.json'
 inventory=json.loads(invpath.read_text(encoding='utf-8'))
 reviewed=[]
 for original in inventory['images']:
  source=Path(original['source'])
  if hashlib.sha256(source.read_bytes()).hexdigest()!=original['sourceSha256']:raise ValueError('source pixel drift')
  with Image.open(source) as image:
   covered=0
   for tile in original['tiles']:
    p=Path(tile['path']);r=tile['sourceRectangle']
    if hashlib.sha256(p.read_bytes()).hexdigest()!=tile['sha256'] or tile['scale']!=1:raise ValueError('tile drift')
    with Image.open(p) as crop:
     region=image.crop((r['x'],r['y'],r['x']+r['width'],r['y']+r['height']))
     if crop.size!=region.size or crop.convert('RGBA').tobytes()!=region.convert('RGBA').tobytes():raise ValueError('tile pixels differ')
    if r['y']>covered or r['x']!=0 or r['width']!=image.width:raise ValueError('coverage gap')
    covered=max(covered,r['y']+r['height'])
    reviewed.append({**tile,'case':original['case'],'actuallyViewedAtOriginalScale':True})
   if covered!=image.height:raise ValueError('incomplete original coverage')
 if len(reviewed)!=expected:raise ValueError('unexpected viewed count')
 result=json.loads((root/'result.json').read_text(encoding='utf-8'))
 findings=(['Identifiers improved; long non-final cells force the Japanese final column too narrow, producing excessive vertical height.',
            'Plaintext hyphen breaks remain legal normal wrapping; no plaintext span conversion was performed.']
           if version in ('r01','r02') else
           ['Plaintext hyphen breaks remain legal normal wrapping; code tokens are kept whole. Explicit br is preserved.'])
 record={'schema':'synthetic-table-css-native-review/1','version':version,
  'scope':'TRUSTED_SYNTHETIC_FIXTURE_DISPLAY_ONLY','createdAt':datetime.now(timezone.utc).isoformat(),
  'resultSha256':hashlib.sha256((root/'result.json').read_bytes()).hexdigest(),
  'inventorySha256':hashlib.sha256(invpath.read_bytes()).hexdigest(),
  'fixtureSha256':result['fixtureSha256'],'candidate':result['candidate'],
  'mechanicalPass':result['mechanicalPass'],'actualViewComplete':True,'reviewedNativeTiles':reviewed,
  'totalNativeTiles':expected,'allPixelRegionsReverified':True,'allOriginalPixelsCovered':True,
  'syntheticReadabilityAcceptable':version=='r03','observations':findings,
  'clippingObserved':False,'glyphLossObserved':False,'candidateCellOverlapObserved':False,
  'businessMaterialsReviewed':False,'mainCodeModified':False,'semanticApproval':False,
  'applicationExecuted':False,'adopted':False,
  'unassessed':['real-document display','formal-semantic-score','real-application behavior']}
 if version=='r03':
  negatives=[]
  for name in ('fixed-normal-only-negative','authored-break-negative'):
   p=root/name/'document.png'
   negatives.append({'case':name,'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
     'actuallyViewedAtOriginalScale':True,'observed':('Adjacent-cell text overlap reproduced.' if name.startswith('fixed') else 'Explicit br still produces two lines; no repair performed.')})
  record['reviewedNegativeImages']=negatives
 out=root/'native-review.json'
 with out.open('x',encoding='utf-8') as f:json.dump(record,f,ensure_ascii=False,indent=2)
 all_records.append({'version':version,'report':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),
                     'mechanicalPass':record['mechanicalPass'],'syntheticReadabilityAcceptable':record['syntheticReadabilityAcceptable'],
                     'tileCount':expected})
print(json.dumps(all_records,ensure_ascii=False))
