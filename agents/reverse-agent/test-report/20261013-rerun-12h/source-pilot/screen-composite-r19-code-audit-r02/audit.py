import ast,copy,json,hashlib,types
from pathlib import Path
from PIL import Image
from datetime import datetime,timezone
H=Path(__file__).resolve().parent;T=H.parents[1]/'scripts/record_screen_composite_r19_r02.py'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,o):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o),encoding='utf8')
def guard(p):
 p=Path(p).absolute()
 for a in [p,*p.parents]:
  if a.exists() and (a.is_symlink() or getattr(a.lstat(),'st_file_attributes',0)&0x400):raise ValueError('Linked path')
 return p.resolve()
initial=digest(T);tree=ast.parse(T.read_text(encoding='utf8'));funcs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name!='main'];main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main');cases=[]
def run(name,mutator=None,expected=False):
 root=H/'f'/f'{len(cases):02}';root.mkdir(parents=True);c=root/'canon.md';c.write_text('# own toy',encoding='utf8');cap=root/'manifest.json';write(cap,{'own':'toy'});capsha=digest(cap)
 runtime=root/'runtime';runtime.mkdir();files={}
 for i in range(128):
  p=runtime/f'f{i:03}.py';p.write_text(f'# own {i}',encoding='utf8');files[p.name]=digest(p)
 receipt=root/'runtime.json';write(receipt,{'destination':str(runtime),'files':files});rsha=digest(receipt)
 render=root/'render';render.mkdir();captures=[];records=[];artifacts=[]
 for i in range(2):
  imageid=f'diagram-{i+1:03}';o=render/(imageid+'.png');t=root/f't{i}.png';Image.new('RGBA',(6,4),(i*40,90,150,255)).save(o);Image.open(o).save(t)
  base={'imageId':imageid,'originalPath':str(o),'originalSha256':digest(o),'path':str(t),'sha256':digest(t),'wholeOriginalSize':[6,4],'sourceRectangle':{'x':0,'y':0,'width':6,'height':4},'scale':1,'pixelsEqualToOriginalRegion':True,'actuallyReviewed':False}
  captures.append(dict(base,actuallyViewed=True,actuallyViewedBy='delivery_tools',captureIndexZeroBased=i,view='original pixels'))
  records.append({'id':imageid,'status':'PASS','png':{'width':6,'height':4,'sha256':digest(o)}});artifacts.append({'path':o.name,'sha256':digest(o),'bytes':o.stat().st_size})
 html=render/'document.html';html.write_text('<p>own fixture</p>',encoding='utf8');artifacts.append({'path':html.name,'sha256':digest(html),'bytes':html.stat().st_size})
 rp=render/'render-pins.json';pins={'documentId':'TOY','sourceSha256':digest(c),'source':str(c),'sourceSnapshotManifestSha256':capsha,'referenceMode':'training-assisted','inputBeforeAfterUnchanged':True,'rendererRuntimeReceipt':str(receipt),'rendererRuntimeReceiptSha256':rsha,'rendererRuntimeFileCount':128,'diagrams':records,'layouts':[],'artifacts':artifacts,'inputPins':{str(c):digest(c),str(receipt):rsha,str(cap):capsha}}
 write(rp,pins);inv=root/'inventory.json';inventory={'schema':'native-review-tile-inventory/1','documentId':'TOY','documentSha256':digest(c),'referenceMode':'training-assisted','sourceSnapshotSha256':capsha,'renderPinsSha256':digest(rp),'captures':[{k:v for k,v in e.items() if k not in ['actuallyViewed','actuallyViewedBy','captureIndexZeroBased','view']} for e in captures]};write(inv,inventory)
 q={'schema':'screen-native-review/2','status':'PASS_NATIVE_GEOMETRY_ONLY','findings':[],'documentId':'TOY','documentSha256':digest(c),'canonicalDocumentPath':str(c),'frozenRuntimeAll128FilesUnchanged':True,'inputBeforeAfterPinsUnchanged':True,'exactRgbaComparisonAndCompletePixelCoverage':True,'rendererRuntimeReceipt':str(receipt),'rendererRuntimeReceiptSha256':rsha,'renderPins':str(rp),'renderPinsSha256':digest(rp),'tileInventory':str(inv),'tileInventorySha256':digest(inv),'captures':captures,'actuallyViewedTileCount':2,'actuallyViewedImageCount':2,'diagramCount':2,'layoutCount':0,'beforeAfterPins':{str(c):digest(c),str(receipt):rsha,str(cap):capsha,str(rp):digest(rp),str(inv):digest(inv),**{str(render/a['path']):a['sha256'] for a in artifacts},**{e['path']:e['sha256'] for e in captures}}}
 ns={'Path':Path,'hashlib':hashlib,'json':json,'Image':Image,'capsule':types.SimpleNamespace(safe_path=guard),'REPO':root,'CAP_SHA':capsha,'RUNTIME_SHA':rsha,'TRACKED_PINS':{},'RUNTIME_ROOTS':{}}
 exec(compile(ast.Module(copy.deepcopy(funcs),[]),str(T),'exec'),ns)
 f={'q':q,'root':root,'c':c,'receipt':receipt,'rp':rp,'inv':inv,'pins':pins,'inventory':inventory,'ns':ns}
 if mutator:mutator(f)
 qp=root/'qa.json';write(qp,q);accepted=True;error=None;result=None
 try:result=ns['tile_review'](qp,digest(qp),c,'TOY')
 except Exception as e:accepted=False;error=f'{type(e).__name__}: {e}'
 cases.append({'name':name,'expectedAccepted':expected,'accepted':accepted,'passed':accepted==expected,'images':len(result) if result is not None else None,'error':error})
