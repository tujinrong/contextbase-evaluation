"""Code-only independent collector audit. All main inputs/outputs are owned synthetic fixtures."""
from __future__ import annotations
import ast,argparse,copy,hashlib,importlib.util,json,sys
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime,timezone
from contextbase.ai import capsule as actual_capsule
from contextbase.ai.validation import validate_document

HERE=Path(__file__).resolve().parent
HELPER=Path(r'D:\開発\contextbase-evaluation\agents\reverse-agent\.tmp\20261013-rerun-12h\training-assisted\collect_reviewed_v4.py')
EXPECTED_SHA='1df7864264b5b4e5bf65f295eda5655c468b392fd8020c3e307121fbfd139666'
raw=actual_capsule.safe_path(HELPER).read_bytes()
digest=lambda b:hashlib.sha256(b).hexdigest()
if digest(raw)!=EXPECTED_SHA:raise ValueError('Approved code bytes drift')
TREE=ast.parse(raw)
DEFS=ast.Module(body=[n for n in TREE.body if isinstance(n,ast.FunctionDef)],type_ignores=[])
CONSTANTS={name:ast.literal_eval(n.value) for n in TREE.body if isinstance(n,ast.Assign)
 for t in n.targets if isinstance(t,ast.Name) and (name:=t.id) in ('CRITICAL_MODULE_PATHS','RECEIPT_IMPORT_PATHS','RUNTIME_RECORD_SHAS')}
CODE=compile(ast.fix_missing_locations(DEFS),str(HELPER)+' [functions only]','exec')
OLD_READ_BYTES,OLD_READ_TEXT=Path.read_bytes,Path.read_text

def store(path,value):
 path.parent.mkdir(parents=True,exist_ok=True)
 if isinstance(value,bytes):path.write_bytes(value)
 else:path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
def disk_sha(path):return digest(OLD_READ_BYTES(path))

