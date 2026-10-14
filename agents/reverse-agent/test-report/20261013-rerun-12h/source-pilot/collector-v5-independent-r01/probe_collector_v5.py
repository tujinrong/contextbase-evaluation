"""Independent code-only v5 delta. Main is executed only with owned synthetic fixtures and toy delegates."""
from __future__ import annotations
import ast,copy,hashlib,importlib,json,subprocess,sys
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime,timezone
from contextbase.ai import capsule as actual_capsule

HERE=Path(__file__).resolve().parent
REPORT=HERE.parent
HELPER=Path(r'D:\開発\contextbase-evaluation\agents\reverse-agent\.tmp\20261013-rerun-12h\training-assisted\collect_reviewed_v5.py')
EXPECTED_SHA='267cad06fb2fb2ed8dc66798c090274a4a2e0ce73ce8eacba739cb8e53033633'
OLD=HELPER.with_name('collect_reviewed_v4.py')
OLD_SHA='1df7864264b5b4e5bf65f295eda5655c468b392fd8020c3e307121fbfd139666'
def sha_file(path):return hashlib.sha256(actual_capsule.safe_path(path).read_bytes()).hexdigest()
if sha_file(HELPER)!=EXPECTED_SHA or sha_file(OLD)!=OLD_SHA:raise ValueError('Approved code-only helper bytes changed')
old_tree=ast.parse(actual_capsule.safe_path(OLD).read_text(encoding='utf-8'))
new_tree=ast.parse(actual_capsule.safe_path(HELPER).read_text(encoding='utf-8'))
old_functions={node.name:node for node in old_tree.body if isinstance(node,ast.FunctionDef)}
new_functions={node.name:node for node in new_tree.body if isinstance(node,ast.FunctionDef)}
changed=[name for name in old_functions if ast.dump(old_functions[name],include_attributes=False)!=ast.dump(new_functions[name],include_attributes=False)]
if set(old_functions)!=set(new_functions) or set(changed)!={'verify_capsule','main'}:raise ValueError('Unexpected v5 function delta')
old_nonfunctions=ast.Module(body=[n for n in old_tree.body if not isinstance(n,ast.FunctionDef)],type_ignores=[])
new_nonfunctions=ast.Module(body=[n for n in new_tree.body if not isinstance(n,ast.FunctionDef)],type_ignores=[])
if ast.dump(old_nonfunctions,include_attributes=False)!=ast.dump(new_nonfunctions,include_attributes=False):
 raise ValueError('Nonfunction production constants or imports changed')

CRITICAL={'contextbase.ai.capsule':'contextbase/ai/capsule.py','contextbase.ai.schemas':'contextbase/ai/schemas.py',
 'contextbase.ai.workflow':'contextbase/ai/workflow.py','contextbase.ai.provider':'contextbase/ai/provider.py',
 'contextbase.ai.prompts':'contextbase/ai/prompts.py','contextbase.ai.validation':'contextbase/ai/validation.py'}
