"""Public v2 workflow tests. Providers are patched at the host process seam."""
from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from contextbase.analysis import contracts
from contextbase.analysis.controller import AcceptanceError, Session
from contextbase.analysis.storage import ArtifactStore


def requirement(identifier, stage='discovery', requires=(), scope='orders'):
    return {'id': identifier, 'stage': stage, 'scope': scope,
            'question': 'Inspect ' + identifier, 'requires': list(requires)}


def unknown(identifier='missing', related=('catalog',), blocked=()):
    return {'id': identifier, 'question': 'A source fact is not yet known.',
            'relatedRequirements': list(related), 'blocksRequirements': list(blocked),
            'scopeReason': 'The original scope requires only the catalog, not external deployment details.'}


class ControllerTests(unittest.TestCase):
    def setUp(self):
        home = Path(__file__).resolve().parents[3] / '.tmp'
        home.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='analysis-workflow-', dir=home)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'Orders.cs').write_bytes(
            b'class Orders {\n public bool Save(int value) { return value > 0; }\n}\n')
        self.request = {'schema': contracts.VERSION, 'projectId': 'synthetic-workflow',
                        'goal': {'id': 'analysis', 'question': 'Inspect the selected source.',
                                 'requirements': [requirement('catalog')]},
                        'allowedPaths': ['.'], 'excludedPaths': []}
        self.session = Session.create(self.source, self.root / 'work', self.request)
        self.contexts = []
        self.calls = []

    def tearDown(self):
        self.temporary.cleanup()

    def configure(self, requirements, language='csharp'):
        self.request['goal']['requirements'] = requirements
        if language == 'java':
            (self.source / 'Orders.cs').rename(self.source / 'Orders.java')
        self.session = Session.create(self.source, self.root / ('work-' + str(len(requirements)) + language),
                                      self.request)

    def chain(self):
        self.configure([requirement('catalog'), requirement('relations', 'relationship', ['catalog']),
                        requirement('behavior', 'behavior', ['relations'])])

    def evidence(self):
        return self.session.source.evidence(self.session.source.paths[0], 1, 2)

    def response(self, prompt):
        context = json.loads(prompt[prompt.index('{"request":'):])
        task = context['task']
        self.contexts.append(task['contextId'])
        self.calls.append((task['operation'], task['stage'], task['requirements']))
        evidence = self.evidence()
        if task['operation'] == 'verify':
            decisions = []
            for binding in task['unknownBindings']:
                content = context['verificationView']['unknowns'][binding['id']]['content']
                blocked = content['blocksRequirements']
                decisions.append({'unknownId': binding['id'], 'unknownSha256': binding['sha256'],
                                  'status': 'blocking' if blocked else 'non-blocking',
                                  'blocksRequirements': blocked, 'reason': 'Checked against original goal.',
                                  'evidence': [evidence]})
            return {'taskId': task['id'], 'candidateSha256': task['candidate'],
                    'viewSha256': task['viewSha256'],
                    'checks': [{'requirement': key, 'status': 'pass',
                                'reason': 'Independently checked original source.', 'evidence': [evidence]}
                               for key in task['requirements']],
                    'unknownChecks': decisions, 'findings': [], 'unknowns': []}
        obligations = {item['id']: item for item in task['goalRequirements']}
        records = [{'key': key + '.record', 'ownerRequirement': key,
                    'kind': {'discovery': 'function', 'relationship': 'relation', 'behavior': 'fact'}[task['stage']],
                    'name': key, 'statement': 'Source-backed ' + task['stage'] + ' for ' + key,
                    'basis': 'observed-source', 'evidence': [evidence],
                    'dependsOn': [dep + '.record' for dep in obligations[key]['requires']]}
                   for key in task['requirements']]
        return {'taskId': task['id'], 'records': records,
                'coverage': [{'requirement': key, 'status': 'supported', 'recordKeys': [key + '.record'],
                              'evidence': [evidence]} for key in task['requirements']],
                'unknowns': [], 'followups': []}

    def runner(self, workspace, job_dir, prompt, schema, timeout_seconds):
        self.assertEqual(self.session.source.root, workspace)
        self.assertGreater(timeout_seconds, 0)
        return {'answer': self.response(prompt), 'exit_code': 0,
                'metadata': {'status': 'passed'}, 'usage': None}

    def execute(self, stage, *, runner=None, **kwargs):
        with patch('contextbase.ai.provider.run_job', side_effect=runner or self.runner):
            return self.session.execute(stage, **kwargs)

    def verify(self, candidate, *, runner=None, **kwargs):
        with patch('contextbase.ai.provider.run_job', side_effect=runner or self.runner):
            return self.session.verify(candidate, **kwargs)

    def run_flow(self, *, runner=None, **kwargs):
        with patch('contextbase.ai.provider.run_job', side_effect=runner or self.runner):
            return self.session.run(**kwargs)

    def reviewed(self, stage='discovery', **kwargs):
        candidate = self.execute(stage, **kwargs)['id']
        self.verify(candidate)
        return candidate

    def test_catalog_only_stops_before_deeper_agents(self):
        result = self.run_flow()
        self.assertEqual('complete', result['status'])
        self.assertEqual([('extract', 'discovery'), ('verify', 'discovery')],
                         [(op, stage) for op, stage, _ in self.calls])
        self.assertEqual(1, result['session']['version'])
        self.assertEqual(2, len(set(self.contexts)))

    def test_three_stages_have_six_independent_calls_and_versioned_handoffs(self):
        self.chain()
        result = self.run_flow()
        self.assertEqual('complete', result['status'])
        self.assertEqual(3, result['session']['version'])
        self.assertEqual(['discovery', 'relationship', 'behavior'],
                         [stage for op, stage, _ in self.calls if op == 'extract'])
        self.assertEqual(6, len(set(self.contexts)))
        records = result['session']['records']
        for child, parent in [('relations', 'catalog'), ('behavior', 'relations')]:
            self.assertEqual([{'key': parent + '.record', 'version': records[parent + '.record']['version']}],
                             records[child + '.record']['dependencies'])
        self.assertEqual(result['session']['revision'], Session.open(self.session.store.root).status()['revision'])
        self.assertFalse((self.session.store.root / 'output').exists())

    def test_partial_selected_goal_does_not_reduce_the_original_goal(self):
        self.chain()
        result = self.run_flow(requirements=['relations'])
        self.assertEqual('scope-complete', result['status'])
        self.assertEqual(['behavior'], result['session']['remainingRequirements'])
        self.assertEqual('active', result['session']['status'])
        self.assertEqual('complete', self.run_flow()['status'])

    def test_behavior_requires_its_verified_relationship_not_just_catalog(self):
        self.chain()
        self.session.adopt(self.reviewed())
        with self.assertRaisesRegex(ValueError, 'prerequisites'):
            self.execute('behavior')
        relations = self.execute('relationship')['id']
        with self.assertRaisesRegex(ValueError, 'prerequisites'):
            self.execute('behavior')
        self.verify(relations)
        self.session.adopt(relations)
        self.assertEqual('behavior', self.execute('behavior')['stage'])

    def test_verified_slice_advances_without_waiting_for_another_catalog(self):
        self.configure([requirement('cat-a', scope='a'), requirement('cat-b', scope='b'),
                        requirement('rel-a', 'relationship', ['cat-a'], 'a'),
                        requirement('rel-b', 'relationship', ['cat-b'], 'b'),
                        requirement('beh-a', 'behavior', ['rel-a'], 'a'),
                        requirement('beh-b', 'behavior', ['rel-b'], 'b')])
        self.assertEqual('complete', self.run_flow()['status'])
        self.assertEqual(['discovery', 'relationship', 'behavior', 'discovery', 'relationship', 'behavior'],
                         [stage for op, stage, _ in self.calls if op == 'extract'])

    def test_another_regions_relationship_cannot_unlock_behavior(self):
        self.configure([requirement('cat-a', scope='a'), requirement('cat-b', scope='b'),
                        requirement('rel-a', 'relationship', ['cat-a'], 'a'),
                        requirement('rel-b', 'relationship', ['cat-b'], 'b'),
                        requirement('beh-b', 'behavior', ['rel-b'], 'b')])
        self.run_flow(requirements=['rel-a'])
        with self.assertRaisesRegex(ValueError, 'prerequisites'):
            self.execute('behavior', requirements=['beh-b'])

    def test_manual_and_injected_results_cannot_attest_independence(self):
        task = self.session.prepare('discovery')
        prompt = json.dumps({'request': self.request, 'task': task})
        candidate = self.session.submit(task['id'], self.response(prompt))['id']
        self.verify(candidate)
        with self.assertRaisesRegex(AcceptanceError, 'provenance'):
            self.session.adopt(candidate)
        injected = self.session.execute('discovery', runner=self.runner)['id']
        self.session.verify(injected, runner=self.runner)
        with self.assertRaisesRegex(AcceptanceError, 'provenance'):
            self.session.adopt(injected)
        self.assertEqual(0, self.session.status()['version'])

    def test_author_cannot_self_assign_acceptance_or_skip_verification(self):
        candidate = self.execute('discovery')['id']
        with self.assertRaisesRegex(AcceptanceError, 'verification'):
            self.session.adopt(candidate)
        def invalid(*args):
            result = self.runner(*args)
            result['answer']['accepted'] = True
            return result
        with self.assertRaisesRegex(ValueError, 'contract'):
            self.execute('discovery', runner=invalid)
        self.assertEqual('stopped', self.session.status()['status'])

    def test_nonblocking_unknown_requires_an_explicit_independent_judgment(self):
        def note(*args):
            result = self.runner(*args)
            result['answer']['unknowns'] = [unknown()]
            return result
        candidate = self.execute('discovery', runner=note)['id']
        self.verify(candidate)
        state = self.session.adopt(candidate)
        item = next(iter(state['unknowns'].values()))
        self.assertEqual('non-blocking', item['decision']['status'])
        self.assertEqual(['catalog'], item['content']['relatedRequirements'])

    def test_verifier_can_detect_author_understated_unknown_impact(self):
        def note(*args):
            result = self.runner(*args)
            result['answer']['unknowns'] = [unknown()]
            return result
        candidate = self.execute('discovery', runner=note)['id']
        def block(*args):
            result = self.runner(*args)
            check = result['answer']['unknownChecks'][0]
            check.update(status='blocking', blocksRequirements=['catalog'])
            return result
        self.verify(candidate, runner=block)
        with self.assertRaisesRegex(AcceptanceError, 'unresolved'):
            self.session.adopt(candidate)

    def test_unknown_judgment_is_bound_to_exact_content(self):
        def note(*args):
            result = self.runner(*args)
            result['answer']['unknowns'] = [unknown()]
            return result
        candidate = self.execute('discovery', runner=note)['id']
        def changed(*args):
            result = self.runner(*args)
            result['answer']['unknownChecks'][0]['unknownSha256'] = '0' * 64
            return result
        with self.assertRaisesRegex(ValueError, 'binding'):
            self.verify(candidate, runner=changed)

    def test_later_evidence_can_resolve_an_unknown_retained_from_an_earlier_stage(self):
        self.chain()
        def early(*args):
            result = self.runner(*args)
            result['answer']['unknowns'] = [unknown(related=['behavior'], blocked=['behavior'])]
            return result
        self.session.adopt(self.reviewed(runner=early))
        self.session.adopt(self.reviewed('relationship'))
        candidate = self.execute('behavior')['id']
        def resolve(*args):
            result = self.runner(*args)
            result['answer']['unknownChecks'][0].update(status='resolved', blocksRequirements=[])
            return result
        self.verify(candidate, runner=resolve)
        self.assertEqual('complete', self.session.adopt(candidate)['status'])

    def test_upstream_replacement_cannot_silently_drop_an_open_future_blocker(self):
        self.chain()
        def early(*args):
            result = self.runner(*args)
            result['answer']['unknowns'] = [unknown(related=['behavior'], blocked=['behavior'])]
            return result
        self.session.adopt(self.reviewed(runner=early))
        original_id = next(iter(self.session.status()['unknowns']))
        # This replacement omits unknowns entirely; it is not a resolution.
        self.session.adopt(self.reviewed())
        self.assertIn(original_id, self.session.status()['unknowns'])
        result = self.run_flow()
        self.assertEqual('needs-investigation', result['status'])
        self.assertEqual(['behavior'], result['session']['remainingRequirements'])
        self.assertIn(original_id, result['session']['unknowns'])

    def test_explicit_revision_keeps_open_unknown_content_for_independent_rejudgment(self):
        self.chain()
        def early(*args):
            result = self.runner(*args)
            result['answer']['unknowns'] = [unknown(related=['behavior'], blocked=['behavior'])]
            return result
        self.session.adopt(self.reviewed(runner=early))
        before = self.session.status()['unknowns']
        state = self.session.revise(['catalog'], 'Correct the catalog without resolving the open question')
        self.assertEqual(set(before), set(state['unknowns']))
        item = next(iter(state['unknowns'].values()))
        self.assertIsNone(item['decision'])
        self.assertEqual(next(iter(before.values()))['content'], item['content'])
        self.session.adopt(self.reviewed())
        self.assertEqual('needs-investigation', self.run_flow()['status'])

    def test_nonblocking_future_followup_is_delivered_to_the_later_stage(self):
        self.chain()
        def handoff(*args):
            context = json.loads(args[2][args[2].index('{"request":'):])
            result = self.runner(*args)
            if context['task']['operation'] == 'extract' and context['task']['stage'] == 'discovery':
                result['answer']['followups'] = [{'stage': 'behavior', 'requirement': 'behavior',
                    'paths': [self.session.source.paths[0]], 'question': 'Trace the exceptional result.'}]
            if context['task']['operation'] == 'extract' and context['task']['stage'] == 'behavior':
                self.assertEqual('Trace the exceptional result.', context['handoffQuestions'][0]['question'])
            return result
        self.assertEqual('complete', self.run_flow(runner=handoff)['status'])

    def test_unresolved_coverage_cannot_be_overridden_by_passing_verifier(self):
        def partial(*args):
            result = self.runner(*args)
            result['answer']['coverage'][0]['status'] = 'unresolved'
            return result
        candidate = self.execute('discovery', runner=partial)['id']
        self.verify(candidate)
        with self.assertRaisesRegex(AcceptanceError, 'unfinished'):
            self.session.adopt(candidate)

    def test_review_blocker_is_preserved_and_identical_run_does_not_spin(self):
        def reject(*args):
            result = self.runner(*args)
            if result['answer'].get('checks'):
                result['answer']['checks'][0]['status'] = 'fail'
                result['answer']['findings'] = [{'id': 'missing', 'severity': 'blocking',
                    'requirement': 'catalog', 'detail': 'A source entry is missing.', 'evidence': [self.evidence()]}]
            return result
        result = self.run_flow(runner=reject)
        self.assertEqual('needs-investigation', result['status'])
        self.assertEqual(0, result['session']['version'])
        calls = len(self.calls)
        again = self.run_flow(runner=reject)
        self.assertEqual(calls, len(self.calls))
        self.assertEqual(result['pending']['candidate'], again['pending']['candidate'])
        # Explicit feedback permits a fresh correction without changing the goal.
        corrected = self.execute('discovery', feedback=result['pending']['candidate'])['id']
        self.verify(corrected)
        self.assertEqual('complete', self.session.adopt(corrected)['status'])

    def test_upstream_followup_stops_behavior_and_keeps_original_obligations(self):
        self.chain()
        def missing(*args):
            result = self.runner(*args)
            if self.calls[-1][:2] == ('extract', 'behavior'):
                result['answer']['coverage'][0]['status'] = 'unresolved'
                result['answer']['followups'] = [{'stage': 'relationship', 'requirement': 'relations',
                    'paths': [self.session.source.paths[0]], 'question': 'Check a missing dispatch target.'}]
            return result
        result = self.run_flow(runner=missing)
        self.assertEqual('needs-investigation', result['status'])
        self.assertEqual('relationship', result['pending']['followups'][0]['stage'])
        self.assertEqual(['behavior'], result['session']['remainingRequirements'])
        self.session.revise(['relations'], 'Investigate the reported dispatch target')
        self.assertEqual(['relations', 'behavior'], self.session.status()['remainingRequirements'])
        def corrected(*args):
            result = self.runner(*args)
            result['answer']['records'][0]['statement'] += ' Dispatch target corrected from new source evidence.'
            return result
        candidate = self.execute('relationship', feedback=result['pending']['candidate'], runner=corrected)['id']
        self.verify(candidate)
        self.session.adopt(candidate)
        self.assertEqual('complete', self.run_flow()['status'])

    def test_supported_behavior_with_passing_verification_still_cannot_ignore_upstream_followup(self):
        self.chain()
        def missing(*args):
            result = self.runner(*args)
            if self.calls[-1][:2] == ('extract', 'behavior'):
                # Leave coverage supported and verifier checks pass to exercise
                # the host's upstream-followup gate rather than another guard.
                result['answer']['followups'] = [{'stage': 'relationship', 'requirement': 'relations',
                    'paths': [self.session.source.paths[0]], 'question': 'The adopted dispatch relation is wrong.'}]
            return result
        result = self.run_flow(runner=missing)
        self.assertEqual('needs-investigation', result['status'])
        self.assertEqual(['behavior'], result['session']['remainingRequirements'])
        self.assertEqual('relations', result['pending']['followups'][0]['requirement'])

    def test_completed_session_can_be_explicitly_revised_and_old_results_stay_in_history(self):
        self.chain()
        completed = self.run_flow()['session']
        old_revision = completed['revision']
        reopened = self.session.revise(['relations'], 'A relationship is wrong')
        self.assertEqual('active', reopened['status'])
        self.assertEqual(['relations', 'behavior'], reopened['remainingRequirements'])
        self.assertEqual(['catalog.record'], list(reopened['records']))
        history = self.session.store.get('revisions/' + old_revision + '.json')
        self.assertIn('behavior.record', history['records'])
        self.assertEqual('complete', self.run_flow()['status'])

    def test_unchanged_upstream_reverification_does_not_fake_new_investigation_progress(self):
        self.chain()
        def block(*args):
            result = self.runner(*args)
            if self.calls[-1][:2] == ('extract', 'behavior'):
                result['answer']['coverage'][0]['status'] = 'unresolved'
            return result
        self.assertEqual('needs-investigation', self.run_flow(runner=block)['status'])
        self.session.revise(['relations'], 'Recheck the same relationship')
        self.session.adopt(self.reviewed('relationship'))
        count = len(self.calls)
        self.assertEqual('needs-investigation', self.run_flow()['status'])
        self.assertEqual(count, len(self.calls))

    def test_revising_shared_catalog_invalidates_both_downstream_branches(self):
        self.configure([requirement('catalog'), requirement('left', 'relationship', ['catalog']),
                        requirement('right', 'relationship', ['catalog']),
                        requirement('left-beh', 'behavior', ['left']),
                        requirement('right-beh', 'behavior', ['right'])])
        self.run_flow()
        state = self.session.revise(['catalog'], 'Correct the shared entry catalog')
        self.assertEqual([], state['acceptedRequirements'])
        self.assertEqual({}, state['records'])
        self.assertEqual(5, len(state['invalidatedRequirements']))

    def test_replacing_adopted_upstream_candidate_invalidates_its_descendants_atomically(self):
        self.chain()
        self.run_flow(requirements=['relations'])
        def changed(*args):
            result = self.runner(*args)
            result['answer']['records'][0]['statement'] += ' corrected'
            return result
        candidate = self.execute('discovery', runner=changed)['id']
        self.verify(candidate)
        result = self.session.adopt(candidate)
        self.assertEqual(['catalog'], result['acceptedRequirements'])
        self.assertNotIn('relations.record', result['records'])
        self.assertIn('relations', result['invalidatedRequirements'])

    def test_record_owner_cannot_change_even_after_its_old_record_is_removed(self):
        self.chain()
        self.run_flow(requirements=['relations'])
        self.session.revise(['catalog'], 'Replace the catalog representation')
        def replacement(*args):
            result = self.runner(*args)
            result['answer']['records'][0]['key'] = 'new.catalog'
            result['answer']['coverage'][0]['recordKeys'] = ['new.catalog']
            return result
        self.session.adopt(self.reviewed(runner=replacement))
        def steal(*args):
            result = self.runner(*args)
            record = result['answer']['records'][0]
            record.update(key='catalog.record', kind='function', dependsOn=['new.catalog'])
            result['answer']['coverage'][0]['recordKeys'] = ['catalog.record']
            return result
        with self.assertRaisesRegex(ValueError, 'owner'):
            self.execute('relationship', runner=steal)

    def test_records_omitted_from_a_requirement_replacement_do_not_inherit_approval(self):
        candidate = self.reviewed()
        self.session.adopt(candidate)
        self.session.revise(['catalog'], 'The old item is no longer in the catalog')
        def empty(*args):
            result = self.runner(*args)
            result['answer']['records'] = []
            result['answer']['coverage'][0].update(status='not-applicable', recordKeys=[])
            return result
        self.session.adopt(self.reviewed(runner=empty))
        self.assertEqual({}, self.session.status()['records'])

    def test_multiple_local_record_dependencies_bind_versions_without_read_order_requirements(self):
        def local(*args):
            result = self.runner(*args)
            first = result['answer']['records'][0]
            second = {**deepcopy(first), 'key': 'catalog.second', 'dependsOn': [first['key']]}
            result['answer']['records'].append(second)
            result['answer']['coverage'][0]['recordKeys'].append(second['key'])
            return result
        candidate = self.reviewed(runner=local)
        records = self.session.adopt(candidate)['records']
        self.assertEqual(records['catalog.record']['version'],
                         records['catalog.second']['dependencies'][0]['version'])

    def test_verification_view_tampering_is_rejected_without_publishing(self):
        candidate = self.reviewed()
        payload = self.session.store.get('candidates/' + candidate + '.json')
        self.assertEqual(payload['viewSha256'], contracts.digest(payload['view']))
        # A verifier cannot substitute another view hash in its result.
        def forged(*args):
            result = self.runner(*args)
            result['answer']['viewSha256'] = '0' * 64
            return result
        with self.assertRaisesRegex(ValueError, 'contract'):
            self.verify(candidate, runner=forged)
        self.assertEqual(0, self.session.status()['version'])

    def test_stale_verification_and_competing_candidates_cannot_overwrite(self):
        self.chain()
        first = self.reviewed()
        other = self.reviewed()
        self.session.adopt(first)
        with self.assertRaisesRegex(ValueError, 'base version'):
            self.session.adopt(other)
        fresh = self.execute('relationship')['id']
        with self.assertRaisesRegex(AcceptanceError, 'verification'):
            self.session.adopt(fresh)

    def test_atomic_pointer_failure_and_mid_revision_write_both_allow_retry(self):
        for phase in ('pointer', 'body'):
            with self.subTest(phase=phase):
                if phase == 'body':
                    self.session = Session.create(self.source, self.root / 'body-work', self.request)
                candidate = self.reviewed()
                original_save, original_dump = ArtifactStore.save_state, json.dump
                def save(store, state):
                    if state['version'] == 1:
                        raise OSError('pointer interruption')
                    return original_save(store, state)
                def dump(value, handle, **kwargs):
                    if '/revisions/' in str(handle.name).replace('\\', '/'):
                        handle.write('{"partial":')
                        raise OSError('body interruption')
                    return original_dump(value, handle, **kwargs)
                target = patch.object(ArtifactStore, 'save_state', save) if phase == 'pointer' else patch(
                    'contextbase.analysis.storage.json.dump', side_effect=dump)
                with target:
                    with self.assertRaises(OSError):
                        self.session.adopt(candidate)
                self.assertEqual(0, self.session.status()['version'])
                self.assertEqual('complete', self.session.adopt(candidate)['status'])

    def test_late_return_after_cancel_resume_or_revision_cannot_change_new_execution(self):
        for action in ('cancel', 'revise'):
            with self.subTest(action=action):
                if action == 'revise':
                    self.chain()
                    self.session.adopt(self.reviewed())
                def late(*args):
                    result = self.runner(*args)
                    if action == 'revise':
                        self.session.revise(['catalog'], 'Upstream correction during extraction')
                    else:
                        self.session.cancel()
                        self.session.resume(self.request)
                    return result
                with self.assertRaisesRegex(ValueError, 'finished|issued'):
                    self.execute('relationship' if action == 'revise' else 'discovery', runner=late)
                self.assertEqual('active', self.session.status()['status'])
                self.assertIn(self.execute('discovery')['id'], self.session.status()['candidates'])

    def test_failed_provider_keeps_raw_response_and_can_resume(self):
        def failed(*args):
            return {'answer': None, 'exit_code': 1, 'metadata': {'status': 'cli_failed'}}
        with self.assertRaises(RuntimeError):
            self.execute('discovery', runner=failed)
        self.assertEqual('stopped', self.session.status()['status'])
        self.assertTrue(list((self.session.store.root / 'tasks').glob('*/transport.json')))
        self.assertEqual('active', self.session.resume(self.request)['status'])

    def test_resume_rejects_goal_snapshot_or_engine_changes(self):
        self.session.cancel()
        changed = deepcopy(self.request)
        changed['goal']['question'] = 'A different goal'
        with self.assertRaisesRegex(ValueError, 'original'):
            self.session.resume(changed)
        with patch('contextbase.analysis.controller.engine_fingerprint', return_value='changed'):
            with self.assertRaisesRegex(ValueError, 'rules or dependencies'):
                self.session.resume(self.request)
        (self.session.source.root / 'sources' / 'Orders.cs').write_text('tampered', encoding='utf-8')
        with self.assertRaises(ValueError):
            self.session.resume(self.request)

    def test_v1_sessions_are_not_silently_migrated_or_modified(self):
        store = ArtifactStore(self.root / 'legacy')
        store.root.mkdir()
        store.put('session.json', {'schema': 'contextbase-analysis/1'})
        original = store.path('session.json').read_bytes()
        with self.assertRaisesRegex(ValueError, 'cannot be auto-migrated'):
            Session.open(store.root)
        self.assertEqual(original, store.path('session.json').read_bytes())

    def test_inline_originals_preserve_delimiters_for_both_fresh_contexts(self):
        original = 'class Orders {\r\n const string Value = "a\u2028b";\r\n}\r\n'
        (self.source / 'Orders.cs').write_bytes(original.encode('utf-8'))
        self.session = Session.create(self.source, self.root / 'inline', self.request)
        deliveries = []
        def inspect(*args):
            context = json.loads(args[2][args[2].index('{"request":'):])
            deliveries.append(context['sourceDelivery'])
            self.assertEqual(original, deliveries[-1]['files'][0]['sourceText'])
            return self.runner(*args)
        candidate = self.execute('discovery', runner=inspect, inline_sources=True)['id']
        self.verify(candidate, runner=inspect, inline_sources=True)
        self.assertEqual(deliveries[0], deliveries[1])
        self.assertEqual('complete', self.session.adopt(candidate)['status'])

    def test_inline_limit_and_finite_per_operation_timeout(self):
        for timeout in (0, -1, True, float('nan')):
            with self.assertRaises(ValueError):
                self.execute('discovery', timeout=timeout)
        (self.source / 'Orders.cs').write_bytes(b'// source\n' + b' ' * 1_048_576)
        self.session = Session.create(self.source, self.root / 'large', self.request)
        with patch('contextbase.ai.provider.run_job') as provider:
            with self.assertRaisesRegex(ValueError, 'exceeds 1 MiB'):
                self.session.execute('discovery', inline_sources=True)
            provider.assert_not_called()

    def test_java_and_csharp_share_the_same_workflow_without_executing_inputs(self):
        for language in ('csharp', 'java'):
            with self.subTest(language=language):
                if language == 'java':
                    self.configure([requirement('catalog'), requirement('relations', 'relationship', ['catalog']),
                                    requirement('behavior', 'behavior', ['relations'])], language='java')
                else:
                    self.chain()
                before = {p.name: p.read_bytes() for p in self.source.iterdir()}
                self.assertEqual('complete', self.run_flow()['status'])
                self.assertEqual(before, {p.name: p.read_bytes() for p in self.source.iterdir()})


if __name__ == '__main__':
    unittest.main()
