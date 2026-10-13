"""Read-only proof of a text-scope approval / unresolved-boundary conflict."""
import ast
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from jsonschema import Draft202012Validator
from contextbase.ai import schemas

root = Path.cwd()
report = Path(__file__).resolve().parent
job = root / 'agents/reverse-agent/.tmp/20261013-session-pilot-01/focus-round-04/488af9821732c8f6/independent-review'
workflow = root / 'agents/reverse-agent/src/contextbase/ai/workflow.py'
paths = [workflow, root / 'agents/reverse-agent/src/contextbase/ai/prompts.py', job / 'prompt.txt', job / 'review-verified.json', job / 'review-handoff.json', root / 'test-project1/spec-analysis/CSharp_ASPNET/20261013-focus-round-04/spec/detail/student-search.md']
def pins():
    return [{'path': p.relative_to(root).as_posix(), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size} for p in paths]
before = pins()
answer = json.loads((job / 'review-verified.json').read_text(encoding='utf-8'))
tree = ast.parse(workflow.read_text(encoding='utf-8'))
review = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'review')
gate = next(n for n in review.body if isinstance(n, ast.If) and "answer['unresolved']" in ast.unparse(n.test))
code = compile(ast.fix_missing_locations(ast.Module(body=[gate], type_ignores=[])), str(workflow), 'exec')
cases = []
for label, value, rejection in [('existing-review-preserved', deepcopy(answer), False), ('text-approved-with-same-out-of-scope-unknowns', dict(answer, approved=True), True), ('text-approved-empty-unresolved-control', dict(answer, approved=True, unresolved=[]), False)]:
    Draft202012Validator(schemas.REVIEW).validate(value)
    error = None
    try:
        exec(code, {'answer': value})
    except ValueError as exc:
        error = str(exc)
    assert bool(error) == rejection
    cases.append({'case': label, 'schemaValid': True, 'rejectedByExactCurrentWorkflowGate': bool(error), 'error': error, 'status': 'PASS'})
after = pins()
assert before == after
result = {'schema': 'independent-method-scope-audit/1', 'readOnly': True, 'aiProviderStarted': False, 'cases': cases, 'inputsUnchanged': before == after, 'gateLines': [gate.lineno, gate.end_lineno], 'existingReview': {'approved': answer['approved'], 'findingCount': len(answer['findings']), 'unresolved': answer['unresolved']}, 'pins': before}
(report / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'cases': len(cases), 'allPass': True, 'inputsUnchanged': True}, ensure_ascii=False))
