"""Code-only AST tests for a partial retry; actual evaluation materials remain unopened."""
from __future__ import annotations
import ast,copy,hashlib,json,re,subprocess,sys
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime,timezone

HERE=Path(__file__).resolve().parent
EVALUATOR=HERE.parent.parent/'evaluator-only'
HELPER=EVALUATOR/'retry_partial_batch_r01.py'
GRADER=EVALUATOR/'grader.py'
ORIGINAL_RETRY=EVALUATOR/'retry_batch.py'
GRADER_SHA='83390d439db12119fa7f82cfb48672105488ccb748ca960c68ff918112190bb7'
RETRY_SHA='4b14998ea7002f8d189d7658248db617d4e542df80555bff40979e11a0a68f7c'
old_rb,old_rt=Path.read_bytes,Path.read_text
digest=lambda b:hashlib.sha256(b).hexdigest()
file_sha=lambda p:digest(old_rb(p))
if file_sha(GRADER)!=GRADER_SHA or file_sha(ORIGINAL_RETRY)!=RETRY_SHA:raise ValueError('Original infrastructure changed')
tree=ast.parse(old_rt(HELPER,encoding='utf-8'))
definitions=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[])
compiled=compile(ast.fix_missing_locations(definitions),str(HELPER)+' [functions only]','exec')
safe_definition=next(n for n in ast.parse(old_rt(GRADER,encoding='utf-8')).body if isinstance(n,ast.FunctionDef) and n.name=='safe')
safe_space={'Path':Path}
exec(compile(ast.fix_missing_locations(ast.Module(body=[safe_definition],type_ignores=[])),str(GRADER)+' [safe function only]','exec'),safe_space)
actual_safe=safe_space['safe']
def store(path,value):
 path.parent.mkdir(parents=True,exist_ok=True)
 if isinstance(value,bytes):path.write_bytes(value)
 else:path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
def read(path):return json.loads(old_rt(path,encoding='utf-8'))

