"""Pure contracts and deterministic reduction of unadopted investigation drafts.

The caller owns persistence, execution provenance and source/fact validation.
These functions never infer coverage, resolve semantic identities or adopt data.
"""
from __future__ import annotations

from copy import deepcopy

from . import contracts


VERSION = 'contextbase-drafts/1'
_UNIT_ID = {'type': 'string', 'pattern': '^[A-Za-z0-9_-]{1,64}$'}
_VERSION_REF = contracts.obj({'key': contracts.TEXT, 'sha256': contracts.SHA256})


def _assigned(task):
    if task.get('operation') != 'extract' or not task.get('requirements'):
        raise ValueError('Drafts require an extraction task with original obligations')
    obligations = {item['id']: item for item in task['goalRequirements']}
    if (len(task['requirements']) != len(set(task['requirements']))
            or not set(task['requirements']).issubset(obligations)):
        raise ValueError('Draft obligations must be unique original requirements')
    if any(obligations[key]['stage'] != task['stage'] for key in task['requirements']):
        raise ValueError('Draft obligations must belong to the original extraction stage')
    return obligations


def _unit_schema(task):
    _assigned(task)
    paths = list(task['authorizedSourcePaths'])
    return contracts.obj({
        'id': deepcopy(_UNIT_ID),
        'requirement': {'type': 'string', 'enum': list(task['requirements'])},
        'question': deepcopy(contracts.TEXT),
        'paths': {'type': 'array', 'items': {'type': 'string', 'enum': paths},
                  'uniqueItems': True} if paths else {
                      'type': 'array', 'items': deepcopy(contracts.TEXT), 'maxItems': 0},
    })


def plan_schema(task):
    return contracts.obj({'units': contracts.arr(_unit_schema(task), 1)})


def validate_plan(task, plan):
    contracts.validate(plan, plan_schema(task))
    units = plan['units']
    _unique(units, 'id', 'plan unit')
    if {item['requirement'] for item in units} != set(task['requirements']):
        raise ValueError('Every original assigned obligation requires a planned unit')


def draft_schema(task, unit):
    contracts.validate(unit, _unit_schema(task))
    properties = contracts.result_schema(task)['properties']
    records = deepcopy(properties['records'])
    records['items']['properties']['ownerRequirement'] = {
        'type': 'string', 'const': unit['requirement']}
    return contracts.obj({
        'unitId': {'type': 'string', 'const': unit['id']},
        'records': records,
        'expectedVersions': contracts.arr(deepcopy(_VERSION_REF)),
        'removals': contracts.arr(contracts.obj({
            **deepcopy(_VERSION_REF['properties']), 'reason': deepcopy(contracts.TEXT)})),
        'unknowns': deepcopy(properties['unknowns']),
        'followups': deepcopy(properties['followups']),
        'factUsage': deepcopy(properties.get('factUsage', {
            'type': 'array', 'items': deepcopy(contracts.TEXT), 'maxItems': 0})),
        'remainingQuestions': deepcopy(contracts.STRINGS),
        'complete': {'type': 'boolean'},
        'addUnits': contracts.arr(_unit_schema(task)),
    })


def closure_schema(task, requirement):
    _assigned(task)
    if requirement not in task['requirements']:
        raise ValueError('Closure must name an original assigned obligation')
    return contracts.obj({
        'requirement': {'type': 'string', 'const': requirement},
        'status': {'type': 'string', 'enum': ['supported', 'unresolved', 'not-applicable']},
        'reason': deepcopy(contracts.TEXT),
        'evidence': contracts.arr(deepcopy(contracts.EVIDENCE)),
    })


def _unique(rows, field, label):
    values = [item[field] for item in rows]
    if len(values) != len(set(values)):
        raise ValueError('Duplicate ' + label)
    return {item[field]: item for item in rows}


def _register(units, unit):
    previous = units.get(unit['id'])
    if previous is not None and previous != unit:
        raise ValueError('An existing unit definition cannot silently change')
    units[unit['id']] = deepcopy(unit)


def _normalized_record(record, unit_id, unknowns, local_unknown_ids):
    record = deepcopy(record)
    classification = record.get('classification')
    if classification and classification['category'] == 'pending':
        normalized = []
        for key in classification['unknownIds']:
            if key in local_unknown_ids:
                identifier = unit_id + ':' + key
            elif key in unknowns:
                identifier = key
            elif unit_id + ':' + key in unknowns:
                identifier = unit_id + ':' + key
            else:
                raise ValueError('Pending classification refers to an unknown question identity')
            normalized.append(identifier)
        classification['unknownIds'] = normalized
    return record


