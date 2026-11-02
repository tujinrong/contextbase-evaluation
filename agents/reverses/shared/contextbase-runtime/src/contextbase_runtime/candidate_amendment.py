"""Pure, deterministic composition of an unadopted base plus explicit delta.

The caller validates custody, deliveries, source facts and full-view semantics.
Nothing in this module starts a model, persists a candidate or adopts a claim.
"""
from __future__ import annotations

from copy import deepcopy

from . import contracts, investigation

VERSION = 'contextbase-candidate-amendment/1'
NATIVE_VERSION = 'contextbase-candidate-amendment/2'
NATIVE_SEED_VERSION = 'contextbase-candidate-amendment-seed/2'
POLICY = '''
Submit explicit permitted changes under task.amendmentPolicy. Native version 2
replaces selected existing keys only; the supplied spec defines allowed changes.
Bind operationId to the supplied stable amendment operation identity. The outer
provider envelope and assembled canonical answer retain their actual task IDs.
Omission never deletes records, unknowns, followups or fact usage. Existing keys
require their exact frozen view version; new keys require expectedVersion=null.
Do not change key, kind or owner. Address each selected issue exactly once using
its supplied issueSha256. A changed disposition names actual delta keys and
original-source evidence. Already-addressed/source-refuted declarations cite
current keys and exact frozen versions in currentRecordRefs plus original-source
evidence; they do not require a fictitious change. currentRecordRefs is always
present; use [] when no current record is referenced. Unresolved dispositions
state the remaining question and only current related blocking obligations;
future-stage questions do not automatically block the current stage. Every
original requirement needs a fresh explicit closure; old coverage is not proof.
All declarations remain subject to fresh independent review of the full view.
'''.strip()


def _unique(rows, field, label):
    result = {row[field]: row for row in rows}
    if len(result) != len(rows):
        raise ValueError('Duplicate ' + label)
    return result


def validate_spec(seed, task, spec):
    """Validate pure content/scope bindings; custody is the caller's boundary."""
    native = spec.get('schema') == NATIVE_VERSION
    if seed.get('schema') != (NATIVE_SEED_VERSION if native else 'contextbase-candidate-amendment-seed/1'):
        raise ValueError('An explicit amendment seed is required')
    contracts.validate(spec, contracts.obj({
        'schema': {'type': 'string', 'const': NATIVE_VERSION if native else VERSION}, 'seedSha256': contracts.SHA256,
        'replaceKeys': contracts.STRINGS, 'addKinds': contracts.STRINGS}))
    if native:
        contracts.validate_task_scope(task)
        if (task.get('stage') is not None or task.get('jointPolicy') != contracts.JOINT_POLICY
                or seed.get('jointPolicy') != contracts.JOINT_POLICY
                or seed.get('nativeToolsPolicy') != 'contextbase-native-tools/1'
                or task['requirements'] != [row['id'] for row in task['goalRequirements']]
                or not spec['replaceKeys'] or spec['addKinds']):
            raise ValueError('Native amendments require joint replacement-only scope')
    elif task.get('jointPolicy') is not None or task.get('stage') is None:
        raise ValueError('Legacy amendments retain their original single stage')
    if spec['seedSha256'] != contracts.digest(seed):
        raise ValueError('Amendment seed content binding changed')
    if task.get('operation') != 'extract' or not task.get('requirements'):
        raise ValueError('Amendment requires original extraction obligations')
    obligations = _unique(task['goalRequirements'], 'id', 'goal obligation')
    assigned = task['requirements']
    if (len(set(assigned)) != len(assigned)
            or set(assigned) != set(seed['requirements'])
            or len(set(seed['requirements'])) != len(seed['requirements'])
            or not set(assigned).issubset(obligations)
            or seed['stage'] != task['stage']
            or (not native and any(obligations[key]['stage'] != task['stage'] for key in assigned))):
        raise ValueError('Amendment must retain its original stage and assigned obligations')
    for task_key, seed_key in [('snapshotId', 'snapshotId'),
                               ('sourceFactsSha256', 'indexSha256'),
                               ('requestSha256', 'requestSha256')]:
        if task_key in task and task[task_key] != seed[seed_key]:
            raise ValueError('Amendment input binding changed: ' + task_key)
    if seed['baseViewSha256'] != contracts.digest(seed['view']):
        raise ValueError('Amendment base view binding changed')
    records = _unique(seed['answer']['records'], 'key', 'base record')
    if not set(spec['replaceKeys']).issubset(records):
        raise ValueError('Replacement scope must name existing base keys')
    for key, row in records.items():
        if row['ownerRequirement'] not in assigned:
            raise ValueError('Base answer contains a foreign owner')
        frozen = seed['view']['records'].get(key)
        comparable = deepcopy(row)
        classification = comparable.get('classification') or {}
        if (classification.get('category') == 'pending' and frozen is not None
                and classification != frozen.get('classification')):
            # Ordinary host extraction freezes author-local unknown IDs. Check
            # that exact known transformation, without rewriting the raw seed.
            classification['unknownIds'] = [seed['answer']['taskId'] + ':' + identifier
                                             for identifier in classification['unknownIds']]
        if frozen is None or any(frozen.get(field) != value for field, value in comparable.items()):
            raise ValueError('Base answer must match its frozen view record: ' + key)
        body = {field: value for field, value in frozen.items() if field not in {'id', 'version'}}
        if frozen['version'] != contracts.digest(body):
            raise ValueError('Base record version changed: ' + key)
    allowed_kinds = set(contracts.result_schema(task)['properties']['records']['items']['properties']['kind']['enum'])
    if not set(spec['addKinds']).issubset(allowed_kinds):
        raise ValueError('Added kind is outside the original extraction contract')
    for issue in _unique(seed['issues'], 'id', 'selected issue').values():
        if issue['sha256'] != contracts.digest({k: v for k, v in issue.items() if k != 'sha256'}):
            raise ValueError('Selected issue content binding changed')
        if issue['finding']['requirement'] not in assigned:
            raise ValueError('Selected issue must refer to an original assigned obligation')


