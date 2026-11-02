"""Explicit amendment CLI routing without provider execution."""
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from contextbase_runtime.cli import main
from contextbase_runtime.config import ProjectProfile
from contextbase_discovery import DiscoveryAgent
from test_independent_agents import request


class RecordingAgent:
    name = 'discovery-agent'
    stage = 'discovery'
    opened = []
    calls = []
    result = {'status': 'complete'}

    def __init__(self, work):
        self.opened.append(work)

    def amend_candidate(self, bundle, verification, finding_ids, **options):
        self.calls.append((bundle, verification, finding_ids, options))
        return self.result


class AmendmentCliTests(unittest.TestCase):
    def invoke(self, agent, arguments):
        with redirect_stdout(io.StringIO()) as output, redirect_stderr(io.StringIO()) as errors:
            try:
                code = main(agent, arguments)
            except SystemExit as exc:
                code = exc.code
        return code, json.loads(output.getvalue()) if output.getvalue() else errors.getvalue()

    def setUp(self):
        RecordingAgent.opened = []
        RecordingAgent.calls = []
        RecordingAgent.result = {'status': 'complete'}

    def test_explicit_amendment_command_routes_selected_findings_and_change_scope(self):
        code, result = self.invoke(RecordingAgent, [
            'amend-candidate', '--work', 'selected-work', '--bundle', 'custody/bundle',
            '--verification', 'old-verification', '--finding', 'one', '--finding', 'two',
            '--replace-key', 'existing', '--add-kind', 'support', '--timeout', '42',
            '--inline-sources', '--compact'])
        self.assertEqual(0, code, result)
        self.assertEqual([Path('selected-work')], RecordingAgent.opened)
        self.assertEqual([(Path('custody/bundle'), 'old-verification', ['one', 'two'],
                           {'replace_keys': ['existing'], 'add_kinds': ['support'], 'timeout': 42,
                            'inline_sources': True, 'compact': True})], RecordingAgent.calls)

    def test_optional_findings_and_change_scope_are_explicitly_empty_by_default(self):
        code, result = self.invoke(RecordingAgent, [
            'amend-candidate', '--work', 'fresh-work', '--bundle', 'bundle', '--verification', 'old'])
        self.assertEqual(0, code, result)
        self.assertEqual((Path('bundle'), 'old', None,
                          {'replace_keys': [], 'add_kinds': [], 'timeout': 1800,
                           'inline_sources': False, 'compact': False}), RecordingAgent.calls[0])

    def test_noncomplete_amendment_and_errors_are_reported(self):
        RecordingAgent.result = {'status': 'blocked'}
        code, result = self.invoke(RecordingAgent, [
            'amend-candidate', '--work', 'fresh-work', '--bundle', 'bundle', '--verification', 'old'])
        self.assertEqual(2, code)
        self.assertEqual('blocked', result['status'])
        with patch.object(RecordingAgent, 'amend_candidate', side_effect=ValueError('fresh incremental work required')):
            code, result = self.invoke(RecordingAgent, [
                'amend-candidate', '--work', 'used-work', '--bundle', 'bundle', '--verification', 'old'])
        self.assertEqual(1, code)
        self.assertIn('fresh incremental', result['error'])

    def test_relationship_and_behavior_reject_before_open_or_profile_loading(self):
        for stage in ('relationship', 'behavior'):
            with self.subTest(stage=stage):
                class Unsupported(RecordingAgent):
                    pass
                Unsupported.stage = stage
                Unsupported.name = stage + '-agent'
                with patch.object(ProjectProfile, 'load', side_effect=AssertionError('must reject before config read')):
                    code, result = self.invoke(Unsupported, ['amend-candidate', '--config', 'missing.toml',
                        '--bundle', 'missing-bundle', '--verification', 'old'])
                self.assertEqual(1, code)
                self.assertIn('unsupported', result['error'])
                self.assertEqual([], RecordingAgent.opened)
                self.assertEqual([], RecordingAgent.calls)

    def test_required_inputs_and_work_are_rejected_without_opening_agent(self):
        for arguments in ([ '--work', 'work', '--verification', 'old'],
                          ['--work', 'work', '--bundle', 'bundle'],
                          ['--bundle', 'bundle', '--verification', 'old']):
            with self.subTest(arguments=arguments):
                code, result = self.invoke(RecordingAgent, ['amend-candidate', *arguments])
                self.assertIn(code, (1, 2), result)
                self.assertEqual([], RecordingAgent.opened)

    def test_config_selects_bound_work_and_rejects_explicit_work_mixing(self):
        home = Path(__file__).resolve().parents[1] / '.tmp'
        home.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='amendment-cli-', dir=home) as temporary:
            root = Path(temporary)
            source = root / 'source'
            source.mkdir()
            (source / 'Synthetic.cs').write_text('class Synthetic {}\n', encoding='utf-8')
            (root / 'request.json').write_text(json.dumps(request()), encoding='utf-8')
            config = root / 'project.toml'
            config.write_text('schema="contextbase-project/1"\ndefault_profile="selected"\n'
                '[profiles.selected]\nsource="source"\nrequest="request.json"\n'
                'output="results"\nwork="work"\ncontext_mode="incremental"\n', encoding='utf-8')
            code, result = self.invoke(DiscoveryAgent, ['init', '--config', str(config)])
            self.assertEqual(0, code, result)
            profile = ProjectProfile.load(config)
            seen = []
            def amend(agent, bundle, verification, finding_ids, **options):
                seen.append((agent.work, bundle, verification, finding_ids, options))
                return {'status': 'complete'}
            # The public amendment method is implemented concurrently; replace
            # only that provider-facing boundary while exercising real profile ownership.
            with patch('contextbase_runtime.provider.run_job') as provider, \
                 patch.object(DiscoveryAgent, 'amend_candidate', amend, create=True):
                code, result = self.invoke(DiscoveryAgent, ['amend-candidate', '--config', str(config),
                    '--bundle', str(root / 'custody'), '--verification', 'old'])
                self.assertEqual(0, code, result)
                self.assertEqual(profile.work(DiscoveryAgent.name), seen[0][0])
                code, result = self.invoke(DiscoveryAgent, ['amend-candidate', '--config', str(config),
                    '--work', 'another-work', '--bundle', str(root / 'custody'), '--verification', 'old'])
                self.assertEqual(1, code)
                self.assertIn('cannot be mixed', result['error'])
                self.assertEqual(1, len(seen))
                provider.assert_not_called()


if __name__ == '__main__':
    unittest.main()
