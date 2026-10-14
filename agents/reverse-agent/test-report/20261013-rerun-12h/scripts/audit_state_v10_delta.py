"""Check the conditional initial-vs-repair prompt delta, without running a provider."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import copy
import hashlib
import json

report = Path(__file__).resolve().parents[1]
base = report.parents[1]/'.tmp/20261013-rerun-12h/training-assisted'
old = base/'run_state_projection_v9.py'
new = base/'run_state_projection_v10.py'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(old) == '98cdfa4952b0afde0d1bab51a0fda1d228b368e51d7c8bdb9669c082838c637a'
assert sha(new) == '2d09399582e217b6082e34fa4d361aa9add0526818386701a716b114b13be8d5'
old_tree,new_tree = [ast.parse(p.read_text(encoding='utf-8')) for p in (old,new)]
main = next(n for n in new_tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
changed = [n for n in main.body if isinstance(n,ast.Assign) and isinstance(n.value,ast.BinOp)
           and any(isinstance(x,ast.IfExp) for x in ast.walk(n.value))]
assert len(changed)==1
expr = changed[0].value
conditional = next(n for n in ast.walk(expr) if isinstance(n,ast.IfExp))
assert ast.unparse(conditional) == "repair_directive if previous_answer is not None else ''"
original = copy.deepcopy(expr)
class Restore(ast.NodeTransformer):
    def visit_IfExp(self,node):
        return ast.Name(id='repair_directive',ctx=ast.Load())
changed[0].value = Restore().visit(expr)
assert ast.dump(new_tree,include_attributes=False)==ast.dump(old_tree,include_attributes=False)
compiled = compile(ast.fix_missing_locations(ast.Expression(original)),'<technical-prompt-delta>','eval')
checks=[]
for name,previous,expected in (
    ('initial-no-old-projection',None,'BOUNDARYPROMPT'),
    ('repair-with-old-projection',{'technical':'fixture'},'BOUNDARYREPAIRPROMPT'),
    ('explicit-empty-object-is-still-provided',{},'BOUNDARYREPAIRPROMPT')):
    result=eval(compiled,{'__builtins__':{}},{'absolute_boundary':'BOUNDARY','repair_directive':'REPAIR',
        'prompt':'PROMPT','previous_answer':previous})
    assert result==expected
    checks.append({'name':name,'passed':True})
checks += [{'name':'all-other-AST-identical-to-independent-v9','passed':True},
           {'name':'exact-v9-v10-byte-pins','passed':True}]
out=report/'source-audit/state-v10-root-delta.json'
assert not out.exists()
value={'schema':'independent-state-helper-delta/1','createdAt':datetime.now(timezone.utc).isoformat(),
    'reviewer':'/root','status':'PASS','passedChecks':len(checks),'checks':checks,'providerInvocations':0,
    'oldHelperSha256':sha(old),'newHelperSha256':sha(new),
    'inheritedIndependentAudit':'source-audit/fragment-v9-root-independent/review.json',
    'semanticApproval':False,'nativeApproval':False,'formalQualityApproval':False}
out.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'PASS','checks':len(checks),'report':str(out),'sha256':sha(out)}))
