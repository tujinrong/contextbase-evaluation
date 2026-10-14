"""Independent AST and toy metadata only; no production material reads or main."""
from __future__ import annotations
import ast, copy, hashlib, json, stat, types
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parents[3]/'.tmp/20261013-rerun-12h/training-assisted'
V2=BASE/'review_search_basic_fidelity_v2.py'
V3=BASE/'review_search_basic_fidelity_v3.py'
EXPECTED='45ad4c9e8cb3702b24a85afd7cef2f10e140ecf4654897e5130104ef29539edd'
def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False),encoding='utf-8')
def safe(p):
    p=Path(p).absolute()
    for v in [p,*p.parents]:
        if v.exists() and (v.is_symlink() or getattr(v.lstat(),'st_file_attributes',0)&0x400):
            raise ValueError('Linked toy path')
    return p.resolve()
def under(p,root,file=False):
    p=safe(p);p.relative_to(safe(root))
    if file and not p.is_file():raise ValueError('Missing toy file')
    return p

assert digest(V3)==EXPECTED
v2=ast.parse(V2.read_text(encoding='utf-8-sig'))
v3=ast.parse(V3.read_text(encoding='utf-8-sig'))
f2={n.name:n for n in v2.body if isinstance(n,ast.FunctionDef)}
f3={n.name:n for n in v3.body if isinstance(n,ast.FunctionDef)}
stable=[n for n in f2 if n!='main']
stable_ok=all(ast.dump(f2[n],include_attributes=False)==ast.dump(f3[n],include_attributes=False) for n in stable)
schema2=[n for n in v2.body if isinstance(n,(ast.Assign,ast.AugAssign)) and any(isinstance(t,ast.Name) and t.id in {'QUOTED_REFERENCE','UNIT','SCHEMA'} for t in getattr(n,'targets',[getattr(n,'target',None)]))]
schema3=[n for n in v3.body if isinstance(n,(ast.Assign,ast.AugAssign)) and any(isinstance(t,ast.Name) and t.id in {'QUOTED_REFERENCE','UNIT','SCHEMA'} for t in getattr(n,'targets',[getattr(n,'target',None)]))]
assert stable_ok and ast.dump(ast.Module(schema2,[]))==ast.dump(ast.Module(schema3,[]))
assert set(f3)-set(f2)=={'bind_previous_raw'}
cases=[]
def record(name,passed,error=None,**extra):
    cases.append({'name':name,'passed':passed,'error':error,**extra})
record('existing-prepare-coverage-sha-load-AST-identical',stable_ok)
record('schema-UNIT-AST-identical',True)
record('one-added-pure-binding-definition',True)

SCHEMA={'type':'object','additionalProperties':False,'properties':{'documentId':{'type':'string'},'approved':{'type':'boolean'},'findings':{'type':'array'}},'required':['documentId','approved','findings']}
rawnode=copy.deepcopy(f3['bind_previous_raw'])
PROD_RESULT='1844bacb820b6cfc135e59202e52286ce85cd0a09bbf9c8a98520789ab95ba11'
PROD_DIAG='faaa28fcd085a4413aaa3c96158ec5f872c094a21ad05e1db1d721860f798ec4'
PROD_V2='ac28f04d4026fec974619f8394fe4997dcea91c6f9c3b0efa3c8926183abda15'
required=['input-pins.json','input-after.json','independent-review-snapshot-before.json','independent-review-snapshot-after.json']+['independent-review/'+n for n in ['answer.txt','result.json','schema.json','prompt.txt','events.jsonl','stderr.log']]

