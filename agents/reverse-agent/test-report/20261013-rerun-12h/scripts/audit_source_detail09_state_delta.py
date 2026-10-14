"""Independent technical AST delta and synthetic approval probes; no provider/main."""
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import ast
import copy
import hashlib
import json

report=Path(__file__).resolve().parents[1]
old=report/'source-pilot/prepare_state_projection_basic08_v6.py'
new=report/'source-pilot/prepare_state_projection_detail09_v6.py'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected={old:'ae29ed7f6fe51ef80d8e7b54afe5b5d6345e649c44a1820bb2c69278ed5f3b06',
          new:'d280a85cb33ee00697180b45609f8a4653e98415f1173fe790692efdf511b9b8'}
assert all(sha(p)==d for p,d in expected.items())
trees={p:ast.parse(p.read_text(encoding='utf-8')) for p in expected}
defs=lambda tree:{n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
dump=lambda n:ast.dump(n,include_attributes=False)
od,nd=defs(trees[old]),defs(trees[new])
assert set(od)==set(nd)
assert all(dump(nd[n])==dump(od[n]) for n in nd if n!='canonical_path')
def assignments(tree,names):
    return [n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in names for t in n.targets)]
assert [dump(n) for n in assignments(trees[old],{'schema','ref_schema','location_schema','task','critical_module_names'})] == [dump(n) for n in assignments(trees[new],{'schema','ref_schema','location_schema','task','critical_module_names'})]
namespace={'Path':Path,'hashlib':hashlib,'json':json,'capsule':SimpleNamespace(safe_path=lambda p:Path(p))}
nodes=[nd[n] for n in ('canonical_path','validate_approved_review','validate_transport_schema','validate_projection_state_fields')]
exec(compile(ast.Module(body=nodes,type_ignores=[]),'<definitions-only>','exec'),namespace)
out=report/'source-audit/state-detail09-v6-independent'
out.mkdir(exist_ok=False)
fixtures=out/'synthetic'
fixtures.mkdir()
cases=[]
def probe(name,fn,accept=True):
    try:
        fn();actual=True;error=None
    except Exception as exc:
        actual=False;error=type(exc).__name__+': '+str(exc)
    cases.append({'case':name,'expectedAccept':accept,'actualAccept':actual,'pass':actual==accept,'error':error})
def canonical(relative):
    path=fixtures/relative
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text('synthetic',encoding='utf-8')
    return namespace['canonical_path'](path,fixtures)
for relative,accept in [('search-detail-09/詳細仕様書/CSharp_ASPNET/01_学生検索画面.md',True),
    ('search-basic-08/基本設計書/01_学生検索画面.md',False),
    ('search-detail-09/詳細仕様書/CSharp_ASPNET/02_学生登録画面.md',False),
    ('assisted-09/詳細仕様書/CSharp_ASPNET/01_学生検索画面.md',False)]:
    probe('role-path-'+relative,lambda r=relative:canonical(r),accept)
parent='a'*64;cap='b'*64;path='C:/synthetic/detail09.md'
rv={'approved':True,'findings':[]}
h={'schema':'reverse-ai-review-handoff/1','approved':True,'reviewScope':'text-source-and-structure',
   'referenceMode':'source-only','snapshot':{'mode':'source-only','manifestSha256':cap},
   'documentFile':path,'documentSha256':parent}
def approval(kind):
    handoff=copy.deepcopy(h);review=copy.deepcopy(rv)
    if kind=='mode':handoff['referenceMode']='training-assisted'
    if kind=='parent':handoff['documentSha256']='c'*64
    if kind=='path':handoff['documentFile']='C:/synthetic/other.md'
    if kind=='snapshot':handoff['snapshot']['manifestSha256']='c'*64
    if kind=='unapproved':review['approved']=False
    if kind=='findings':review['findings']=[{'synthetic':True}]
    rb=json.dumps(review).encode();rh=hashlib.sha256(rb).hexdigest()
    handoff['reviewSha256']=rh
    hb=json.dumps(handoff).encode();hh=hashlib.sha256(hb).hexdigest()
    if kind=='review-drift':rb+=b' '
    if kind=='handoff-drift':hb+=b' '
    return namespace['validate_approved_review'](hb,rb,expected_handoff_sha256=hh,
        expected_review_sha256=rh,document_file=path,document_sha256=parent,snapshot_sha256=cap)
for kind in ('correct','mode','parent','path','snapshot','unapproved','findings','review-drift','handoff-drift'):
    probe('approval-'+kind,lambda k=kind:approval(k),kind=='correct')
probe('typed-schema',lambda:namespace['validate_transport_schema']({'type':'string','enum':['x']}))
probe('untyped-schema-rejected',lambda:namespace['validate_transport_schema']({'enum':['x']}),False)
for flag,html,reason,accept in ((False,'<p>synthetic</p>','',True),(True,'','reason',True),
                               (True,'<p>x</p>','reason',False),(True,'','',False),(False,'','',False)):
    probe('canonical-gap-'+str((flag,html,reason)),lambda f=flag,h=html,r=reason:
        namespace['validate_projection_state_fields']({'requiresCanonicalRevision':f,'html':h,'canonicalRevisionReason':r}),accept)
assert all(c['pass'] for c in cases) and all(sha(p)==d for p,d in expected.items())
result={'schema':'reverse-agent-independent-state-helper-delta/1','createdUtc':datetime.now(timezone.utc).isoformat(),
    'status':'PASS_MECHANICAL_DELTA_ONLY','helperHashes':{str(p):d for p,d in expected.items()},
    'unchangedDefinitionNames':[n for n in nd if n!='canonical_path'],
    'schemaAndTaskAstUnchanged':True,'cases':cases,'matches':len(cases),
    'inheritedGuardEvidence':'delivery/state-helper-independent-basic08-v6/review.json',
    'inheritedGuardEvidenceSha256':sha(report/'delivery/state-helper-independent-basic08-v6/review.json'),
    'providerInvocations':0,'topLevelInvocations':0,'originalSourceSpecEvalManuscriptRead':False,
    'businessMeaningApproved':False,'formalQualityApproved':False,
    'limitations':['Synthetic metadata and approved helper code only. Main preflight, real provider transport, source meaning, and native state review remain separate.']}
target=out/'review.json'
target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'cases':len(cases),'matches':len(cases),'sha256':sha(target),'report':str(target)}))
