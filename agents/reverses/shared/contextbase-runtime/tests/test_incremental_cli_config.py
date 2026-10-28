"""Incremental mode is an explicit fresh-workspace choice, never a run-time switch."""
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from contextbase_runtime.cli import main
from contextbase_runtime.config import ProjectProfile
from contextbase_runtime.evidence_dialog import VERSION as EVIDENCE_POLICY
from contextbase_runtime.incremental import VERSION as INCREMENTAL_POLICY
from contextbase_discovery import DiscoveryAgent
from contextbase_relationship import RelationshipAgent
from contextbase_behavior import BehaviorAgent
from test_independent_agents import request


class IncrementalCliConfigTests(unittest.TestCase):
    def setUp(self):
        temporary_root = Path(__file__).resolve().parents[1] / '.tmp'
        temporary_root.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='incremental-config-', dir=temporary_root)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'Registration.cs').write_text('class Registration {}\n', encoding='utf-8')
        self.request_path = self.root / 'request.json'
        self.request_path.write_text(json.dumps(request()), encoding='utf-8')
        self.config_path = self.root / 'project.toml'
        self.write_config()

    def tearDown(self):
        self.temporary.cleanup()

    def write_config(self, mode='incremental'):
        self.config_path.write_text(
            'schema="contextbase-project/1"\ndefault_profile="sample"\n'
            '[profiles.sample]\nsource="source"\nrequest="request.json"\n'
            'output="results"\nwork="work"\ncontext_mode=' + json.dumps(mode) + '\n',
            encoding='utf-8')

    def invoke(self, agent_type, argv, expected=0):
        with patch('contextbase_runtime.provider.run_job') as provider:
            with redirect_stdout(io.StringIO()) as output, redirect_stderr(io.StringIO()) as errors:
                try:
                    code = main(agent_type, argv)
                except SystemExit as exc:
                    code = exc.code
            provider.assert_not_called()
        self.assertEqual(expected, code, (output.getvalue(), errors.getvalue()))
        return json.loads(output.getvalue()) if output.getvalue() else errors.getvalue()

    def test_paths_report_incremental_without_creating_work_or_output(self):
        profile = ProjectProfile.load(self.config_path)
        result = self.invoke(DiscoveryAgent, ['paths', '--config', str(self.config_path)])
        self.assertEqual('incremental', profile.context_mode)
        self.assertEqual('incremental', result['contextMode'])
        self.assertFalse(profile.work_root.exists())
        self.assertFalse(profile.output_root.exists())

    def test_each_manual_agent_initializes_fresh_incremental_work_only(self):
        for agent_type in (DiscoveryAgent, RelationshipAgent, BehaviorAgent):
            with self.subTest(agent=agent_type.name):
                work = self.root / agent_type.name
                args = ['init', '--source', str(self.source), '--request', str(self.request_path),
                        '--work', str(work), '--incremental']
                self.invoke(agent_type, args)
                configuration = agent_type(work).session.config
                self.assertEqual(INCREMENTAL_POLICY, configuration['incrementalPolicy'])
                self.assertNotIn('evidencePolicy', configuration)
                self.invoke(agent_type, args, expected=1)

    def test_configured_incremental_mode_does_not_require_an_extra_flag(self):
        self.invoke(DiscoveryAgent, ['init', '--config', str(self.config_path)])
        profile = ProjectProfile.load(self.config_path)
        agent = DiscoveryAgent(profile.work(DiscoveryAgent.name))
        self.assertEqual(INCREMENTAL_POLICY, agent.session.config['incrementalPolicy'])
        profile.validate_workspace(agent)

    def test_explicit_incremental_flag_matches_the_configured_mode(self):
        self.invoke(DiscoveryAgent, ['init', '--config', str(self.config_path), '--incremental'])
        self.assertTrue(ProjectProfile.load(self.config_path).work(DiscoveryAgent.name).exists())

    def test_flags_cannot_override_a_different_profile_mode(self):
        for mode, flag in (('full', '--incremental'), ('evidence', '--incremental'),
                           ('incremental', '--evidence')):
            with self.subTest(mode=mode, flag=flag):
                self.write_config(mode)
                result = self.invoke(DiscoveryAgent,
                    ['init', '--config', str(self.config_path), flag], expected=1)
                self.assertIn('cannot override', result['error'])
                self.assertFalse((self.root / 'work').exists())

    def test_init_modes_are_mutually_exclusive_before_workspace_creation(self):
        work = self.root / 'never-created'
        self.invoke(DiscoveryAgent, ['init', '--source', str(self.source),
            '--request', str(self.request_path), '--work', str(work),
            '--evidence', '--incremental'], expected=2)
        self.assertFalse(work.exists())

    def test_run_cannot_change_an_existing_workspace_mode(self):
        self.invoke(DiscoveryAgent, ['run', '--work', str(self.root / 'missing'),
                                    '--incremental'], expected=2)

    def test_profile_mode_requires_exact_non_conflicting_policy_bindings(self):
        configurations = {'full': {}, 'evidence': {'evidencePolicy': EVIDENCE_POLICY},
                          'incremental': {'incrementalPolicy': INCREMENTAL_POLICY}}
        for mode, valid in configurations.items():
            self.write_config(mode)
            profile = ProjectProfile.load(self.config_path)
            profile._validate_context_mode(SimpleNamespace(session=SimpleNamespace(config=valid)))
            invalid = [value for other, value in configurations.items() if other != mode]
            invalid += [{'incrementalPolicy': INCREMENTAL_POLICY, 'evidencePolicy': EVIDENCE_POLICY},
                        {'incrementalPolicy': 'unknown'}, {'incrementalPolicy': None},
                        {'evidencePolicy': None}]
            for configuration in invalid:
                with self.subTest(mode=mode, configuration=configuration), self.assertRaises(ValueError):
                    profile._validate_context_mode(
                        SimpleNamespace(session=SimpleNamespace(config=configuration)))

    def test_changing_profile_mode_does_not_mutate_its_existing_workspace(self):
        self.invoke(DiscoveryAgent, ['init', '--config', str(self.config_path)])
        profile = ProjectProfile.load(self.config_path)
        marker = profile.work(DiscoveryAgent.name) / 'project.json'
        original = marker.read_bytes()
        for mode in ('full', 'evidence'):
            with self.subTest(mode=mode):
                self.write_config(mode)
                result = self.invoke(DiscoveryAgent, ['status', '--config', str(self.config_path)], expected=1)
                self.assertIn('context_mode differs', result['error'])
                self.assertEqual(original, marker.read_bytes())


if __name__ == '__main__':
    unittest.main()
