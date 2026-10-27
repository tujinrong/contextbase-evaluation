"""One-click lifecycle tests use the real agent with synthetic inference only."""
from contextlib import redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from contextbase_discovery import DiscoveryAgent
from contextbase_discovery import launch
from contextbase_runtime.config import ProjectProfile
from contextbase_runtime.wire import CompactWire
from test_reporting import request, synthetic_provider


class LaunchTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='one click fixture ')
        self.root = Path(self.temporary.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'Fixture.cs').write_text('class Fixture {\n bool Save() { return true; }\n}\n', encoding='utf-8')
        (self.root / 'request.json').write_text(json.dumps(request()), encoding='utf-8')
        self.config = self.root / 'contextbase.toml'
        self.config.write_text('schema="contextbase-project/1"\ndefault_profile="sample"\n'
            '[profiles.sample]\nsource="source"\nrequest="request.json"\noutput="results"\nwork="work"\n', encoding='utf-8')
        self.profile = ProjectProfile.load(self.config)
        self.output = self.profile.output('discovery-agent').parent
        self.calls = []
        self.reject = False

    def tearDown(self):
        self.temporary.cleanup()

    def provider(self, workspace, job, prompt, schema, timeout):
        canonical_path = Path(job).parent / 'canonical-context.json'
        if canonical_path.exists():
            canonical = json.loads(canonical_path.read_text(encoding='utf-8'))['payload']
            prompt_context = {'request': canonical['request'], **canonical}
            result = synthetic_provider(workspace, job, json.dumps(prompt_context), schema, timeout)
            codec = CompactWire(canonical['task'])
        else:
            canonical = json.loads(prompt[prompt.index('{"request":'):])
            result = synthetic_provider(workspace, job, prompt, schema, timeout)
            codec = None
        self.calls.append(canonical['task'])
        if self.reject and canonical['task']['operation'] == 'verify':
            result['answer']['checks'][0]['status'] = 'fail'
        if codec:
            result['answer'] = codec.encode_response(result['answer'])
        return result

    def run_launcher(self, **options):
        with patch('contextbase_runtime.provider.run_job', side_effect=self.provider):
            return launch.start(self.config, emit=lambda _: None, **options)

    def bundle(self):
        return {name: (self.output / name).read_bytes() for name in launch.FILES}

    def test_repeat_clicks_use_fresh_owned_work_from_any_cwd_and_preserve_manual_work(self):
        manual = self.profile.work('discovery-agent')
        manual.mkdir(parents=True)
        (manual / 'human.txt').write_text('unowned', encoding='utf-8')
        cwd = Path.cwd()
        try:
            os.chdir(self.root.parent)
            first = self.run_launcher()
            second = self.run_launcher()
        finally:
            os.chdir(cwd)
        self.assertTrue(first['published'])
        self.assertTrue(second['published'])
        self.assertEqual(8, len(self.calls))
        self.assertNotEqual(first['formalSha256'], second['formalSha256'])
        self.assertEqual('unowned', (manual / 'human.txt').read_text(encoding='utf-8'))
        formal = json.loads((self.output / 'contextbase.json').read_text(encoding='utf-8'))
        self.assertEqual(second['formalSha256'], formal['sha256'])
        self.assertIn(formal['sha256'], (self.output / 'review.md').read_text(encoding='utf-8'))
        home, _ = launch._prepare_home(self.profile)
        self.assertFalse((home / 'staging').exists())
        self.assertTrue((Path(second['work']) / 'state.json').is_file())
        self.assertFalse((self.profile.work_root / 'relationship-agent').exists())
        self.assertFalse((self.profile.work_root / 'behavior-agent').exists())

    def test_second_click_is_busy_before_creating_work_or_calling_provider(self):
        home, _ = launch._prepare_home(self.profile)
        with launch._lock(home):
            with self.assertRaises(launch.LaunchBusy):
                self.run_launcher()
            with redirect_stdout(io.StringIO()):
                self.assertEqual(3, launch.main(['--config', str(self.config)]))
        self.assertEqual([], self.calls)
        self.assertFalse((home / 'current').exists())

    def test_rejected_independent_verification_preserves_entire_formal_bundle(self):
        self.run_launcher()
        original = self.bundle()
        self.reject = True
        result = self.run_launcher()
        self.assertFalse(result['published'])
        self.assertEqual('needs-investigation', result['status'])
        self.assertEqual(original, self.bundle())
        self.assertEqual([], result['session']['acceptedRequirements'])

    def test_report_failure_preserves_formal_bundle_and_diagnostics(self):
        self.run_launcher()
        original = self.bundle()
        with patch.object(launch, 'prepare_report', side_effect=OSError('report failed')):
            with self.assertRaisesRegex(OSError, 'report failed'):
                self.run_launcher()
        self.assertEqual(original, self.bundle())
        home, _ = launch._prepare_home(self.profile)
        status = json.loads((home / 'current/status.json').read_text(encoding='utf-8'))
        self.assertEqual('failed', status['phase'])
        self.assertIn('report failed', status['message'])

    def test_publication_failure_rolls_back_every_changed_file(self):
        self.run_launcher()
        original = self.bundle()
        write = launch._write
        failed = False

        def fail_once(path, data):
            nonlocal failed
            if Path(path) == self.output / 'review.md' and not failed:
                failed = True
                raise OSError('publication failed')
            return write(path, data)

        with patch.object(launch, '_write', side_effect=fail_once):
            with self.assertRaisesRegex(OSError, 'publication failed'):
                self.run_launcher()
        self.assertTrue(failed)
        self.assertEqual(original, self.bundle())
        home, _ = launch._prepare_home(self.profile)
        journal = json.loads((home / 'staging/publication.json').read_text(encoding='utf-8'))
        self.assertEqual('rolled-back', journal['status'])

    def test_unowned_current_is_never_deleted(self):
        home, _ = launch._prepare_home(self.profile)
        (home / 'current').mkdir()
        marker = home / 'current/keep.txt'
        marker.write_text('keep', encoding='utf-8')
        with self.assertRaises((OSError, ValueError)):
            self.run_launcher()
        self.assertEqual('keep', marker.read_text(encoding='utf-8'))
        self.assertEqual([], self.calls)

    def test_links_in_owned_work_are_never_followed_for_cleanup(self):
        home, owner = launch._prepare_home(self.profile)
        launch._create_owned(home / 'current', owner)
        outside = self.root / 'outside.txt'
        outside.write_text('keep', encoding='utf-8')
        link = home / 'current/link.txt'
        try:
            link.symlink_to(outside)
        except OSError:
            self.skipTest('Creating symlinks requires local privilege')
        with self.assertRaisesRegex(ValueError, 'symlink|reparse'):
            launch._clean(home, home / 'current', owner)
        self.assertEqual('keep', outside.read_text(encoding='utf-8'))

    def test_finish_existing_accepted_work_does_not_call_model_again(self):
        manual = self.profile.work('discovery-agent')
        agent = DiscoveryAgent.create(self.source, manual, self.profile.request)
        self.profile.bind(agent)
        with patch('contextbase_runtime.provider.run_job', side_effect=self.provider):
            self.assertEqual('complete', agent.run(inline_sources=True)['status'])
        with patch('contextbase_runtime.provider.run_job', side_effect=AssertionError('No second model run')):
            result = launch.start(self.config, publish_work=manual, emit=lambda _: None)
        self.assertTrue(result['published'])
        self.assertEqual(str(manual), result['work'])
        self.assertEqual(4, len(self.calls))
        self.assertEqual(agent.export()['sha256'], result['formalSha256'])

    def test_incomplete_publication_recovers_before_a_new_run(self):
        self.run_launcher()
        original = self.bundle()
        home, owner = launch._prepare_home(self.profile)
        staging = home / 'staging'
        launch._create_owned(staging, owner)
        before = {}
        for relative, data in original.items():
            launch._write(staging / 'rollback' / relative, data)
            before[relative] = hashlib.sha256(data).hexdigest()
        changed_review = b'interrupted publication'
        after = {**before, 'review.md': hashlib.sha256(changed_review).hexdigest()}
        launch._json(staging / 'publication.json', {'schema': 'contextbase-discovery-publication/1',
            'status': 'publishing', 'target': self.profile.binding('discovery-agent'), 'before': before, 'after': after})
        (self.output / 'review.md').write_bytes(changed_review)
        with patch.object(DiscoveryAgent, 'create', side_effect=RuntimeError('stop after recovery')):
            with self.assertRaisesRegex(RuntimeError, 'stop after recovery'):
                self.run_launcher()
        self.assertEqual(original, self.bundle())

    def test_failed_rollback_cannot_overwrite_a_later_successful_publication(self):
        self.run_launcher()
        write = launch._write

        def fail_review(path, data):
            if Path(path) == self.output / 'review.md':
                raise OSError('publication interrupted')
            return write(path, data)

        with patch.object(launch, '_write', side_effect=fail_review), \
             patch.object(launch, '_restore', side_effect=OSError('rollback interrupted')):
            with self.assertRaisesRegex(OSError, 'rollback interrupted'):
                self.run_launcher()

        newer = DiscoveryAgent.create(self.source, self.root / 'newer-manual-work', self.profile.request)
        self.profile.bind(newer)
        with patch('contextbase_runtime.provider.run_job', side_effect=self.provider):
            self.assertEqual('complete', newer.run(inline_sources=True)['status'])
        self.profile.publish(newer)
        latest = self.bundle()
        count = len(self.calls)
        with self.assertRaisesRegex(ValueError, 'changed after interrupted publication'):
            self.run_launcher()
        self.assertEqual(latest, self.bundle())
        self.assertEqual(count, len(self.calls))
        home, _ = launch._prepare_home(self.profile)
        self.assertTrue((home / 'staging/publication.json').is_file())
        self.assertTrue((home / 'staging/rollback/contextbase.json').is_file())

    def test_invalid_recovery_journal_is_preserved_without_deleting_staging(self):
        home, owner = launch._prepare_home(self.profile)
        staging = home / 'staging'
        launch._create_owned(staging, owner)
        launch._json(staging / 'publication.json', {'status': 'unknown'})
        with self.assertRaisesRegex(ValueError, 'Invalid publication recovery journal'):
            self.run_launcher()
        self.assertTrue((staging / 'publication.json').exists())
        self.assertEqual([], self.calls)


if __name__ == '__main__':
    unittest.main()
