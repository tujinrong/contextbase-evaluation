"""Model-facing acquisition crosses the same draft, delivery and replay seams."""
from copy import deepcopy
import unittest
from contextbase_runtime.native_tools import Tools, run, replay
import test_native_tools as fixtures


class NativeTransportTests(unittest.TestCase):
    setUp = fixtures.NativeToolsTests.setUp
    tearDown = fixtures.NativeToolsTests.tearDown

    def test_batch_delivers_originals_for_submission_and_replay(self):
        def provider(workspace, job, prompt, schema, timeout, **options):
            from test_native_mcp import rpc
            import json
            def call(name, arguments):
                result = rpc(options['tool_connection'], 'tools/call', {'name': name, 'arguments': arguments})['result']
                self.assertFalse(result['isError'], result)
                return json.loads(result['content'][0]['text'])
            call('evidence_batch', {'requests': [
                {'operation': 'read', 'path': 'A.cs', 'startLine': 1, 'endLine': 1}]})
            call('plan_update', {'operation_id': 'plan', 'expected_revision': 0, 'plan': {'units': [self.unit]}})
            call('draft_apply', {'operation_id': 'draft', 'expected_revision': 1, 'unit_id': 'u1', 'draft': self.draft})
            submitted = call('submit_candidate', {'operation_id': 'submit', 'expected_revision': 2, 'closures': [self.closure]})
            return {'exit_code': 0, 'metadata': {'status': 'passed'}, 'answer': {'submission_id': submitted['submission_id']}}
        result = run(self.source, self.index, self.store, self.task, self.context, 'Analyze', provider, 10)
        replay(self.source, self.index, self.store, self.task, result['answer'], result['metadata']['nativeTranscriptSha256'])

    def test_assigned_followup_requires_ack_before_any_mutation(self):
        tools = Tools(self.source, self.index, self.task, self.context)
        tools.handle('plan_update', {'operation_id': 'plan', 'expected_revision': 0, 'plan': {'units': [self.unit]}})
        draft = deepcopy(self.draft)
        draft['followups'] = [{'stage': 'discovery', 'requirement': 'catalog',
                              'question': 'Confirm a deployment condition in a later runtime task.', 'paths': ['A.cs']}]
        arguments = {'operation_id': 'draft', 'expected_revision': 1, 'unit_id': 'u1', 'draft': draft}
        before = deepcopy((tools.events, tools.revision, tools.operations, tools.calls))
        with self.assertRaisesRegex(ValueError, 'followup|follow-up|unfinished'):
            tools.handle('draft_apply', arguments)
        self.assertEqual(before, (tools.events, tools.revision, tools.operations, tools.calls))
        reply = tools.handle('draft_apply', {**arguments, 'retain_blocking_followups': True})
        self.assertFalse(reply['readiness']['readyForReview'])
        self.assertEqual(1, len(tools.events[0]['answer']['followups']))

    def test_batch_cannot_invoke_mutation_or_hide_operation_override(self):
        tools = Tools(self.source, self.index, self.task, self.context)
        for operation in ['draft_apply', 'submit_candidate', 'review_submit']:
            with self.assertRaises(ValueError):
                tools.handle('evidence_batch', {'requests': [{'operation': operation}]})
        self.assertEqual([], tools.pairs)
        self.assertEqual([], tools.events)

    def test_state_pages_roundtrip_unicode_and_escaping_within_wire_budget(self):
        import json
        from contextbase_runtime.native_evidence import reply_size, MAX_BATCH_BYTES
        value = {'material': ('日本語中文 "quote" \\path\n\t\x01' * 5000)}
        tools = Tools(self.source, self.index, self.task, {'candidate': value})
        pointer = {'collection': 'context', 'field': 'candidate', 'offset': 0, 'limit': 32768}
        chunks = []
        while True:
            page = tools.handle('analysis_state', pointer)
            self.assertLessEqual(reply_size(page), MAX_BATCH_BYTES)
            chunks.append(page['text'])
            if page['next_offset'] is None:
                break
            self.assertEqual(pointer['offset'] + len(page['text']), page['next_offset'])
            self.assertGreater(page['next_offset'], pointer['offset'])
            pointer = {**pointer, 'offset': page['next_offset']}
        self.assertGreater(len(chunks), 1)
        self.assertEqual(value, json.loads(''.join(chunks)))

    def test_large_followup_diagnostics_do_not_discard_saved_followups(self):
        from contextbase_runtime.native_evidence import reply_size, MAX_BATCH_BYTES
        tools = Tools(self.source, self.index, self.task, self.context)
        tools.handle('plan_update', {'operation_id': 'plan', 'expected_revision': 0, 'plan': {'units': [self.unit]}})
        draft = deepcopy(self.draft)
        draft['followups'] = [{'stage': 'discovery', 'requirement': 'catalog',
            'question': 'Explicit remaining obligation ' + str(number), 'paths': ['A.cs']}
            for number in range(300)]
        reply = tools.handle('draft_apply', {'operation_id': 'draft', 'expected_revision': 1,
            'unit_id': 'u1', 'draft': draft, 'retain_blocking_followups': True})
        self.assertLessEqual(reply_size(reply), MAX_BATCH_BYTES)
        self.assertEqual(300, reply['readiness']['blockingConditionCount'])
        self.assertFalse(reply['readiness']['readyForReview'])
        self.assertEqual(draft['followups'], tools.events[0]['answer']['followups'])

    def test_future_batch_cannot_authorize_earlier_submission(self):
        from contextbase_runtime.native_tools import _replay_calls
        tools = Tools(self.source, self.index, self.task, self.context)
        tools.handle('evidence_batch', {'requests': [
            {'operation': 'read', 'path': 'A.cs', 'startLine': 1, 'endLine': 1}]})
        tools.handle('plan_update', {'operation_id': 'plan', 'expected_revision': 0, 'plan': {'units': [self.unit]}})
        tools.handle('draft_apply', {'operation_id': 'draft', 'expected_revision': 1, 'unit_id': 'u1', 'draft': self.draft})
        tools.handle('submit_candidate', {'operation_id': 'submit', 'expected_revision': 2, 'closures': [self.closure]})
        with self.assertRaisesRegex(ValueError, 'not supplied'):
            _replay_calls(Tools(self.source, self.index, self.task, self.context), tools.calls[1:] + tools.calls[:1])

    def test_unreturned_batch_suffix_has_no_source_delivery_rights(self):
        from pathlib import Path
        from contextbase_runtime.sources import SourceAccess
        from contextbase_runtime.facts import FactIndex
        from contextbase_runtime.storage import ArtifactStore
        from contextbase_runtime.adapters import index_source
        root = Path(self.tmp.name) / 'batch'
        source = root / 'input'
        source.mkdir(parents=True)
        (source / 'Large.cs').write_text(('//' + 'x' * 2500 + '\n') * 20, encoding='utf-8')
        (source / 'Z.cs').write_text('class Z {}\n', encoding='utf-8')
        snapshot = SourceAccess.create(source, root / 'snapshot', project_id='batch', allowed_paths=['.'], excluded_paths=[])
        index = FactIndex.open(snapshot, ArtifactStore(root / 'work'), parser=index_source)
        task = {**self.task, 'snapshotId': snapshot.snapshot_id, 'authorizedSourcePaths': ['Large.cs', 'Z.cs']}
        tools = Tools(snapshot, index, task, {**self.context, 'task': task})
        requests = [{'operation': 'read', 'path': 'Large.cs', 'startLine': 1, 'endLine': None}] * 7
        requests.append({'operation': 'read', 'path': 'Z.cs', 'startLine': 1, 'endLine': 1})
        reply = tools.handle('evidence_batch', {'requests': requests})
        self.assertIsNotNone(reply['next_request_index'])
        self.assertNotIn('Z.cs', [pair['request']['path'] for pair in tools.pairs])
        unit = {**self.unit, 'paths': ['Z.cs']}
        tools.handle('plan_update', {'operation_id': 'plan', 'expected_revision': 0, 'plan': {'units': [unit]}})
        ref = snapshot.evidence('Z.cs', 1, 1)
        draft = deepcopy(self.draft)
        draft['records'][0]['evidence'] = [ref]
        tools.handle('draft_apply', {'operation_id': 'draft', 'expected_revision': 1, 'unit_id': 'u1', 'draft': draft})
        closure = {**self.closure, 'evidence': [ref]}
        with self.assertRaisesRegex(ValueError, 'not supplied'):
            tools.handle('submit_candidate', {'operation_id': 'submit', 'expected_revision': 2, 'closures': [closure]})
        tools.handle('evidence_batch', {'requests': requests[reply['next_request_index']:]})
        # A continuation may itself be bounded. Read the exact outstanding source explicitly.
        tools.handle('evidence_batch', {'requests': [requests[-1]]})
        tools.handle('submit_candidate', {'operation_id': 'submit', 'expected_revision': 2, 'closures': [closure]})


if __name__ == '__main__':
    unittest.main()
