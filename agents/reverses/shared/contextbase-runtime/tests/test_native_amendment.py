"""Source-validated, untrusted native imports; no model or old runtime runs."""
from copy import deepcopy
import json
import unittest
from unittest.mock import patch

from contextbase_runtime import contracts as c, native_amendment, candidate_amendment
from contextbase_runtime.project_analysis import ProjectAnalysisAgent
import test_project_analysis as fixture_module


class NativeAmendmentTests(unittest.TestCase):
    provider = fixture_module.ProjectAnalysisTests.provider
    run_native = fixture_module.ProjectAnalysisTests.run_native

    def setUp(self):
        fixture_module.ProjectAnalysisTests.setUp(self)
        original = fixture_module.simulated_answer
        def fail_review(context):
            answer = original(context)
            ref = self.agent.session.source.evidence('Registration.cs', 1, 3)
            answer['findings'] = [{'id': 'review-finding', 'severity': 'blocking',
                'requirement': 'rules', 'detail': 'Reconcile one source interpretation', 'evidence': [ref]}]
            return answer
        with patch.object(fixture_module, 'simulated_answer', side_effect=fail_review):
            result = self.run_native()
        self.assertEqual('needs-investigation', result['status'])
        self.origin = self.agent
        state = self.origin.session._state()
        self.candidate = state['candidates'][-1]
        self.verification = state['verifications'][-1]
        self.agent = ProjectAnalysisAgent.create(self.source, self.root / 'fresh', fixture_module.request())

    def install(self, **kwargs):
        return native_amendment.install(self.agent, self.origin.work, self.candidate,
            self.verification, replace_keys=['rules.record'], **kwargs)

    def rewrite(self, store, name, payload):
        store.path(name).write_text(json.dumps({'sha256': c.digest(payload), 'payload': payload}), encoding='utf-8')

    def test_import_keeps_untrusted_claims_and_all_findings_without_acceptance(self):
        before = deepcopy(self.agent.session._state())
        seed, spec = self.install()
        self.assertEqual(candidate_amendment.NATIVE_VERSION, spec['schema'])
        self.assertEqual([], spec['addKinds'])
        self.assertEqual(['rules.record'], spec['replaceKeys'])
        self.assertEqual('untrusted-source-validated-data', seed['custody']['trust'])
        self.assertEqual('review-finding', seed['priorFindings'][0]['id'])
        self.assertEqual(before, self.agent.session._state())
        self.assertEqual((seed, spec), native_amendment.installed(self.agent.session))
        self.assertFalse(self.agent.session.store.path('tasks').exists())

    def test_cross_engine_is_data_and_installed_does_not_reopen_old_work(self):
        config = deepcopy(self.origin.session.config)
        config['engineSha256'] = '0' * 64
        self.rewrite(self.origin.session.store, 'session.json', config)
        state = self.origin.session.store.get('state.json')
        state['sessionSha256'] = c.digest(config)
        self.origin.session.store.save_state(state)
        seed, _ = self.install()
        self.assertEqual('0' * 64, seed['custody']['engineSha256'])
        with patch.object(native_amendment, 'ArtifactStore', side_effect=AssertionError('origin reopened')):
            self.assertEqual(seed, native_amendment.installed(self.agent.session)[0])

    def test_bad_selection_and_nonfresh_work_fail_before_install(self):
        with self.assertRaises(ValueError):
            self.install(finding_ids=['not-a-finding'])
        self.assertFalse(self.agent.session.store.path('amendment-seed.json').exists())
        state = self.agent.session._state()
        state['attempts']['prior'] = {'reason': 'already used'}
        self.agent.session.store.save_state(state)
        with self.assertRaisesRegex(ValueError, 'fresh'):
            self.install()

    def test_corrupt_artifact_or_view_is_rejected(self):
        artifact = self.origin.session.store.get('candidates/' + self.candidate + '.json')
        artifact['view']['acceptedRequirements'] = []
        self.rewrite(self.origin.session.store, 'candidates/' + self.candidate + '.json', artifact)
        with self.assertRaisesRegex(ValueError, 'content-address'):
            self.install()

    def test_changed_current_roles_request_source_and_seed_bindings_fail(self):
        seed, spec = self.install()
        original_roles = deepcopy(self.agent.session.config.get('roleSpecs'))
        self.agent.session.config['roleSpecs'] = {'changed': True}
        with self.assertRaisesRegex(ValueError, 'current source/index/request/runtime'):
            native_amendment.installed(self.agent.session)
        if original_roles is None:
            self.agent.session.config.pop('roleSpecs')
        else:
            self.agent.session.config['roleSpecs'] = original_roles
        original_request = deepcopy(self.agent.session.config['request'])
        self.agent.session.config['request']['projectId'] = 'different-project'
        with self.assertRaisesRegex(ValueError, 'current source/index/request/runtime'):
            native_amendment.installed(self.agent.session)
        self.agent.session.config['request'] = original_request
        with patch('contextbase_runtime.controller.engine_fingerprint', return_value='0' * 64):
            with self.assertRaisesRegex(ValueError, 'current source/index/request/runtime'):
                native_amendment.installed(self.agent.session)
        changed = deepcopy(spec)
        changed['seedSha256'] = '0' * 64
        self.rewrite(self.agent.session.store, 'amendment-spec.json', changed)
        with self.assertRaisesRegex(ValueError, 'seed content'):
            native_amendment.installed(self.agent.session)

    def test_sealed_source_mutation_rejected_without_imported_delivery(self):
        self.install()
        snapshot = self.agent.session.source.root / 'Registration.cs'
        snapshot.write_text('changed source', encoding='utf-8')
        with self.assertRaises(ValueError):
            native_amendment.installed(self.agent.session)

    def test_review_must_match_candidate_even_when_artifact_resealed(self):
        store = self.origin.session.store
        artifact = store.get('verifications/' + self.verification + '.json')
        artifact['candidate'] = '0' * 64
        identifier = c.digest(artifact)
        store.put('verifications/' + identifier + '.json', artifact)
        state = store.get('state.json')
        state['verifications'].append(identifier)
        store.save_state(state)
        self.verification = identifier
        with self.assertRaises(ValueError):
            self.install()


if __name__ == '__main__':
    unittest.main()
