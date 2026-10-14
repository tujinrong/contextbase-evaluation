"""Independent technical checks; no provider invocation or specification authorship."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import copy
import hashlib
import importlib.util
import json
from types import SimpleNamespace

REPORT = Path(__file__).resolve().parents[1]
BASE = REPORT.parents[1] / '.tmp/20261013-rerun-12h/training-assisted'
OUT = REPORT / 'source-audit/fragment-v9-root-independent'
EXPECTED = '98cdfa4952b0afde0d1bab51a0fda1d228b368e51d7c8bdb9669c082838c637a'
ANCHOR = '47f0c1a928198dde2147de2a5638c4190e96377b26f62e78fe7bf6dab5f3eb90'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
load = lambda p: json.loads(Path(p).read_text(encoding='utf-8-sig'))
checks = []

def check(name, action, rejected=False):
    try:
        value = action()
    except (ValueError, KeyError) as exc:
        if not rejected:
            raise
        checks.append({'name': name, 'passed': True, 'result': 'REJECTED', 'errorType': type(exc).__name__})
        return
    if rejected:
        raise AssertionError('Not rejected: ' + name)
    if value is False:
        raise AssertionError(name)
    checks.append({'name': name, 'passed': True, 'result': 'ACCEPTED'})

assert not OUT.exists()
assert sha(BASE/'run_state_projection_v9.py') == EXPECTED
assert sha(BASE/'fragment_anchor_gate_v1.py') == ANCHOR
spec = importlib.util.spec_from_file_location('audited_projection_v9', BASE/'run_state_projection_v9.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def parsed(text):
    parser = m.ProjectionHtml()
    parser.feed(text)
    parser.close()
    return True

for name, text in {
    'matched-id': '<a href="#section-1">Jump</a><section id="section-1">Target</section>',
    'matched-name': '<a href="#part">Jump</a><a name="part">Target</a>',
    'same-node-id-and-name': '<a href="#part">Jump</a><a id="part" name="part">Target</a>',
    'unicode-fragment': '<a href="#説明">Jump</a><div id="説明">Target</div>',
    'forward-and-backward-fragments': '<div id="one">One</div><a href="#one">One</a><a href="#two">Two</a><div id="two">Two</div>',
    'inert-form-with-fragment': '<form inert><fieldset disabled><input disabled="disabled"></fieldset></form><a href="#part">Back</a><div id="part">Part</div>',
}.items():
    check(name, lambda text=text: parsed(text))

for name, text in {
    'external-url': '<a href="https://example.invalid">X</a>',
    'relative-url': '<a href="relative.html#x">X</a>',
    'blank-fragment': '<a href="#">X</a>',
    'missing-target': '<a href="#missing">X</a>',
    'fragment-on-other-tag': '<div href="#part" id="part">X</div>',
    'duplicate-target': '<div id="part"></div><div id="part"></div>',
    'duplicate-attribute': '<a href="#part" HREF="#part">X</a><div id="part"></div>',
    'percent-fragment': '<a href="#p%61rt">X</a><div id="part"></div>',
    'control-fragment': '<a href="#pa&#10;rt">X</a><div id="part"></div>',
    'space-fragment': '<a href="#part two">X</a><div id="part two"></div>',
    'javascript': '<a href="javascript:alert(1)">X</a>',
    'event-attribute': '<a href="#part" onclick="alert(1)">X</a><div id="part"></div>',
    'xlink': '<a xlink:href="#part">X</a><div id="part"></div>',
    'boolean-false': '<input disabled="false">',
    'script': '<script>alert(1)</script>',
    'css-network': '<style>div{background:url(https://example.invalid/a)}</style>',
    'css-import': '<style>@import "https://example.invalid/a";</style>',
    'meta-refresh': '<meta http-equiv="refresh" content="0;url=https://example.invalid">',
}.items():
    check(name, lambda text=text: parsed(text), rejected=True)

def definitions(path):
    return {node.name: ast.dump(node, include_attributes=False) for node in ast.parse(path.read_text(encoding='utf-8')).body
            if isinstance(node, (ast.FunctionDef, ast.ClassDef))}

old_defs = definitions(BASE/'run_state_projection_v8.py')
new_defs = definitions(BASE/'run_state_projection_v9.py')
check('v8-to-v9-only-three-functions-changed', lambda: set(old_defs) == set(new_defs) and
      {name for name in new_defs if old_defs[name] != new_defs[name]} == {'sha', 'load', 'bind_previous_projection'})

def assert_safe_before_read(name):
    tree = ast.parse((BASE/'run_state_projection_v9.py').read_text(encoding='utf-8'))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    call = node.body[0].value
    if name == 'sha':
        read = call.func.value.args[0]
    else:
        read = call.args[0]
    return isinstance(read, ast.Call) and isinstance(read.func, ast.Attribute) and isinstance(read.func.value, ast.Call) and ast.unparse(read.func.value).startswith('capsule.safe_path(')

check('sha-safe-path-before-read', lambda: assert_safe_before_read('sha'))
check('load-safe-path-before-read', lambda: assert_safe_before_read('load'))
check('actual-fragment-module-binding', lambda: m.fragment_module_pin()['sha256'] == ANCHOR)
old_module_file = m.anchors.__file__
try:
    m.anchors.__file__ = str(BASE/'wrong-fragment-file.py')
    check('wrong-loaded-fragment-module-refused', m.fragment_module_pin, rejected=True)
finally:
    m.anchors.__file__ = old_module_file

old_job = BASE/'state-projections/state-basic-registration-r05-v01'
old = load(old_job/'input-pins.json')
manifest = m.capsule.verify(BASE/'snapshot')
item = next(d for d in load(REPORT/'document-contract.json')['documents'] if d['id'] == old['documentId'])
args = SimpleNamespace(previous_projection_job=old_job,
    previous_projection_sha256=sha(old_job/'projection-verified.json'),
    previous_input_sha256=sha(old_job/'input-pins.json'),
    previous_review_sha256=sha(old_job/'projection-review-verified.json'))

def bound(args_value=args, parent_value=old['parent'], metadata_value=None):
    metadata_value = metadata_value or {'capsule': copy.deepcopy(old['capsule']), 'pinnedFiles': {}}
    answer, review = m.bind_previous_projection(args_value, parent_value, item, manifest, metadata_value)
    if len(metadata_value['pinnedFiles']) != 17:
        raise AssertionError('All seventeen old artifacts must be pinned')
    if not all(str(old_job/stage/'answer.txt') in metadata_value['pinnedFiles'] for stage in ('projection','independent-review')):
        raise AssertionError('Both raw AI answers must be pinned')
    return metadata_value

binding = bound()
checks.append({'name': 'actual-old-minor-only-projection-seventeen-artifact-binding', 'passed': True, 'result': 'ACCEPTED'})
wrong = copy.copy(args)
wrong.previous_projection_sha256 = '0'*64
check('wrong-old-projection-pin', lambda: bound(wrong), rejected=True)
wrong = copy.copy(args)
wrong.previous_review_sha256 = None
check('partial-old-binding', lambda: bound(wrong), rejected=True)
wrong_parent = copy.deepcopy(old['parent'])
wrong_parent['sha256'] = '0'*64
check('wrong-old-parent', lambda: bound(parent_value=wrong_parent), rejected=True)
wrong_metadata = {'capsule': copy.deepcopy(old['capsule']), 'pinnedFiles': {}}
wrong_metadata['capsule']['manifestSha256'] = '0'*64
check('wrong-old-capsule', lambda: bound(metadata_value=wrong_metadata), rejected=True)

tree = ast.parse((BASE/'run_state_projection_v9.py').read_text(encoding='utf-8'))
main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
accepted = next(n for n in ast.walk(main) if isinstance(n, ast.Assign) and any(isinstance(t,ast.Name) and t.id=='accepted' for t in n.targets))
check('new-review-zero-findings-and-unresolved-required', lambda: ast.unparse(accepted.value) ==
      "bool(projection_review['approved'] and (not projection_review['findings']) and (not projection_review['unresolved']))")
check('fresh-writer-and-independent-review-stages', lambda: len([n for n in ast.walk(main)
    if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='_bound_job']) == 2)
check('old-artifacts-still-exact-after-independent-read', lambda: all(sha(p)==h for p,h in binding['pinnedFiles'].items()))
assert sha(BASE/'run_state_projection_v9.py') == EXPECTED and sha(BASE/'fragment_anchor_gate_v1.py') == ANCHOR
OUT.mkdir(parents=True)
value = {'schema':'independent-technical-state-helper-audit/1','createdAt':datetime.now(timezone.utc).isoformat(),
    'reviewer':'/root','helper':str(BASE/'run_state_projection_v9.py'),'helperSha256':EXPECTED,
    'fragmentGateSha256':ANCHOR,'status':'PASS','passedChecks':len(checks),'checks':checks,
    'oldPinnedArtifacts':binding['pinnedFiles'],'providerInvocations':0,
    'businessSpecificationAuthored':False,'originalApplicationExecuted':False,
    'scope':'v9 delta and local fragment validation; inherited v6/v7 guards have separate independent reports',
    'newProjectionSemanticApproval':False,'nativeVisualApproval':False,'formalQualityApproval':False}
(OUT/'review.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'PASS','passedChecks':len(checks),'report':str(OUT/'review.json'),'sha256':sha(OUT/'review.json')}))
