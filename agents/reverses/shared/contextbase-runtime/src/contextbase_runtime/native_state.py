"""Mechanical counts and explicit question identities for native task state."""
from collections import Counter
from copy import deepcopy

from . import investigation


def summarize(task, events, units, revision, context=None):
    """Expose bookkeeping without interpreting claims or merging unknowns."""
    context = context or {}
    explicit = investigation.explicit_unknown_definitions(task)
    definition_ids = {}
    if task['operation'] == 'verify':
        view = context.get('verificationView', {})
        records = list(view.get('records', {}).values())
        questions = [
            {**deepcopy(row['content']), 'id': identifier,
             'contentSha256': row['sha256']}
            for identifier, row in sorted(view.get('unknowns', {}).items())]
        definition_ids = {identifier: row['content']['id']
                          for identifier, row in view.get('unknowns', {}).items()}
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
    if explicit:
        for question in questions:
            identifier = question['id']
            definition = definition_ids.get(identifier, identifier)
            # Frozen future followups have identities but no draft definition.
            if task['operation'] == 'verify' and identifier.startswith('followup:'):
                owner, local = None, None
            else:
                owner, separator, local = definition.partition(':')
                if not separator:
                    owner, local = None, None
            question.update(referenceId=identifier, definitionId=local, unitId=owner)
    meaning = ('Counts of saved records only, not semantic completeness or acceptance. '
               'Unknown IDs name separate questions; reuse an existing ID only when its '
               'scope, related obligations and blocking rationale apply.')
    if explicit:
        meaning += (' referenceId is for classification.unknownIds; definitionId is local to unitId. '
                    'Saved questions remain retained; close a unit with unknowns=[] when no new '
                    'definitions are needed.')
    return {
        'scope': scope,
        'revision': revision,
        'meaning': meaning,
        'recordCounts': {
            'total': len(records),
            'byKind': dict(sorted(Counter(row['kind'] for row in records).items())),
            'byRequirement': dict(sorted(Counter(row['ownerRequirement'] for row in records).items())),
        },
        'unitStates': unit_states,
        'unknownCount': len(questions),
        'unknownDirectory': sorted(questions, key=lambda row: row['id']),
    }
