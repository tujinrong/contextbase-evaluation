"""Unadopted draft reduction, without providers or execution of input programs."""
from copy import deepcopy
import unittest

from contextbase_runtime import catalog, contracts, investigation


def task(*, facts=False, requirements=None):
    obligations = requirements or [
        {'id': 'catalog', 'question': 'List source responsibilities.', 'stage': 'discovery',
         'scope': 'selected-system', 'requires': []}]
    result = {'id': 'author-task', 'operation': 'extract', 'stage': 'discovery',
              'origin': 'host-executed', 'requirements': [item['id'] for item in obligations],
              'goalRequirementIds': [item['id'] for item in obligations],
              'goalRequirements': obligations, 'authorizedSourcePaths': ['A.cs', 'B.cs'],
              'catalogPolicy': catalog.VERSION,
              'recordKinds': ['system', 'entry', 'function', 'common', 'unclassified']}
    if facts:
        result['sourceFactsSha256'] = 'b' * 64
    return result


def unit(identifier='a', requirement='catalog'):
    return {'id': identifier, 'requirement': requirement,
            'question': 'Identify the responsibility and its evidence.', 'paths': ['A.cs']}


def evidence(path='A.cs'):
    return {'path': path, 'startLine': 1, 'endLine': 2, 'sha256': 'a' * 64}


def record(key='entry', *, kind='entry', owner='catalog', classification=None):
    return {'key': key, 'ownerRequirement': owner, 'kind': kind, 'name': key,
            'statement': 'Observed responsibility.', 'basis': 'observed-source',
            'evidence': [evidence()], 'dependsOn': [], 'classification': classification}


def draft(identifier='a', records=None, **changes):
    result = {'unitId': identifier, 'records': records or [], 'expectedVersions': [],
              'removals': [], 'unknowns': [], 'followups': [], 'factUsage': [],
              'remainingQuestions': [], 'complete': True, 'addUnits': []}
    result.update(changes)
    return result


def event(answer, definition=None):
    return {'unit': definition or unit(answer['unitId']), 'answer': answer}


def closure(requirement='catalog', status='supported'):
    return {'requirement': requirement, 'status': status,
            'reason': 'The original source was reviewed for this obligation.',
            'evidence': [evidence()]}


