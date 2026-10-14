"""Root exact review preparation audit; no AI provider invocation."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, importlib.util, json, sys
sys.dont_write_bytecode = True
RUN = Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/.tmp/20261014-nenkin-high-01')
REPORT = Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/report/20261014-nenkin-high-01')
helper = RUN / 'review_plan_with_scope_r05.py'
assert hashlib.sha256(helper.read_bytes()).hexdigest() == '9d5ec80c5fd3efe2044302104a64ff928777fd98d3cdd0e0c8ef0ff301ee5802'
spec = importlib.util.spec_from_file_location('root_scope_preparation_audit_r04', helper)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)
parser = argparse.ArgumentParser()
parser.add_argument('--preparation-sha256', required=True)
args = parser.parse_args()
prep = guard.safe(REPORT / 'independent-plan-review/independent-plan-review-04/preparation.json')
expected = guard.hash_arg(args.preparation_sha256)
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
guard.require(pin['planSha256'] == 'e14b5e5acd96aed44c800209efbe452d094cb595f7d57da097b8c9a4a7bc9ee3' and
              pin['planHandoffSha256'] == '2815a418a728f5ba8e71ec8a8d0cf7308b1920ecdf283b6ec9288e0831b68660',
              'Actual current plan pin differs')
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
guard.require(guard.allowed_job('independent-plan-review-04') == guard.safe(record['job']), 'Fresh job differs')
guard.recheck(pin, runtime)
guard.require(guard.sha(prep) == expected, 'Prepared metadata drift')
out = REPORT / 'root-plan-review-preparation-audit-r04.json'
result = {'schema': 'spec-agent-root-preparation-audit/1', 'createdUtc': datetime.now(timezone.utc).isoformat(),
          'status': 'APPROVED_EXACT_PREPARATION_FOR_PROVIDER', 'preparation': str(prep), 'preparationSha256': expected,
          'helperSha256': guard.sha(helper), 'promptSha256': guard.sha(prompt), 'planSha256': pin['planSha256'],
          'planHandoffSha256': pin['planHandoffSha256'], 'sourceSnapshotManifestSha256': guard.SNAPSHOT_SHA,
          'executionContextSha256': guard.CONTEXT_SHA, 'runtimeReceiptSha256': guard.RECEIPT_SHA,
          'documentCount': 63, 'specificationCount': 61, 'reportOnlyCount': 2,
          'runtimeFileCount': runtime['runtimeFileCount'], 'loadedImports': len(runtime['loadedImports']),
          'criticalModules': len(runtime['criticalModules']), 'inputRuntimeBeforeAfterUnchanged': True,
          'fullPromptMetadataVerified': True, 'scopeTransportDescriptionCorrected': True,
          'providerCallsDuringAudit': 0, 'published': False}
with out.open('xb') as stream:
    stream.write((json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
print(json.dumps({'status': result['status'], 'report': str(out), 'sha256': guard.sha(out)}, ensure_ascii=False))
