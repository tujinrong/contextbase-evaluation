"""Explicit, narrowly compatible maintenance of stopped author checkpoints.

This is not an engine-check bypass. It authenticates one known predecessor,
replays every completed component without inference, and records the original
session and state before activating a new execution epoch. No acceptance is
imported. The normal Session constructor remains unchanged and fail-closed.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import tempfile
import uuid

from . import contracts as c, controller, incremental, investigation
from .agent import AgentWorkspace
from .facts import FactIndex, extractor_fingerprint
from .paths import safe_path
from .sources import SourceAccess
from .storage import ArtifactStore


VERSION = 'contextbase-checkpoint-upgrade/1'
SUPPORTED_ENGINE_SHA256 = '78ced2aba044e28ec922d0022c363a1c5812f8395936b129b6e0fc47c6811474'
SUPPORTED_TARGET_ENGINE_SHA256 = '4c66372b2352a1fb83047f38db5fd8bc3e1c851c75b3c794f91c18b2da529780'
_ENGINE_FILES = ('agents.py', 'contracts.py', 'controller.py', 'storage.py',
                 'sources.py', 'adapters.py', 'paths.py', 'provider.py', 'catalog.py',
                 'facts.py', 'wire.py', 'repair.py', 'evidence.py', 'evidence_dialog.py',
                 'incremental.py', 'investigation.py', 'review_set.py', 'material_window.py')
_PACKAGES = ('jsonschema', 'tree-sitter', 'tree-sitter-c-sharp', 'tree-sitter-java')
_COMPATIBLE_FILES = frozenset({'incremental.py'})
_PENDING = 'runtime-upgrades/closure-pending.json'
REVIEW_SOURCE_ENGINE_SHA256 = SUPPORTED_TARGET_ENGINE_SHA256
# This pair is pinned after the review-only schema/context compatibility tests.
REVIEW_TARGET_ENGINE_SHA256 = '5b4157a97836890407be9214ba6eb5a069b48fe030fa5493649bd0d3c4026931'
_REVIEW_PENDING = 'runtime-upgrades/review-pending.json'


class _EndPrefix(Exception):
    pass


def _versions():
    versions = {}
    for package in _PACKAGES:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    return versions


def _runtime(previous, old_engine, review=False):
    if old_engine != (REVIEW_SOURCE_ENGINE_SHA256 if review else SUPPORTED_ENGINE_SHA256):
        raise ValueError('Checkpoint upgrade requires the specifically supported prior engine')
    previous = safe_path(previous)
    old_files = {name: safe_path(previous / name).read_text(encoding='utf-8') for name in _ENGINE_FILES}
    versions = _versions()
    if c.digest({'files': old_files, 'dependencies': versions}) != old_engine:
        raise ValueError('The previous runtime or dependency versions do not match the recorded engine')
    current = Path(controller.__file__).parent
    new_files = {name: safe_path(current / name).read_text(encoding='utf-8') for name in _ENGINE_FILES}
    changed = sorted(name for name in _ENGINE_FILES if old_files[name] != new_files[name])
    compatible = {'incremental.py', 'review_set.py'} if review else _COMPATIBLE_FILES
    if set(changed) - compatible:
        raise ValueError('Runtime changes exceed the obligation-closure compatibility boundary')
    return {'changedFiles': changed, 'dependencies': versions,
            'previousFileHashes': {name: hashlib.sha256(text.encode('utf-8')).hexdigest()
                                   for name, text in old_files.items()}}


def _reader(store, config, state, source, index, agent_type):
    # This private reader only reconstructs the historical host context. It is
    # never returned to a caller and cannot issue or record a task. It does not
    # execute the old runtime or change the public Session fingerprint rule.
    class HistoricalContextReader(AgentWorkspace):
        def __init__(self):
            self.store, self.config, self.source = store, config, source
            self.agent = agent_type.__new__(agent_type)

        def _state(self):
            return deepcopy(state)

        def fact_index(self):
            return index

        def _prepare(self, *args, **kwargs):
            raise ValueError('Historical context validation cannot issue tasks')

        def _record(self, *args, **kwargs):
            raise ValueError('Historical context validation cannot record results')

    return HistoricalContextReader()


def _source(store, config):
    source = SourceAccess.open(store.path('snapshot'))
    source.verify()
    if source.snapshot_id != config['snapshotId']:
        raise ValueError('Checkpoint snapshot binding changed')
    request = config['request']
    manifest = source.manifest
    with tempfile.TemporaryDirectory(prefix='checkpoint-source-probe-', dir=store.root.parent) as directory:
        probe = SourceAccess.create(Path(manifest['sourceRoot']), Path(directory) / 'snapshot',
            project_id=request['projectId'], allowed_paths=request['allowedPaths'],
            excluded_paths=request['excludedPaths'])
        if probe.snapshot_id != source.snapshot_id or probe.manifest != manifest:
            raise ValueError('Original source inventory changed; checkpoints cannot cross snapshots')
    indexes = sorted(store.path('source-facts').glob('*.json'))
    if len(indexes) != 1:
        raise ValueError('Upgrade requires one existing source-fact index')
    document = store.get(indexes[0].relative_to(store.root).as_posix())
    index = FactIndex(document, source)
    index.validate()
    if document['extractorSha256'] != extractor_fingerprint():
        raise ValueError('Source-fact extraction rules changed')
    return source, index


def _replay_prefix(store, config, state, source, index, agent_type):
    workflows = list(store.path('workflows').glob('*/state.json'))
    if len(workflows) != 1:
        raise ValueError('This compatibility upgrade requires one stopped author workflow')
    work = ArtifactStore(workflows[0].parent)
    checkpoint = work.get('state.json')
    trace = checkpoint['trace']
    if (checkpoint['schema'] != incremental.VERSION or not trace or checkpoint.get('rejections')
            or checkpoint['basis']['operation'] != 'extract'):
        raise ValueError('Only a valid completed author prefix is compatible')
    first = work.get('calls/' + trace[0] + '/setup.json')
    root_id = first['task']['rootTaskId']
    task = store.get('tasks/' + root_id + '/request.json')
    context = store.get('tasks/' + root_id + '/context.json')
    if (incremental._basis(task) != checkpoint['basis']
            or work.root.name != c.digest(checkpoint['basis'])
            or task['sessionId'] != config['id'] or task['snapshotId'] != source.snapshot_id
            or task['goalSha256'] != c.digest(config['request']['goal'])
            or task['sourceFactsSha256'] != index.sha256
            or state['tasks'].get(root_id) != 'failed'
            or task['stage'] != 'discovery' or task['operation'] != 'extract'
            or task['origin'] != 'host-executed' or task.get('feedback') is not None
            or task['baseVersion'] != 0 or task['baseRevision'] is not None):
        raise ValueError('Historical root task bindings changed')
    reader = _reader(store, config, state, source, index, agent_type)
    if reader._context(task, False) != context:
        raise ValueError('Historical root context no longer matches the original request/source')
    instruction = reader._incremental_instruction(task)
    used, events, files = [], [], {}

    def remember(relative):
        files[relative] = hashlib.sha256(store.path(relative).read_bytes()).hexdigest()

    def invoke(phase, unit, materials, schema):
        if len(used) == len(trace):
            raise _EndPrefix()
        pointer = trace[len(used)]
        call = 'calls/' + pointer
        setup = work.get(call + '/setup.json')
        if phase not in {'plan', 'draft'} or setup['phase'] != phase:
            raise ValueError('Only completed plan/draft checkpoints can be upgraded')
        answer, returned = incremental._dialog(source, index, work, task, context, phase, unit,
            materials, instruction, schema, None, None, lambda: None, pointer)
        if returned != pointer:
            raise ValueError('Historical trace identity changed')
        complete = work.get(call + '/complete.json')
        for filename in ('setup.json', 'complete.json'):
            remember((work.root / call / filename).relative_to(store.root).as_posix())
        for number in range(1, len(complete['rounds']) + 1):
            relative = call + f'/round-{number:04d}.json'
            row = work.get(relative)
            raw_relative = call + f'/round-{number:04d}-response.json'
            if work.get(raw_relative) != row['response']:
                raise ValueError('Historical trace response differs from the saved raw response')
            for name in (relative, raw_relative):
                remember((work.root / name).relative_to(store.root).as_posix())
        if phase == 'draft':
            reader.agent.validate_extraction(answer)
            # A unit schema binds the fact index through its task rather than
            # repeating sourceFactsSha256 in every small draft response.
            index.validate_usage({'records': answer['records'], 'factUsage': answer['factUsage'],
                                  'sourceFactsSha256': task['sourceFactsSha256']}, index.sha256)
            events.append({'unit': deepcopy(unit), 'answer': deepcopy(answer)})
        used.append(pointer)
        return answer

    invoke.commit = lambda: None
    invoke.reject = lambda error: None
    try:
        incremental._drive(task, context, invoke)
    except _EndPrefix:
        pass
    else:
        raise ValueError('Upgrade prefix unexpectedly produced a complete extraction')
    if used != trace:
        raise ValueError('Not every completed trace component was replayed')
    reduced = investigation.reduce_drafts(task, events)
    for relative in ('session.json', 'state.json', 'agent.json', 'snapshot/manifest.json',
                     'snapshot/seal.json', 'tasks/' + root_id + '/request.json',
                     'tasks/' + root_id + '/context.json'):
        if relative not in {'session.json', 'state.json'}:
            remember(relative)
    remember(workflows[0].relative_to(store.root).as_posix())
    remember(next(store.path('source-facts').glob('*.json')).relative_to(store.root).as_posix())
    return {'completedCalls': len(used), 'draftRecordCount': len(reduced['records']),
            'draftKindCounts': dict(Counter(row['kind'] for row in reduced['records'])),
            'unknownCount': len(reduced['unknowns']), 'followupCount': len(reduced['followups']),
            'draftMaterialSha256': c.digest(reduced), 'traceSha256': c.digest(trace),
            'files': files}


def _previous_audit(store, config, expected, review=False):
    """Pin an existing completed upgrade without replacing its history/journal."""
    identifier = config.get('runtimeUpgrade')
    if identifier is None:
        if expected is not None or review:
            raise ValueError('The previous audit pin does not belong to this session')
        return
    if (not isinstance(identifier, str) or len(identifier) != 64
            or any(character not in '0123456789abcdef' for character in identifier)
            or expected != identifier):
        raise ValueError('The previous audit must be explicitly pinned to the existing session')
    try:
        audit = store.get('runtime-upgrades/' + identifier + '.json')
        committed = store.get('runtime-upgrades/' + identifier + '-committed.json')
    except (OSError, ValueError) as error:
        raise ValueError('The previous audit is missing or damaged') from error
    if (c.digest(audit) != identifier or audit.get('schema') != VERSION
            or audit.get('reason') != ('obligation-closure-package' if review else 'directory-query-and-request-recovery')
            or audit['oldEngineSha256'] != audit['oldSession']['engineSha256']
            or audit['newEngineSha256'] != config['engineSha256']):
        raise ValueError('The previous audit engine or policy binding changed')
    prior_config = {**deepcopy(audit['oldSession']), 'engineSha256': audit['newEngineSha256'],
                    'runtimeUpgrade': identifier}
    prior_state = {**deepcopy(audit['oldState']), 'sessionSha256': c.digest(prior_config),
                   'executionEpoch': audit['oldState']['executionEpoch'] + 1}
    if prior_config != config or committed != {
            'schema': VERSION, 'auditSha256': identifier,
            'sessionSha256': c.digest(prior_config), 'stateSha256': c.digest(prior_state)}:
        raise ValueError('The previous audit commit or session binding changed')


def _replay_candidate(store, config, state, source, index, agent_type, identifier):
    """Replay the complete frozen author transcript; no reviewer result is reused."""
    relative = 'candidates/' + identifier + '.json'
    candidate = store.get(relative)
    task = store.get('tasks/' + candidate['taskId'] + '/request.json')
    context = store.get('tasks/' + task['id'] + '/context.json')
    if (c.digest(candidate) != identifier or c.digest(candidate['view']) != candidate['viewSha256']
            or candidate['sessionId'] != config['id'] or candidate['snapshotId'] != source.snapshot_id
            or task['sessionId'] != config['id'] or task['snapshotId'] != source.snapshot_id
            or task['goalSha256'] != c.digest(config['request']['goal'])
            or task['sourceFactsSha256'] != index.sha256 or task['operation'] != 'extract'
            or task['stage'] != 'discovery' or task['origin'] != 'host-executed'
            or task.get('feedback') is not None or candidate.get('feedback') is not None
            or task['baseVersion'] != 0 or task['baseRevision'] is not None
            or candidate['baseVersion'] != 0 or candidate['baseRevision'] is not None
            or state['tasks'].get(task['id']) != 'finished'
            or candidate['provenance'].get('kind') != 'host-composed'):
        raise ValueError('Frozen candidate or author task binding changed')
    reader = _reader(store, config, state, source, index, agent_type)
    if reader._context(task, False) != context:
        raise ValueError('Frozen author context changed')
    reader._replay_evidence(task, candidate)
    if reader._proposal_view(state, task, candidate['answer']) != candidate['view']:
        raise ValueError('Frozen candidate view changed')
    manifest = store.get('tasks/' + task['id'] + '/incremental.json')
    author = ArtifactStore(store.path(manifest['workflow']))
    author_checkpoint = author.get('state.json')
    if author_checkpoint['trace'] != manifest['trace'] or author_checkpoint.get('rejections'):
        raise ValueError('Frozen author checkpoint changed')
    rounds = 0
    phases = Counter()
    for pointer in manifest['trace']:
        call = 'calls/' + pointer
        phases[author.get(call + '/setup.json')['phase']] += 1
        complete = author.get(call + '/complete.json')
        for number in range(1, len(complete['rounds']) + 1):
            row = author.get(call + f'/round-{number:04d}.json')
            if row['response'] != author.get(call + f'/round-{number:04d}-response.json'):
                raise ValueError('Frozen author raw response changed')
            rounds += 1
    for path in store.path('workflows').glob('*/state.json'):
        if path.parent == author.root:
            continue
        checkpoint = store.get(path.relative_to(store.root).as_posix())
        basis = checkpoint['basis']
        if (basis['operation'] != 'verify' or basis['candidate'] != identifier
                or checkpoint['trace']):
            raise ValueError('Only rejected, uncompleted reviews of this frozen candidate are compatible')
    # Bind every historical byte, including invalid review diagnostics, without
    # granting them authority under the replacement review schema.
    files = {path.relative_to(store.root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
             for path in store.root.rglob('*') if path.is_file()
             and path.name not in {'session.json', 'state.json'}
             and path.relative_to(store.root).as_posix() != 'session.lock'
             and 'runtime-upgrades' not in path.relative_to(store.root).parts}
    # Workflow state is evidence too; only the root mutable state was excluded.
    for path in store.path('workflows').glob('*/state.json'):
        files[path.relative_to(store.root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {'frozenCandidateSha256': identifier, 'viewSha256': candidate['viewSha256'],
            'candidateFileSha256': hashlib.sha256(store.path(relative).read_bytes()).hexdigest(),
            'completedCalls': len(manifest['trace']), 'authorRounds': rounds, 'authorPhases': dict(phases),
            'draftRecordCount': len(candidate['answer']['records']),
            'traceSha256': c.digest(manifest['trace']), 'files': files}


def _validate(store, config, state, request, agent_type, previous_audit_sha256=None, frozen_candidate=None):
    review = frozen_candidate is not None
    _previous_audit(store, config, previous_audit_sha256, review)
    c.validate_request(request)
    if config['request'] != request:
        raise ValueError('Upgrade requires the exact original request')
    if (config.get('schema') != c.VERSION or config.get('incrementalPolicy') != incremental.VERSION
            or 'evidencePolicy' in config
            or state['sessionSha256'] != c.digest(config)
            or state['status'] not in ({'stopped', 'cancelled'} if review else {'stopped'})
            or state['version'] != 0 or state['revision'] is not None
            or state['acceptedRequirements'] or state['verifications']
            or state['candidates'] != ([frozen_candidate] if review else [])
            or 'issued' in state['tasks'].values() or state['invalidatedRequirements']):
        raise ValueError('Upgrade requires a stopped, unadopted incremental author workspace')
    if agent_type.stage != 'discovery' or store.get('agent.json') != agent_type.binding():
        raise ValueError('Agent implementation binding changed')
    if store.path('project.json').exists():
        project = store.get('project.json')
        manifest = SourceAccess.open(store.path('snapshot')).manifest
        if (project.get('agent') != agent_type.name or project.get('projectId') != request['projectId']
                or project.get('requestSha256') != c.digest(request)
                or project.get('source') != manifest['sourceRoot']):
            raise ValueError('Project profile/source/request binding changed')
    source, index = _source(store, config)
    if review:
        return _replay_candidate(store, config, state, source, index, agent_type, frozen_candidate)
    return _replay_prefix(store, config, state, source, index, agent_type)


def _replace_session(store, config):
    relative = 'upgrade-session-' + uuid.uuid4().hex + '.tmp'
    store.put(relative, config)
    try:
        os.replace(store.path(relative), store.path('session.json'))
    finally:
        store.path(relative).unlink(missing_ok=True)


def upgrade(work, previous_runtime, request, agent_type, *, dry_run=False, previous_audit_sha256=None,
            frozen_candidate=None):
    """Validate/activate this one compatible upgrade, with restartable journaling."""
    store = ArtifactStore(safe_path(work))
    review = frozen_candidate is not None
    pending_path = _REVIEW_PENDING if review else _PENDING
    with store.transaction() as observed_state:
        observed_config = store.get('session.json')
        pending = store.get(pending_path) if store.path(pending_path).exists() else None
        if pending:
            audit_id = pending['auditSha256']
            audit = store.get('runtime-upgrades/' + audit_id + '.json')
            if c.digest(audit) != audit_id or pending['schema'] != VERSION:
                raise ValueError('Interrupted upgrade audit binding changed')
            config, state = audit['oldSession'], audit['oldState']
        else:
            config, state = observed_config, observed_state
        runtime = _runtime(previous_runtime, config['engineSha256'], review)
        current_engine = controller.engine_fingerprint()
        if current_engine != (REVIEW_TARGET_ENGINE_SHA256 if review else SUPPORTED_TARGET_ENGINE_SHA256):
            raise ValueError('Checkpoint upgrade requires the specifically supported target engine')
        if current_engine == config['engineSha256']:
            raise ValueError('No compatible runtime change is present')
        tool_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        proof = _validate(store, config, state, request, agent_type, previous_audit_sha256, frozen_candidate)
        expected_audit = {'schema': VERSION, 'reason': 'review-version-binding' if review else 'obligation-closure-package',
            'previousAuditSha256': previous_audit_sha256,
            'oldSession': deepcopy(config), 'oldState': deepcopy(state),
            'oldEngineSha256': config['engineSha256'], 'newEngineSha256': current_engine,
            'runtimeCompatibility': runtime, 'proof': proof, 'toolSha256': tool_sha}
        if pending and expected_audit != audit:
            raise ValueError('Interrupted upgrade compatibility proof changed')
        audit = expected_audit
        audit_id = c.digest(audit)
        new_config = {**deepcopy(config), 'engineSha256': current_engine, 'runtimeUpgrade': audit_id}
        new_state = {**deepcopy(state), 'sessionSha256': c.digest(new_config),
                     'executionEpoch': state['executionEpoch'] + 1}
        if observed_config not in (config, new_config) or observed_state not in (state, new_state):
            raise ValueError('Unexpected configuration/state during interrupted upgrade recovery')
        if dry_run:
            return {'status': 'compatible', 'auditSha256': audit_id, 'proof': proof}
        committed = 'runtime-upgrades/' + audit_id + '-committed.json'
        if store.path(committed).exists():
            if observed_config != new_config or observed_state != new_state:
                raise ValueError('An upgraded workspace has advanced; it cannot be rolled back by maintenance')
            if store.get(committed) != {'schema': VERSION, 'auditSha256': audit_id,
                                       'sessionSha256': c.digest(new_config), 'stateSha256': c.digest(new_state)}:
                raise ValueError('Committed upgrade audit binding changed')
            return {'status': 'already-upgraded', 'auditSha256': audit_id, 'proof': proof}
        store.put('runtime-upgrades/' + audit_id + '.json', audit)
        store.put(pending_path, {'schema': VERSION, 'auditSha256': audit_id})
        if observed_config != new_config:
            _replace_session(store, new_config)
        if observed_state != new_state:
            store.save_state(new_state)
        store.put(committed, {'schema': VERSION, 'auditSha256': audit_id,
                             'sessionSha256': c.digest(new_config), 'stateSha256': c.digest(new_state)})
        return {'status': 'upgraded', 'auditSha256': audit_id, 'proof': proof}


def main(argv=None):
    parser = argparse.ArgumentParser(description='停止済みDiscovery草稿を明示的な互換検査後に継続可能にする')
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--previous-runtime', type=Path, required=True)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--previous-audit', help='既存の互換移行監査SHAを明示して履歴へ束縛する')
    parser.add_argument('--frozen-candidate', help='検証のみを継続する未採用候補SHAを明示する')
    parser.add_argument('--dry-run', action='store_true', help='互換性だけを検査し、状態を更新しない')
    args = parser.parse_args(argv)
    try:
        from contextbase_discovery import DiscoveryAgent
        from .sources import _json
        result = upgrade(args.work, args.previous_runtime, _json(safe_path(args.request)),
                         DiscoveryAgent, dry_run=args.dry_run, previous_audit_sha256=args.previous_audit,
                         frozen_candidate=args.frozen_candidate)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, RuntimeError) as error:
        print(json.dumps({'status': 'failed', 'error': str(error)}, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
