"""Read-only driver audit with synthetic AST fragments and in-memory stubs; never launch AI."""
from __future__ import annotations

import ast
import contextlib
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
from pathlib import Path
from types import SimpleNamespace

from jsonschema import Draft202012Validator
from contextbase.ai import capsule, schemas, workflow

ROOT = Path.cwd().resolve()
REPORT = Path(__file__).resolve().parent
SESSION = ROOT / 'agents/reverse-agent/.tmp/20261013-session-pilot-01'
DRIVER = SESSION / 'focus_cycle.py'
SNAPSHOT = ROOT / 'agents/reverse-agent/.tmp/20261013-tuning-01/capsules/CSharp_ASPNET-assisted'


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pin(path):
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path), 'bytes': path.stat().st_size}


def write(name, data):
    (REPORT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def fragment(nodes, names):
    exec(compile(ast.Module(body=nodes, type_ignores=[]), '<pinned-driver-AST-fragment>', 'exec'), names)


def main():
    paths = [DRIVER, SESSION / 'focus_cycle-generation-03.py', SESSION / 'focus-round-03-config.json',
        SESSION / 'focus-round-04-config.json',
        ROOT / 'agents/reverse-agent/test-report/20261013-session-pilot-01/focus-round-03/scope.json',
        ROOT / 'agents/reverse-agent/test-report/20261013-session-pilot-01/focus-protected-check-04.json',
        ROOT / 'agents/reverse-agent/src/contextbase/ai/workflow.py',
        ROOT / 'agents/reverse-agent/src/contextbase/ai/provider.py',
        ROOT / 'agents/reverse-agent/src/contextbase/ai/prompts.py',
        ROOT / 'agents/reverse-agent/src/contextbase/ai/schemas.py',
        ROOT / 'agents/reverse-agent/src/contextbase/ai/validation.py']
    config = load(SESSION / 'focus-round-04-config.json')
    materials = capsule.verify(SNAPSHOT)
    actual_addenda = []
    for identity, files in config['sourceReviewAddenda'].items():
        for name in files:
            path = ROOT / name
            answer = load(path)
            assert answer['documentId'] == identity
            Draft202012Validator(schemas.REVIEW).validate(answer)
            workflow.references_valid(answer, materials)
            paths.append(path)
            actual_addenda.append(pin(path))
    before = [pin(path) for path in paths]
    write('audit-inputs-before.json', before)
    source = DRIVER.read_text(encoding='utf-8')
    tree = ast.parse(source)
    loop = next(item for item in ast.walk(tree) if isinstance(item, ast.For)
                and isinstance(item.target, ast.Name) and item.target.id == 'relative')
    identity = 'SYNTHETIC-DOCUMENT'
    accepted = []

    def addendum_case(payload, relative='agents/reverse-agent/test-report/synthetic-review.json'):
        reads = []
        names = {'config': {'sourceReviewAddenda': {identity: [relative]}}, 'identity': identity,
                 'repo': ROOT, 'addenda': [],
                 'read_pin': lambda path: (reads.append(path), payload)[1]}
        fragment([loop], names)
        return names['addenda'], reads

    payload = {'documentId': identity, 'unexpectedField': 'SYNTHETIC_NON_REVIEW_SENTINEL'}
    assert not Draft202012Validator(schemas.REVIEW).is_valid(payload)
    forwarded, _ = addendum_case(payload)
    assert forwarded == [payload]
    accepted.append({'case': 'invalid_REVIEW_shape_forwarded', 'result': 'REPRODUCED',
                     'actualExpectationDataUsed': False})
    invalid_ref = {'documentId': identity, 'approved': False, 'findings': [{
        'severity': 'minor', 'documentLocation': 'synthetic', 'defect': 'synthetic', 'repairDirection': 'synthetic',
        'references': [{'path': 'sources/not-present.cs', 'startLine': 0, 'endLine': 0}]}], 'unresolved': []}
    Draft202012Validator(schemas.REVIEW).validate(invalid_ref)
    try:
        workflow.references_valid(invalid_ref, materials)
    except ValueError:
        pass
    else:
        raise AssertionError('Synthetic invalid source range unexpectedly valid')
    assert addendum_case(invalid_ref)[0] == [invalid_ref]
    accepted.append({'case': 'non_snapshot_source_reference_forwarded', 'result': 'REPRODUCED'})
    for name in ['test-project1/spec-eval/synthetic.json',
                 'agents/reverse-agent/test-report/evaluator-only/synthetic.json']:
        try:
            addendum_case({'documentId': identity}, name)
        except ValueError:
            pass
        else:
            raise AssertionError('Protected addendum path unexpectedly accepted')
    accepted.append({'case': 'protected_addendum_paths', 'result': 'REJECTED_AS_REQUIRED'})
    try:
        addendum_case({'documentId': 'OTHER-SYNTHETIC'})
    except ValueError:
        pass
    else:
        raise AssertionError('Wrong addendum identity unexpectedly accepted')
    accepted.append({'case': 'wrong_addendum_identity', 'result': 'REJECTED_AS_REQUIRED'})

    task = next(item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == 'task')
    writes = []
    document_attempts = []

    def deadline_failure(*args, **kwargs):
        document_attempts.append(kwargs)
        raise RuntimeError('RuntimeErrorTimeLimit: synthetic less than30 seconds remain')

    names = {'definitions': {identity: {'id': identity, 'path': 'spec/detail/synthetic.md'}},
        'digest': lambda value: hashlib.sha256(value).hexdigest(), 'prepared': {identity: {'previousDraft': 'synthetic'}},
        'validate_document': lambda *args, **kwargs: [], 'capsule': SimpleNamespace(write_json=lambda *args: writes.append(args)),
        'workflow': SimpleNamespace(document=deadline_failure), 'snapshot': SNAPSHOT, 'jobs': SESSION / 'synthetic-not-created',
        'output': ROOT / 'synthetic-not-created', 'report': REPORT / 'synthetic-not-created',
        'config': {'deadline': config['deadline']}, 'json': json}
    fragment([task], names)
    with contextlib.redirect_stdout(io.StringIO()):
        failed = names['task'](identity)
    assert failed['status'] == 'FAILED' and len(document_attempts) == 1
    final_call = tree.body[-1].value
    final_value = final_call.args[1]
    envelope = eval(compile(ast.Expression(final_value), '<pinned-driver-result-dict>', 'eval'),
                    {'results': [failed], 'input_drift': [], 'runtime_drift': []})
    assert envelope['freshAnalysisInEachDocument'] is True
    accepted.append({'case': 'deadline_before_provider_failed_but_fresh_analysis_reported_true',
                     'result': 'REPRODUCED', 'providerCalls': 0, 'durableWrites': 0})

    wf_tree = ast.parse((ROOT / 'agents/reverse-agent/src/contextbase/ai/workflow.py').read_text(encoding='utf-8'))
    timeout_node = next(item for item in wf_tree.body if isinstance(item, ast.FunctionDef) and item.name == '_timeout')
    instant = datetime(2026, 10, 13, 0, 0, tzinfo=timezone.utc)

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return instant

    names = {'datetime': FixedDateTime, 'timezone': timezone}
    fragment([timeout_node], names)
    for seconds in [-1, 30]:
        try:
            names['_timeout'](1800, (instant + timedelta(seconds=seconds)).isoformat())
        except RuntimeError:
            pass
        else:
            raise AssertionError('Too-late provider phase unexpectedly allowed')
    assert names['_timeout'](1800, (instant + timedelta(seconds=90)).isoformat()) == 60
    accepted.append({'case': 'each_provider_phase_deadline_guard', 'result': '30SECOND_RESERVE_AND_TIMEOUT_CLAMP_PASS'})

    generation_scope = load(paths[4])
    assert sha(SESSION / 'focus_cycle-generation-03.py') == generation_scope['runnerSha256']
    assert sha(DRIVER) != generation_scope['runnerSha256']
    protected = load(paths[5])
    assert protected['total'] == protected['unchanged'] == 179
    assert protected['changed'] == protected['missing'] == 0
    after = [pin(path) for path in paths]
    assert before == after
    write('audit-inputs-after.json', after)
    write('audit-checks.json', {'status': 'AUDIT_CHECKS_PASS_WITH_REPRODUCED_GAPS', 'exitCode': 0,
        'driver': pin(DRIVER), 'round3PreservedRunner': pin(SESSION / 'focus_cycle-generation-03.py'),
        'round3RunnerMatchesHistoricalScope': True, 'actualConfig4AddendaSchemaAndSourceRanges': 'PASS',
        'actualConfig4AddendaPins': actual_addenda, 'syntheticChecks': accepted,
        'unchangedAuditInputPins': len(before), 'protectedFilesUnchanged': 179,
        'driverExecutedWhole': False, 'originalProgramsExecuted': False,
        'AIJobsStarted': 0, 'renderJobsStarted': 0, 'evaluatorSemanticContentsRead': False,
        'productionOrGeneratedMarkdownEdited': False})
    print(json.dumps({'status': 'AUDIT_CHECKS_PASS_WITH_REPRODUCED_GAPS', 'exitCode': 0,
                      'syntheticCases': len(accepted), 'unchangedAuditInputs': len(before), 'protectedUnchanged': 179}))


if __name__ == '__main__':
    main()