def response_schema(seed, task, spec):
    """The explicit delta contract, distinct from an ordinary extraction answer."""
    validate_spec(seed, task, spec)
    c_operation = task.get('amendmentOperationId')
    contracts.validate(c_operation, contracts.SHA256)
    result = contracts.result_schema(task)['properties']
    disposition = contracts.obj({
        'issueId': contracts.TEXT, 'issueSha256': contracts.SHA256,
        'status': {'type': 'string', 'enum': [
            'changed', 'already-addressed', 'source-refuted', 'unresolved']},
        'recordKeys': contracts.STRINGS,
        'currentRecordRefs': contracts.arr(contracts.obj({
            'key': contracts.TEXT, 'sha256': contracts.SHA256})),
        'evidence': contracts.arr(deepcopy(contracts.EVIDENCE)), 'reason': contracts.TEXT,
        'relatedRequirements': deepcopy(result['unknowns']['items']['properties']['relatedRequirements']),
        'blocksRequirements': deepcopy(result['unknowns']['items']['properties']['blocksRequirements'])})
    return contracts.obj({
        'operationId': {'type': 'string', 'const': c_operation},
        'seedSha256': {'type': 'string', 'const': spec['seedSha256']},
        'baseCandidateSha256': {'type': 'string', 'const': seed['baseCandidateSha256']},
        'changes': contracts.arr(contracts.obj({
            'key': contracts.TEXT,
            'expectedVersion': {'anyOf': [deepcopy(contracts.SHA256), {'type': 'null'}]},
            'record': deepcopy(result['records']['items'])})),
        'factUsage': deepcopy(result.get('factUsage', contracts.arr(contracts.obj({
            'recordKey': contracts.TEXT, 'factIds': contracts.STRINGS, 'reason': contracts.TEXT})))),
        'dispositions': contracts.arr(disposition),
        'unknowns': deepcopy(result['unknowns']), 'followups': deepcopy(result['followups'])})


def issue_bindings(seed, patch):
    """Freeze all selected issues and author declarations for a new review."""
    issues = _unique(seed['issues'], 'id', 'selected issue')
    dispositions = _unique(patch['dispositions'], 'issueId', 'issue disposition')
    if set(issues) != set(dispositions):
        raise ValueError('Every selected issue requires exactly one disposition')
    base = {record['key']: record for record in seed['answer']['records']}
    changes = _unique(patch['changes'], 'key', 'record change')
    actual_delta = {key for key, change in changes.items() if change['record'] != base.get(key)}
    known = set(seed['view']['records']) | set(changes)
    bindings = []
    for identifier, issue in issues.items():
        if issue['sha256'] != contracts.digest({k: v for k, v in issue.items() if k != 'sha256'}):
            raise ValueError('Selected issue content binding changed')
        disposition = dispositions[identifier]
        if disposition['issueSha256'] != issue['sha256']:
            raise ValueError('Issue disposition content binding changed')
        keys = disposition['recordKeys']
        if len(keys) != len(set(keys)) or not set(keys).issubset(known):
            raise ValueError('Disposition must name unique current or changed records')
        refs = _unique(disposition['currentRecordRefs'], 'key', 'current record reference')
        for key, ref in refs.items():
            frozen = seed['view']['records'].get(key)
            if key not in keys or frozen is None or frozen['version'] != ref['sha256']:
                raise ValueError('Current record reference must bind its exact base version')
        related = set(disposition['relatedRequirements'])
        blocked = set(disposition['blocksRequirements'])
        if not blocked.issubset(related & set(seed['requirements'])):
            raise ValueError('Disposition blocking obligations must be declared current related obligations')
        status = disposition['status']
        if status == 'changed':
            if not keys or not set(keys).issubset(actual_delta) or not disposition['evidence']:
                raise ValueError('Changed disposition requires matching actual delta and source evidence')
        elif status in {'already-addressed', 'source-refuted'}:
            if not disposition['evidence'] or set(refs) != set(keys):
                raise ValueError('Addressed or refuted disposition requires current record refs and source evidence')
        elif status != 'unresolved':
            raise ValueError('Unknown issue disposition status')
        if status != 'unresolved' and blocked:
            raise ValueError('Only an unresolved disposition may declare blocking obligations')
        bindings.append({'id': identifier, 'sha256': issue['sha256'],
                         'dispositionSha256': contracts.digest(disposition),
                         'requirement': issue['finding']['requirement']})
    return bindings


