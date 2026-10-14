"""AST-selected module provenance delta; fake paths/modules only, no provider or production input."""
import ast,copy,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
from types import SimpleNamespace
R=Path(__file__).parent;BASE=R.parents[4]/'agents/reverse-agent/.tmp/20261013-rerun-12h/training-assisted'
PINS={'run_state_projection_v5.py':'193efe246ed770392cfbd1d4cedd547c2196d740d55ced76953075300df3c84b','run_state_projection_v6.py':'dea405e860904d3cff89a1de675a5c8b0270d24bad76f9005c90518f140ca78f'}
def sha(b):return hashlib.sha256(b).hexdigest()
def run(ns,nodes):exec(compile(ast.Module(body=copy.deepcopy(nodes),type_ignores=[]),'<AST-selected-synthetic-only>','exec'),ns)
def assign(n,name):return isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets)
def main():
 out=R/'state-helper-independent-assisted-v6';out.mkdir(exist_ok=False);trees={};cases=[]
 for n,p in PINS.items():
  raw=(BASE/n).read_bytes();assert sha(raw)==p;trees[n]=ast.parse(raw.decode('utf8'))
 tree=trees['run_state_projection_v6.py'];before=trees['run_state_projection_v5.py'];ns={'Path':Path}
 constants=[next(n for n in tree.body if assign(n,name)) for name in ['CRITICAL_MODULE_PATHS','RECEIPT_IMPORT_PATHS']];run(ns,constants)
 critical=ns['CRITICAL_MODULE_PATHS'];receipt=ns['RECEIPT_IMPORT_PATHS']
 assert len(critical)==6 and len(receipt)==13 and set(critical)=={'contextbase.ai.'+n for n in ['capsule','schemas','workflow','provider','prompts','validation']}
 function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='runtime_module_pins')
 def probe(name,fn,accept=True):
  try:fn();actual=True;err=None
  except Exception as e:actual=False;err=type(e).__name__+': '+str(e)
  cases.append({'case':name,'expectedAccept':accept,'actualAccept':actual,'pass':accept==actual,'error':err})
 def module_case(kind,name=None):
  directory=Path('C:/synthetic/freeze');expected={n:directory/p for n,p in {**receipt,**critical}.items()};files={p:'a'*64 for p in {**receipt,**critical}.values()}
  runtime={'imports':{n:str(expected[n]) for n in receipt},'files':files};modules={n:SimpleNamespace(__file__=str(expected[n]),__spec__=SimpleNamespace(origin=str(expected[n]))) for n in critical}
  resolved={n:SimpleNamespace(origin=str(expected[n])) for n in expected};digests={str(p):'a'*64 for p in expected.values()};linked=set();reads=[]
  n=name or 'contextbase.ai.capsule';wrong=str(directory/'contextbase/ai/unexpected.py')
  if kind=='loaded-file':modules[n].__file__=wrong
  elif kind=='loaded-spec':modules[n].__spec__.origin=wrong
  elif kind=='module-byte':digests[str(expected[n])]='b'*64
  elif kind=='resolved-file':resolved[n].origin=wrong
  elif kind=='outside-loaded':modules[n].__file__='C:/synthetic/outside/module.py'
  elif kind=='missing-loaded':modules.pop(n)
  elif kind=='missing-spec':modules[n].__spec__=None
  elif kind=='missing-origin':resolved[n].origin=None
  elif kind=='missing-resolution':resolved[n]=None
  elif kind=='receipt-missing':runtime['imports'].pop('specgen')
  elif kind=='receipt-extra':runtime['imports']['extra.module']=wrong
  elif kind=='receipt-file':runtime['imports']['contextbase.ai.schemas']=wrong
  elif kind=='missing-inventory':runtime['files'].pop(critical[n])
  elif kind=='linked-path':linked.add(str(expected[n]))
  def safe(p):
   if str(p) in linked:raise ValueError('synthetic reparse path refused')
   return p
  def digest(p):reads.append(str(p));return digests[str(p)]
  local={**ns,'Path':Path,'capsule':SimpleNamespace(safe_path=safe),'sys':SimpleNamespace(modules=modules),'import_util':SimpleNamespace(find_spec=lambda n:resolved[n]),'sha':digest}
  run(local,[function])
  try:result=local['runtime_module_pins'](directory,runtime)
  finally:
   if kind=='linked-path':assert str(expected[n]) not in reads
  assert len(result['criticalLoadedModules'])==6 and len(result['receiptFindSpec'])==13
 probe('exact-six-loaded-and-thirteen-resolved-positive',lambda:module_case('correct'))
 for name in critical:
  for kind in ['loaded-file','loaded-spec','module-byte']:probe(name+'-'+kind,lambda n=name,k=kind:module_case(k,n),False)
 for name in receipt:probe(name+'-resolved-file',lambda n=name:module_case('resolved-file',n),False)
 for kind in ['outside-loaded','missing-loaded','missing-spec','missing-origin','missing-resolution','receipt-missing','receipt-extra','receipt-file','missing-inventory','linked-path']:
  probe('module-provenance-'+kind,lambda k=kind:module_case(k),False)
 def unchanged_parts():
  old={n.name:ast.dump(n,include_attributes=False) for n in before.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
  new={n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
  assert set(new)-set(old)=={'runtime_module_pins'}
  assert {n for n in old if old[n]!=new[n]}=={'input_pins','assert_unchanged','main'}
  names={'STRING','INTEGER','LOCATION','REFERENCE','STATE','PROJECTION','FINDING','REVIEW','BOOLEAN_ATTRIBUTES','MODE','SCOPE','STATE_IDS','MANIFEST_SHA','CONTRACT_SHA','PLAN_SHA','GATES_SHA','RUNTIME_RECORD_SHA'}
  values=lambda t:{ast.unparse(n.targets[0]):ast.dump(n,include_attributes=False) for n in t.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in names}
  assert values(before)==values(tree)
  inputfn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='input_pins')
  assert "runtime_module_pins(directory, runtime)" in ast.unparse(inputfn) and "'runtimeModulePins': module_pins" in ast.unparse(inputfn)
  mainfn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
  text=ast.unparse(mainfn);assert "'runtimeModulePins'" in text and text.index('input_pins(args)')<text.index('workflow._bound_job')
  assert 'finally:' in text and 'assert_unchanged(metadata)' in text[text.index('finally:'):]
 probe('unchanged-pins-schemas-html-controls-plus-preflight-metadata-finally-placement',unchanged_parts)
 unchanged=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='assert_unchanged')
 new_guard=next(n for n in unchanged.body if isinstance(n,ast.If) and 'module resolution' in ast.unparse(n))
 def recheck(kind):
  fixed={'receiptFindSpec':{'x':{'path':'C:/synthetic/module.py','sha256':'a'*64}},'criticalLoadedModules':{}}
  actual=copy.deepcopy(fixed)
  if kind=='drift':actual['receiptFindSpec']['x']['path']='C:/synthetic/other.py'
  metadata={'runtimeInventory':{'directory':'C:/synthetic/freeze'},'runtimeModulePins':fixed}
  run({'Path':Path,'metadata':metadata,'runtime_module_pins':lambda *a:actual,'load':lambda p:{},'RUNTIME_RECORD':Path('C:/synthetic/receipt.json')},[new_guard])
 probe('module-recapture-after-ai-positive',lambda:recheck('same'))
 probe('module-recapture-after-ai-drift-rejected',lambda:recheck('drift'),False)
 assert all(c['pass'] for c in cases)
 report={'schema':'reverse-agent-independent-module-provenance-delta/1','createdUtc':datetime.now(timezone.utc).isoformat(),'status':'PASS_MECHANICAL_DELTA_ONLY','helpers':[{'path':str(BASE/n),'sha256':p} for n,p in PINS.items()],
  'cases':cases,'casesPassed':len(cases),'priorSameFreezeUnexpectedLoadedFileGapClosed':True,'criticalSixExactLoadedFileSpecResolutionAndHash':True,'thirteenReceiptModulesExactNameFileResolutionAndHash':True,
  'capsuleSchemasIncluded':True,'preflightMetadataAndAfterAiRecapturePresent':True,'schemasModeCapRuntimeParentControlLogicUnchanged':True,
  'providerCalls':0,'wholeHelperImportedOrExecuted':False,'productionDataRead':False,'originalSourceSpecSpecEvalOtherModeBusinessRead':False,
  'remaining':['No complete in-memory/race-free or HTML inertness proof is asserted.','Provider invocation, semantic review, native image QA, original application runtime and formal quality are separate.']}
 p=out/'review.json';p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 assert all(sha((BASE/n).read_bytes())==pin for n,pin in PINS.items())
 print(json.dumps({'report':str(p),'sha256':sha(p.read_bytes()),'passed':len(cases),'providerCalls':0},ensure_ascii=False))
if __name__=='__main__':main()
