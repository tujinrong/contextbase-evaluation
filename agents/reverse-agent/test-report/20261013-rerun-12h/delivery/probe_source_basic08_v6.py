"""AST selected synthetic-only guard delta; never imports or starts a whole helper."""
from __future__ import annotations
import ast,copy,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
from types import SimpleNamespace
from html.parser import HTMLParser
from markdown_it import MarkdownIt
import tinycss2
HERE=Path(__file__).parent;SOURCE=HERE.parent/'source-pilot'
PINS={'prepare_state_projection_detail07_v5.py':'6fb6aaabaea7822aa6e74a7847c1d175f7d0b949f4df32b68f9b21b1c868237e','prepare_state_projection_basic08_v6.py':'ae29ed7f6fe51ef80d8e7b54afe5b5d6345e649c44a1820bb2c69278ed5f3b06'}
CAP='2f64e2211b1fcd7850203927fc75b5a7f2ce37457cc2afe88c8065d9f931273b'
RECEIPT='0b2f2aff745a7e32394ecc5cde4c1a849ad2d5a32c7fa4339af2e7cdecd48906'
def sha(b):return hashlib.sha256(b).hexdigest()
def run(ns,nodes):exec(compile(ast.Module(body=copy.deepcopy(nodes),type_ignores=[]),'<AST-selected-synthetic-only>','exec'),ns)
def assigned(n,name):return isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets)
def main():
 out=HERE/'state-helper-independent-basic08-v6';out.mkdir(exist_ok=False);trees={};cases=[]
 for name,pin in PINS.items():
  raw=(SOURCE/name).read_bytes();assert sha(raw)==pin;trees[name]=ast.parse(raw.decode('utf8'))
 tree=trees['prepare_state_projection_basic08_v6.py'];base=trees['prepare_state_projection_detail07_v5.py']
 ns={'hashlib':hashlib,'json':json,'Path':Path,'HTMLParser':HTMLParser,'MarkdownIt':MarkdownIt,'tinycss2':tinycss2}
 functions=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name!='runtime_import_pin'];run(ns,functions)
 def probe(name,fn,accept=True):
  try:fn();actual=True;error=None
  except Exception as e:actual=False;error=type(e).__name__+': '+str(e)
  cases.append({'case':name,'expectedAccept':accept,'actualAccept':actual,'pass':accept==actual,'error':error})
 def one_assign(name):return next(n for n in tree.body if assigned(n,name))
 def guard(text):return next(n for n in tree.body if isinstance(n,ast.If) and text in ast.unparse(n))
 def unchanged():
  old={n.name:ast.dump(n,include_attributes=False) for n in base.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
  new={n.name:ast.dump(n,include_attributes=False) for n in functions}
  assert set(old)==set(new) and len(old)==9
  assert {k for k in old if old[k]!=new[k]}=={'canonical_path'}
  names={'ref_schema','location_schema','schema'}
  schemas=lambda t:[ast.dump(n,include_attributes=False) for n in t.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id in names for x in n.targets)]
  assert schemas(base)==schemas(tree)
 probe('nine-existing-functions-eight-byte-equivalent-AST-one-role-path-change-schema-identical',unchanged)
 state={'manifestSha256':CAP};drafts=[{'sha256':'d'*64}]
 schema_ns={**ns,'state':state,'drafts':drafts};run(schema_ns,[one_assign(n) for n in ['ref_schema','location_schema','schema']]);ns['validate_transport_schema'](schema_ns['schema'])
 def schema_case(kind):
  schema=copy.deepcopy(schema_ns['schema'])
  if kind=='missing-type':schema['properties']['reviewScope'].pop('type')
  ns['validate_transport_schema'](schema)
  assert schema['properties']['states']['minItems']==schema['properties']['states']['maxItems']==4
  assert schema['properties']['states']['items']['properties']['id']['enum']==['normal','empty','tooMany','viewer']
 probe('typed-transport-four-fixed-state-schema',lambda:schema_case('correct'))
 probe('transport-enum-without-type-refused',lambda:schema_case('missing-type'),False)
 capnodes=[one_assign('pinned_manifest_before'),guard('before collecting input files'),one_assign('manifest')]
 def capsule_before(kind):
  calls=[];digest=CAP if kind=='correct' else 'a'*64
  local={'args':SimpleNamespace(snapshot=Path('C:/synthetic/snapshot')),'capsule':SimpleNamespace(material_path=lambda *a:SimpleNamespace(read_bytes=lambda:b'synthetic-metadata'),sha256=lambda b:digest,verify=lambda p:calls.append(p) or {'mode':'source-only'})}
  try:run(local,capnodes)
  finally:assert len(calls)==(1 if kind=='correct' else 0)
 probe('fixed-cap-before-verify-collection-positive',lambda:capsule_before('correct'))
 probe('wrong-cap-before-verify-zero-collection',lambda:capsule_before('wrong'),False)
 capguards=[n for n in tree.body if isinstance(n,ast.If) and 'fixed capsule changed' in ast.unparse(n)]
 assert len(capguards)==2
 def capsule_stage(node,kind):
  actual_state=state.copy();value=CAP
  if kind=='bytes':value='a'*64
  elif kind=='state':actual_state={'manifestSha256':CAP,'drift':True}
  local={'args':SimpleNamespace(snapshot=Path('C:/synthetic/snapshot')),'state':state,'capsule':SimpleNamespace(material_path=lambda *a:SimpleNamespace(read_bytes=lambda:b'synthetic'),sha256=lambda b:value,verification_state=lambda p:actual_state)}
  run(local,[node])
 for i,node in enumerate(capguards):
  for kind in ['correct','bytes','state']:probe(f'fixed-cap-stage-{i}-{kind}',lambda n=node,k=kind:capsule_stage(n,k),kind=='correct')
 class File:
  parts=('synthetic','module.py');suffix='.py'
  def __init__(self,name,data=b'original',linked=False):self.name=name;self.data=data;self.linked=linked;self.reads=0
  def relative_to(self,root):return Path(self.name)
  def is_file(self):return True
  def read_bytes(self):self.reads+=1;return self.data
 def inventory(kind,name):
  f=File('module.py',linked=kind=='linked');files=[f]
  if kind=='added':files.append(File('added.py',b'new'))
  elif kind=='deleted':files=[]
  elif kind=='bytes':f.data=b'drift'
  def safe(p):
   if p.linked:raise ValueError('synthetic reparse rejected before read')
   return p
  local={'hashlib':hashlib,'capsule':SimpleNamespace(safe_path=safe),'runtime':SimpleNamespace(rglob=lambda _:files)}
  try:run(local,[one_assign(name)])
  finally:
   if kind=='linked':assert f.reads==0
  if local[name]!={'module.py':sha(b'original')}:raise ValueError('synthetic inventory drift')
 for name in ['actual','runtime_after']:
  for kind in ['same','added','deleted','bytes','linked']:probe(f'{name}-safe-inventory-{kind}',lambda k=kind,n=name:inventory(k,n),kind=='same')
 names=('contextbase.ai.capsule','contextbase.ai.workflow','contextbase.ai.provider','contextbase.ai.prompts','contextbase.ai.schemas','contextbase.ai.validation')
 function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='runtime_import_pin')
 def imports(kind):
  runtime=Path('C:/synthetic/freeze');expected={n:str(runtime/('/'.join(n.split('.'))+'.py')) for n in names}
  receipt={n:p for n,p in expected.items() if n!='contextbase.ai.capsule'}
  receipt.update({f'contextbase.other{i}':str(runtime/f'contextbase/other{i}.py') for i in range(8)})
  loaded=expected.copy();resolved=receipt.copy();files={'/'.join(n.split('.'))+'.py':'a'*64 for n in names}
  if kind=='loaded-other-file':loaded[names[0]]=str(runtime/'contextbase/ai/other.py')
  elif kind=='loaded-other-freeze':loaded[names[1]]='C:/synthetic/outside/workflow.py'
  elif kind=='resolved-drift':resolved[names[2]]=str(runtime/'other.py')
  elif kind=='receipt-drift':receipt[names[3]]=str(runtime/'other.py');resolved=receipt.copy()
  elif kind=='missing-capsule':files.pop('contextbase/ai/capsule.py')
  library=SimpleNamespace(import_module=lambda n:SimpleNamespace(__file__=loaded[n]),util=SimpleNamespace(find_spec=lambda n:SimpleNamespace(origin=resolved[n])))
  local={'runtime':runtime,'Path':Path,'critical_module_names':names,'freeze':{'imports':receipt,'files':files},'capsule':SimpleNamespace(safe_path=lambda p:p),'importlib':library}
  run(local,[function]);answer=local['runtime_import_pin']();assert len(answer['actualCriticalImports'])==6 and len(answer['allResolvedFrozenImports'])==13
 for kind in ['correct','loaded-other-file','loaded-other-freeze','resolved-drift','receipt-drift','missing-capsule']:probe('actual-six-plus-resolved-thirteen-'+kind,lambda k=kind:imports(k),kind=='correct')
 def boundary(kind):
  root=Path('C:/synthetic/source-only');receipt=Path('C:/synthetic/report/runtime-code-source-07.json')
  local={'Path':Path,'capsule':SimpleNamespace(safe_path=lambda p:p),'approved_base':root,'approved_receipts':{receipt},'repo':Path('C:/synthetic/repo'),'original_root':Path('C:/synthetic/repo/test-project1/srcs/CSharp_ASPNET'),'runtime':root/'runtime-code/source-07/src','runtime_receipt_sha256':RECEIPT,'args':SimpleNamespace(runtime_receipt=receipt,document=[Path('correct.md')],document_sha256=['a'*64]),'expected_document':Path('correct.md')}
  node=guard('fixed authorized SHA')
  if kind=='receiptSHA':local['runtime_receipt_sha256']='a'*64
  elif kind=='receiptPath':local['args'].runtime_receipt=Path('C:/synthetic/assisted/receipt.json');node=guard('approved source-only freeze')
  elif kind=='destination':local['runtime']=root/'runtime-code/source-06/src';node=guard('fixed frozen source06 root')
  elif kind=='sourceRoot':local['original_root']=Path('C:/synthetic/othermode/source');node=guard('approved original source root')
  elif kind=='count':local['args'].document.append(Path('second.md'));node=guard('explicit caller SHA pin')
  elif kind=='exact-parent':local['args'].document=[Path('other-revision.md')];node=guard('exact reviewed search-basic-08 canonical path')
  run(local,[node])
 for kind in ['correct','receiptSHA','receiptPath','destination','sourceRoot','count','exact-parent']:probe('fixed-role-boundary-'+kind,lambda k=kind:boundary(k),kind=='correct')
 def placement():
  provider=one_assign('answer').lineno
  assert capguards[0].lineno<provider<capguards[1].lineno
  assert one_assign('runtime_imports_before').lineno<provider
  assert guard('actual frozen imports changed').lineno>provider
  assert one_assign('original_before').lineno<provider<one_assign('original_after').lineno
  for name in ['original_before','original_after']:
   assert 'capsule.safe_path' in ast.unparse(one_assign(name))
  assert guard('approved canonical review bytes changed').lineno>provider
  assert guard('runtime receipt changed during execution').lineno>provider
  assert 'runtime_after != actual' in ast.unparse(guard('allowed original source or frozen runtime changed'))
  assert {'88d5648ed3a75abf50e4cea695079c6ba517436dd744366915f1db06795d9307','94477aa19ff7648ad1043c7314bca996d53c009f1a5db56cc6d8f5937af6b035','5ceb2c96b24f2283dae150a4640ab9d98dbad465eaa86c5a57acac023a70c8de'}<=set(n.value for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,str))
 probe('exact-parent-review-pins-and-before-after-placement',placement)
 assert all(c['pass'] for c in cases)
 report={'schema':'reverse-agent-independent-state-helper-delta/1','createdUtc':datetime.now(timezone.utc).isoformat(),'status':'PASS_MECHANICAL_DELTA_ONLY',
  'helpers':[{'path':str(SOURCE/n),'sha256':p} for n,p in PINS.items()],'cases':cases,'casesPassed':len(cases),'providerCalls':0,'wholeHelperImportedOrExecuted':False,
  'productionDataRead':False,'originalSourceSpecSpecEvalOtherModeBusinessRead':False,'syntheticMetadataOnly':True,
  'fixedCapsuleBeforeVerifyAndBeforeAfterAi':True,'runtimeAndOriginalPerFileSafePathBeforeRead':True,'actualCriticalSixAndAllResolvedThirteenExactFiles':True,
  'schemaAndExistingEightFunctionsUnchanged':True,'requiresNativeAndMeaningReview':True,'completeHtmlInertnessProven':False,
  'remaining':['The current candidate is bound to source07/basic08; a future source08 freeze requires a fresh helper and separate pin delta.',
               'This audit does not authorize provider execution or assert meaning/native/runtime/formal quality.']}
 path=out/'review.json';path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 assert all(sha((SOURCE/n).read_bytes())==pin for n,pin in PINS.items())
 print(json.dumps({'report':str(path),'sha256':sha(path.read_bytes()),'passed':len(cases),'providerCalls':0},ensure_ascii=False))
if __name__=='__main__':main()