class InvestigationTests(unittest.TestCase):
    def test_plan_keeps_original_obligation_and_checks_coverage_and_paths(self):
        current = task()
        investigation.validate_plan(current, {'units': [unit('a'), unit('b')]})
        for invalid in ({'units': []}, {'units': [unit(), unit()]},
                        {'units': [{**unit(), 'paths': ['../outside.cs']}]},
                        {'units': [{**unit(), 'requirement': 'invented-scope'}]}):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                investigation.validate_plan(current, invalid)

    def test_two_units_retain_cross_references_and_materialize_once(self):
        main = record('main', kind='function', classification={
            'category': 'main', 'scope': 'selected-system', 'area': 'business',
            'businessObject': 'record', 'purpose': 'Search records', 'trigger': 'Search',
            'outcome': 'Results', 'rationale': 'Independent inquiry',
            'alternative': 'A step in editing', 'actors': ['operator'], 'entryRefs': ['entry']})
        events = [event(draft('a', [main])), event(draft('b', [record()]))]
        partial = investigation.reduce_drafts(task(), events[:1])
        self.assertEqual(['entry'], partial['records'][0]['classification']['entryRefs'])
        result = investigation.canonical_answer(task(), events, [closure()])
        self.assertEqual('author-task', result['taskId'])
        self.assertEqual(['main', 'entry'], [item['key'] for item in result['records']])
        self.assertEqual(['main', 'entry'], result['coverage'][0]['recordKeys'])
        self.assertNotIn('factUsage', result)

    def test_same_names_are_not_identity_and_conflict_requires_exact_cas(self):
        first = record('first')
        second = {**record('second'), 'name': first['name']}
        events = [event(draft('a', [first])), event(draft('b', [second]))]
        self.assertEqual(2, len(investigation.reduce_drafts(task(), events)['records']))
        changed = {**first, 'statement': 'Explicit source correction.'}
        with self.assertRaises(ValueError):
            investigation.reduce_drafts(task(), [*events, event(draft('b', [changed]))])
        corrected = draft('b', [changed], expectedVersions=[
            {'key': 'first', 'sha256': contracts.digest(first)}])
        result = investigation.reduce_drafts(task(), [*events, event(corrected)])
        self.assertEqual('Explicit source correction.', result['records'][0]['statement'])
        bad = deepcopy(corrected)
        bad['expectedVersions'][0]['sha256'] = 'f' * 64
        with self.assertRaises(ValueError):
            investigation.reduce_drafts(task(), [*events, event(bad)])

    def test_expected_version_cannot_create_record_or_change_kind_or_owner(self):
        current = record()
        seed = event(draft(records=[current]))
        for revised in ({**current, 'kind': 'system'}, {**current, 'ownerRequirement': 'other'}):
            change = draft('b', [revised], expectedVersions=[
                {'key': current['key'], 'sha256': contracts.digest(current)}])
            with self.subTest(revised=revised), self.assertRaises(ValueError):
                investigation.reduce_drafts(task(), [seed, event(change)])
        unexpected = draft(records=[current], expectedVersions=[
            {'key': current['key'], 'sha256': contracts.digest(current)}])
        with self.assertRaises(ValueError):
            investigation.reduce_drafts(task(), [event(unexpected)])

    def test_delete_preserves_unknown_and_followup_and_pending_namespacing(self):
        question = {'id': 'missing', 'question': 'Which configuration is active?',
                    'relatedRequirements': ['catalog'], 'blocksRequirements': ['catalog'],
                    'scopeReason': 'The active entry affects the catalog.'}
        pending = record('pending', kind='unclassified', classification={
            'category': 'pending', 'scope': 'selected-system', 'tentativeKind': 'entry',
            'impact': 'count-or-coverage', 'reason': 'Configuration is missing.',
            'unknownIds': ['missing']})
        followup = {'stage': 'discovery', 'question': 'Find the active configuration.',
                    'paths': ['A.cs'], 'requirement': 'catalog'}
        events = [event(draft(records=[pending], unknowns=[question], followups=[followup]))]
        reduced = investigation.reduce_drafts(task(), events)
        self.assertEqual('a:missing', reduced['unknowns'][0]['id'])
        self.assertEqual(['a:missing'], reduced['records'][0]['classification']['unknownIds'])
        removal = {'key': 'pending', 'sha256': contracts.digest(reduced['records'][0]),
                   'reason': 'Explicitly withdraw this candidate, leaving the question open.'}
        result = investigation.reduce_drafts(task(), [*events, event(draft('b', removals=[removal]))])
        self.assertEqual([], result['records'])
        self.assertEqual(reduced['unknowns'], result['unknowns'])
        self.assertEqual([followup], result['followups'])
        with self.assertRaises(ValueError):
            investigation.reduce_drafts(task(), [event(draft(removals=[removal]))])

    def test_unknown_identity_is_not_overwritten_or_erased_by_omission(self):
        unknown = {'id': 'q', 'question': 'Which target?', 'relatedRequirements': ['catalog'],
                   'blocksRequirements': ['catalog'], 'scopeReason': 'Target affects scope.'}
        events = [event(draft(unknowns=[unknown]))]
        result = investigation.reduce_drafts(task(), [*events, event(draft())])
        self.assertEqual(['a:q'], [item['id'] for item in result['unknowns']])
        changed = {**unknown, 'question': 'Silently replaced question'}
        with self.assertRaises(ValueError):
            investigation.reduce_drafts(task(), [*events, event(draft(unknowns=[changed]))])

    def test_cross_unit_pending_reference_preserves_an_exact_known_identity(self):
        unknown = {'id': 'q', 'question': 'Which target?', 'relatedRequirements': ['catalog'],
                   'blocksRequirements': ['catalog'], 'scopeReason': 'Target affects scope.'}
        pending = record('p', kind='unclassified', classification={
            'category': 'pending', 'scope': 'selected-system', 'tentativeKind': 'entry',
            'impact': 'count-or-coverage', 'reason': 'Target is not known.', 'unknownIds': ['a:q']})
        events = [event(draft(unknowns=[unknown])), event(draft('b', [pending]))]
        reduced = investigation.reduce_drafts(task(), events)
        self.assertEqual(['a:q'], reduced['records'][0]['classification']['unknownIds'])
        self.assertEqual(['a:q'], [item['id'] for item in reduced['unknowns']])

    def test_colon_in_reference_does_not_create_a_global_unknown_identity(self):
        pending = record('p', kind='unclassified', classification={
            'category': 'pending', 'scope': 'selected-system', 'tentativeKind': 'entry',
            'impact': 'count-or-coverage', 'reason': 'Target is not known.',
            'unknownIds': ['forged:question']})
        with self.assertRaises(ValueError):
            investigation.reduce_drafts(task(), [event(draft('b', [pending]))])

    def test_canonical_requires_explicit_exact_closures_and_complete_units(self):
        events = [event(draft(records=[record()]))]
        for closures in ([], [closure(), closure()], [closure('invented')]):
            with self.subTest(closures=closures), self.assertRaises(ValueError):
                investigation.canonical_answer(task(), events, closures)
        result = investigation.canonical_answer(task(), events, [closure(status='unresolved')])
        self.assertEqual('unresolved', result['coverage'][0]['status'])
        for incomplete in (draft(records=[record()], complete=False),
                           draft(records=[record()], remainingQuestions=['Still need a source.']),
                           draft(records=[record()], addUnits=[unit('unexecuted')])):
            with self.subTest(incomplete=incomplete), self.assertRaises(ValueError):
                investigation.canonical_answer(task(), [event(incomplete)], [closure()])

    def test_unit_owner_and_classification_scope_cannot_change_original_scope(self):
        pending = record('p', kind='unclassified', classification={
            'category': 'pending', 'scope': 'invented-subscope', 'tentativeKind': 'entry',
            'impact': 'outside-obligation', 'reason': 'Insufficient evidence.', 'unknownIds': ['q']})
        with self.assertRaises(ValueError):
            investigation.reduce_drafts(task(), [event(draft(records=[pending]))])
        requirements = [*task()['goalRequirements'],
            {'id': 'other', 'question': 'Inspect another scope.', 'stage': 'discovery',
             'scope': 'other', 'requires': []}]
        with self.assertRaises(ValueError):
            investigation.reduce_drafts(task(requirements=requirements),
                [event(draft(records=[record(owner='other')]))])

    def test_fact_usage_is_exact_per_submitted_record_and_retained_on_other_units(self):
        first = record('first')
        usage = {'recordKey': 'first', 'factIds': ['F-1'], 'reason': 'Overlapping declaration.'}
        events = [event(draft(records=[first], factUsage=[usage]))]
        with self.assertRaises(ValueError):
            investigation.reduce_drafts(task(facts=True), [event(draft(records=[first]))])
        with self.assertRaises(ValueError):
            investigation.reduce_drafts(task(), events)
        second = record('second')
        events.append(event(draft('b', [second], factUsage=[
            {'recordKey': 'second', 'factIds': [], 'reason': 'Unindexed source.'}])))
        result = investigation.canonical_answer(task(facts=True), events, [closure()])
        self.assertEqual('b' * 64, result['sourceFactsSha256'])
        self.assertEqual(['first', 'second'], [item['recordKey'] for item in result['factUsage']])

    def test_progress_ignores_wording_and_completion_declarations(self):
        before = investigation.reduce_drafts(task(), [event(draft(records=[record()]))])
        after = deepcopy(before)
        after['records'][0].update(name='Renamed', statement='Same evidence, different prose.')
        self.assertFalse(investigation.structural_progress(before, after))
        after['records'][0]['evidence'][0]['endLine'] += 1
        self.assertTrue(investigation.structural_progress(before, after))
        after = deepcopy(before)
        after['records'].append(record('new'))
        self.assertTrue(investigation.structural_progress(before, after))
        self.assertFalse(investigation.structural_progress(before, before))

    def test_replay_does_not_mutate_inputs_or_silently_change_unit_definitions(self):
        submitted = event(draft(records=[record()]))
        saved = deepcopy(submitted)
        first = investigation.reduce_drafts(task(), [submitted])
        self.assertEqual(first, investigation.reduce_drafts(task(), [submitted, submitted]))
        self.assertEqual(saved, submitted)
        changed_unit = {**unit(), 'question': 'A different investigation.'}
        with self.assertRaises(ValueError):
            investigation.reduce_drafts(task(), [submitted, event(draft(), changed_unit)])

    def test_removed_identity_and_unassigned_plan_coverage_are_preserved(self):
        seed = record()
        events = [event(draft(records=[seed])), event(draft('b', removals=[
            {'key': seed['key'], 'sha256': contracts.digest(seed), 'reason': 'Withdrawn.'}]))]
        with self.assertRaises(ValueError):
            investigation.reduce_drafts(task(), [*events, event(draft('b', [
                {**seed, 'kind': 'system'}]))])
        requirements = [*task()['goalRequirements'],
            {'id': 'other', 'question': 'Another obligation.', 'stage': 'discovery',
             'scope': 'other-scope', 'requires': []}]
        with self.assertRaises(ValueError):
            investigation.validate_plan(task(requirements=requirements), {'units': [unit()]})


if __name__ == '__main__':
    unittest.main()
