"""Change only HELPER filename/SHA in fresh collector and renderer candidates."""
import ast
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

WORK = Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\.tmp\20261014-nenkin-high-01')
REPORT = Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\report\20261014-nenkin-high-01')
OLD_HELPER = WORK / 'review_plan_with_scope_r03.py'
OLD_HELPER_SHA = 'cec73d552fa2ae35f14f9b6151f4552ca0c8d7a3c451bcba92fef8f43b0944c2'
NEW_HELPER = WORK / 'review_plan_with_scope_r05.py'
NEW_HELPER_SHA = '9d5ec80c5fd3efe2044302104a64ff928777fd98d3cdd0e0c8ef0ff301ee5802'
BASES = [
    ('collect_reviewed_r07.py', 'ee8419432a9b553c04ba757a2b188c86614ae230d980c5822ac8d8fe17a40a50', 'collect_reviewed_r08.py'),
    ('render_reviewed_r04.py', '888db1128cc0f5dc0ab942e18fb4476e4f0ce79cf1aa2d1e3bd75324952571be', 'render_reviewed_r05.py'),
]

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def file_sha(path):
    return sha(path.read_bytes())

def dump(node):
    return ast.dump(node, include_attributes=False)

def assignments(tree):
    return {node.targets[0].id: node.value for node in tree.body
            if isinstance(node, ast.Assign) and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)}

def without_pointer_assignments(tree):
    tree.body = [node for node in tree.body if not (
        isinstance(node, ast.Assign) and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id in {'HELPER', 'HELPER_SHA'})]
    return dump(tree)

def no_reparse(path):
    for candidate in (path, *path.parents):
        if candidate.exists():
            stat = candidate.lstat()
            assert not candidate.is_symlink() and not (getattr(stat, 'st_file_attributes', 0) & 0x400), str(candidate)

for p in (WORK, REPORT, OLD_HELPER, NEW_HELPER):
    no_reparse(p)
assert file_sha(OLD_HELPER) == OLD_HELPER_SHA
assert file_sha(NEW_HELPER) == NEW_HELPER_SHA
old_guard = ast.parse(OLD_HELPER.read_bytes().decode('utf-8-sig'))
new_guard = ast.parse(NEW_HELPER.read_bytes().decode('utf-8-sig'))
old_constants, new_constants = assignments(old_guard), assignments(new_guard)
preserved_guard_constants = ('REPO', 'RUN', 'REPORT', 'SNAPSHOT', 'SNAPSHOT_SHA', 'CONTEXT', 'CONTEXT_SHA', 'RECEIPT', 'RECEIPT_SHA', 'RUNTIME', 'DEADLINE', 'CRITICAL')
assert all(dump(old_constants[name]) == dump(new_constants[name]) for name in preserved_guard_constants)
prepared = []
for old_name, old_sha, new_name in BASES:
    original, candidate = WORK / old_name, WORK / new_name
    no_reparse(original)
    no_reparse(candidate)
    assert not candidate.exists()
    raw = original.read_bytes()
    assert sha(raw) == old_sha
    old_filename, new_filename = OLD_HELPER.name.encode('ascii'), NEW_HELPER.name.encode('ascii')
    old_digest, new_digest = OLD_HELPER_SHA.encode('ascii'), NEW_HELPER_SHA.encode('ascii')
    assert raw.count(old_filename) == raw.count(old_digest) == 1
    revised = raw.replace(old_filename, new_filename).replace(old_digest, new_digest)
    assert revised.replace(new_filename, old_filename).replace(new_digest, old_digest) == raw
    old_ast, new_ast = ast.parse(raw.decode('utf-8-sig')), ast.parse(revised.decode('utf-8-sig'))
    old_values, new_values = assignments(old_ast), assignments(new_ast)
    assert set(old_values) == set(new_values)
    changed_constants = sorted(name for name in old_values if dump(old_values[name]) != dump(new_values[name]))
    assert changed_constants == ['HELPER', 'HELPER_SHA']
    old_functions = {node.name: dump(node) for node in old_ast.body if isinstance(node, ast.FunctionDef)}
    new_functions = {node.name: dump(node) for node in new_ast.body if isinstance(node, ast.FunctionDef)}
    assert old_functions == new_functions
    assert without_pointer_assignments(old_ast) == without_pointer_assignments(new_ast)
    assert ast.literal_eval(new_values['HELPER_SHA']) == NEW_HELPER_SHA
    assert new_values['HELPER'].right.value == NEW_HELPER.name
    prepared.append((original, old_sha, candidate, revised, len(old_functions), changed_constants))
