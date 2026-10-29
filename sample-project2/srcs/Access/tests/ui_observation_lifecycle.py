"""Exercise failed-observation invalidation without Office or a product DB.

Only the measurement body is replaced with a deterministic exception in memory;
the real entry-point RUNNING/except FAILED and atomic writer execute unchanged
against a private test folder. No canonical observation/product is changed.
"""
from pathlib import Path
import ast,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 source=ROOT/'tests/ui_observe.py'; fixture=ROOT/'.tmp/ui-observer-lifecycle'
 target=fixture/'build/test-results/ui-observations.json'; target.parent.mkdir(parents=True,exist_ok=True)
 target.write_text(json.dumps({'status':'PASS','obsolete':'old-complete-observation','components':[{'id':'old'}],'observations':[{'ruleId':'old'}]}),encoding='utf-8')
 tree=ast.parse(source.read_text(encoding='utf-8'))
 probe=ast.parse('''
seen=json.loads((ROOT/'build/test-results/ui-observations.json').read_text(encoding='utf-8'))
assert seen['status']=='RUNNING'
assert seen['components']==[] and seen['observations']==[]
raise RuntimeError('Expected isolated observer failure')
''').body
 for node in tree.body:
  if isinstance(node,ast.FunctionDef) and node.name=='main': node.body=probe
 # Retain all actual imports/functions/error handling; redirect its output root
 # immediately before the actual __main__ branch runs.
 index=next(i for i,n in enumerate(tree.body) if isinstance(n,ast.If) and '__name__' in ast.unparse(n.test))
 tree.body.insert(index,ast.parse('ROOT=Path('+repr(str(fixture))+')').body[0]); ast.fix_missing_locations(tree)
 previous=sys.argv; sys.argv=[str(source),'--run-id','observer-failure-regression']
 caught=False
 try:
  exec(compile(tree,str(source),'exec'),{'__name__':'__main__','__file__':str(source)})
 except RuntimeError as error:
  caught=str(error)=='Expected isolated observer failure'
 finally: sys.argv=previous
 after=json.loads(target.read_text(encoding='utf-8'))
 checks=[{'id':'current-running-invalidated-before-body','passed':caught},
  {'id':'failure-persists-incomplete-state','passed':after.get('status')=='FAILED' and after.get('components')==[] and after.get('observations')==[]},
  {'id':'old-complete-observation-removed','passed':'obsolete' not in after}]
 okay=all(c['passed'] for c in checks)
 record={'status':'PASS' if okay else 'FAIL','artifactSha256':sha(ROOT/'build/CareerManagement.accdb'),
  'measurementSourceSha256':sha(source),'testSourceSha256':sha(Path(__file__)),'checks':checks,
  'scope':'Observation entry-point failure lifecycle only; in-memory AST replaces the expensive measurement body. Real writer and RUNNING/FAILED branches run on an isolated output root. No Office/product execution or keyboard proof.','formalScore':None}
 (ROOT/'build/test-results/ui-observation-lifecycle.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'status':record['status'],'checks':len(checks)})); return int(not okay)
if __name__=='__main__': raise SystemExit(main())