RUNTIME_RECEIPT=REPORT/'runtime-code-source-10.json'
RECEIPT_SHA='a38c4efa878dc4c6a47967a39b99494ddc3818d63db953e00058e7eab80b1083'
def actual_runtime_proof(label):
 if sha_file(RUNTIME_RECEIPT)!=RECEIPT_SHA:raise ValueError('Own runtime receipt changed')
 value=json.loads(actual_capsule.safe_path(RUNTIME_RECEIPT).read_text(encoding='utf-8'))
 root=actual_capsule.safe_path(Path(value['destination']))
 expected_root=Path(r'D:\開発\contextbase-evaluation\agents\reverse-agent\.tmp\20261013-rerun-12h\source-only\runtime-code\source-10\src')
 if root!=actual_capsule.safe_path(expected_root):raise ValueError('Own runtime leaves source10')
 actual={}
 pending=[root]
 while pending:
  directory=actual_capsule.safe_path(pending.pop())
  for raw in directory.iterdir():
   path=actual_capsule.safe_path(raw)
   if '__pycache__' in path.parts or path.suffix in {'.pyc','.pyo'}:continue
   if path.is_dir():pending.append(path)
   elif path.is_file():actual[path.relative_to(root).as_posix()]=sha_file(path)
 if actual!=value['files'] or len(actual)!=126:raise ValueError('Own complete runtime membership/bytes mismatch')
 discovered={}
 for name,recorded in value['imports'].items():
  origin=actual_capsule.safe_path(Path(importlib.util.find_spec(name).origin))
  if origin!=actual_capsule.safe_path(Path(recorded)) or sha_file(origin)!=actual[origin.relative_to(root).as_posix()]:
   raise ValueError('Own thirteen import resolution mismatch')
  discovered[name]=str(origin)
 if len(discovered)!=13:raise ValueError('Own thirteen imports required')
 loaded={}
 for name,relative in CRITICAL.items():
  module=importlib.import_module(name);expected=actual_capsule.safe_path(root/relative)
  if actual_capsule.safe_path(Path(module.__file__))!=expected or actual_capsule.safe_path(Path(module.__spec__.origin))!=expected:
   raise ValueError('Own loaded critical module exact path mismatch')
  if sha_file(expected)!=actual[relative]:raise ValueError('Own loaded critical bytes mismatch')
  loaded[name]={'path':str(expected),'sha256':actual[relative]}
 proof={'schema':'collector-own-audit-runtime-proof/1','label':label,'createdAt':datetime.now(timezone.utc).isoformat(),
  'receipt':str(RUNTIME_RECEIPT),'receiptSha256':RECEIPT_SHA,'files':actual,'fileCount':126,
  'resolvedImports':discovered,'criticalLoadedModules':loaded,'pythonExecutable':sys.executable,
  'applicationImportedOrExecuted':False}
 with (HERE/f'audit-runtime-{label}.json').open('x',encoding='utf-8') as stream:json.dump(proof,stream,ensure_ascii=False,indent=2)
 return proof
before=actual_runtime_proof('before')

old_probe=REPORT/'collector-v4-independent-r01/probe_collector.py'
probe_text=old_probe.read_text(encoding='utf-8')
space={'__file__':str(__file__),'__name__':'owned_fixture_definitions_only'}
exec(compile(probe_text.split('\nRESULTS=[]\n',1)[0],str(old_probe)+' [definitions only]','exec'),space)
space['CODE']=compile(ast.fix_missing_locations(ast.Module(body=list(new_functions.values()),type_ignores=[])),str(HELPER)+' [functions only]','exec')
BaseFixture=space['Fixture'];store=space['store'];disk_sha=space['disk_sha']

