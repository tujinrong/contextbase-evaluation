"""The public launcher preserves old work and selects one explicit amendment."""
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from contextbase_discovery import DiscoveryAgent, launch
from contextbase_runtime import contracts
from contextbase_runtime.config import ProjectProfile
import test_amendment_seed as seed_fixture
import test_amendment_runtime as runtime_fixture


class AmendmentLaunchTests(unittest.TestCase):
    def setUp(self):
        self.fixture = seed_fixture.AmendmentSeedTests('test_load_rebuilds_author_chain_and_preserves_inherited_followup')
        self.fixture.setUp()
        self.root = self.fixture.root
        (self.root / 'request.json').write_text(json.dumps(
            self.fixture.agent.session.config['request']), encoding='utf-8')
        self.config = self.root / 'contextbase.toml'
        self.config.write_text('schema="contextbase-project/1"\ndefault_profile="sample"\n'
            '[profiles.sample]\nsource="source"\nrequest="request.json"\n'
            'output="results"\nwork="launch-work"\ncontext_mode="incremental"\n', encoding='utf-8')
        self.profile = ProjectProfile.load(self.config)
        self.options = {'amend_bundle': self.fixture.bundle,
                        'amend_verification': self.fixture.verification_id,
                        'add_kinds': ['material']}

    def tearDown(self):
        self.fixture.tearDown()

    def start(self, **options):
        with patch.object(DiscoveryAgent, 'run', return_value={
                'status': 'needs-investigation', 'actions': []}) as run:
            result = launch.start(self.config, emit=lambda _: None, **options)
        return result, run

    def test_next_click_resumes_selected_amendment_and_keeps_original_work(self):
        old, _ = self.start()
        old_work = Path(old['work'])
        sentinel = old_work / 'preserved-input.json'
        sentinel.write_bytes(b'old workspace must survive')
        first, _ = self.start(**self.options)
        self.assertNotEqual(old['work'], first['work'])
        work = Path(first['work'])
        self.assertEqual('amendment-current', work.parent.name)
        seeded = DiscoveryAgent(work).session.store.get('amendment-seed.json')
        self.assertEqual(self.fixture.candidate['id'], seeded['baseCandidateSha256'])
        again, run = self.start()
        self.assertEqual(first['work'], again['work'])
        self.assertEqual(b'old workspace must survive', sentinel.read_bytes())
        run.assert_called_once()
        self.assertFalse(first['published'])
        self.assertFalse(self.profile.work('relationship-agent').exists())
        self.assertFalse(self.profile.work('behavior-agent').exists())

    def test_source_change_cannot_be_hidden_by_fresh_and_preserves_old_and_new_work(self):
        first, _ = self.start(**self.options)
        work = Path(first['work'])
        before = (work / 'amendment-seed.json').read_bytes()
        (self.root / 'source' / 'Added.cs').write_text('class Added {}\n', encoding='utf-8')
        with patch.object(DiscoveryAgent, 'run') as run:
            with self.assertRaisesRegex(ValueError, 'source inventory|contents changed'):
                launch.start(self.config, fresh=True, emit=lambda _: None)
        run.assert_not_called()
        self.assertEqual(before, (work / 'amendment-seed.json').read_bytes())

    def test_changed_seed_scope_or_custody_is_rejected_before_cleaning(self):
        first, _ = self.start(**self.options)
        work = Path(first['work'])
        before = (work / 'amendment-seed.json').read_bytes()
        with patch.object(DiscoveryAgent, 'run') as run:
            with self.assertRaisesRegex(ValueError, 'operation changed'):
                launch.start(self.config, **{**self.options, 'replace_keys': ['material']}, emit=lambda _: None)
        run.assert_not_called()
        self.assertEqual(before, (work / 'amendment-seed.json').read_bytes())
        manifest = self.fixture.bundle / 'custody.json'
        content = json.loads(manifest.read_text(encoding='utf-8'))
        one = next(iter(content['files']))
        (self.fixture.bundle / one).write_bytes(b'changed input')
        with self.assertRaises(ValueError):
            self.start(fresh=True)
        self.assertEqual(before, (work / 'amendment-seed.json').read_bytes())

    def test_fresh_discards_only_new_execution_state_and_retains_the_input_bundle(self):
        old, _ = self.start()
        sentinel = Path(old['work']) / 'preserve.txt'
        sentinel.write_bytes(b'old')
        first, _ = self.start(**self.options)
        work = Path(first['work'])
        (work / 'discard.txt').write_bytes(b'new execution state')
        original = (self.fixture.bundle / 'custody.json').read_bytes()
        renewed, _ = self.start(fresh=True)
        self.assertEqual(first['work'], renewed['work'])
        self.assertFalse((work / 'discard.txt').exists())
        self.assertEqual(b'old', sentinel.read_bytes())
        self.assertEqual(original, (self.fixture.bundle / 'custody.json').read_bytes())

    def test_failed_installation_keeps_selected_operation_for_the_next_click(self):
        from contextbase_runtime import amendment_seed
        with patch.object(amendment_seed, 'install', side_effect=OSError('Synthetic disk failure.')):
            with self.assertRaisesRegex(OSError, 'Synthetic disk failure'):
                self.start(**self.options)
        selected = self.profile.work_root / 'discovery-agent-launch' / launch.AMENDMENT
        self.assertEqual(str(self.fixture.bundle), json.loads(selected.read_text(encoding='utf-8'))['selection']['bundle'])
        renewed, _ = self.start()
        self.assertEqual('amendment-current', Path(renewed['work']).parent.name)

    def test_interrupted_second_seed_write_is_recovered_without_replacing_the_seed(self):
        from contextbase_runtime.storage import ArtifactStore
        put = ArtifactStore.put
        def fail_spec(store, relative, payload):
            if relative == 'amendment-spec.json':
                raise OSError('Synthetic second-file publication failure.')
            return put(store, relative, payload)
        with patch.object(ArtifactStore, 'put', new=fail_spec):
            with self.assertRaisesRegex(OSError, 'second-file publication failure'):
                self.start(**self.options)
        work = self.profile.work_root / 'discovery-agent-launch/amendment-current/work'
        before = (work / 'amendment-seed.json').read_bytes()
        self.assertFalse((work / 'amendment-spec.json').exists())
        continued, _ = self.start()
        self.assertEqual(str(work), continued['work'])
        self.assertEqual(before, (work / 'amendment-seed.json').read_bytes())
        self.assertTrue((work / 'amendment-spec.json').exists())

    def test_explicit_fresh_can_recover_interrupted_initial_workspace_creation(self):
        def partial_creation(source, work, request, **options):
            work.mkdir()
            (work / 'partial.txt').write_bytes(b'incomplete initial snapshot')
            raise OSError('Synthetic interrupted creation.')
        with patch.object(DiscoveryAgent, 'create', side_effect=partial_creation):
            with self.assertRaisesRegex(OSError, 'Synthetic interrupted creation'):
                self.start(**self.options)
        renewed, _ = self.start(fresh=True)
        work = Path(renewed['work'])
        self.assertFalse((work / 'partial.txt').exists())
        self.assertTrue((work / 'amendment-seed.json').exists())

    def test_adopted_amendment_finishes_interrupted_report_and_republishes_without_model(self):
        fixture = SimpleNamespace(fixture=self.fixture, agent=None, calls=[], unresolved=False,
                                  fail_review=False, fail_closure=False, reject_issue=False)
        provider = lambda *args, instruction_role='analysis': runtime_fixture.AmendmentRuntimeTests.provider(
            fixture, *args, instruction_role=instruction_role)
        create = DiscoveryAgent.create
        def capture(*args, **options):
            fixture.agent = create(*args, **options)
            return fixture.agent
        with patch.object(DiscoveryAgent, 'create', side_effect=capture), \
                patch('contextbase_runtime.provider.run_job', side_effect=provider), \
                patch.object(launch, 'prepare_report', side_effect=OSError('Synthetic report failure.')):
            with self.assertRaisesRegex(OSError, 'Synthetic report failure'):
                launch.start(self.config, **self.options, emit=lambda _: None)
        self.assertEqual(['catalog'], fixture.agent.status()['acceptedRequirements'])
        self.assertFalse(self.profile.output('discovery-agent').exists())
        with patch('contextbase_runtime.provider.run_job') as model:
            final = launch.start(self.config, emit=lambda _: None)
            repeated = launch.start(self.config, emit=lambda _: None)
        model.assert_not_called()
        self.assertTrue(final['published'])
        self.assertTrue(repeated['published'])
        self.assertEqual(final['formalSha256'], repeated['formalSha256'])
        self.assertEqual(set(launch.FILES), {path.relative_to(self.profile.output('discovery-agent').parent).as_posix()
                         for path in self.profile.output('discovery-agent').parent.rglob('*') if path.is_file()})


if __name__ == '__main__':
    unittest.main()
