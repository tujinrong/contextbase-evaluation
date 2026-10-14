"""Root code/runtime audit only; no activation, source analysis, author or provider."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util, json, sys
sys.dont_write_bytecode = True
RUN = Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/.tmp/20261014-nenkin-high-01')
REPORT = Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/report/20261014-nenkin-high-01')
GUARD = RUN / 'review_plan_with_scope_r03.py'
spec = importlib.util.spec_from_file_location('root_scoped_writer_audit', GUARD)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)
guard.require(guard.sha(GUARD) == 'cec73d552fa2ae35f14f9b6151f4552ca0c8d7a3c451bcba92fef8f43b0944c2',
              'Root scoped audit helper changed')
writer_file = guard.safe(RUN / 'nenkin_writer_driver_r04.py')
guard.require(guard.sha(writer_file) == 'ce836766e61f5abad0fc4d2abfe11b3c6e6588f4dc8b9d46f62f913f0cd8e664',
              'Audited writer code changed')
writer_spec = importlib.util.spec_from_file_location('root_frozen_writer_r04', writer_file)
writer = importlib.util.module_from_spec(writer_spec)
writer_spec.loader.exec_module(writer)
runtime = writer.bootstrap()
from contextbase.ai import capsule
from jsonschema import Draft202012Validator
manifest = capsule.verify(guard.SNAPSHOT)
guard.require(guard.sha(guard.SNAPSHOT / 'manifest.json') == guard.SNAPSHOT_SHA and len(manifest['files']) == 179 and
              guard.sha(guard.CONTEXT) == guard.CONTEXT_SHA, 'Expanded input/context changed')
for name, (path, expected) in writer.SCHEMAS.items():
    guard.require(writer.sha(path) == expected, 'Pinned writer schema changed')
    Draft202012Validator.check_schema(writer.load(path))
baseline = writer.load(writer.PROTECTED_SEAL)
originals = {item['path']: {'bytes': item['bytes'], 'sha256': item['sha256']} for item in baseline['files']}
guard.require(len(originals) == 345 and writer.inventory(writer.SOURCE) == originals, 'Original source drift')
peer = REPORT / 'independent-audit/writer-revision-code-review-r04.json'
guard.require(guard.sha(peer) == '41ce4286ac9c69d395bdd81f26aedd77e50dfbdfca1f8e0ac121a61ceba89dc7',
              'Independent code audit bytes changed')
guard.require(writer.bootstrap() == runtime and writer.inventory(writer.SOURCE) == originals and
              capsule.verify(guard.SNAPSHOT) == manifest, 'Audit input/runtime drift')
record = {'schema': 'spec-agent-root-writer-code-audit/1',
          'createdAt': datetime.now(timezone.utc).isoformat(), 'status': 'APPROVED_CODE_AND_FROZEN_RUNTIME_SCOPE_ONLY',
          'driver': str(writer_file), 'driverSha256': writer.sha(writer_file),
          'agentRole': 'AG-SPEC', 'projectId': 'nenkin',
          'rootCodeRead': 'Complete r01 plus complete r02/r03/r04 deltas; all writer functions inspected',
          'independentCodeAudit': str(peer), 'independentCodeAuditSha256': guard.sha(peer),
          'runtimeReceiptSha256': guard.RECEIPT_SHA, 'runtimeFileCount': runtime['fileCount'],
          'actualLoadedReceiptImports': runtime['receiptImports'], 'actualCriticalModules': runtime['criticalModules'],
          'expandedSourceSnapshotManifestSha256': guard.SNAPSHOT_SHA, 'expandedSourceFileCount': 179,
          'executionContextSha256': guard.CONTEXT_SHA, 'protectedOriginalFileCount': 345,
          'runtimeAndSourceBeforeAfterUnchanged': True, 'frozenCoreOrPromptModified': False,
          'originalApplicationOrDatabaseExecuted': False, 'providerCalls': 0,
          'activationBindingExecuted': False, 'fullNewScopedPlanReviewBindingTested': False,
          'requiredBeforeAuthor': 'Actual independently approved expanded-input plan, exact full-plan activation grant and successful production binding/prepare',
          'publicationRequires': 'Unchanged wave completion plus approved per-document raw/text/structure evidence and independent native conversion checks',
          'businessProseAssembledByPython': False, 'formalPercentage': None, 'published': False}
target = REPORT / 'writer-root-code-audit-r04.json'
writer.write(target, record)
print(json.dumps({'status': record['status'], 'report': str(target), 'reportSha256': writer.sha(target)}, ensure_ascii=False))