class Fixture:
 def __init__(self,name):
  self.name=name;self.root=HERE/'synthetic'/name;self.root.mkdir(parents=True,exist_ok=False)
  self.base=self.root/'base';self.report=self.root/'report';self.output_base=self.root/'outputs'
  self.cap=self.base/'snapshot';self.contract=self.report/'document-contract.json'
  self.plan=self.base/'jobs/plan/plan-verified.json';self.plan_handoff=self.plan.parent/'plan-handoff.json'
  self.selection=self.report/'selection.json';self.output=self.output_base/'collected';self.outreport=self.report/'collection.json'
  self.trace=[];self.validated=set();self.reject=set();self.verify_calls=0;self.state_calls=0;self.reference_calls=[]
  self.runtime_records={};self.findspec={};self.loaded={};self.modules={};self.documents=[]
  self.manifest={'mode':'training-assisted','trainingReferenceAuthorizedByUser':True,
    'referenceSpecificationIncluded':True,'sourceRoot':str(self.root/'repo/test-project1/srcs/CSharp_ASPNET')}
  store(self.cap/'manifest.json',self.manifest)
  self.state={'manifestSha256':disk_sha(self.cap/'manifest.json'),'mode':'training-assisted',
   'capsuleSchema':'reverse-ai-source-capsule/2','modeDerivation':'explicit-manifest-mode','scope':'synthetic'}
  self.runtime_shas={}
  for version in ('01','04','05','06'):
   directory=self.base/f'runtime-code/assisted-{version}/src'
   names=set(CONSTANTS['RECEIPT_IMPORT_PATHS'].values())|set(CONSTANTS['CRITICAL_MODULE_PATHS'].values())
   names|={f'synthetic/file-{i:03d}.txt' for i in range(124-len(names))}
   files={}
   for relative in sorted(names):
    path=directory/relative;store(path,('synthetic runtime '+version+' '+relative+'\n').encode());files[relative]=disk_sha(path)
   imports={k:str(directory/v) for k,v in CONSTANTS['RECEIPT_IMPORT_PATHS'].items()}
   receipt={'destination':str(directory),'fileCount':124,'files':files,'imports':imports}
   record=self.report/f'runtime-code-assisted-{version}.json';store(record,receipt)
   self.runtime_shas[record.name]=disk_sha(record);self.runtime_records[version]=(record,receipt)
   if version=='06':
    for name,relative in {**CONSTANTS['RECEIPT_IMPORT_PATHS'],**CONSTANTS['CRITICAL_MODULE_PATHS']}.items():
     self.findspec[name]=SimpleNamespace(origin=str(directory/relative))
    for name,relative in CONSTANTS['CRITICAL_MODULE_PATHS'].items():
     self.loaded[name]=SimpleNamespace(__file__=str(directory/relative),__spec__=SimpleNamespace(origin=str(directory/relative)))
  definitions=[{'id':f'SYN-DOC-{i:02d}','path':f'合成/{i:02d}_fixture.md','kind':'GRID'} for i in range(11)]
  store(self.contract,{'documents':definitions});store(self.plan,{'documents':definitions,'projectId':'synthetic'})
  store(self.plan_handoff,{'planSha256':disk_sha(self.plan),'snapshot':self.state})
  selected=[]
  for i,definition in enumerate(definitions):
   identifier=definition['id'];path=definition['path'];doc=self.output_base/'drafts'/path
   metadata={'schema':'spec-md/1.0','documentId':identifier,'version':'1.0','path':path,
    'sheets':[{'heading':'合成情報','kind':'GRID','sheet':'01_合成'}]}
   text='<!-- spec-meta: '+json.dumps(metadata,ensure_ascii=False)+' -->\n# Synthetic fixture\n\n## 合成情報\n\n| key | value |\n| --- | --- |\n| synthetic | literal |\n'
   store(doc,text.encode('utf-8'))
   findings=validate_document(text,path,expected_document_id=identifier,expected_kind='GRID')
   if findings:raise ValueError('Fixture structurally invalid: '+str(findings))
   job=self.base/f'jobs/document-{i:02d}';analysis=job/'analysis-verified.json';checkpoint=job/'analysis-handoff.json'
   store(analysis,{'documentId':identifier,'sourcePathsRead':['sources/synthetic.txt'],'facts':[],'unresolved':[]})
   for n in ('prompt.txt','answer.txt','events.jsonl','result.json','schema.json'):store(job/'provider'/n,b'synthetic provider artifact\n')
   store(job/'snapshot-evidence.json',b'synthetic evidence\n')
   checkpoint_body={'document':definition,'snapshot':self.state,'referenceMode':'training-assisted',
    'planFile':str(self.plan),'planSha256':disk_sha(self.plan),'planHandoffSha256':disk_sha(self.plan_handoff),
    'analysisSha256':disk_sha(analysis),'analysisJob':str(job),'providerDirectory':'provider',
    'providerArtifactsSha256':{n:disk_sha(job/'provider'/n) for n in ('prompt.txt','answer.txt','events.jsonl','result.json','schema.json')},
    'snapshotEvidenceSha256':{'snapshot-evidence.json':disk_sha(job/'snapshot-evidence.json')}}
   store(checkpoint,checkpoint_body)
   draft=job/'draft-result.json';review=job/'review/review-verified.json';handoff=review.parent/'review-handoff.json'
   store(draft,{'documentId':identifier,'contentSha256':disk_sha(doc),'snapshot':self.state,
    'referenceMode':'training-assisted','analysisJob':str(job),'analysisExecutedInThisJob':False})
   store(review,{'documentId':identifier,'approved':True,'findings':[],'unresolved':[],'sourcePathsRead':['sources/synthetic.txt']})
   store(handoff,{'documentFile':str(doc),'documentSha256':disk_sha(doc),'reviewSha256':disk_sha(review),
    'snapshot':self.state,'referenceMode':'training-assisted','approved':True,'reviewScope':'text-source-and-structure'})
   pin=self.report/f'pin-{i:02d}.json'
   runtimes={}
   for role,version in (('generationRuntime','01'),('reviewRuntime','04'),('structureRuntime','05')):
    record,runtime=self.runtime_records[version]
    runtimes[role]={'record':str(record),'recordSha256':disk_sha(record),'directory':runtime['destination']}
   body={**definition,'documentId':identifier,'canonicalMarkdown':str(doc),'sha256':disk_sha(doc),
    'draftResult':str(draft),'draftResultSha256':disk_sha(draft),'independentReview':str(review),
    'independentReviewSha256':disk_sha(review),'independentReviewApproved':True,
    'noFurtherTextRevisionPlanned':True,'structureStatus':'STRUCTURE_VALID','capsule':self.state,'basisCounts':{'facts':0},**runtimes}
   store(pin,body);selected.append({'documentId':identifier,'pin':str(pin),'pinSha256':disk_sha(pin)})
   self.documents.append({'definition':definition,'doc':doc,'job':job,'analysis':analysis,'checkpoint':checkpoint,
    'draft':draft,'review':review,'handoff':handoff,'pin':pin})
  store(self.selection,{'documents':selected})
  self.ns={'__file__':str(self.root/'synthetic-collector.py'),'argparse':argparse,'datetime':datetime,'timezone':timezone,
   'hashlib':hashlib,'json':json,'Path':Path,'sys':SimpleNamespace(modules=self.loaded),
   'import_util':SimpleNamespace(find_spec=lambda n:self.findspec.get(n)),
   'capsule':SimpleNamespace(safe_path=self.safe_path,verify=self.verify,verification_state=self.verification_state),
   'workflow':SimpleNamespace(references_valid=self.references_valid),'validate_document':validate_document,
   'BASE':self.base,'REPORT':self.report,'REPO':self.root/'repo','OUTPUT_BASE':self.output_base,'CAP':self.cap,
   'CONTRACT':self.contract,'PLAN':self.plan,'PLAN_HANDOFF':self.plan_handoff,
   'MANIFEST_SHA':disk_sha(self.cap/'manifest.json'),'CONTRACT_SHA':disk_sha(self.contract),
   'PLAN_SHA':disk_sha(self.plan),'PLAN_HANDOFF_SHA':disk_sha(self.plan_handoff),
   'RUNTIME_RECORD_SHAS':self.runtime_shas,'LOADED_RUNTIME_DIRECTORY':self.base/'runtime-code/assisted-06/src',
   **{k:v for k,v in CONSTANTS.items() if k!='RUNTIME_RECORD_SHAS'}}
  store(Path(self.ns['__file__']),b'synthetic collector code pin\n')
  exec(CODE,self.ns)
 def safe_path(self,path):
  path=Path(path);self.trace.append({'op':'safe_path','path':str(path)})
  if str(path) in self.reject:raise ValueError('Synthetic linked-path rejection before read')
  safe=actual_capsule.safe_path(path)
  if not safe.is_relative_to(self.root.resolve()):raise ValueError('Synthetic guard refuses production path')
  self.validated.add(str(safe));return safe
 def verify(self,path):
  if Path(path)!=self.cap:raise ValueError('Unexpected cap')
  self.verify_calls+=1;self.trace.append({'op':'verify','path':str(path)});return copy.deepcopy(self.manifest)
 def verification_state(self,path):
  self.state_calls+=1;return copy.deepcopy(self.state)
 def references_valid(self,doc,manifest):
  self.reference_calls.append(doc.get('documentId'))
  if doc.get('sourcePathsRead')!=['sources/synthetic.txt']:raise ValueError('Synthetic non-manifest source')
 def read(self,path):return json.loads(OLD_READ_TEXT(path,encoding='utf-8'))
 def change(self,path,**fields):
  obj=self.read(path);obj.update(fields);store(path,obj)
 def repack(self,i=0):
  d=self.documents[i]
  # Adjust enclosing fixed synthetic pins, so targeted inner guards rather than stale outer SHA reject the mutation.
  handoff=self.read(d['handoff']);handoff['reviewSha256']=disk_sha(d['review']);store(d['handoff'],handoff)
  pin=self.read(d['pin']);pin['draftResultSha256']=disk_sha(d['draft']);pin['independentReviewSha256']=disk_sha(d['review']);store(d['pin'],pin)
  selected=self.read(self.selection)
  selected['documents'][i]['pinSha256']=disk_sha(d['pin']);store(self.selection,selected)
 def collect(self):
  old_argv=sys.argv
  def rb(path):
   resolved=str(path.resolve())
   if path.is_relative_to(self.root) and resolved not in self.validated:raise AssertionError('READ_BEFORE_SAFE_PATH: '+str(path))
   self.trace.append({'op':'read_bytes','path':str(path)});return OLD_READ_BYTES(path)
  def rt(path,*args,**kwargs):
   resolved=str(path.resolve())
   if path.is_relative_to(self.root) and resolved not in self.validated:raise AssertionError('READ_BEFORE_SAFE_PATH: '+str(path))
   self.trace.append({'op':'read_text','path':str(path)});return OLD_READ_TEXT(path,*args,**kwargs)
  Path.read_bytes,Path.read_text=rb,rt
  sys.argv=['synthetic-collector','--selection',str(self.selection),'--output',str(self.output),'--report',str(self.outreport)]
  try:self.ns['main']()
  finally:Path.read_bytes,Path.read_text=OLD_READ_BYTES,OLD_READ_TEXT;sys.argv=old_argv