class Fixture:
 def __init__(self,name):
  self.root=HERE/'synthetic'/name;self.root.mkdir(parents=True,exist_ok=False)
  self.evaluator=self.root/'evaluator';self.source=self.evaluator/'batches/original'
  self.destination=self.evaluator/'batches/fresh';self.receipt=self.evaluator/'checkpoints/closed.json'
  self.trace=[];self.validated=set();self.check_calls=[];self.validation_calls=[];self.validation_fail=False
  self.callback_fault=None;self.changed_source_by_test=False
  grader_file=self.evaluator/'grader.py';store(grader_file,b'owned synthetic grader code')
  self.grader_sha=file_sha(grader_file)
  jobs=[{'shardId':f'S{i:03d}','documentId':'SYN-DOC','requestPath':f'requests/S{i:03d}.json'} for i in range(1,21)]
  records=[]
  for job in jobs:
   path=self.source/'capsule'/job['requestPath'];store(path,{'shardId':job['shardId'],'synthetic':True})
   records.append({'path':job['requestPath'],'sha256':file_sha(path)})
  path=self.source/'capsule/source/fixture.txt';store(path,b'synthetic source material; never executed')
  records.append({'path':'source/fixture.txt','sha256':file_sha(path)})
  store(self.source/'capsule/manifest.json',{'schema':'synthetic-capsule','files':records})
  self.seal={'schema':'independent-grade-batch/1','jobs':jobs,'graderSha256':self.grader_sha,
             'capsuleManifestSha256':file_sha(self.source/'capsule/manifest.json'),'rubricMaximumPoints':100}
  store(self.source/'batch.json',self.seal)
  store(self.source/'answer-schema.json',{'type':'object','synthetic':True})
  store(self.source/'canonical-pin.json',{'synthetic':True,'sha256':'a'*64})
  bad=self.source/'jobs/S001';ok=self.source/'jobs/S002'
  store(bad/'answer.txt',b'TIMEOUT partial opaque bytes are not a JSON answer\n')
  store(bad/'events.jsonl',b'{"synthetic":"failed partial raw"}\n')
  store(bad/'result.json',{'shardId':'S001','documentId':'SYN-DOC','status':'TIMEOUT'})
  store(ok/'answer.txt',b'{ "opaque" : "unchanged literal", "scale" : "1.00" }\n')
  store(ok/'events.jsonl',b'{"synthetic":"accepted raw events"}\n')
  store(ok/'stderr.log',b'synthetic diagnostic\n')
  store(ok/'result.json',{'shardId':'S002','documentId':'SYN-DOC','status':'PASSED','answerSha256':file_sha(ok/'answer.txt')})
  store(self.receipt,{'schema':'partial-controller-terminal-receipt/1','sourceBatch':str(self.source),
   'sourceBatchManifestSha256':file_sha(self.source/'batch.json'),'controllerExited':True,
   'observedRootSessionId':14055,'controllerExitCode':1,'startedJobLimit':2,
   'terminalJobs':[{'shardId':s,'status':read(self.source/'jobs'/s/'result.json')['status'],
                    'resultSha256':file_sha(self.source/'jobs'/s/'result.json')} for s in ('S001','S002')],
   'otherJobDirectoriesAbsent':True,'unstartedJobs':18})
  self.receipt_sha=file_sha(self.receipt)
  fake=SimpleNamespace(HERE=self.evaluator,__file__=str(grader_file),__spec__=SimpleNamespace(origin=str(grader_file)),
    safe=self.safe,check_capsule=self.check_capsule,validate_answer=self.validate_answer)
  self.ns={'grader':fake,'Path':Path,'PurePosixPath':__import__('pathlib').PurePosixPath,'hashlib':hashlib,'json':json,
   're':re,'datetime':datetime,'timezone':timezone,'argparse':__import__('argparse'),
   'GRADER_SHA256':self.grader_sha,'STARTED_JOB_LIMIT':2,'TOTAL_JOB_COUNT':20,
   'TERMINAL_STATUSES':{'PASSED','TIMEOUT','CLI_FAILED','VALIDATION_OR_PROVIDER_FAILED','DEADLINE_EXPIRED'}}
  exec(compiled,self.ns)
 def safe(self,path,root):
  self.trace.append({'op':'safe','path':str(path),'root':str(root)})
  answer=actual_safe(path,root)
  if not answer.resolve().is_relative_to(self.root.resolve()):raise ValueError('Fixture refuses production path')
  self.validated.add(str(answer.resolve()));return answer
 def check_capsule(self,batch):
  self.check_calls.append(str(batch))
  seal=self.ns['_load'](batch/'batch.json',batch);cap=self.ns['_safe'](batch/'capsule',batch)
  if seal['graderSha256']!=self.grader_sha or self.ns['_digest'](cap/'manifest.json',cap)!=seal['capsuleManifestSha256']:
   raise ValueError('Toy original grader/capsule seal drift')
  manifest=self.ns['_load'](cap/'manifest.json',cap)
  for item in manifest['files']:
   if self.ns['_digest'](cap/item['path'],cap)!=item['sha256']:raise ValueError('Toy sealed capsule member drift')
  if self.callback_fault=='returned-seal':return {**seal,'syntheticMismatch':True},cap
  if self.callback_fault=='returned-cap':return seal,batch/'other-cap'
  if self.callback_fault=='during-validation' and len(self.check_calls)==1:
   store(self.source/'capsule/source/fixture.txt',b'changed by synthetic callback');self.changed_source_by_test=True
  if self.callback_fault=='after-copy-source' and batch==self.destination:
   store(self.source/'jobs/S001/events.jsonl',b'changed by synthetic callback');self.changed_source_by_test=True
  return seal,cap
 def validate_answer(self,answer,request,cap):
  self.validation_calls.append({'answer':answer,'request':request,'capsule':str(cap)})
  if self.validation_fail or answer!={'opaque':'unchanged literal','scale':'1.00'} or request.get('shardId')!='S002':
   raise ValueError('Toy strict answer validation rejected')
 def receipt_change(self,**fields):
  body=read(self.receipt);body.update(fields);store(self.receipt,body);self.receipt_sha=file_sha(self.receipt)
 def result_change(self,shard='S001',**fields):
  path=self.source/'jobs'/shard/'result.json';body=read(path);body.update(fields);store(path,body)
  receipt=read(self.receipt)
  for item in receipt['terminalJobs']:
   if item['shardId']==shard:item.update(status=body['status'],resultSha256=file_sha(path))
  store(self.receipt,receipt);self.receipt_sha=file_sha(self.receipt)
 def collect(self):
  def rb(path):
   if path.resolve().is_relative_to(self.root.resolve()) and str(path.resolve()) not in self.validated:
    raise AssertionError('READ_BEFORE_SAFE: '+str(path))
   self.trace.append({'op':'read_bytes','path':str(path)});return old_rb(path)
  def rt(path,*args,**kwargs):
   if path.resolve().is_relative_to(self.root.resolve()) and str(path.resolve()) not in self.validated:
    raise AssertionError('READ_BEFORE_SAFE: '+str(path))
   self.trace.append({'op':'read_text','path':str(path)});return old_rt(path,*args,**kwargs)
  Path.read_bytes,Path.read_text=rb,rt
  try:return self.ns['prepare_partial_retry'](self.source,self.destination,self.receipt,self.receipt_sha)
  finally:Path.read_bytes,Path.read_text=old_rb,old_rt

