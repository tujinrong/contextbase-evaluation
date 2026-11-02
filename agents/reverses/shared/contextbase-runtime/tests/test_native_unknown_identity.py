"""Unknown creation and reference keep one immutable identity in new tasks."""
from copy import deepcopy
import json
import unittest

from contextbase_runtime import catalog, contracts as c, investigation
from contextbase_runtime.native_contracts import ToolContracts
from contextbase_runtime.native_state import summarize
from contextbase_runtime.native_tools import Tools, run, replay
from test_native_mcp import rpc
import test_native_tools
from test_investigation import task, unit, draft, event


POLICY = 'contextbase-draft-unknowns/2'


def question(identifier='missing', *, blocks=None):
    return {'id': identifier, 'question': 'Which configuration applies?',
            'relatedRequirements': ['catalog'], 'blocksRequirements': blocks or [],
            'scopeReason': 'Configuration can affect the original catalog scope.'}


class NativeUnknownIdentityTests(unittest.TestCase):
    def setUp(self):
        test_native_tools.NativeToolsTests.setUp(self)
        self.draft['records'][0]['classification'] = None

    tearDown = test_native_tools.NativeToolsTests.tearDown

    def tools(self, *, second=False):
        current = {**self.task, 'draftUnknownPolicy': POLICY, 'catalogPolicy': catalog.VERSION}
        tools = Tools(self.source, self.index, current, self.context)
        units = [self.unit, {**self.unit, 'id': 'u2'}] if second else [self.unit]
        tools.handle('plan_update', {'operation_id': 'plan', 'expected_revision': 0,
                                    'plan': {'units': units}})
        return tools

    def save(self, tools, answer=None, *, identifier='initial', unit_id='u1'):
        tools.handle('draft_apply', {'operation_id': identifier, 'expected_revision': tools.revision,
                                    'unit_id': unit_id, 'draft': answer or deepcopy(self.draft)})

    def initial(self, *, blocks=None):
        answer = deepcopy(self.draft)
        answer.update(unknowns=[question(blocks=blocks)], complete=False,
                      remainingQuestions=['Inspect configuration applicability.'])
        return answer

    def summary(self, tools):
        page = tools.handle('analysis_state', {'collection': 'summary', 'offset': 0, 'limit': 32768})
        return json.loads(page['text'])

    def test_save_summary_close_preserves_one_identity_without_redeclaration(self):
        tools = self.tools()
        tools.handle('read', {'path': 'A.cs', 'startLine': 1, 'endLine': 1})
        self.save(tools, self.initial())
        directory = self.summary(tools)['unknownDirectory']
        self.assertEqual(('u1:missing', 'u1:missing', 'missing', 'u1'),
                         tuple(directory[0][key] for key in ('id', 'referenceId', 'definitionId', 'unitId')))
        self.save(tools, {**deepcopy(self.draft), 'records': [], 'unknowns': []}, identifier='close')
        tools.handle('submit_candidate', {'operation_id': 'submit', 'expected_revision': tools.revision,
                                         'closures': [self.closure]})
        self.assertEqual(['u1:missing'], [x['id'] for x in tools.submission['answer']['unknowns']])

    def test_full_reference_and_whitespace_definitions_are_rejected_atomically(self):
        for identifier in ('u1:missing', ' ', 'missing question'):
            with self.subTest(identifier=identifier):
                tools = self.tools()
                self.save(tools, self.initial())
                before = deepcopy((tools.revision, tools.events, tools.operations, tools.calls))
                answer = {**deepcopy(self.draft), 'records': [], 'unknowns': [question(identifier)]}
                with self.assertRaisesRegex(ValueError, r'local definition ID.*unknowns=\[\].*classification.unknownIds'):
                    self.save(tools, answer, identifier='mistaken-reference')
                self.assertEqual(before, (tools.revision, tools.events, tools.operations, tools.calls))

    def test_cross_unit_reference_and_patch_keep_original_scope_and_blocking(self):
        tools = self.tools(second=True)
        self.save(tools, self.initial(blocks=['catalog']))
        other = deepcopy(self.draft)
        other.update(unitId='u2', unknowns=[])
        other['records'][0].update(key='pending', kind='unclassified', classification={
            'category': 'pending', 'scope': 'all', 'tentativeKind': 'common',
            'impact': 'count-or-coverage', 'reason': 'Configuration affects classification.',
            'unknownIds': ['u1:missing']})
        self.save(tools, other, identifier='other', unit_id='u2')
        tools.handle('draft_patch', {'operation_id': 'patch', 'expected_revision': tools.revision,
                                    'unit_id': 'u2', 'updates': [{'key': 'pending', 'fields': {
                                        'statement': 'Configuration-dependent classification remains open.'}}]})
        current = investigation.reduce_drafts(tools.task, tools.events)
        self.assertEqual([{**question(blocks=['catalog']), 'id': 'u1:missing'}], current['unknowns'])
        pending = next(x for x in current['records'] if x['key'] == 'pending')
        self.assertEqual(['u1:missing'], pending['classification']['unknownIds'])
        self.assertEqual(1, self.summary(tools)['unknownCount'])

    def test_patch_of_defining_unit_keeps_local_declaration_and_immutable_question(self):
        tools = self.tools()
        self.save(tools, self.initial())
        tools.handle('draft_patch', {'operation_id': 'patch', 'expected_revision': tools.revision,
                                    'unit_id': 'u1', 'updates': [{'key': 'system', 'fields': {
                                        'statement': 'A is declared in original source.'}}]})
        self.assertEqual('missing', tools.events[-1]['answer']['unknowns'][0]['id'])
        self.assertEqual(['u1:missing'], [x['id'] for x in investigation.reduce_drafts(tools.task, tools.events)['unknowns']])
        changed = deepcopy(self.draft)
        changed.update(records=[], unknowns=[{**question(), 'question': 'Replace the question silently.'}])
        with self.assertRaisesRegex(ValueError, 'cannot be overwritten'):
            self.save(tools, changed, identifier='overwrite')

    def test_same_local_name_in_distinct_units_keeps_both_scopes(self):
        tools = self.tools(second=True)
        self.save(tools, self.initial())
        other = deepcopy(self.draft)
        other.update(unitId='u2', records=[], unknowns=[question(blocks=['catalog'])])
        self.save(tools, other, identifier='other', unit_id='u2')
        current = self.summary(tools)
        self.assertEqual(['u1:missing', 'u2:missing'], [x['referenceId'] for x in current['unknownDirectory']])
        self.assertEqual(['catalog'], current['unknownDirectory'][1]['blocksRequirements'])

    def test_native_transcript_binds_unknown_policy_and_replays_close_without_duplication(self):
        current = {**self.task, 'draftUnknownPolicy': POLICY, 'catalogPolicy': catalog.VERSION}
        context = {**self.context, 'task': current}
        def provider(workspace, job, prompt, schema, timeout, **kwargs):
            def call(name, arguments):
                reply = rpc(kwargs['tool_connection'], 'tools/call', {'name': name, 'arguments': arguments})['result']
                self.assertFalse(reply['isError'], reply)
                return json.loads(reply['content'][0]['text'])
            call('read', {'path': 'A.cs', 'startLine': 1, 'endLine': 1})
            call('plan_update', {'operation_id': 'plan', 'expected_revision': 0, 'plan': {'units': [self.unit]}})
            call('draft_apply', {'operation_id': 'initial', 'expected_revision': 1,
                                 'unit_id': 'u1', 'draft': self.initial()})
            directory = json.loads(call('analysis_state', {'collection': 'summary', 'offset': 0, 'limit': 32768})['text'])
            self.assertEqual('u1:missing', directory['unknownDirectory'][0]['referenceId'])
            call('draft_apply', {'operation_id': 'close', 'expected_revision': 2, 'unit_id': 'u1',
                                 'draft': {**deepcopy(self.draft), 'records': [], 'unknowns': []}})
            submitted = call('submit_candidate', {'operation_id': 'submit', 'expected_revision': 3,
                                                  'closures': [self.closure]})
            return {'exit_code': 0, 'metadata': {'status': 'passed'},
                    'answer': {'submission_id': submitted['submission_id']}}
        result = run(self.source, self.index, self.store, current, context, 'Inspect source', provider, 10)
        transcript = result['metadata']['nativeTranscriptSha256']
        self.assertEqual(['u1:missing'], [x['id'] for x in result['answer']['unknowns']])
        replay(self.source, self.index, self.store, current, result['answer'], transcript)
        legacy = {k:v for k,v in current.items() if k != 'draftUnknownPolicy'}
        with self.assertRaisesRegex(ValueError, 'Native transcript binding changed'):
            replay(self.source, self.index, self.store, legacy, result['answer'], transcript)


