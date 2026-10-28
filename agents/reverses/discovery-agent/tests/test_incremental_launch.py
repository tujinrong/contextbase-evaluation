"""One-click launch selects mode flags without starting a real model."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from contextbase_discovery import DiscoveryAgent, launch
from contextbase_runtime.config import ProjectProfile
from contextbase_runtime.controller import Session
from test_reporting import request


class IncrementalLaunchTests(unittest.TestCase):
    def setUp(self):
        temporary_root = Path(__file__).resolve().parents[1] / '.tmp'
        temporary_root.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='incremental-launch-', dir=temporary_root)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        self.original = b'class Fixture {}\n'
        (self.source / 'Fixture.cs').write_bytes(self.original)
        (self.root / 'request.json').write_text(json.dumps(request()), encoding='utf-8')
        self.config = self.root / 'contextbase.toml'

    def tearDown(self):
        self.temporary.cleanup()

    def configure(self, mode='incremental'):
        self.config.write_text('schema="contextbase-project/1"\ndefault_profile="sample"\n'
            '[profiles.sample]\nsource="source"\nrequest="request.json"\n'
            'output="results"\nwork="work-' + mode + '"\ncontext_mode="' + mode + '"\n',
            encoding='utf-8')
        return ProjectProfile.load(self.config)

    def paused_work(self, status='stopped'):
        profile = self.configure()
        with patch.object(DiscoveryAgent, 'run', return_value={'status': 'needs-investigation', 'actions': []}):
            first = launch.start(self.config, emit=lambda _: None)
        work = Path(first['work'])
        agent = DiscoveryAgent(work)
        agent.session.store.put('resume-sentinel.json', {'progress': 'a saved draft', 'revision': 3})
        if status == 'cancelled':
            agent.session.cancel('Synthetic cancellation.')
        elif status == 'stopped':
            with agent.session.store.transaction() as state:
                state.update(status='stopped', stopReason='Synthetic provider failure.')
                agent.session.store.save_state(state)
        return profile, work, agent

    def test_each_launcher_mode_uses_the_matching_init_and_delivery_options(self):
        for mode in ('full', 'evidence', 'incremental'):
            with self.subTest(mode=mode):
                profile = self.configure(mode)
                with patch.object(DiscoveryAgent, 'create', wraps=DiscoveryAgent.create) as create, \
                        patch.object(DiscoveryAgent, 'run', return_value={
                            'status': 'needs-investigation', 'actions': []}) as run, \
                        patch('contextbase_runtime.provider.run_job') as provider:
                    result = launch.start(self.config, emit=lambda _: None)
                    provider.assert_not_called()
                self.assertFalse(result['published'])
                self.assertEqual('needs-investigation', result['status'])
                self.assertEqual(mode == 'evidence', create.call_args.kwargs['evidence_mode'])
                self.assertEqual(mode == 'incremental', create.call_args.kwargs['incremental_mode'])
                run.assert_called_once_with(timeout=1800, inline_sources=mode == 'full', compact=mode == 'full')
                self.assertFalse(profile.work('relationship-agent').exists())
                self.assertFalse(profile.work('behavior-agent').exists())
                self.assertFalse(profile.output(DiscoveryAgent.name).exists())
                self.assertEqual(self.original, (self.source / 'Fixture.cs').read_bytes())

    def test_same_basis_stopped_and_cancelled_clicks_resume_without_recreating_work(self):
        for status in ('stopped', 'cancelled'):
            with self.subTest(status=status):
                profile, work, agent = self.paused_work(status)
                before = (work / 'resume-sentinel.json').read_bytes()
                resume = Session.resume
                with patch.object(DiscoveryAgent, 'create') as create, \
                        patch.object(Session, 'resume', autospec=True, side_effect=resume) as continued, \
                        patch.object(DiscoveryAgent, 'run', return_value={
                            'status': 'needs-investigation', 'actions': []}) as run, \
                        patch('contextbase_runtime.provider.run_job') as provider:
                    result = launch.start(self.config, emit=lambda _: None)
                    provider.assert_not_called()
                create.assert_not_called()
                continued.assert_called_once()
                run.assert_called_once_with(timeout=1800, inline_sources=False, compact=False)
                self.assertEqual(str(work), result['work'])
                self.assertFalse(result['published'])
                self.assertEqual(before, (work / 'resume-sentinel.json').read_bytes())
                self.assertEqual('active', DiscoveryAgent(work).status()['status'])
                self.assertFalse(profile.output(DiscoveryAgent.name).exists())
                # The next subtest intentionally starts another fresh fixture.
                if status == 'stopped':
                    with patch.object(DiscoveryAgent, 'run', return_value={
                            'status': 'needs-investigation', 'actions': []}):
                        launch.start(self.config, fresh=True, emit=lambda _: None)

    def test_active_checkpoint_runs_again_without_reinitializing_or_resuming(self):
        _, work, _ = self.paused_work('active')
        before = (work / 'resume-sentinel.json').read_bytes()
        with patch.object(DiscoveryAgent, 'create') as create, \
                patch.object(Session, 'resume') as resume, \
                patch.object(DiscoveryAgent, 'run', return_value={
                    'status': 'needs-investigation', 'actions': []}) as run:
            result = launch.start(self.config, emit=lambda _: None)
        create.assert_not_called()
        resume.assert_not_called()
        run.assert_called_once()
        self.assertFalse(result['published'])
        self.assertEqual(before, (work / 'resume-sentinel.json').read_bytes())

    def test_changed_or_added_source_retains_the_old_checkpoint_until_explicit_fresh(self):
        for mutation in ('modified', 'added'):
            with self.subTest(mutation=mutation):
                profile, work, _ = self.paused_work()
                before = (work / 'resume-sentinel.json').read_bytes()
                if mutation == 'modified':
                    (self.source / 'Fixture.cs').write_bytes(self.original + b'// changed\n')
                else:
                    (self.source / 'Added.cs').write_text('class Added {}\n', encoding='utf-8')
                with patch.object(DiscoveryAgent, 'create') as create, \
                        patch.object(DiscoveryAgent, 'run') as run, \
                        patch('contextbase_runtime.provider.run_job') as provider:
                    with self.assertRaisesRegex(ValueError, '--fresh'):
                        launch.start(self.config, emit=lambda _: None)
                    provider.assert_not_called()
                create.assert_not_called()
                run.assert_not_called()
                self.assertEqual(before, (work / 'resume-sentinel.json').read_bytes())
                self.assertEqual('stopped', DiscoveryAgent(work).status()['status'])
                with patch.object(DiscoveryAgent, 'run', return_value={
                        'status': 'needs-investigation', 'actions': []}):
                    renewed = launch.start(self.config, fresh=True, emit=lambda _: None)
                self.assertEqual(str(work), renewed['work'])
                self.assertFalse((work / 'resume-sentinel.json').exists())
                self.assertEqual((self.source / 'Fixture.cs').read_bytes(),
                    (work / 'snapshot/sources/Fixture.cs').read_bytes())
                self.assertFalse(profile.output(DiscoveryAgent.name).exists())

    def test_changed_engine_does_not_delete_the_old_checkpoint(self):
        _, work, _ = self.paused_work()
        sentinel = (work / 'resume-sentinel.json').read_bytes()
        with patch('contextbase_runtime.controller.engine_fingerprint', return_value='f' * 64), \
                patch.object(DiscoveryAgent, 'run') as run:
            with self.assertRaisesRegex(ValueError, '--fresh'):
                launch.start(self.config, emit=lambda _: None)
        run.assert_not_called()
        self.assertEqual(sentinel, (work / 'resume-sentinel.json').read_bytes())

    def test_fresh_does_not_remove_another_targets_owned_work(self):
        _, work, _ = self.paused_work()
        sentinel = (work / 'resume-sentinel.json').read_bytes()
        changed = request()
        changed['goal']['question'] = 'A different original request.'
        (self.root / 'request.json').write_text(json.dumps(changed), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'ownership|another target'):
            launch.start(self.config, fresh=True, emit=lambda _: None)
        self.assertEqual(sentinel, (work / 'resume-sentinel.json').read_bytes())

    def test_complete_incremental_work_only_republishes_without_another_run(self):
        profile, work, agent = self.paused_work('active')
        completed = {**agent.status(), 'status': 'complete', 'remainingAgentRequirements': []}
        sentinel = (work / 'resume-sentinel.json').read_bytes()
        with patch.object(DiscoveryAgent, 'status', return_value=completed), \
                patch.object(DiscoveryAgent, 'create') as create, \
                patch.object(DiscoveryAgent, 'run') as run, \
                patch.object(DiscoveryAgent, 'export', return_value={
                    'sha256': 'e' * 64, 'payload': {}}) as export, \
                patch.object(launch, 'prepare_report', return_value={
                    'acceptedRequirements': ['first-inventory', 'second-inventory']}) as report, \
                patch.object(launch, '_publish') as publish, \
                patch('contextbase_runtime.provider.run_job') as provider:
            result = launch.start(self.config, emit=lambda _: None)
            provider.assert_not_called()
        create.assert_not_called()
        run.assert_not_called()
        export.assert_called_once()
        report.assert_called_once()
        publish.assert_called_once()
        self.assertTrue(result['published'])
        self.assertEqual(str(work), result['work'])
        self.assertEqual(sentinel, (work / 'resume-sentinel.json').read_bytes())
        self.assertFalse(profile.work('relationship-agent').exists())


if __name__ == '__main__':
    unittest.main()
