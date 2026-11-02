"""Mechanical association diagnostics are bounded, repairable and non-authorizing."""
from copy import deepcopy
import json
import unittest

from contextbase_runtime import contracts as c, investigation
from contextbase_runtime.facts import bound_usage_diagnostics
from contextbase_runtime.native_tools import Tools, run, replay
from test_native_mcp import rpc
import test_native_tools


class FactUsageDiagnosticsTests(unittest.TestCase):
    setUp = test_native_tools.NativeToolsTests.setUp
    tearDown = test_native_tools.NativeToolsTests.tearDown

    def answer(self, count=2):
        return {'sourceFactsSha256': self.index.sha256,
                'records': [{'key': 'r%02d' % n, 'evidence': [self.ref]} for n in range(count)],
                'factUsage': [{'recordKey': 'r%02d' % n, 'factIds': [], 'reason': 'Investigation ongoing'}
                              for n in range(count)]}

    def test_multiple_empty_associations_identify_all_record_keys_and_ranges(self):
        answer = self.answer(12)
        before = deepcopy(answer)
        diagnostics = self.index.usage_diagnostics(answer, self.index.sha256)
        self.assertEqual(before, answer)
        self.assertEqual(12, diagnostics['issueCount'])
        self.assertEqual([row['key'] for row in answer['records']], [row['recordKey'] for row in diagnostics['issues']])
        self.assertTrue(all(row['code'] == 'empty-usage' for row in diagnostics['issues']))
        self.assertTrue(all(row['queryPaths'] == ['A.cs'] for row in diagnostics['issues']))
        self.assertEqual({'path': 'A.cs', 'startLine': 1, 'endLine': 1}, diagnostics['issues'][0]['sourceRanges'][0])
        self.assertNotIn('factIds', json.dumps(diagnostics))
        self.assertNotIn('class A', json.dumps(diagnostics))
        with self.assertRaises(ValueError) as raised:
            self.index.validate_usage(answer, self.index.sha256)
        preview = json.loads(str(raised.exception).split(': ', 1)[1])
        self.assertEqual(8, len(preview['issues']))
        self.assertEqual(4, preview['remainingCount'])
        self.assertEqual('fact_usage_diagnostics', preview['completeReport']['collection'])

    def test_fixing_one_record_leaves_other_failures_visible(self):
        answer = self.answer()
        answer['factUsage'][0]['factIds'] = [self.index.document['facts'][0]['id']]
        diagnostics = self.index.usage_diagnostics(answer, self.index.sha256)
        self.assertEqual(['r01'], [row['recordKey'] for row in diagnostics['issues']])
        answer['factUsage'][1]['factIds'] = answer['factUsage'][0]['factIds']
        self.index.validate_usage(answer, self.index.sha256)

    def test_missing_unknown_and_disjoint_associations_remain_invalid(self):
        answer = self.answer()
        answer['factUsage'].pop()
        self.assertEqual(['empty-usage', 'missing-usage'],
                         [row['code'] for row in self.index.usage_diagnostics(answer, self.index.sha256)['issues']])
        answer = self.answer(1)
        answer['factUsage'][0]['factIds'] = ['does-not-exist']
        self.assertEqual('unknown-fact', self.index.usage_diagnostics(answer, self.index.sha256)['issues'][0]['code'])
        answer['factUsage'][0]['factIds'] = [self.index.document['facts'][0]['id']]
        answer['records'][0]['evidence'] = [{**self.ref, 'startLine': 99, 'endLine': 99}]
        self.assertEqual('disjoint-fact', self.index.usage_diagnostics(answer, self.index.sha256)['issues'][0]['code'])
        answer['factUsage'][0]['factIds'] = []
        self.index.validate_usage(answer, self.index.sha256)  # No indexed overlap, as before.
        with self.assertRaisesRegex(ValueError, 'another index'):
            self.index.validate_usage(answer, '0' * 64)

    def test_preview_bounds_ranges_without_changing_complete_report(self):
        diagnostics = self.index.usage_diagnostics(self.answer(1), self.index.sha256)
        diagnostics['issues'][0]['sourceRanges'] *= 10
        complete = deepcopy(diagnostics)
        preview = bound_usage_diagnostics(diagnostics, max_ranges=2)
        self.assertEqual(2, len(preview['issues'][0]['sourceRanges']))
        self.assertEqual(8, preview['issues'][0]['remainingSourceRangeCount'])
        self.assertEqual(complete, diagnostics)


