"""Root-facing static delta and technical receipt metadata comparison only."""
import ast
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath

WORK = Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\.tmp\20261014-nenkin-high-01')
REPORT = Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\report\20261014-nenkin-high-01')
PINS = {
    WORK / 'delivery/build_delivery_binding_r02.py': '866269fd244073bae610eed8fd0683e2d5b1cd4073f9fcbeb8f8f3928d039c5b',
    WORK / 'delivery/build_delivery_binding_r03.py': 'fe7af7ea233186fa3a1a6becc382b003c0d9b64ea6410cf061a0a15b5bbef27a',
    WORK / 'delivery/publication_bound_r04.py': 'fd64394ef596f20558ea8e25c06f426c12c39ed0e5bec5468c9ef77b7f4ef4b9',
    WORK / 'review_plan_with_scope_r03.py': 'cec73d552fa2ae35f14f9b6151f4552ca0c8d7a3c451bcba92fef8f43b0944c2',
    REPORT / 'delivery-audit-r01/binding-r03-preparation.json': 'e9410f6884f8f64412f0ad0a4d02b9d985d0f84cbcc8ad1a88c8f40944199313',
    REPORT / 'delivery-audit-r01/binding-source13-technical-identity-r01.json': '97143ba23408854cf10c4e387e31d119e424d8a3352a5315a4861fb0b9f229ef',
    REPORT / 'independent-audit/delivery-root-code-review-r01.json': '44a9025d69aab816b965e8869675ce19d58f01276b877239e905de54d2010d25',
}
RECEIPT = Path(r'D:\開発\contextbase-evaluation\agents\reverse-agent\test-report\20261013-rerun-12h\source-pilot\runtime-code-source-13.json')
RECEIPT_SHA = '5c3eeafb764afb64e3ef80fb422e4f68a9c41b98f000d13a8d57a505d947cc79'
PINS[RECEIPT] = RECEIPT_SHA

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def verify():
    for path, expected in PINS.items():
        assert sha(path) == expected, str(path)

def assignments(tree):
    return {node.targets[0].id: node.value for node in tree.body
            if isinstance(node, ast.Assign) and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)}

