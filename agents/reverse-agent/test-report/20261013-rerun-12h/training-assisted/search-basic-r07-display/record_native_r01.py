"""Record completed actor views, immutable metadata and exact crop binding only."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, stat
from PIL import Image
HERE=Path(__file__).resolve().parent
RENDER=HERE/'render-r18'
def safe(p):
    p=Path(os.path.abspath(p))
    for x in [*reversed(p.parents),p]:
        if x.exists():
            s=x.lstat()
            assert not stat.S_ISLNK(s.st_mode) and not getattr(s,'st_file_attributes',0)&0x400
    return p
def sha(p):return hashlib.sha256(safe(p).read_bytes()).hexdigest()
def read(p):return json.loads(safe(p).read_text(encoding='utf8'))
pins=read(RENDER/'render-pins.json'); mf=read(RENDER/'manifest.json')
assert pins['sourceSha256']=='c954ae728a0a51040c2ab99dc0d20fc4416955483a158269e5014df7bd9e122b'
assert pins['inputBeforeAfterUnchanged'] is True and pins['rendererRuntimeFileCount']==126
assert len(pins['diagrams'])==27 and len(pins['layouts'])==1 and mf['display']['status']=='PASS'
assert all(x['status']=='PASS' for x in pins['diagrams']+pins['layouts'])
bound=dict(pins['inputPins'])
receipt=read(pins['rendererRuntimeReceipt']); frozen=Path(receipt['destination'])
assert sha(pins['rendererRuntimeReceipt'])==pins['rendererRuntimeReceiptSha256']
for rel,h in receipt['files'].items():bound[str(frozen/rel)]=h
for records in (pins['frozenResolvedImports'],pins['frozenRenderImports']):
    assert isinstance(records,dict)
    for x in records.values():bound[x['path']]=x['sha256']
for x in pins['artifacts']:bound[str(RENDER/x['path'])]=x['sha256']
for p in (RENDER/'manifest.json',RENDER/'render-pins.json',HERE/'worker.json',HERE/'audit-helper-r01.json'):
    bound[str(p)]=sha(p)
rows=[]
for kind,folder,count in [('DIAGRAM_AND_LAYOUT','native-diagrams-r01',28),('FULL_STATIC_BODY','native-full-document-r01',35)]:
    ip=HERE/folder/'inventory.json'; inv=read(ip); bound[str(ip)]=sha(ip)
    assert len(inv['captures'])==count
    for i,c in enumerate(inv['captures']):
        bound[c['originalPath']]=c['originalSha256'];bound[c['path']]=c['sha256']
        r=c['sourceRectangle'];box=(r['x'],r['y'],r['x']+r['width'],r['y']+r['height'])
        with Image.open(safe(c['originalPath'])) as src,Image.open(safe(c['path'])) as crop:
            assert crop.size==(r['width'],r['height']) and crop.convert('RGBA').tobytes()==src.crop(box).convert('RGBA').tobytes()
        rows.append({**c,'inventoryIndex':i,'kind':kind,'actuallyReviewed':True,'actualActor':'/root/delivery_tools','imageDetail':'original','resampling':False})
assert all(sha(p)==h for p,h in bound.items())
def inventory(root):
    result={}
    for p in safe(root).iterdir():
        safe(p)
        if p.is_dir() and p.name!='__pycache__':
            for rel,h in inventory(p).items():result[p.name+'/'+rel]=h
        elif p.is_file() and p.suffix!='.pyc':result[p.name]=sha(p)
    return result
assert inventory(frozen)==receipt['files']
r={'schema':'actual-native-geometry-review/1','createdAt':datetime.now(timezone.utc).isoformat(),
   'scope':'IMMUTABLE_SEARCH_BASIC_R07_R18_STATIC_GEOMETRY_ONLY','status':'HOLD_FULL_BODY_FIRST_COLUMN_IDENTIFIER_WRAP',
   'documentId':pins['documentId'],'sourceSha256':pins['sourceSha256'],'sourceSnapshotSha256':pins['sourceSnapshotManifestSha256'],
   'rendererReceipt':pins['rendererRuntimeReceipt'],'rendererReceiptSha256':pins['rendererRuntimeReceiptSha256'],
   'diagramLayout':{'status':'PASS_GEOMETRY_ONLY','actualViews':28,'images':28,'blocking':[]},
   'fullBody':{'status':'HOLD','actualViews':35,'originalPages':12,'completeSize':[1440,46314],
     'blocking':[{'cause':'CSS/table column width at viewport1440; original values not changed',
                  'inventoryIndices':[2,3,4,5,6],
                  'examples':['SRC-001 shown SRC-/001','SRC-INT-002 split at hyphens','OP-PREFECTURE and UI-DIRECTION split at hyphens'],
                  'scope':'identifier continuity only; no loss of columns or values observed','authorRevisionRequiredByThisRecord':False}]},
   'notes':['All original diagram pixels and all complete body pixels covered by scale1 exactRGBA crops.',
            'Captures at 4000px page boundaries continue into the next original; all continuations actually viewed.',
            'Bytecode caches excluded from frozen inventory; no claim of all-cache bytes immutability.',
            'No child stdout captured; actual manifest/artifacts and natural worker exit checked separately.',
            'Independent semantic approval was announced by author after render; not evaluated in this geometry record.'],
   'beforeAfterUnchanged':True,'boundFileCount':len(bound),'beforeAfterPins':bound,'actualViewCount':63,'actualViews':rows,
   'canonicalOrOriginalHtmlModified':False,'businessContentAuthored':False,'providerExecuted':False,'originalApplicationExecuted':False,
   'stateProjectionIncluded':False,'formalEvaluation':False,'semanticApproval':False,'wholeDocumentApproval':False,'adoptionApproval':False,'published':False}
out=HERE/'native-review-r01.json'
with out.open('x',encoding='utf8') as f:f.write(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'path':str(out),'sha256':sha(out),'status':r['status'],'actualViews':63,'boundFileCount':len(bound)}))