def apply_patch(seed, task, spec, patch):
    """Retain base content; omission is never deletion or resolution."""
    contracts.validate(patch, response_schema(seed, task, spec))
    issue_bindings(seed, patch)
    records = _unique(deepcopy(seed['answer']['records']), 'key', 'base record')
    changes = _unique(patch['changes'], 'key', 'record change')
    usages = _unique(deepcopy(seed['answer'].get('factUsage', [])), 'recordKey', 'base fact usage')
    new_usages = _unique(patch['factUsage'], 'recordKey', 'delta fact usage')
    if set(new_usages) - set(changes) or (task.get('sourceFactsSha256') and set(new_usages) != set(changes)):
        raise ValueError('Fact usage must name exactly the changed or added keys')
    for key, change in changes.items():
        record = change['record']
        if key != record['key']:
            raise ValueError('Change key must match the submitted record key')
        if record['ownerRequirement'] not in task['requirements']:
            raise ValueError('Amendment record must retain an original assigned owner')
        if key in records:
            previous = records[key]
            if key not in spec['replaceKeys']:
                raise ValueError('Replacement key is outside the explicit amendment scope')
            if change['expectedVersion'] != seed['view']['records'][key]['version']:
                raise ValueError('Replacement expected version is stale or absent: ' + key)
            if any(previous[field] != record[field] for field in ('key', 'kind', 'ownerRequirement')):
                raise ValueError('Replacement cannot change key, kind or owner')
            if previous == record:
                raise ValueError('A replacement must contain an actual delta')
        else:
            if key in seed['view']['records']:
                raise ValueError('Added key collides with a retained view record')
            if change['expectedVersion'] is not None:
                raise ValueError('An added record requires a null expected version')
            if record['kind'] not in spec['addKinds']:
                raise ValueError('Added record kind is outside the explicit amendment scope')
        records[key] = deepcopy(record)
        if key in new_usages:
            usages[key] = deepcopy(new_usages[key])
    unknowns = _unique(deepcopy(seed['answer']['unknowns']), 'id', 'base unknown identity')
    for identifier, unknown in _unique(patch['unknowns'], 'id', 'new unknown identity').items():
        if not set(unknown['blocksRequirements']).issubset(unknown['relatedRequirements']):
            raise ValueError('Unknown blocking obligations must be related obligations')
        if identifier in unknowns and unknowns[identifier] != unknown:
            raise ValueError('An existing unknown identity cannot be overwritten')
        unknowns[identifier] = deepcopy(unknown)
    followups = {}
    for followup in [*seed['answer'].get('followups', []), *seed['followups'], *patch['followups']]:
        followups.setdefault(contracts.digest(followup), deepcopy(followup))
    return {'records': list(records.values()),
            'unknowns': list(unknowns.values()),
            'followups': list(followups.values()),
            'factUsage': list(usages.values())}


def canonical_answer(seed, task, spec, patch, closures):
    """Build an ordinary full answer, using fresh model-authored closures only."""
    draft = apply_patch(seed, task, spec, patch)
    by_requirement = _unique(closures, 'requirement', 'obligation closure')
    if set(by_requirement) != set(task['requirements']):
        raise ValueError('Every original assigned obligation requires an explicit new closure')
    coverage = []
    for requirement in task['requirements']:
        closure = by_requirement[requirement]
        contracts.validate(closure, investigation.closure_schema(task, requirement))
        if closure['status'] in {'supported', 'not-applicable'} and not closure['evidence']:
            raise ValueError('A positive closure requires original-source evidence')
        coverage.append({'requirement': requirement, 'status': closure['status'],
                         'recordKeys': [record['key'] for record in draft['records']
                                        if record['ownerRequirement'] == requirement],
                         'evidence': deepcopy(closure['evidence'])})
    answer = {'taskId': task['id'], 'records': draft['records'], 'coverage': coverage,
              'unknowns': draft['unknowns'], 'followups': draft['followups']}
    if task.get('sourceFactsSha256'):
        answer.update(sourceFactsSha256=task['sourceFactsSha256'], factUsage=draft['factUsage'])
    contracts.validate(answer, contracts.result_schema(task))
    return answer
