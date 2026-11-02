"""Pure diagnostics for obligations that already prevent host acceptance.

These checks do not replace independent review or decide unknown semantics.
"""
from .contracts import digest


UNFINISHED_REASON = 'Candidate has unfinished assigned obligations; retain the partial result'


def assess(answer, accepted_requirements):
    """Apply the existing adoption predicate without granting acceptance."""
    accepted = set(accepted_requirements)
    conditions = [
        {'code': 'coverage-unresolved', 'requirement': item['requirement']}
        for item in answer['coverage'] if item['status'] == 'unresolved'
    ]
    conditions.extend(
        {'code': 'assigned-followup', 'requirement': item['requirement'],
         'followupSha256': digest(item)}
        for item in answer['followups'] if item['requirement'] in accepted
    )
    return {'readyForReview': not conditions,
            'reason': UNFINISHED_REASON if conditions else None,
            'blockingConditions': conditions}


def require_followup_acknowledgement(task, draft, existing_followups=(), *,
                                    retain_blocking_followups=False):
    """Reject newly assigned open work before the caller persists any event.

Identical sticky followups have already been acknowledged. Acknowledgement
retains their ordinary blocking meaning; it never changes a draft or readiness.
"""
    existing = {digest(item) for item in existing_followups}
    targets = set(task['requirements'])
    new = [{'requirement': item['requirement'], 'followupSha256': digest(item)}
           for item in draft.get('followups', [])
           if item['requirement'] in targets and digest(item) not in existing]
    if new and retain_blocking_followups is not True:
        raise ValueError(
            'New followup.requirement names a current obligation that must be completed, '
            'not merely a related area. Continue current investigation using plan units, '
            'addUnits or remainingQuestions; represent source uncertainty as unknowns with '
            'its related and blocking rationale. Use requirement=null for a future action '
            'only when you determine it is outside the current completion target. To '
            'deliberately retain unfinished assigned work, set retain_blocking_followups=true; '
            'the candidate will remain blocked. The host does not reclassify or delete it.')
    return {'newBlockingFollowups': new, 'acknowledged': bool(new) and retain_blocking_followups is True}
