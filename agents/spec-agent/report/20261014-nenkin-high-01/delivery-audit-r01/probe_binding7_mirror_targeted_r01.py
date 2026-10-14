"""Targeted mirror delta only; pure metadata and entirely virtual byte inventory.
No helper import/build, real document, source, capsule, output, or render read.
"""
import ast,copy,hashlib,json,re,stat,sys
from pathlib import Path,PureWindowsPath
from types import SimpleNamespace
from datetime import datetime,timezone
sys.dont_write_bytecode=True
W=Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\.tmp\20261014-nenkin-high-01')
A=Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\report\20261014-nenkin-high-01\delivery-audit-r01')
SOURCE=W/'delivery/build_delivery_binding_r07.py';OLD=W/'delivery/build_delivery_binding_r06.py';RENDERER=W/'render_reviewed_r06.py'
EXPECTED='d01e3586ddd9f171e8daa1479611f2ba3d800ef906979d4f60cd1ad9da7297ed'
OLD_SHA='05986ecbc18642b071aa456f75c9d30390582989b3b530c5c83f7322a334ac30'
RENDER_SHA='eada05d737ed3bbf9bf0173681eb117024c9a1fa49d778040de51bdd43b40b02'
def sha(raw):return hashlib.sha256(raw).hexdigest()
raw=SOURCE.read_bytes();old_raw=OLD.read_bytes();assert sha(raw)==EXPECTED and sha(old_raw)==OLD_SHA and sha(RENDERER.read_bytes())==RENDER_SHA
text=raw.decode('utf-8');tree=ast.parse(text);old_tree=ast.parse(old_raw.decode('utf-8'))
def require(ok,message):
    if not ok:raise ValueError('HOLD: '+message)
def lexical_safe(value):
    p=Path(value);require(p.is_absolute(),'synthetic absolute path');return p
def relative(value):
    require(isinstance(value,str) and value and '\\' not in value and ':' not in value and not value.startswith('/') and not any(ord(c)<32 or ord(c)==127 for c in value),'canonical relative')
    require(all(s not in {'','.','..'} and not s.endswith((' ','.')) for s in value.split('/')),'canonical segments')
    require(not any(s.split('.')[0].casefold() in {'con','prn','aux','nul',*[f'com{i}' for i in range(1,10)],*[f'lpt{i}' for i in range(1,10)]} for s in value.split('/')),'device segment')
    return Path(value)
ns={'WORK':W,'Path':Path,'require':require,'safe':lexical_safe,'relative':relative,'hashlib':hashlib,'re':re}
selected={'digest','mirror_model','exclusive_mirror_inventory','verify_mirror_bytes'}
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in selected]
assert len(nodes)==4
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(SOURCE)+'-functions-only','exec'),ns)

# Only new mirror call is added to metadata_model; all previous guards remain.
old_functions={n.name:n for n in old_tree.body if isinstance(n,ast.FunctionDef)}
new_functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
class StripMirrorCall(ast.NodeTransformer):
    def visit_Expr(self,node):
        if isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='mirror_model':return None
        return self.generic_visit(node)
normalized=StripMirrorCall().visit(copy.deepcopy(new_functions['metadata_model']))
assert ast.dump(normalized,include_attributes=False)==ast.dump(old_functions['metadata_model'],include_attributes=False)
unchanged=[name for name in old_functions if ast.dump(old_functions[name],include_attributes=False)==ast.dump(new_functions[name],include_attributes=False)]
assert set(unchanged)=={'canonical_metadata_sha','digest','approved_ids','main'}
tests=[]
def case(name,fn):fn();tests.append({'name':name,'pass':True})
def reject(fn):
    try:fn()
    except (ValueError,KeyError,TypeError,AttributeError):return
    raise AssertionError('Expected mirror refusal')
