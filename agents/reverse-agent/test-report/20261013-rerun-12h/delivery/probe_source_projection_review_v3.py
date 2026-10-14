"""AST-selected v1-to-v3 mechanical delta, synthetic metadata only, no provider/import."""
from __future__ import annotations
import ast,copy,hashlib,json
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent;SOURCE=HERE.parent/'source-pilot'
PINS={'review_state_projection.py':'c9d0d3afdbc3af98cebdcc2bf50c768022ba661d03f63922fb23231bbd7070a9','review_state_projection_v2.py':'9b53eeb880003deba2a2cabc93dc33f4b879f2944357f524f39e2ec6b2259c7f','review_state_projection_v3.py':'789e59b5c42768f65e2f3ee46d252ab38f8012f91862e2b196ebb71042de414f'}
def sha(b):return hashlib.sha256(b).hexdigest()
def run(ns,nodes):exec(compile(ast.Module(body=nodes,type_ignores=[]),'<synthetic-ast-only>','exec'),ns)
def main():
 out=HERE/'state-review-helper-independent-r03';out.mkdir(exist_ok=False);trees={};cases=[]
 for name,pin in PINS.items():
  raw=(SOURCE/name).read_bytes();assert sha(raw)==pin;trees[name]=ast.parse(raw.decode('utf8'))
 tree=trees['review_state_projection_v3.py'];manifest_sha='2f64e2211b1fcd7850203927fc75b5a7f2ce37457cc2afe88c8065d9f931273b'
 def probe(name,fn,accept):
  try:fn();actual=True;err=None
  except Exception as exc:actual=False;err=type(exc).__name__+': '+str(exc)
  cases.append({'case':name,'expectedAccept':accept,'actualAccept':actual,'pass':accept==actual,'error':err})
 fixed=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='assert_fixed_capsule')
 def capsule_case(kind):
  value={'digest':manifest_sha};state={'manifestSha256':manifest_sha}
  if kind=='bytes':value['digest']='b'*64
  elif kind=='state':state['manifestSha256']='b'*64
  elif kind=='missing':state={}
  ns={'capsule':SimpleNamespace(material_path=lambda *a:SimpleNamespace(read_bytes=lambda:b'synthetic'),sha256=lambda b:value['digest']),'manifest_sha':manifest_sha}
  run(ns,[fixed]);ns['assert_fixed_capsule'](Path('C:/synthetic/snapshot'),None if kind=='before-collection' else state)
 for kind in ['correct','before-collection','bytes','state','missing']:probe('fixed-capsule-'+kind,lambda k=kind:capsule_case(k),kind in ['correct','before-collection'])
 inventory=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='inventory')
 class File:
  parts=('synthetic','module.py');suffix='.py'
  def __init__(self,name,data,linked=False):self.name=name;self.data=data;self.linked=linked
  def relative_to(self,r):return Path(self.name)
  def is_file(self):return True
  def read_bytes(self):return self.data
 def inventory_case(kind):
  files=[File('module.py',b'original',kind=='linked')];calls=[]
  if kind=='added':files.append(File('added.py',b'new'))
  elif kind=='deleted':files=[]
  elif kind=='bytes':files[0].data=b'drift'
  def safe(p):
   calls.append(p)
   if p.linked:raise ValueError('synthetic linked/reparse file rejected')
   return p
  ns={'runtime':SimpleNamespace(rglob=lambda p:list(files)),'capsule':SimpleNamespace(safe_path=safe,sha256=sha)};run(ns,[inventory])
  if ns['inventory']()!={'module.py':sha(b'original')}:raise ValueError('inventory differs')
  assert len(calls)==1
 for kind in ['same','added','deleted','bytes','linked']:probe('runtime-inventory-'+kind,lambda k=kind:inventory_case(k),kind=='same')
 names=('contextbase.ai.capsule','contextbase.ai.workflow','contextbase.ai.provider','contextbase.ai.prompts','contextbase.ai.schemas','contextbase.ai.validation');runtime=Path('C:/synthetic/freeze')
 def assign_name(n,name):return isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets)
 expected_assignment=next(n for n in tree.body if assign_name(n,'expected_critical_imports'))
 expected_loop=next(n for n in tree.body if isinstance(n,ast.For) and ast.unparse(n.iter)=='critical_module_names')
 import_guard=next(n for n in tree.body if isinstance(n,ast.If) and 'actual critical or all resolved' in ast.unparse(n))
 def imports_case(kind):
  expected={n:str(runtime/('/'.join(n.split('.'))+'.py')) for n in names}
  freeze={'imports':{n:p for n,p in expected.items() if n!='contextbase.ai.capsule'},'files':{'/'.join(n.split('.'))+'.py':'a'*64 for n in names}}
  freeze['imports']['contextbase.ai.other']=str(runtime/'contextbase/ai/other.py')
  loaded=expected.copy();resolved=freeze['imports'].copy()
  if kind=='loaded-other-file':loaded[names[0]]=str(runtime/'contextbase/ai/other.py')
  elif kind=='loaded-other-freeze':loaded[names[1]]=str(Path('C:/synthetic/other')/'contextbase/ai/workflow.py')
  elif kind=='resolved-other-file':resolved[names[2]]=str(runtime/'other.py')
  elif kind=='receipt-other-file':freeze['imports'][names[3]]=str(runtime/'other.py');resolved=freeze['imports'].copy()
  elif kind=='missing-inventory':freeze['files'].pop('contextbase/ai/capsule.py')
  ns={'critical_module_names':names,'runtime':runtime,'freeze':freeze,'capsule':SimpleNamespace(safe_path=lambda p:p),'critical_imports':loaded,'all_resolved_imports':resolved}
  run(ns,[expected_assignment,expected_loop,import_guard])
 for kind in ['correct','loaded-other-file','loaded-other-freeze','resolved-other-file','receipt-other-file','missing-inventory']:probe('actual-module-provenance-'+kind,lambda k=kind:imports_case(k),kind=='correct')
 provider_line=next(n.lineno for n in tree.body if isinstance(n,ast.Assign) and 'workflow._bound_job' in ast.unparse(n))
 def placement():
  calls=[n for n in tree.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and ast.unparse(n.value.func)=='assert_fixed_capsule']
  assert len(calls)==4 and any(n.lineno<provider_line and len(n.value.args)==2 for n in calls) and any(n.lineno>provider_line and len(n.value.args)==2 for n in calls)
  check=next(n for n in tree.body if isinstance(n,ast.If) and 'fixed review inputs/source/runtime/helper changed' in ast.unparse(n))
  assert check.lineno>provider_line and 'critical_imports_after != critical_imports' in ast.unparse(check) and 'all_resolved_imports_after != all_resolved_imports' in ast.unparse(check) and "inventory() != freeze['files']" in ast.unparse(check)
 probe('before-after-fixed-cap-full-inventory-exact-import-check-placement',placement,True)
 def unchanged_schema():
  wanted={'ref_schema','location_schema','state_schema','finding_schema','schema'}
  schemas=lambda t:[ast.dump(n,include_attributes=False) for n in t.body if isinstance(n,ast.Assign) and any(isinstance(a,ast.Name) and a.id in wanted for a in n.targets)]
  assert schemas(tree)==schemas(trees['review_state_projection.py'])
 probe('review-schema-unchanged-from-typed-transport-verified-v1',unchanged_schema,True)
 assert all(c['pass'] for c in cases)
 report={'schema':'reverse-agent-independent-state-review-delta/1','createdUtc':datetime.now(timezone.utc).isoformat(),'status':'PASS_MECHANICAL_DELTA_ONLY','helpers':[{'path':str(SOURCE/n),'sha256':p} for n,p in PINS.items()],'cases':cases,'casesPassed':sum(c['pass'] for c in cases),'providerCalls':0,'productionDataRead':False,'sourceOrOriginalSpecOrSpecEvalOrOtherModeBusinessRead':False,'wholeHelperImportedOrExecuted':False,'fixedCapsuleBytesAndCollectedStateRechecked':True,'runtimeInventoryPerFileSafePath':True,'criticalSixActualLoadedPathsExactInventoryFiles':True,'allReceiptResolvedImportsExactBeforeAfter':True,'remaining':['Meaning/visual/runtime/formal evaluation are separate and were not performed.','Synthetic audit covers the changed guards and does not prove HTML completely inert.']}
 path=out/'review.json';path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 assert all(sha((SOURCE/n).read_bytes())==p for n,p in PINS.items())
 print(json.dumps({'report':str(path),'sha256':sha(path.read_bytes()),'passed':len(cases),'providerCalls':0},ensure_ascii=False))
if __name__=='__main__':main()