RESULTS=[]
def main_case(name,mutate=None,accepted=False):
 f=Fixture(name)
 if mutate:mutate(f)
 error=None
 try:f.collect()
 except Exception as exc:error={'type':type(exc).__name__,'message':str(exc)}
 passed=(error is None)==accepted
 records={'name':name,'expected':'ACCEPT' if accepted else 'REJECT','actual':'ACCEPT' if error is None else 'REJECT',
  'pass':passed,'error':error,'capsuleVerifyCalls':f.verify_calls,'stateCalls':f.state_calls,
  'actualMaterialsRead':False,'readTraceCount':sum(x['op'].startswith('read_') for x in f.trace),
  'safePathTraceCount':sum(x['op']=='safe_path' for x in f.trace),'reportExists':f.outreport.exists(),
  'syntheticCopiedFileCount':len(list(f.output.rglob('*.md'))) if f.output.exists() else 0}
 RESULTS.append(records)
 store(f.root/'trace.json',f.trace)
 return f

def selected_change(f,fn):
 obj=f.read(f.selection);fn(obj['documents']);store(f.selection,obj)
def pin_change(f,**fields):
 f.change(f.documents[0]['pin'],**fields);f.repack()
def review_change(f,**fields):
 f.change(f.documents[0]['review'],**fields);f.repack()
