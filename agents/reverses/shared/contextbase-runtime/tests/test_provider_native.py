import json
from pathlib import Path
import subprocess
import tempfile
import tomllib
import unittest
from unittest.mock import patch
from contextbase_runtime import provider, roles

from contextbase_runtime import native_environment

class _EnvironmentFixture:
    def setUp(self):
        self.environment_env = patch.dict('os.environ', {key: '' for key in native_environment._SECRET_ENV})
        self.environment_env.start()
        self.environment_temp = tempfile.TemporaryDirectory(prefix='native-provider-fake-auth-')
        auth = Path(self.environment_temp.name) / 'auth.json'
        auth.write_text(json.dumps({'auth_mode': 'chatgpt', 'tokens': {
            'id_token': 'fake-id', 'access_token': 'fake-access', 'refresh_token': 'fake-refresh'}}))
        self.environment = native_environment.NativeEnvironment(auth_source=auth)
        self.environment.__enter__()
        self.probe_patch = patch.object(native_environment.NativeEnvironment, 'prepare_role', return_value=([], {'policy': native_environment.POLICY, 'probes': []}))
        self.probe_patch.start()

    def tearDown(self):
        self.probe_patch.stop()
        self.environment.__exit__(None, None, None)
        self.environment_temp.cleanup()
        self.environment_env.stop()

