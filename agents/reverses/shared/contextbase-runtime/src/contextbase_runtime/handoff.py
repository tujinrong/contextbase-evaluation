"""Portable claims, revalidated locally before activation as external premises.

Hashes detect damage, not producer identity. Historical receipts never confer
acceptance authority. Activation requires a new host-owned verification call.
"""
from __future__ import annotations

from copy import deepcopy
import uuid

from . import contracts, catalog
from .controller import AcceptanceError, Session

VERSION = 'contextbase-handoff/2'
FIELDS = {'schema', 'producer', 'request', 'source', 'acceptedRequirements', 'records',
          'identities', 'coverage', 'unknowns', 'followups', 'audit', 'premises'}
IDENTITY = contracts.obj({'id': contracts.TEXT, 'kind': contracts.RECORD['properties']['kind'],
                          'ownerRequirement': contracts.TEXT})
MATERIAL_RECORD = contracts.obj({**contracts.RECORD['properties'], 'id': contracts.TEXT,
    'version': contracts.SHA256, 'dependencies': contracts.arr(contracts.obj({
        'key': contracts.TEXT, 'version': contracts.SHA256}))},
    required=[*contracts.RECORD['required'], 'id', 'version', 'dependencies'])
BOUND_UNKNOWN = contracts.obj({'id': contracts.TEXT, 'sha256': contracts.SHA256,
    'content': contracts.UNKNOWN, 'owners': contracts.STRINGS})
SUMMARY = contracts.obj({'sha256': contracts.SHA256, 'origin': contracts.TEXT,
    'checks': contracts.arr(contracts.obj({'requirement': contracts.TEXT,
                                         'status': {'enum': ['pass', 'fail', 'unknown']}}))})
AUDIT = contracts.obj({'candidateSha256': contracts.SHA256,
    'stage': {'enum': list(contracts.STAGES)}, 'requirements': contracts.STRINGS,
    'origin': contracts.TEXT, 'followups': contracts.arr(contracts.FOLLOWUP),
    'verificationSummaries': contracts.arr(SUMMARY)})


def mapping(item):
    return {'type': 'object', 'additionalProperties': item}


PAYLOAD = contracts.obj({'schema': {'const': VERSION}, 'producer': {'enum': list(contracts.STAGES)},
    'request': contracts.REQUEST, 'source': {'type': 'object'},
    'acceptedRequirements': contracts.STRINGS, 'records': mapping(MATERIAL_RECORD),
    'identities': mapping(IDENTITY), 'coverage': contracts.arr(contracts.COVERAGE, 1),
    'unknowns': mapping(BOUND_UNKNOWN), 'followups': contracts.arr(contracts.FOLLOWUP),
    'audit': contracts.arr(AUDIT), 'premises': mapping(contracts.SHA256),
    'catalogPolicy': {'type': 'string', 'const': catalog.VERSION}}, required=sorted(FIELDS))


def source_binding(source):
    return {key: value for key, value in source.manifest.items() if key != 'sourceRoot'}


def followup_question(note, owners):
    identifier = 'followup:' + contracts.digest(note)
    related = [note['requirement']] if note['requirement'] is not None else []
    content = {'id': identifier, 'question': note['question'], 'relatedRequirements': related,
               'blocksRequirements': related,
               'scopeReason': 'An explicit ' + note['stage'] + ' investigation request remains open '
                              'until a local independent reviewer resolves it from original source.'}
    return {'id': identifier, 'sha256': contracts.digest(content), 'content': content,
            'owners': list(owners)}


def validate_lineage(payload):
    expected = set(contracts.STAGES[:contracts.STAGES.index(payload['producer'])])
    if set(payload['premises']) != expected:
        raise ValueError('Handoff must bind every preceding layer by its exact envelope fingerprint')


def validate_catalog_policy(payload):
    policy = payload.get('catalogPolicy')
    if policy is not None and policy != catalog.VERSION:
        raise ValueError('Unsupported catalog policy')
    classified = any('classification' in record for record in payload['records'].values())
    if classified and policy != catalog.VERSION:
        raise ValueError('Classified handoff requires an explicit catalog policy')
    if policy == catalog.VERSION:
        obligations = {item['id']: item for item in payload['request']['goal']['requirements']}
        catalog.validate_records(payload['records'], obligations, strict=True,
                                 unknown_ids=set(payload['unknowns']))


