"""AST-extracted adapter plus synthetic files/modules, never production main."""
from pathlib import Path
from datetime import datetime,timezone
import ast,copy,hashlib,importlib,json,re,sys,tempfile,types
HERE=Path(__file__).resolve().parent
HELPER=HERE.parents[2]/'.tmp/20261014-nenkin-high-01/review_plan_with_scope_r01.py'
RAW=HELPER.read_bytes();H=hashlib.sha256(RAW).hexdigest()
assert H=='6cb4ca230efe445912a1ca6daa28148edfa764d3bd300d2cb0fae91c247ea2e5'
TREE=ast.parse(RAW);DEFS=[x for x in TREE.body if isinstance(x,ast.FunctionDef) and x.name!='main']
CASE=[]
def check(name,ok):
 assert ok,name
 CASE.append({'name':name,'passed':True})
def rejects(name,fn):
 try:fn()
 except (ValueError,FileExistsError,KeyError):check(name,True)
 else:raise AssertionError(name+' accepted')
check('main guarded and no production top-level run',isinstance(TREE.body[-1],ast.If))
check('core validation schema and pin calls retained',b'plan_review._validate(answer,value,manifest)' in RAW and b'plan_review._assert_pin(SNAPSHOT,definition,plan_bytes,handoff_sha)' in RAW and b'plan_review.PLAN_REVIEW' in RAW)
check('no core or frozen prompt monkeypatch assignment',not any(isinstance(x,ast.Attribute) and isinstance(x.ctx,ast.Store) and isinstance(x.value,ast.Name) and x.value.id in {'capsule','workflow','plan_review','prompts'} for x in ast.walk(TREE)))
check('full context decoded without semantic reconstruction',b"context_bytes.decode('utf-8')" in RAW)
check('full plan decoded without semantic reconstruction',b"plan_bytes.decode('utf-8')" in RAW)
check('raw AI answer copy uses original bytes exclusive',b"with verified.open('xb') as handle:handle.write(original_bytes)" in RAW)
check('scope material forbidden as raw references in task',b'sourcePathsRead' in RAW and b'basis=plan-structure' in RAW)
saved_modules={k:sys.modules.get(k) for k in ('contextbase','contextbase.ai')}
try:
 with tempfile.TemporaryDirectory(prefix='scope-wrapper-toy-',dir=HERE) as td:
  root=Path(td);run=root/'run';report=root/'report';snapshot=run/'snapshot';runtime=root/'runtime';runtime.mkdir();snapshot.mkdir(parents=True)
  names=['contextbase','contextbase.__main__','contextbase.ai','contextbase.ai.__main__','contextbase.ai.workflow','contextbase.ai.provider','contextbase.ai.prompts','contextbase.ai.schemas','contextbase.ai.validation','contextbase.ai.iteration','contextbase.ai.document_contract','docsite','specgen']
  critical=('contextbase.ai.capsule','contextbase.ai.workflow','contextbase.ai.provider','contextbase.ai.prompts','contextbase.ai.schemas','contextbase.ai.validation','contextbase.ai.plan_review')
  paths={n:runtime/(n.replace('.','/')+('/__init__.py' if n in {'contextbase','contextbase.ai','docsite','specgen'} else '.py')) for n in names}
  for n in critical:paths.setdefault(n,runtime/(n.replace('.','/')+'.py'))
  for p in paths.values():p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'# toy infrastructure, not imported as code\n')
  for i in range(128-len(paths)):(runtime/f'toy-{i:03}.py').write_bytes(str(i).encode())
  files={p.relative_to(runtime).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in runtime.rglob('*') if p.is_file()}
  receipt=root/'receipt.json';receipt.write_text(json.dumps({'destination':str(runtime),'files':files,'imports':{n:str(paths[n]) for n in names}}))
  context=run/'execution-context.json';ctx={'schema':'spec-agent-execution-context/1','agentRole':'AG-SPEC','projectId':'nenkin','primarySourceDirectory':'nenkin','dependencySourceDirectory':'n2framework','sourceOnly':True,'originalSpecificationsAuthorized':False,'evaluationExpectationsAuthorized':False,'originalProgramsAndDatabaseExecutionAuthorized':False,'toyExtra':'FULL_CONTEXT_MARKER'};context.write_text(json.dumps(ctx))
  capmanifest=snapshot/'manifest.json';capmanifest.write_text(json.dumps({'mode':'source-only','projectId':'nenkin'}))
  planfile=run/'jobs/plan-01/plan-verified.json';planfile.parent.mkdir(parents=True)
  plan={'systemSummary':'toy only','documents':[{'id':'TOY-001','path':'toy.md','title':'toy','kind':'common','sourcePaths':[],'responsibilities':['toy scope']}],'unresolved':[]};planfile.write_text(json.dumps(plan))
  handoff=planfile.parent/'plan-handoff.json';handoff.write_text(json.dumps({'origin':'toy'}))
  provider_calls=[];validate_calls=[];pin_calls=[]
  ai=types.ModuleType('contextbase.ai');package=types.ModuleType('contextbase');package.ai=ai
  sys.modules['contextbase']=package;sys.modules['contextbase.ai']=ai
  ns={'Path':Path,'datetime':datetime,'timezone':timezone,'argparse':None,'hashlib':hashlib,'json':json,'re':re,'sys':sys,'importlib':types.SimpleNamespace(import_module=lambda n:types.SimpleNamespace(__file__=str(paths[n]))),'RUN':run,'REPORT':report,'SNAPSHOT':snapshot,'SNAPSHOT_SHA':hashlib.sha256(capmanifest.read_bytes()).hexdigest(),'CONTEXT':context,'CONTEXT_SHA':hashlib.sha256(context.read_bytes()).hexdigest(),'RECEIPT':receipt,'RECEIPT_SHA':hashlib.sha256(receipt.read_bytes()).hexdigest(),'RUNTIME':runtime,'DEADLINE':'2099-01-01T00:00:00+00:00','CRITICAL':critical,'SCOPE_TASK':'scope only\n','__file__':str(HELPER)}
  exec(compile(ast.Module(body=DEFS,type_ignores=[]),str(HELPER),'exec'),ns)
  capsule=types.SimpleNamespace(safe_path=ns['safe'],sha256=ns['digest'],_load_json=ns['load'],verify=lambda p:{'mode':'source-only'},verification_state=lambda p:{'manifestSha256':ns['sha'](capmanifest),'mode':'source-only'})
  def write_json(p,v):
   p=ns['safe'](p);p.parent.mkdir(parents=True,exist_ok=True)
   with p.open('x',encoding='utf8') as f:json.dump(v,f)
  capsule.write_json=write_json
  class Definition(dict):pass
  def select(p,document_id):
   d=Definition(plan['documents'][0]);d.handoff_sha=ns['sha'](handoff);d.handoff={'origin':'toy'};return d
  answer={'approved':True,'toy':'untouched raw value'}
  def bound(snapshot_path,job,prompt,schema,timeout,state,deadline):
   provider_calls.append({'job':str(job),'prompt':prompt,'schema':schema})
   job.mkdir();(job/'answer.txt').write_bytes(b'{ "approved": true, "toy": "untouched raw value" }\n')
   return copy.deepcopy(answer)
  workflow=types.SimpleNamespace(_timeout=lambda t,d:t,_validate_plan=lambda p,m:None,select_document=select,_definition_state=lambda p,d:capsule.verification_state(p),_bound_job=bound)
  core=types.SimpleNamespace(REVIEW_TASK='CORE_REVIEW_TASK\n',PLAN_REVIEW={'type':'object','toy':True},_assert_pin=lambda *args:pin_calls.append(True),_validate=lambda *args:validate_calls.append(True))
  prompts=types.SimpleNamespace(BOUNDARY='BOUNDARY\n',QUALITY='QUALITY\n',FORMAT='FORMAT\n')
  ai.capsule=capsule;ai.workflow=workflow;ai.plan_review=core;ai.prompts=prompts
  original_import=ns['importlib'].import_module
  ns['importlib'].import_module=lambda n:core if n=='contextbase.ai.plan_review' and not n in paths else original_import(n)
  # Bootstrap uses mock modules with exact file locations and byte inventory.
  boot=ns['bootstrap']();check('128 toy files and thirteen exact import paths positive',boot['runtimeFileCount']==128 and len(boot['loadedImports'])==13 and len(boot['criticalModules'])==7)
  extra=runtime/'extra.py';extra.write_bytes(b'addition');rejects('runtime membership addition refused',ns['bootstrap']);extra.unlink()
  original=next(runtime.glob('toy-*.py'));data=original.read_bytes();original.write_bytes(b'drift');rejects('runtime byte drift refused',ns['bootstrap']);original.write_bytes(data)
  original.rename(original.with_suffix('.save'));rejects('runtime deletion/renaming refused',ns['bootstrap']);original.with_suffix('.save').rename(original)
  rb=receipt.read_bytes();receipt.write_bytes(rb+b' ');rejects('runtime receipt drift refused',ns['bootstrap']);receipt.write_bytes(rb)
  ns['importlib'].import_module=lambda n:types.SimpleNamespace(__file__=str(original)) if n==critical[0] else original_import(n)
  rejects('critical loaded same-root wrong-file refused',ns['bootstrap']);ns['importlib'].import_module=original_import
  for name in ['../escape','independent-plan-review-1','other-01','independent-plan-review-01/child']:
   rejects('job name rejects '+name,lambda n=name:ns['allowed_job'](n))
  used=run/'jobs/independent-plan-review-09';used.mkdir();rejects('existing job refused',lambda:ns['allowed_job'](used.name))
  rejects('outside-run plan refused',lambda:ns['allowed_plan'](root/'plan-verified.json'))
  rejects('unverified plan filename refused',lambda:ns['allowed_plan'](planfile.with_name('answer.txt')))
  for h in ['','a'*63,'A'*64,'f'*65]:rejects('bad exact hash '+str(len(h))+h[:1],lambda x=h:ns['hash_arg'](x))
  psha=ns['sha'](planfile);hsha=ns['sha'](handoff)
  pin,*rest=ns['current_pin'](planfile,psha,hsha);check('fixed full context/capsule/plan/handoff positive',pin['executionContextSha256']==ns['CONTEXT_SHA'] and len(pin_calls)>0)
  rejects('wrong plan SHA refuses before provider',lambda:ns['current_pin'](planfile,'0'*64,hsha))
  rejects('wrong handoff SHA refuses before provider',lambda:ns['current_pin'](planfile,psha,'0'*64))
  cb=context.read_bytes();context.write_bytes(cb+b' ');rejects('context byte drift refused',lambda:ns['current_pin'](planfile,psha,hsha));context.write_bytes(cb)
  mb=capmanifest.read_bytes();capmanifest.write_bytes(mb+b' ');rejects('fixed manifest byte drift refused',lambda:ns['current_pin'](planfile,psha,hsha));capmanifest.write_bytes(mb)
  for key,value in [('agentRole','AG-OTHER'),('projectId','other'),('sourceOnly',False),('originalSpecificationsAuthorized',True),('evaluationExpectationsAuthorized',True),('originalProgramsAndDatabaseExecutionAuthorized',True)]:
   bad=dict(ctx);bad[key]=value;context.write_text(json.dumps(bad));oldsha=ns['CONTEXT_SHA'];ns['CONTEXT_SHA']=ns['sha'](context)
   rejects('scope semantic metadata rejects '+key,lambda:ns['current_pin'](planfile,psha,hsha));ns['CONTEXT_SHA']=oldsha;context.write_bytes(cb)
  prompt=ns['build_prompt'](pin,planfile.read_bytes(),cb)
  check('entire context bytes marker and plan verbatim in prompt',cb.decode() in prompt and planfile.read_text() in prompt and 'FULL_CONTEXT_MARKER' in prompt)
  check('core boundary quality format task unchanged prefix',prompt.startswith('BOUNDARY\nQUALITY\nFORMAT\nCORE_REVIEW_TASK\n'))
  ns['importlib'].import_module=lambda n:core if n=='contextbase.ai.plan_review' else original_import(n)
  # Freeze bootstrap closure separately; no production import/capsule main.
  frozen_boot=copy.deepcopy(boot);ns['bootstrap']=lambda:copy.deepcopy(frozen_boot)
  rejects('timeout maximum enforced',lambda:ns['prepare'](planfile,psha,hsha,'independent-plan-review-01',2401))
  prepared=ns['prepare'](planfile,psha,hsha,'independent-plan-review-01',2400)
  check('prepare-only leaves actual job absent/provider0',not Path(prepared['job']).exists() and provider_calls==[])
  prep=Path(prepared['preparation']);rejects('preparation wrong SHA refuses provider',lambda:ns['execute'](prep,'0'*64))
  record=json.loads(prep.read_text());pf=Path(record['promptFile']);pb=pf.read_bytes();pf.write_bytes(pb+b'x');rejects('prepared prompt byte drift refuses provider',lambda:ns['execute'](prep,prepared['preparationSha256']));pf.write_bytes(pb)
  check('negative pre-start cases never invoke bound provider stub',provider_calls==[])
  success=ns['execute'](prep,prepared['preparationSha256'])
  job=Path(prepared['job']);check('run control invokes bound schema exactly once',len(provider_calls)==1 and provider_calls[0]['schema']==core.PLAN_REVIEW)
  check('same core answer validator invoked',validate_calls==[True])
  check('accepted answer byte copy exact',success['approved'] is True and (job/'answer.txt').read_bytes()==(job/'plan-review-verified.json').read_bytes())
  check('handoff preserves AI response unchanged',json.loads((job/'plan-review-handoff.json').read_text())['aiResponseBytesModified'] is False)
  check('after receipt success and formal score absent',json.loads((job.parent/(job.name+'-plan-review-after.json')).read_text())['status']=='UNCHANGED_AND_REVIEW_VALIDATED' and success['formalPercentage'] is None)
  rejects('completed job cannot be reused',lambda:ns['execute'](prep,prepared['preparationSha256']))
  late=ns['prepare'](planfile,psha,hsha,'independent-plan-review-02',2400)
  oldbound=workflow._bound_job
  def drift(*args):
   ret=oldbound(*args);context.write_bytes(cb+b' ');return ret
  workflow._bound_job=drift
  rejects('context drift during provider refuses verified copy',lambda:ns['execute'](late['preparation'],late['preparationSha256']))
  latejob=Path(late['job']);check('failed raw kept and verified answer absent',(latejob/'answer.txt').exists() and not (latejob/'plan-review-verified.json').exists())
  check('failure sidecar explicit not verified',json.loads((latejob.parent/(latejob.name+'-plan-review-after.json')).read_text())['status']=='REVIEW_NOT_VERIFIED')
