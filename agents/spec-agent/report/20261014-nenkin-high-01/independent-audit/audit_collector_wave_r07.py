"""New wave gate AST only, toy metadata. No production import/main/collection or prose read."""
from pathlib import Path
from datetime import datetime,timezone
import ast,copy,hashlib,json,re,types
HERE=Path(__file__).resolve().parent
RUN=Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/.tmp/20261014-nenkin-high-01')
TARGET=RUN/'collect_reviewed_r07.py'
EXPECTED='ee8419432a9b553c04ba757a2b188c86614ae230d980c5822ac8d8fe17a40a50'
raw=TARGET.read_bytes();assert hashlib.sha256(raw).hexdigest()==EXPECTED
prior=TARGET.with_name('collect_reviewed_r06.py');oldtree=ast.parse(prior.read_bytes());tree=ast.parse(raw)
assert hashlib.sha256(prior.read_bytes()).hexdigest()=='441618b3934e11ebd7180108c5dfa82af5cace2b454ea2cfc73324dca5b28723'
of={n.name:ast.dump(n,include_attributes=False) for n in oldtree.body if isinstance(n,ast.FunctionDef)};nf={n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.FunctionDef)}
assert set(of)==set(nf) and {k for k in of if of[k]!=nf[k]}=={'main'}
assert [ast.dump(n,include_attributes=False) for n in oldtree.body if not isinstance(n,ast.FunctionDef)]==[ast.dump(n,include_attributes=False) for n in tree.body if not isinstance(n,ast.FunctionDef)]
main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
loop=next(n for n in main.body if isinstance(n,ast.For) and ast.unparse(n.target)=='item')
start=next(i for i,n in enumerate(loop.body) if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=='generation')
end=next(i for i,n in enumerate(loop.body) if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=='review_handoff')
segment=loop.body[start:end]
ROOT=HERE/'collector-wave-r07-toy';ROOT.mkdir(exist_ok=False)
def safe(p):
 p=Path(p).absolute()
 for q in (p,*p.parents):
  if q.is_symlink() or q.exists() and getattr(q.lstat(),'st_file_attributes',0)&0x400:raise ValueError('Linked path before read')
 return p.resolve()
def sha(p):return hashlib.sha256(safe(p).read_bytes()).hexdigest()
def load(p):return json.loads(safe(p).read_bytes().decode('utf-8'))
def save(p,v):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((json.dumps(v,sort_keys=True)+'\n').encode())
def require(ok,message):
 if not ok:raise ValueError(message)
checks=[]
def fixture(i):
 r=ROOT/str(i);run=r/'run';report=r/'report';wave=run/'jobs/author-wave-01';gen=wave/'toy-folder'
 sourcepin=report/'text-pins/author-wave-01/toy-folder/text-reviewed-pin.json'
 definition={'id':'TOY','path':'detail/toy.md','kind':'detailed-specification'}
 state={'manifestSha256':'a'*64,'mode':'source-only'};args=types.SimpleNamespace(plan_sha256='b'*64);context='c'*64
 driver=run/'toy-driver.py';driver.parent.mkdir(parents=True);driver.write_bytes(b'# toy driver metadata only\n')
 driversha=sha(driver);grant=report/'grant.json';save(grant,{'approved':True,'driverSha256':driversha,'capsuleManifestSha256':'a'*64,'executionContextSha256':context})
 grantsha=sha(grant);input={'snapshot':state,'planSha256':args.plan_sha256,'executionContextSha256':context,'grantSha256':grantsha,'grant':str(grant),'pinnedFiles':{str(grant):grantsha,str(driver):driversha}}
 prep=report/'author-preparation/author-wave-01/preparation.json';save(prep,{'schema':'spec-agent-author-wave-preparation/1','wave':'author-wave-01','input':input,'providerStarted':False,'documents':['TOY'],'helper':str(driver),'helperSha256':driversha})
 prep_sha=sha(prep);before={'preparationSha256':prep_sha,'input':input};after={'status':'UNCHANGED',**copy.deepcopy(before)}
 save(wave/'author-inputs-before.json',before);save(wave/'author-inputs-after.json',after)
 original={'activationGrantSha256':grantsha,'waveIntegrityVerificationRequiredForCollection':True,'waveVerification':{'before':str((wave/'author-inputs-before.json').resolve()),'beforeSha256':sha(wave/'author-inputs-before.json'),'after':str((wave/'author-inputs-after.json').resolve()),'result':str((wave/'author-wave-result.json').resolve())}}
 save(sourcepin,original)
 result={'schema':'spec-agent-author-document-result/1','status':'TEXT_REVIEW_APPROVED','documentId':'TOY','path':definition['path'],'kind':definition['kind'],'capsule':state,'planSha256':args.plan_sha256,'executionContextSha256':context,'textPin':{'path':str(sourcepin.resolve()),'sha256':sha(sourcepin)}}
 save(gen/'author-document-result.json',result)
 completed={'status':'TEXT_REVIEW_APPROVED','waveIntegrityVerified':True,'input':copy.deepcopy(input),'preparation':str(prep),'preparationSha256':prep_sha,'inputsAfter':str((wave/'author-inputs-after.json').resolve()),'inputsAfterSha256':sha(wave/'author-inputs-after.json'),'documents':[copy.deepcopy(result)]}
 save(wave/'author-wave-result.json',completed)
 return {'run':run,'report':report,'wave':wave,'gen':gen,'sourcepin':sourcepin,'definition':definition,'state':state,'args':args,'context':context,'grant':grant,'driver':driver,'prep':prep,'original':original,'before':before,'after':after,'result':result,'completed':completed}
