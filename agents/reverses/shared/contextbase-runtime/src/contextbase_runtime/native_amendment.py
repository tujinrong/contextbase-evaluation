"""Import native joint claims as untrusted data, never as old execution authority.

Only immutable seed/spec artifacts enter fresh work. Archived runtime code,
delivery ledgers, receipts and acceptance state are never loaded as authority.
"""
from copy import deepcopy
from pathlib import Path

from . import candidate_amendment as amendment, contracts as c
from .amendment_seed import _artifact, _artifact_task, _source_refs
from .handoff import followup_question
from .paths import safe_path
from .sources import SourceAccess
from .storage import ArtifactStore

NATIVE_POLICY = 'contextbase-native-tools/1'


def _joint(task):
    c.validate_task_scope(task)
    if task.get('jointPolicy') != c.JOINT_POLICY or task.get('nativeToolsPolicy') != NATIVE_POLICY:
        raise ValueError('Native amendment requires joint native analysis')
    if task['requirements'] != [row['id'] for row in task['goalRequirements']]:
        raise ValueError('Native amendment requires the full original goal')


def _semantic(store, config, source, index=None, *, raw_index_sha256=None):
    from .semantic_support import normalize_options
    options = config.get('semanticOptions')
    if options is None:
        if store.path('semantic-runtime.json').exists():
            raise ValueError('Unexpected semantic runtime without explicit options')
        return None
    if normalize_options(options) != options:
        raise ValueError('Native amendment semantic options must be explicit normalized settings')
    runtime = store.get('semantic-runtime.json')
    if (runtime.get('snapshotId') != source.snapshot_id
            or (index is not None and runtime.get('sourceFactsSha256') != index.sha256)
            or (raw_index_sha256 is not None and runtime.get('sourceFactsSha256') != raw_index_sha256)
            or runtime.get('options') != options):
        raise ValueError('Native amendment semantic runtime source/options changed')
    documents = [store.get(path.relative_to(store.root).as_posix())
                 for path in store.path('semantic-calls').glob('*.json')]
    document = next((row for row in documents if c.digest(row) == runtime['semanticIndexSha256']), None)
    if document is None:
        raise ValueError('Native amendment semantic index artifact is missing')
    binding = document['binding']
    if (binding.get('snapshotId') != source.snapshot_id
            or binding.get('sourceFactsSha256') != runtime['sourceFactsSha256']
            or binding.get('rootProject') != options['project']
            or binding.get('context', {}).get('analysisConfiguration') != options['configuration']):
        raise ValueError('Native amendment semantic index source/options binding changed')
    if index is not None:
        semantic = getattr(index, 'semantic_index', None)
        if semantic is None or semantic.sha256 != runtime['semanticIndexSha256']:
            raise ValueError('Native amendment current semantic binding changed')
        semantic.validate()
    return {'options': deepcopy(options), 'runtimeSha256': c.digest(runtime),
            'semanticIndexSha256': runtime['semanticIndexSha256'],
            'bindingSha256': c.digest(document['binding']), 'policy': runtime['policy']}


def _current_binding(session, index):
    from .controller import engine_fingerprint
    return {'engineSha256': engine_fingerprint(), 'rolesSha256': c.digest(session.config.get('roleSpecs')),
            'semantic': _semantic(session.store, session.config, session.source, index)}


def _task_for_seed(session, seed, index):
    return {**deepcopy(seed['sourceTask']), 'stage': None, 'operation': 'extract',
            'requirements': list(seed['requirements']), 'executionScope': list(seed['requirements']),
            'goalRequirements': deepcopy(session.config['request']['goal']['requirements']),
            'snapshotId': session.source.snapshot_id, 'sourceFactsSha256': index.sha256,
            'requestSha256': c.digest(session.config['request'])}


