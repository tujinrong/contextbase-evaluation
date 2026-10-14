"""Independent prompt-scope delta check, without importing the helper or reading business data."""
from pathlib import Path
from datetime import datetime, timezone
import ast, copy, hashlib, json

report=Path(__file__).resolve().parents[1]
base=report.parents[1]/'.tmp/20261013-rerun-12h/training-assisted'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old,new=base/'run_state_projection_v10.py',base/'run_state_projection_v11.py'
assert sha(old)=='2d09399582e217b6082e34fa4d361aa9add0526818386701a716b114b13be8d5'
assert sha(new)=='1943ebe7ee054d4cf0ee0dbc1652ae8af34f7e85dbddbe254b6a1a1934f3a8cf'
old_tree=ast.parse(old.read_text(encoding='utf-8-sig'))
new_tree=ast.parse(new.read_text(encoding='utf-8-sig'))
assignments={}
for node in ast.walk(new_tree):
    if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
        assignments.setdefault(node.targets[0].id,[]).append(node)
scope=assignments['state_scope']
assert len(scope)==1 and isinstance(scope[0].value,ast.Constant)
text=scope[0].value.value
assert all(term in text for term in ('同一画面','Viewer/Staff/Admin','新独立meaning review','意味不足を原資料で実証'))
old_main=next(n for n in old_tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
new_main=next(n for n in new_tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
original_assigns={}
for node in ast.walk(old_main):
    if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
        original_assigns.setdefault(node.targets[0].id,[]).append(node)
class Restore(ast.NodeTransformer):
    def visit_Assign(self,node):
        if len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            name=node.targets[0].id
            if name=='state_scope': return None
            if name in ('prompt','review_prompt') and any(isinstance(n,ast.Name) and n.id=='state_scope' for n in ast.walk(node.value)):
                candidates=[n for n in original_assigns[name] if isinstance(n.value,ast.BinOp) and
                    any(isinstance(x,ast.Name) and x.id=='absolute_boundary' for x in ast.walk(n.value))]
                assert len(candidates)==1
                return copy.deepcopy(candidates[0])
        return self.generic_visit(node)
restored=Restore().visit(copy.deepcopy(new_tree))
assert ast.dump(old_tree,include_attributes=False)==ast.dump(restored,include_attributes=False)
prompt_node=next(n for n in assignments['prompt'] if any(isinstance(x,ast.Name) and x.id=='state_scope' for x in ast.walk(n.value)))
for previous,expected in ((None,False),({},True),({'states':[]},True)):
    value=eval(compile(ast.Expression(prompt_node.value),'<synthetic-prompt>','eval'),{},
        {'absolute_boundary':'BOUNDARY','state_scope':'SCOPE','repair_directive':'REPAIR','previous_answer':previous,'prompt':'BODY'})
    assert value=='BOUNDARYSCOPE'+('REPAIR' if expected else '')+'BODY'
target=report/'source-audit/state-v11-root-delta.json'
assert not target.exists()
result={'schema':'independent-state-helper-delta/1','createdAt':datetime.now(timezone.utc).isoformat(),
    'reviewer':'/root','status':'PASS','passedChecks':6,'checks':['exact-helper-byte-pins','same-parent-screen-scope-explicit',
        'all-other-AST-identical-to-independent-v10','initial-no-repair','explicit-empty-object-repair','provided-object-repair'],
    'oldHelperSha256':sha(old),'newHelperSha256':sha(new),'providerInvocations':0,'businessMaterialsRead':0,
    'inheritedIndependentAudit':'source-audit/state-v10-root-delta.json','semanticApproval':False,'nativeApproval':False,'formalQualityApproval':False}
target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