class NativeProviderTests(_EnvironmentFixture, unittest.TestCase):
    def test_native_skill_disabling_uses_actual_bootstrap_probe_paths(self):
        temporary = Path(__file__).resolve().parents[1] / '.tmp'
        temporary.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temporary) as temp:
            root = Path(temp)
            codex_home, user_home = root / 'codex', root / 'home'
            skills = [codex_home / 'skills/demo/SKILL.md', user_home / '.agents/skills/other/SKILL.md']
            for skill in skills:
                skill.parent.mkdir(parents=True)
                skill.write_text('---\nname: fixture\ndescription: Fixture only.\n---\n', encoding='utf-8')
            source = root / 'source'
            source.mkdir()
            cli = root / 'codex.exe'
            cli.write_bytes(b'cli')
            def launch(command, **options):
                setting = next(value for value in command if value.startswith('skills.config='))
                entries = tomllib.loads(setting)['skills']['config']
                self.assertEqual({str(path.resolve()) for path in skills}, {row['path'] for row in entries})
                self.assertTrue(all(row['enabled'] is False for row in entries))
                Path(command[command.index('--output-last-message') + 1]).write_text('{"submission_id":"frozen"}', encoding='utf-8')
                return subprocess.CompletedProcess(command, 0)
            with patch.dict('os.environ', {'CODEX_HOME': str(codex_home)}), patch.object(Path, 'home', return_value=user_home):
                role = roles.normalize_roles()['analysis']
                skills_setting = 'skills.config=[' + ','.join('{path=' + json.dumps(str(path.resolve())) + ',enabled=false}' for path in skills) + ']'
                with patch.object(self.environment, 'prepare_role', return_value=(['-c', skills_setting], {'policy': native_environment.POLICY})), patch.object(provider, 'resolve_cli', return_value=cli), patch.object(provider.subprocess, 'run', side_effect=launch):
                    result = provider.run_job(source, root / 'job', 'Analyze', role_spec=role,
                        tool_connection={'url':'http://127.0.0.1:1234/mcp','token':'secret','enabled_tools':['read']})
            self.assertEqual('passed', result['metadata']['status'])

    def test_native_job_uses_frozen_role_and_private_token_environment(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / 'source'
            source.mkdir()
            cli = root / 'codex.exe'
            cli.write_bytes(b'cli')
            with patch.dict('os.environ', {'CODEX_HOME': str(root)}):
                role = roles.normalize_roles()['analysis']
            seen = []
            def launch(command, **options):
                seen.append(command)
                self.assertIn('--ignore-user-config', command)
                self.assertIn('features.view_image=false', command)
                self.assertNotIn('tools.view_image=false', command)
                self.assertIn('mcp_servers.contextbase.default_tools_approval_mode="approve"', command)
                self.assertIn('tool_output_token_limit=262144', command)
                for name in ('read', 'submit'):
                    self.assertIn('mcp_servers.contextbase.tools.' + name + '.output_token_limit=262144', command)
                self.assertNotEqual(source, options['cwd'])
                self.assertIn('private-secret', options['env'].values())
                self.assertNotIn('private-secret', str(command))
                Path(command[command.index('--output-last-message')+1]).write_text('{"submission_id":"frozen"}', encoding='utf-8')
                return subprocess.CompletedProcess(command, 0)
            with patch.object(provider, 'resolve_cli', return_value=cli), patch.object(provider.subprocess, 'run', side_effect=launch):
                result = provider.run_job(source, root / 'job', 'Analyze source.', role_spec=role, tool_connection={'url':'http://127.0.0.1:12345/mcp', 'token':'private-secret', 'enabled_tools':['read','submit']})
            self.assertEqual('passed', result['metadata']['status'])
            self.assertEqual(1, len(seen))
            self.assertNotIn('private-secret', json.dumps(result))
            self.assertNotIn('Do not write files or use network tools', (root/'job'/'prompt.txt').read_text())

    def test_nonlocal_broker_rejected_before_job_creation(self):
        with self.assertRaises(ValueError):
            provider.run_job(Path('.'), Path('unused'), '', role_spec={}, tool_connection={'url':'https://remote/mcp','token':'x','enabled_tools':['read']})


class NativeEventAuditTests(_EnvironmentFixture, unittest.TestCase):
    def test_audit_rejects_foreign_mcp_commands_and_spawns_but_records_wait(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'events.jsonl'
            items = [{'type': 'mcp_tool_call', 'server': 'contextbase', 'tool': 'read'},
                     {'type': 'collab_tool_call', 'tool': 'wait'},
                     {'type': 'command_execution', 'command': 'not persisted in audit'},
                     {'type': 'file_change'}, {'type': 'web_search'},
                     {'type': 'mcp_tool_call', 'server': 'other', 'tool': 'read'},
                     {'type': 'collab_tool_call', 'tool': 'spawn_agent'}]
            path.write_text('\n'.join(json.dumps({'type': 'item.completed', 'item': i}) for i in items), encoding='utf-8')
            result = provider._audit_native_events(path, ['read'])
            self.assertEqual(5, len(result['disallowed_tool_events']))
            self.assertEqual(1, len(result['harmless_control_events']))
            self.assertNotIn('not persisted', json.dumps(result))

    def test_reported_unauthorized_tool_prevents_native_provider_success(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / 'source'
            source.mkdir()
            cli = root / 'codex.exe'
            cli.write_bytes(b'cli')
            with patch.dict('os.environ', {'CODEX_HOME': str(root)}):
                role = roles.normalize_roles()['analysis']
            def launch(command, **options):
                answer = Path(command[command.index('--output-last-message') + 1])
                answer.write_text('{"submission_id":"frozen"}', encoding='utf-8')
                (answer.parent / 'events.jsonl').write_text(json.dumps({
                    'type': 'item.completed', 'item': {'type': 'command_execution'}}), encoding='utf-8')
                return subprocess.CompletedProcess(command, 0)
            with patch.object(provider, 'resolve_cli', return_value=cli), patch.object(provider.subprocess, 'run', side_effect=launch):
                result = provider.run_job(source, root / 'job', 'Analyze', role_spec=role,
                    tool_connection={'url': 'http://127.0.0.1:1234/mcp', 'token': 'secret', 'enabled_tools': ['read']})
            self.assertEqual('disallowed_tool_events', result['metadata']['status'])
            self.assertEqual('reported-cli-events-only', result['metadata']['native_tool_audit_scope'])