def export(agent):
    session = agent.session
    session.source.verify()
    state = session._state()
    current = session._current(state)
    accepted = state['acceptedRequirements']
    if not any(session.obligations[key]['stage'] == agent.stage for key in accepted):
        raise ValueError('Export requires an independently accepted result from this agent')
    coverage = []
    for key in accepted:
        candidate = session.store.get('candidates/' + current['receipts'][key]['candidate'] + '.json')
        coverage.append(deepcopy(next(item for item in candidate['answer']['coverage']
                                      if item['requirement'] == key)))
    questions = deepcopy(current['unknowns'])
    for item in questions.values():
        item.pop('decision', None)
    followups = {}
    audit = deepcopy(session.store.get('incoming.json')['payload']['audit']) \
        if session.store.path('incoming.json').exists() else []
    for identifier in state['candidates']:
        candidate = session.store.get('candidates/' + identifier + '.json')
        for note in candidate['answer']['followups']:
            question = followup_question(note, candidate['requirements'])
            key = question['id']
            if key not in questions or candidate['baseVersion'] >= state['version']:
                questions[key] = question
            # Only an explicit, source-backed independent resolution closes a
            # question. Neither target acceptance nor non-blocking does so.
            decision = current['unknowns'].get(key, {}).get('decision')
            if (candidate['baseVersion'] >= state['version'] or not decision
                    or decision['status'] != 'resolved'):
                followups[key] = deepcopy(note)
        # Even an unadopted candidate's unknown is not silently dropped at export.
        for item in candidate['answer']['unknowns']:
            key = candidate['taskId'] + ':' + item['id']
            if candidate['provenance']['kind'] != 'external-handoff':
                questions.setdefault(key, {'id': key, 'sha256': contracts.digest(item),
                    'content': deepcopy(item), 'owners': candidate['requirements']})
        audit.append({'candidateSha256': identifier, 'stage': candidate['stage'],
                      'requirements': candidate['requirements'],
                      'origin': candidate['provenance']['kind'],
                      'followups': deepcopy(candidate['answer']['followups']), 'verificationSummaries': [
                          {'sha256': key, 'origin': verification['provenance']['kind'],
                           'checks': [{'requirement': item['requirement'], 'status': item['status']}
                                      for item in verification['answer']['checks']]}
                          for key in state['verifications']
                          for verification in [session.store.get('verifications/' + key + '.json')]
                          if verification['candidate'] == identifier]})
    for identifier in state['verifications']:
        verification = session.store.get('verifications/' + identifier + '.json')
        for item in verification['answer']['unknowns']:
            key = verification['taskId'] + ':' + item['id']
            questions.setdefault(key, {'id': key, 'sha256': contracts.digest(item),
                'content': deepcopy(item), 'owners': verification['requirements']})
    premises = {}
    if session.store.path('incoming.json').exists():
        incoming = session.store.get('incoming.json')
        premises.update(incoming['payload']['premises'])
        premises[incoming['payload']['producer']] = incoming['sha256']
    payload = {'schema': VERSION, 'producer': agent.stage, 'premises': premises,
               'request': deepcopy(session.config['request']), 'source': source_binding(session.source),
               'acceptedRequirements': list(accepted), 'records': deepcopy(current['records']),
               'identities': deepcopy(current['identities']), 'coverage': coverage,
               'unknowns': questions, 'followups': list(followups.values()), 'audit': audit}
    policy = getattr(agent, 'catalog_policy', None)
    if session.store.path('incoming.json').exists():
        policy = policy or session.store.get('incoming.json')['payload'].get('catalogPolicy')
    if policy is not None:
        payload['catalogPolicy'] = policy
    validate_catalog_policy(payload)
    return {'sha256': contracts.digest(payload), 'payload': payload}


