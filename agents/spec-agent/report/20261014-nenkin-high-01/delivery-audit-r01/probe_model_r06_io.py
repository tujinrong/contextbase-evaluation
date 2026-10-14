"""Synthetic bound drafts/render metadata only; do not call model CLI or providers."""
import ast,hashlib,importlib.util,json
from pathlib import Path
D=Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\.tmp\20261014-nenkin-high-01\delivery');O=Path(__file__).parent
p=D/'delivery_model_v2_62_r06.py';before=p.read_bytes();pin='f8bacc711c751659ef0a6497c46e76a496833d20e311cd234111baa7042a1c31';assert hashlib.sha256(before).hexdigest()==pin
spec=importlib.util.spec_from_file_location('model_io_r06',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
checks=[]
def check(name,expected,fn):
    try:fn();seen=True
    except ValueError:seen=False
    checks.append({'name':name,'expectedAccepted':expected,'observedAccepted':seen,'pass':seen==expected});assert seen==expected,name
toy=O/'model-io-toy-r01';toy.mkdir();mdroot=toy/'drafts';mdroot.mkdir();renderroot=toy/'render';renderroot.mkdir()
def file(path,raw):
    with path.open('xb') as h:h.write(raw)
    return hashlib.sha256(raw).hexdigest()
def jfile(path,data):return file(path,json.dumps(data,ensure_ascii=False).encode('utf-8'))
md=mdroot/'toy.md';mdsha=file(md,b'# Toy fixture\n001 =literal\n')
html=b'<html><body>Toy fixture only</body></html>'
htmlsha=file(renderroot/'toy.html',html);file(renderroot/'document.html',html)
pngsha=file(renderroot/'diagram-001.png',b'TOY NONIMAGE PNG PIN FIXTURE ONLY')
manifest={'sourceSha256':mdsha,'documentId':'TOY','canonicalDocumentPath':'toy.md','sourceSnapshotManifestSha256':'0'*64,'structure':{'status':'PASS','findings':[]},'display':{'status':'PASS','blockedRequests':[],'errors':[]},'safety':{'removed':[],'inputJavaScriptEnabled':False},'referenceMode':'source-only','artifacts':[{'path':'toy.html','sha256':htmlsha},{'path':'document.html','sha256':htmlsha},{'path':'diagram-001.png','sha256':pngsha}],'layouts':[],'diagrams':[{'id':'diagram-001','status':'PASS','sourceLines':[1,2],'png':{'width':10,'height':10}}]}
pins={**manifest,'canonicalHtmlFilename':'toy.html','canonicalHtmlSha256':htmlsha}
pinsha=jfile(renderroot/'render-pins.json',pins);mansha=jfile(renderroot/'manifest.json',manifest)
entry={'documentId':'TOY','canonicalDocumentPath':'toy.md','markdown':str(md),'markdownSha256':mdsha,'renderDirectory':str(renderroot),'renderPinsSha256':pinsha,'renderManifestSha256':mansha}
binding={'schema':m.SCHEMA.replace('model','binding'),'permittedMarkdownRoot':str(mdroot),'permittedRenderRoot':str(renderroot),'sourceSnapshotManifestSha256':'0'*64,'referenceMode':'source-only','documents':[entry]}
bound=toy/'binding.json';boundsha=jfile(bound,binding)
check('own synthetic pinned binding accepted',True,lambda:m.load_bound(bound,boundsha))
check('wrong binding pin refused before material read',False,lambda:m.load_bound(bound,'0'*64))
check('missing explicit binding pin refused',False,lambda:m.load_bound(bound,None))
check('render child ordinary accepted',True,lambda:m.render_child(renderroot,'diagram-001.png'))
for name in ('../diagram-001.png','a:stream.png','a\x00.png','a\x7f.png','sub/file.png'):
    check('unsafe render child '+repr(name),False,lambda name=name:m.render_child(renderroot,name))
original_safe=m.safe_path;reads=[]
def spy(value):reads.append(str(value));return original_safe(value)
m.safe_path=spy
try:m.load_bound(bound,boundsha)
finally:m.safe_path=original_safe
for name in ('render-pins.json','manifest.json','toy.html','document.html','diagram-001.png'):
    check('read metadata gate reached for '+name,True,lambda name=name:any(Path(path).name==name for path in reads) or (_ for _ in ()).throw(ValueError('missing IO gate')))
for name in ('x:stream.md','a\x7f.md','../x.md'):
    check('canonical guarded '+repr(name),False,lambda name=name:m.canonical(name))
prior=(D/'delivery_model_v2_62_r05.py').read_bytes()
def functions(raw):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(raw).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
old,new=functions(prior),functions(before)
delta=sorted(k for k in old.keys()|new.keys() if old.get(k)!=new.get(k))
assert delta==['canonical','load_bound','main','render_child']
assert p.read_bytes()==before
result={'scope':'CODE_AND_SYNTHETIC_IO_ONLY','status':'PASS','candidate':{'path':str(p),'sha256':pin},'checks':checks,'count':len(checks),'changedFunctions':delta,'businessParserAndSheetPlacementUnchanged':True,'providers':0,'actualBusinessReads':0,'actualModelExport':0,'actualAuthoring':0,'htmlExecuted':False,'imageRendered':False,'limitations':['Toy HTML/PNG bytes were pinned and read as data only.','No actual canonical draft was read and no delivery package was created.','Non-atomic filesystem checks remain explicitly limited.']}
out=O/'model-r06-io-probes.json'
with out.open('x',encoding='utf-8') as h:json.dump(result,h,ensure_ascii=False,indent=2);h.write('\n')
print(json.dumps({'path':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'checks':len(checks)}))