for original, old_sha, candidate, revised, _, _ in prepared:
    assert file_sha(original) == old_sha
    assert file_sha(NEW_HELPER) == NEW_HELPER_SHA
    with candidate.open('xb') as stream:
        stream.write(revised)
for original, old_sha, candidate, revised, _, _ in prepared:
    assert file_sha(original) == old_sha and candidate.read_bytes() == revised
assert file_sha(OLD_HELPER) == OLD_HELPER_SHA and file_sha(NEW_HELPER) == NEW_HELPER_SHA
result = {
    'schema': 'spec-agent-collector-renderer-pointer-review/1',
    'createdUtc': datetime.now(timezone.utc).isoformat(),
    'reviewer': '/root/delivery_root_review',
    'scope': 'POINTER_ONLY_CODE_PREPARATION_AND_STATIC_AST_AUDIT',
    'status': 'APPROVED_POINTER_ONLY_CODE_ACTUAL_COLLECTION_RENDER_PENDING',
    'helper': {'path': str(NEW_HELPER), 'sha256': NEW_HELPER_SHA},
    'previousHelper': {'path': str(OLD_HELPER), 'sha256': OLD_HELPER_SHA, 'unchanged': True},
    'candidates': [
        {'base': str(original), 'baseSha256': old_sha, 'path': str(candidate),
         'sha256': sha(revised), 'changedConstantsOnly': changed_constants,
         'unchangedFunctionCount': function_count, 'allFunctionAstsIdentical': True,
         'allOtherModuleAstIdentical': True, 'byteDeltaInverseEqualsOriginal': True,
         'baseBytesBeforeAfterUnchanged': True}
        for original, old_sha, candidate, revised, function_count, changed_constants in prepared
    ],
    'guardProvenanceConstantsUnchanged': list(preserved_guard_constants),
    'sourceCapsuleSha256': 'f074529043ff1c25ea53be34c16ae3a4788f137a1e3afb33c6214de7bf4c7445',
    'executionContextSha256': '8966757e00954241029817027efa85bafeb859beee5105b05c7c939c84470605',
    'deadlineUtc': '2026-10-14T13:06:43.011844+00:00',
    'runtimeReceiptSha256': '5c3eeafb764afb64e3ef80fb422e4f68a9c41b98f000d13a8d57a505d947cc79',
    'scopeMeaning': 'Corrected review scope acknowledges full definition/all-document outline/execution metadata author inputs and own-group reference contract; no approval or source evidence is invented.',
    'optionalSupplementalCollectorDeltaImplemented': False,
    'actualOperations': {
        'businessOrProtectedSourceReads': 0, 'actualAuthorCollectionRenderRecordsRead': 0,
        'runtimeCodeImports': 0, 'helperImportsOrFunctionExecution': 0,
        'providers': 0, 'collectors': 0, 'renderers': 0, 'browsers': 0,
        'markers': 0, 'artifactPdfComOrStagePublish': 0
    },
    'limitations': [
        'This is a static pointer preparation, not production activation, semantic approval, native qualification or collection/render success.',
        'No supplemental index/report marker compatibility is added in these candidates.',
        'Delivery binding producer pointers must be revised separately before adopting these collector/renderer candidates.',
        'Exact current verified plan/review and actual author records remain prerequisites.'
    ],
    'nativeApproval': False, 'formalPercentage': None, 'published': False,
    'preparationScript': {'path': str(Path(__file__)), 'sha256': file_sha(Path(__file__))}
}
audit = REPORT / 'independent-audit/collector-renderer-pointer-review-r08-r05.json'
with audit.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps({'audit': str(audit), 'auditSha256': file_sha(audit), 'status': result['status'], 'candidates': [{'path': str(candidate), 'sha256': sha(revised)} for _, _, candidate, revised, _, _ in prepared]}, ensure_ascii=False))
