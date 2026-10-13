"""Independent scoped verification of future-driver fixes using exact AST and memory-only stubs."""
from __future__ import annotations

import ast
import contextlib
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
from types import SimpleNamespace

from jsonschema import Draft202012Validator
from contextbase.ai import capsule, schemas, workflow

ROOT = Path.cwd().resolve()
REPORT = Path(__file__).resolve().parent / 'fix-confirmation'
SESSION = ROOT / 'agents/reverse-agent/.tmp/20261013-session-pilot-01'
DRIVER = SESSION / 'focus_cycle.py'
SNAPSHOT = ROOT / 'agents/reverse-agent/.tmp/20261013-tuning-01/capsules/CSharp_ASPNET-assisted'


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pin(path):
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path), 'bytes': path.stat().st_size}


def write(name, value):
    REPORT.mkdir(parents=True, exist_ok=True)
    (REPORT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def define(nodes, names):
    exec(compile(ast.Module(body=nodes, type_ignores=[]), '<future-driver-AST-functions>', 'exec'), names)


def main():
    assert sha(DRIVER) == '7634cf5f938ab127c93cdc5bc5e010425c034105958d5a65571b2acd4615bfc3'
    frozen_runner = SESSION / 'focus-round-04/runner-source.py'
    assert sha(frozen_runner) == 'cae525d98b1496f311539e5d515614a07d36b135b0b89a00eb11031d1f09b01e'
    config_path = SESSION / 'focus-round-04-config.json'
    config = load(config_path)
    scope_path = ROOT / (config['report'] + '/scope.json')
    scope = load(scope_path)
    assert scope['runnerSha256'] == sha(frozen_runner) != sha(DRIVER)
    materials = capsule.verify(SNAPSHOT)
    paths = [DRIVER, frozen_runner, config_path, scope_path, Path(__file__).resolve(),
             ROOT / 'agents/reverse-agent/src/contextbase/ai/schemas.py',
             ROOT / 'agents/reverse-agent/src/contextbase/ai/workflow.py']
    contexts = {}
    for identity, names in config['sourceReviewAddenda'].items():
        files = [ROOT / name for name in names]
        paths += files
        contexts[identity] = {'sourceBackedReviewAddenda': [load(path) for path in files]}
    before = [pin(path) for path in paths]
    write('inputs-before.json', before)
    tree = ast.parse(DRIVER.read_text(encoding='utf-8'))
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    names = {'Draft202012Validator': Draft202012Validator, 'schemas': schemas, 'workflow': workflow}
    define([functions['validate_addenda']], names)
    original = deepcopy(contexts)
    names['validate_addenda'](contexts, materials)
    assert contexts == original
    checks = [{'case': 'two_actual_addenda_preserved_after_schema_and_source_validation', 'status': 'PASS'}]
    identity = next(iter(contexts))

    def invalid_case(name, change):
        altered = deepcopy(contexts)
        change(altered[identity]['sourceBackedReviewAddenda'][0])
        try:
            names['validate_addenda'](altered, materials)
        except Exception as exc:
            checks.append({'case': name, 'status': 'REJECTED_AS_REQUIRED', 'errorType': type(exc).__name__})
        else:
            raise AssertionError(name + ' unexpectedly accepted')

    invalid_case('missing_required_review_field', lambda value: value.pop('approved'))
    invalid_case('unknown_source_path', lambda value: value['findings'][0]['references'][0].update(path='sources/not-in-capsule.txt'))
    invalid_case('zero_source_line', lambda value: value['findings'][0]['references'][0].update(startLine=0))
    invalid_case('empty_finding_references', lambda value: value['findings'][0].update(references=[]))

    writes = []
    calls = []
    digest = lambda value: hashlib.sha256(value).hexdigest()
    definition = {'id': identity, 'path': 'spec/detail/transport-check.md'}
    draft = {'documentId': identity, 'path': definition['path'], 'structureFindings': [], 'analysisExecutedInThisJob': True}

    class ReviewStructureConflict(Exception):
        pass

    def document_deadline(*args, **kwargs):
        calls.append('document_attempt')
        raise RuntimeError('RuntimeErrorTimeLimit: provider not started')

    def unverified(*args, **kwargs):
        calls.append('checkpoint_check')
        raise FileNotFoundError('No completed checkpoint')

    def review_failed(*args, **kwargs):
        calls.append('review_attempt')
        raise RuntimeError('Review transport failed')

    expected_job = SESSION / 'not-created' / digest(identity.encode())[:16]

    def verified(*args, **kwargs):
        assert args[2] == expected_job
        calls.append('verified_checkpoint_check')
        return {}, {'origin': 'same-job:analysis-verified-before-draft', 'analysisSha256': '0' * 64}, '1' * 64

    stub = SimpleNamespace(document=document_deadline, _resume_analysis=unverified,
                           review=review_failed, ReviewStructureConflict=ReviewStructureConflict)
    task_names = {'definitions': {identity: definition}, 'digest': digest, 'prepared': {identity: {'previousDraft': ''}},
        'validate_document': lambda *args, **kwargs: [], 'capsule': SimpleNamespace(write_json=lambda *args: writes.append(args)),
        'workflow': stub, 'snapshot': SNAPSHOT, 'jobs': SESSION / 'not-created', 'repo': ROOT,
        'output': ROOT / 'not-created', 'report': ROOT / 'not-created', 'config': config, 'json': json}
    define([functions['analysis_evidence'], functions['task']], task_names)
    with contextlib.redirect_stdout(io.StringIO()):
        failed = task_names['task'](identity)
    assert failed['status'] == 'FAILED' and 'draft' not in failed
    assert failed['analysisExecution']['completed'] is None
    assert failed['analysisExecution']['state'] == 'NOT_VERIFIED'
    envelope_ast = tree.body[-1].value.args[1]

    def envelope(results):
        return eval(compile(ast.Expression(envelope_ast), '<future-driver-result-dict>', 'eval'),
                    {'results': results, 'input_drift': [], 'runtime_drift': []})

    result = envelope([failed])
    assert result['freshAnalysisRequired'] is True
    assert result['freshAnalysisInEachDocument'] is None
    assert result['freshAnalysisEvidenceVerifiedForEveryDocument'] is False
    checks.append({'case': 'deadline_before_provider_completed_and_all_flags_null', 'status': 'PASS', 'providerCalls': 0})

    stub.document = lambda *args, **kwargs: draft
    stub._resume_analysis = verified
    with contextlib.redirect_stdout(io.StringIO()):
        failed_review = task_names['task'](identity)
    assert failed_review['status'] == 'FAILED' and failed_review['draft'] is draft
    assert failed_review['analysisExecution']['completed'] is True
    assert envelope([failed_review])['freshAnalysisInEachDocument'] is True
    assert envelope([failed_review, failed])['freshAnalysisInEachDocument'] is None
    checks.append({'case': 'review_failure_preserves_draft_and_only_verified_analysis_proof', 'status': 'PASS'})

    stub._resume_analysis = lambda *args, **kwargs: ({}, {'origin': 'legacy-recovery', 'analysisSha256': '0' * 64}, '1' * 64)
    legacy = task_names['analysis_evidence'](identity)
    assert legacy['completed'] is None and legacy['state'] == 'NOT_VERIFIED'
    checks.append({'case': 'legacy_origin_cannot_claim_fresh_same_job_analysis', 'status': 'REJECTED_AS_REQUIRED'})
    assert sha(frozen_runner) == scope['runnerSha256']
    after = [pin(path) for path in paths]
    assert before == after
    write('inputs-after.json', after)
    result = {'schema': 'reverse-ai-driver-fix-confirmation/1', 'status': 'PASS', 'exitCode': 0,
        'checkedFutureDriver': pin(DRIVER), 'unchangedRunningRound4Runner': pin(frozen_runner),
        'runningRound4WasNotUpgraded': True, 'checks': checks, 'unchangedInputPins': len(before),
        'actualAddendaShape': 'schemas.REVIEW; documentId/approved/findings/unresolved, no wrapper schema field',
        'inputExpectationTextUsed': False, 'evaluatorSemanticContentsRead': False,
        'originalApplicationExecuted': False, 'driverExecutedWhole': False,
        'AIJobsStarted': 0, 'renderJobsStarted': 0, 'durableStubWrites': 0,
        'productionOrGeneratedMarkdownEdited': False}
    write('result.json', result)
    print(json.dumps({'status': 'PASS', 'exitCode': 0, 'cases': len(checks),
                      'unchangedInputPins': len(before), 'runningRound4WasNotUpgraded': True}))


if __name__ == '__main__':
    main()
