"""Infrastructure AST/toy image/hash tests only; no production captures or main."""
import ast,copy,json,hashlib,os,types
from pathlib import Path
from PIL import Image
from datetime import datetime,timezone
H=Path(__file__).resolve().parent;TARGET=H.parents[1]/'scripts/record_screen_composite_r19.py'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
initial=digest(TARGET);tree=ast.parse(TARGET.read_text(encoding='utf-8-sig'))
funcs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name!='main']
main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
def write(p,obj):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj),encoding='utf-8')
def guard(p):
 p=Path(p).absolute()
 for a in [p,*p.parents]:
  if a.exists() and (a.is_symlink() or getattr(a.lstat(),'st_file_attributes',0)&0x400):raise ValueError('Linked path')
 return p.resolve()
cases=[]
def run(name,mutator=None,expected=True):
 root=H/'f'/f'{len(cases):02}';root.mkdir(parents=True)
 canonical=root/'canon.md';canonical.write_text('# owned toy',encoding='utf8')
 runtime=root/'runtime';runtime.mkdir();files={}
 for i in range(128):
  p=runtime/f'f{i:03}.py';p.write_text(f'# own toy {i}',encoding='utf8');files[p.name]=digest(p)
 receipt=root/'runtime.json';write(receipt,{'destination':str(runtime),'files':files,'fileCount':128})
 rsha=digest(receipt);cap='toy-fixed-cap';doc='TOY-DOC'
 rp=root/'render-pins.json';write(rp,{'documentId':doc,'sourceSha256':digest(canonical),'source':str(canonical),'sourceSnapshotManifestSha256':cap,'inputBeforeAfterUnchanged':True})
 captures=[]
 for i in range(2):
  original=root/f'o{i}.png';tile=root/f't{i}.png';Image.new('RGBA',(6,4),(40*i,90,150,255)).save(original);Image.open(original).save(tile)
  captures.append({'originalPath':str(original),'originalSha256':digest(original),'path':str(tile),'sha256':digest(tile),'wholeOriginalSize':[6,4],'sourceRectangle':{'x':0,'y':0,'width':6,'height':4},'scale':1,'pixelsEqualToOriginalRegion':True,'actuallyViewed':True,'actuallyViewedBy':'delivery_tools'})
 inventory=root/'inventory.json';index=root/'viewed.json';write(inventory,{'captures':copy.deepcopy(captures)});write(index,{'captures':copy.deepcopy(captures),'actuallyViewedTileCount':2})
 qa={'schema':'screen-native-review/2','status':'PASS_NATIVE_GEOMETRY_ONLY','findings':[],'documentId':doc,'documentSha256':digest(canonical),'referenceMode':'training-assisted','sourceSnapshotManifestSha256':cap,'frozenRuntimeAll128FilesUnchanged':True,'inputBeforeAfterPinsUnchanged':True,'exactRgbaComparisonAndCompletePixelCoverage':True,'rendererRuntimeReceiptSha256':rsha,'rendererRuntimeReceipt':str(receipt),'renderPins':str(rp),'renderPinsSha256':digest(rp),'tileInventory':str(inventory),'tileInventorySha256':digest(inventory),'actuallyViewedIndexRecord':str(index),'actuallyViewedIndexRecordSha256':digest(index),'captures':captures,'actuallyViewedTileCount':2,'actuallyViewedImageCount':2}
 if mutator:mutator(qa,root,canonical,receipt,rp,inventory,index)
 qp=root/'qa.json';write(qp,qa)
 ns={'Path':Path,'hashlib':hashlib,'json':json,'Image':Image,'capsule':types.SimpleNamespace(safe_path=guard),'REPO':root,'CAP_SHA':cap,'RUNTIME_SHA':rsha}
 exec(compile(ast.Module(copy.deepcopy(funcs),[]),str(TARGET),'exec'),ns)
 accepted=True;err=None;count=None
 try:count=len(ns['tile_review'](qp,digest(qp),canonical,doc))
 except Exception as e:accepted=False;err=f'{type(e).__name__}: {e}'
 cases.append({'name':name,'passed':accepted==expected,'accepted':accepted,'expectedAccepted':expected,'returnedImages':count,'error':err})
