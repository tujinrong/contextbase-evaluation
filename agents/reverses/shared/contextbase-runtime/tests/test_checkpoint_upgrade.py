"""Explicit compatible upgrades preserve author checkpoints, never acceptance."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

import test_incremental_agents as fixtures
from contextbase_discovery import DiscoveryAgent
from contextbase_runtime import checkpoint_upgrade as upgrade, contracts, controller


class CheckpointUpgradeTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.IncrementalAgentTests(methodName='runTest')
        self.fixture.setUp()
        self.agent = self.fixture.create()
        self.fixture.fail_once = ('draft', 'function-unit')
        with self.assertRaisesRegex(RuntimeError, 'provider failed'):
            self.fixture.run_agent(self.agent)
        self.assertEqual('stopped', self.agent.status()['status'])
        self.work = self.agent.work
        self.store = self.agent.session.store
        self.request = deepcopy(self.agent.session.config['request'])
        self.old_engine = self.agent.session.config['engineSha256']
        self.new_engine = 'f' * 64
        self.before = self.store.get('state.json')
        self.previous = self.fixture.root / 'previous-runtime'
        self.previous.mkdir()
        runtime = Path(controller.__file__).parent
        for file in runtime.glob('*.py'):
            shutil.copyfile(file, self.previous / file.name)
        self.legacy_bytes = {p.relative_to(self.work).as_posix(): p.read_bytes()
                             for p in self.work.rglob('*.json')
                             if p.name not in {'state.json', 'session.json'}}

    def tearDown(self):
        self.fixture.tearDown()

    def execute(self, previous_audit=None):
        with patch.object(upgrade, 'SUPPORTED_ENGINE_SHA256', self.old_engine), \
                patch.object(upgrade, 'SUPPORTED_TARGET_ENGINE_SHA256', self.new_engine), \
                patch.object(controller, 'engine_fingerprint', return_value=self.new_engine):
            options = {'previous_audit_sha256': previous_audit} if previous_audit is not None else {}
            return upgrade.upgrade(self.work, self.previous, self.request, DiscoveryAgent, **options)

    def rewrite(self, relative, mutate):
        value = self.store.get(relative)
        mutate(value)
        self.store.path(relative).write_text(json.dumps(
            {'payload': value, 'sha256': contracts.digest(value)}), encoding='utf-8')

    def predecessor(self):
        """A sealed synthetic prior upgrade, followed by the present stopped run."""
        config = self.store.get('session.json')
        old_config = {**deepcopy(config), 'engineSha256': 'a' * 64}
        old_state = {**deepcopy(self.before), 'sessionSha256': contracts.digest(old_config)}
        audit = {'schema': upgrade.VERSION, 'reason': 'directory-query-and-request-recovery',
                 'oldSession': old_config, 'oldState': old_state,
                 'oldEngineSha256': old_config['engineSha256'], 'newEngineSha256': self.old_engine,
                 'proof': {'fixture': True}}
        identifier = contracts.digest(audit)
        config = {**config, 'runtimeUpgrade': identifier}
        state = {**deepcopy(old_state), 'sessionSha256': contracts.digest(config),
                 'executionEpoch': old_state['executionEpoch'] + 1}
        self.store.put('runtime-upgrades/' + identifier + '.json', audit)
        self.store.put('runtime-upgrades/' + identifier + '-committed.json', {
            'schema': upgrade.VERSION, 'auditSha256': identifier,
            'sessionSha256': contracts.digest(config), 'stateSha256': contracts.digest(state)})
        self.store.put('runtime-upgrades/pending.json', {'schema': upgrade.VERSION,
                                                       'auditSha256': identifier})
        self.rewrite('session.json', lambda value: value.update(config))
        self.store.save_state(state)
        self.before = state
        return identifier

    def test_chained_upgrade_pins_and_preserves_predecessor_and_old_calls(self):
        previous = self.predecessor()
        previous_bytes = self.store.path('runtime-upgrades/' + previous + '.json').read_bytes()
        legacy_pending = self.store.path('runtime-upgrades/pending.json').read_bytes()
        result = self.execute(previous)
        self.assertEqual('upgraded', result['status'])
        self.assertEqual(2, self.store.get('state.json')['executionEpoch'])
        audit = self.store.get('runtime-upgrades/' + result['auditSha256'] + '.json')
        self.assertEqual(previous, audit['previousAuditSha256'])
        self.assertEqual(previous_bytes, self.store.path('runtime-upgrades/' + previous + '.json').read_bytes())
        self.assertEqual(legacy_pending, self.store.path('runtime-upgrades/pending.json').read_bytes())
        for name, content in self.legacy_bytes.items():
            self.assertEqual(content, self.store.path(name).read_bytes(), name)
        self.assertEqual('already-upgraded', self.execute(previous)['status'])

    def test_chained_upgrade_requires_explicit_matching_previous_audit(self):
        self.predecessor()
        config, state = self.store.path('session.json').read_bytes(), self.store.path('state.json').read_bytes()
        with self.assertRaisesRegex(ValueError, 'previous audit'):
            self.execute()
        with self.assertRaisesRegex(ValueError, 'previous audit'):
            self.execute('b' * 64)
        self.assertEqual(config, self.store.path('session.json').read_bytes())
        self.assertEqual(state, self.store.path('state.json').read_bytes())

    def test_chained_upgrade_rejects_damaged_predecessor_commit(self):
        previous = self.predecessor()
        self.rewrite('runtime-upgrades/' + previous + '-committed.json',
                     lambda value: value.update(sessionSha256='0' * 64))
        with self.assertRaisesRegex(ValueError, 'previous audit'):
            self.execute(previous)

    def test_previous_audit_pin_cannot_be_ignored_for_an_unmigrated_session(self):
        with self.assertRaisesRegex(ValueError, 'previous audit'):
            self.execute('b' * 64)

    def test_upgrade_replays_drafts_and_resumes_without_reextracting_completed_unit(self):
        with patch.object(controller, 'engine_fingerprint', return_value=self.new_engine):
            with self.assertRaisesRegex(ValueError, 'rules or dependencies changed'):
                DiscoveryAgent(self.work)
        result = self.execute()
        self.assertEqual('upgraded', result['status'])
        self.assertEqual(1, result['proof']['draftRecordCount'])
        self.assertEqual(2, result['proof']['completedCalls'])
        self.assertEqual(self.before['executionEpoch'] + 1, self.store.get('state.json')['executionEpoch'])
        self.assertEqual([], self.store.get('state.json')['acceptedRequirements'])
        for name, content in self.legacy_bytes.items():
            self.assertEqual(content, self.store.path(name).read_bytes(), name)
        self.fixture.calls.clear()
        with patch.object(controller, 'engine_fingerprint', return_value=self.new_engine):
            agent = DiscoveryAgent(self.work)
            self.fixture.agents[agent.session.source.root] = agent
            agent.session.resume(self.request)
            self.assertEqual('complete', self.fixture.run_agent(agent)['status'])
        phases = self.fixture.phase_counts()
        self.assertEqual(0, phases[('plan', None)])
        self.assertEqual(0, phases[('draft', 'entry-unit')])
        self.assertGreater(phases[('draft', 'function-unit')], 0)

    def test_repeated_upgrade_is_idempotent_before_resuming(self):
        first = self.execute()
        second = self.execute()
        self.assertEqual('already-upgraded', second['status'])
        self.assertEqual(first['auditSha256'], second['auditSha256'])
        self.assertEqual(self.before['executionEpoch'] + 1, self.store.get('state.json')['executionEpoch'])

    def test_dry_run_validates_without_activating_or_persisting_upgrade(self):
        config = self.store.path('session.json').read_bytes()
        state = self.store.path('state.json').read_bytes()
        with patch.object(upgrade, 'SUPPORTED_ENGINE_SHA256', self.old_engine), \
                patch.object(upgrade, 'SUPPORTED_TARGET_ENGINE_SHA256', self.new_engine), \
                patch.object(controller, 'engine_fingerprint', return_value=self.new_engine):
            result = upgrade.upgrade(self.work, self.previous, self.request, DiscoveryAgent, dry_run=True)
        self.assertEqual('compatible', result['status'])
        self.assertEqual(config, self.store.path('session.json').read_bytes())
        self.assertEqual(state, self.store.path('state.json').read_bytes())
        self.assertFalse(self.store.path('runtime-upgrades').exists())

    def test_changed_request_is_refused_without_workspace_mutation(self):
        self.request['goal']['question'] += ' changed'
        before = self.store.path('state.json').read_bytes()
        with self.assertRaisesRegex(ValueError, 'request'):
            self.execute()
        self.assertEqual(before, self.store.path('state.json').read_bytes())
        self.assertFalse(self.store.path('runtime-upgrades').exists())

    def test_unsupported_old_engine_is_refused(self):
        with patch.object(controller, 'engine_fingerprint', return_value=self.new_engine):
            with self.assertRaisesRegex(ValueError, 'supported prior engine'):
                upgrade.upgrade(self.work, self.previous, self.request, DiscoveryAgent)

    def test_unsupported_target_engine_is_refused_without_workspace_mutation(self):
        config = self.store.path('session.json').read_bytes()
        state = self.store.path('state.json').read_bytes()
        with patch.object(upgrade, 'SUPPORTED_ENGINE_SHA256', self.old_engine), \
                patch.object(controller, 'engine_fingerprint', return_value=self.new_engine):
            with self.assertRaisesRegex(ValueError, 'supported target engine'):
                upgrade.upgrade(self.work, self.previous, self.request, DiscoveryAgent)
        self.assertEqual(config, self.store.path('session.json').read_bytes())
        self.assertEqual(state, self.store.path('state.json').read_bytes())
        self.assertFalse(self.store.path('runtime-upgrades').exists())

    def test_changed_previous_runtime_is_refused(self):
        with (self.previous / 'controller.py').open('a', encoding='utf-8') as stream:
            stream.write('\n# altered historical code\n')
        with self.assertRaisesRegex(ValueError, 'previous runtime'):
            self.execute()

    def test_changed_dependency_version_is_refused(self):
        with patch.object(upgrade.importlib.metadata, 'version', return_value='changed'):
            with self.assertRaisesRegex(ValueError, 'previous runtime'):
                self.execute()

    def test_issued_task_or_candidate_blocks_upgrade(self):
        for field, value in [('tasks', {'late-task': 'issued'}), ('candidates', ['unverified'])]:
            with self.subTest(field=field):
                original = self.store.get('state.json')
                altered = deepcopy(original)
                altered[field] = value
                self.store.save_state(altered)
                with self.assertRaisesRegex(ValueError, 'stopped, unadopted'):
                    self.execute()
                self.store.save_state(original)

    def test_changed_original_source_inventory_blocks_upgrade(self):
        (self.fixture.source / 'Added.cs').write_text('class Added {}', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'source inventory'):
            self.execute()

    def test_changed_agent_binding_blocks_upgrade(self):
        self.rewrite('agent.json', lambda value: value.update(implementationSha256='0' * 64))
        with self.assertRaisesRegex(ValueError, 'Agent implementation'):
            self.execute()

    def test_resealed_changed_trace_record_cannot_pass_historical_replay(self):
        workflow = next((self.work / 'workflows').glob('*/state.json'))
        checkpoint = json.loads(workflow.read_text(encoding='utf-8'))['payload']
        call = workflow.parent / 'calls' / checkpoint['trace'][-1]
        complete = json.loads((call / 'complete.json').read_text(encoding='utf-8'))['payload']
        relative = (call / f"round-{len(complete['rounds']):04d}.json").relative_to(self.work).as_posix()
        self.rewrite(relative, lambda value: value['response']['answer']['answer']['records'][0].update(
            statement='A changed claim hidden under a fresh artifact seal'))
        with self.assertRaisesRegex(ValueError, 'trace|response|replay'):
            self.execute()
        self.assertFalse(self.store.path('runtime-upgrades').exists())

    def test_interrupt_between_config_and_state_is_fail_closed_and_recoverable(self):
        original_replace = upgrade._replace_session
        def interrupt(store, config):
            original_replace(store, config)
            raise RuntimeError('synthetic crash after config replace')
        with patch.object(upgrade, '_replace_session', side_effect=interrupt):
            with self.assertRaisesRegex(RuntimeError, 'synthetic crash'):
                self.execute()
        with patch.object(controller, 'engine_fingerprint', return_value=self.new_engine):
            with self.assertRaisesRegex(ValueError, 'contract changed'):
                DiscoveryAgent(self.work)
        recovered = self.execute()
        self.assertEqual('upgraded', recovered['status'])
        self.assertEqual(self.before['executionEpoch'] + 1, self.store.get('state.json')['executionEpoch'])

    def test_interrupted_upgrade_refuses_unexpected_state_change(self):
        with patch.object(upgrade, '_replace_session', side_effect=RuntimeError('synthetic crash')):
            with self.assertRaises(RuntimeError):
                self.execute()
        self.rewrite('state.json', lambda value: value.update(stopReason='another writer changed state'))
        with self.assertRaisesRegex(ValueError, 'interrupted upgrade'):
            self.execute()


if __name__ == '__main__':
    unittest.main()
