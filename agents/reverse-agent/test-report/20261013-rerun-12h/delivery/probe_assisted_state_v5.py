"""Read-only AST delta of runtime04-to06 pins with synthetic guard executions."""
from __future__ import annotations
import ast,copy,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
from types import SimpleNamespace
HERE=Path(__file__).parent;REPO=HERE.parents[4];BASE=REPO/'agents/reverse-agent/.tmp/20261013-rerun-12h/training-assisted'
PINS={'run_state_projection_v4.py':'e94820ea65bb2734be542f090946525e5bd1e3fdf8d1967a3aa38ab1be9d2f4b','run_state_projection_v5.py':'193efe246ed770392cfbd1d4cedd547c2196d740d55ced76953075300df3c84b'}
RECEIPT='9ef12bc2f6412bddfd9f4d8de45d25f9e5eff1ab31402808d97023aaf6a846e3'
DELTA={'runtime-code-assisted-04.json':'runtime-code-assisted-06.json','dc98d83b3f4be42514664c17e35b90cbd4439ec355ae3fdb9784de85b93b337e':RECEIPT,'runtime-code/assisted-04/src':'runtime-code/assisted-06/src','r11':'r14','Frozen runtime destination leaves the fixed assisted-04 scope':'Frozen runtime destination leaves the fixed assisted-06 scope'}
def sha(b):return hashlib.sha256(b).hexdigest()
def run(ns,nodes):exec(compile(ast.Module(body=copy.deepcopy(nodes),type_ignores=[]),'<AST-selected-synthetic-only>','exec'),ns)
def main():
 out=HERE/'state-helper-independent-assisted-v5';out.mkdir(exist_ok=False);trees={};cases=[]
 for n,p in PINS.items():
  raw=(BASE/n).read_bytes();assert sha(raw)==p;trees[n]=ast.parse(raw.decode('utf8'))
 tree=trees['run_state_projection_v5.py'];prior=copy.deepcopy(trees['run_state_projection_v4.py']);changes=[]
 class Update(ast.NodeTransformer):
  def visit_Constant(self,node):
   if isinstance(node.value,str) and node.value in DELTA:
    changes.append({'line':node.lineno,'before':node.value,'after':DELTA[node.value]});node.value=DELTA[node.value]
   return node
 Update().visit(prior)
 assert ast.dump(prior,include_attributes=False)==ast.dump(tree,include_attributes=False)
 assert len(changes)==5
 def probe(name,fn,accept=True):
  try:fn();actual=True;err=None
  except Exception as e:actual=False;err=type(e).__name__+': '+str(e)
  cases.append({'case':name,'expectedAccept':accept,'actualAccept':actual,'pass':accept==actual,'error':err})
 input_fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='input_pins')
 changed_guard=next(n for n in input_fn.body if isinstance(n,ast.If) and 'Explicit assisted runtime receipt required' in ast.unparse(n))
 destination_guard=next(n for n in input_fn.body if isinstance(n,ast.If) and 'fixed assisted-06 scope' in ast.unparse(n))
 record=Path('C:/synthetic/report/runtime-code-assisted-06.json');directory=Path('C:/synthetic/base/runtime-code/assisted-06/src')
 def runtime_case(kind):
  local={'capsule':SimpleNamespace(safe_path=lambda p:p),'RUNTIME_RECORD':record,'RUNTIME_RECORD_SHA':RECEIPT,'runtime_record':record,'sha':lambda p:RECEIPT,
      'args':SimpleNamespace(runtime_label='r14'),'RUNTIME_DIRECTORY':directory,'directory':directory}
  node=changed_guard
  if kind=='old-label':local['args'].runtime_label='r11'
  elif kind=='old-record':local['runtime_record']=Path('C:/synthetic/report/runtime-code-assisted-04.json')
  elif kind=='wrong-SHA':local['sha']=lambda p:'a'*64
  elif kind=='old-destination':local['directory']=Path('C:/synthetic/base/runtime-code/assisted-04/src');node=destination_guard
  elif kind=='other-mode':local['directory']=Path('C:/synthetic/source-only/runtime-code/source-08/src');node=destination_guard
  run(local,[node])
 for kind in ['correct','old-label','old-record','wrong-SHA','old-destination','other-mode']:probe('new-runtime-fixed-pin-'+kind,lambda k=kind:runtime_case(k),kind=='correct')
 unchanged=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='assert_unchanged')
 def after_case(kind):
  snapshot=Path('C:/synthetic/snapshot');cap='e76a6c40e8927011fff9145d5f5ab2fa94ad89acefc9a03bbad0cbf09b85a0e7';state={'manifestSha256':cap,'mode':'training-assisted'}
  known=Path('C:/synthetic/parent.md');hashes={str(snapshot/'manifest.json'):cap,str(record):RECEIPT,str(known):'b'*64};files={'module.py':'c'*64};metadata={'capsule':state,'pinnedFiles':{str(known):'b'*64},'runtimeInventory':{'directory':str(directory),'files':files.copy()}}
  if kind=='runtime-added':files['added.py']='d'*64
  elif kind=='runtime-deleted':files.clear()
  elif kind=='runtime-byte':files['module.py']='e'*64
  elif kind=='parent-drift':hashes[str(known)]='d'*64
  elif kind=='receipt-drift':hashes[str(record)]='a'*64
  elif kind=='cap-drift':hashes[str(snapshot/'manifest.json')]='a'*64
  elif kind=='state-drift':state={**state,'changed':True}
  local={'Path':Path,'SNAPSHOT':snapshot,'MANIFEST_SHA':cap,'RUNTIME_RECORD':record,'RUNTIME_RECORD_SHA':RECEIPT,
      'capsule':SimpleNamespace(safe_path=lambda p:p,verification_state=lambda p:state),'sha':lambda p:hashes[str(p)],'runtime_inventory':lambda p:files}
  run(local,[unchanged]);local['assert_unchanged'](metadata)
 for kind in ['correct','runtime-added','runtime-deleted','runtime-byte','parent-drift','receipt-drift','cap-drift','state-drift']:probe('unchanged-before-final-write-'+kind,lambda k=kind:after_case(k),kind=='correct')
 probe('complete-AST-only-five-authorized-runtime-constants-change',lambda:None)
 assert all(c['pass'] for c in cases)
 # Existing provenance limitation: containment checks four modules, not six exact inventoried paths.
 import_guard=next(n for n in input_fn.body if isinstance(n,ast.If) and 'Actual imports must belong' in ast.unparse(n))
 imports={name:str(directory/'contextbase/ai/unexpected.py') for name in ['contextbase.ai.workflow','contextbase.ai.validation','contextbase.ai.prompts','contextbase.ai.provider']}
 run({'Path':Path,'directory':directory,'imports':imports},[import_guard])
 limitation={'introducedByV5':False,'reproduction':'Existing loaded-module containment check accepts four same-freeze unexpected.py __file__ paths. It does not independently enforce six critical exact inventoried files as source v6 does. The entire v4/v5 AST is unchanged except the five runtime pin constants.','syntheticGuardAccepted':True,'wholeHelperOrProviderExecuted':False}
 report={'schema':'reverse-agent-independent-runtime-pin-delta/1','createdUtc':datetime.now(timezone.utc).isoformat(),'status':'PASS_RUNTIME06_DELTA_ONLY',
  'helpers':[{'path':str(BASE/n),'sha256':p} for n,p in PINS.items()],'literalChanges':changes,'fullAstEquivalentAfterFiveAuthorizedConstantChanges':True,
  'schemasFunctionsNeutralGatesAndControlFlowUnchanged':True,'cases':cases,'casesPassed':len(cases),'providerCalls':0,'wholeHelperImportedOrExecuted':False,
  'productionDataRead':False,'originalSourceSpecSpecEvalOtherModeBusinessRead':False,'existingProvenanceLimitation':limitation,
  'remaining':['This delta does not establish six-critical exact-loaded-module provenance; retained containment is a prior limitation for parent to assess.',
   'Meaning, native state QA, original application runtime, and formal quality are separate.']}
 p=out/'review.json';p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 assert all(sha((BASE/n).read_bytes())==v for n,v in PINS.items())
 print(json.dumps({'report':str(p),'sha256':sha(p.read_bytes()),'casesPassed':len(cases),'providerCalls':0,'existingLimitationReproduced':True},ensure_ascii=False))
if __name__=='__main__':main()