def _validate(agent, envelope):
    session = agent.session
    if (not isinstance(envelope, dict) or set(envelope) != {'sha256', 'payload'}
            or contracts.digest(envelope['payload']) != envelope['sha256']):
        raise ValueError('Handoff content fingerprint mismatch')
    payload = envelope['payload']
    if (not isinstance(payload, dict) or not FIELDS.issubset(payload)
            or set(payload) - FIELDS - {'catalogPolicy'} or payload['schema'] != VERSION):
        raise ValueError('Unsupported handoff contract')
    contracts.validate(payload, PAYLOAD)
    validate_lineage(payload)
    validate_catalog_policy(payload)
    if payload.get('catalogPolicy') != catalog.VERSION:
        raise ValueError('Legacy catalog has no classification policy; re-extract discovery '
                         'before importing into an independent agent')
    expected = {'relationship': 'discovery', 'behavior': 'relationship'}.get(agent.stage)
    if payload['producer'] != expected:
        raise ValueError('Expected an upstream ' + str(expected) + ' handoff')
    if payload['request'] != session.config['request']:
        raise ValueError('Handoff must preserve the original goal, project and authorized scope')
    if payload['source'] != source_binding(session.source):
        raise ValueError('Handoff source content or scope does not match this independent snapshot')
    ids = payload['acceptedRequirements']
    if (not isinstance(ids, list) or not ids or len(ids) != len(set(ids))
            or not set(ids).issubset(session.obligations)):
        raise ValueError('Handoff requires unique original prerequisite obligations')
    if (not any(session.obligations[key]['stage'] == expected for key in ids)
            or any(contracts.STAGES.index(session.obligations[key]['stage']) >=
                   contracts.STAGES.index(agent.stage) for key in ids)):
        raise ValueError('Handoff may contain only accepted upstream obligations')
    if any(not set(session.obligations[key]['requires']).issubset(ids) for key in ids):
        raise ValueError('Handoff prerequisite closure is incomplete')
    contracts.validate(payload['coverage'], contracts.arr(contracts.COVERAGE, 1))
    if (len(payload['coverage']) != len(ids)
            or {item['requirement'] for item in payload['coverage']} != set(ids)
            or any(item['status'] == 'unresolved' for item in payload['coverage'])):
        raise ValueError('Handoff coverage must account for every claimed prerequisite')
    if not isinstance(payload['records'], dict) or not isinstance(payload['identities'], dict):
        raise ValueError('Handoff records and stable identities must be maps')
    session._validate_records(payload['records'])
    for key, record in payload['records'].items():
        if record['ownerRequirement'] not in ids:
            raise ValueError('Handoff record has no accepted owner')
        identity = {field: record[field] for field in ('id', 'kind', 'ownerRequirement')}
        if payload['identities'].get(key) != identity:
            raise ValueError('Handoff record identity or owner changed')
    for key, identity in payload['identities'].items():
        if (set(identity) != {'id', 'kind', 'ownerRequirement'}
                or identity['ownerRequirement'] not in session.obligations
                or identity['id'] != contracts.record_id(session.config['request']['projectId'], identity['kind'], key)):
            raise ValueError('Handoff stable identity is invalid')
    if not isinstance(payload['unknowns'], dict):
        raise ValueError('Handoff unknowns must be a complete identity map')
    for key, item in payload['unknowns'].items():
        if (set(item) != {'id', 'sha256', 'content', 'owners'} or item['id'] != key
                or item['sha256'] != contracts.digest(item['content'])
                or not isinstance(item['owners'], list)
                or not set(item['owners']).issubset(session.obligations)):
            raise ValueError('Handoff unknown binding changed')
        contracts.validate(item['content'], contracts.UNKNOWN)
        contracts._validate_unknowns([item['content']], set(session.obligations))
    contracts.validate(payload['followups'], contracts.arr(contracts.FOLLOWUP))
    for note in payload['followups']:
        expected_question = followup_question(note, [])
        actual = payload['unknowns'].get(expected_question['id'])
        if (not actual or actual['sha256'] != expected_question['sha256']
                or actual['content'] != expected_question['content']):
            raise ValueError('Every active followup must retain its bound question')
    return payload


