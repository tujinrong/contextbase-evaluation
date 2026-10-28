"""Fresh-workspace opt-in for host evidence delivery, without model calls."""
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
from contextbase_relationship import RelationshipAgent
from contextbase_behavior import BehaviorAgent
from test_independent_agents import request


class EvidenceCliConfigTests(unittest.TestCase):
    def setUp(self):
        temporary_root = Path(__file__).resolve().parents[1] / '.tmp'
        temporary_root.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='evidence-config-', dir=temporary_root)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'Registration.cs').write_text('class Registration { void Save() {} }\n', encoding='utf-8')
        self.request_path = self.root / 'request.json'
        self.request_path.write_text(json.dumps(request()), encoding='utf-8')
        self.config_path = self.root / 'project.toml'
        self.fields = {'source': 'source', 'request': 'request.json',
                       'output': 'results', 'work': '.tmp/work'}
        self.write_config()

    def tearDown(self):
        self.temporary.cleanup()

    def write_config(self):
        content = ['schema = "contextbase-project/1"', 'default_profile = "sample"', '',
                   '[profiles.sample]']
        content += [key + ' = ' + json.dumps(value) for key, value in self.fields.items()]
        self.config_path.write_text('\n'.join(content) + '\n', encoding='utf-8')

    def invoke(self, agent_type, argv, expected=0):
        with patch('contextbase_runtime.provider.run_job') as provider:
            with redirect_stdout(io.StringIO()) as stream, redirect_stderr(io.StringIO()) as errors:
                try:
                    code = main(agent_type, argv)
                except SystemExit as exc:
                    code = exc.code
            provider.assert_not_called()
        self.assertEqual(expected, code, (stream.getvalue(), errors.getvalue()))
        return json.loads(stream.getvalue()) if stream.getvalue() else errors.getvalue()

    def test_legacy_profile_defaults_to_full_and_paths_do_not_create_work(self):
        profile = ProjectProfile.load(self.config_path)
        self.assertEqual('full', profile.context_mode)
        description = self.invoke(DiscoveryAgent, ['paths', '--config', str(self.config_path)])
        self.assertEqual('full', description['contextMode'])
        self.assertFalse(profile.work_root.exists())
        self.assertFalse(profile.output_root.exists())

    def test_config_context_mode_does_not_change_output_owner_identity(self):
        legacy = ProjectProfile.load(self.config_path)
        self.fields['context_mode'] = 'evidence'
        self.write_config()
        selected = ProjectProfile.load(self.config_path)
        self.assertEqual('evidence', selected.context_mode)
        self.assertEqual(legacy.binding(DiscoveryAgent.name), selected.binding(DiscoveryAgent.name))
        self.assertEqual('evidence', selected.describe(DiscoveryAgent)['contextMode'])

    def test_profile_rejects_invalid_modes_and_unrecognized_fields(self):
        for value in ('other', '', 1, True, ['evidence']):
            with self.subTest(value=value):
                self.fields['context_mode'] = value
                self.write_config()
                with self.assertRaisesRegex(ValueError, 'context_mode'):
                    ProjectProfile.load(self.config_path)
        self.fields.pop('context_mode')
        self.fields['contextMode'] = 'evidence'
        self.write_config()
        with self.assertRaisesRegex(ValueError, 'profile requires'):
            ProjectProfile.load(self.config_path)

    def test_all_three_manual_clis_can_opt_in_only_when_initializing_fresh_work(self):
        from contextbase_runtime.evidence_dialog import VERSION
        for agent_type in (DiscoveryAgent, RelationshipAgent, BehaviorAgent):
            with self.subTest(agent=agent_type.name):
                work = self.root / agent_type.name
                args = ['init', '--source', str(self.source), '--request', str(self.request_path),
                        '--work', str(work), '--evidence']
                self.invoke(agent_type, args)
                self.assertEqual(VERSION, agent_type(work).session.config['evidencePolicy'])
                result = self.invoke(agent_type, args, expected=1)
                self.assertIn('fresh work', result['error'].lower())

    def test_manual_init_without_flag_preserves_legacy_mode(self):
        work = self.root / 'legacy-work'
        self.invoke(DiscoveryAgent, ['init', '--source', str(self.source),
                    '--request', str(self.request_path), '--work', str(work)])
        self.assertNotIn('evidencePolicy', DiscoveryAgent(work).session.config)

    def test_profile_explicit_mode_is_used_without_an_extra_flag(self):
        from contextbase_runtime.evidence_dialog import VERSION
        self.fields['context_mode'] = 'evidence'
        self.write_config()
        self.invoke(DiscoveryAgent, ['init', '--config', str(self.config_path)])
        profile = ProjectProfile.load(self.config_path)
        agent = DiscoveryAgent(profile.work(DiscoveryAgent.name))
        self.assertEqual(VERSION, agent.session.config['evidencePolicy'])
        profile.validate_workspace(agent)

    def test_explicit_flag_cannot_override_a_full_mode_profile(self):
        result = self.invoke(DiscoveryAgent, ['init', '--config', str(self.config_path), '--evidence'], expected=1)
        self.assertIn('cannot override', result['error'])
        self.assertFalse(ProjectProfile.load(self.config_path).work_root.exists())

    def test_changing_profile_mode_rejects_the_previously_initialized_work(self):
        self.invoke(DiscoveryAgent, ['init', '--config', str(self.config_path)])
        original = ProjectProfile.load(self.config_path)
        original_marker = (original.work(DiscoveryAgent.name) / 'project.json').read_bytes()
        self.fields['context_mode'] = 'evidence'
        self.write_config()
        result = self.invoke(DiscoveryAgent, ['status', '--config', str(self.config_path)], expected=1)
        self.assertIn('context_mode differs', result['error'])
        self.assertEqual(original_marker, (original.work(DiscoveryAgent.name) / 'project.json').read_bytes())

    def test_run_has_no_mode_switch_and_cannot_reconfigure_work(self):
        self.invoke(DiscoveryAgent, ['run', '--work', str(self.root / 'missing'), '--evidence'], expected=2)


if __name__ == '__main__':
    unittest.main()
