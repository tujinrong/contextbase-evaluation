"""Versioned contracts for three extraction stages and independent verification.

Author responses name dependency keys; the host freezes those references to
record versions before creating the verification view.
"""
from __future__ import annotations

import hashlib
import json

from jsonschema import Draft202012Validator

VERSION = 'contextbase-analysis/2'
STAGES = ('discovery', 'relationship', 'behavior')
ROLES = STAGES
OPERATIONS = ('extract', 'verify')


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()


def obj(properties, required=None):
    return {'type': 'object', 'properties': properties,
            'required': list(properties) if required is None else required,
            'additionalProperties': False}


def arr(item, minimum=0):
    return {'type': 'array', 'items': item, 'minItems': minimum}


TEXT = {'type': 'string', 'minLength': 1}
STRINGS = {'type': 'array', 'items': TEXT, 'uniqueItems': True}
SHA256 = {'type': 'string', 'pattern': '^[0-9a-f]{64}$'}
EVIDENCE = obj({'path': TEXT, 'startLine': {'type': 'integer', 'minimum': 1},
                'endLine': {'type': 'integer', 'minimum': 1}, 'sha256': SHA256})
RECORD = obj({'key': TEXT, 'ownerRequirement': TEXT,
              'kind': {'enum': ['system', 'function', 'entry', 'data', 'common', 'relation', 'fact']},
              'name': TEXT, 'statement': TEXT, 'basis': {'enum': ['observed-source', 'inferred']},
              'evidence': arr(EVIDENCE, 1), 'dependsOn': STRINGS})
COVERAGE = obj({'requirement': TEXT, 'status': {'enum': ['supported', 'unresolved', 'not-applicable']},
                'recordKeys': STRINGS, 'evidence': arr(EVIDENCE)})
UNKNOWN = obj({'id': TEXT, 'question': TEXT, 'relatedRequirements': STRINGS,
               'blocksRequirements': STRINGS, 'scopeReason': TEXT})
FOLLOWUP = obj({'stage': {'enum': list(STAGES)}, 'question': TEXT, 'paths': STRINGS,
                'requirement': {'type': ['string', 'null']}})
REQUIREMENT = obj({'id': TEXT, 'question': TEXT, 'stage': {'enum': list(STAGES)},
                   'scope': TEXT, 'requires': STRINGS})
GOAL = obj({'id': TEXT, 'question': TEXT, 'requirements': arr(REQUIREMENT, 1)})
REQUEST = obj({'schema': {'type': 'string', 'const': VERSION}, 'projectId': TEXT,
               'goal': GOAL, 'allowedPaths': arr(TEXT, 1), 'excludedPaths': STRINGS})


def validate(value, schema) -> None:
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda e: str(list(e.path)))
    if errors:
        error = errors[0]
        raise ValueError('Invalid analysis contract at ' + '.'.join(map(str, error.path)) + ': ' + error.message)


def validate_request(value) -> None:
    if not isinstance(value, dict) or value.get('schema') != VERSION:
        raise ValueError('A contextbase-analysis/2 request with explicit stage and scope is required; '
                         'v1/investigation is not automatically migrated. Create an explicit v2 request.')
    validate(value, REQUEST)
    obligations = value['goal']['requirements']
    by_id = {item['id']: item for item in obligations}
    if len(by_id) != len(obligations):
        raise ValueError('Goal requirement IDs must be unique')
    if not any(item['stage'] == 'discovery' for item in obligations):
        raise ValueError('A goal requires an explicit discovery obligation')
    previous = {'relationship': 'discovery', 'behavior': 'relationship'}
    for item in obligations:
        if item['stage'] == 'discovery':
            if item['requires']:
                raise ValueError('Discovery obligations do not have prerequisite obligations')
            continue
        if not item['requires']:
            raise ValueError(item['stage'] + ' must name its required ' + previous[item['stage']] + ' obligations')
        for identifier in item['requires']:
            required = by_id.get(identifier)
            if required is None or required['stage'] != previous[item['stage']]:
                raise ValueError(item['stage'] + ' requires existing ' + previous[item['stage']] + ' obligations')
            if required['scope'] != item['scope']:
                raise ValueError('Prerequisites must belong to the same scope as the dependent obligation')


def _enum(values):
    values = list(values)
    return {'type': 'string', 'enum': values} if values else dict(TEXT)


def _exact_array(item, count):
    return {'type': 'array', 'items': item, 'minItems': count, 'maxItems': count}


def result_schema(task: dict) -> dict:
    if task['operation'] not in OPERATIONS:
        raise ValueError('Unknown analysis operation')
    if task['stage'] not in STAGES:
        raise ValueError('Unknown extraction stage')
    binding = {'taskId': {'type': 'string', 'const': task['id']}}
    requirement = _enum(task['requirements'])
    if task['operation'] == 'verify':
        bindings = task['unknownBindings']
        unknown_check = obj({
            'unknownId': _enum(item['id'] for item in bindings), 'unknownSha256': SHA256,
            'status': {'enum': ['non-blocking', 'blocking', 'unresolved', 'resolved']},
            'blocksRequirements': STRINGS, 'reason': TEXT, 'evidence': arr(EVIDENCE)})
        return obj({**binding,
                    'candidateSha256': {'type': 'string', 'const': task['candidate']},
                    'viewSha256': {'type': 'string', 'const': task['viewSha256']},
                    'checks': _exact_array(obj({'requirement': requirement,
                        'status': {'enum': ['pass', 'fail', 'unknown']}, 'reason': TEXT,
                        'evidence': arr(EVIDENCE)}), len(task['requirements'])),
                    'unknownChecks': _exact_array(unknown_check, len(bindings)),
                    'findings': arr(obj({'id': TEXT, 'severity': {'enum': ['blocking', 'minor']},
                        'requirement': requirement, 'detail': TEXT, 'evidence': arr(EVIDENCE)})),
                    'unknowns': arr(UNKNOWN)})
    coverage = obj({**COVERAGE['properties'], 'requirement': requirement})
    record = obj({**RECORD['properties'], 'ownerRequirement': requirement})
    return obj({**binding, 'records': arr(record),
                'coverage': _exact_array(coverage, len(task['requirements'])),
                'unknowns': arr(UNKNOWN), 'followups': arr(FOLLOWUP)})