def draft_change(f,**fields):
 f.change(f.documents[0]['draft'],**fields);f.repack()
def handoff_change(f,**fields):f.change(f.documents[0]['handoff'],**fields)
def checkpoint_change(f,**fields):f.change(f.documents[0]['checkpoint'],**fields)
def runtime_change(f,version='06',**fields):
 record,runtime=f.runtime_records[version];runtime.update(fields);store(record,runtime)
 f.runtime_shas[record.name]=disk_sha(record)
def setup_mid_copy_mutation(f):
 original=f.ns['assert_unchanged'];calls=[0]
 def altered(*args):
  original(*args);calls[0]+=1
  if calls[0]==1:store(f.documents[0]['doc'],b'changed synthetic document\n')
 f.ns['assert_unchanged']=altered
def setup_after_copy_mutation(f):
 original=f.ns['sha'];changed=[False]
 def altered(path):
  result=original(path)
  if Path(path)==f.output/f.documents[0]['definition']['path'] and not changed[0]:
   changed[0]=True;store(f.documents[0]['pin'],b'changed synthetic pin\n')
  return result
 f.ns['sha']=altered

main_case('positive-full-11-byte-copy',accepted=True)
main_case('selection-duplicate',lambda f:selected_change(f,lambda a:a.__setitem__(10,copy.deepcopy(a[0]))))
main_case('selection-missing',lambda f:selected_change(f,lambda a:a.pop()))
main_case('selection-unknown-id',lambda f:selected_change(f,lambda a:a[0].__setitem__('documentId','UNKNOWN')))
main_case('output-exists',lambda f:f.output.mkdir(parents=True))
main_case('report-exists',lambda f:store(f.outreport,b'existing'))
main_case('selection-outside-root',lambda f:setattr(f,'selection',f.root/'outside.json'))
main_case('selection-linked-policy-before-read',lambda f:f.reject.add(str(f.selection)))
main_case('loaded-runtime-count',lambda f:runtime_change(f,fileCount=123))
main_case('loaded-runtime-membership-added',lambda f:store(f.base/'runtime-code/assisted-06/src/synthetic/extra.txt',b'extra'))
main_case('loaded-runtime-membership-missing',lambda f:runtime_change(f,files={k:v for i,(k,v) in enumerate(f.runtime_records['06'][1]['files'].items()) if i!=0}))
main_case('loaded-runtime-byte-drift',lambda f:store(f.base/'runtime-code/assisted-06/src/contextbase/ai/capsule.py',b'drift'))
main_case('runtime-receipt-destination',lambda f:runtime_change(f,destination=str(f.base/'runtime-code/other/src')))
main_case('loaded-module-file-other-inventory-file',lambda f:setattr(f.loaded['contextbase.ai.capsule'],'__file__',str(f.base/'runtime-code/assisted-06/src/contextbase/ai/provider.py')))
main_case('loaded-module-spec-origin-wrong',lambda f:setattr(f.loaded['contextbase.ai.capsule'].__spec__,'origin',str(f.root/'wrong.py')))
main_case('findspec-origin-wrong',lambda f:setattr(f.findspec['contextbase.ai.workflow'],'origin',str(f.root/'wrong.py')))
main_case('receipt-import-missing',lambda f:runtime_change(f,imports={k:v for k,v in f.runtime_records['06'][1]['imports'].items() if k!='contextbase'}))
main_case('fixed-manifest-sha',lambda f:store(f.cap/'manifest.json',b'drift'))
main_case('fixed-contract-sha',lambda f:store(f.contract,b'drift'))
main_case('fixed-plan-sha',lambda f:store(f.plan,b'drift'))
main_case('fixed-plan-handoff-sha',lambda f:store(f.plan_handoff,b'drift'))
main_case('manifest-mode',lambda f:f.manifest.__setitem__('mode','source-only'))
main_case('manifest-authorization',lambda f:f.manifest.__setitem__('trainingReferenceAuthorizedByUser',False))
main_case('manifest-source-root',lambda f:f.manifest.__setitem__('sourceRoot',str(f.root/'wrong')))
main_case('pin-no-further-revision',lambda f:pin_change(f,noFurtherTextRevisionPlanned=False))
main_case('pin-independent-approved',lambda f:pin_change(f,independentReviewApproved=False))
main_case('pin-structure-status',lambda f:pin_change(f,structureStatus='ERROR'))
main_case('pin-document-wrong-root',lambda f:pin_change(f,canonicalMarkdown=str(f.root/'outside.md')))
main_case('review-approved-false',lambda f:review_change(f,approved=False))
main_case('review-major',lambda f:review_change(f,findings=[{'severity':'major','references':[]}]))
main_case('review-unresolved',lambda f:review_change(f,unresolved=['synthetic']))
main_case('handoff-approved-false',lambda f:handoff_change(f,approved=False))
main_case('handoff-mode',lambda f:handoff_change(f,referenceMode='source-only'))
main_case('handoff-document-other-path',lambda f:handoff_change(f,documentFile=str(f.documents[1]['doc'])))
main_case('handoff-document-sha',lambda f:handoff_change(f,documentSha256='0'*64))
main_case('draft-mode',lambda f:draft_change(f,referenceMode='source-only'))
main_case('draft-document-id',lambda f:draft_change(f,documentId='OTHER'))
main_case('review-source-read-outside-manifest',lambda f:review_change(f,sourcePathsRead=['outside.txt']))
main_case('analysis-plan-sha',lambda f:checkpoint_change(f,planSha256='0'*64))
main_case('analysis-plan-path',lambda f:checkpoint_change(f,planFile=str(f.root/'other-plan.json')))
main_case('analysis-mode',lambda f:checkpoint_change(f,referenceMode='source-only'))
main_case('analysis-provider-traversal',lambda f:checkpoint_change(f,providerDirectory='../elsewhere'))
main_case('analysis-provider-artifact-sha',lambda f:checkpoint_change(f,providerArtifactsSha256={'answer.txt':'0'*64}))
main_case('analysis-evidence-traversal',lambda f:checkpoint_change(f,snapshotEvidenceSha256={'../outside.txt':'0'*64}))
main_case('unregistered-runtime',lambda f:pin_change(f,generationRuntime={'record':str(f.report/'runtime-unknown.json'),'recordSha256':'0'*64,'directory':str(f.base/'runtime-code/other')}))
main_case('source-byte-drift-before-copy',setup_mid_copy_mutation)
main_case('pin-byte-drift-after-copy',setup_after_copy_mutation)