def gate(f):
 pins={}
 def pin(p,expected=None):
  p=safe(p);h=sha(p);require(expected is None or h==expected,'Wrong pin');require(str(p) not in pins or pins[str(p)]==h,'Artifact drift');pins[str(p)]=h;return p
 def inside(value,root):
  value,root=safe(value),safe(root);require(value!=root and value.is_relative_to(root),'Outside selected root');return value
 ns={'REPORT':f['report'],'inside':inside,'RUN':f['run'],'safe':safe,'sha':sha,'load':load,'pin':pin,'require':require,'re':re,'draft_file':f['gen']/'draft-result.json','source_pin':f['sourcepin'].resolve(),'definition':f['definition'],'state':f['state'],'args':f['args'],'guard':types.SimpleNamespace(CONTEXT_SHA=f['context'],SNAPSHOT_SHA='a'*64,RECEIPT=f['report']/'receipt.json'),'original':f['original']}
 exec(compile(ast.Module(body=segment,type_ignores=[]),str(TARGET),'exec'),ns)
 return pins
def one(name,mut=None,reject=True,probe=False):
 f=fixture(len(checks))
 if mut:mut(f)
 try:gate(f);observed='ACCEPTED';error=None
 except Exception as e:observed='REJECTED';error=type(e).__name__+': '+str(e)
 checks.append({'case':name,'expected':'REJECTED' if reject else 'ACCEPTED','observed':observed,'match':(observed=='REJECTED')==reject,'exploratory':probe,'error':error})
def modify(f,key,change):
 mapping={'after':f['wave']/'author-inputs-after.json','before':f['wave']/'author-inputs-before.json','completed':f['wave']/'author-wave-result.json','result':f['gen']/'author-document-result.json'}
 v=copy.deepcopy(f[key]);change(v);save(mapping[key],v)
