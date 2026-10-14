"""Root code/runtime audit only. Does not activate authors or create business text."""
import ast
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

WORK = Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/.tmp/20261014-nenkin-high-01')
REPORT = Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/report/20261014-nenkin-high-01')
driver = WORK / 'nenkin_writer_driver_r05.py'
spec = importlib.util.spec_from_file_location('root_metadata_writer_audit', driver)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.require(module.sha(driver) == '6b8e5456d96fabfda1bf43b6c17b6155167726492b10c0f9145473f243ee102c', 'Driver differs from inspected bytes')
old_driver = WORK / 'nenkin_writer_driver_r04.py'
module.require(module.sha(old_driver) == 'ce836766e61f5abad0fc4d2abfe11b3c6e6588f4dc8b9d46f62f913f0cd8e664', 'Base writer drift')
before = {node.name: ast.dump(node, include_attributes=False) for node in ast.parse(old_driver.read_text(encoding='utf-8')).body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
after = {node.name: ast.dump(node, include_attributes=False) for node in ast.parse(driver.read_text(encoding='utf-8')).body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
allowed = {'prepare', 'recheck', 'previous_revision', 'scoped_review', 'text_pin', 'run', 'main'}
changed = sorted(name for name in before if before[name] != after[name])
module.require(set(changed) == allowed, 'Unexpected base-function change')
pins = {
    REPORT / 'writer-root-code-audit-r04.json': 'f1271a52da98ec3ebd430dccb50d32a1a30537fbccb79dbea3086e2ef37e2a96',
    REPORT / 'author-execution-metadata-preparation-r05-r02.json': '70044169321f9e2467d084158f6ad9c16927ea0168027666a8387e75fd282a76',
    REPORT / 'independent-audit/writer-metadata-r05-independent-code-review-r01.json': '5002a883e75a2b51ecda580e8570ca1f9f1773072e71b8e02ccc7517ab847ec3',
    REPORT / 'independent-audit/writer-metadata-r05-bounded-probes-r03.json': '635595f3269bf50e2b68ad05fb4bf7139fcb7f0d31a8053807ce06a1c38bcc23',
}
for path, expected in pins.items():
    module.require(module.sha(path) == expected, 'Preparation/peer audit drift')
runtime = module.bootstrap()
from contextbase.ai import capsule
snapshot = WORK / 'snapshot-input-02'
module.require(module.sha(snapshot / 'manifest.json') == 'f074529043ff1c25ea53be34c16ae3a4788f137a1e3afb33c6214de7bf4c7445', 'Capsule identity drift')
manifest = capsule.verify(snapshot)
module.require(len(manifest['files']) == 179, 'Capsule count drift')
context = WORK / 'execution-context-input-02.json'
module.require(module.sha(context) == '8966757e00954241029817027efa85bafeb859beee5105b05c7c939c84470605', 'Context drift')
seal = module.load(module.PROTECTED_SEAL)
sealed = {item['path']: {'bytes': item['bytes'], 'sha256': item['sha256']} for item in seal['files']}
module.require(len(sealed) == 345 and module.inventory(module.SOURCE) == sealed, 'Original input drift')
for name, (path, expected) in module.METADATA_SCHEMAS.items():
    module.require(module.sha(path) == expected, 'Metadata schema drift')
    from jsonschema import Draft202012Validator
    Draft202012Validator.check_schema(module.load(path))
runtime_after = module.bootstrap()
module.require(runtime == runtime_after and module.inventory(module.SOURCE) == sealed, 'Runtime/input drift during audit')
record = {
    'schema': 'spec-agent-root-writer-code-audit/1', 'createdAt': datetime.now(timezone.utc).isoformat(),
    'status': 'APPROVED_CODE_AND_FROZEN_RUNTIME_SCOPE_ONLY', 'driver': str(driver), 'driverSha256': module.sha(driver),
    'agentRole': 'AG-SPEC', 'projectId': 'nenkin',
    'rootCodeRead': 'Base r04 audit retained; root inspected all r05 added functions and changed prepare/recheck/previous_revision/scoped_review/text_pin/run/main',
    'changedBaseFunctions': changed, 'baseBindingAndBootstrapAstUnchanged': True,
    'auditPins': {str(path): expected for path, expected in pins.items()},
    'runtimeReceiptSha256': module.RECEIPT_SHA, 'runtimeFileCount': 128,
    'actualLoadedReceiptImports': runtime['receiptImports'], 'actualCriticalModules': runtime['criticalModules'],
    'expandedSourceSnapshotManifestSha256': module.sha(snapshot / 'manifest.json'), 'expandedSourceFileCount': 179,
    'executionContextSha256': module.sha(context), 'protectedOriginalFileCount': 345,
    'runtimeAndSourceBeforeAfterUnchanged': True, 'frozenCoreOrPromptModified': False,
    'originalApplicationOrDatabaseExecuted': False, 'providerCalls': 0, 'activationBindingExecuted': False,
    'reservedMetadataKinds': ['index', 'analysis-report'],
    'metadataQualificationLimits': ['Referenced completion evidence needs root association/status validation', 'Actual routing/layout/links need final bundle validation', 'Composite before/after guards do not prove internal callback or atomic protection'],
    'requiredBeforeAuthor': 'Exact full-plan r05 activation and production binding/prepare; reserved wave requires current owned pinned metadata',
    'publicationRequires': 'Closed unchanged wave, raw/structure/text review and actual native/literal conversion validation',
    'businessProseAssembledByPython': False, 'formalPercentage': None, 'published': False,
}
target = REPORT / 'writer-root-code-audit-r05.json'
module.write(target, record)
print(json.dumps({'path': str(target), 'sha256': module.sha(target), 'status': record['status']}, ensure_ascii=False))