def run(name,mutate=None,expected=True,repin_mutated_fixed=False,after_hook=None):
    root=ROOT/'f'/f'{len(cases):02d}'; base=root/'base';report=root/'report'
    previous=base/'jobs/search-basic-r04-fidelity-r02'
    parent=root/'parent.md';parent.parent.mkdir(parents=True,exist_ok=True);parent.write_text('toy canonical',encoding='utf-8')
    v2toy=base/'review_search_basic_fidelity_v2.py';v2toy.parent.mkdir(parents=True,exist_ok=True);v2toy.write_text('# toy v2',encoding='utf-8')
    capsule={'mode':'toy-assisted','manifestSha256':'toy-cap'}
    metadata={'documentId':'toy-document','parentDocumentSha256':'toy-parent','documentFile':str(parent),'capsule':capsule,'mode':'toy-assisted','scope':'toy-scope','materialClosure':['toy/raw.txt'],'completedAnalysisCheckpointSha256':'toy-checkpoint','pinnedFiles':{str(parent):digest(parent)}}
    old=copy.deepcopy(metadata)
    answer={'documentId':'toy-document','approved':False,'findings':[]}
    result={'exit_code':0,'metadata':{'status':'passed'},'answer':answer}
    diag={'status':'RAW_AI_REVIEW_NOT_ACCEPTED','parentDocumentSha256':'toy-parent','rawAnswerModified':False,'judgmentsMechanicallyRepaired':False}
    data={'input-pins.json':old,'input-after.json':{'status':'UNCHANGED','pins':old},'independent-review/result.json':result,'independent-review/answer.txt':answer,'independent-review/schema.json':SCHEMA,'independent-review-snapshot-before.json':capsule,'independent-review-snapshot-after.json':capsule}
    for relative in required:put(previous/relative,data.get(relative,{'toyArtifact':relative}))
    diagnostic=report/'search-basic-r04-fidelity-r02-validation-failure.json';put(diagnostic,diag)
    expected_result=digest(previous/'independent-review/result.json');expected_diag=digest(diagnostic);expected_v2=digest(v2toy)
    if mutate:mutate(previous,diagnostic,metadata,parent,v2toy)
    if repin_mutated_fixed:
        expected_result=digest(previous/'independent-review/result.json');expected_diag=digest(diagnostic)
    pins_before={str(p):digest(p) for p in root.rglob('*') if p.is_file()}
    calls=[]
    def unchanged(m):
        calls.append('assert')
        for p,s in m['pinnedFiles'].items():
            if digest(safe(p))!=s:raise ValueError('Toy pinned input drift')
        if after_hook:after_hook(m,previous)
    state=types.SimpleNamespace(BASE=base,REPORT=report,MODE='toy-assisted',SNAPSHOT=root/'snapshot',under=under,assert_unchanged=unchanged,
        capsule=types.SimpleNamespace(safe_path=safe,verify=lambda p:(calls.append('verify') or capsule)),
        workflow=types.SimpleNamespace(references_valid=lambda a,m:calls.append('references')))
    class Replace(ast.NodeTransformer):
        def visit_Constant(self,n):
            if isinstance(n.value,str):
                replacement={PROD_RESULT:expected_result,PROD_DIAG:expected_diag,PROD_V2:expected_v2}.get(n.value)
                if replacement:return ast.copy_location(ast.Constant(replacement),n)
            return n
    node=Replace().visit(copy.deepcopy(rawnode)); ast.fix_missing_locations(node)
    ns={'state':state,'Path':Path,'sha':lambda p:digest(safe(p)),'load':lambda p:json.loads(safe(p).read_text(encoding='utf-8-sig')),
        'DOCUMENT_ID':'toy-document','PARENT_SHA':'toy-parent','SCOPE':'toy-scope','SCHEMA':SCHEMA,'Draft202012Validator':Draft202012Validator}
    exec(compile(ast.Module([node],[]),str(V3),'exec'),ns)
    accepted=False;error=None;checks=[]
    try:
        a,d=ns['bind_previous_raw'](metadata);accepted=True
        checks=[a==answer,d==diag,len(metadata['pinnedFiles'])==13,metadata['previousRawReview']['requiredArtifactCount']==10,
            metadata['previousRawReview']['rawReviewNotAccepted'] is True,metadata['previousRawReview']['oldApprovalReused'] is False,
            calls.count('assert')==2,calls.count('references')==1,calls.count('verify')==1,
            all(str(previous/r) in metadata['pinnedFiles'] for r in required)]
    except Exception as e:error=f'{type(e).__name__}: {e}'
    pins_after={str(p):digest(p) for p in root.rglob('*') if p.is_file()}
    ok=(accepted==expected) and (all(checks) if expected else True) and pins_before==pins_after
    record(name,ok,error,accepted=accepted,checks=checks,repinnedToyFixedDigest=repin_mutated_fixed,artifactBytesUnchanged=pins_before==pins_after)

def edit(rel,key,val):
    def mutate(p,d,m,parent,v2):
        path=d if rel=='diagnostic' else p/rel
        obj=json.loads(path.read_text(encoding='utf-8'))
        target=obj
        parts=key.split('.')
        for n in parts[:-1]:target=target[n]
        target[parts[-1]]=val;put(path,obj)
    return mutate