class Fixture(BaseFixture):
 def __init__(self,name):
  super().__init__(name)
  self.delegate_calls=[];self.delegate_fault=None;self.planned_fault=None
  for d in self.documents:self.raw_contract(d,'analysis','same-job:analysis-verified-before-draft')
  self.ns['workflow']=SimpleNamespace(references_valid=self.references_valid,
      select_document=self.select_document,_resume_analysis=self.resume_analysis)
 def raw_contract(self,d,provider,origin):
  job=d['job'];analysis=self.read(d['analysis'])
  artifacts={
   'answer.txt':analysis,'result.json':{'synthetic':True,'answer':analysis},
   'schema.json':{'type':'object','synthetic':True},'prompt.txt':{'synthetic':'fixed provider prompt'}}
  for name,body in artifacts.items():store(job/provider/name,body)
  evidence={provider+'-snapshot-before.json':self.state,
            provider+'-snapshot-after.json':{'status':'UNCHANGED','before':self.state,'after':self.state}}
  for name,body in evidence.items():store(job/name,body)
  checkpoint=self.read(d['checkpoint'])
  checkpoint.update(schema='reverse-ai-analysis-handoff/1',origin=origin,aiResponseBytesModified=False,
   providerDirectory=provider,providerArtifactsSha256={n:disk_sha(job/provider/n) for n in artifacts},
   snapshotEvidenceSha256={n:disk_sha(job/n) for n in evidence})
  store(d['checkpoint'],checkpoint)
 def select_document(self,plan,document_id):
  if Path(plan)!=self.plan:raise ValueError('Toy selector received another plan')
  if self.ns['sha'](self.plan)!=self.ns['PLAN_SHA']:raise ValueError('Toy plan changed')
  definitions=self.ns['read'](self.plan)['documents']
  result=copy.deepcopy(next(d for d in definitions if d['id']==document_id))
  self.delegate_calls.append({'op':'select_document','plan':str(plan),'documentId':document_id})
  if self.planned_fault:result.update(self.planned_fault)
  return result
 def resume_analysis(self,cap,definition,job):
  if Path(cap)!=self.cap:raise ValueError('Toy resume received another capsule')
  self.ns['inside'](Path(job),self.base/'jobs')
  if not any(d['definition']==definition and d['job']==Path(job) for d in self.documents):
   raise ValueError('Toy resume received another bound definition/job')
  analysis=self.ns['read'](Path(job)/'analysis-verified.json')
  checkpoint=self.ns['read'](Path(job)/'analysis-handoff.json')
  digest=self.ns['sha'](Path(job)/'analysis-handoff.json')
  self.delegate_calls.append({'op':'_resume_analysis','capsule':str(cap),'job':str(job),'documentId':definition['id']})
  if self.delegate_fault=='analysis':analysis={**analysis,'syntheticMismatch':True}
  elif self.delegate_fault=='checkpoint':checkpoint={**checkpoint,'syntheticMismatch':True}
  elif self.delegate_fault=='sha':digest='0'*64
  elif self.delegate_fault=='reject':raise ValueError('Toy frozen delegate rejected raw evidence')
  return analysis,checkpoint,digest

space['Fixture']=Fixture;space['RESULTS']=[]
probe_tree=ast.parse(probe_text)
extra_functions=[n for n in probe_tree.body if isinstance(n,ast.FunctionDef) and n.name not in {'store','disk_sha'}]
exec(compile(ast.fix_missing_locations(ast.Module(body=extra_functions,type_ignores=[])),str(old_probe)+' [technical functions only]','exec'),space)
original_main_case=space['main_case']
def main_case(name,mutate=None,accepted=False):
 fixture=original_main_case(name,mutate,accepted)
 row=space['RESULTS'][-1]
 row['selectCalls']=sum(c['op']=='select_document' for c in fixture.delegate_calls)
 row['resumeCalls']=sum(c['op']=='_resume_analysis' for c in fixture.delegate_calls)
 row['linkedTargetReadCount']=sum(c['op'].startswith('read_') and '/linked/' in c['path'].replace('\\','/') for c in fixture.trace)
 if accepted:
  if row['selectCalls']!=11 or row['resumeCalls']!=11:row['pass']=False;row['delegatePositiveControlFailed']=True
  if not fixture.outreport.exists():row['pass']=False
  else:
   collected=fixture.read(fixture.outreport)
   if not all(d.get('completedAnalysisCheckpointRevalidated') is True for d in collected['documents']):row['pass']=False
 print(json.dumps(row,ensure_ascii=False),flush=True)
 return fixture
space['main_case']=main_case
old_calls=[n for n in probe_tree.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call)
           and isinstance(n.value.func,ast.Name) and n.value.func.id=='main_case']
exec(compile(ast.fix_missing_locations(ast.Module(body=old_calls,type_ignores=[])),str(old_probe)+' [49 owned synthetic main cases]','exec'),space)