case('base6-existing-metadata-guards-exact-AST-plus-one-mirror-call',lambda:None)
BLOB=b'\xef\xbb\xbfSYNTHETIC-ONLY\r\n001\r\n';MD_SHA=sha(BLOB);COLL='1'*64
doc={'documentId':'TOY-001','path':'Synthetic/Sub/01.md','canonicalMarkdown':str(W/'collections/SYNTHETIC/Synthetic/Sub/01.md'),'sha256':MD_SHA}
render=W/'renders/SYNTHETIC/TOY-001';location='md/'+doc['path']
# Independent owner calculation uses concatenated byte components.
key=sha(doc['documentId'].encode()+b'\x00'+COLL.encode()+b'\x00'+str(render).encode()+b'\x00'+doc['path'].encode())
owner=W/'render-citation-roots'/key;root=owner/'root';mirror=root/location
mapping={'schema':'spec-agent-render-citation-mirror/1','owner':str(owner),'root':str(root),'mirrorFile':str(mirror),
 'mirrorSha256':MD_SHA,'originalSource':doc['canonicalMarkdown'],'originalSourceSha256':MD_SHA,
 'canonicalDocumentPath':doc['path'],'finalMarkdownLocation':location,'finalFolderPrefixes':['md','html','PDF','Excel'],
 'inventory':{location:MD_SHA},'scope':'ONE_BYTE_IDENTICAL_APPROVED_MARKDOWN_NO_OTHER_ARTIFACTS',
 'businessTextRewritten':False,'additionalSourceOrAssetReadsAuthorized':False,'beforeAfterByteEqualityVerified':True}
statuses={'structure':{'status':'PASS','findings':[]},'display':{'status':'PASS','errors':[],'blockedRequests':[]},'safety':{'removed':[],'inputJavaScriptEnabled':False}}
pins={**copy.deepcopy(statuses),'source':doc['canonicalMarkdown'],'rendererSource':str(mirror),'rendererSourceSha256':MD_SHA,'citationMirror':copy.deepcopy(mapping)}
manifest={**copy.deepcopy(statuses),'source':str(mirror),'citationMirror':copy.deepcopy(mapping)}
original={**copy.deepcopy(statuses),'source':str(mirror),'sourceSha256':MD_SHA,'originalModified':False}
def fixture():return [copy.deepcopy(v) for v in (pins,manifest,original,doc,render,COLL)]
def model(f):return ns['mirror_model'](*f)
def positive():assert model(fixture())==mapping and len(mapping)==15
case('exact15fields-independent-NUL-owner-key-final4-original-vs-mirror-positive',positive)
def neg(name,mutate):
    def fn():f=fixture();mutate(f);reject(lambda:model(f))
    case(name,fn)
def map_change(f,key,value):
    f[0]['citationMirror'][key]=value;f[1]['citationMirror']=copy.deepcopy(f[0]['citationMirror'])
neg('missing-mirror-mapping',lambda f:f[0].pop('citationMirror'))
neg('extra-mapping-field',lambda f:map_change(f,'extra',True))
neg('pins-versus-enriched-mapping-not-exact',lambda f:f[1]['citationMirror'].update(mirrorSha256='f'*64))
neg('wrong-mirror-schema',lambda f:map_change(f,'schema','wrong'))
neg('wrong-single-file-scope',lambda f:map_change(f,'scope','OTHER'))
neg('text-rewrite-flag',lambda f:map_change(f,'businessTextRewritten',True))
neg('additional-source-read-flag',lambda f:map_change(f,'additionalSourceOrAssetReadsAuthorized',True))
neg('beforeafter-byte-flag-not-true',lambda f:map_change(f,'beforeAfterByteEqualityVerified',False))
neg('canonical-document-mapping-mismatch',lambda f:map_change(f,'canonicalDocumentPath','OTHER.md'))
neg('final-four-prefix-order-or-case-mismatch',lambda f:map_change(f,'finalFolderPrefixes',['MD','html','PDF','Excel']))
neg('wrong-owner-key-directory',lambda f:map_change(f,'owner',str(W/'render-citation-roots'/('f'*64))))
neg('wrong-mirror-root-template',lambda f:map_change(f,'root',str(owner/'other')))
neg('wrong-mirror-file-template',lambda f:map_change(f,'mirrorFile',str(root/'md/OTHER.md')))
def owner_bound_inputs():
    for which in ('docid','collection','render'):
        f=fixture()
        if which=='docid':f[3]['documentId']='TOY-OTHER'
        elif which=='collection':f[5]='2'*64
        else:f[4]=W/'renders/SYNTHETIC/OTHER'
        reject(lambda f=f:model(f))
