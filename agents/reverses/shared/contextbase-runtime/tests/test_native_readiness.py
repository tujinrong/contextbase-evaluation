from copy import deepcopy
import unittest
from unittest.mock import MagicMock, patch

from contextbase_runtime.agent import AnalysisAgent
from contextbase_runtime import native_readiness


class NativeReadinessTests(unittest.TestCase):
    def answer(self, **changes):
        return {'coverage': [{'requirement': 'current', 'status': 'supported'}],
                'followups': [], 'unknowns': [], **changes}

    def note(self, requirement='current'):
        return {'stage': 'behavior', 'requirement': requirement,
                'question': 'Investigate source behavior', 'paths': ['A.cs']}

    def test_new_assigned_followup_requires_ack_without_mutation(self):
        task = {'requirements': ['current']}
        draft = {'followups': [self.note()]}
        before = deepcopy((task, draft))
        with self.assertRaisesRegex(ValueError, 'retain_blocking_followups'):
            native_readiness.require_followup_acknowledgement(task, draft)
        self.assertEqual(before, (task, draft))

    def test_acknowledged_followup_remains_blocking(self):
        draft = {'followups': [self.note()]}
        result = native_readiness.require_followup_acknowledgement(
            {'requirements': ['current']}, draft, retain_blocking_followups=True)
        self.assertEqual(1, len(result['newBlockingFollowups']))
        readiness = native_readiness.assess(self.answer(followups=draft['followups']), ['current'])
        self.assertFalse(readiness['readyForReview'])
        self.assertEqual('assigned-followup', readiness['blockingConditions'][0]['code'])

    def test_identical_sticky_followup_needs_no_repeated_ack(self):
        note = self.note()
        native_readiness.require_followup_acknowledgement(
            {'requirements': ['current']}, {'followups': [deepcopy(note)]}, [note])
        changed = {**note, 'question': 'A new investigation'}
        with self.assertRaises(ValueError):
            native_readiness.require_followup_acknowledgement(
                {'requirements': ['current']}, {'followups': [changed]}, [note])

    def test_unknown_and_future_followup_remain_available_to_review(self):
        answer = self.answer(followups=[self.note(None), self.note('future')],
                             unknowns=[{'blocksRequirements': ['current']}])
        self.assertTrue(native_readiness.assess(answer, ['current'])['readyForReview'])
        native_readiness.require_followup_acknowledgement(
            {'requirements': ['current']}, {'followups': answer['followups']})

    def test_coverage_unresolved_matches_legacy_even_outside_accepted_subset(self):
        answer = self.answer(coverage=[{'requirement': 'other', 'status': 'unresolved'}])
        self.assertFalse(native_readiness.assess(answer, ['current'])['readyForReview'])

    def test_shared_predicate_preserves_legacy_truth_table(self):
        for status in ('supported', 'not-applicable', 'unresolved'):
            for requirement in (None, 'current', 'future'):
                for accepted in ([], ['current'], ['future']):
                    answer = self.answer(coverage=[{'requirement': 'current', 'status': status}],
                                         followups=[self.note(requirement)])
                    blocked = status == 'unresolved' or requirement in accepted
                    with self.subTest(status=status, requirement=requirement, accepted=accepted):
                        self.assertEqual(blocked, not native_readiness.assess(answer, accepted)['readyForReview'])

    def attempt(self, answer, *, native=True, accepted=('current',)):
        agent = object.__new__(AnalysisAgent)
        agent.name, agent.stage = 'test', 'behavior'
        session = MagicMock()
        agent.session = session
        session.config = {'nativeToolsPolicy': native}
        session._state.return_value = {'candidates': []}
        session.execute.return_value = {'id': 'candidate', 'result': answer}
        session.store.get.return_value = {'view': {'acceptedRequirements': list(accepted)}}
        state = {'attempts': {}}
        session.store.transaction.return_value.__enter__.return_value = state
        session.verify.return_value = {'id': 'review', 'result': {'findings': []}}
        with patch('contextbase_runtime.amendment_runtime.unresolved', return_value=[]):
            result = agent._execute_attempt_scoped(['current'], timeout=1,
                inline_sources=False, runner=None, compact=False, attempt_key='attempt')
        return session, state, result

    def test_native_early_stop_preserves_candidate_and_records_attempt(self):
        session, state, (action, pending) = self.attempt(self.answer(followups=[self.note('retained')]), accepted=('current', 'retained'))
        session.verify.assert_not_called()
        session.adopt.assert_not_called()
        self.assertEqual('candidate', action['candidate'])
        self.assertIsNone(action['verification'])
        self.assertEqual(pending, state['attempts']['attempt'])
        self.assertEqual(pending['reason'], state['stopReason'])

    def test_normal_and_unknown_candidates_still_review(self):
        for answer in (self.answer(), self.answer(unknowns=[{'blocksRequirements': ['current']}])):
            with self.subTest(answer=answer):
                session, _, (_, pending) = self.attempt(answer)
                session.verify.assert_called_once()
                session.adopt.assert_called_once()
                self.assertIsNone(pending)

    def test_native_unresolved_coverage_stops_review(self):
        session, _, (_, pending) = self.attempt(self.answer(
            coverage=[{'requirement': 'current', 'status': 'unresolved'}]))
        session.verify.assert_not_called()
        self.assertEqual('coverage-unresolved', pending['readiness']['blockingConditions'][0]['code'])

    def test_legacy_still_reviews_before_adoption_gate(self):
        session, _, _ = self.attempt(self.answer(followups=[self.note()]), native=False)
        session.verify.assert_called_once()
        session.adopt.assert_called_once()


if __name__ == '__main__':
    unittest.main()
