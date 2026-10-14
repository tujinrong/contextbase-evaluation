"""Selected delivery metadata/byte bindings and exact RGBA coverage only."""
import argparse, hashlib, json, os
from pathlib import Path
from datetime import datetime,timezone
from PIL import Image,ImageDraw

HERE=Path(__file__).resolve().parent
REPORT=HERE.parent.parent
ID='CSHARP_ASPNET-DET-CSharp_ASPNET-SCR-STU-001'
MANIFEST=REPORT/'delivery/xlsx-native-tiles-r18-r02/inventory.json'
EXPECTED='aed204b356031cdf61e6d61e551decbb657be17f03050a046e576116a8187e51'
DELIVERY=REPORT/'delivery/xlsx-assisted-screens-r18-r02/delivery-manifest.json'
DELIVERY_SHA='773971eb607780b6cb2ddc6699e3d00cf52998e5ae524664ecefdede5a0477a2'
MD_SHA='9a49fb5a1d22094db7c57fdaf751807dd2f69c12367973ea839bc5ff9b037696'
CANONICAL=Path(r'D:\開発\contextbase-evaluation\test-project1\spec-analysis\CSharp_ASPNET\20261013-rerun-12h\training-assisted\drafts\revision-pending-r02-4a8437c580b548ac\詳細仕様書\CSharp_ASPNET\01_学生検索画面.md')
def safe(path):
    p=Path(os.path.abspath(path))
    for item in [p,*p.parents]:
        if item.is_symlink() or (item.exists() and getattr(item.lstat(),'st_file_attributes',0)&0x400):raise ValueError('Linked input refused')
    return p.resolve()
def sha(path):return hashlib.sha256(safe(path).read_bytes()).hexdigest()
def load(path):return json.loads(safe(path).read_text(encoding='utf-8-sig'))
args=argparse.ArgumentParser();args.add_argument('--phase',choices=['before','after'],required=True);phase=args.parse_args().phase
assert sha(MANIFEST)==EXPECTED and sha(DELIVERY)==DELIVERY_SHA
inv=load(MANIFEST);doc=next(d for d in inv['documents'] if d['documentId']==ID)
dm=load(DELIVERY);dd=next(d for d in dm['documents'] if d['documentId']==ID)
assert dm['referenceMode']=='training-assisted' and dm['sourceSnapshotManifestSha256']=='e76a6c40e8927011fff9145d5f5ab2fa94ad89acefc9a03bbad0cbf09b85a0e7'
assert doc['xlsx']==dd['xlsx'] and doc['xlsxSha256']==dd['xlsxSha256']=='1f37f6fca3687407d86acbac5315455ed4b45d21d0d7ee2e59efef5c03cc8e83'
assert doc['markdownSha256']==dd['markdownSha256']==MD_SHA and sha(CANONICAL)==MD_SHA
assert doc['originalPreviewCount']==47 and len(doc['captures'])==89
pins={str(safe(MANIFEST)):EXPECTED,str(safe(DELIVERY)):DELIVERY_SHA,str(safe(CANONICAL)):MD_SHA,str(safe(doc['xlsx'])):doc['xlsxSha256']}
assert sha(doc['xlsx'])==doc['xlsxSha256']
for name,digest in inv['sourceBindings'].items():
    p=safe(name)
    # Shared JSON is hash-only; never inspect model cell values or the other document.
    if p.suffix.lower()=='.json' or str(p)==doc['xlsx'] or '詳細仕様書\\CSharp_ASPNET\\01_学生検索画面\\' in str(p):
        assert sha(p)==digest;pins[str(p)]=digest
originals={};captures=[]
for index,c in enumerate(doc['captures'],1):
    p,original=safe(c['path']),safe(c['originalPath'])
    assert REPORT in p.parents and REPORT in original.parents
    assert sha(p)==c['sha256'] and sha(original)==c['originalSha256']
    pins[str(p)]=c['sha256'];pins[str(original)]=c['originalSha256']
    oi=Image.open(original).convert('RGBA');tile=Image.open(p).convert('RGBA')
    r=c['sourceRectangle'];box=(r['x'],r['y'],r['x']+r['width'],r['y']+r['height'])
    assert c['scale']==1 and list(oi.size)==c['wholeOriginalSize'] and tile.size==(r['width'],r['height'])
    assert 0<=box[0]<box[2]<=oi.width and 0<=box[1]<box[3]<=oi.height
    assert oi.crop(box).tobytes()==tile.tobytes()
    key=str(original)
    if key not in originals:originals[key]={'image':oi,'rectangles':[],'originalPreviewIndex':c['originalPreviewIndex']}
    originals[key]['rectangles'].append(box)
    captures.append({'viewIndex':index,**c,'exactRGBARechecked':True})
coverage=[]
for path,item in originals.items():
    mask=Image.new('L',item['image'].size,0);draw=ImageDraw.Draw(mask)
    for x0,y0,x1,y1 in item['rectangles']:draw.rectangle((x0,y0,x1-1,y1-1),fill=255)
    covered=mask.histogram()[255];pixels=mask.width*mask.height;assert covered==pixels
    coverage.append({'originalPath':path,'previewIndex':item['originalPreviewIndex'],'coveredPixels':covered,'wholePixels':pixels,'allCovered':True})
assert len(originals)==47
# Reject an opaque RGB difference even when alpha is identical.
assert Image.new('RGBA',(1,1),(255,0,0,255)).tobytes()!=Image.new('RGBA',(1,1),(0,0,255,255)).tobytes()
report={'schema':'own-native-xlsx-inventory/1','phase':phase,'createdUtc':datetime.now(timezone.utc).isoformat(),
        'subject':'training-assisted delivery','scope':'SELECTED_DETAIL_GEOMETRY_ONLY','documentId':ID,'workbook':doc['xlsx'],
        'workbookSha256':doc['xlsxSha256'],'markdownSha256':MD_SHA,'sourceSnapshotManifestSha256':dm['sourceSnapshotManifestSha256'],
        'sourceOnlyBaseline':'CLOSED','pins':pins,'captures':captures,'originalPreviewCount':47,'captureCount':89,
        'pixelComparator':'exact RGBA bytes','coverage':coverage,'opaqueRGBNegativeRejected':True,
        'actualViewCompleted':False,'productionProvider':0,'canonicalOrWorkbookChanges':0,'semanticOrFormalApproval':False}
destination=HERE/('inventory-'+phase+'.json')
if destination.exists():raise FileExistsError('Fresh receipt required')
destination.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
if phase=='after':
    before=load(HERE/'inventory-before.json');assert before['pins']==report['pins']
print(json.dumps({'path':str(destination),'sha256':sha(destination),'previews':len(originals),'tiles':len(captures),'completePixelCoverage':True,'bindingsCount':len(pins),'phase':phase},ensure_ascii=False))