def rewrite_inv(f):
 write(f['inv'],f['inventory']);f['q']['tileInventorySha256']=digest(f['inv']);f['q']['beforeAfterPins'][str(f['inv'])]=digest(f['inv'])
def rewrite_pins(f):
 write(f['rp'],f['pins']);f['q']['renderPinsSha256']=digest(f['rp']);f['q']['beforeAfterPins'][str(f['rp'])]=digest(f['rp']);f['inventory']['renderPinsSha256']=digest(f['rp']);rewrite_inv(f)
def q(k,v):return lambda f:f['q'].__setitem__(k,v)
def e(k,v):return lambda f:f['q']['captures'][0].__setitem__(k,v)
run('positive-real-v2-key-shape-no-legacy-index',expected=True)
for k,v in [('schema','wrong'),('status','HOLD'),('findings',[{'own':'toy'}]),('documentId','wrong'),('documentSha256','wrong'),('canonicalDocumentPath','wrong'),('frozenRuntimeAll128FilesUnchanged',False),('inputBeforeAfterPinsUnchanged',False),('exactRgbaComparisonAndCompletePixelCoverage',False),('rendererRuntimeReceiptSha256','wrong'),('actuallyViewedTileCount',0),('actuallyViewedTileCount',True),('actuallyViewedImageCount',0),('actuallyViewedImageCount',1),('diagramCount',1),('layoutCount',1)]:run('qa-'+k+'-'+str(v),q(k,v))
for k,v in [('actuallyViewed',False),('actuallyViewed',0),('actuallyViewedBy','root'),('pixelsEqualToOriginalRegion',False),('scale',2),('scale',True),('captureIndexZeroBased',1),('captureIndexZeroBased',False)]:run('tile-'+k+'-'+str(v),e(k,v))
run('missing-actual-view-flag',lambda f:f['q']['captures'][0].pop('actuallyViewed'))
run('empty-counts-captures',lambda f:(f['q'].__setitem__('captures',[]),f['q'].__setitem__('actuallyViewedTileCount',0),f['q'].__setitem__('actuallyViewedImageCount',0)))
run('whole-original-omission-inventory-full',lambda f:(f['q'].__setitem__('captures',f['q']['captures'][:1]),f['q'].__setitem__('actuallyViewedTileCount',1),f['q'].__setitem__('actuallyViewedImageCount',1)))
def omit_both(f):
 f['q']['captures']=f['q']['captures'][:1];f['q']['actuallyViewedTileCount']=1;f['q']['actuallyViewedImageCount']=1;f['inventory']['captures']=f['inventory']['captures'][:1];rewrite_inv(f)
run('whole-original-omitted-both-qa-inventory',omit_both)
run('qa-order-reversed',lambda f:f['q']['captures'].reverse())
run('inventory-order-reversed',lambda f:(f['inventory']['captures'].reverse(),rewrite_inv(f)))
run('inventory-empty',lambda f:(f['inventory'].__setitem__('captures',[]),rewrite_inv(f)))
for k,v in [('schema','wrong'),('documentId','other'),('documentSha256','wrong'),('referenceMode','source-only'),('sourceSnapshotSha256','wrong'),('renderPinsSha256','wrong')]:run('inventory-'+k,lambda f,k=k,v=v:(f['inventory'].__setitem__(k,v),rewrite_inv(f)))
run('inventory-rectangle-drift',lambda f:(f['inventory']['captures'][0]['sourceRectangle'].__setitem__('width',5),rewrite_inv(f)))
run('duplicate-tile-in-both',lambda f:(f['q']['captures'].__setitem__(1,{**f['q']['captures'][0],'captureIndexZeroBased':1}),f['inventory']['captures'].__setitem__(1,copy.deepcopy(f['inventory']['captures'][0])),rewrite_inv(f)))
for k,v in [('sourceSha256','wrong'),('referenceMode','source-only'),('sourceSnapshotManifestSha256','wrong'),('rendererRuntimeReceiptSha256','wrong'),('rendererRuntimeFileCount',126)]:run('render-'+k,lambda f,k=k,v=v:(f['pins'].__setitem__(k,v),rewrite_pins(f)))
run('render-extra-canonical-image',lambda f:(f['pins']['diagrams'].append(copy.deepcopy(f['pins']['diagrams'][0])),rewrite_pins(f)))
run('missing-beforeafter-canonical',lambda f:f['q']['beforeAfterPins'].pop(str(f['c'])))
run('missing-beforeafter-tile',lambda f:f['q']['beforeAfterPins'].pop(f['q']['captures'][0]['path']))
run('missing-beforeafter-artifact',lambda f:f['q']['beforeAfterPins'].pop(str(f['root']/'render/document.html')))
run('artifact-byte-drift',lambda f:(f['root']/'render/document.html').write_text('drift'))
run('artifact-path-escape',lambda f:(f['pins']['artifacts'][0].__setitem__('path','../outside.png'),rewrite_pins(f)))
run('beforeafter-empty',q('beforeAfterPins',{}))
run('runtime-file-added',lambda f:(f['root']/'runtime/extra.py').write_text('extra'))
run('runtime-file-removed',lambda f:(f['root']/'runtime/f000.py').unlink())
run('runtime-byte-drift',lambda f:(f['root']/'runtime/f000.py').write_text('drift'))
run('canonical-byte-drift',lambda f:f['c'].write_text('drift'))
def rgba(f):
 t=Path(f['q']['captures'][0]['path']);Image.new('RGBA',(6,4),(255,0,0,255)).save(t);new=digest(t);f['q']['captures'][0]['sha256']=new;f['inventory']['captures'][0]['sha256']=new;f['q']['beforeAfterPins'][str(t)]=new;rewrite_inv(f)