cp_change=lambda f,**kwargs:f.change(f.documents[0]['checkpoint'],**kwargs)
main_case('checkpoint-provider-map-empty',lambda f:cp_change(f,providerArtifactsSha256={}))
main_case('checkpoint-evidence-map-empty',lambda f:cp_change(f,snapshotEvidenceSha256={}))
main_case('checkpoint-provider-map-incomplete',lambda f:cp_change(f,providerArtifactsSha256={'answer.txt':disk_sha(f.documents[0]['job']/'analysis/answer.txt')}))
main_case('checkpoint-unrecognized-schema',lambda f:cp_change(f,schema='unexpected'))
main_case('checkpoint-ai-response-marked-modified',lambda f:cp_change(f,aiResponseBytesModified=True))
main_case('checkpoint-analysis-documentid-wrong',lambda f:(f.change(f.documents[0]['analysis'],documentId='OTHER'),cp_change(f,analysisSha256=disk_sha(f.documents[0]['analysis']))))
main_case('checkpoint-schema-missing',lambda f:cp_change(f,schema=None))
main_case('checkpoint-origin-unknown',lambda f:cp_change(f,origin='unknown'))
main_case('checkpoint-modified-integer-false',lambda f:cp_change(f,aiResponseBytesModified=0))
main_case('checkpoint-provider-directory-unknown',lambda f:cp_change(f,providerDirectory='provider'))
main_case('checkpoint-provider-map-wrongtype',lambda f:cp_change(f,providerArtifactsSha256=[]))
main_case('checkpoint-provider-map-additionalkey',lambda f:cp_change(f,providerArtifactsSha256={**f.read(f.documents[0]['checkpoint'])['providerArtifactsSha256'],'events.jsonl':'0'*64}))
main_case('checkpoint-evidence-map-wrongtype',lambda f:cp_change(f,snapshotEvidenceSha256=[]))
main_case('checkpoint-evidence-map-incomplete',lambda f:cp_change(f,snapshotEvidenceSha256={'analysis-snapshot-before.json':disk_sha(f.documents[0]['job']/'analysis-snapshot-before.json')}))
main_case('checkpoint-evidence-map-additionalkey',lambda f:cp_change(f,snapshotEvidenceSha256={**f.read(f.documents[0]['checkpoint'])['snapshotEvidenceSha256'],'other.json':'0'*64}))
main_case('checkpoint-full-provider-map-wronghash',lambda f:cp_change(f,providerArtifactsSha256={**f.read(f.documents[0]['checkpoint'])['providerArtifactsSha256'],'answer.txt':'0'*64}))
main_case('checkpoint-full-evidence-map-wronghash',lambda f:cp_change(f,snapshotEvidenceSha256={**f.read(f.documents[0]['checkpoint'])['snapshotEvidenceSha256'],'analysis-snapshot-before.json':'0'*64}))
main_case('selector-documentid-mismatch',lambda f:setattr(f,'planned_fault',{'id':'OTHER'}))
main_case('selector-documentpath-mismatch',lambda f:setattr(f,'planned_fault',{'path':'other.md'}))
main_case('selector-documentkind-mismatch',lambda f:setattr(f,'planned_fault',{'kind':'TABLE'}))
for fault in ('analysis','checkpoint','sha','reject'):
 main_case('resume-return-'+fault,lambda f,fault=fault:setattr(f,'delegate_fault',fault))
def all_repair(f):
 for d in f.documents:f.raw_contract(d,'analysis-repair','deferred-bind:legacy-provider-and-before-after-evidence-verified')
main_case('positive-analysis-repair-deferred-exact-contract',all_repair,accepted=True)
for key,value in [('manifestSha256','0'*64),('mode','source-only')]:
 main_case('fixed-plan-preserved-state-'+key,lambda f,key=key,value=value:f.state.__setitem__(key,value))
def manifest_changed_during_state(f):
 original=f.ns['capsule'].verification_state
 def changed(path):
  value=original(path);store(f.cap/'manifest.json',b'changed synthetic manifest');return value
 f.ns['capsule'].verification_state=changed
main_case('manifest-byte-change-during-state',manifest_changed_during_state)

def junction(path,target):
 path.parent.mkdir(parents=True,exist_ok=True);target.mkdir(parents=True,exist_ok=True)
 quoted=lambda p:"'"+str(p).replace("'","''")+"'"
 result=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',
  'New-Item -ItemType Junction -Path '+quoted(path)+' -Target '+quoted(target)+' | Out-Null'],
  capture_output=True,text=True,encoding='utf-8',errors='replace')
 if result.returncode:raise RuntimeError('Owned junction fixture failed: '+result.stderr)
