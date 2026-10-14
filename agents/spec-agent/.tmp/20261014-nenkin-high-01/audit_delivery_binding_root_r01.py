"""Root actual code/read and full frozen runtime audit; no document authoring."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, importlib.util, json

work = Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\.tmp\20261014-nenkin-high-01')
report = Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\report\20261014-nenkin-high-01')
pins = {
    work / 'review_plan_with_scope_r06.py': '21b518c3fde79a6036b7c4e98cddc9d34489f1ed013cc4a9151687555c682fc8',
    work / 'delivery/build_delivery_binding_r07.py': 'd01e3586ddd9f171e8daa1479611f2ba3d800ef906979d4f60cd1ad9da7297ed',
    report / 'delivery-audit-r01/delivery-preparation-handoff-r06.json': 'f2def803000b25ac5fea631f4cd66dca13bd44b15b43d48f7d49d3121bc01924',
    report / 'delivery-audit-r01/binding-r07-mirror-independent-targeted-probes-r01.json': '71fed0845f8d25372db329c7f9d221a4b3b31bbe480aba262e2cf27c10b7b98c',
    report / 'root-delivery-citation-code-runtime-audit-r01.json': 'b34f29afa0909023e58555a3a46631f09dd9e5a4299e284d0ae30c83615748ee',
}
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
for path, expected in pins.items():
    assert sha(path) == expected, str(path)
spec = importlib.util.spec_from_file_location('root_binding_scope_guard_r01', work / 'review_plan_with_scope_r06.py')
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)
before = guard.bootstrap()
from contextbase.ai import capsule
state_before = capsule.verification_state(guard.SNAPSHOT)
assert state_before['manifestSha256'] == guard.SNAPSHOT_SHA
after = guard.bootstrap()
assert before == after and state_before == capsule.verification_state(guard.SNAPSHOT)
for path, expected in pins.items():
    assert sha(path) == expected, str(path)
result = {
    'schema': 'spec-agent-root-delivery-binding-code-runtime-audit/1',
    'createdUtc': datetime.now(timezone.utc).isoformat(),
    'status': 'APPROVED_CODE_AND_FROZEN_RUNTIME_SCOPE_ONLY',
    'rootCodeRead': 'Complete binding7 functions/main and mirror15 field model, inventory, provenance, beforeafter pins inspected; targeted peer 30 plus 6 static checks read',
    'pinnedInputs': {str(path): value for path, value in pins.items()},
    'actualFrozenFileCount': len(before['runtimeFiles']),
    'actualLoadedImportCount': len(before['loadedImports']),
    'actualCriticalModuleCount': len(before['criticalModules']),
    'runtimeReceiptSha256': before['receiptSha256'],
    'sourceCapsule': state_before,
    'runtimeAndCapsuleUnchangedDuringAudit': True,
    'actualBindingCollectionRenderRecordReads': 0,
    'actualAuthoringMarkersExportsNativeOrPublicationOperations': 0,
    'canonicalMarkdownBodyChanges': 0,
    'actualNativeQualification': False,
    'formalPercentage': None,
    'published': False,
    'remainingRequirements': ['Actual closed author selection/collection/render7 binding grant and physical fresh source/runtime recheck', 'Exact byte equality/format/full native QA and actual HTML routing/link inspection before publication'],
}
target = report / 'root-delivery-binding-code-runtime-audit-r01.json'
with target.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps({'status': result['status'], 'report': str(target), 'sha256': sha(target)}, ensure_ascii=False))