verify()
old_tree = ast.parse((WORK / 'delivery/build_delivery_binding_r02.py').read_text(encoding='utf-8-sig'))
new_tree = ast.parse((WORK / 'delivery/build_delivery_binding_r03.py').read_text(encoding='utf-8-sig'))
old_functions = {node.name: ast.dump(node, include_attributes=False) for node in old_tree.body if isinstance(node, ast.FunctionDef)}
new_functions = {node.name: ast.dump(node, include_attributes=False) for node in new_tree.body if isinstance(node, ast.FunctionDef)}
changed = sorted(name for name in old_functions if old_functions[name] != new_functions[name])
added = sorted(set(new_functions) - set(old_functions))
assert changed == ['build', 'metadata_model']
assert added == ['canonical_metadata_sha']
values = assignments(new_tree)
receipt = json.loads(RECEIPT.read_text(encoding='utf-8-sig'))
technical = json.loads((REPORT / 'delivery-audit-r01/binding-source13-technical-identity-r01.json').read_text(encoding='utf-8-sig'))
runtime_root = PureWindowsPath(values['FROZEN_RUNTIME_ROOT'].args[0].value)
receipt_path = PureWindowsPath(values['FROZEN_RUNTIME_RECEIPT'].args[0].value)
assert runtime_root == PureWindowsPath(receipt['destination']) == PureWindowsPath(technical['runtimeRoot'])
assert receipt_path == PureWindowsPath(RECEIPT) == PureWindowsPath(technical['receipt']['path'])
assert ast.literal_eval(values['FROZEN_RUNTIME_RECEIPT_SHA']) == RECEIPT_SHA == technical['receipt']['sha256']
files = receipt['files']
assert len(files) == technical['runtimeFileCount'] == 128
inventory_sha = hashlib.sha256(json.dumps(files, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()
assert inventory_sha == ast.literal_eval(values['FROZEN_RUNTIME_FILES_SHA']) == technical['runtimeFilesSha256']
imports = ast.literal_eval(values['FROZEN_RUNTIME_IMPORTS'])
assert len(imports) == len(receipt['imports']) == 13
assert imports == technical['importRelativePaths']
for name, relative in imports.items():
    assert runtime_root / relative == PureWindowsPath(receipt['imports'][name])
    assert relative in files
critical = ast.literal_eval(values['FROZEN_RUNTIME_CRITICAL'])
assert len(critical) == 7 and list(critical) == technical['criticalNames']
for name in critical:
    assert name.replace('.', '/') + '.py' in files
guard_tree = ast.parse((WORK / 'review_plan_with_scope_r03.py').read_text(encoding='utf-8-sig'))
guard_values = assignments(guard_tree)
assert ast.literal_eval(guard_values['CRITICAL']) == critical
verify()
result = {
    'schema': 'spec-agent-delivery-root-code-delta-review/1',
    'createdUtc': datetime.now(timezone.utc).isoformat(),
    'reviewer': '/root/delivery_root_review',
    'scope': 'STATIC_AST_DELTA_AND_TECHNICAL_RECEIPT_JSON_METADATA_ONLY',
    'status': 'APPROVED_CODE_ONLY_ACTUAL_BINDING_CONVERSION_QUALIFICATION_PENDING',
    'reviewedInputPins': {str(path): digest for path, digest in PINS.items()},
    'oldHoldRetained': True,
    'changedFunctionsOnly': changed,
    'addedFunctionsOnly': added,
    'unchangedFunctionCount': len(old_functions) - len(changed),
    'formerRuntimeRootBlockerResolvedInCode': True,
    'technicalMetadataComparison': {
        'receiptPath': str(RECEIPT), 'receiptSha256': RECEIPT_SHA,
        'runtimeRoot': str(runtime_root), 'runtimeFileCount': 128,
        'runtimeFilesCanonicalSha256': inventory_sha,
        'exactImportMetadataCount': 13, 'exactCriticalMetadataCount': 7,
        'producerMetadataShapeMatchesScopedGuardCode': True,
        'allReviewedPinsBeforeAfterUnchanged': True
    },
    'retainedRootConstraints': [
        'Metadata-only binding grants no semantic, native or formal approval.',
        'Binding authenticates full128 frozen metadata identity and physically hashes receipt plus renderer; root must retain full current128 byte recheck at actual use.',
        'Final approved specification ID set is dynamic and excludes analysis-report; an approved first-two subset is not final completion.',
        'Root must inspect exact current actual export/native/literal/equality receipts with source/render/converter pins and full actual seen pages/ranges before final grant booleans.',
        'Original345, raw-source179 and old-output906 inventory proofs remain separate; raw179 is not the entire indexed/manifest snapshot tree.',
        'Publisher r04 retains unchanged document-local HTML and original sibling asset names, exact explicit bundle linkcheck, fragment HOLD and report-only exclusion.',
        'Actual stage receipt/manifest inspection and separate publication grant are required; two renames are not an atomic pair.'
    ],
    'actualOperations': {
        'technicalReceiptJsonReads': 1, 'businessInputReads': 0,
        'frozenRuntimeCodeContentReads': 0, 'actualCollectionOrRenderReads': 0,
        'oldOutputBodyOrHashReads': 0, 'helperImportsOrFunctionExecution': 0,
        'syntheticTestsRerun': 0, 'providers': 0, 'markers': 0,
        'artifactPdfBrowserOrComRuns': 0, 'stageOrSwapOrPublish': 0,
        'durablePromotion': 0
    },
    'scopeLimitations': [
        'No actual author, collector, renderer or converter result was assessed.',
        'AST and receipt metadata comparison does not prove real filesystem gates, native legibility, print accuracy or rollback behavior.',
        'Handoff/recipe adoption must select the fresh r03 helper by exact SHA; r02 remains rejected.',
        'No previous synthetic counts or old ASP.NET results are transferred to current qualification.'
    ],
    'nativeApproval': False, 'formalPercentage': None, 'actualStageAuthorized': False,
    'actualPublicationAuthorized': False, 'published': False,
    'reviewScript': str(Path(__file__)), 'reviewScriptSha256': sha(Path(__file__))
}
target = REPORT / 'independent-audit/delivery-root-code-review-r02.json'
with target.open('x', encoding='utf-8', newline='\n') as handle:
    json.dump(result, handle, ensure_ascii=False, indent=2)
    handle.write('\n')
print(json.dumps({'audit': str(target), 'sha256': sha(target), 'status': result['status'], 'changed': changed}, ensure_ascii=False))