run('positive-ten-artifacts-plus-diagnostic-v2-pins')
run('fixed-result-byte-drift',edit('independent-review/result.json','exit_code',1),False)
run('fixed-diagnostic-byte-drift',edit('diagnostic','status','changed'),False)
for field,val in [('documentId','wrong'),('parentDocumentSha256','wrong'),('capsule',{'manifestSha256':'wrong'}),('mode','wrong'),('scope','wrong'),('materialClosure',[]),('documentFile',str(ROOT/'outside-toy.md')),('completedAnalysisCheckpointSha256','wrong')]:
    run('old-'+field,edit('input-pins.json',field,val),False)
run('after-status',edit('input-after.json','status','CHANGED'),False)
run('after-pins',edit('input-after.json','pins.mode','wrong'),False)
run('result-exit',edit('independent-review/result.json','exit_code',1),False,True)
run('result-status',edit('independent-review/result.json','metadata.status','failed'),False,True)
run('result-document',edit('independent-review/result.json','answer.documentId','wrong'),False,True)
run('answer-raw-disagreement',edit('independent-review/answer.txt','approved',True),False)
run('schema-disagreement',edit('independent-review/schema.json','type','array'),False)
for field,val in [('status','accepted'),('parentDocumentSha256','wrong'),('rawAnswerModified',True),('rawAnswerModified',0),('judgmentsMechanicallyRepaired',True),('judgmentsMechanicallyRepaired',0)]:
    run('diagnostic-'+field+'-'+str(val),edit('diagnostic',field,val),False,True)
for relative in required:
    run('missing-'+relative.replace('/','-'),lambda p,d,m,par,v2,r=relative:(p/r).unlink(),False)
run('v2-code-byte-drift',lambda p,d,m,par,v2:v2.write_text('changed',encoding='utf-8'),False)
run('old-current-parent-byte-drift',lambda p,d,m,par,v2:par.write_text('changed',encoding='utf-8'),False)
run('schema-type-in-raw',edit('independent-review/result.json','answer.approved','yes'),False,True)

# Actual helper/code only: fresh job ordering and provider boundary remain unchanged.
main=f3['main']; calls=[n for n in ast.walk(main) if isinstance(n,ast.Call)]
names=[ast.unparse(n.func) for n in calls]
lines={name:min(n.lineno for n in calls if ast.unparse(n.func)==name) for name in ['prepare','bind_previous_raw','job.mkdir','state.workflow._bound_job']}
record('bind-before-fresh-job-and-provider',lines['prepare']<lines['bind_previous_raw']<lines['job.mkdir']<lines['state.workflow._bound_job'])
record('bounded-provider-2400-unchanged',any(ast.unparse(n.func)=='state.workflow._bound_job' and any(isinstance(a,ast.Constant) and a.value==2400 for a in n.args) for n in calls))
record('unchanged-postresponse-validation-gates',all(n in names for n in ['Draft202012Validator(SCHEMA).validate','state.workflow.references_valid','validate_coverage','state.assert_unchanged']))
report={'scope':'CODE_AST_AND_OWN_SYNTHETIC_METADATA_ONLY','helperSha256':digest(V3),'previousHelperSha256':digest(V2),
    'cases':cases,'passed':sum(c['passed'] for c in cases),'total':len(cases),'productionMaterialReads':0,'productionRawOrDiagnosticReads':0,'provider':0,'main':0,
    'toyOnlyTransform':'Only fixed digest literals replaced with real own fixture digests; deeper binding-negative controls intentionally re-pin toy digests.',
    'schemaScope':'Real Draft202012Validator on a strict toy schema. Production v2/v3 schema AST identical; no production answer read.',
    'stateAssertScope':'Toy pinned-file validator and capsule/references call spies. Existing production guards unchanged by AST.',
    'semanticReadClaimsScope':'Preserves inherited raw read claims explicitly; new full material reread neither executed nor claimed.',
    'codePinsUnchanged':digest(V3)==EXPECTED,'findings':[]}
put(ROOT/'review.json',report)
print(json.dumps({k:report[k] for k in ['helperSha256','passed','total','codePinsUnchanged','findings']}))
if report['passed']!=report['total']:raise SystemExit(1)
