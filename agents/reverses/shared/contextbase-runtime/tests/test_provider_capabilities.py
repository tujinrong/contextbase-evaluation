"""A selected role permits only its declared optional native capabilities."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from contextbase_runtime import provider, roles
from contextbase_runtime.capabilities import normalize_capabilities
from test_provider_native import _EnvironmentFixture


class CapabilityEventTests(unittest.TestCase):
    def setUp(self):
        home = Path(__file__).resolve().parents[1] / '.tmp'
        home.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='capability-events-', dir=home)
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / 'events.jsonl'

    def audit(self, items, capability=None):
        self.path.write_text('\n'.join(json.dumps({'type': 'item.completed', 'item': item})
                                       for item in items), encoding='utf-8')
        return provider._audit_native_events(self.path, ['read'], normalize_capabilities(capability))

    def test_web_events_require_the_current_role_selection(self):
        items = [{'type': 'web_search'}, {'type': 'web_search_call'}]
        rejected = self.audit(items)
        self.assertEqual(2, len(rejected['disallowed_tool_events']))
        for mode in ('cached', 'live'):
            with self.subTest(mode=mode):
                allowed = self.audit(items, {'web_search': mode})
                self.assertEqual([], allowed['disallowed_tool_events'])
                self.assertEqual(2, len(allowed['permitted_capability_events']))

    def test_subagent_events_require_selection_and_a_known_operation(self):
        tools = ['spawn_agent', 'send_input', 'wait', 'close_agent', 'resume_agent', 'unrecognized_agent_tool']
        items = [{'type': 'collab_tool_call', 'tool': tool} for tool in tools]
        disabled = self.audit(items)
        self.assertEqual(5, len(disabled['disallowed_tool_events']))
        enabled = self.audit(items, {'subagents': True})
        self.assertEqual(1, len(enabled['disallowed_tool_events']))
        self.assertEqual(4, len(enabled['permitted_capability_events']))
        self.assertEqual(1, len(enabled['harmless_control_events']))

    def test_optional_capabilities_do_not_authorize_execution_or_foreign_tools(self):
        items = [{'type': 'command_execution', 'command': 'sensitive-command-not-copied'},
                 {'type': 'file_change'}, {'type': 'function_call'},
                 {'type': 'image_generation_call'},
                 {'type': 'mcp_tool_call', 'server': 'foreign', 'tool': 'read'},
                 {'type': 'mcp_tool_call', 'server': 'contextbase', 'tool': 'draft_apply'},
                 {'type': 'mcp_tool_call', 'server': 'contextbase', 'tool': 'read'}]
        audit = self.audit(items, {'web_search': 'live', 'subagents': True})
        self.assertEqual(6, len(audit['disallowed_tool_events']))
        self.assertNotIn('sensitive-command-not-copied', json.dumps(audit))


class CapabilityProviderTests(_EnvironmentFixture, unittest.TestCase):
    def run_job(self, capability, events, *, instruction_role='analysis'):
        source = Path(self.environment_temp.name) / 'source'
        source.mkdir()
        cli = source.parent / 'codex.exe'
        cli.write_bytes(b'fake-cli-only')
        with patch.dict('os.environ', {'CODEX_HOME': str(source.parent)}):
            role = roles.normalize_roles({instruction_role: {
                'model': 'fixture-model', 'model_reasoning_effort': 'high',
                'capabilities': capability}})[instruction_role]
        captured = []
        def launch(command, **options):
            captured.append((command, options))
            answer = Path(command[command.index('--output-last-message') + 1])
            answer.write_text('{"submission_id":"frozen"}', encoding='utf-8')
            (answer.parent / 'events.jsonl').write_text('\n'.join(json.dumps({
                'type': 'item.completed', 'item': item}) for item in events), encoding='utf-8')
            return subprocess.CompletedProcess(command, 0)
        with patch.object(provider, 'resolve_cli', return_value=cli), \
                patch.object(provider.subprocess, 'run', side_effect=launch):
            result = provider.run_job(source, source.parent / 'job', 'Inspect the source.',
                instruction_role=instruction_role, role_spec=role,
                tool_connection={'url': 'http://127.0.0.1:1234/mcp',
                                 'token': 'fixture-private-token', 'enabled_tools': ['read']})
        return result, role, captured[0]

    def test_selected_capabilities_reach_configuration_prompt_and_audit(self):
        events = [{'type': 'web_search'}, {'type': 'collab_tool_call', 'tool': 'spawn_agent'}]
        result, role, (command, options) = self.run_job(
            {'web_search': 'cached', 'subagents': True}, events)
        self.assertEqual('passed', result['metadata']['status'])
        self.assertEqual(role['capabilities'], result['metadata']['role_capabilities'])
        self.assertNotIn('--ephemeral', command)
        for setting in ('web_search="cached"', 'features.multi_agent=true', 'features.apps=false',
                        'agents.enabled=true', 'agents.max_concurrent_threads_per_session=2',
                        'agents.max_depth=1', 'agents.default_subagent_model="fixture-model"',
                        'agents.default_subagent_reasoning_effort="high"'):
            self.assertIn(setting, command)
        self.assertIn('features.shell_tool=false', command)
        self.assertIn('features.hooks=false', command)
        self.assertIn('features.plugins=false', command)
        self.assertIn(self.environment.home, options['cwd'].parents)
        self.assertEqual(role['capabilities'], self.environment.prepare_role.call_args.args[-1])
        self.assertEqual(2, len(result['metadata']['permitted_capability_events']))
        prompt = Path(result['metadata']['job_dir']) / 'prompt.txt'
        self.assertIn('public language/framework documentation', prompt.read_text(encoding='utf-8'))
        self.assertIn('same role', prompt.read_text(encoding='utf-8'))
        self.assertNotIn('fixture-private-token', json.dumps(result))

    def test_default_role_rejects_events_from_unselected_capabilities(self):
        result, _, (command, _) = self.run_job({}, [
            {'type': 'web_search'}, {'type': 'collab_tool_call', 'tool': 'spawn_agent'}])
        self.assertEqual('disallowed_tool_events', result['metadata']['status'])
        self.assertIn('web_search="disabled"', command)
        self.assertIn('features.multi_agent=false', command)
        self.assertIn('--ephemeral', command)

    def test_verifier_optional_capabilities_do_not_grant_author_tools(self):
        result, _, _ = self.run_job({'web_search': 'live', 'subagents': True}, [
            {'type': 'web_search'},
            {'type': 'mcp_tool_call', 'server': 'contextbase', 'tool': 'draft_apply'}],
            instruction_role='verification')
        self.assertEqual('disallowed_tool_events', result['metadata']['status'])
        self.assertEqual(1, len(result['metadata']['disallowed_tool_events']))