RESULTS=[]
def case(name,mutate=None,accepted=False):
 f=Fixture(name)
 if mutate:mutate(f)
 before=f.ns['_inventory'](f.source)
 f.trace=[];f.validated=set()
 error=None;result=None
 try:result=f.collect()
 except Exception as exc:error={'type':type(exc).__name__,'message':str(exc)}
 after=f.ns['_inventory'](f.source)
 passed=(error is None)==accepted
 if accepted:
  passed=passed and result['reused']==1 and result['retryJobs']==1 and result['unstarted']==18 and before==after
  record=read(f.destination/'retry-provenance.json')
  passed=passed and len(record['reusedAcceptedJobs'])==1 and len(record['retryJobs'])==1 and len(record['unstartedJobs'])==18
  passed=passed and not (f.destination/'jobs/S001').exists() and all(not (f.destination/'jobs'/f'S{i:03d}').exists() for i in range(3,21))
  for path in (f.source/'jobs/S002').iterdir():
   passed=passed and old_rb(path)==old_rb(f.destination/'jobs/S002'/path.name)
  for relative in ['batch.json','answer-schema.json','canonical-pin.json',*[f'capsule/requests/S{i:03d}.json' for i in range(1,21)]]:
   passed=passed and old_rb(f.source/relative)==old_rb(f.destination/relative)
 row={'name':name,'expected':'ACCEPT' if accepted else 'REJECT','actual':'ACCEPT' if error is None else 'REJECT',
      'pass':bool(passed),'error':error,'destinationExists':f.destination.exists(),
      'provenanceExists':(f.destination/'retry-provenance.json').exists(),
      'sourceBeforeAfterUnchanged':before==after,'sourceMutationInjectedByTest':f.changed_source_by_test,
      'validateAnswerCalls':len(f.validation_calls),'checkCapsuleCalls':len(f.check_calls),
      'result':result,'productionMaterialsRead':0,'providers':0}
 RESULTS.append(row);store(f.root/'trace.json',f.trace)
 print(json.dumps(row,ensure_ascii=False),flush=True)
 return f

