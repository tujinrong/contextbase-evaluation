"""A schema-only review upgrade replays, but never replaces, the frozen author."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

import test_incremental_agents as fixtures
from contextbase_discovery import DiscoveryAgent
from contextbase_runtime import checkpoint_upgrade as upgrade, contracts, controller


class FrozenReviewUpgradeTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.IncrementalAgentTests(methodName='runTest')
        self.fixture.setUp()
        self.agent = self.fixture.create()
        self.fixture.fail_once = ('review', 'records-0000')
        with self.assertRaisesRegex(RuntimeError, 'provider failed'):
            self.fixture.run_agent(self.agent)
        self.work, self.store = self.agent.work, self.agent.session.store
        self.request = deepcopy(self.agent.session.config['request'])
        config = self.store.get('session.json')
        self.old_engine, self.new_engine = config['engineSha256'], 'f' * 64
        self.identifier = self.store.get('state.json')['candidates'][0]
        self.previous = self.fixture.root / 'previous-runtime'
        self.previous.mkdir()
        for path in Path(controller.__file__).parent.glob('*.py'):
            shutil.copyfile(path, self.previous / path.name)
        # Reconstruct a sealed predecessor commit followed by this failed run.
        state = self.store.get('state.json')
        old_config = {**config, 'engineSha256': 'a' * 64}
        old_state = {**deepcopy(state), 'sessionSha256': contracts.digest(old_config)}
        audit = {'schema': upgrade.VERSION, 'reason': 'obligation-closure-package',
                 'oldSession': old_config, 'oldState': old_state,
                 'oldEngineSha256': old_config['engineSha256'], 'newEngineSha256': self.old_engine}
        self.prior = contracts.digest(audit)
        config = {**config, 'runtimeUpgrade': self.prior}
        committed_state = {**deepcopy(old_state), 'sessionSha256': contracts.digest(config),
                           'executionEpoch': old_state['executionEpoch'] + 1}
        self.store.put('runtime-upgrades/' + self.prior + '.json', audit)
        self.store.put('runtime-upgrades/' + self.prior + '-committed.json', {
            'schema': upgrade.VERSION, 'auditSha256': self.prior,
            'sessionSha256': contracts.digest(config), 'stateSha256': contracts.digest(committed_state)})
        self.store.put('runtime-upgrades/closure-pending.json', {'schema': upgrade.VERSION,
                                                              'auditSha256': self.prior})
        upgrade._replace_session(self.store, config)
        self.store.save_state(committed_state)
        self.before = {p.relative_to(self.work).as_posix(): p.read_bytes()
                       for p in self.work.rglob('*') if p.is_file()}

    def tearDown(self):
        self.fixture.tearDown()

    def execute(self, **options):
        arguments = dict(previous_audit_sha256=self.prior, frozen_candidate=self.identifier)
        arguments.update(options)
        with patch.object(upgrade, 'REVIEW_SOURCE_ENGINE_SHA256', self.old_engine), \
                patch.object(upgrade, 'REVIEW_TARGET_ENGINE_SHA256', self.new_engine), \
                patch.object(controller, 'engine_fingerprint', return_value=self.new_engine):
            return upgrade.upgrade(self.work, self.previous, self.request, DiscoveryAgent, **arguments)

    def test_migration_preserves_candidate_author_history_and_resumes_review_only(self):
        DiscoveryAgent(self.work).session.cancel('Synthetic host stop before review schema maintenance.')
        result = self.execute()
        self.assertEqual('upgraded', result['status'])
        self.assertEqual(4, result['proof']['completedCalls'])
        self.assertEqual({'plan': 1, 'draft': 2, 'closure': 1}, result['proof']['authorPhases'])
        for name, data in self.before.items():
            if name not in {'session.json', 'state.json'}:
                self.assertEqual(data, self.store.path(name).read_bytes(), name)
        candidate_path = 'candidates/' + self.identifier + '.json'
        self.assertEqual(hashlib.sha256(self.before[candidate_path]).hexdigest(),
                         result['proof']['candidateFileSha256'])
        self.fixture.calls.clear()
        with patch.object(controller, 'engine_fingerprint', return_value=self.new_engine):
            agent = DiscoveryAgent(self.work)
            self.fixture.agents[agent.session.source.root] = agent
            agent.session.resume(self.request)
            self.assertEqual('complete', self.fixture.run_agent(agent)['status'])
        self.assertTrue(self.fixture.calls)
        self.assertEqual({'review'}, {row['incremental']['phase'] for row in self.fixture.calls})

    def test_dry_run_has_no_mutation_and_commit_is_idempotent(self):
        dry = self.execute(dry_run=True)
        for name, data in self.before.items():
            self.assertEqual(data, self.store.path(name).read_bytes(), name)
        actual = self.execute()
        self.assertEqual(dry['auditSha256'], actual['auditSha256'])
        self.assertEqual('already-upgraded', self.execute()['status'])

    def test_audit_ignores_ephemeral_lock_owner_across_processes(self):
        with patch('contextbase_runtime.storage.os.getpid', return_value=100):
            dry = self.execute(dry_run=True)
        with patch('contextbase_runtime.storage.os.getpid', return_value=200):
            actual = self.execute()
        self.assertEqual(dry['auditSha256'], actual['auditSha256'])
        self.assertNotIn('session.lock', actual['proof']['files'])

    def test_candidate_pin_is_required_to_select_this_compatibility_mode(self):
        with self.assertRaises(ValueError):
            self.execute(frozen_candidate='0' * 64)
        with self.assertRaises(ValueError):
            self.execute(frozen_candidate=None)

    def test_previous_upgrade_must_be_pinned(self):
        with self.assertRaisesRegex(ValueError, 'previous audit'):
            self.execute(previous_audit_sha256=None)
        with self.assertRaisesRegex(ValueError, 'previous audit'):
            self.execute(previous_audit_sha256='0' * 64)

    def test_existing_successful_review_slices_are_not_reused(self):
        for path in self.work.glob('workflows/*/state.json'):
            relative = path.relative_to(self.work).as_posix()
            state = self.store.get(relative)
            if state['basis']['operation'] == 'verify':
                state['trace'] = ['forbidden-successful-review']
                self.store.path(relative).write_text(json.dumps(
                    {'payload': state, 'sha256': contracts.digest(state)}), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'uncompleted reviews'):
            self.execute()

    def test_modified_candidate_cannot_be_resealed_under_old_identifier(self):
        path = 'candidates/' + self.identifier + '.json'
        candidate = self.store.get(path)
        candidate['answer']['records'][0]['statement'] += ' altered'
        self.store.path(path).write_text(json.dumps(
            {'payload': candidate, 'sha256': contracts.digest(candidate)}), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Frozen candidate'):
            self.execute()


if __name__ == '__main__':
    unittest.main()