run('opaque-RGBA-negative-even-repinned',rgba)
def gap(f):
 a=f['q']['captures'][0];t=Path(a['path']);Image.new('RGBA',(5,4),(0,90,150,255)).save(t);a['sha256']=digest(t);a['sourceRectangle']['width']=5;f['inventory']['captures'][0]={k:v for k,v in a.items() if k not in ['actuallyViewed','actuallyViewedBy','captureIndexZeroBased','view']};f['q']['beforeAfterPins'][str(t)]=digest(t);rewrite_inv(f)
run('one-pixel-coverage-gap-repinned',gap)
def late(f):
 original=f['ns']['recheck_all_inputs']
 def wrapper():
  f['c'].write_text('late drift');original()
 f['ns']['recheck_all_inputs']=wrapper
run('canonical-drift-before-final-recheck',late)
def late_membership(f):
 original=f['ns']['recheck_all_inputs']
 def wrapper():
  (f['root']/'runtime/late.py').write_text('late');original()
 f['ns']['recheck_all_inputs']=wrapper
run('runtime-membership-drift-before-final-recheck',late_membership)
# Existing four-state actual guards remain unchanged from r01; isolate them again.
clauses=[n for n in main.body if isinstance(n,ast.If) and any(s in ast.unparse(n) for s in ['Exactly four states required','Every captured state needs'])]
def state(name,mod=None,expect=False):
 cap={'images':[{'stateId':s,'path':s+'.png','sha256':'own'+s} for s in ['initial','normal','error','view-edit']]};actual={'reviewedImages':[dict(x,actuallyReviewed=True,scale=1) for x in cap['images']]}
 if mod:mod(cap,actual)
 ns={'capture':cap,'actual':actual,'MODES':{'initial','normal','error','view-edit'},'expected':{(e['stateId'],e['path'],e['sha256']) for e in cap['images']}};accepted=True;err=None
 try:exec(compile(ast.Module(copy.deepcopy(clauses),[]),'<own-state>','exec'),ns)
 except Exception as x:accepted=False;err=str(x)
 cases.append({'name':name,'expectedAccepted':expect,'accepted':accepted,'passed':accepted==expect,'error':err})
state('state-four-positive',expect=True);state('state-duplicate',lambda c,a:c['images'][0].__setitem__('stateId','normal'));state('state-missing',lambda c,a:c['images'].pop());state('state-unreviewed',lambda c,a:a['reviewedImages'][0].__setitem__('actuallyReviewed',False));state('state-missing-reviewedflag',lambda c,a:a['reviewedImages'][0].pop('actuallyReviewed'));state('state-image-sha-drift',lambda c,a:a['reviewedImages'][0].__setitem__('sha256','wrong'));state('state-scaled',lambda c,a:a['reviewedImages'][0].__setitem__('scale',2))
assert digest(T)==initial
out={'schema':'code-synthetic-audit/1','createdUtc':datetime.now(timezone.utc).isoformat(),'subject':str(T),'subjectSha256':initial,'status':'PASS' if all(x['passed'] for x in cases) else 'FAILED','passed':sum(x['passed'] for x in cases),'total':len(cases),'cases':cases,'productionMainOrProviderApplicationRuns':0,'productionBodyReferenceExpectedRawReads':0,'productionQaRead':'Only one root-authorized r19 example JSON metadata key shape was inspected separately; tests use own toy files/images.','limitations':['No production capture/parent/runtime is executed or validated by this audit.','128 runtime toy files exercise inventory equality; state clauses isolated from main.','No new actual-view assertion or semantic approval is created.']};p=H/'review.json';assert not p.exists();write(p,out);print(json.dumps({'passed':out['passed'],'total':out['total'],'failures':[x for x in cases if not x['passed']],'sha256':digest(p)}))
