"""Native deltas require new evidence and a fresh review of the complete candidate."""
from copy import deepcopy
import json
import unittest
from unittest.mock import patch

from contextbase_runtime import contracts as c, native_amendment
from contextbase_runtime.project_analysis import ProjectAnalysisAgent, validate_export
import test_project_analysis as fixture
from test_native_mcp import rpc


class NativeAmendmentFlowTests(unittest.TestCase):
    run_native = fixture.ProjectAnalysisTests.run_native

    def setUp(self):
        fixture.ProjectAnalysisTests.setUp(self)
        self.amending = False
        original = fixture.simulated_answer
        def reject(context):
            answer = original(context)
            answer['findings'] = [{'id': 'review-finding', 'severity': 'blocking',
                'requirement': 'rules', 'detail': 'Clarify the predicate interpretation',
                'evidence': [self.agent.session.source.evidence('Registration.cs', 1, 3)]}]
            return answer
        with patch.object(fixture, 'simulated_answer', side_effect=reject):
            self.assertEqual('needs-investigation', self.run_native()['status'])
        self.origin = self.agent
        state = self.origin.session._state()
        self.old_candidate = state['candidates'][-1]
        self.old_review = state['verifications'][-1]
        self.original = self.origin.session.store.get('candidates/' + self.old_candidate + '.json')
        self.agent = ProjectAnalysisAgent.create(self.source, self.root / 'amended', fixture.request())
        self.seed, self.spec = native_amendment.install(self.agent, self.origin.work,
            self.old_candidate, self.old_review, replace_keys=['rules.record'])
        self.amending = True
        self.skip_author_read = False
        self.skip_author_query = False
        self.stale_version = False
        self.reject_unselected = False
        self.amend_calls = []
        self.review_context = None

    def provider(self, workspace, job, prompt, schema, timeout, **options):
        if not self.amending:
            return fixture.ProjectAnalysisTests.provider(self, workspace, job, prompt, schema, timeout, **options)
        connection = options['tool_connection']
        def call(name, arguments):
            response = rpc(connection, 'tools/call', {'name': name, 'arguments': arguments})['result']
            if response['isError']:
                raise ValueError(response['content'][0]['text'])
            self.amend_calls.append((name, deepcopy(arguments)))
            return json.loads(response['content'][0]['text'])
        def material(collection):
            text, offset = '', 0
            while True:
                page = call('analysis_state', {'collection': collection, 'offset': offset, 'limit': 32768})
                text += page['text']
                if page['next_offset'] is None:
                    return json.loads(text)
                offset = page['next_offset']
        task, context = material('task'), material('context')
        if task['operation'] == 'verify':
            self.review_context = deepcopy(context)
            call('read', {'path': 'Registration.cs', 'startLine': 1, 'endLine': 3})
            call('query', {'offset': 0, 'limit': 100, 'path': None, 'kind': None,
                'text': None, 'caller': None, 'callee': None, 'route': None})
            review = fixture.simulated_answer(context)
            ref = self.agent.session.source.evidence('Registration.cs', 1, 3)
            review['amendmentIssueChecks'] = [{'issueId': row['id'], 'issueSha256': row['sha256'],
                'dispositionSha256': row['dispositionSha256'], 'status': 'pass',
                'reason': 'Independently checked the changed predicate against source', 'evidence': [ref]}
                for row in task['amendmentIssueBindings']]
            if self.reject_unselected:
                review['checks'][0].update(status='fail', reason='A retained catalog claim needs investigation')
                review['findings'] = [{'id': 'fresh-catalog-finding', 'severity': 'blocking',
                    'requirement': 'catalog', 'detail': 'Unrelated retained claim remains incomplete', 'evidence': [ref]}]
            submitted = call('review_submit', {'review': review})
        else:
            state = material('amendment')
            selected = state['selectedRecords']['rules.record']
            ref = self.agent.session.source.evidence('Registration.cs', 2, 2)
            if not self.skip_author_read:
                call('read', {'path': 'Registration.cs', 'startLine': 2, 'endLine': 2})
            if not self.skip_author_query:
                call('query', {'offset': 0, 'limit': 100, 'path': None, 'kind': None,
                    'text': None, 'caller': None, 'callee': None, 'route': None})
            record = deepcopy(selected['record'])
            record.update(statement='Save returns whether value is greater than zero.', evidence=[ref])
            delta = {'operationId': state['operationId'], 'seedSha256': state['seedSha256'],
                'baseCandidateSha256': state['baseCandidateSha256'],
                'changes': [{'key': record['key'], 'expectedVersion':
                    '0' * 64 if self.stale_version else selected['expectedVersion'], 'record': record}],
                'factUsage': deepcopy(selected['factUsage']), 'unknowns': [], 'followups': [],
                'dispositions': [{'issueId': issue['id'], 'issueSha256': issue['sha256'],
                    'status': 'changed', 'recordKeys': [record['key']], 'currentRecordRefs': [],
                    'evidence': [ref], 'reason': 'Replaced the predicate interpretation with the exact source condition',
                    'relatedRequirements': ['rules'], 'blocksRequirements': []} for issue in state['issues']]}
            closures = [{'requirement': key, 'status': 'supported',
                'reason': 'Fresh source-backed closure of the retained plus amended view', 'evidence': [ref]}
                for key in task['requirements']]
            submitted = call('submit_amendment', {'patch': delta, 'closures': closures})
        return {'exit_code': 0, 'metadata': {'status': 'passed'},
                'answer': {'submission_id': submitted['submission_id']}}

    def test_delta_retains_other_records_and_gets_fresh_complete_review(self):
        result = self.run_native()
        self.assertEqual('complete', result['status'])
        state = self.agent.session._state()
        candidate = self.agent.session.store.get('candidates/' + state['candidates'][-1] + '.json')
        before = {row['key']: row for row in self.original['answer']['records']}
        after = {row['key']: row for row in candidate['answer']['records']}
        self.assertEqual(before['catalog.record'], after['catalog.record'])
        self.assertEqual(before['links.record'], after['links.record'])
        self.assertNotEqual(before['rules.record'], after['rules.record'])
        self.assertEqual(set(before), set(self.review_context['verificationView']['records']))
        self.assertEqual(self.seed['priorFindings'], self.review_context['amendmentAudit']['priorFindings'])
        self.assertNotEqual(self.old_candidate, state['candidates'][-1])
        self.assertNotEqual(self.old_review, state['verifications'][-1])
        self.assertEqual(self.original, self.origin.session.store.get('candidates/' + self.old_candidate + '.json'))
        author_calls = self.amend_calls[:next(i for i, row in enumerate(self.amend_calls)
            if row[0] == 'submit_amendment') + 1]
        reads = [args for name, args in author_calls if name == 'read']
        self.assertEqual([{'path': 'Registration.cs', 'startLine': 2, 'endLine': 2}], reads)
        self.assertFalse(any(name in {'plan_update', 'draft_apply', 'submit_candidate'} for name, _ in author_calls))
        validate_export(self.agent.export())

    def test_imported_source_receipts_do_not_authorize_new_citations(self):
        self.skip_author_read = True
        with self.assertRaisesRegex(ValueError, 'not supplied'):
            self.run_native()
        self.assertEqual([], self.agent.session._state()['acceptedRequirements'])
        self.assertIsNone(self.review_context)

    def test_imported_fact_usage_requires_new_fact_delivery(self):
        self.skip_author_query = True
        with self.assertRaisesRegex(ValueError, 'facts not supplied'):
            self.run_native()
        self.assertIsNone(self.review_context)

    def test_replacement_requires_frozen_view_version(self):
        self.stale_version = True
        with self.assertRaisesRegex(ValueError, 'version|stale'):
            self.run_native()
        self.assertIsNone(self.review_context)

    def test_fresh_review_can_reject_an_unselected_retained_claim(self):
        self.reject_unselected = True
        result = self.run_native()
        self.assertEqual('needs-investigation', result['status'])
        self.assertEqual([], self.agent.session._state()['acceptedRequirements'])
        self.assertEqual(3, len(self.review_context['verificationView']['records']))
        with self.assertRaisesRegex(ValueError, 'every original obligation'):
            self.agent.export()

    def test_amendment_transcript_tampering_invalidates_replay(self):
        self.assertEqual('complete', self.run_native()['status'])
        session = self.agent.session
        candidate = session.store.get('candidates/' + session._state()['candidates'][-1] + '.json')
        task = session.store.get('tasks/' + candidate['taskId'] + '/request.json')
        identifier = candidate['provenance']['nativeTranscriptSha256']
        transcript = session.store.get('native-transcripts/' + identifier + '.json')
        transcript['submission']['amendment']['patch']['changes'][0]['record']['statement'] = 'Tampered delta'
        session.store.path('native-transcripts/' + identifier + '.json').write_text(
            json.dumps({'sha256': c.digest(transcript), 'payload': transcript}), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'binding|fingerprint|content'):
            session._replay_evidence(task, candidate)


if __name__ == '__main__':
    unittest.main()
