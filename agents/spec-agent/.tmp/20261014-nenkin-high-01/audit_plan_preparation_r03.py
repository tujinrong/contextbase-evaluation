"""Root metadata and runtime audit, without invoking an AI provider."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, importlib.util, json, sys
sys.dont_write_bytecode = True
RUN = Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/.tmp/20261014-nenkin-high-01')
REPORT = Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/report/20261014-nenkin-high-01')
helper = RUN / 'review_plan_with_scope_r03.py'
assert hashlib.sha256(helper.read_bytes()).hexdigest() == 'cec73d552fa2ae35f14f9b6151f4552ca0c8d7a3c451bcba92fef8f43b0944c2'
spec = importlib.util.spec_from_file_location('root_scope_preparation_audit', helper)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)
prep = guard.safe(REPORT / 'independent-plan-review/independent-plan-review-03/preparation.json')
expected = 'd214eb0f2cada55b65e3ed7906792c11e770b3f87b24c60ce7a843077e162369'
guard.require(guard.sha(prep) == expected, 'Preparation SHA differs')
record = guard.load(prep)
guard.require(record['helperSha256'] == guard.sha(helper) and record['helper'] == str(guard.safe(helper)), 'Helper pin differs')
guard.require(record['providerStarted'] is False and record['businessProseAuthored'] is False and
              record['coreOrFrozenPromptModified'] is False and record['agentRole'] == 'AG-SPEC' and
              record['reviewerRole'] == 'independent-plan-review' and record['deadline'] == guard.DEADLINE and
              record['timeout'] == 2400, 'Prepared role or timing differs')
runtime = guard.bootstrap()
guard.require(record['runtime'] == runtime, 'Actual loaded runtime differs')
pin = record['input']
current, definition, plan, manifest, raw_plan = guard.current_pin(
    guard.allowed_plan(pin['planFile']), pin['planSha256'], pin['planHandoffSha256'])
guard.require(current == pin and len(manifest['files']) == 179 and len(plan['documents']) == 63,
              'Current scope or plan differs')
prompt = guard.safe(record['promptFile'])
guard.require(prompt.parent == prep.parent and guard.sha(prompt) == record['promptSha256'] and
              prompt.read_bytes() == guard.build_prompt(pin, raw_plan, guard.read(guard.CONTEXT)).encode('utf-8'),
              'Full scope and original plan prompt differs')
from contextbase.ai import plan_review
guard.require(record['schemaSha256'] == guard.digest(json.dumps(plan_review.PLAN_REVIEW, sort_keys=True).encode()),
              'Frozen review schema differs')
guard.require(guard.allowed_job('independent-plan-review-03') == guard.safe(record['job']), 'Fresh job differs')
guard.recheck(pin, runtime)
guard.require(guard.sha(prep) == expected, 'Prepared metadata drift')
out = REPORT / 'root-plan-review-preparation-audit-r03.json'
result = {'schema': 'spec-agent-root-preparation-audit/1', 'createdUtc': datetime.now(timezone.utc).isoformat(),
          'status': 'APPROVED_EXACT_PREPARATION_FOR_PROVIDER', 'preparation': str(prep), 'preparationSha256': expected,
          'helperSha256': guard.sha(helper), 'promptSha256': guard.sha(prompt), 'planSha256': pin['planSha256'],
          'planHandoffSha256': pin['planHandoffSha256'], 'sourceSnapshotManifestSha256': guard.SNAPSHOT_SHA,
          'executionContextSha256': guard.CONTEXT_SHA, 'runtimeReceiptSha256': guard.RECEIPT_SHA,
          'documentCount': 63, 'specificationCount': 61, 'reportOnlyCount': 2,
          'runtimeFileCount': runtime['runtimeFileCount'], 'loadedImports': len(runtime['loadedImports']),
          'criticalModules': len(runtime['criticalModules']), 'inputRuntimeBeforeAfterUnchanged': True,
          'fullPromptMetadataVerified': True, 'providerCallsDuringAudit': 0, 'published': False}
with out.open('xb') as stream:
    stream.write((json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
print(json.dumps({'status': result['status'], 'report': str(out), 'sha256': guard.sha(out)}, ensure_ascii=False))
