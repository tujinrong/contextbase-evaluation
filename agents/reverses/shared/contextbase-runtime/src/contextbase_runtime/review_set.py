"""Versioned review assignments and conservative, deterministic aggregation.

This module assigns and combines judgments; it does not execute a reviewer or
certify independent provenance. The host must preserve and replay each assigned
task's original response and source deliveries before accepting the aggregate.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import json

from . import catalog, contracts as c


VERSION = 'contextbase-review-set/1'
_STATUS = {'enum': ['pass', 'fail', 'unknown']}
_UNIT = c.obj({'id': {'type': 'string', 'pattern': '^[A-Za-z0-9_-]{1,64}$'},
               'kind': {'enum': ['records', 'global']}, 'recordKeys': c.STRINGS,
               'unknownIds': c.STRINGS, 'requirements': c.STRINGS, 'scopes': c.STRINGS})


def _exact(items, field, expected, description):
    actual = [item[field] for item in items]
    if len(actual) != len(set(actual)) or set(actual) != set(expected):
        raise ValueError('Review set must cover exact ' + description)


def _root(task, view):
    if task.get('operation') != 'verify' or task.get('viewSha256') != c.digest(view):
        raise ValueError('Review set requires the exact frozen verification view')
    if (len(task['requirements']) != len(set(task['requirements']))
            or set(task['requirements']) != set(view['acceptedRequirements'])):
        raise ValueError('Review set obligations disagree with the complete view')
    for key, record in view['records'].items():
        if record['key'] != key or record['ownerRequirement'] not in task['requirements']:
            raise ValueError('Review record is outside its original owner obligation')
        body = {field: value for field, value in record.items() if field not in {'id', 'version'}}
        if record['version'] != c.digest(body):
            raise ValueError('Review record content and version disagree')
    bindings = task['unknownBindings']
    _exact(bindings, 'id', view['unknowns'], 'unknown bindings')
    if any(item['sha256'] != view['unknowns'][item['id']]['sha256'] for item in bindings):
        raise ValueError('Review unknown content binding changed')
    if task.get('catalogPolicy') == catalog.VERSION:
        expected = {item['key']: item['sha256'] for item in catalog.bindings(view['records'])}
        actual = task.get('classificationBindings', [])
        _exact(actual, 'key', expected, 'classification bindings')
        if any(item['sha256'] != expected[item['key']] for item in actual):
            raise ValueError('Review classification content binding changed')


def _scopes(task):
    return catalog.scopes(task) if task.get('catalogPolicy') == catalog.VERSION else []


def _unit(task, view, unit):
    c.validate(unit, _UNIT)
    if (not set(unit['recordKeys']).issubset(view['records'])
            or not set(unit['unknownIds']).issubset(view['unknowns'])
            or not set(unit['requirements']).issubset(task['requirements'])
            or not set(unit['scopes']).issubset(_scopes(task))):
        raise ValueError('Review unit expands the host-assigned complete view')
    if unit['kind'] == 'records':
        if unit['requirements'] or unit['scopes'] or not (unit['recordKeys'] or unit['unknownIds']):
            raise ValueError('Record review must have targets and cannot replace a global review')
    elif unit['recordKeys'] or unit['unknownIds'] or not unit['requirements']:
        raise ValueError('Global review must explicitly check original obligations')
    if unit['scopes']:
        obligations = {item['id']: item for item in task['goalRequirements']}
        eligible = {obligations[key]['scope'] for key in unit['requirements']
                    if obligations[key]['stage'] == 'discovery'}
        if not set(unit['scopes']).issubset(eligible):
            raise ValueError('Global scope review is assigned to an unrelated obligation')


def make_units(task, view, *, max_records=6, max_chars=16_000):
    """Assign every record/question and an independent global coverage review.

    max_chars guides grouping only. An oversized single record remains assigned;
    its host transport must provide a reference and paginated access, not drop it.
    """
    _root(task, view)
    if any(type(value) is not int or value <= 0 for value in (max_records, max_chars)):
        raise ValueError('Review grouping requires positive integer limits')
    units, group, size = [], [], 0

    def append(kind, *, keys=(), unknowns=(), requirements=(), scopes=()):
        units.append({'id': kind + '-' + str(len(units)).zfill(4), 'kind': kind,
                      'recordKeys': list(keys), 'unknownIds': list(unknowns),
                      'requirements': list(requirements), 'scopes': list(scopes)})

    for key in sorted(view['records']):
        row_size = len(json.dumps(view['records'][key], ensure_ascii=False, separators=(',', ':')))
        if group and (len(group) >= max_records or size + row_size > max_chars):
            append('records', keys=group)
            group, size = [], 0
        group.append(key)
        size += row_size
    if group:
        append('records', keys=group)
    questions = sorted(view['unknowns'])
    for offset in range(0, len(questions), max_records):
        append('records', unknowns=questions[offset:offset + max_records])
    obligations = {item['id']: item for item in task['goalRequirements']}
    remaining_scopes = set(_scopes(task))
    for key in task['requirements']:
        owner = obligations[key]
        scopes = ([owner['scope']] if owner['stage'] == 'discovery'
                  and owner['scope'] in remaining_scopes else [])
        remaining_scopes.difference_update(scopes)
        append('global', requirements=[key], scopes=scopes)
    return units


def _array(schema, count):
    return {'type': 'array', 'items': deepcopy(schema), 'minItems': count, 'maxItems': count}


def _paired(schema, identity_field, version_field, bindings):
    """Expose exact identity/version pairs without cross-product hash choices."""
    if not bindings:
        # An empty target array still needs a legal item schema for strict
        # providers. Its array min/maxItems=0 excludes every actual element.
        return deepcopy(schema)
    variants = []
    for identity, version in bindings:
        item = deepcopy(schema)
        item['properties'][identity_field] = {'type': 'string', 'const': identity}
        item['properties'][version_field] = {'type': 'string', 'const': version}
        variants.append(item)
    return {'anyOf': variants}


def unit_schema(task, view, unit):
    """A slice contract leaves no implicit pass for unassigned checks."""
    _root(task, view)
    _unit(task, view, unit)
    canonical = c.result_schema(task)['properties']
    result = {'status': deepcopy(_STATUS), 'reason': deepcopy(c.TEXT), 'evidence': c.arr(c.EVIDENCE)}
    record_check = _paired(c.obj({'key': c._enum(unit['recordKeys']), 'recordSha256': c.SHA256, **result}),
                           'key', 'recordSha256',
                           [(key, view['records'][key]['version']) for key in unit['recordKeys']])
    classified = [item for item in task.get('classificationBindings', [])
                  if task.get('catalogPolicy') == catalog.VERSION and item['key'] in unit['recordKeys']]
    classification_check = _paired(c.obj({'key': c._enum(item['key'] for item in classified),
                                          'recordSha256': c.SHA256, **result}),
                                   'key', 'recordSha256', [(item['key'], item['sha256']) for item in classified])
    unknown_check = deepcopy(canonical['unknownChecks']['items'])
    unknown_check['properties']['unknownId'] = c._enum(unit['unknownIds'])
    unknown_check = _paired(unknown_check, 'unknownId', 'unknownSha256',
                            [(key, view['unknowns'][key]['sha256']) for key in unit['unknownIds']])
    requirement_check = deepcopy(canonical['checks']['items'])
    requirement_check['properties']['requirement'] = c._enum(unit['requirements'])
    scope_check = c.obj({'scope': c._enum(unit['scopes']), **result})
    return c.obj({
        'unitId': {'type': 'string', 'const': unit['id']},
        'candidateSha256': {'type': 'string', 'const': task['candidate']},
        'viewSha256': {'type': 'string', 'const': task['viewSha256']},
        'recordChecks': _array(record_check, len(unit['recordKeys'])),
        'classificationChecks': _array(classification_check, len(classified)),
        'unknownChecks': _array(unknown_check, len(unit['unknownIds'])),
        'checks': _array(requirement_check, len(unit['requirements'])),
        'scopeChecks': _array(scope_check, len(unit['scopes'])),
        'findings': deepcopy(canonical['findings']), 'unknowns': deepcopy(canonical['unknowns']),
        'factUsageCheck': deepcopy(canonical['factUsageCheck'])
            if task.get('sourceFactsSha256') else {'type': 'null'},
    })


def validate_unit(task, view, unit, answer):
    """Validate identities and judgments; source delivery is checked by the host."""
    c.validate(answer, unit_schema(task, view, unit))
    _exact(answer['recordChecks'], 'key', unit['recordKeys'], 'record checks')
    for row in answer['recordChecks']:
        if row['recordSha256'] != view['records'][row['key']]['version']:
            raise ValueError('Review record fingerprint changed')
    classified = {item['key']: item['sha256'] for item in task.get('classificationBindings', [])
                  if task.get('catalogPolicy') == catalog.VERSION and item['key'] in unit['recordKeys']}
    _exact(answer['classificationChecks'], 'key', classified, 'classification checks')
    for row in answer['classificationChecks']:
        if row['recordSha256'] != classified[row['key']]:
            raise ValueError('Classification review fingerprint changed')
    _exact(answer['checks'], 'requirement', unit['requirements'], 'global obligation checks')
    _exact(answer['scopeChecks'], 'scope', unit['scopes'], 'scope checks')
    _exact(answer['unknownChecks'], 'unknownId', unit['unknownIds'], 'unknown decisions')
    for row in answer['unknownChecks']:
        if row['unknownSha256'] != view['unknowns'][row['unknownId']]['sha256']:
            raise ValueError('Unknown review fingerprint changed')
        blocked = set(row['blocksRequirements'])
        if row['status'] in {'non-blocking', 'resolved'}:
            if blocked or not row['evidence']:
                raise ValueError('Resolved/non-blocking questions require evidence and no blockers')
        elif not blocked:
            raise ValueError('Unresolved questions require explicit blocking obligations')
    for rows in (answer['recordChecks'], answer['classificationChecks'], answer['checks'], answer['scopeChecks']):
        if any(row['status'] == 'pass' and not row['evidence'] for row in rows):
            raise ValueError('Positive review judgments require original source evidence')
    fact_check = answer['factUsageCheck']
    if fact_check is not None and fact_check['status'] == 'pass' and not fact_check['evidence']:
        raise ValueError('Positive fact-usage review requires source evidence')
    for field in ('findings', 'unknowns'):
        ids = [row['id'] for row in answer[field]]
        if len(ids) != len(set(ids)):
            raise ValueError('Duplicate review ' + field + ' identity')
    c._validate_unknowns(answer['unknowns'], set(task['goalRequirementIds']))


def _partition(task, view, units):
    ids = [unit['id'] for unit in units]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate review unit identity')
    for unit in units:
        _unit(task, view, unit)
    for field, expected in (('recordKeys', view['records']), ('unknownIds', view['unknowns']),
                            ('requirements', task['requirements']), ('scopes', _scopes(task))):
        counts = Counter(key for unit in units for key in unit[field])
        if set(counts) != set(expected) or any(count != 1 for count in counts.values()):
            raise ValueError('Incomplete or overlapping review partition: ' + field)


def _combine(rows):
    """Select only submitted judgments; a local failure cannot become a pass."""
    if not rows:
        raise ValueError('No review judgment to aggregate')
    severity = {'pass': 0, 'unknown': 1, 'fail': 2}
    evidence, seen = [], set()
    for row in rows:
        for ref in row['evidence']:
            fingerprint = c.digest(ref)
            if fingerprint not in seen:
                evidence.append(deepcopy(ref))
                seen.add(fingerprint)
    return {'status': max((row['status'] for row in rows), key=severity.__getitem__),
            'reason': '\n'.join(row['reason'] for row in rows), 'evidence': evidence}


def aggregate(task, view, units, answers):
    """Materialize a canonical inspection input, never execution provenance.

    The host must also replay the versioned composite review receipt. Passing
    this JSON through old semantic gates alone cannot prove independent review.
    """
    _root(task, view)
    _partition(task, view, units)
    if len(answers) != len(units):
        raise ValueError('Each assigned review unit requires one exact response')
    by_id = {row['unitId']: row for row in answers}
    if len(by_id) != len(answers) or set(by_id) != {unit['id'] for unit in units}:
        raise ValueError('Review responses do not match the assigned unit set')
    for unit in units:
        validate_unit(task, view, unit, by_id[unit['id']])
    ordered = [by_id[unit['id']] for unit in units]
    global_checks = {row['requirement']: row for result in ordered for row in result['checks']}
    record_checks = {row['key']: row for result in ordered for row in result['recordChecks']}
    checks = []
    for key in task['requirements']:
        rows = [global_checks[key], *[record_checks[record_key]
                for record_key, record in view['records'].items() if record['ownerRequirement'] == key]]
        checks.append({'requirement': key, **_combine(rows)})
    findings, unknowns = [], []
    for unit in units:
        result = by_id[unit['id']]
        findings.extend({**deepcopy(row), 'id': unit['id'] + ':' + row['id']} for row in result['findings'])
        unknowns.extend({**deepcopy(row), 'id': unit['id'] + ':' + row['id']} for row in result['unknowns'])
    result = {'taskId': task['id'], 'candidateSha256': task['candidate'],
              'viewSha256': task['viewSha256'], 'checks': checks,
              'unknownChecks': [deepcopy(row) for item in ordered for row in item['unknownChecks']],
              'findings': findings, 'unknowns': unknowns}
    if task.get('catalogPolicy') == catalog.VERSION:
        result.update(classificationChecks=[deepcopy(row) for item in ordered for row in item['classificationChecks']],
                      scopeChecks=[deepcopy(row) for item in ordered for row in item['scopeChecks']])
    if task.get('sourceFactsSha256'):
        result.update(sourceFactsSha256=task['sourceFactsSha256'],
                      factUsageCheck=_combine([row['factUsageCheck'] for row in ordered]))
    c.validate(result, c.result_schema(task))
    return result