case('positive-closed-partial-byte-copy',accepted=True)
case('active-controller',lambda f:f.receipt_change(controllerExited=False))
case('controller-exit-success',lambda f:f.receipt_change(controllerExitCode=0))
case('controller-exit-bool',lambda f:f.receipt_change(controllerExitCode=True))
case('joblimit-other',lambda f:f.receipt_change(startedJobLimit=3))
case('joblimit-bool',lambda f:f.receipt_change(startedJobLimit=True))
case('receipt-schema-other',lambda f:f.receipt_change(schema='other'))
case('receipt-sha-drift',lambda f:store(f.receipt,b'changed receipt'))
case('receipt-pin-not-explicit',lambda f:setattr(f,'receipt_sha',None))
case('receipt-source-mismatch',lambda f:f.receipt_change(sourceBatch=str(f.evaluator/'batches/other')))
case('receipt-batch-sha-mismatch',lambda f:f.receipt_change(sourceBatchManifestSha256='0'*64))
case('receipt-unstarted-count-wrong',lambda f:f.receipt_change(unstartedJobs=17))
case('receipt-absent-flag-false',lambda f:f.receipt_change(otherJobDirectoriesAbsent=False))
case('receipt-terminal-order-wrong',lambda f:f.receipt_change(terminalJobs=list(reversed(read(f.receipt)['terminalJobs']))))
case('receipt-terminal-duplicate',lambda f:f.receipt_change(terminalJobs=[read(f.receipt)['terminalJobs'][0]]*2))
case('receipt-result-sha-mismatch',lambda f:f.receipt_change(terminalJobs=[{**read(f.receipt)['terminalJobs'][0],'resultSha256':'0'*64},read(f.receipt)['terminalJobs'][1]]))
case('started-running',lambda f:f.result_change(status='RUNNING'))
case('started-unknown-status',lambda f:f.result_change(status='SKIPPED'))
case('started-document-mismatch',lambda f:f.result_change(documentId='OTHER'))
case('started-shard-mismatch',lambda f:f.result_change(shardId='OTHER'))
def empty_started(f):
 root=f.source/'jobs/S001'
 for path in root.iterdir():
  if not path.resolve().is_relative_to(f.root.resolve()) or not path.is_file():raise ValueError('Unsafe owned fixture cleanup')
  path.unlink()
case('empty-started-directory',empty_started)
case('started-result-missing',lambda f:(f.source/'jobs/S001/result.json').unlink())
case('unstarted-empty-directory',lambda f:(f.source/'jobs/S003').mkdir())
case('unknown-job-directory',lambda f:(f.source/'jobs/EXTRA').mkdir())
case('accepted-answer-drift',lambda f:store(f.source/'jobs/S002/answer.txt',b'{"changed":true}'))
case('accepted-answer-missing',lambda f:(f.source/'jobs/S002/answer.txt').unlink())
case('accepted-answer-validation-fails',lambda f:setattr(f,'validation_fail',True))
case('destination-already-exists',lambda f:f.destination.mkdir())
case('destination-nested-source',lambda f:setattr(f,'destination',f.source/'nested-retry'))
case('destination-is-source',lambda f:setattr(f,'destination',f.source))
case('grader-returned-seal-mismatch',lambda f:setattr(f,'callback_fault','returned-seal'))
case('grader-returned-capsule-mismatch',lambda f:setattr(f,'callback_fault','returned-cap'))
case('source-drift-during-validation',lambda f:setattr(f,'callback_fault','during-validation'))
case('source-drift-after-copy',lambda f:setattr(f,'callback_fault','after-copy-source'))

def inject_copy(f,kind):
 original=f.ns['copy_checked'];done=[False]
 def altered(source,destination,*args):
  value=original(source,destination,*args)
  if not done[0]:
   done[0]=True
   if kind in {'failed','unstarted'}:
    store(f.destination/'jobs'/('S001' if kind=='failed' else 'S003')/'result.json',{'synthetic':'injected forbidden result'})
   elif kind=='source':
    store(f.source/'jobs/S002/answer.txt',b'changed by synthetic callback');f.changed_source_by_test=True
  if kind=='rewrite-answer' and destination.name=='answer.txt':store(destination,b'changed copied answer')
  return value
 f.ns['copy_checked']=altered
for kind in ('failed','unstarted','source','rewrite-answer'):
 case('copy-injection-'+kind,lambda f,kind=kind:inject_copy(f,kind))