def _reduce(task, events):
    obligations = _assigned(task)
    records, identities, unknowns, followups, usages = {}, {}, {}, {}, {}
    units, latest = {}, {}
    for event in events:
        if not isinstance(event, dict) or set(event) != {'unit', 'answer'}:
            raise ValueError('Draft event must contain exactly its unit and model answer')
        unit, answer = event['unit'], event['answer']
        contracts.validate(answer, draft_schema(task, unit))
        _register(units, unit)
        for added in answer['addUnits']:
            _register(units, added)
        _unique(answer['addUnits'], 'id', 'added unit')
        latest[unit['id']] = answer
        incoming = _unique(answer['records'], 'key', 'draft record')
        expected = _unique(answer['expectedVersions'], 'key', 'expected record version')
        removals = _unique(answer['removals'], 'key', 'record removal')
        usage = _unique(answer['factUsage'], 'recordKey', 'fact usage')
        if set(incoming) & set(removals):
            raise ValueError('A draft cannot replace and remove the same record')
        if set(expected) - set(incoming):
            raise ValueError('Expected versions must correspond to submitted records')
        if task.get('sourceFactsSha256') and set(usage) != set(incoming):
            raise ValueError('Every submitted record requires exactly one fact-usage declaration')
        for item in answer['unknowns']:
            identifier = unit['id'] + ':' + item['id']
            normalized = {**deepcopy(item), 'id': identifier}
            if not set(item['blocksRequirements']).issubset(item['relatedRequirements']):
                raise ValueError('Unknown blocking requirements must be related requirements')
            if identifier in unknowns and unknowns[identifier] != normalized:
                raise ValueError('An existing unknown identity cannot be overwritten')
            unknowns[identifier] = normalized
        _unique(answer['unknowns'], 'id', 'unknown identity')
        for followup in answer['followups']:
            followups.setdefault(contracts.digest(followup), deepcopy(followup))
        for key, declaration in incoming.items():
            normalized = _normalized_record(declaration, unit['id'], unknowns,
                                            {item['id'] for item in answer['unknowns']})
            if normalized['ownerRequirement'] != unit['requirement']:
                raise ValueError('Draft record owner must remain its original unit obligation')
            classification = normalized.get('classification')
            if classification and classification['scope'] != obligations[unit['requirement']]['scope']:
                raise ValueError('Draft classification scope must match its original owner')
            if classification and classification['category'] == 'pending':
                for identifier in classification['unknownIds']:
                    question = unknowns.get(identifier)
                    if question is None or unit['requirement'] not in question['relatedRequirements']:
                        raise ValueError('Pending classification must retain a related unknown')
                    if (classification['impact'] == 'count-or-coverage'
                            and unit['requirement'] not in question['blocksRequirements']):
                        raise ValueError('Pending count or coverage must block its owner')
            identity = (normalized['kind'], normalized['ownerRequirement'])
            if key in identities and identities[key] != identity:
                raise ValueError('A stable draft key cannot change kind or owner')
            previous = records.get(key)
            if key in expected and (previous is None or contracts.digest(previous) != expected[key]['sha256']):
                raise ValueError('Draft expected record version is stale or absent: ' + key)
            if previous is not None and previous != normalized and key not in expected:
                raise ValueError('Conflicting draft record requires an exact expected version: ' + key)
            identities.setdefault(key, identity)
            records[key] = normalized
            if key in usage:
                usages[key] = deepcopy(usage[key])
        for key, removal in removals.items():
            previous = records.get(key)
            if previous is None or contracts.digest(previous) != removal['sha256']:
                raise ValueError('Record removal must name the current exact draft version: ' + key)
            if previous['ownerRequirement'] != unit['requirement']:
                raise ValueError('A unit cannot remove another obligation\'s record')
            del records[key]
            usages.pop(key, None)
    return {'records': list(records.values()), 'unknowns': list(unknowns.values()),
            'followups': list(followups.values()), 'factUsage': list(usages.values())}, units, latest


def reduce_drafts(task, events):
    """Replay explicit proposals, preserving questions and rejecting last-wins merges."""
    return _reduce(task, events)[0]


def canonical_answer(task, events, closures):
    """Assemble model-authored content; coverage membership is mechanical, status is not."""
    result, units, latest = _reduce(task, events)
    validate_plan(task, {'units': list(units.values())})
    for identifier in units:
        final = latest.get(identifier)
        if final is None or not final['complete'] or final['remainingQuestions']:
            raise ValueError('Every declared unit must finish with no remaining questions')
    # complete ends authorized investigation, not uncertainty. The reducer
    # deliberately retains questions even for ended units; model closures and
    # independent review still decide whether the original goal is fulfilled.
    by_requirement = _unique(closures, 'requirement', 'obligation closure')
    if set(by_requirement) != set(task['requirements']):
        raise ValueError('Every original assigned obligation requires an explicit closure')
    coverage = []
    for requirement in task['requirements']:
        submitted = by_requirement[requirement]
        contracts.validate(submitted, closure_schema(task, requirement))
        if submitted['status'] in {'supported', 'not-applicable'} and not submitted['evidence']:
            raise ValueError('A positive closure requires original-source evidence')
        coverage.append({'requirement': requirement, 'status': submitted['status'],
                         'recordKeys': [item['key'] for item in result['records']
                                        if item['ownerRequirement'] == requirement],
                         'evidence': deepcopy(submitted['evidence'])})
    answer = {'taskId': task['id'], 'records': result['records'], 'coverage': coverage,
              'unknowns': result['unknowns'], 'followups': result['followups']}
    if task.get('sourceFactsSha256'):
        answer.update(sourceFactsSha256=task['sourceFactsSha256'], factUsage=result['factUsage'])
    contracts.validate(answer, contracts.result_schema(task))
    return answer


def _structural(value):
    if isinstance(value, dict):
        return {key: _structural(child) for key, child in value.items()
                if key not in {'name', 'statement', 'rationale', 'alternative', 'reason',
                               'question', 'scopeReason', 'sha256', 'version', 'complete'}}
    if isinstance(value, list):
        return [_structural(child) for child in value]
    return value


def structural_progress(before, after):
    """Observe structural change, without claiming that it proves semantic improvement."""
    return _structural(before) != _structural(after)
