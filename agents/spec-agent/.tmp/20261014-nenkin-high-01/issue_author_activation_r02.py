"""Issue a whole-plan root grant only after exact independent review verification."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, importlib.util, json, sys
sys.dont_write_bytecode = True
RUN = Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/.tmp/20261014-nenkin-high-01')
REPORT = Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/report/20261014-nenkin-high-01')
DRIVER = RUN / 'nenkin_writer_driver_r05.py'
DRIVER_SHA = '6b8e5456d96fabfda1bf43b6c17b6155167726492b10c0f9145473f243ee102c'
assert hashlib.sha256(DRIVER.read_bytes()).hexdigest() == DRIVER_SHA
spec = importlib.util.spec_from_file_location('root_author_activation_writer', DRIVER)
writer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(writer)
parser = argparse.ArgumentParser()
parser.add_argument('--plan', required=True)
parser.add_argument('--plan-sha256', required=True)
parser.add_argument('--plan-handoff-sha256', required=True)
parser.add_argument('--review', required=True)
parser.add_argument('--review-sha256', required=True)
parser.add_argument('--review-handoff-sha256', required=True)
parser.add_argument('--grant-name', required=True)
args = parser.parse_args()
plan = writer.plan_path(args.plan)
writer.require(writer.sha(plan) == writer.hash_arg(args.plan_sha256) and
               writer.sha(plan.parent / 'plan-handoff.json') == writer.hash_arg(args.plan_handoff_sha256),
               'Selected plan bytes differ')
review = writer.inside(args.review, RUN / 'jobs')
writer.require(review.name == 'plan-review-verified.json' and writer.sha(review) == writer.hash_arg(args.review_sha256) and
               writer.sha(review.parent / 'plan-review-handoff.json') == writer.hash_arg(args.review_handoff_sha256),
               'Selected review bytes differ')
assessment = writer.load(review)
writer.require(assessment['approved'] is True and not assessment['blockingUnresolved'] and
               not any(row['severity'] in {'critical', 'major'} for row in assessment['findings']),
               'Independent plan approval required')
audit = REPORT / 'writer-root-code-audit-r05.json'
writer.require(writer.sha(audit) == '673983cab479dbf6418ad0d816e30c9219e7cdfba2585fd255c0751212af897a',
               'Root code audit changed')
writer.require(args.grant_name.startswith('author-activation-r') and Path(args.grant_name).name == args.grant_name and
               args.grant_name.endswith('.json'), 'Fresh root-owned grant filename required')
target = writer.inside(REPORT / args.grant_name, REPORT)
writer.require(not target.exists(), 'Existing grant must not be reused')
grant = {
    'schema': 'spec-agent-author-activation/1', 'approved': True, 'agentRole': 'AG-SPEC', 'projectId': 'nenkin',
    'mode': 'source-only', 'runId': '20261014-nenkin-high-01', 'deadline': writer.DEADLINE,
    'driverSha256': DRIVER_SHA, 'capsuleManifestSha256': 'f074529043ff1c25ea53be34c16ae3a4788f137a1e3afb33c6214de7bf4c7445',
    'executionContextSha256': '8966757e00954241029817027efa85bafeb859beee5105b05c7c939c84470605',
    'runtimeReceiptSha256': writer.RECEIPT_SHA, 'codeAuditApproved': True,
    'codeAudit': {'path': str(writer.safe(audit)), 'sha256': writer.sha(audit)},
    'plan': {'path': str(plan), 'sha256': writer.sha(plan), 'handoffSha256': args.plan_handoff_sha256},
    'planReview': {'path': str(review), 'sha256': writer.sha(review), 'handoffSha256': args.review_handoff_sha256},
    'documents': [{key: item[key] for key in ('id', 'kind', 'path')} for item in writer.load(plan)['documents']],
    'protectedInputSealSha256': writer.sha(writer.PROTECTED_SEAL),
    'capsuleRoot': str(writer.safe(RUN / 'snapshot-input-02')),
    'executionContext': str(writer.safe(RUN / 'execution-context-input-02.json'))
}
writer.check_schema('activation', grant)
writer.write(target, grant)
pin, verified_plan, context = writer.binding(target, writer.sha(target))
record = {'schema': 'spec-agent-root-activation-binding/1', 'createdUtc': datetime.now(timezone.utc).isoformat(),
          'status': 'EXACT_ACTIVATION_BINDING_VERIFIED', 'activation': str(target), 'activationSha256': writer.sha(target),
          'input': pin, 'documentCount': len(verified_plan['documents']),
          'specificationCount': sum(d['kind'] != 'analysis-report' for d in verified_plan['documents']),
          'reportOnlyCount': sum(d['kind'] == 'analysis-report' for d in verified_plan['documents']),
          'actualProviderCalls': 0, 'applicationExecuted': False, 'published': False}
audit_target = REPORT / (target.stem + '-binding.json')
writer.write(audit_target, record)
print(json.dumps({'status': record['status'], 'activation': str(target), 'activationSha256': writer.sha(target),
                  'bindingAudit': str(audit_target), 'bindingAuditSha256': writer.sha(audit_target)}, ensure_ascii=False))
