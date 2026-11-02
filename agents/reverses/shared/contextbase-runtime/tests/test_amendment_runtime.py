"""Public amendment lifecycle with synthetic provider and source custody only."""
from copy import deepcopy
import json
from unittest.mock import patch
import unittest

from contextbase_discovery import DiscoveryAgent
from contextbase_runtime import catalog, contracts
import test_amendment_seed as seed_fixture
from test_independent_agents import request


class AmendmentRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.fixture = seed_fixture.AmendmentSeedTests()
        self.fixture.setUp()
        self.root = self.fixture.root
        self.agent = DiscoveryAgent.create(self.root / 'source', self.root / 'amended',
                                            request(), incremental_mode=True)
        self.calls = []
        self.unresolved = False
        self.fail_review = False
        self.fail_closure = False
        self.reject_issue = False

    def tearDown(self):
        self.fixture.tearDown()

    def provider(self, workspace, job, prompt, schema, timeout, *, instruction_role='analysis'):
        context = json.loads(prompt.rsplit('\n', 1)[-1])
        self.calls.append(deepcopy(context))
        task, phase = context['task'], context['incremental']['phase']
        unit = context['incremental']['unit'] or {}
        if self.fail_review and phase == 'review':
            self.fail_review = False
            return {'exit_code': 1, 'metadata': {'status': 'failed'}, 'answer': None}
        if self.fail_closure and phase == 'closure':
            self.fail_closure = False
            return {'exit_code': 1, 'metadata': {'status': 'failed'}, 'answer': None}
        wrapper = {'protocol': 'contextbase-incremental/1', 'taskId': task['id'],
                   'action': 'requests', 'requests': [], 'answer': None, 'workingNotes': ''}
        if context['evidenceDialog']['round'] == 1:
            wrapper['requests'] = [{'operation': 'read', 'path': 'README.md',
                                    'startLine': 1, 'endLine': 2}]
        else:
            ref = self.fixture.ref()
            if phase == 'amend':
                seed = self.agent.session.store.get('amendment-seed.json')
                issue = seed['issues'][0]
                added = {**seed['answer']['records'][0], 'key': 'readme-index',
                         'name': 'Readme index', 'statement': 'A second source-backed material.'}
                disposition = {'issueId': issue['id'], 'issueSha256': issue['sha256'],
                               'status': 'unresolved' if self.unresolved else 'changed',
                               'recordKeys': [] if self.unresolved else ['readme-index'],
                               'currentRecordRefs': [], 'evidence': [ref],
                               'reason': 'Synthetic issue disposition.',
                               'relatedRequirements': ['catalog'],
                               'blocksRequirements': ['catalog'] if self.unresolved else []}
                answer = {'operationId': task['amendmentOperationId'], 'seedSha256': contracts.digest(seed),
                          'baseCandidateSha256': seed['baseCandidateSha256'],
                          'changes': [] if self.unresolved else [
                              {'key': 'readme-index', 'expectedVersion': None, 'record': added}],
                          'factUsage': [] if self.unresolved else [
                              {'recordKey': 'readme-index', 'factIds': [], 'reason': 'Plain text.'}],
                          'dispositions': [disposition], 'unknowns': [], 'followups': []}
            elif phase == 'closure':
                answer = {'requirement': 'catalog', 'status': 'unresolved' if self.unresolved else 'supported',
                          'reason': 'Fresh synthetic closure.', 'evidence': [ref]}
            elif phase == 'review':
                candidate = self.agent.session.store.get('candidates/' + task['candidate'] + '.json')
                view = candidate['view']
                positive = {'status': 'pass', 'reason': 'Fresh independent source check.', 'evidence': [ref]}
                classifications = {row['key']: row['sha256'] for row in catalog.bindings(view['records'])}
                answer = {'unitId': unit['id'], 'candidateSha256': task['candidate'],
                          'viewSha256': task['viewSha256'],
                          'recordChecks': [{'key': key, 'recordSha256': view['records'][key]['version'], **positive}
                                           for key in unit['recordKeys']],
                          'classificationChecks': [{'key': key, 'recordSha256': classifications[key], **positive}
                                                   for key in unit['recordKeys'] if key in classifications],
                          'unknownChecks': [{'unknownId': key, 'unknownSha256': view['unknowns'][key]['sha256'],
                                             'status': 'non-blocking', 'blocksRequirements': [],
                                             'reason': 'Retained future-stage question.', 'evidence': [ref]}
                                            for key in unit['unknownIds']],
                          'checks': [{'requirement': key, **positive} for key in unit['requirements']],
                          'scopeChecks': [{'scope': key, **positive} for key in unit['scopes']],
                          'findings': [], 'unknowns': [], 'factUsageCheck': positive,
                          'amendmentIssueChecks': [
                              {'issueId': row['id'], 'issueSha256': row['sha256'],
                               'dispositionSha256': row['dispositionSha256'],
                               **{**positive, 'status': 'fail' if self.reject_issue else 'pass'}}
                              for row in task['amendmentIssueBindings'] if row['id'] in unit['issueIds']]}
            else:
                raise AssertionError('Amendment must never restart extraction: ' + phase)
            wrapper.update(action='finish', answer=answer)
        return {'exit_code': 0, 'metadata': {'status': 'passed'}, 'answer': wrapper}

    def amend(self):
        with patch('contextbase_runtime.provider.run_job', side_effect=self.provider):
            return self.agent.amend_candidate(self.fixture.bundle, self.fixture.verification_id,
                                               replace_keys=[], add_kinds=['material'])

    def test_addition_preserves_base_and_runs_fresh_full_review_with_issue_check(self):
        result = self.amend()
        self.assertEqual('complete', result['status'])
        state = self.agent.session._state()
        self.assertEqual(1, len(state['candidates']))
        self.assertEqual(1, len(state['verifications']))
        saved = self.agent.session.store.get('candidates/' + state['candidates'][0] + '.json')
        base = self.fixture.agent.session.store.get('candidates/' + self.fixture.candidate['id'] + '.json')
        self.assertEqual(base['answer']['records'][0], saved['answer']['records'][0])
        self.assertEqual(base['view']['records']['material'], saved['view']['records']['material'])
        self.assertEqual(base['view']['unknowns'], saved['view']['unknowns'])
        self.assertEqual({'material', 'readme-index'}, set(saved['view']['records']))
        self.assertEqual('amended-untrusted-candidate', saved['provenance']['proposalOrigin'])
        self.assertEqual({'amend', 'closure', 'review'}, {row['incremental']['phase'] for row in self.calls})
        review = [row for row in self.calls if row['incremental']['phase'] == 'review']
        self.assertTrue(any(row['incremental']['unit']['kind'] == 'issues' for row in review))
        self.assertTrue(all('amendmentAudit' in row for row in review))
        original_contexts = {row['task']['contextId'] for row in self.calls if row['incremental']['phase'] != 'review'}
        self.assertTrue(original_contexts.isdisjoint(row['task']['contextId'] for row in review))

    def test_unresolved_current_issue_saves_candidate_without_starting_review(self):
        self.unresolved = True
        result = self.amend()
        self.assertEqual('needs-investigation', result['status'])
        self.assertEqual([], self.agent.session._state()['verifications'])
        self.assertEqual(1, len(self.agent.session._state()['candidates']))
        self.assertFalse(any(row['incremental']['phase'] == 'review' for row in self.calls))
        self.assertIsNone(result['pending']['verification'])

    def test_review_transport_failure_resumes_frozen_candidate_without_new_delta(self):
        self.fail_review = True
        with self.assertRaises(RuntimeError):
            self.amend()
        before = self.agent.session._state()['candidates'][:]
        amend_calls = sum(row['incremental']['phase'] == 'amend' for row in self.calls)
        self.agent.session.resume(request())
        with patch('contextbase_runtime.provider.run_job', side_effect=self.provider):
            self.assertEqual('complete', self.agent.run()['status'])
        self.assertEqual(before, self.agent.session._state()['candidates'])
        self.assertEqual(amend_calls, sum(row['incremental']['phase'] == 'amend' for row in self.calls))

    def test_independent_issue_failure_prevents_adoption_despite_other_checks_passing(self):
        self.reject_issue = True
        self.assertEqual('needs-investigation', self.amend()['status'])
        state = self.agent.session._state()
        self.assertEqual([], state['acceptedRequirements'])
        self.assertEqual(1, len(state['verifications']))
        result = self.agent.session.store.get('verifications/' + state['verifications'][0] + '.json')['answer']
        self.assertEqual('fail', result['amendmentIssueChecks'][0]['status'])
        self.assertEqual('fail', result['checks'][0]['status'])

    def test_seed_scope_cannot_change_while_resuming_a_frozen_candidate(self):
        self.fail_review = True
        with self.assertRaises(RuntimeError):
            self.amend()
        self.agent.session.resume(request())
        spec = self.agent.session.store.get('amendment-spec.json')
        spec['replaceKeys'] = ['material']
        seed_fixture.overwrite_artifact(self.agent.work, 'amendment-spec.json', spec)
        calls = len(self.calls)
        with patch('contextbase_runtime.provider.run_job', side_effect=self.provider):
            with self.assertRaisesRegex(ValueError, 'seed/spec binding changed'):
                self.agent.run()
        self.assertEqual(calls, len(self.calls))
        self.assertEqual([], self.agent.session._state()['acceptedRequirements'])

    def test_closure_failure_resumes_original_delta_without_reauthoring_it(self):
        self.fail_closure = True
        with self.assertRaises(RuntimeError):
            self.amend()
        self.assertEqual([], self.agent.session._state()['candidates'])
        amend_calls = sum(row['incremental']['phase'] == 'amend' for row in self.calls)
        self.agent.session.resume(request())
        with patch('contextbase_runtime.provider.run_job', side_effect=self.provider):
            self.assertEqual('complete', self.agent.run()['status'])
        self.assertEqual(amend_calls, sum(row['incremental']['phase'] == 'amend' for row in self.calls))


if __name__ == '__main__':
    unittest.main()