one('new_wave_gate_positive',reject=False)
one('failed_wave_after',lambda f:modify(f,'after',lambda v:v.update(status='NOT_VERIFIED')))
one('missing_wave_after',lambda f:(f['wave']/'author-inputs-after.json').unlink())
one('missing_completed_wave_result',lambda f:(f['wave']/'author-wave-result.json').unlink())
one('missing_author_document_result',lambda f:(f['gen']/'author-document-result.json').unlink())
for k,v in [('status','FAILED'),('schema','wrong'),('documentId','OTHER'),('path','elsewhere.md'),('kind','analysis-report'),('capsule',{}),('planSha256','0'*64),('executionContextSha256','0'*64)]:one('author_'+k,lambda f,k=k,v=v:modify(f,'result',lambda x:x.update({k:v})))
one('author_different_pin_sha',lambda f:modify(f,'result',lambda v:v['textPin'].update(sha256='0'*64)))
one('author_different_pin_path',lambda f:modify(f,'result',lambda v:v['textPin'].update(path=str(f['report']/'other.json'))))
one('after_input_drift',lambda f:modify(f,'after',lambda v:v['input'].update(executionContextSha256='0'*64)))
one('after_preparation_sha_drift',lambda f:modify(f,'after',lambda v:v.update(preparationSha256='0'*64)))
one('text_pin_wave_requirement_false',lambda f:f['original'].update(waveIntegrityVerificationRequiredForCollection=False))
one('text_pin_before_sha_drift',lambda f:f['original']['waveVerification'].update(beforeSha256='0'*64))
one('text_pin_after_path_drift',lambda f:f['original']['waveVerification'].update(after=str(f['report']/'other.json')))
for k,v in [('waveIntegrityVerified',False),('input',{}),('preparationSha256','0'*64),('inputsAfterSha256','0'*64),('inputsAfter','other.json')]:one('completed_'+k,lambda f,k=k,v=v:modify(f,'completed',lambda x:x.update({k:v})))
one('duplicate_matching_document',lambda f:modify(f,'completed',lambda v:v['documents'].append(copy.deepcopy(v['documents'][0]))))
one('missing_matching_document',lambda f:modify(f,'completed',lambda v:v.update(documents=[])))
one('different_matching_document_result',lambda f:modify(f,'completed',lambda v:v['documents'][0].update(status='REQUIRES_AI_REVISION')))
one('completed_input_grant_drift',lambda f:modify(f,'completed',lambda v:v['input'].update(grantSha256='0'*64)))
one('actual_preparation_file_drift_after_wave',lambda f:f['prep'].write_bytes(b'changed preparation'),probe=False)
one('actual_grant_file_drift_after_wave',lambda f:f['grant'].write_bytes(b'changed grant'),probe=False)
one('completed_preparation_path_wrong',lambda f:modify(f,'completed',lambda v:v.update(preparation=str(f['report']/'other.json'))),probe=False)
one('actual_pinned_driver_byte_drift',lambda f:f['driver'].write_bytes(b'changed driver'))
one('actual_pinned_driver_missing',lambda f:f['driver'].unlink())
nonexploratory=[c for c in checks if not c['exploratory']]
assert all(c['match'] for c in nonexploratory)
# Renderer delta is pointers only; exact renderer module guard body remains unchanged.
r2=RUN/'render_reviewed_r02.py';r4=RUN/'render_reviewed_r04.py'
assert hashlib.sha256(r2.read_bytes()).hexdigest()=='03d4f8badac3a218a315e8bb6507aa3062039b1dda0309871a65c762471eefd4'
assert hashlib.sha256(r4.read_bytes()).hexdigest()=='888db1128cc0f5dc0ab942e18fb4476e4f0ce79cf1aa2d1e3bd75324952571be'
def functions(p):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_bytes()).body if isinstance(n,ast.FunctionDef)}
assert functions(r2)==functions(r4)
def assigns(p):return {tuple(ast.unparse(t) for t in n.targets):ast.dump(n.value,include_attributes=False) for n in ast.parse(p.read_bytes()).body if isinstance(n,ast.Assign)}
x,y=assigns(r2),assigns(r4);assert set(x)==set(y) and {k for k in x if x[k]!=y[k]}=={('HELPER',),('HELPER_SHA',)}
assert TARGET.read_bytes()==raw
report={'schema':'collector-wave-independent-delta-audit/1','createdUtc':datetime.now(timezone.utc).isoformat(),'helper':str(TARGET),'helperSha256':EXPECTED,'status':'PASS_WAVE_AND_ACTUAL_PREPARATION_BINDING_DELTA','controlsMatched':sum(c['match'] for c in nonexploratory),'controlCount':len(nonexploratory),'cases':checks,'rendererHelperSha256':hashlib.sha256(r4.read_bytes()).hexdigest(),'rendererAllFunctionAstsUnchanged':True,'rendererOnlyHelperPointerChanged':True,'actualProductionMainOrCollectionOrProviderExecuted':False,'productionSourceCapsulePlanDraftProseOrExpectedRead':False,'frozenMutation':False,'limitations':['Only the newly added collector wave gate statements were executed against synthetic metadata. Old r04 fullflow validations are inherited evidence, not rerun here.','The three external-binding probes accepted by r06 are rejected by r07, together with actual pinned-driver byte drift/missing-file controls.','This is a scoped additional-gate test, not an actual collection or full activation/schema/source-read validation.','Formal/semantic/native qualification remains unassessed.']}
target=HERE/'collector-wave-code-review-r07.json'
with target.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
print(json.dumps({'report':str(target),'sha256':sha(target),'controls':len(nonexploratory),'matched':sum(c['match'] for c in nonexploratory),'externalBindingRegressionRejectCount':sum(c['observed']=='REJECTED' for c in checks if c['case'] in ['actual_preparation_file_drift_after_wave','actual_grant_file_drift_after_wave','completed_preparation_path_wrong'])}))
