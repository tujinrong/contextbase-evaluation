"""Expand revision-checked native patches into the existing draft event contract.

The caller checks the revision before invoking this pure function. Evidence
associations remain model-authored; expansion only restores unchanged state.
"""
from copy import deepcopy

from . import contracts as c, investigation


FIELDS = ('name', 'statement', 'basis', 'evidence', 'dependsOn', 'classification')


def expand(task, events, unit_id, updates, fact_usage):
    current = investigation.reduce_drafts(task, events)
    records = {row['key']: row for row in current['records']}
    usages = {row['recordKey']: row for row in current['factUsage']}
    latest = None
    owners = {}
    for event in events:
        unit, answer = event['unit'], event['answer']
        if unit['id'] == unit_id:
            latest = answer
        for row in answer['records']:
            owners.setdefault(row['key'], unit['id'])
        for row in answer['removals']:
            owners.pop(row['key'], None)
    if latest is None:
        raise ValueError('Draft patch requires an existing draft for its unit')
    changed = _unique(updates, 'key', 'record update')
    proposed_usage = _unique(fact_usage, 'recordKey', 'fact usage')
    keys = list(dict.fromkeys([*changed, *proposed_usage]))
    if not keys:
        raise ValueError('Draft patch requires a record update or fact-usage replacement')
    for key in keys:
        if key not in records:
            raise ValueError('Draft patch cannot create an absent record: ' + key)
        if owners.get(key) != unit_id:
            raise ValueError('Draft patch cannot modify another unit record: ' + key)
    replacements = []
    for key in keys:
        row = deepcopy(records[key])
        if key in changed:
            fields = changed[key]['fields']
            if not fields or set(fields) - set(FIELDS):
                raise ValueError('Draft patch requires explicit permitted record fields')
            row.update(deepcopy(fields))
        replacements.append(row)
    # Reuse the unit's exact investigation state. A metadata patch cannot end it,
    # clear questions or followups, add units, or change an identity/ownership.
    draft = deepcopy(latest)
    draft.update(records=replacements,
                 expectedVersions=[{'key': key, 'sha256': c.digest(records[key])} for key in keys],
                 removals=[], addUnits=[],
                 factUsage=[deepcopy(proposed_usage.get(key, usages.get(key))) for key in keys]
                 if task.get('sourceFactsSha256') else [])
    if any(row is None for row in draft['factUsage']):
        raise ValueError('Patched record requires an existing or supplied fact-usage declaration')
    return draft


def _unique(rows, key, label):
    values = {row[key]: row for row in rows}
    if len(values) != len(rows):
        raise ValueError('Duplicate draft patch ' + label)
    return values