# The collected verification_state must itself be tied to the fixed manifest/mode, not only compared to itself.
def wrong_state(f,key,value):
 f.state[key]=value
 store(f.plan_handoff,{'planSha256':disk_sha(f.plan),'snapshot':f.state});f.ns['PLAN_HANDOFF_SHA']=disk_sha(f.plan_handoff)
 for i,d in enumerate(f.documents):
  f.change(d['draft'],snapshot=f.state);f.change(d['handoff'],snapshot=f.state)
  f.change(d['checkpoint'],snapshot=f.state,planHandoffSha256=f.ns['PLAN_HANDOFF_SHA'])
  f.change(d['pin'],capsule=f.state);f.repack(i)
main_case('verification-state-manifest-sha-mismatch',lambda f:wrong_state(f,'manifestSha256','0'*64))
main_case('verification-state-mode-mismatch',lambda f:wrong_state(f,'mode','source-only'))

out=HERE/'review.json'
result={'schema':'collector-independent-technical-synthetic-review/1','createdAt':datetime.now(timezone.utc).isoformat(),
 'helper':str(HELPER),'helperSha256':EXPECTED_SHA,'extraction':'FunctionDef only; production top-level/imports/main not executed',
 'constantsUsed':['runtime metadata registration names','13 module path map','6 critical module path map'],
 'syntheticMainOnly':True,'validStructuralFixture':True,'capsuleVerifyStateMocked':True,
 'actualBusinessMaterialsRead':0,'actualCollections':0,'providers':0,'applications':0,
 'cases':RESULTS,'total':len(RESULTS),'passed':sum(x['pass'] for x in RESULTS),
 'allPass':all(x['pass'] for x in RESULTS),'findings':[x for x in RESULTS if not x['pass']],
 'oldHelperModified':False,'newSemanticApproval':False}
store(out,result)
print(json.dumps({'review':str(out),'sha256':disk_sha(out),'total':result['total'],'passed':result['passed'],
 'findings':result['findings']},ensure_ascii=False))
