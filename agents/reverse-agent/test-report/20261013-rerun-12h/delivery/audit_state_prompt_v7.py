"""AST-only prompt delta; never imports or executes the production helper."""
from pathlib import Path
from datetime import datetime,timezone
import ast,copy,hashlib,json
HERE=Path(__file__).resolve().parent
BASE=HERE.parents[4]/'agents/reverse-agent/.tmp/20261013-rerun-12h/training-assisted'
expected={'run_state_projection_v6.py':'dea405e860904d3cff89a1de675a5c8b0270d24bad76f9005c90518f140ca78f',
 'run_state_projection_v7.py':'cd01ce3486a00f7787779acdf0cd16dec442262d6d43996806e776b08af14295'}
trees={}
for name,sha in expected.items():
 data=(BASE/name).read_bytes();assert hashlib.sha256(data).hexdigest()==sha
 trees[name]=ast.parse(data.decode('utf8'))
old,new=[trees[name] for name in expected]
main=next(node for node in new.body if isinstance(node,ast.FunctionDef) and node.name=='main')
added=[]
for node in ast.walk(main):
 if not isinstance(node,ast.Assign) or len(node.targets)!=1 or not isinstance(node.targets[0],ast.Name):continue
 name=node.targets[0].id
 if name=='absolute_boundary':added.append(node)
 elif (name in {'prompt','review_prompt'} and isinstance(node.value,ast.BinOp) and isinstance(node.value.op,ast.Add)
   and isinstance(node.value.left,ast.Name) and node.value.left.id=='absolute_boundary' and isinstance(node.value.right,ast.Name)
   and node.value.right.id==name):added.append(node)
assert len(added)==3
class Strip(ast.NodeTransformer):
 def visit_Assign(self,node):
  if any(ast.dump(node)==ast.dump(extra) for extra in added):return None
  return node
stripped=Strip().visit(copy.deepcopy(new))
assert ast.dump(old,include_attributes=False)==ast.dump(stripped,include_attributes=False)
prefix=next(node for node in added if node.targets[0].id=='absolute_boundary')
assert isinstance(prefix.value,ast.Constant) and isinstance(prefix.value.value,str)
for text in ['snapshot','絶対パス','相対パス','`.`','作業ディレクトリ','snapshot外ファイル名','列挙は禁止']:
 assert text in prefix.value.value
env={'prompt':'SYNTHETIC-PROJECTION','review_prompt':'SYNTHETIC-REVIEW'}
ordered=[prefix]+[node for node in added if node is not prefix]
exec(compile(ast.Module(body=ordered,type_ignores=[]),'<synthetic prompt assignments>','exec'),env)
assert env['prompt']==prefix.value.value+'SYNTHETIC-PROJECTION'
assert env['review_prompt']==prefix.value.value+'SYNTHETIC-REVIEW'
report={'schema':'independent-code-only-delta/1','createdUtc':datetime.now(timezone.utc).isoformat(),
 'status':'PASS_PROMPT_ONLY_AST_DELTA','helperSha256':expected['run_state_projection_v7.py'],
 'basisSha256':expected['run_state_projection_v6.py'],'checks':{'onlyThreeAssignmentsAdded':True,
 'allOtherAstIdentical':True,'schemasGatesGuardsControlFlowUnchanged':True,'projectionPrefixExact':True,
 'reviewPrefixExact':True,'absoluteSnapshotConstraintExplicit':True},'productionDataRead':False,
 'providerCalls':0,'helperImportedOrMainExecuted':False,'limits':['Code-only technical prompt delta; no guarantee of actual provider adherence or meaning/native approval.']}
out=HERE/'state-prompt-v7-independent.json';assert not out.exists()
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'path':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'status':report['status']},ensure_ascii=False))