def linked_selection(f):
 target=f.report/'link-target';target.mkdir();store(target/'selection.json',f.read(f.selection))
 junction(f.report/'linked',target);f.selection=f.report/'linked/selection.json'
def linked_runtime(f):
 target=f.root/'link-target';target.mkdir();store(target/'never-read.txt',b'owned synthetic file')
 junction(f.base/'runtime-code/assisted-06/src/linked',target)
def linked_raw_provider(f):
 d=f.documents[0];job=d['job'];target=f.root/'raw-link-target';target.mkdir()
 current=f.read(d['checkpoint'])
 for name in current['providerArtifactsSha256']:store(target/name,(job/'analysis'/name).read_bytes())
 for suffix,body in [('before',f.state),('after',{'status':'UNCHANGED','before':f.state,'after':f.state})]:
  store(job/f'analysis-repair-snapshot-{suffix}.json',body)
 junction(job/'analysis-repair',target)
 cp_change(f,providerDirectory='analysis-repair',
  snapshotEvidenceSha256={f'analysis-repair-snapshot-{suffix}.json':disk_sha(job/f'analysis-repair-snapshot-{suffix}.json') for suffix in ('before','after')})
main_case('actual-junction-selection-read-refused',linked_selection)
main_case('actual-junction-runtime-descend-refused',linked_runtime)
main_case('actual-junction-raw-provider-read-refused',linked_raw_provider)

after=actual_runtime_proof('after')
if before['files']!=after['files'] or before['resolvedImports']!=after['resolvedImports'] or before['criticalLoadedModules']!=after['criticalLoadedModules']:
 raise ValueError('Own audit runtime changed')
if sha_file(HELPER)!=EXPECTED_SHA or sha_file(OLD)!=OLD_SHA:raise ValueError('Approved helper code changed during audit')
rows=space['RESULTS']
result={'schema':'collector-v5-independent-code-synthetic-delta/1','createdAt':datetime.now(timezone.utc).isoformat(),
 'helper':str(HELPER),'helperSha256':EXPECTED_SHA,'oldHelperSha256':OLD_SHA,'oldHelperUnchanged':True,
 'changedFunctions':changed,'allOtherFunctionAstsAndConstantsUnchanged':True,
 'cases':rows,'total':len(rows),'passed':sum(row['pass'] for row in rows),'allPass':all(row['pass'] for row in rows),
 'findings':[row for row in rows if not row['pass']],
 'positiveControl':'Exact raw4 + before/after2 in analysis/same-job and analysis-repair/deferred cases; toy select/resume called eleven times each and returned analysis/checkpoint/SHA compared',
 'frozenWorkflowDelegatesMocked':True,'actualFrozenWorkflowResumeInvoked':False,
 'actualSafePathAndStructuralValidatorUsed':True,'actualOwnJunctionsUsed':True,
 'ownRuntimeReceiptSha256':RECEIPT_SHA,'ownRuntime126Files13Resolved6LoadedBeforeAfterExact':True,
 'actualBusinessMaterialsRead':0,'originalSpecificationsRead':0,'evaluationMaterialsRead':0,
 'actualCollections':0,'providers':0,'applications':0,'databases':0,'syntheticMainAndCopyOnly':True,
 'visualReview':False,'semanticApproval':False,'finalAdoptionApproval':False,
 'limitations':['Production eleven inputs and actual raw provider responses not opened',
                'Frozen workflow select/resume delegated behavior tested with toy stubs; no new claim of their core semantic verification',
                'No atomic-open hostile concurrent filesystem race guarantee']}
store(HERE/'review.json',result)
print(json.dumps({'review':str(HERE/'review.json'),'sha256':disk_sha(HERE/'review.json'),
                  'total':result['total'],'passed':result['passed'],'findings':result['findings']},ensure_ascii=False),flush=True)