finally:
 for name,value in saved_modules.items():
  if value is None:sys.modules.pop(name,None)
  else:sys.modules[name]=value
check('production helper bytes unchanged',HELPER.read_bytes()==RAW)
report={'schema':'spec-agent-scoped-plan-review-code-audit/1','createdUtc':datetime.now(timezone.utc).isoformat(),'helper':str(HELPER),'helperSha256':H,'status':'PASS_CODE_AND_SYNTHETIC','passed':len(CASE),'failed':0,'cases':CASE,'productionTopLevelExecuted':False,'actualSnapshotOrPlanOrSourceOrOldOutputBodyRead':False,'actualProviderOrApplicationOrDatabaseExecuted':False,'coreOrFrozenModuleModified':False,'limitations':['Toy bound_job and core validator spies establish wrapper sequencing only; no AI or production capsule was invoked.','AST proves unchanged core _validate/_assert_pin and PLAN_REVIEW calls; this audit does not rerun all pre-existing semantic schema tests.','Fresh preparation and actual plan binding await the production verified plan SHA and parent code review.','No actual junction is created in this synthetic audit; safe() explicit pre-read ancestor/reparse checks are reviewed statically.']}
out=HERE/'scoped-plan-wrapper-review-r01.json';assert not out.exists();out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':report['status'],'passed':len(CASE),'report':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}))