class NativeFactUsageDiagnosticsTests(unittest.TestCase):
    setUp = test_native_tools.NativeToolsTests.setUp
    tearDown = test_native_tools.NativeToolsTests.tearDown

    def create(self, *, include=True, count=2, record_keys=None, extra_range=None):
        task = {**self.task, 'sourceFactsSha256': self.index.sha256}
        tools = Tools(self.source, self.index, task, self.context,
                      validate_final=lambda answer: self.index.validate_usage(answer, self.index.sha256))
        tools.handle('plan_update', {'operation_id': 'plan', 'expected_revision': 0, 'plan': {'units': [self.unit]}})
        draft = deepcopy(self.draft)
        draft.update(complete=False, remainingQuestions=['Check association semantics'])
        draft['records'] = [{**deepcopy(draft['records'][0]), 'key': key}
                            for key in (record_keys or ['r%02d' % n for n in range(count)])]
        if extra_range:
            draft['records'][0]['evidence'].append(extra_range)
        draft['factUsage'] = [{'recordKey': row['key'], 'factIds': [], 'reason': 'Inspection ongoing'} for row in draft['records']]
        args = {'operation_id': 'draft', 'expected_revision': 1, 'unit_id': 'u1', 'draft': draft}
        if include is not None:
            args['include_diagnostics'] = include
        reply = tools.handle('draft_apply', args)
        return tools, reply

    def full(self, tools, limit=32768):
        pointer = {'collection': 'fact_usage_diagnostics', 'offset': 0, 'limit': limit}
        chunks = []
        while True:
            reply = tools.handle('analysis_state', pointer)
            chunks.append(reply['text'])
            if reply['next_offset'] is None:
                break
            pointer = {**pointer, 'offset': reply['next_offset']}
        return json.loads(''.join(chunks))

    def test_incomplete_draft_saves_and_patch_reports_only_affected_records(self):
        tools, reply = self.create()
        self.assertEqual(2, tools.revision)
        self.assertEqual(2, reply['factUsageDiagnostics']['issueCount'])
        self.assertFalse(tools.events[-1]['answer']['complete'])
        patched = tools.handle('draft_patch', {'operation_id': 'patch', 'expected_revision': 2,
            'unit_id': 'u1', 'include_diagnostics': True,
            'factUsage': [{'recordKey': 'r00', 'factIds': [], 'reason': 'Still investigating'}]})
        self.assertEqual(['r00'], [row['recordKey'] for row in patched['factUsageDiagnostics']['issues']])
        full = self.full(tools, limit=71)
        self.assertEqual(['r00', 'r01'], [row['recordKey'] for row in full['issues']])
        self.assertEqual([], tools.pairs, 'Diagnostic state must grant no evidence delivery')

    def test_legacy_reply_is_unchanged_without_explicit_opt_in(self):
        tools, reply = self.create(include=None)
        self.assertEqual({'revision', 'readiness'}, set(reply))
        tools, reply = self.create(include=False)
        self.assertEqual({'revision', 'readiness'}, set(reply))

    def test_large_unicode_identity_and_path_keep_draft_reply_bounded_before_commit(self):
        from contextbase_runtime.native_evidence import reply_size, MAX_BATCH_BYTES
        huge_key, huge_path = '記録' * 10000, '領域' * 10000 + '.cs'
        tools, reply = self.create(record_keys=[huge_key], extra_range={**self.ref, 'path': huge_path})
        self.assertEqual(2, tools.revision)
        self.assertLessEqual(reply_size(reply), MAX_BATCH_BYTES)
        self.assertEqual(1, reply['factUsageDiagnostics']['issueCount'])
        self.assertEqual([], reply['factUsageDiagnostics']['issues'])
        self.assertEqual(1, reply['factUsageDiagnostics']['remainingCount'])
        self.assertEqual(huge_key, investigation.reduce_drafts(tools.task, tools.events)['records'][0]['key'])
        full = self.full(tools)
        self.assertEqual(huge_key, full['issues'][0]['recordKey'])
        self.assertIn(huge_path, full['issues'][0]['queryPaths'])

    def test_submission_keeps_empty_usage_strict_after_source_read(self):
        tools, _ = self.create(count=1)
        tools.handle('read', {'path': 'A.cs', 'startLine': 1, 'endLine': 1})
        finish = deepcopy(tools.events[-1]['answer'])
        finish.update(records=[], factUsage=[], expectedVersions=[], complete=True, remainingQuestions=[])
        tools.handle('draft_apply', {'operation_id': 'finish', 'expected_revision': 2, 'unit_id': 'u1', 'draft': finish})
        with self.assertRaisesRegex(ValueError, 'empty-usage.*|cannot be bypassed') as raised:
            tools.handle('submit_candidate', {'operation_id': 'submit', 'expected_revision': 3, 'closures': [self.closure]})
        self.assertIn('r00', str(raised.exception))
        self.assertIsNone(tools.submission)

    def test_diagnostics_do_not_deliver_recommended_fact_ids(self):
        tools, _ = self.create(count=1)
        self.full(tools)
        usage = [{'recordKey': 'r00', 'factIds': [self.index.document['facts'][0]['id']], 'reason': 'Must be delivered separately'}]
        tools.handle('draft_patch', {'operation_id': 'patch', 'expected_revision': 2,
            'unit_id': 'u1', 'include_diagnostics': True, 'factUsage': usage})
        tools.handle('read', {'path': 'A.cs', 'startLine': 1, 'endLine': 1})
        finish = deepcopy(tools.events[-1]['answer'])
        finish.update(records=[], factUsage=[], expectedVersions=[], complete=True, remainingQuestions=[])
        tools.handle('draft_apply', {'operation_id': 'finish', 'expected_revision': 3, 'unit_id': 'u1', 'draft': finish})
        with self.assertRaisesRegex(ValueError, 'facts not supplied'):
            tools.handle('submit_candidate', {'operation_id': 'submit', 'expected_revision': 4, 'closures': [self.closure]})

    def test_explicit_diagnostic_replies_recompute_during_replay(self):
        task = {**self.task, 'sourceFactsSha256': self.index.sha256}
        def provider(workspace, job, prompt, schema, timeout, **kwargs):
            def call(name, args):
                response = rpc(kwargs['tool_connection'], 'tools/call', {'name': name, 'arguments': args})['result']
                self.assertFalse(response['isError'], response)
                return json.loads(response['content'][0]['text'])
            call('read', {'path': 'A.cs', 'startLine': 1, 'endLine': 1})
            call('plan_update', {'operation_id': 'plan', 'expected_revision': 0, 'plan': {'units': [self.unit]}})
            draft = deepcopy(self.draft)
            draft['factUsage'] = [{'recordKey': 'system', 'factIds': [], 'reason': 'Incomplete association'}]
            reply = call('draft_apply', {'operation_id': 'draft', 'expected_revision': 1,
                'unit_id': 'u1', 'include_diagnostics': True, 'draft': draft})
            self.assertEqual('system', reply['factUsageDiagnostics']['issues'][0]['recordKey'])
            call('analysis_state', {'collection': 'fact_usage_diagnostics', 'offset': 0, 'limit': 32768})
            call('query', {'path': 'A.cs', 'offset': 0, 'limit': 100, 'kind': None, 'text': None,
                           'caller': None, 'callee': None, 'route': None})
            call('draft_patch', {'operation_id': 'patch', 'expected_revision': 2, 'unit_id': 'u1',
                'include_diagnostics': True, 'factUsage': [{'recordKey': 'system',
                    'factIds': [self.index.document['facts'][0]['id']], 'reason': 'Explicit delivered declaration'}]})
            receipt = call('submit_candidate', {'operation_id': 'submit', 'expected_revision': 3, 'closures': [self.closure]})
            return {'exit_code': 0, 'metadata': {'status': 'passed'}, 'answer': {'submission_id': receipt['submission_id']}}
        validator = lambda answer: self.index.validate_usage(answer, self.index.sha256)
        result = run(self.source, self.index, self.store, task, self.context, 'Analyze', provider, 10,
                     validate_final=validator)
        replay(self.source, self.index, self.store, task, result['answer'],
               result['metadata']['nativeTranscriptSha256'], validate_final=validator)

    def test_failed_run_diagnostics_recompute_when_checkpoint_resumes(self):
        task = {**self.task, 'sourceFactsSha256': self.index.sha256}
        draft = deepcopy(self.draft)
        draft['factUsage'] = [{'recordKey': 'system', 'factIds': [], 'reason': 'Association not yet chosen'}]
        def call(connection, name, args):
            response = rpc(connection, 'tools/call', {'name': name, 'arguments': args})['result']
            self.assertFalse(response['isError'], response)
            return json.loads(response['content'][0]['text'])
        def failed(workspace, job, prompt, schema, timeout, **kwargs):
            connection = kwargs['tool_connection']
            call(connection, 'plan_update', {'operation_id': 'plan', 'expected_revision': 0,
                                            'plan': {'units': [self.unit]}})
            reply = call(connection, 'draft_apply', {'operation_id': 'draft', 'expected_revision': 1,
                'unit_id': 'u1', 'include_diagnostics': True, 'draft': draft})
            self.assertEqual(1, reply['factUsageDiagnostics']['issueCount'])
            return {'exit_code': 1, 'metadata': {'status': 'failed'}}
        validator = lambda answer: self.index.validate_usage(answer, self.index.sha256)
        with self.assertRaises(RuntimeError):
            run(self.source, self.index, self.store, task, self.context, 'Analyze', failed, 10, validate_final=validator)
        resumed_task = {**task, 'id': 'resumed', 'contextId': 'resumed-context'}
        def resumed(workspace, job, prompt, schema, timeout, **kwargs):
            connection = kwargs['tool_connection']
            state = call(connection, 'analysis_state', {'collection': 'fact_usage_diagnostics', 'offset': 0, 'limit': 32768})
            self.assertEqual('system', json.loads(state['text'])['issues'][0]['recordKey'])
            call(connection, 'read', {'path': 'A.cs', 'startLine': 1, 'endLine': 1})
            call(connection, 'query', {'path': 'A.cs', 'offset': 0, 'limit': 100, 'kind': None,
                                      'text': None, 'caller': None, 'callee': None, 'route': None})
            call(connection, 'draft_patch', {'operation_id': 'patch', 'expected_revision': 2, 'unit_id': 'u1',
                'include_diagnostics': True, 'factUsage': [{'recordKey': 'system',
                    'factIds': [self.index.document['facts'][0]['id']], 'reason': 'Current execution delivered this declaration'}]})
            receipt = call(connection, 'submit_candidate', {'operation_id': 'submit', 'expected_revision': 3,
                                                          'closures': [self.closure]})
            return {'exit_code': 0, 'metadata': {'status': 'passed'}, 'answer': {'submission_id': receipt['submission_id']}}
        result = run(self.source, self.index, self.store, resumed_task, self.context, 'Analyze', resumed, 10,
                     validate_final=validator)
        replay(self.source, self.index, self.store, resumed_task, result['answer'],
               result['metadata']['nativeTranscriptSha256'], validate_final=validator)


if __name__ == '__main__':
    unittest.main()