def _validate_data(session, seed, index):
    task, answer, view = seed['sourceTask'], seed['answer'], seed['view']
    _joint(task)
    if (task.get('amendmentPolicy') or task.get('operation') != 'extract'
            or task['snapshotId'] != session.source.snapshot_id
            or task['sourceFactsSha256'] != index.sha256
            or ('evidenceIndexSha256' in task and task['evidenceIndexSha256'] != index.sha256)
            or task['goalRequirements'] != session.config['request']['goal']['requirements']
            or task['goalSha256'] != c.digest(session.config['request']['goal'])
            or task.get('authorizedSourcePaths') != list(session.source.paths)
            or seed['baseViewSha256'] != c.digest(view)
            or view['acceptedRequirements'] != task['requirements']
            or view['invalidatedRequirements']):
        raise ValueError('Native amendment candidate source, scope or view binding changed')
    c.validate_result(answer, task, session.source, {})
    session.agent.validate_extraction(answer)
    index.validate_usage(answer, index.sha256)
    session.source.verify_evidence_many(list(_source_refs(seed)))
    session._validate_records(view['records'])
    if set(view['records']) != {row['key'] for row in answer['records']}:
        raise ValueError('Native amendment view must contain exactly the full candidate records')
    for key, row in view['records'].items():
        if row['id'] != c.record_id(session.config['request']['projectId'], row['kind'], key):
            raise ValueError('Native amendment stable record identity changed')
        if [dep['key'] for dep in row['dependencies']] != row['dependsOn']:
            raise ValueError('Native amendment dependency declaration changed')
    expected_unknowns = {}
    for item in answer['unknowns']:
        key = task['id'] + ':' + item['id']
        expected_unknowns[key] = {'id': key, 'sha256': c.digest(item), 'content': deepcopy(item),
                                  'owners': list(task['requirements'])}
    for note in seed['followups']:
        question = followup_question(note, task['requirements'])
        expected_unknowns.setdefault(question['id'], question)
    if view['unknowns'] != expected_unknowns:
        raise ValueError('Native amendment unknown/followup content or ownership changed')
    spec = {'schema': amendment.NATIVE_VERSION, 'seedSha256': c.digest(seed),
            'replaceKeys': [row['key'] for row in answer['records']][:1], 'addKinds': []}
    amendment.validate_spec(seed, _task_for_seed(session, seed, index), spec)


def installed(session, task=None):
    """Revalidate installed data and current bindings, without reopening origin work."""
    names = ('amendment-seed.json', 'amendment-spec.json')
    present = [session.store.path(name).exists() for name in names]
    if not any(present):
        if task and task.get('amendmentPolicy') == amendment.NATIVE_VERSION:
            raise ValueError('Native amendment task lost its installed seed/spec')
        return None
    if not all(present):
        raise ValueError('Native amendment installation is incomplete')
    seed, spec = (session.store.get(name) for name in names)
    if seed.get('schema') != amendment.NATIVE_SEED_VERSION:
        raise ValueError('Native amendment requires version 2 seed data')
    current_semantic = seed['currentBinding']['semantic']
    if session.config.get('semanticOptions') != (current_semantic['options'] if current_semantic else None):
        raise ValueError('Installed native amendment current semantic options changed')
    session.source.verify()
    index = session.fact_index()
    index.validate()
    if (session.config.get('nativeToolsPolicy') != NATIVE_POLICY
            or session.config.get('jointPolicy') != c.JOINT_POLICY
            or seed['snapshotId'] != session.source.snapshot_id or seed['indexSha256'] != index.sha256
            or seed['requestSha256'] != c.digest(session.config['request'])
            or seed['currentBinding'] != _current_binding(session, index)):
        raise ValueError('Installed native amendment current source/index/request/runtime binding changed')
    _validate_data(session, seed, index)
    amendment.validate_spec(seed, _task_for_seed(session, seed, index), spec)
    if task is not None:
        from .amendment_runtime import operation_id
        _joint(task)
        if (task.get('amendmentPolicy') != amendment.NATIVE_VERSION
                or task.get('amendmentSeedSha256') != c.digest(seed)
                or task.get('amendmentSpecSha256') != c.digest(spec)
                or task.get('amendmentOperationId') != operation_id(seed, spec)
                or task.get('requestSha256') != seed['requestSha256']):
            raise ValueError('Native amendment task seed/spec binding changed')
        if task['operation'] == 'extract':
            amendment.validate_spec(seed, task, spec)
    session.source.verify()
    return seed, spec


