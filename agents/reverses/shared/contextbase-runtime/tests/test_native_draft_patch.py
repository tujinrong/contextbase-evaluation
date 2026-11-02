"""Native metadata/field patches retain the existing draft and acceptance gates."""
from copy import deepcopy
import json
import unittest

from contextbase_runtime import contracts as c, investigation
from contextbase_runtime.native_tools import Tools, run, replay
from test_native_mcp import rpc
import test_native_tools


class NativeDraftPatchTests(unittest.TestCase):
    setUp = test_native_tools.NativeToolsTests.setUp
    tearDown = test_native_tools.NativeToolsTests.tearDown

    def tools(self, *, facts=False, complete=True, question=None):
        task = {**self.task, **({'sourceFactsSha256': self.index.sha256} if facts else {})}
        tools = Tools(self.source, self.index, task, self.context)
        tools.handle('plan_update', {'operation_id': 'plan', 'expected_revision': 0,
                                    'plan': {'units': [self.unit]}})
        draft = deepcopy(self.draft)
        draft['complete'] = complete
        draft['remainingQuestions'] = [question] if question else []
        if facts:
            draft['factUsage'] = [{'recordKey': 'system', 'factIds': [],
                                  'reason': 'Source observation; no static fact claimed.'}]
        tools.handle('draft_apply', {'operation_id': 'initial', 'expected_revision': 1,
                                    'unit_id': 'u1', 'draft': draft})
        return tools

    def patch_args(self, **changes):
        return {'operation_id': 'patch', 'expected_revision': 2, 'unit_id': 'u1',
                'updates': [{'key': 'system', 'fields': {'statement': 'A declares class A.'}}], **changes}

    def current(self, tools):
        return investigation.reduce_drafts(tools.task, tools.events)

    def test_fact_usage_can_change_without_model_resending_record_body(self):
        tools = self.tools(facts=True)
        before = deepcopy(self.current(tools)['records'])
        args = self.patch_args(updates=[], factUsage=[{'recordKey': 'system', 'factIds': [],
                                                      'reason': 'Exact source text establishes this declaration.'}])
        tools.handle('draft_patch', args)
        current = self.current(tools)
        self.assertEqual(before, current['records'])
        self.assertEqual(args['factUsage'], current['factUsage'])
        self.assertEqual(args, tools.calls[-1]['arguments'])
        self.assertNotIn('records', tools.calls[-1]['arguments'])
        self.assertEqual([{'key': 'system', 'sha256': c.digest(before[0])}],
                         tools.events[-1]['answer']['expectedVersions'])

    def test_whole_fields_replace_without_changing_other_fields_or_usage(self):
        tools = self.tools(facts=True)
        before = deepcopy(self.current(tools))
        tools.handle('draft_patch', self.patch_args())
        current = self.current(tools)
        expected = deepcopy(before['records'][0])
        expected['statement'] = 'A declares class A.'
        self.assertEqual([expected], current['records'])
        self.assertEqual(before['factUsage'], current['factUsage'])

    def test_revision_and_operation_identity_are_checked_before_expansion(self):
        tools = self.tools()
        args = self.patch_args()
        before = deepcopy(tools.events)
        with self.assertRaisesRegex(ValueError, 'revision'):
            tools.handle('draft_patch', {**args, 'expected_revision': 0})
        self.assertEqual(before, tools.events)
        reply = tools.handle('draft_patch', args)
        self.assertEqual(reply, tools.handle('draft_patch', args))
        self.assertEqual(3, tools.revision)
        self.assertEqual(2, len(tools.events))
        with self.assertRaisesRegex(ValueError, 'identity reused'):
            tools.handle('draft_patch', {**args, 'updates': []})

    def test_patch_cannot_modify_identity_fields_or_create_records(self):
        tools = self.tools()
        for field in ('key', 'kind', 'ownerRequirement', 'unitId', 'complete'):
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'Invalid native tool arguments'):
                tools.handle('draft_patch', self.patch_args(updates=[{'key': 'system', 'fields': {field: 'changed'}}]))
        with self.assertRaisesRegex(ValueError, 'absent record'):
            tools.handle('draft_patch', self.patch_args(updates=[{'key': 'absent', 'fields': {'name': 'New'}}]))
        with self.assertRaisesRegex(ValueError, 'requires a record update'):
            tools.handle('draft_patch', self.patch_args(updates=[]))
        self.assertEqual(2, tools.revision)

    def test_record_unit_ownership_is_stricter_than_same_obligation(self):
        tools = Tools(self.source, self.index, self.task, self.context)
        second = {**self.unit, 'id': 'u2', 'question': 'Another part of the same obligation'}
        tools.handle('plan_update', {'operation_id': 'plan', 'expected_revision': 0,
                                    'plan': {'units': [self.unit, second]}})
        tools.handle('draft_apply', {'operation_id': 'first', 'expected_revision': 1,
                                    'unit_id': 'u1', 'draft': self.draft})
        other = {**deepcopy(self.draft), 'unitId': 'u2', 'records': []}
        tools.handle('draft_apply', {'operation_id': 'second', 'expected_revision': 2,
                                    'unit_id': 'u2', 'draft': other})
        with self.assertRaisesRegex(ValueError, 'another unit'):
            tools.handle('draft_patch', self.patch_args(expected_revision=3, unit_id='u2'))

    def test_failed_patch_does_not_leave_a_partially_updated_state(self):
        tools = self.tools()
        before = deepcopy((tools.events, tools.revision, tools.operations, tools.calls))
        args = self.patch_args(updates=[{'key': 'system', 'fields': {'name': 'Changed'}},
                                       {'key': 'absent', 'fields': {'statement': 'Cannot create'}}])
        with self.assertRaisesRegex(ValueError, 'absent'):
            tools.handle('draft_patch', args)
        self.assertEqual(before, (tools.events, tools.revision, tools.operations, tools.calls))

    def test_patch_retains_unfinished_unit_questions_unknowns_and_followups(self):
        tools = self.tools(complete=False, question='Read the missing source path')
        unknown = {'id': 'unresolved', 'question': 'Is the source complete?',
                   'relatedRequirements': ['catalog'], 'blocksRequirements': ['catalog'],
                   'scopeReason': 'Original scope still needs investigation.'}
        followup = {'stage': 'behavior', 'question': 'Inspect runtime separately', 'paths': ['A.cs'],
                    'requirement': None}
        # Existing creation interface explicitly declares investigation material.
        draft = deepcopy(self.draft)
        draft.update(records=[], complete=False, remainingQuestions=['Read the missing source path'],
                     unknowns=[unknown], followups=[followup])
        tools.handle('draft_apply', {'operation_id': 'questions', 'expected_revision': 2,
                                    'unit_id': 'u1', 'draft': draft})
        tools.handle('draft_patch', self.patch_args(expected_revision=3))
        state = tools.events[-1]['answer']
        self.assertFalse(state['complete'])
        self.assertEqual(['Read the missing source path'], state['remainingQuestions'])
        self.assertEqual([unknown], state['unknowns'])
        self.assertEqual([followup], state['followups'])
        with self.assertRaisesRegex(ValueError, 'finish with no remaining'):
            tools.handle('submit_candidate', {'operation_id': 'submit', 'expected_revision': 4,
                                             'closures': [self.closure]})

    def test_existing_canonical_unknown_reference_survives_patch(self):
        from contextbase_runtime import catalog
        task = {**self.task, 'catalogPolicy': catalog.VERSION}
        tools = Tools(self.source, self.index, task, self.context)
        tools.handle('plan_update', {'operation_id': 'plan', 'expected_revision': 0,
                                    'plan': {'units': [self.unit]}})
        draft = deepcopy(self.draft)
        draft['records'][0].update(kind='unclassified', classification={
            'category': 'pending', 'scope': 'all', 'tentativeKind': 'common',
            'impact': 'count-or-coverage', 'reason': 'Missing classification evidence', 'unknownIds': ['pending']})
        draft['unknowns'] = [{'id': 'pending', 'question': 'Which classification is supported?',
            'relatedRequirements': ['catalog'], 'blocksRequirements': ['catalog'], 'scopeReason': 'Original catalog count'}]
        tools.handle('draft_apply', {'operation_id': 'initial', 'expected_revision': 1,
                                    'unit_id': 'u1', 'draft': draft})
        tools.handle('draft_patch', self.patch_args())
        current = self.current(tools)
        self.assertEqual(['u1:pending'], current['records'][0]['classification']['unknownIds'])
        self.assertEqual(['u1:pending'], [row['id'] for row in current['unknowns']])

    def test_patch_does_not_grant_source_or_fact_delivery(self):
        tools = self.tools(facts=True)
        usage = [{'recordKey': 'system', 'factIds': [self.index.document['facts'][0]['id']],
                  'reason': 'Declaration identity must be independently delivered.'}]
        tools.handle('draft_patch', self.patch_args(updates=[], factUsage=usage))
        submit = {'operation_id': 'submit', 'expected_revision': 3, 'closures': [self.closure]}
        with self.assertRaisesRegex(ValueError, 'not supplied'):
            tools.handle('submit_candidate', submit)
        tools.handle('read', {'path': 'A.cs', 'startLine': 1, 'endLine': 1})
        with self.assertRaisesRegex(ValueError, 'facts not supplied'):
            tools.handle('submit_candidate', submit)

    def test_cross_unit_unknown_reference_retains_one_original_identity(self):
        from contextbase_runtime import catalog
        task = {**self.task, 'catalogPolicy': catalog.VERSION}
        tools = Tools(self.source, self.index, task, self.context)
        second = {**self.unit, 'id': 'u2', 'question': 'Classify another declaration'}
        tools.handle('plan_update', {'operation_id': 'plan', 'expected_revision': 0,
                                    'plan': {'units': [self.unit, second]}})
        first = deepcopy(self.draft)
        first['records'][0]['classification'] = None
        first['unknowns'] = [{'id': 'pending', 'question': 'Which classification is supported?',
            'relatedRequirements': ['catalog'], 'blocksRequirements': ['catalog'], 'scopeReason': 'Original catalog count'}]
        tools.handle('draft_apply', {'operation_id': 'first', 'expected_revision': 1,
                                    'unit_id': 'u1', 'draft': first})
        other = deepcopy(self.draft)
        other.update(unitId='u2', unknowns=[])
        other['records'][0].update(key='another', kind='unclassified', classification={
            'category': 'pending', 'scope': 'all', 'tentativeKind': 'common',
            'impact': 'count-or-coverage', 'reason': 'Same original investigation', 'unknownIds': ['u1:pending']})
        tools.handle('draft_apply', {'operation_id': 'second', 'expected_revision': 2,
                                    'unit_id': 'u2', 'draft': other})
        tools.handle('draft_patch', self.patch_args(expected_revision=3, unit_id='u2',
            updates=[{'key': 'another', 'fields': {'statement': 'Another declaration remains unresolved.'}}]))
        current = self.current(tools)
        self.assertEqual(['u1:pending'], [row['id'] for row in current['unknowns']])
        record = next(row for row in current['records'] if row['key'] == 'another')
        self.assertEqual(['u1:pending'], record['classification']['unknownIds'])

    def test_saved_patch_replays_and_freezes_with_raw_arguments(self):
        def provider(workspace, job, prompt, schema, timeout, **kwargs):
            def call(name, args):
                result = rpc(kwargs['tool_connection'], 'tools/call', {'name': name, 'arguments': args})['result']
                self.assertFalse(result['isError'], result)
                return json.loads(result['content'][0]['text'])
            call('read', {'path': 'A.cs', 'startLine': 1, 'endLine': 1})
            call('plan_update', {'operation_id': 'plan', 'expected_revision': 0, 'plan': {'units': [self.unit]}})
            call('draft_apply', {'operation_id': 'initial', 'expected_revision': 1, 'unit_id': 'u1', 'draft': self.draft})
            patch_args = self.patch_args()
            reply = call('draft_patch', patch_args)
            submitted = call('submit_candidate', {'operation_id': 'submit', 'expected_revision': 3, 'closures': [self.closure]})
            self.assertEqual(reply, call('draft_patch', patch_args))
            denied = rpc(kwargs['tool_connection'], 'tools/call', {'name': 'draft_patch', 'arguments': {
                **patch_args, 'operation_id': 'new-patch', 'expected_revision': 4}})['result']
            self.assertTrue(denied['isError'])
            return {'exit_code': 0, 'metadata': {'status': 'passed'}, 'answer': {'submission_id': submitted['submission_id']}}
        result = run(self.source, self.index, self.store, self.task, self.context, 'Analyze', provider, 10)
        digest = result['metadata']['nativeTranscriptSha256']
        transcript = self.store.get('native-transcripts/' + digest + '.json')
        patch_call = next(row for row in transcript['calls'] if row['name'] == 'draft_patch')
        self.assertEqual(self.patch_args(), patch_call['arguments'])
        execution = next(self.store.path('tasks/' + self.task['id'] + '/native').iterdir())
        timings = [self.store.get(path.relative_to(self.store.root).as_posix())
                   for path in sorted((execution / 'timings').glob('*.json'))]
        self.assertEqual(len(transcript['calls']) + 1, len(timings))
        self.assertEqual(['ValueError'], [row['errorType'] for row in timings if row['errorType']])
        failed = next(row for row in timings if row['errorType'])
        self.assertEqual('draft_patch', failed['tool'])
        self.assertIsNone(failed['successfulCallNumber'])
        self.assertTrue(all(row['elapsedSeconds'] >= 0 for row in timings))
        self.assertEqual([row['argumentsSha256'] for row in timings if row['successfulCallNumber']],
                         [c.digest(row['arguments']) for row in transcript['calls']])
        replay(self.source, self.index, self.store, self.task, result['answer'], digest)
        changed = deepcopy(transcript)
        next(row for row in changed['calls'] if row['name'] == 'draft_patch')['arguments']['updates'][0]['fields']['statement'] = 'Tampered'
        altered = c.digest(changed)
        self.store.put('native-transcripts/' + altered + '.json', changed)
        with self.assertRaisesRegex(ValueError, 'replay changed'):
            replay(self.source, self.index, self.store, self.task, result['answer'], altered)

    def test_checkpoint_recovers_patch_but_requires_current_execution_evidence(self):
        def failed(workspace, job, prompt, schema, timeout, **kwargs):
            for name, args in (
                    ('plan_update', {'operation_id': 'plan', 'expected_revision': 0, 'plan': {'units': [self.unit]}}),
                    ('draft_apply', {'operation_id': 'initial', 'expected_revision': 1, 'unit_id': 'u1', 'draft': self.draft}),
                    ('draft_patch', self.patch_args())):
                result = rpc(kwargs['tool_connection'], 'tools/call', {'name': name, 'arguments': args})['result']
                self.assertFalse(result['isError'], result)
            return {'exit_code': 1, 'metadata': {'status': 'failed'}}
        with self.assertRaises(RuntimeError):
            run(self.source, self.index, self.store, self.task, self.context, 'Analyze', failed, 10)
        task = {**self.task, 'id': 'resumed-author', 'contextId': 'resumed-context'}
        def resumed(workspace, job, prompt, schema, timeout, **kwargs):
            self.assertIn('current draft revision is 3', prompt)
            def call(name, args):
                return rpc(kwargs['tool_connection'], 'tools/call', {'name': name, 'arguments': args})['result']
            state = call('analysis_state', {'collection': 'drafts', 'offset': 0, 'limit': 12000})
            current = json.loads(json.loads(state['content'][0]['text'])['text'])
            self.assertEqual('A declares class A.', current['records'][0]['statement'])
            submit = {'operation_id': 'submit', 'expected_revision': 3, 'closures': [self.closure]}
            denied = call('submit_candidate', submit)
            self.assertTrue(denied['isError'])
            self.assertIn('not supplied', denied['content'][0]['text'])
            self.assertFalse(call('read', {'path': 'A.cs', 'startLine': 1, 'endLine': 1})['isError'])
            response = call('submit_candidate', submit)
            self.assertFalse(response['isError'], response)
            submission = json.loads(response['content'][0]['text'])['submission_id']
            return {'exit_code': 0, 'metadata': {'status': 'passed'}, 'answer': {'submission_id': submission}}
        result = run(self.source, self.index, self.store, task, self.context, 'Analyze', resumed, 10)
        replay(self.source, self.index, self.store, task, result['answer'], result['metadata']['nativeTranscriptSha256'])

    def test_verifier_cannot_gain_draft_patch(self):
        task = {**self.task, 'operation': 'verify', 'candidate': 'f' * 64, 'viewSha256': 'a' * 64, 'unknownBindings': []}
        tools = Tools(self.source, self.index, task, {'verificationView': {'records': {}}})
        with self.assertRaisesRegex(ValueError, 'not authorized'):
            tools.handle('draft_patch', self.patch_args())


if __name__ == '__main__':
    unittest.main()