def mutate_jobs(f,kind):
 seal=read(f.source/'batch.json')
 if kind=='count':seal['jobs'].pop()
 if kind=='duplicate':seal['jobs'][2]=copy.deepcopy(seal['jobs'][1])
 if kind=='request-traversal':seal['jobs'][2]['requestPath']='../outside.json'
 if kind=='id-traversal':seal['jobs'][2]['shardId']='../outside'
 store(f.source/'batch.json',seal);f.receipt_change(sourceBatchManifestSha256=file_sha(f.source/'batch.json'))
for kind in ('count','duplicate','request-traversal','id-traversal'):
 case('batch-jobs-'+kind,lambda f,kind=kind:mutate_jobs(f,kind))

def junction(path,target):
 path.parent.mkdir(parents=True,exist_ok=True);target.mkdir(parents=True,exist_ok=True)
 quote=lambda p:"'"+str(p).replace("'","''")+"'"
 proc=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',
  'New-Item -ItemType Junction -Path '+quote(path)+' -Target '+quote(target)+' | Out-Null'],
  capture_output=True,text=True,encoding='utf-8',errors='replace')
 if proc.returncode:raise RuntimeError('Owned junction fixture failed: '+proc.stderr)
def linked(f,kind):
 if kind=='source':
  path=f.evaluator/'batches/source-link';junction(path,f.source);f.source=path
 elif kind=='destination':
  path=f.evaluator/'batches/destination-link';junction(path,f.evaluator/'batches/link-target');f.destination=path/'fresh'
 else:
  path=f.source/('capsule/link' if kind=='capsule' else 'jobs/S002/link')
  target=f.root/'never-read';target.mkdir();store(target/'opaque.txt',b'never read linked target');junction(path,target)
for kind in ('source','destination','capsule','passed-raw'):
 # Inventory of a linked source is itself expected to refuse. Run via a dedicated
 # case wrapper that avoids pre-test inventory following or inspecting the link.
 f=Fixture('junction-'+kind);linked(f,kind);f.trace=[];f.validated=set();error=None
 try:f.collect()
 except Exception as exc:error={'type':type(exc).__name__,'message':str(exc)}
 reads=[x for x in f.trace if x['op'].startswith('read_') and ('never-read' in x['path'] or '/link/' in x['path'].replace('\\','/'))]
 row={'name':'junction-'+kind,'expected':'REJECT','actual':'REJECT' if error else 'ACCEPT',
      'pass':error is not None and not reads,'error':error,'linkedTargetReads':len(reads),
      'provenanceExists':(f.destination/'retry-provenance.json').exists(),'productionMaterialsRead':0,'providers':0}
 RESULTS.append(row);store(f.root/'trace.json',f.trace);print(json.dumps(row,ensure_ascii=False),flush=True)

if file_sha(GRADER)!=GRADER_SHA or file_sha(ORIGINAL_RETRY)!=RETRY_SHA:raise ValueError('Original code changed during tests')
report={'schema':'partial-batch-retry-code-synthetic-audit/1','createdAt':datetime.now(timezone.utc).isoformat(),
 'helper':str(HELPER),'helperSha256':file_sha(HELPER),'graderSha256':GRADER_SHA,'oldRetrySha256':RETRY_SHA,
 'originalGraderAndRetryUnchanged':True,'cases':RESULTS,'total':len(RESULTS),
 'passed':sum(row['pass'] for row in RESULTS),'allPass':all(row['pass'] for row in RESULTS),
 'findings':[row for row in RESULTS if not row['pass']],
 'extraction':'Helper FunctionDefs only plus original grader.safe FunctionDef; no production grader import/main',
 'graderCheckCapsuleAndValidateAnswerMocked':True,'actualOwnedJunctions':True,
 'actualExpectedReferenceCapsuleAnswersRead':0,'actualCollections':0,'providers':0,'applications':0,'databases':0,
 'syntheticOnly':True,'qualityScore':None,'formalOrSemanticApproval':False}
store(HERE/'review.json',report)
print(json.dumps({'review':str(HERE/'review.json'),'sha256':file_sha(HERE/'review.json'),
                  'helperSha256':report['helperSha256'],'total':report['total'],'passed':report['passed'],
                  'findings':report['findings']},ensure_ascii=False),flush=True)