def receive(agent, envelope):
    session = agent.session
    payload = _validate(agent, envelope)
    state = session._state()
    if state['revision'] or state['candidates'] or state['tasks']:
        raise ValueError('Receive a handoff only into a fresh independent workspace')
    # Reconstruct a normal proposal view, without promoting producer receipts.
    task = {'schema': contracts.VERSION, 'id': uuid.uuid4().hex, 'contextId': uuid.uuid4().hex,
            'sessionId': session.config['id'], 'stage': payload['producer'], 'operation': 'extract',
            'origin': 'external-handoff', 'executionEpoch': state['executionEpoch'],
            'snapshotId': session.source.snapshot_id, 'baseVersion': state['version'],
            'baseRevision': state['revision'], 'goalSha256': contracts.digest(session.config['request']['goal']),
            'goalRequirementIds': list(session.obligations),
            'goalRequirements': list(session.obligations.values()),
            'requirements': session._ordered(payload['acceptedRequirements']),
            'candidate': None, 'feedback': None, 'prerequisites': {},
            'viewSha256': None, 'invalidatedRequirements': [], 'unknownBindings': []}
    if payload.get('catalogPolicy') == catalog.VERSION:
        task.update(catalogPolicy=catalog.VERSION, classificationBindings=[])
    records = [{field: deepcopy(record[field]) for field in contracts.RECORD['properties'] if field in record}
               for record in payload['records'].values()]
    answer = {'taskId': task['id'], 'records': records, 'coverage': deepcopy(payload['coverage']),
              'unknowns': [{**deepcopy(item['content']), 'id': key} for key, item in payload['unknowns'].items()],
              'followups': deepcopy(payload['followups'])}
    contracts.validate_result(answer, task, session.source)
    # Check dependency versions and IDs against deterministic local materialization.
    view = Session._proposal_view(session, state, task, answer)
    if view['records'] != payload['records']:
        raise ValueError('Handoff record ownership, evidence or dependency versions are inconsistent')
    session.store.put('incoming.json', deepcopy(envelope))
    view = session._proposal_view(state, task, answer)
    candidate = {key: deepcopy(task[key]) for key in
                 ('schema', 'sessionId', 'stage', 'operation', 'baseVersion', 'baseRevision',
                  'snapshotId', 'goalSha256', 'requirements', 'candidate', 'feedback')}
    candidate.update(taskId=task['id'], contextId=task['contextId'], answer=answer,
                     provenance={'kind': 'external-handoff', 'independenceVerified': False,
                                 'handoffSha256': envelope['sha256']},
                     view=view, viewSha256=contracts.digest(view))
    identifier = contracts.digest(candidate)
    with session.store.transaction() as latest:
        if latest != state:
            raise ValueError('Workspace changed during handoff import')
        session.store.put('tasks/' + task['id'] + '/request.json', task)
        session.store.put('candidates/' + identifier + '.json', candidate)
        session.store.put('incoming-candidate.json', {'candidate': identifier})
        latest['tasks'][task['id']] = 'finished'
        latest['candidates'].append(identifier)
        session.store.save_state(latest)
    return identifier


def revalidate(agent, *, timeout, inline_sources, runner):
    session = agent.session
    identifier = session.store.get('incoming-candidate.json')['candidate']
    attempt_key = 'handoff:' + identifier
    state = session._state()
    if attempt_key in state['attempts']:
        return {'status': 'needs-prerequisites', 'pending': state['attempts'][attempt_key],
                'actions': [], 'session': agent.status()}
    verification = session.verify(identifier, timeout=timeout, inline_sources=inline_sources, runner=runner)
    try:
        _activate(agent, identifier, verification['id'])
    except AcceptanceError as exc:
        pending = {'handoff': identifier, 'verification': verification['id'], 'reason': str(exc),
                   'findings': verification['result']['findings']}
        with session.store.transaction() as latest:
            latest['attempts'][attempt_key] = pending
            latest['stopReason'] = str(exc)
            session.store.save_state(latest)
        return {'status': 'needs-prerequisites', 'pending': pending,
                'actions': [], 'session': agent.status()}
    return None