def install(agent, from_work, candidate_id, verification_id, finding_ids=None, *, replace_keys):
    """Seal only checked untrusted claims in fresh native joint work."""
    session = agent.session
    work, origin = safe_path(agent.work), safe_path(Path(from_work))
    if work == origin or work in origin.parents or origin in work.parents:
        raise ValueError('Native amendment origin and new workspace must be disjoint')
    state = session._state()
    if (agent.stage is not None or session.config.get('nativeToolsPolicy') != NATIVE_POLICY
            or session.config.get('jointPolicy') != c.JOINT_POLICY
            or state['version'] != 0 or state['revision'] is not None or state['tasks']
            or state['candidates'] or state['verifications'] or state['acceptedRequirements']
            or state.get('attempts') or state.get('status') != 'active'
            or any(session.store.path(name).exists() for name in ('incoming.json', 'repair-seed.json'))):
        raise ValueError('Native amendment installation requires fresh joint native work')
    store = ArtifactStore(origin)
    config, prior = store.get('session.json'), store.get('state.json')
    original = SourceAccess.open(store.path('snapshot'))
    original.verify(); session.source.verify()
    index = session.fact_index(); index.validate()
    if (config.get('nativeToolsPolicy') != NATIVE_POLICY or config.get('jointPolicy') != c.JOINT_POLICY
            or config['request'] != session.config['request'] or config['snapshotId'] != original.snapshot_id
            or original.snapshot_id != session.source.snapshot_id
            or prior['sessionSha256'] != c.digest(config) or prior['acceptedRequirements']
            or prior['revision'] is not None or prior['version'] != 0):
        raise ValueError('Native amendment requires an unadopted original source/request match')
    documents = [store.get(path.relative_to(store.root).as_posix())
                 for path in store.path('source-facts').glob('*.json')]
    if index.document not in documents:
        raise ValueError('Native amendment original raw index differs from the current index')
    candidate = _artifact(store, 'candidates', candidate_id)
    verification = _artifact(store, 'verifications', verification_id)
    task = store.get('tasks/' + candidate['taskId'] + '/request.json')
    review_task = store.get('tasks/' + verification['taskId'] + '/request.json')
    _joint(task); _joint(review_task)
    _artifact_task(candidate, task); _artifact_task(verification, review_task)
    if (candidate_id not in prior['candidates'] or verification_id not in prior['verifications']
            or task['sessionId'] != config['id'] or review_task['sessionId'] != config['id']
            or prior['tasks'].get(task['id']) != 'finished' or prior['tasks'].get(review_task['id']) != 'finished'
            or candidate['operation'] != 'extract' or verification['operation'] != 'verify'
            or verification['candidate'] != candidate_id or review_task['candidate'] != candidate_id
            or verification['viewSha256'] != candidate['viewSha256']
            or candidate['viewSha256'] != c.digest(candidate['view'])
            or review_task['requirements'] != task['requirements']
            or candidate['baseVersion'] != 0 or candidate['baseRevision'] is not None):
        raise ValueError('Native amendment candidate/review/task binding changed')
    for artifact, artifact_task in ((candidate, task), (verification, review_task)):
        if (artifact_task.get('origin') != 'host-executed'
                or artifact['provenance'].get('kind') != 'host-executed'
                or artifact['provenance'].get('answerSha256') != c.digest(artifact['answer'])):
            raise ValueError('Native amendment requires original native artifact provenance')
    if ({row['id']: row['sha256'] for row in review_task['unknownBindings']}
            != {key: row['sha256'] for key, row in candidate['view']['unknowns'].items()}):
        raise ValueError('Native amendment review unknown bindings disagree with candidate view')
    for current_task in (task, review_task):
        if (current_task['snapshotId'] != original.snapshot_id
                or current_task['sourceFactsSha256'] != index.sha256
                or ('evidenceIndexSha256' in current_task and current_task['evidenceIndexSha256'] != index.sha256)
                or current_task['goalRequirements'] != config['request']['goal']['requirements']
                or current_task['goalRequirementIds'] != [row['id'] for row in config['request']['goal']['requirements']]
                or current_task['goalSha256'] != c.digest(config['request']['goal'])
                or current_task.get('authorizedSourcePaths') != list(original.paths)):
            raise ValueError('Native amendment original task source/index/request changed')
    c.validate_result(verification['answer'], review_task, session.source, candidate['view']['records'])
    prior_semantic = _semantic(store, config, original, raw_index_sha256=index.sha256)
    for current_task in (task, review_task):
        if ((prior_semantic is None and ('semanticPolicy' in current_task or 'semanticIndexSha256' in current_task))
                or (prior_semantic is not None and (current_task.get('semanticPolicy') != prior_semantic['policy']
                    or current_task.get('semanticIndexSha256') != prior_semantic['semanticIndexSha256']))):
            raise ValueError('Native amendment original task semantic binding changed')
    findings = {row['id']: row for row in verification['answer']['findings']}
    chosen = list(findings) if finding_ids is None else list(finding_ids)
    if not chosen or len(chosen) != len(set(chosen)) or not set(chosen).issubset(findings):
        raise ValueError('Select exact unique existing native review finding identities')
    issues = []
    for key in chosen:
        issue = {'id': verification_id + ':' + key, 'sourceCandidateSha256': candidate_id,
                 'sourceVerificationSha256': verification_id, 'finding': deepcopy(findings[key])}
        issue['sha256'] = c.digest(issue)
        issues.append(issue)
    followups = {}
    for identifier in prior['candidates'][:prior['candidates'].index(candidate_id) + 1]:
        historical = _artifact(store, 'candidates', identifier)
        for note in historical['answer']['followups']:
            followups.setdefault(c.digest(note), deepcopy(note))
    seed = {'schema': amendment.NATIVE_SEED_VERSION, 'jointPolicy': c.JOINT_POLICY,
            'nativeToolsPolicy': NATIVE_POLICY, 'requestSha256': c.digest(config['request']),
            'snapshotId': original.snapshot_id, 'indexSha256': index.sha256, 'stage': None,
            'requirements': list(task['requirements']), 'baseCandidateSha256': candidate_id,
            'baseViewSha256': candidate['viewSha256'], 'answer': deepcopy(candidate['answer']),
            'view': deepcopy(candidate['view']), 'sourceTask': deepcopy(task),
            'followups': list(followups.values()), 'issues': issues,
            'priorFindings': deepcopy(verification['answer']['findings']),
            'custody': {'trust': 'untrusted-source-validated-data', 'originWork': str(origin),
                        'engineSha256': config['engineSha256'], 'rolesSha256': c.digest(config.get('roleSpecs')),
                        'semantic': prior_semantic, 'sourceVerificationSha256': verification_id,
                        'sessionSha256': c.digest(config), 'stateSha256': c.digest(prior),
                        'authorTaskSha256': c.digest(task), 'reviewTaskSha256': c.digest(review_task)},
            'currentBinding': _current_binding(session, index)}
    _validate_data(session, seed, index)
    spec = {'schema': amendment.NATIVE_VERSION, 'seedSha256': c.digest(seed),
            'replaceKeys': list(replace_keys), 'addKinds': []}
    amendment.validate_spec(seed, _task_for_seed(session, seed, index), spec)
    original.verify(); session.source.verify()
    with session.store.transaction() as current:
        if current != state:
            raise ValueError('Workspace changed during native amendment import')
        for name, payload in (('amendment-seed.json', seed), ('amendment-spec.json', spec)):
            if session.store.path(name).exists() and session.store.get(name) != payload:
                raise ValueError('Installed native amendment artifacts cannot be replaced')
        session.store.put('amendment-seed.json', seed)
        session.store.put('amendment-spec.json', spec)
    return seed, spec