case('owner-key-binds-documentID-collectionSHA-render-directory',owner_bound_inputs)
def original_mapping():
    for key,value in (('originalSource',str(W/'collections/SYNTHETIC/OTHER.md')),('originalSourceSha256','f'*64),('inventory',{location:MD_SHA,'extra.md':MD_SHA})):
        f=fixture();map_change(f,key,value);reject(lambda f=f:model(f))
case('original-source-path-SHA-and-single-file-inventory-bound',original_mapping)
def pin_sources():
    for key,value in (('source',str(mirror)),('rendererSource',doc['canonicalMarkdown']),('rendererSourceSha256','f'*64)):
        f=fixture();f[0][key]=value;reject(lambda f=f:model(f))
case('pins-original-source-renderer-mirror-source-and-SHA-not-interchangeable',pin_sources)
def manifests_sources():
    for which,key,value in ((1,'source',doc['canonicalMarkdown']),(2,'source',doc['canonicalMarkdown']),(2,'sourceSha256','f'*64)):
        f=fixture();f[which][key]=value;reject(lambda f=f:model(f))
case('enriched-and-untouched-original-manifest-source-must-be-mirror',manifests_sources)
def raw_statuses():
    for key in ('originalModified','structure','display','safety'):
        f=fixture()
        if key=='originalModified':f[2][key]=True
        else:f[2][key]={'status':'DIFFERENT'}
        reject(lambda f=f:model(f))
case('untouched-manifest-modification-and-all3-status-records-bound',raw_statuses)
neg('invalid-Windows-canonical-name',lambda f:f[3].update(path='Synthetic/<bad>.md'))
neg('missing-untouched-original-manifest-record',lambda f:f.__setitem__(2,None))

# No real filesystem object is consulted. The real guard safe() AST runs with
# a virtual PureWindowsPath supporting lstat/resolve only from this memory map.
guard=W/'delivery/publication_bound_r03.py';guard_raw=guard.read_bytes();assert sha(guard_raw)=='8be4c01b30a73eade999d78a039ba46911167882140f37c028c051716fc7fa6f'
guard_tree=ast.parse(guard_raw.decode('utf-8'));safe_node=next(n for n in guard_tree.body if isinstance(n,ast.FunctionDef) and n.name=='safe')
class VPath(PureWindowsPath):
    fs={}
    def lstat(self):
        node=self.fs.get(PureWindowsPath(self))
        if node is None:raise FileNotFoundError(str(self))
        return SimpleNamespace(st_mode={'dir':stat.S_IFDIR,'file':stat.S_IFREG,'link':stat.S_IFLNK}.get(node['kind'],0),st_file_attributes=node.get('attributes',0))
    def resolve(self,strict=False):return self
    def is_dir(self):return self.fs.get(PureWindowsPath(self),{}).get('kind')=='dir'
    def is_file(self):return self.fs.get(PureWindowsPath(self),{}).get('kind')=='file'
    def read_bytes(self):
        require(self.is_file(),'virtual ordinary file');return self.fs[PureWindowsPath(self)]['bytes']
    def iterdir(self):
        require(self.is_dir(),'virtual directory')
        return iter(VPath(p) for p in sorted(self.fs,key=str) if p.parent==PureWindowsPath(self))
