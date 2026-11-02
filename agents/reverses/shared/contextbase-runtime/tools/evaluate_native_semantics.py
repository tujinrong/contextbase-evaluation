"""Run one source-only native analysis arm and prepare an ungraded review view.

The default is a no-model dry run. Use a fresh --work path for each arm and
--execute to invoke the real provider. Judging material is a sibling of source,
never part of the source snapshot, request, or either role's instructions.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time


RUNTIME = Path(__file__).resolve().parents[1]
FIXTURE = RUNTIME / 'tests/fixtures/native-semantics'
sys.path.insert(0, str(RUNTIME / 'src'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def now():
    return datetime.now(timezone.utc).isoformat()


def fixture_inputs(fixture=FIXTURE):
    """Verify the checked-in evaluation boundary before creating any session."""
    from contextbase_runtime.contracts import validate_request

    fixture = Path(fixture).resolve()
    source = fixture / 'source'
    request = load(fixture / 'request.json')
    judging = load(fixture / 'judging.json')
    validate_request(request)
    entries = list(source.rglob('*'))
    files = sorted(p for p in entries if p.is_file())
    if not files or any(p.is_symlink() for p in entries) or any(p.suffix != '.cs' for p in files):
        raise ValueError('The evaluation source capsule must contain only regular C# files')
    if judging.get('sourcePath') not in {p.relative_to(source).as_posix() for p in files}:
        raise ValueError('Judging source path is outside the capsule')
    if digest(source / judging['sourcePath']) != judging.get('sourceSha256'):
        raise ValueError('The judging checklist does not match the frozen source bytes')
    source_text = (source / judging['sourcePath']).read_text(encoding='utf-8')
    if any(anchor not in source_text for case in judging['cases'] for anchor in case['evidenceAnchors']):
        raise ValueError('A judging evidence anchor is absent from the frozen source')
    return source, request, judging, files


def provider_observations(session_work):
    providers, tools = [], Counter()
    for path in sorted(session_work.glob('tasks/*/native/*/provider/result.json')):
        data = load(path)
        meta = data.get('metadata', {})
        providers.append({'path': str(path), 'sha256': digest(path),
                          'role': meta.get('role_id'), 'seconds': meta.get('seconds'),
                          'instructionsSha256': meta.get('model_instructions_sha256'),
                          'usage': data.get('usage'), 'configuration': meta.get('configuration'),
                          'capabilities': meta.get('role_capabilities')})
    events = []
    for path in sorted(session_work.glob('tasks/*/native/*/provider/events.jsonl')):
        completed, failed = 0, 0
        for line in path.read_text(encoding='utf-8').splitlines():
            event = json.loads(line)
            item = event.get('item', {})
            if event.get('type') == 'item.completed':
                completed += 1
                if item.get('type') == 'mcp_tool_call':
                    tools[item.get('tool')] += 1
                    failed += item.get('status') == 'failed'
        events.append({'path': str(path), 'sha256': digest(path),
                       'completedItems': completed, 'failedToolCalls': failed})
    return {'providers': providers, 'eventLogs': events, 'toolCalls': dict(tools)}


def citation_view(reference, source):
    """Check exact source binding; never infer that a citation proves a claim."""
    result = {'reference': deepcopy(reference), 'sourceReferenceValid': False}
    try:
        source.verify_evidence(reference)
        result['excerpt'] = source.read(reference['path'], reference['startLine'], reference['endLine'])
        result['sourceReferenceValid'] = True
    except (KeyError, TypeError, ValueError, OSError) as exc:
        result['error'] = {'type': type(exc).__name__, 'message': str(exc)}
    return result


def review_view(session_work, source, judging):
    """Extract exact claims and evidence for a human, with artifact JSON pointers."""
    candidates, verifications = [], []
    for path in sorted((session_work / 'candidates').glob('*.json')):
        envelope = load(path)
        payload = envelope['payload']
        rows = []
        for index, record in enumerate(payload.get('answer', {}).get('records', [])):
            pointer = f'/payload/answer/records/{index}'
            rows.append({'recordPointer': pointer, 'record': record,
                         'citations': [{'citationPointer': f'{pointer}/evidence/{number}',
                                        **citation_view(ref, source)}
                                       for number, ref in enumerate(record.get('evidence', []))]})
        candidates.append({'path': str(path), 'fileSha256': digest(path),
                           'contentSha256': envelope['sha256'], 'records': rows})
    for path in sorted((session_work / 'verifications').glob('*.json')):
        envelope = load(path)
        verifications.append({'path': str(path), 'fileSha256': digest(path),
                              'contentSha256': envelope['sha256'],
                              'answerPointer': '/payload/answer',
                              'answer': envelope['payload'].get('answer')})
    return {'schema': 'contextbase-native-semantics-review/1',
            'semanticVerdict': 'not-automatically-graded',
            'meaning': 'Reference validity checks file bytes and line ranges, not semantic support, '
                       'coverage or actual model consumption. Review every claim and contradiction manually.',
            'judging': judging,
            'manualResults': [{'caseId': case['id'], 'status': 'pending', 'recordPointers': [],
                               'reason': ''} for case in judging['cases']],
            'candidates': candidates, 'independentVerifications': verifications}


def run_evaluation(work, roles, *, execute=False, timeout=900, fixture=FIXTURE,
                   agent_factory=None, fingerprint=None):
    """Prepare one fresh arm; the injectable factory lets tests avoid model calls."""
    from contextbase_runtime.controller import engine_fingerprint
    from contextbase_runtime.project_analysis import ProjectAnalysisAgent
    from contextbase_runtime.roles import validate_roles
    from contextbase_runtime.sources import SourceAccess

    fixture_source, request, judging, files = fixture_inputs(fixture)
    work = Path(work).resolve()
    if work == fixture_source or fixture_source in work.parents or work in fixture_source.parents:
        raise ValueError('Evaluation work and source capsule must not overlap')
    if work.exists():
        raise FileExistsError(f'Evaluation work must be fresh: {work}')
    if timeout <= 0:
        raise ValueError('Per-role timeout must be positive')
    if set(roles) != {'analysis', 'verification'}:
        raise ValueError('Both frozen role specifications are required')
    roles = validate_roles(roles)
    models = {role.get('model') for role in roles.values()}
    efforts = {role.get('model_reasoning_effort') for role in roles.values()}
    if len(models) != 1 or None in models or len(efforts) != 1 or None in efforts:
        raise ValueError('Both roles must freeze the same explicit model and reasoning effort')
    frozen = fingerprint or engine_fingerprint
    engine_before = frozen()
    work.mkdir(parents=True)
    # Formal fixtures live under tests/, which production source policy excludes.
    # Copy only the approved C# bytes into this isolated input capsule.
    source_root = work / 'capsule'
    source_root.mkdir()
    for original in files:
        target = source_root / original.relative_to(fixture_source)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(original.read_bytes())
        if digest(original) != digest(target):
            raise ValueError('The isolated capsule differs from the frozen fixture bytes')
    snapshot = SourceAccess.create(source_root, work / 'input-snapshot',
        project_id=request['projectId'], allowed_paths=request['allowedPaths'], excluded_paths=request['excludedPaths'])
    expected_paths = sorted(p.relative_to(fixture_source).as_posix() for p in files)
    if sorted(row['path'] for row in snapshot.manifest['files']) != expected_paths:
        raise ValueError('The sealed source inventory differs from the isolated capsule')
    plan = {'schema': 'contextbase-native-semantics-plan/1', 'startedUtc': now(),
            'mode': 'execute-native-provider' if execute else 'dry-run-no-provider-calls',
            'fixtureSourceRoot': str(fixture_source), 'sourceRoot': str(source_root),
            'sessionWork': str(work / 'analysis'),
            'sourceFiles': [{'path': p.relative_to(fixture_source).as_posix(), 'sha256': digest(p)} for p in files],
            'snapshotId': snapshot.snapshot_id, 'request': request,
            'requestSha256': digest(Path(fixture) / 'request.json'),
            'judgingSha256': digest(Path(fixture) / 'judging.json'),
            'judgingDeliveredToModel': False, 'sourceProgramsExecuted': False,
            'roles': {key: {field: spec.get(field) for field in ('id', 'instructions_path',
                'instructions_sha256', 'model', 'model_reasoning_effort', 'capabilities')}
                for key, spec in roles.items()},
            'engineBefore': engine_before, 'perRoleTimeoutSeconds': timeout}
    write(work / 'plan.json', plan)
    # This is an evaluation artifact, outside source and the agent's work directory.
    write(work / 'judging.json', judging)
    start = time.perf_counter()
    result, error, exported = None, None, None
    initialization_seconds = None
    try:
        if execute:
            factory = agent_factory or ProjectAnalysisAgent
            agent = factory.create(source_root, work / 'analysis', deepcopy(request),
                native_mode=True, joint_analysis=True, role_specs=deepcopy(roles))
            initialization_seconds = time.perf_counter() - start
            result = agent.run(timeout=timeout)
            write(work / 'run-result.json', result)
            if result.get('status') == 'complete':
                exported = agent.export()
                write(work / 'export.json', exported)
    except Exception as exc:
        error = {'type': type(exc).__name__, 'message': str(exc)}
    finished = now()
    seconds = time.perf_counter() - start
    observations = provider_observations(work / 'analysis')
    review = review_view(work / 'analysis', snapshot, judging)
    write(work / 'review-view.json', review)
    report = {**plan, 'finishedUtc': finished, 'seconds': seconds,
              'initializationSeconds': initialization_seconds,
              'status': result.get('status') if result else 'failed' if error else 'prepared',
              'error': error, 'acceptedRequirements': (result or {}).get('session', {}).get('acceptedRequirements', []),
              'exportContentSha256': (exported or {}).get('sha256'),
              'engineAfter': frozen(), 'semanticVerdict': 'pending-manual-review',
              'candidateCount': len(review['candidates']),
              'verificationCount': len(review['independentVerifications']),
              'reviewViewPath': str(work / 'review-view.json'), **observations}
    report['engineUnchanged'] = report['engineBefore'] == report['engineAfter']
    write(work / 'report.json', report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', required=True, type=Path, help='Fresh evaluation directory, outside the fixture source.')
    parser.add_argument('--execute', action='store_true', help='Invoke the native model provider for both roles.')
    parser.add_argument('--analysis-instructions', type=Path)
    parser.add_argument('--verification-instructions', type=Path)
    parser.add_argument('--model', help='Freeze the same model in both roles; otherwise inherit the resolved user selection.')
    parser.add_argument('--reasoning-effort', '--effort', dest='effort', help='Freeze the same effort in both roles.')
    parser.add_argument('--timeout', type=int, default=900, help='Timeout in seconds for each role execution.')
    args = parser.parse_args(argv)
    from contextbase_runtime.roles import normalize_roles
    config = {operation: {**({'instructions': str(path.resolve())} if path else {}),
                          **({'model': args.model} if args.model else {}),
                          **({'model_reasoning_effort': args.effort} if args.effort else {})}
              for operation, path in (('analysis', args.analysis_instructions),
                                      ('verification', args.verification_instructions))}
    roles = normalize_roles(config, base_dir=Path.cwd())
    report = run_evaluation(args.work, roles, execute=args.execute, timeout=args.timeout)
    print(json.dumps({key: report[key] for key in ('status', 'mode', 'seconds', 'engineUnchanged',
          'candidateCount', 'verificationCount', 'semanticVerdict', 'reviewViewPath', 'error')}, ensure_ascii=False, indent=2))
    return 1 if report['error'] or not report['engineUnchanged'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
