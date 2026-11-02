"""Native tools preserve host evidence, draft revisions and immutable submissions."""
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
import tempfile
import unittest
from contextbase_runtime import contracts as c
from contextbase_runtime.adapters import index_source
from contextbase_runtime.sources import SourceAccess
from contextbase_runtime.facts import FactIndex
from contextbase_runtime.storage import ArtifactStore
from contextbase_runtime.native_tools import Tools, run, replay
from test_native_mcp import rpc


class NativeToolsTests(unittest.TestCase):
    def setUp(self):
        home = Path(__file__).resolve().parents[1] / '.tmp'
        home.mkdir(exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=home)
        root = Path(self.tmp.name)
        source = root / 'input'
        source.mkdir()
        (source / 'A.cs').write_text('class A {}\n', encoding='utf-8')
        self.source = SourceAccess.create(source, root / 'snapshot', project_id='native-test', allowed_paths=['.'], excluded_paths=[])
        self.store = ArtifactStore(root / 'work')
        self.index = FactIndex.open(self.source, self.store, parser=index_source)
        self.task = {'id': 'native-author', 'contextId': 'native-context', 'operation': 'extract',
            'stage': 'discovery', 'origin': 'host-executed', 'requirements': ['catalog'],
            'goalRequirementIds': ['catalog'], 'snapshotId': self.source.snapshot_id,
            'goalRequirements': [{'id': 'catalog', 'stage': 'discovery', 'scope': 'all', 'question': 'Analyze source', 'requires': []}],
            'authorizedSourcePaths': ['A.cs']}
        self.ref = self.source.evidence('A.cs', 1, 1)
        self.context = {'task': self.task, 'currentRecords': {}, 'currentUnknowns': {}}
        self.unit = {'id': 'u1', 'requirement': 'catalog', 'question': 'Inspect system', 'paths': ['A.cs']}
        self.draft = {'unitId': 'u1', 'records': [{'key': 'system', 'ownerRequirement': 'catalog',
            'kind': 'system', 'name': 'A', 'statement': 'Class A exists.', 'basis': 'observed-source',
            'evidence': [self.ref], 'dependsOn': []}], 'expectedVersions': [], 'removals': [], 'unknowns': [],
            'followups': [], 'factUsage': [], 'remainingQuestions': [], 'complete': True, 'addUnits': []}
        self.closure = {'requirement': 'catalog', 'status': 'supported', 'reason': 'Read source', 'evidence': [self.ref]}

    def tearDown(self):
        self.tmp.cleanup()

    def complete(self, call):
        call('read', {'path': 'A.cs', 'startLine': 1, 'endLine': 1})
        call('plan_update', {'operation_id': 'plan', 'expected_revision': 0, 'plan': {'units': [self.unit]}})
        call('draft_apply', {'operation_id': 'draft', 'expected_revision': 1, 'unit_id': 'u1', 'draft': self.draft})
        call('analysis_state', {'collection': 'draft_versions', 'offset': 0, 'limit': 12000})
        return call('submit_candidate', {'operation_id': 'submit', 'expected_revision': 2, 'closures': [self.closure]})

    def test_one_provider_execution_can_retrieve_draft_submit_and_replay(self):
        calls = []
        def provider(workspace, job, prompt, schema, timeout, **kwargs):
            calls.append(job)
            def tool(name, arguments):
                result = rpc(kwargs['tool_connection'], 'tools/call', {'name': name, 'arguments': arguments})['result']
                self.assertFalse(result['isError'], result)
                import json
                return json.loads(result['content'][0]['text'])
            submitted = self.complete(tool)
            return {'exit_code': 0, 'metadata': {'status': 'passed'}, 'answer': {'submission_id': submitted['submission_id']}}
        result = run(self.source, self.index, self.store, self.task, self.context, 'Analyze', provider, 10)
        self.assertEqual(1, len(calls))
        transcript_sha256 = result['metadata']['nativeTranscriptSha256']
        manifest = self.store.get('native-transcripts/' + transcript_sha256 + '.json')
        self.assertEqual(transcript_sha256, c.digest(manifest))
        execution = calls[0].parent
        self.assertFalse((execution / 'transcript.json').exists())
        self.assertTrue((execution / 'setup.json').is_file())
        self.assertEqual(len(manifest['calls']), len(list((execution / 'calls').glob('*.json'))))
        replay(self.source, self.index, self.store, self.task, result['answer'], transcript_sha256)
        broken = deepcopy(result['answer'])
        broken['records'][0]['statement'] = 'Unsupported replacement'
        with self.assertRaisesRegex(ValueError, 'submission replay'):
            replay(self.source, self.index, self.store, self.task, broken, result['metadata']['nativeTranscriptSha256'])

    def test_failed_provider_recovers_drafts_but_requires_fresh_source_delivery(self):
        def failed(workspace, job, prompt, schema, timeout, **kwargs):
            connection = kwargs['tool_connection']
            for name, arguments in [
                ('plan_update', {'operation_id': 'plan', 'expected_revision': 0, 'plan': {'units': [self.unit]}}),
                ('draft_apply', {'operation_id': 'draft', 'expected_revision': 1, 'unit_id': 'u1', 'draft': self.draft})]:
                reply = rpc(connection, 'tools/call', {'name': name, 'arguments': arguments})['result']
                self.assertFalse(reply['isError'])
            return {'exit_code': 1, 'metadata': {'status': 'failed'}}
        with self.assertRaises(RuntimeError):
            run(self.source, self.index, self.store, self.task, self.context, 'Analyze', failed, 10)
        task = {**self.task, 'id': 'resumed-author', 'contextId': 'resumed-context'}
        def resumed(workspace, job, prompt, schema, timeout, **kwargs):
            self.assertIn('Validated saved plan and drafts exist; current draft revision is 2', prompt)
            import json
            connection = kwargs['tool_connection']
            def call(name, arguments):
                return rpc(connection, 'tools/call', {'name': name, 'arguments': arguments})['result']
            versions = call('analysis_state', {'collection': 'draft_versions', 'offset': 0, 'limit': 12000})
            self.assertFalse(versions['isError'])
            self.assertEqual([{'key': 'system', 'sha256': c.digest(self.draft['records'][0])}], json.loads(json.loads(versions['content'][0]['text'])['text']))
            submit = {'operation_id': 'submit', 'expected_revision': 2, 'closures': [self.closure]}
            denied = call('submit_candidate', submit)
            self.assertTrue(denied['isError'])
            self.assertIn('not supplied', denied['content'][0]['text'])
            self.assertFalse(call('read', {'path': 'A.cs', 'startLine': 1, 'endLine': 1})['isError'])
            reply = call('submit_candidate', submit)
            self.assertFalse(reply['isError'], reply)
            identity = json.loads(reply['content'][0]['text'])['submission_id']
            return {'exit_code': 0, 'metadata': {'status': 'passed'}, 'answer': {'submission_id': identity}}
        result = run(self.source, self.index, self.store, task, self.context, 'Analyze', resumed, 10)
        replay(self.source, self.index, self.store, task, result['answer'], result['metadata']['nativeTranscriptSha256'])

    def test_review_retries_are_idempotent_and_submission_is_queryable(self):
        task = {**self.task, 'operation': 'verify', 'candidate': 'f' * 64,
                'viewSha256': 'a' * 64, 'unknownBindings': []}
        tools = Tools(self.source, self.index, task, {'verificationView': {'records': {}}})
        tools.handle('read', {'path': 'A.cs', 'startLine': 1, 'endLine': 1})
        review = {'taskId': task['id'], 'candidateSha256': task['candidate'], 'viewSha256': task['viewSha256'],
                  'checks': [{'requirement': 'catalog', 'status': 'pass', 'reason': 'Reviewed source', 'evidence': [self.ref]}],
                  'unknownChecks': [], 'findings': [], 'unknowns': []}
        receipt = tools.handle('review_submit', {'review': review})
        self.assertEqual(receipt, tools.handle('review_submit', {'review': review}))
        state = tools.handle('analysis_state', {'collection': 'submission', 'offset': 0, 'limit': 12000})
        import json
        self.assertEqual(receipt, json.loads(state['text']))
        changed = deepcopy(review)
        changed['checks'][0]['reason'] = 'Different judgment'
        with self.assertRaisesRegex(ValueError, 'frozen'):
            tools.handle('review_submit', {'review': changed})

    def test_argument_diagnostics_list_missing_fields_and_matching_classification(self):
        from contextbase_runtime import catalog

        tools = Tools(self.source, self.index, self.task, self.context)
        with self.assertRaises(ValueError) as caught:
            tools.handle('read', {})
        self.assertIn('path', str(caught.exception))
        self.assertIn('startLine', str(caught.exception))

        task = {**self.task, 'catalogPolicy': catalog.VERSION}
        tools = Tools(self.source, self.index, task, self.context)
        draft = deepcopy(self.draft)
        draft['records'][0].update(kind='common', classification={'category': 'common'})
        arguments = {'operation_id': 'draft', 'expected_revision': 0,
                     'unit_id': 'u1', 'draft': draft}
        with self.assertRaises(ValueError) as caught:
            tools.handle('draft_apply', arguments)
        self.assertIn('responsibility', str(caught.exception))
        self.assertIn('alternative', str(caught.exception))
        self.assertNotIn('businessObject', str(caught.exception))

        draft['records'] = [{} for _ in range(100)]
        with self.assertRaises(ValueError) as caught:
            tools.handle('draft_apply', arguments)
        self.assertLess(len(str(caught.exception)), 10000)
        self.assertIn('"truncated": true', str(caught.exception))

        lookup = tools.handle('contract_schema', {'contract': 'classification', 'category': 'common'})
        self.assertIn('responsibility', lookup['schema']['required'])

    def test_recovery_rejects_self_hashed_foreign_basis(self):
        from contextbase_runtime.native_tools import _basis, _recover, _state, _bootstrap, BOOTSTRAP_POLICY
        tools = Tools(self.source, self.index, self.task, self.context)
        plan = {'operation_id': 'plan', 'expected_revision': 0, 'plan': {'units': [self.unit]}}
        tools.handle('plan_update', plan)
        prefix = 'foreign-run'
        role = {'id': 'foreign-role'}
        setup = {'binding': {'version': 'contextbase-native-tools/1', 'task': self.task,
                  'snapshot': self.source.snapshot_id, 'index': self.index.sha256},
                 'context': self.context, 'roleSpec': role, 'bootstrapPolicy': BOOTSTRAP_POLICY,
                 'bootstrap': _bootstrap(self.task, self.context)}
        self.store.put(prefix + '/setup.json', setup)
        self.store.put(prefix + '/calls/00000001.json', tools.calls[0])
        foreign_basis = _basis(self.source, self.index, self.task, self.context, role)
        checkpoint = {'basis': foreign_basis, 'producerTask': self.task, 'callPrefix': prefix,
                      'callCount': 1, 'state': _state(tools)}
        consumer = Tools(self.source, self.index, self.task, self.context)
        for context, spec, task in [
            (self.context, {'id': 'consumer-role'}, self.task),
            ({**self.context, 'currentRecords': {'foreign': {}}}, role, self.task),
            (self.context, role, {**self.task, 'baseRevision': 'different'})]:
            with self.assertRaisesRegex(ValueError, 'basis changed'):
                _recover(consumer, checkpoint, self.source, self.index, self.store,
                         _basis(self.source, self.index, task, context, spec))

    def test_bootstrap_delivers_complete_small_fields_without_duplicate_task(self):
        import json
        from contextbase_runtime.native_tools import _bootstrap, MAX_BOOTSTRAP_CHARS
        context = {**self.context, 'assignment': {'purpose': 'Analyze complete scope'}}
        bootstrap = _bootstrap(self.task, context)
        self.assertEqual(self.task, bootstrap['included']['task'])
        self.assertEqual(context['assignment'], bootstrap['included']['assignment'])
        self.assertNotIn('task', bootstrap['directory']['context'])
        self.assertLessEqual(len(json.dumps(bootstrap, ensure_ascii=False, sort_keys=True, separators=(',', ':'))), MAX_BOOTSTRAP_CHARS)

    def test_large_bootstrap_omits_whole_field_and_exposes_exact_read_pointer(self):
        import json
        from contextbase_runtime.native_tools import _bootstrap, MAX_BOOTSTRAP_CHARS
        context = {**self.context, 'candidate': {'records': ['source claim' * 3000]}}
        bootstrap = _bootstrap(self.task, context)
        self.assertEqual(self.task, bootstrap['included']['task'])
        self.assertNotIn('candidate', bootstrap['included'])
        self.assertLessEqual(len(json.dumps(bootstrap, ensure_ascii=False, sort_keys=True, separators=(',', ':'))), MAX_BOOTSTRAP_CHARS)
        pointer = bootstrap['directory']['context']['candidate']['read']
        tools = Tools(self.source, self.index, self.task, context)
        chunks = []
        while True:
            reply = tools.handle('analysis_state', pointer)
            self.assertEqual('candidate', reply['field'])
            self.assertEqual(bootstrap['directory']['context']['candidate']['characters'], reply['total_characters'])
            chunks.append(reply['text'])
            if reply['next_offset'] is None:
                break
            pointer = {**pointer, 'offset': reply['next_offset']}
        self.assertEqual(context['candidate'], json.loads(''.join(chunks)))
        full = tools.handle('analysis_state', {'collection': 'context', 'offset': 0, 'limit': 12000})
        self.assertNotIn('field', full)
        with self.assertRaisesRegex(ValueError, 'Unknown top-level field'):
            tools.handle('analysis_state', {'collection': 'context', 'field': 'absent', 'offset': 0, 'limit': 12000})

    def test_bootstrap_material_does_not_supply_source_evidence(self):
        from contextbase_runtime.native_tools import _bootstrap
        context = {**self.context, 'claim': {'evidence': [self.ref], 'text': 'class A {}'}}
        self.assertIn('claim', _bootstrap(self.task, context)['included'])
        tools = Tools(self.source, self.index, self.task, context)
        tools.handle('plan_update', {'operation_id': 'plan', 'expected_revision': 0, 'plan': {'units': [self.unit]}})
        tools.handle('draft_apply', {'operation_id': 'draft', 'expected_revision': 1, 'unit_id': 'u1', 'draft': self.draft})
        with self.assertRaisesRegex(ValueError, 'not supplied'):
            tools.handle('submit_candidate', {'operation_id': 'submit', 'expected_revision': 2, 'closures': [self.closure]})

    def test_native_replay_rejects_rehashed_bootstrap_tampering(self):
        def provider(workspace, job, prompt, schema, timeout, **kwargs):
            import json
            self.assertIn('complete included task/material fields', prompt)
            self.assertNotIn('Read analysis_state(task/context)', prompt)
            def tool(name, arguments):
                response = rpc(kwargs['tool_connection'], 'tools/call', {'name': name, 'arguments': arguments})['result']
                self.assertFalse(response['isError'], response)
                return json.loads(response['content'][0]['text'])
            receipt = self.complete(tool)
            return {'exit_code': 0, 'metadata': {'status': 'passed'}, 'answer': {'submission_id': receipt['submission_id']}}
        result = run(self.source, self.index, self.store, self.task, self.context, 'Analyze', provider, 10)
        manifest = self.store.get('native-transcripts/' + result['metadata']['nativeTranscriptSha256'] + '.json')
        manifest['bootstrap']['included']['task']['authorizedSourcePaths'] = ['foreign.cs']
        changed_hash = c.digest(manifest)
        self.store.put('native-transcripts/' + changed_hash + '.json', manifest)
        with self.assertRaisesRegex(ValueError, 'bootstrap'):
            replay(self.source, self.index, self.store, self.task, result['answer'], changed_hash)

    def test_draft_version_tokens_allow_replace_remove_and_reject_stale_tokens(self):
        import json
        tools = Tools(self.source, self.index, self.task, self.context)
        tools.handle('plan_update', {'operation_id': 'plan', 'expected_revision': 0, 'plan': {'units': [self.unit]}})
        tools.handle('draft_apply', {'operation_id': 'initial', 'expected_revision': 1, 'unit_id': 'u1', 'draft': self.draft})
        query = {'collection': 'draft_versions', 'offset': 0, 'limit': 12000}
        reply = tools.handle('analysis_state', query)
        tokens = json.loads(reply['text'])
        self.assertEqual(2, reply['revision'])
        chunks, page = [], {**query, 'limit': 17}
        while True:
            part = tools.handle('analysis_state', page)
            chunks.append(part['text'])
            if part['next_offset'] is None:
                break
            page = {**page, 'offset': part['next_offset']}
        self.assertEqual(tokens, json.loads(''.join(chunks)))
        self.assertEqual([{'key': 'system', 'sha256': c.digest(self.draft['records'][0])}], tokens)
        changed = deepcopy(self.draft)
        changed['records'][0]['statement'] = 'Class A is declared in the supplied source.'
        changed['expectedVersions'] = tokens
        tools.handle('draft_apply', {'operation_id': 'replace', 'expected_revision': 2, 'unit_id': 'u1', 'draft': changed})
        stale = deepcopy(changed)
        stale['records'][0]['statement'] = 'Another changed statement'
        with self.assertRaisesRegex(ValueError, 'stale'):
            tools.handle('draft_apply', {'operation_id': 'stale', 'expected_revision': 3, 'unit_id': 'u1', 'draft': stale})
        current = json.loads(tools.handle('analysis_state', query)['text'])
        self.assertNotEqual(tokens, current)
        removed = {**deepcopy(self.draft), 'records': [], 'removals': [{**current[0], 'reason': 'Remove this explicit proposed record'}]}
        tools.handle('draft_apply', {'operation_id': 'remove', 'expected_revision': 3, 'unit_id': 'u1', 'draft': removed})
        self.assertEqual([], json.loads(tools.handle('analysis_state', query)['text']))
        with self.assertRaisesRegex(ValueError, 'top-level field'):
            tools.handle('analysis_state', {**query, 'field': 'system'})

    def test_draft_version_hash_uses_normalized_pending_unknown_ids(self):
        import json
        from contextbase_runtime import catalog
        task = {**self.task, 'catalogPolicy': catalog.VERSION}
        tools = Tools(self.source, self.index, task, self.context)
        tools.handle('plan_update', {'operation_id': 'plan', 'expected_revision': 0, 'plan': {'units': [self.unit]}})
        draft = deepcopy(self.draft)
        draft['records'][0].update(kind='unclassified', classification={
            'category': 'pending', 'scope': 'all', 'tentativeKind': 'common',
            'impact': 'count-or-coverage', 'reason': 'Classification needs more evidence', 'unknownIds': ['missing']})
        draft['unknowns'] = [{'id': 'missing', 'question': 'What is the source-supported classification?',
            'relatedRequirements': ['catalog'], 'blocksRequirements': ['catalog'], 'scopeReason': 'Classification affects coverage'}]
        tools.handle('draft_apply', {'operation_id': 'initial', 'expected_revision': 1, 'unit_id': 'u1', 'draft': draft})
        tokens = json.loads(tools.handle('analysis_state', {'collection': 'draft_versions', 'offset': 0, 'limit': 12000})['text'])
        normalized = deepcopy(draft['records'][0])
        normalized['classification']['unknownIds'] = ['u1:missing']
        self.assertEqual(c.digest(normalized), tokens[0]['sha256'])
        self.assertNotEqual(c.digest(draft['records'][0]), tokens[0]['sha256'])
        replacement = deepcopy(draft)
        replacement['unknowns'] = []
        replacement['records'][0]['statement'] = 'A remains pending classification with its original blocker.'
        replacement['expectedVersions'] = tokens
        tools.handle('draft_apply', {'operation_id': 'replacement', 'expected_revision': 2, 'unit_id': 'u1', 'draft': replacement})

    def test_cas_idempotency_and_role_permissions(self):
        tools = Tools(self.source, self.index, self.task, self.context)
        args = {'operation_id': 'plan', 'expected_revision': 0, 'plan': {'units': [self.unit]}}
        reply = tools.handle('plan_update', args)
        self.assertEqual(reply, tools.handle('plan_update', args))
        with self.assertRaisesRegex(ValueError, 'revision'):
            tools.handle('draft_apply', {'operation_id': 'draft', 'expected_revision': 0, 'unit_id': 'u1', 'draft': self.draft})
        with self.assertRaisesRegex(ValueError, 'authorized'):
            tools.handle('review_submit', {'review': {}})
        tools.active = False
        with self.assertRaisesRegex(ValueError, 'revoked'):
            tools.handle('inventory', {'offset': 0, 'limit': 10})

    def test_unread_citations_cannot_be_submitted(self):
        tools = Tools(self.source, self.index, self.task, self.context)
        tools.handle('plan_update', {'operation_id': 'plan', 'expected_revision': 0, 'plan': {'units': [self.unit]}})
        tools.handle('draft_apply', {'operation_id': 'draft', 'expected_revision': 1, 'unit_id': 'u1', 'draft': self.draft})
        with self.assertRaisesRegex(ValueError, 'not supplied'):
            tools.handle('submit_candidate', {'operation_id': 'submit', 'expected_revision': 2, 'closures': [self.closure]})

    def saved_execution(self, reads=1):
        def provider(workspace, job, prompt, schema, timeout, **kwargs):
            import json
            def call(name, arguments):
                response = rpc(kwargs['tool_connection'], 'tools/call', {'name': name, 'arguments': arguments})['result']
                self.assertFalse(response['isError'], response)
                return json.loads(response['content'][0]['text'])
            for _ in range(reads - 1):
                call('read', {'path': 'A.cs', 'startLine': 1, 'endLine': 1})
            submitted = self.complete(call)
            return {'exit_code': 0, 'metadata': {'status': 'passed'}, 'answer': {'submission_id': submitted['submission_id']}}
        return run(self.source, self.index, self.store, self.task, self.context, 'Analyze', provider, 10)

    def test_replay_binding_checks_are_constant_for_many_source_pages(self):
        from contextbase_runtime.evidence import EvidenceAccess
        result = self.saved_execution(reads=16)
        checks = []
        original = EvidenceAccess._assert_binding
        def counted(access):
            checks.append(1)
            return original(access)
        with patch.object(EvidenceAccess, '_assert_binding', counted):
            replay(self.source, self.index, self.store, self.task, result['answer'], result['metadata']['nativeTranscriptSha256'])
        self.assertLessEqual(len(checks), 4, 'Binding fences must be batch-scoped, not per source page')

    def test_batch_replay_rejects_self_hashed_tampered_source_reply(self):
        result = self.saved_execution()
        manifest = self.store.get('native-transcripts/' + result['metadata']['nativeTranscriptSha256'] + '.json')
        reply = manifest['calls'][0]['reply']
        reply['result']['sourceText'] = 'class Fabricated {}\n'
        reply['resultSha256'] = c.digest(reply['result'])
        reply['replySha256'] = c.digest({key: value for key, value in reply.items() if key != 'replySha256'})
        identifier = c.digest(manifest)
        self.store.put('native-transcripts/' + identifier + '.json', manifest)
        with self.assertRaisesRegex(ValueError, 'source replay'):
            replay(self.source, self.index, self.store, self.task, result['answer'], identifier)

    def test_future_verified_read_cannot_authorize_an_earlier_submission(self):
        result = self.saved_execution()
        manifest = self.store.get('native-transcripts/' + result['metadata']['nativeTranscriptSha256'] + '.json')
        read = manifest['calls'].pop(0)
        manifest['calls'].append(read)
        identifier = c.digest(manifest)
        self.store.put('native-transcripts/' + identifier + '.json', manifest)
        with self.assertRaisesRegex(ValueError, 'not supplied'):
            replay(self.source, self.index, self.store, self.task, result['answer'], identifier)

    def test_future_verified_query_cannot_authorize_earlier_fact_usage(self):
        from contextbase_runtime.native_tools import _replay_calls
        task = {**self.task, 'sourceFactsSha256': self.index.sha256}
        context = {**self.context, 'task': task}
        original = Tools(self.source, self.index, task, context)
        original.handle('query', {'offset': 0, 'limit': 50, 'path': None, 'kind': None,
                        'text': None, 'caller': None, 'callee': None, 'route': None})
        original.handle('read', {'path': 'A.cs', 'startLine': 1, 'endLine': 1})
        original.handle('plan_update', {'operation_id': 'plan', 'expected_revision': 0, 'plan': {'units': [self.unit]}})
        draft = deepcopy(self.draft)
        draft['factUsage'] = [{'recordKey': 'system', 'factIds': [self.index.document['facts'][0]['id']],
                               'reason': 'Supported by a delivered source symbol.'}]
        original.handle('draft_apply', {'operation_id': 'draft', 'expected_revision': 1, 'unit_id': 'u1', 'draft': draft})
        original.handle('submit_candidate', {'operation_id': 'submit', 'expected_revision': 2, 'closures': [self.closure]})
        calls = deepcopy(original.calls[1:] + original.calls[:1])
        with self.assertRaisesRegex(ValueError, 'facts not supplied'):
            _replay_calls(Tools(self.source, self.index, task, context), calls)

    def test_final_fence_rejects_late_unreferenced_snapshot_material(self):
        result = self.saved_execution()
        def mutate(answer):
            (self.source.root / 'sources/Unreferenced.cs').write_text('class Unreferenced {}', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Unlisted'):
            replay(self.source, self.index, self.store, self.task, result['answer'],
                   result['metadata']['nativeTranscriptSha256'], validate_final=mutate)

    def test_final_fence_rejects_index_mutation_during_submission(self):
        result = self.saved_execution()
        def mutate(answer):
            self.index.document['snapshotId'] = 'changed-after-batch'
        with self.assertRaisesRegex(ValueError, 'binding changed'):
            replay(self.source, self.index, self.store, self.task, result['answer'],
                   result['metadata']['nativeTranscriptSha256'], validate_final=mutate)

    def test_replay_source_arguments_cannot_override_authoritative_tool_name(self):
        from contextbase_runtime.native_tools import _replay_calls
        tools = Tools(self.source, self.index, self.task, self.context)
        with self.assertRaisesRegex(ValueError, 'Additional properties'):
            _replay_calls(tools, [{'name': 'read', 'arguments': {'operation': 'inventory',
                'path': 'A.cs', 'startLine': 1, 'endLine': 1}, 'reply': {}}])


if __name__ == '__main__':
    unittest.main()