safe_ns={'Path':VPath,'stat':stat,'require':require}
exec(compile(ast.Module(body=[safe_node],type_ignores=[]),str(guard)+'-safe-only','exec'),safe_ns)
virtual_ns=dict(ns)
for name in ('exclusive_mirror_inventory','verify_mirror_bytes'):
    node=new_functions[name]
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(SOURCE)+'-virtual-functions','exec'),virtual_ns)
virtual_ns['safe']=safe_ns['safe'];virtual_ns['hashfile']=lambda p:sha(safe_ns['safe'](p).read_bytes())
def reset():
    VPath.fs={PureWindowsPath(root):{'kind':'dir'},PureWindowsPath(doc['canonicalMarkdown']):{'kind':'file','bytes':BLOB},PureWindowsPath(mirror):{'kind':'file','bytes':BLOB}}
    for parent in PureWindowsPath(mirror).parents:
        if parent==PureWindowsPath(root):break
        VPath.fs[parent]={'kind':'dir'}
def vpositive():
    reset();virtual_ns['verify_mirror_bytes'](copy.deepcopy(mapping))
    assert virtual_ns['exclusive_mirror_inventory'](mapping)=={location:MD_SHA}
case('virtual-entire-BOM-CRLF-leadingzero-bytes-and-only-ancestor-dirs-positive',vpositive)
def vnegative(name,change,spoof_hash=False):
    def fn():
        reset();change()
        old_hash=virtual_ns['hashfile']
        if spoof_hash:virtual_ns['hashfile']=lambda p:MD_SHA
        try:reject(lambda:virtual_ns['verify_mirror_bytes'](mapping))
        finally:virtual_ns['hashfile']=old_hash
    case(name,fn)
vnegative('virtual-original-source-byte-SHA-drift',lambda:VPath.fs[PureWindowsPath(doc['canonicalMarkdown'])].update(bytes=BLOB+b'x'))
vnegative('virtual-mirror-byte-SHA-drift',lambda:VPath.fs[PureWindowsPath(mirror)].update(bytes=BLOB+b'x'))
vnegative('virtual-equal-stub-SHA-does-not-bypass-entire-byte-comparison',lambda:VPath.fs[PureWindowsPath(mirror)].update(bytes=BLOB+b'x'),True)
vnegative('virtual-extra-empty-directory-rejected',lambda:VPath.fs.update({PureWindowsPath(root/'unexpected'):{'kind':'dir'}}))
vnegative('virtual-extra-other-file-rejected',lambda:VPath.fs.update({PureWindowsPath(root/'extra.md'):{'kind':'file','bytes':BLOB}}))
vnegative('virtual-missing-mirror-file-rejected',lambda:VPath.fs.pop(PureWindowsPath(mirror)))
def vlinks():
    for key,value in ((PureWindowsPath(mirror),'reparse'),(PureWindowsPath(mirror).parent,'reparse'),(PureWindowsPath(mirror),'link')):
        reset()
        if value=='reparse':VPath.fs[key]['attributes']=0x400
        else:VPath.fs[key]['kind']='link'
        reject(lambda:virtual_ns['verify_mirror_bytes'](mapping))
case('virtual-child-ancestor-reparse-and-symlink-rejected-by-real-safe-AST',vlinks)