def _activate(agent, candidate_id, verification_id):
    session = agent.session
    session.source.verify()
    session._state()
    with session.store.transaction() as state:
        incoming = session.store.get('incoming.json')
        payload = _validate(agent, incoming)
        candidate = session.store.get('candidates/' + candidate_id + '.json')
        verification = session.store.get('verifications/' + verification_id + '.json')
        task = session.store.get('tasks/' + verification['taskId'] + '/request.json')
        author = session.store.get('tasks/' + candidate['taskId'] + '/request.json')
        provenance = verification['provenance']
        if (state['revision'] or state['status'] != 'active'
                or verification_id not in state['verifications']
                or candidate_id not in state['candidates']
                or verification['candidate'] != candidate_id
                or candidate['provenance']['kind'] != 'external-handoff'
                or candidate['provenance']['handoffSha256'] != incoming['sha256']
                or task['origin'] != 'host-executed' or task['operation'] != 'verify'
                or provenance.get('kind') != 'host-executed'
                or provenance.get('transport') != 'codex-ephemeral'
                or not provenance.get('independenceVerified')
                or task['sessionId'] != session.config['id']
                or verification['sessionId'] != session.config['id']
                or verification['snapshotId'] != session.source.snapshot_id
                or verification['goalSha256'] != contracts.digest(session.config['request']['goal'])
                or verification['baseVersion'] != state['version']
                or task['executionEpoch'] != state['executionEpoch']
                or state['tasks'].get(task['id']) != 'finished'
                or verification['contextId'] != task['contextId']
                or provenance['contextId'] != task['contextId']
                or provenance['invocationId'] != task['id']
                or provenance['answerSha256'] != contracts.digest(verification['answer'])
                or verification['contextId'] == candidate['contextId']):
            raise AcceptanceError('Local independent host-owned verification required for external premises')
        view = session._proposal_view(state, author, candidate['answer'])
        if (contracts.digest(view) != candidate['viewSha256']
                or verification['viewSha256'] != candidate['viewSha256']
                or task['viewSha256'] != candidate['viewSha256']
                or set(task['requirements']) != set(payload['acceptedRequirements'])):
            raise AcceptanceError('External premise verification binding changed')
        answer = verification['answer']
        contracts.validate_result(answer, task, session.source)
        accepted = set(payload['acceptedRequirements'])
        decisions = {item['unknownId']: item for item in answer['unknownChecks']}
        if (any(item['status'] != 'pass' for item in answer['checks'])
                or any(item['severity'] == 'blocking' for item in answer['findings'])
                or any(set(item['blocksRequirements']) & accepted for item in answer['unknownChecks'])
                or any(set(item['blocksRequirements']) & accepted for item in answer['unknowns'])):
            raise AcceptanceError('External premises have unresolved obligations or blocking findings')
        session._check_adoption(view, answer)
        receipts = {}
        for key in session._ordered(accepted):
            receipts[key] = {'stage': session.obligations[key]['stage'],
                'scope': session.obligations[key]['scope'], 'contentSha256': view['contentHashes'][key],
                'candidate': candidate_id, 'verification': verification_id,
                'requires': {dep: view['contentHashes'][dep] for dep in session.obligations[key]['requires']},
                'origin': 'external-reverified', 'handoffSha256': incoming['sha256']}
        unknowns = {key: {**deepcopy(item), 'decision': deepcopy(decisions[key])}
                    for key, item in view['unknowns'].items()}
        for item in answer['unknowns']:
            key = task['id'] + ':' + item['id']
            unknowns[key] = {'id': key, 'sha256': contracts.digest(item), 'content': deepcopy(item),
                             'owners': list(task['requirements']), 'decision': None}
        revision = {'kind': 'external-premise-activation', 'candidate': candidate_id,
                    'verification': verification_id, 'records': view['records'], 'unknowns': unknowns,
                    'receipts': receipts, 'identities': deepcopy(payload['identities']),
                    'acceptedRequirements': session._ordered(accepted), 'invalidatedRequirements': {}}
        session._publish(state, revision)