def transport_schema(task: dict) -> dict:
    """Strict transport uses its supported subset; the host validates all rules."""
    def compatible(value):
        if isinstance(value, list):
            return [compatible(item) for item in value]
        if not isinstance(value, dict):
            return value
        result = {key: compatible(item) for key, item in value.items() if key != 'uniqueItems'}
        if 'enum' in result and 'type' not in result:
            result['type'] = 'string'
        return result
    return compatible(result_schema(task))


def _unique_ids(items, field, description):
    ids = [item[field] for item in items]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate ' + description)
    return ids


def _validate_unknowns(items: list[dict], goal_ids: set[str]) -> None:
    _unique_ids(items, 'id', 'unknown identity')
    for item in items:
        if not set(item['relatedRequirements']).issubset(goal_ids):
            raise ValueError('Unknown must refer to original goal obligations')
        if not set(item['blocksRequirements']).issubset(item['relatedRequirements']):
            raise ValueError('Unknown blocking obligations must be among its related obligations')


def validate_result(answer: dict, task: dict, source, existing_keys=()) -> None:
    validate(answer, result_schema(task))
    verification = task['operation'] == 'verify'
    checks = answer['checks'] if verification else answer['coverage']
    ids = _unique_ids(checks, 'requirement', 'coverage/check identity')
    if set(ids) != set(task['requirements']):
        raise ValueError('Result must account for every assigned requirement exactly once')
    goal_ids = set(task['goalRequirementIds'])
    obligations = {item['id']: item for item in task['goalRequirements']}
    scopes = {obligations[identifier]['scope'] for identifier in task['requirements']}
    records = answer.get('records', [])
    keys = _unique_ids(records, 'key', 'record identity key')
    known = set(keys) | set(existing_keys)
    coverage = {item['requirement']: item for item in checks}
    for record in records:
        owner = record['ownerRequirement']
        if owner not in task['requirements']:
            raise ValueError('Record owner must be an assigned obligation')
        if record['key'] not in coverage[owner]['recordKeys']:
            raise ValueError('Record must be included in its owner coverage')
        if not set(record['dependsOn']).issubset(known):
            raise ValueError('Unknown record dependency')
    for item in checks:
        if item['status'] in {'supported', 'not-applicable', 'pass'} and not item['evidence']:
            raise ValueError('A positive conclusion requires source evidence')
        if not set(item.get('recordKeys', [])).issubset(known):
            raise ValueError('Coverage refers to an unknown record')
    _unique_ids(answer.get('findings', []), 'id', 'finding identity')
    for finding in answer.get('findings', []):
        if finding['requirement'] not in task['requirements']:
            raise ValueError('Finding refers to an unassigned requirement')
    for followup in answer.get('followups', []):
        for path in followup['paths']:
            if path not in source.paths:
                raise ValueError('Follow-up path outside the sealed scope')
        identifier = followup['requirement']
        if identifier is not None:
            required = obligations.get(identifier)
            if required is None:
                raise ValueError('Follow-up must refer to an original goal obligation')
            if required['stage'] != followup['stage']:
                raise ValueError('Follow-up stage must match the referenced obligation')
            if required['scope'] not in scopes:
                raise ValueError('Follow-up must remain in the assigned scope')
    _validate_unknowns(answer['unknowns'], goal_ids)
    if verification:
        bindings = {item['id']: item['sha256'] for item in task['unknownBindings']}
        unknown_ids = _unique_ids(answer['unknownChecks'], 'unknownId', 'unknown verification')
        if set(unknown_ids) != set(bindings):
            raise ValueError('Verification must account for every bound unknown exactly once')
        for check in answer['unknownChecks']:
            if check['unknownSha256'] != bindings[check['unknownId']]:
                raise ValueError('Unknown verification content binding changed')
            blocked = set(check['blocksRequirements'])
            if not blocked.issubset(goal_ids):
                raise ValueError('Unknown verification refers to an unknown goal obligation')
            if check['status'] in {'non-blocking', 'resolved'}:
                if blocked:
                    raise ValueError('A non-blocking/resolved unknown cannot block obligations')
                if not check['evidence']:
                    raise ValueError('A non-blocking/resolved unknown requires source evidence')
            elif not blocked:
                raise ValueError('A blocking/unresolved unknown must identify impacted obligations')
    groups = [records, checks, answer.get('findings', []), answer.get('unknownChecks', [])]
    for group in groups:
        for item in group:
            for evidence in item.get('evidence', []):
                source.verify_evidence(evidence)


def record_id(project_id: str, kind: str, key: str) -> str:
    """The identity key persists across revisions; ordering never renumbers IDs."""
    return kind.upper() + '-' + digest([project_id, kind, key])[:16]