build=ast.get_source_segment(text,new_functions['build'])
source_checks={
 'original-manifest-descriptor-before-JSON':build.index("original_path=pinned(")<build.index("records[-1]['originalManifest']"),
 'mirror-readbytes-and-exclusive-inventory':"read_bytes()==safe(mirror).read_bytes()" in ast.get_source_segment(text,new_functions['verify_mirror_bytes']) and "exclusive_mirror_inventory(mapping)" in ast.get_source_segment(text,new_functions['verify_mirror_bytes']),
 'mirror-file-added-to-beforeafter-inputpins':"inputs[mapping['mirrorFile']]=mapping['mirrorSha256']" in build,
 'mirror-checked-in-loop-plus-pre-and-post-write':build.count('verify_mirror_bytes(mapping)')==3 and build.index('for mapping in mirror_checks:verify_mirror_bytes(mapping)')<build.index('fresh_json(output,binding)')<build.rindex('for mapping in mirror_checks:verify_mirror_bytes(mapping)'),
 'mirror-owner-roots-excluded-for-output-metadata':"safe(m['owner']) for m in mirror_checks" in build,
 'review-percentage-native-approval-not-created':"'nativeApproval':False" in build and "'formalPercentage':None" in build,
}
assert all(source_checks.values())
assert len(tests)==30,len(tests)
assert sha(SOURCE.read_bytes())==EXPECTED and sha(OLD.read_bytes())==OLD_SHA and sha(RENDERER.read_bytes())==RENDER_SHA and sha(guard.read_bytes())=='8be4c01b30a73eade999d78a039ba46911167882140f37c028c051716fc7fa6f'
record={'schema':'spec-agent-binding7-mirror-independent-targeted-audit/1','createdUtc':datetime.now(timezone.utc).isoformat(),
 'scope':'AST_FUNCTIONS_ONLY_SYNTHETIC_MIRROR_METADATA_AND_VIRTUAL_FS','status':'CODE_AND_TARGETED_SYNTHETIC_PASS_ACTUAL_BINDING_PENDING',
 'helper':{'path':str(SOURCE),'sha256':EXPECTED},'base6':{'path':str(OLD),'sha256':OLD_SHA},'renderer6':{'path':str(RENDERER),'sha256':RENDER_SHA},
 'tests':tests,'targetedCaseCount':len(tests),'staticSourceChecks':source_checks,'staticSourceCheckCount':len(source_checks),
 'baseExistingMetadataGuardsExactAfterRemovingOneMirrorCall':True,'unchangedExistingFunctions':unchanged,
 'mirrorFieldsCount':15,'independentOwnerKeyAlgorithm':'UTF8 docID/NUL/collectionSHA/NUL/renderpath/NUL/canonicalpath then SHA256',
 'virtualBytesFixtureOnly':True,'virtualSourceByteReadsOnly':True,'allSourceAndGuardBytesBeforeAfterUnchanged':True,
 'helperImported':False,'helperBuildExecuted':False,'rendererImported':False,'rendererExecuted':False,
 'actualInputRead':False,'actualOldOutputRead':False,'actualCapsuleRead':False,'actualBusinessRead':False,
 'actualCollectionRead':False,'actualRenderRecordsRead':False,'actualMarkdownRead':False,'actualPNGRead':False,'actualHTMLRead':False,
 'actualJobRead':False,'actualBindingWritten':False,'providerExecuted':False,'authoringExecuted':False,'markerExecuted':False,
 'semanticApproval':False,'formalQualityAssessed':False,'stateApproval':False,'wholeApproval':False,'adoption':False,'published':False,
 'reviewer':'/root/delivery_tools/registration_pdf_qa',
 'limits':['Standalone mirror_model is checked with valid surrounding fixture fields; it is used together with unchanged base6 metadata guards, not a substitute for them.',
           'Actual renderer/collection/runtime/mirror/Markdown/manifest records and source quality were not read or qualified.',
           'Virtual lstat/iterator/hash/bytes tests do not prove physical Windows paths, race exclusion, or actual pre/post binding I/O.',
           'No huge old suite or full frozen-runtime inventory scan was run; unchanged old field guards were compared as AST only.']}
target=A/'binding-r07-mirror-independent-targeted-probes-r01.json'
with target.open('x',encoding='utf-8') as h:json.dump(record,h,ensure_ascii=False,indent=2);h.write('\n')
print(json.dumps({'path':str(target),'sha256':sha(target.read_bytes()),'targetedCases':len(tests),'staticChecks':len(source_checks)},ensure_ascii=False))
