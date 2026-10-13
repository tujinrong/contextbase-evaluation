"""Independent AST checks of scope separation, without provider or source execution."""
import ast
import hashlib
import json
from pathlib import Path
from jsonschema import Draft202012Validator
from contextbase.ai import prompts, schemas
root=Path.cwd(); report=Path(__file__).resolve().parent
workflow=root/'agents/reverse-agent/src/contextbase/ai/workflow.py'
job=root/'agents/reverse-agent/.tmp/20261013-session-pilot-01/focus-round-04/488af9821732c8f6/independent-review'
paths=[workflow,root/'agents/reverse-agent/src/contextbase/ai/prompts.py',root/'agents/reverse-agent/src/contextbase/ai/schemas.py',job/'review-verified.json',job/'review-handoff.json',job/'schema.json',job/'prompt.txt',job.parent.parent/'runner-source.py']
def pins(): return [{'path':p.relative_to(root).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]
before=pins(); tree=ast.parse(workflow.read_text(encoding='utf-8')); review=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='review')
gate=next(n for n in review.body if isinstance(n,ast.If) and "answer['unresolved']" in ast.unparse(n.test))
code=compile(ast.fix_missing_locations(ast.Module(body=[gate],type_ignores=[])),str(workflow),'exec')
cases=[]
for label,unresolved,findings,reject in [('text-clear-approved',[],[],False),('text-unknown-fake-approval',['source condition remains unknown'],[],True),('important-finding-fake-approval',[],[{'severity':'major','documentLocation':'spec/detail/document.md:1','defect':'Unverified source condition is asserted as guaranteed.','repairDirection':'Recheck cited source and retain conditional scope.','references':[{'path':'sources/Infrastructure/SearchContextStore.cs','startLine':14,'endLine':14}]}],True)]:
    answer={'documentId':'SM-DET-STUDENT-SEARCH','approved':True,'findings':findings,'unresolved':unresolved}
    Draft202012Validator(schemas.REVIEW).validate(answer)
    error=None
    try: exec(code,{'answer':answer})
    except ValueError as exc: error=str(exc)
    assert bool(error)==reject
    cases.append({'case':label,'status':'PASS','rejected':bool(error)})
handoff_call=next(n.value for n in review.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and ast.unparse(n.value.func)=='capsule.write_json' and 'review-handoff.json' in ast.unparse(n.value.args[0]))
fields={k.value:v for k,v in zip(handoff_call.args[1].keys,handoff_call.args[1].values)}
assert ast.literal_eval(fields['unassessedScopes'])==['visual-fidelity','application-runtime','formal-semantic-scoring']
assert ast.literal_eval(fields['visualFidelityVerified']) is False
assert ast.literal_eval(fields['formallyEvaluatedByOriginalRubric']) is False
assert ast.literal_eval(fields['reviewScope'])=='text-source-and-structure'
assert 'unresolvedは本文・原文根拠・構造の未解決疑問だけ' in prompts.REVIEW
assert 'unresolvedへ混ぜません' in prompts.REVIEW
assert schemas.REVIEW==json.loads((job/'schema.json').read_text(encoding='utf-8'))
cases.append({'case':'unchanged-raw-schema-and-explicit-unassessed-handoff','status':'PASS','unassessedScopes':ast.literal_eval(fields['unassessedScopes']),'visualFidelityVerified':False,'formallyEvaluatedByOriginalRubric':False})
after=pins(); assert before==after
(report/'fix-confirmation.json').write_text(json.dumps({'schema':'independent-review-scope-fix-check/1','cases':cases,'inputsUnchanged':True,'providerStarted':False,'oldV4ReviewRewritten':False,'runningV4RuntimePatched':False,'gateLines':[gate.lineno,gate.end_lineno],'handoffLines':[handoff_call.lineno,handoff_call.end_lineno],'pins':before},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'cases':len(cases),'allPass':True,'inputsUnchanged':True}))