class UnknownPolicyContractTests(unittest.TestCase):
    def test_new_schema_advertises_local_definitions_and_preserved_questions(self):
        current = {**task(), 'draftUnknownPolicy': POLICY}
        schema = investigation.draft_schema(current, unit())
        definition = schema['properties']['unknowns']['items']['properties']['id']
        with self.assertRaises(ValueError):
            c.validate('a:missing', definition)
        self.assertIn('reference', definition['description'])
        tool = next(x for x in ToolContracts(current).schemas() if x['name'] == 'draft_apply')
        self.assertIn('unknowns=[]', tool['description'])

    def test_reducer_rejects_full_ids_without_native_adapter(self):
        current = {**task(), 'draftUnknownPolicy': POLICY}
        with self.assertRaisesRegex(ValueError, 'local definition ID'):
            investigation.reduce_drafts(current, [event(draft(unknowns=[question('a:missing')]))])

    def test_legacy_double_prefixed_events_replay_without_change_or_new_summary_fields(self):
        events = [event(draft(unknowns=[question()])), event(draft(unknowns=[question('a:missing')]))]
        reduced = investigation.reduce_drafts(task(), events)
        self.assertEqual(['a:missing', 'a:a:missing'], [x['id'] for x in reduced['unknowns']])
        summary = summarize(task(), events, [unit()], 2)
        self.assertTrue(all('referenceId' not in x for x in summary['unknownDirectory']))

    def test_unknown_policy_version_fails_closed(self):
        with self.assertRaisesRegex(ValueError, 'Unsupported draft unknown policy'):
            investigation.draft_schema({**task(), 'draftUnknownPolicy': 'future-version'}, unit())

    def test_verifier_directory_distinguishes_frozen_reference_from_local_definition(self):
        current = {**task(), 'operation': 'verify', 'draftUnknownPolicy': POLICY}
        authored = {**question(), 'id': 'a:missing'}
        future = {**question(), 'id': 'followup:' + 'c' * 64}
        context = {'verificationView': {'records': {}, 'unknowns': {
            'task:a:missing': {'content': authored, 'sha256': 'a' * 64},
            future['id']: {'content': future, 'sha256': 'b' * 64}}}}
        result = summarize(current, [], [], 0, context=context)
        by_id = {x['id']:x for x in result['unknownDirectory']}
        self.assertEqual(('task:a:missing', 'a', 'missing'),
                         tuple(by_id['task:a:missing'][k] for k in ('referenceId', 'unitId', 'definitionId')))
        self.assertIsNone(by_id[future['id']]['unitId'])
        self.assertIsNone(by_id[future['id']]['definitionId'])
        self.assertEqual(authored, context['verificationView']['unknowns']['task:a:missing']['content'])


if __name__ == '__main__':
    unittest.main()