def qfield(k,v):return lambda q,*args:q.__setitem__(k,v)
def cfield(k,v):return lambda q,*args:q['captures'][0].__setitem__(k,v)
run('positive-two-originals-and-128-frozen-files')
for k,v in [('schema','wrong'),('status','HOLD'),('findings',[{'toy':'finding'}]),('documentId','wrong'),('documentSha256','wrong'),('referenceMode','source-only'),('sourceSnapshotManifestSha256','wrong'),('frozenRuntimeAll128FilesUnchanged',False),('inputBeforeAfterPinsUnchanged',False),('exactRgbaComparisonAndCompletePixelCoverage',False),('rendererRuntimeReceiptSha256','wrong')]:run(k,qfield(k,v),False)
for k,v in [('actuallyViewed',False),('actuallyViewed',0),('actuallyViewedBy','root'),('pixelsEqualToOriginalRegion',False),('scale',2)]:run('tile-'+k+'-'+str(v),cfield(k,v),False)
run('missing actuallyViewed',lambda q,*a:q['captures'][0].pop('actuallyViewed'),False)
run('duplicate tile path',lambda q,*a:q['captures'].append(copy.deepcopy(q['captures'][0])),False)
run('count mismatch',qfield('actuallyViewedTileCount',1),False)
run('image-count mismatch',qfield('actuallyViewedImageCount',1),False)
run('runtime-byte-drift',lambda q,r,*a:(r/'runtime/f000.py').write_text('drift',encoding='utf8'),False)
run('runtime-file-removed',lambda q,r,*a:(r/'runtime/f000.py').unlink(),False)
run('runtime-file-added',lambda q,r,*a:(r/'runtime/extra.py').write_text('extra',encoding='utf8'),False)
run('canonical-byte-drift',lambda q,r,c,*a:c.write_text('drift',encoding='utf8'),False)
run('render-parent-mismatch',lambda q,r,c,rr,rp,*a:(write(rp,{**json.loads(rp.read_text()),'sourceSha256':'wrong'}),q.__setitem__('renderPinsSha256',digest(rp))),False)
run('opaque-RGBA-different-color',lambda q,r,*a:(Image.new('RGBA',(6,4),(99,0,0,255)).save(r/'t0.png'),q['captures'][0].__setitem__('sha256',digest(r/'t0.png'))),False)
def gap(q,r,*a):
 Image.new('RGBA',(5,4),(0,90,150,255)).save(r/'t0.png');q['captures'][0]['sha256']=digest(r/'t0.png');q['captures'][0]['sourceRectangle']['width']=5
run('coverage-one-pixel-column-gap',gap,False)
run('empty-captures-with-zero-counts',lambda q,*a:(q.__setitem__('captures',[]),q.__setitem__('actuallyViewedTileCount',0),q.__setitem__('actuallyViewedImageCount',0)),False)
run('whole-original-omitted-but-inventory-remains',lambda q,*a:(q.__setitem__('captures',q['captures'][:1]),q.__setitem__('actuallyViewedTileCount',1),q.__setitem__('actuallyViewedImageCount',1)),False)
run('viewed-index-false-not-cross-checked',lambda q,r,c,rr,rp,inv,idx:(write(idx,{'actuallyViewed':False}),q.__setitem__('actuallyViewedIndexRecordSha256',digest(idx))),False)
run('inventory-empty-not-cross-checked',lambda q,r,c,rr,rp,inv,idx:(write(inv,{'captures':[]}),q.__setitem__('tileInventorySha256',digest(inv))),False)

# Execute only the main four-state set/actual-inspection checks using own tuples.
clauses=[n for n in main.body if isinstance(n,ast.If) and any(s in ast.unparse(n) for s in ['Exactly four states required','Every captured state needs'])]
def stateprobe(name,modifier=None,expected=True):
 capture={'images':[{'stateId':s,'path':s+'.png','sha256':'toy-'+s} for s in ['initial','normal','error','view-edit']]}
 actual={'reviewedImages':[dict(x,actuallyReviewed=True,scale=1) for x in capture['images']]}
 if modifier:modifier(capture,actual)
 ns={'capture':capture,'actual':actual,'MODES':{'initial','normal','error','view-edit'},'expected':{(e['stateId'],e['path'],e['sha256']) for e in capture['images']}}
 accepted=True;error=None
 try:exec(compile(ast.Module(copy.deepcopy(clauses),[]),'<four-state-toy>','exec'),ns)
 except Exception as e:accepted=False;error=str(e)
 cases.append({'name':name,'passed':accepted==expected,'accepted':accepted,'expectedAccepted':expected,'error':error})
stateprobe('four-state-positive')
stateprobe('four-state-duplicate',lambda c,a:c['images'][0].__setitem__('stateId','normal'),False)
stateprobe('four-state-missing',lambda c,a:c['images'].pop(),False)
stateprobe('actual-state-false',lambda c,a:a['reviewedImages'][0].__setitem__('actuallyReviewed',False),False)
stateprobe('actual-state-missing-flag',lambda c,a:a['reviewedImages'][0].pop('actuallyReviewed'),False)
stateprobe('actual-state-parent-image-drift',lambda c,a:a['reviewedImages'][0].__setitem__('sha256','changed'),False)
stateprobe('actual-state-scaled',lambda c,a:a['reviewedImages'][0].__setitem__('scale',2),False)
assert digest(TARGET)==initial
issues=[c for c in cases if not c['passed']]
out={'schema':'independent-code-toy-audit/1','createdUtc':datetime.now(timezone.utc).isoformat(),'subject':str(TARGET),'subjectSha256':initial,'scope':'AST_FUNCTIONS_AND_OWN_TOY_PNGS_METADATA_ONLY','cases':cases,'passed':sum(c['passed'] for c in cases),'total':len(cases),'findings':issues,'productionSourceCanonicalStateExpectedRubricRawReads':0,'providerApplicationRuns':0,'productionMainRuns':0,'codeUnchanged':True,'limitations':['128 runtime files are own toy fixtures; no production runtime receipt or captures were read.','Main four-state guards are isolated AST checks; actual whole main is not executed.','TOY evidence schemas are synthetic; findings establish absence of set linkage checks in this helper, not invalidity of any production inspection.']}
p=H/'review.json';assert not p.exists();p.write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps({'passed':out['passed'],'total':out['total'],'findings':[{k:c[k] for k in ['name','accepted','returnedImages'] if k in c} for c in issues],'sha256':digest(p)}))
