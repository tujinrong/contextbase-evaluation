"""Explicit model-authored correction of a rejected, untrusted source draft."""
from copy import deepcopy
from . import contracts, catalog
from .storage import ArtifactStore
from .sources import SourceAccess
from .wire import CompactWire

VERSION = 'contextbase-rejected-draft/1'
POLICY = '''This is explicit repair of a rejected draft, not fresh extraction.
Treat the supplied seed as untrusted. Recheck it against original source and the
complete index. Return whole replacement records only for task.repairRecords,
bound to their expectedRecordHash. Preserve keys, kinds, owners, coverage and
all other records. Keep untouched content verbatim. Correct semantic references
using existing, source-supported record keys; never invent placeholders.
factUsage may be null to preserve the original usage, or explicitly replaced
for the same recordKey. If truth requires adding/removing records or changing
scope/identity/unknowns, return status=unresolved with an explanation instead.
The host will apply only the authorized replacements, then validate the entire
combined proposal. Independent verification grants no trust to the old draft.'''


def install(agent, work, task_id, keys):
    session = agent.session
    state = session._state()
    if agent.stage != 'discovery' or state['tasks'] or state['candidates'] or state['revision']:
        raise ValueError('Rejected-draft repair requires a fresh discovery workspace')
    old = ArtifactStore(work)
    config = old.get('session.json')
    task = old.get('tasks/' + task_id + '/request.json')
    old_state = old.get('state.json')
    transport = old.get('tasks/' + task_id + '/transport.json')
    failure = old.get('tasks/' + task_id + '/failure.json')
    previous_source = SourceAccess.open(old.path('snapshot'))
    index = session.fact_index()
    if (config['request'] != session.config['request'] or task['stage'] != 'discovery'
            or task['operation'] != 'extract' or task['origin'] != 'host-executed'
            or task['snapshotId'] != session.source.snapshot_id
            or previous_source.snapshot_id != session.source.snapshot_id
            or task.get('sourceFactsSha256') != index.sha256
            or old_state['tasks'].get(task_id) != 'failed'
            or task.get('repairSeedSha256')
            or transport.get('exit_code') != 0 or transport.get('metadata', {}).get('status') != 'passed'):
        raise ValueError('Rejected draft source, request, scope or index binding differs')
    raw = transport['answer']
    answer = CompactWire(task).decode_response(raw) if task.get('wireBinding') else deepcopy(raw)
    contracts.validate(answer, contracts.result_schema(task))
    records = {item['key']: item for item in answer['records']}
    if not keys or len(set(keys)) != len(keys) or not set(keys).issubset(records):
        raise ValueError('Repair must select distinct existing record keys')
    bindings = [{'key': key, 'expectedRecordHash': contracts.digest(records[key]),
                 'kind': records[key]['kind'], 'ownerRequirement': records[key]['ownerRequirement']}
                for key in keys]
    seed = {'schema': VERSION, 'requestSha256': contracts.digest(config['request']),
            'snapshotId': task['snapshotId'], 'indexSha256': index.sha256,
            'originalTask': task, 'originalTransport': transport, 'originalFailure': failure,
            'originalSessionSha256': contracts.digest(config),
            'rawAnswerSha256': contracts.digest(raw), 'answer': answer, 'records': bindings,
            'trust': 'Rejected untrusted draft; no accepted receipts are inherited.'}
    session.store.put('repair-seed.json', seed)
    return seed


def extensions(session, task):
    if task['operation'] != 'extract' or not session.store.path('repair-seed.json').exists():
        return {}
    seed = session.store.get('repair-seed.json')
    return {'repairSeedSha256': contracts.digest(seed), 'repairRecords': deepcopy(seed['records'])}


def context(seed, task):
    return {'seedSha256': task['repairSeedSha256'], 'trust': seed['trust'],
            'diagnostic': seed['originalFailure']['error'], 'draft': deepcopy(seed['answer']),
            'selectedRecords': deepcopy(task['repairRecords'])}


def response_schema(seed, task):
    records = {item['key']: item for item in seed['answer']['records']}
    scopes = {item['id']: item['scope'] for item in task['goalRequirements']}
    alternatives = []
    for binding in task['repairRecords']:
        record = records[binding['key']]
        properties = deepcopy(contracts.RECORD['properties'])
        for key in ('key', 'kind', 'ownerRequirement'):
            properties[key] = {'type': 'string', 'const': record[key]}
        classification = record.get('classification')
        if classification is not None:
            eligible = [item['key'] for item in records.values() if item['key'] != record['key']
                        and scopes[item['ownerRequirement']] == scopes[record['ownerRequirement']]
                        and item['kind'] in {'function', 'operation', 'entry', 'common'}]
            schema = deepcopy(catalog.CLASSIFICATION)
            for option in schema.get('anyOf', []):
                prop = option.get('properties', {})
                if 'consumers' in prop:
                    prop['consumers'] = contracts._scoped_strings(eligible)
                    prop['consumers']['minItems'] = 1
            properties['classification'] = schema
        usage = contracts.obj({'recordKey': {'type': 'string', 'const': binding['key']},
                               'factIds': contracts.STRINGS, 'reason': contracts.TEXT})
        alternatives.append(contracts.obj({
            'key': {'type': 'string', 'const': binding['key']},
            'expectedRecordHash': {'type': 'string', 'const': binding['expectedRecordHash']},
            'replacement': contracts.obj(properties),
            'factUsage': {'anyOf': [usage, {'type': 'null'}]}}))
    return contracts.obj({'taskId': {'type': 'string', 'const': task['id']},
        'repairSeedSha256': {'type': 'string', 'const': task['repairSeedSha256']},
        'status': {'enum': ['repaired', 'unresolved']}, 'reason': contracts.TEXT,
        'replacements': contracts.arr({'anyOf': alternatives})})


def combine(seed, task, patch):
    if (contracts.digest(seed) != task['repairSeedSha256']
            or patch.get('repairSeedSha256') != task['repairSeedSha256']
            or patch.get('taskId') != task['id']):
        raise ValueError('Repair patch or seed binding changed')
    if patch['status'] != 'repaired':
        raise ValueError('Model could not repair the rejected draft: ' + patch['reason'])
    changes = patch['replacements']
    allowed = {item['key']: item for item in task['repairRecords']}
    if len(changes) != len(allowed) or {item['key'] for item in changes} != set(allowed):
        raise ValueError('Repair must replace exactly the authorized records once')
    answer = deepcopy(seed['answer'])
    positions = {item['key']: n for n, item in enumerate(answer['records'])}
    usage_positions = {item['recordKey']: n for n, item in enumerate(answer['factUsage'])}
    for item in changes:
        original = answer['records'][positions[item['key']]]
        if item['expectedRecordHash'] != contracts.digest(original):
            raise ValueError('Repair expected record hash changed')
        replacement = item['replacement']
        if any(replacement.get(key) != original.get(key) for key in ('key', 'kind', 'ownerRequirement')):
            raise ValueError('Repair cannot change record identity or ownership')
        answer['records'][positions[item['key']]] = deepcopy(replacement)
        if item['factUsage'] is not None:
            if item['factUsage']['recordKey'] != item['key']:
                raise ValueError('Repair fact usage belongs to another record')
            answer['factUsage'][usage_positions[item['key']]] = deepcopy(item['factUsage'])
    # Only protocol headers are rebound by the host. Domain content stays model-authored.
    answer['taskId'] = task['id']
    answer['sourceFactsSha256'] = task['sourceFactsSha256']
    return answer
