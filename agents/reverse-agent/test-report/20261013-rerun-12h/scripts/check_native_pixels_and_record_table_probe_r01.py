"""Recheck existing crops exactly and record two actual root prototype views."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import importlib.util
import json
from PIL import Image, ImageChops

report=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def fresh(path,value):
    if path.exists():raise ValueError('Fresh evidence required')
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
spec=importlib.util.spec_from_file_location('tile_v2',report/'scripts/prepare_native_tiles_v2.py')
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
red=Image.new('RGBA',(2,2),(255,0,0,255))
blue=Image.new('RGBA',(2,2),(0,0,255,255))
assert ImageChops.difference(red,blue).getbbox() is None
assert not m.same_pixels(red,blue)
assert m.same_pixels(red,red.copy())
assert not m.same_pixels(red,Image.new('RGBA',(2,2),(255,0,0,254)))
assert not m.same_pixels(red,Image.new('RGBA',(1,2),(255,0,0,255)))
assert m.same_pixels(red,Image.new('RGB',(2,2),(255,0,0)))

records=[]
for path in sorted((report/'visual-review').rglob('inventory.json')):
    data=load(path)
    if data.get('schema')!='native-review-tile-inventory/1':continue
    captures=data['captures']
    for capture in captures:
        original,saved=Path(capture['originalPath']),Path(capture['path'])
        assert sha(original)==capture['originalSha256'] and sha(saved)==capture['sha256']
        rectangle=capture['sourceRectangle']
        bounds=(rectangle['x'],rectangle['y'],rectangle['x']+rectangle['width'],rectangle['y']+rectangle['height'])
        with Image.open(original) as image,Image.open(saved) as tile:
            assert m.same_pixels(image.crop(bounds),tile)
    records.append({'inventoryPath':str(path),'inventorySha256':sha(path),'captures':len(captures),'exactRgbaEquality':True})
created=datetime.now(timezone.utc).isoformat()
fresh(report/'visual-review/exact-pixel-recheck-root-r01.json',{
    'schema':'native-crop-exact-pixel-recheck/1','createdAt':created,'reviewer':'/root','status':'PASS',
    'opaqueColorNegativeRejected':True,'regressionChecks':5,'inventories':records,
    'capturesChecked':sum(r['captures'] for r in records),'oldReportsOrImagesEdited':False,
    'additionalImagesActuallyViewed':0,'businessMeaningApproval':False})

prototype=report/'source-pilot/table-css-prototype-r03'
result=load(prototype/'result.json')
assert sha(prototype/'candidate.css')=='e3373dc2efc2ee2a60693a34e7a24010c6092a737a7703722f9d053056be3d54'
images=[]
for width in (1440,800):
    path=prototype/f'candidate-{width}'/'document.png'
    with Image.open(path) as image:size=list(image.size)
    images.append({'path':str(path),'sha256':sha(path),'size':size,'actuallyReviewed':True,'detail':'original'})
record=report/'visual-review/table-css-prototype-r03-root-native.json'
fresh(record,{'schema':'reverse-agent-native-technical-review/1','reviewedAt':created,'reviewer':'/root',
    'scope':'SYNTHETIC_TABLE_CSS_DISPLAY_ONLY','prototypeResultSha256':sha(prototype/'result.json'),
    'images':images,'observations':['Whole code identifiers and numbers remain legible. The explanation column has usable width; all rows and columns remain present.',
        'Plain text hyphen wrapping remains at legal punctuation boundaries. One- and two-column tables and embedded layout retain their existing behavior.'],
    'businessMeaningApproved':False,'actualSpecificationGeometryApproved':False,'formalQualityGatePassed':False,
    'originalApplicationExecuted':False,'published':False})
manifest_path=report/'run-manifest.json'
manifest=load(manifest_path)
assert manifest['nativeVisualReview']['imagesActuallyReviewed']==97
fresh(report/'checkpoints/run-manifest-before-root-table-probe.json',manifest)
manifest['nativeVisualReview']['records'].append(record.relative_to(report).as_posix())
manifest['nativeVisualReview']['imagesActuallyReviewed']=99
manifest['updatedAt']=created
manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'pixelInventoriesChecked':len(records),'pixelCapturesChecked':sum(r['captures'] for r in records),
    'additionalActualRootViews':2,'totalActualRootViews':99,'technicalRecordSha256':sha(record)}))
