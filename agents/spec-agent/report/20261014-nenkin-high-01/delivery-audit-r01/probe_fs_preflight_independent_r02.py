"""Independent synthetic-only filesystem guard checks; no Artifact or business reads."""
import hashlib,importlib.util,json,stat,types
from pathlib import Path
D=Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\.tmp\20261014-nenkin-high-01\delivery')
O=Path(__file__).parent
p=D/'fs_preflight_v2_62_r02.py';raw=p.read_bytes();pin='4c03b060269ee36dbbb1b8368fbb6cde9a95a6f7e91849e376c40919b61c567c'
assert hashlib.sha256(raw).hexdigest()==pin
spec=importlib.util.spec_from_file_location('fs_independent_v2',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
checks=[]
def check(name,expected,fn):
    try:fn();seen=True
    except (ValueError,FileNotFoundError):seen=False
    checks.append({'name':name,'expectedAccepted':expected,'observedAccepted':seen,'pass':seen==expected});assert seen==expected,name
toy=O/'fs-independent-toy-r01';toy.mkdir()
mdroot=toy/'markdown-root';mdroot.mkdir();renderroot=toy/'render-root';renderroot.mkdir()
def file(path,content):
    with path.open('xb') as h:h.write(content)
    return {'path':str(path),'sha256':hashlib.sha256(content).hexdigest()}
model=file(toy/'model.json',b'{"synthetic":true}')
image=file(renderroot/'diagram.png',b'SYNTHETIC NONIMAGE PNG BYTES: do not render')
md=file(mdroot/'toy.md',b'# Synthetic fixture only\n001 =literal\n')
binding={'schema':'reverse-agent-delivery-binding/1','permittedMarkdownRoot':str(mdroot),'permittedRenderRoot':str(renderroot)}
bound=file(toy/'binding.json',json.dumps(binding).encode())
def request(path,role='image',**extra):return {'schema':m.SCHEMA,'path':path,'role':role,'operation':'read','expectedSha256':image['sha256'],'binding':bound,**extra}
check('own pinned model read',True,lambda:m.check(request(model['path'],'model',expectedSha256=model['sha256'])))
check('bound PNG pin accepted',True,lambda:m.check(request(image['path'])))
check('bound Markdown pin accepted',True,lambda:m.check(request(md['path'],'markdown',expectedSha256=md['sha256'])))
check('PNG drift rejected',False,lambda:m.check(request(image['path'],expectedSha256='0'*64)))
check('wrong file extension rejected',False,lambda:m.check(request(md['path'],expectedSha256=md['sha256'])))
bad_schema=file(toy/'binding-wrong-schema.json',json.dumps({**binding,'schema':'wrong'}).encode())
check('binding schema rejected',False,lambda:m.check(request(image['path'],binding=bad_schema)))
wide=file(toy/'binding-wide-root.json',json.dumps({**binding,'permittedRenderRoot':str(m.WORKSPACE)}).encode())
check('whole workspace permitted root rejected',False,lambda:m.check(request(image['path'],binding=wide)))
protected=file(toy/'binding-protected-root.json',json.dumps({**binding,'permittedRenderRoot':str(m.OWN_TMP/'input')}).encode())
check('raw input permitted root rejected before read',False,lambda:m.check(request(image['path'],binding=protected)))
check('outside run model rejected before read',False,lambda:m.check(request(str(m.WORKSPACE/'outside.json'),'model')))
output=toy/'output';fresh=output/'fresh.xlsx'
def write_req(**extra):return {'schema':m.SCHEMA,'path':str(fresh),'role':'output','operation':'save-fresh','outputRoot':str(output),**extra}
check('fresh owned output preflight accepted',True,lambda:m.check(write_req()))
check('output escaping exact outputroot rejected',False,lambda:m.check({**write_req(),'path':str(toy/'escape.xlsx')}))
check('owned existing save rejected',False,lambda:m.check({**write_req(),'path':model['path'],'outputRoot':str(toy)}))
check('undeclared owned write rejected',False,lambda:m.check({**write_req(),'operation':'write-owned'}))
for value in ('a:stream.md','a\x00.md','a\n.md','../a.md','a\\b.md','a//b.md','/a.md'):
    check('canonical unsafe '+repr(value),False,lambda value=value:m.canonical_relative(value,suffix='.md'))
check('canonical Unicode hierarchy accepted',True,lambda:m.canonical_relative('基本設計書/01_題名.md',suffix='.md'))
class FakePath:
    def __init__(self,attrs=0,mode=stat.S_IFREG):self.attrs=attrs;self.mode=mode;self.parents=()
    def lstat(self):return types.SimpleNamespace(st_mode=self.mode,st_file_attributes=self.attrs,st_size=10)
    def resolve(self,strict=False):return self
regular=FakePath();child=FakePath(attrs=0x400);ancestor=FakePath(attrs=0x400);regular.parents=(ancestor,)
check('reparse child metadata rejected',False,lambda:m.metadata(child,expectation='existing',kind='file'))
check('reparse ancestor metadata rejected',False,lambda:m.metadata(regular,expectation='existing',kind='file'))
check('symlink metadata rejected',False,lambda:m.metadata(FakePath(mode=stat.S_IFLNK),expectation='existing',kind='file'))
check('unknown metadata expectation rejected',False,lambda:m.metadata(FakePath(),expectation='unchecked'))
check('unknown metadata kind rejected',False,lambda:m.metadata(FakePath(),kind='arbitrary'))
check('ordinary file metadata accepted',True,lambda:m.metadata(FakePath(),expectation='existing',kind='file'))
check('duplicate JSON member rejected',False,lambda:m.json_unique('{"x":1,"x":2}'))
check('nonfinite JSON rejected',False,lambda:m.json_unique('{"x":NaN}'))
assert p.read_bytes()==raw
result={'scope':'INDEPENDENT_CODE_AND_SYNTHETIC_FILES_ONLY','status':'PASS','candidate':{'path':str(p),'sha256':pin},'checks':checks,'count':len(checks),'actualAuthoring':0,'productionBusinessReads':0,'actualImageRenders':0,'providers':0,'realJunctionCreated':False,'limitations':['The guard remains a non-atomic check/use projection.','Caller ownership is a declaration, not an OS ownership proof.','Runtime and package-internal filesystem activity is outside this helper scope.','Toy PNG bytes are nonimage metadata fixtures, not renderable artifacts.']}
out=O/'fs-preflight-independent-probes-r02.json'
with out.open('x',encoding='utf-8') as h:json.dump(result,h,ensure_ascii=False,indent=2);h.write('\n')
print(json.dumps({'path':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'checks':len(checks)}))
