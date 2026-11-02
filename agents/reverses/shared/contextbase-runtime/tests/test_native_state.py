"""State summaries count actual saved data and retain independent question scopes."""
from copy import deepcopy
import unittest

from contextbase_runtime import contracts as c
from contextbase_runtime.native_state import summarize
from test_native_contracts import author_task


class NativeStateTests(unittest.TestCase):
    def setUp(self):
        self.task = author_task()
        self.unit = {'id': 'first', 'requirement': 'catalog', 'question': 'Inspect', 'paths': ['A.cs']}
        self.record = {'key': 'a', 'kind': 'system', 'ownerRequirement': 'catalog',
                       'name': 'A', 'statement': 'A exists', 'basis': 'observed-source',
                       'evidence': [{'path': 'A.cs', 'startLine': 1, 'endLine': 1, 'sha256': 'a' * 64}],
                       'dependsOn': []}
        self.question = {'id': 'missing', 'question': 'Which input applies?',
                         'relatedRequirements': ['catalog'], 'blocksRequirements': [],
                         'scopeReason': 'Unavailable configuration outside the source-only goal.'}
        self.draft = {'unitId': 'first', 'records': [self.record], 'expectedVersions': [],
                      'removals': [], 'unknowns': [self.question], 'followups': [],
                      'factUsage': [], 'remainingQuestions': ['Inspect registrations'],
                      'complete': False, 'addUnits': []}

    def test_counts_saved_records_and_preserves_unfinished_work(self):
        event = {'unit': self.unit, 'answer': self.draft}
        result = summarize(self.task, [event], [self.unit], 2)
        self.assertEqual({'total': 1, 'byKind': {'system': 1}, 'byRequirement': {'catalog': 1}}, result['recordCounts'])
        self.assertFalse(result['unitStates'][0]['complete'])
        self.assertEqual(['Inspect registrations'], result['unitStates'][0]['remainingQuestions'])
        self.assertEqual('first:missing', result['unknownDirectory'][0]['id'])
        result['unknownDirectory'][0]['question'] = 'Changed copy'
        self.assertEqual('Which input applies?', self.draft['unknowns'][0]['question'])

    def test_same_question_text_does_not_merge_distinct_scopes(self):
        other = {**self.unit, 'id': 'second'}
        draft = deepcopy(self.draft)
        draft.update(unitId='second', records=[])
        draft['unknowns'][0]['scopeReason'] = 'Different source scope with a blocking gap.'
        draft['unknowns'][0]['blocksRequirements'] = ['catalog']
        result = summarize(self.task, [{'unit': self.unit, 'answer': self.draft},
                           {'unit': other, 'answer': draft}], [self.unit, other], 3)
        self.assertEqual(2, result['unknownCount'])
        self.assertEqual(['first:missing', 'second:missing'], [q['id'] for q in result['unknownDirectory']])
        self.assertEqual(['catalog'], result['unknownDirectory'][1]['blocksRequirements'])

    def test_replacement_is_not_counted_as_an_additional_record(self):
        changed = deepcopy(self.draft)
        changed['records'][0]['statement'] = 'Updated claim'
        changed['expectedVersions'] = [{'key': 'a', 'sha256': c.digest(self.record)}]
        result = summarize(self.task, [{'unit': self.unit, 'answer': self.draft},
                           {'unit': self.unit, 'answer': changed}], [self.unit], 3)
        self.assertEqual(1, result['recordCounts']['total'])

    def test_verifier_counts_frozen_view_and_keeps_bound_unknown_identity(self):
        question = {'id': 'task:first:missing', 'content': self.question, 'sha256': 'c' * 64}
        context = {'verificationView': {'records': {'a': self.record},
                                       'unknowns': {question['id']: question}}}
        result = summarize({**self.task, 'operation': 'verify'}, [], [], 0, context=context)
        self.assertEqual('frozen-verification-view', result['scope'])
        self.assertEqual(1, result['recordCounts']['total'])
        self.assertEqual('task:first:missing', result['unknownDirectory'][0]['id'])
        self.assertEqual('c' * 64, result['unknownDirectory'][0]['contentSha256'])

    def test_unstarted_unit_is_not_reported_as_complete(self):
        result = summarize(self.task, [], [self.unit], 1)
        self.assertEqual(0, result['recordCounts']['total'])
        self.assertFalse(result['unitStates'][0]['hasDraft'])
        self.assertFalse(result['unitStates'][0]['complete'])


if __name__ == '__main__':
    unittest.main()
