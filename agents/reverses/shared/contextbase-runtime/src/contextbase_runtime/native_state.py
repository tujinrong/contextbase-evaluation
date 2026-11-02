"""Mechanical counts and explicit question identities for native task state."""
from collections import Counter
from copy import deepcopy

from . import investigation


def summarize(task, events, units, revision, context=None):
    """Expose bookkeeping without interpreting claims or merging unknowns."""
    context = context or {}
    if task['operation'] == 'verify':
        view = context.get('verificationView', {})
        records = list(view.get('records', {}).values())
        questions = [
            {**deepcopy(row['content']), 'id': identifier,
             'contentSha256': row['sha256']}
            for identifier, row in sorted(view.get('unknowns', {}).items())]
        scope = 'frozen-verification-view'
        unit_states = []
    else:
        draft = investigation.reduce_drafts(task, events) if events else {}
        records = draft.get('records', [])
        questions = deepcopy(draft.get('unknowns', []))
        scope = 'current-investigation-drafts'
        latest = {event['unit']['id']: event['answer'] for event in events}
        unit_states = [
            {'id': unit['id'], 'requirement': unit['requirement'],
             'hasDraft': unit['id'] in latest,
             'complete': latest.get(unit['id'], {}).get('complete', False),
             'remainingQuestions': deepcopy(latest.get(unit['id'], {}).get('remainingQuestions', []))}
            for unit in units]
    return {
        'scope': scope,
        'revision': revision,
        'meaning': 'Counts of saved records only, not semantic completeness or acceptance. '
                   'Unknown IDs name separate questions; reuse an existing ID only when its '
                   'scope, related obligations and blocking rationale apply.',
        'recordCounts': {
            'total': len(records),
            'byKind': dict(sorted(Counter(row['kind'] for row in records).items())),
            'byRequirement': dict(sorted(Counter(row['ownerRequirement'] for row in records).items())),
        },
        'unitStates': unit_states,
        'unknownCount': len(questions),
        'unknownDirectory': sorted(questions, key=lambda row: row['id']),
    }
