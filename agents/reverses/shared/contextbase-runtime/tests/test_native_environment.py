"""Staged environment tests: synthetic cached login only, no model invocation."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from contextbase_runtime import native_environment as module
FAKE = {'auth_mode': 'chatgpt', 'tokens': {'id_token': 'fake-id', 'access_token': 'fake-access', 'refresh_token': 'fake-refresh'}}


class NativeEnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='native-env-test-')
        self.root = Path(self.temp.name)
        self.auth = self.root / 'auth.json'
        self.raw = json.dumps(FAKE).encode()
        self.auth.write_bytes(self.raw)
        self.environ = patch.dict(os.environ, {key: '' for key in module._SECRET_ENV})
        self.environ.start()

    def tearDown(self):
        self.environ.stop()
        self.temp.cleanup()

    def test_private_home_nested_scope_child_env_and_cleanup(self):
        parent = dict(os.environ)
        with module.NativeEnvironment(auth_source=self.auth, excluded_roots=[Path.cwd()]) as environment:
            home = environment.home
            self.assertNotEqual(self.auth.parent, home)
            self.assertEqual(self.raw, (home / 'auth.json').read_bytes())
            self.assertEqual(['auth.json'], sorted(path.name for path in home.iterdir()))
            self.assertEqual(str(home), environment.child_env()['CODEX_HOME'])
            with module.scope() as second_role:
                self.assertIs(environment, second_role)
            self.assertIs(environment, module.current())
            self.assertEqual(parent, dict(os.environ))
        self.assertIsNone(module.current())
        self.assertFalse(home.exists())
        self.assertTrue(environment.report()['cleanupComplete'])
        self.assertEqual(self.raw, self.auth.read_bytes())
        self.assertNotIn('fake-access', json.dumps(environment.report()))

    def test_failure_cancel_and_private_refresh_cleanup(self):
        environment = module.NativeEnvironment(auth_source=self.auth)
        with self.assertRaises(KeyboardInterrupt):
            with environment:
                (environment.home / 'auth.json').write_text(json.dumps({**FAKE, 'last_refresh': 'fake-time'}))
                raise KeyboardInterrupt()
        self.assertFalse(environment.home.exists())
        self.assertTrue(environment.report()['privateAuthCacheChanged'])
        self.assertTrue(environment.report()['cleanupComplete'])
        self.assertEqual(self.raw, self.auth.read_bytes())

    def test_missing_api_key_and_endpoint_overrides_fail_without_fallback(self):
        with self.assertRaises(module.EnvironmentError):
            with module.NativeEnvironment(auth_source=self.root / 'missing.json'):
                self.fail('unsupported auth entered')
        self.auth.write_text(json.dumps({'OPENAI_API_KEY': 'fake-probe-key'}))
        with self.assertRaises(module.EnvironmentError):
            with module.NativeEnvironment(auth_source=self.auth):
                self.fail('API-key fallback entered')
        self.auth.write_bytes(self.raw)
        with patch.dict(os.environ, {'OPENAI_BASE_URL': 'http://127.0.0.1:9'}):
            with self.assertRaises(module.EnvironmentError):
                with module.NativeEnvironment(auth_source=self.auth):
                    self.fail('endpoint override accepted')

    def test_role_probe_discovers_skills_disables_actual_files_and_checks_sources(self):
        calls = []
        config = {'model': 'fixture-model', 'model_provider': 'openai', 'model_reasoning_effort': 'high',
                  'project_doc_max_bytes': 0, 'model_instructions_file': str(self.root / 'role.md')}
        command = ['fake-cli', 'exec']
        for key, value in config.items():
            command += ['-c', key + '=' + json.dumps(value)]
        with module.NativeEnvironment(auth_source=self.auth) as environment:
            skill = str(environment.home / 'skills' / '.system' / 'fixture' / 'SKILL.md')
            def probe(cli, cwd, overrides, child_env):
                calls.append(overrides)
                disabled = any(arg.startswith('skills.config=') for arg in overrides)
                return {'skills': [] if disabled else [{'path': skill, 'enabled': True}],
                        'enabledSkillCount': 0 if disabled else 1, 'instructionSources': [],
                        'config': config, 'cliVersion': 'fixture-cli'}
            with patch.object(module, 'probe', side_effect=probe):
                arguments, report = environment.prepare_role('fake-cli', self.root, command, environment.child_env())
                environment.prepare_role('fake-cli', self.root, command, environment.child_env())
            self.assertEqual(3, len(calls))
            self.assertIn('SKILL.md', arguments[1])
            self.assertEqual(2, len(environment.probes))
            self.assertEqual(0, report['probes'][0]['enabledSkillCount'])

    def test_unexpected_instruction_source_or_config_rejected(self):
        with module.NativeEnvironment(auth_source=self.auth) as environment:
            observed = {'skills': [], 'enabledSkillCount': 0, 'instructionSources': ['unexpected/AGENTS.md'],
                        'config': {}, 'cliVersion': 'fixture-cli'}
            with patch.object(module, 'probe', return_value=observed):
                with self.assertRaises(module.EnvironmentError):
                    environment.prepare_role('fake-cli', self.root, ['fake-cli', 'exec'], environment.child_env())
            observed['instructionSources'] = []
            with patch.object(module, 'probe', return_value=observed):
                with self.assertRaises(module.EnvironmentError):
                    environment.prepare_role('fake-cli', self.root, ['fake-cli', 'exec', '-c', 'model="expected"'], environment.child_env())

    def test_tool_output_limits_must_be_observed_exactly(self):
        observed = {'skills': [], 'enabledSkillCount': 0, 'instructionSources': [],
                    'config': {}, 'cliVersion': 'fixture-cli'}
        command = ['fake-cli', 'exec', '-c', 'mcp_servers.contextbase.tools.read.output_token_limit=262144']
        with module.NativeEnvironment(auth_source=self.auth) as environment:
            for limits in (None, {}, {'read': 100}, {'read': 262144, 'foreign': 262144}):
                if limits is not None:
                    observed['mcpToolOutputLimits'] = limits
                with patch.object(module, 'probe', return_value=observed):
                    with self.assertRaisesRegex(module.EnvironmentError, 'output limits'):
                        environment.prepare_role('fake-cli', self.root, command, environment.child_env())
            observed['mcpToolOutputLimits'] = {'read': 262144}
            with patch.object(module, 'probe', return_value=observed):
                _, report = environment.prepare_role('fake-cli', self.root, command, environment.child_env())
            self.assertEqual({'read': 262144}, report['probes'][0]['mcpToolOutputLimits'])

    def test_global_tool_output_limit_is_checked_not_assumed(self):
        observed = {'skills': [], 'enabledSkillCount': 0, 'instructionSources': [],
                    'config': {}, 'cliVersion': 'fixture-cli'}
        command = ['fake-cli', 'exec', '-c', 'tool_output_token_limit=262144']
        with module.NativeEnvironment(auth_source=self.auth) as environment:
            for value in (None, 12000):
                observed['config'] = {'tool_output_token_limit': value}
                with patch.object(module, 'probe', return_value=observed):
                    with self.assertRaisesRegex(module.EnvironmentError, 'configuration differs'):
                        environment.prepare_role('fake-cli', self.root, command, environment.child_env())
            observed['config']['tool_output_token_limit'] = 262144
            with patch.object(module, 'probe', return_value=observed):
                _, report = environment.prepare_role('fake-cli', self.root, command, environment.child_env())
            self.assertEqual(262144, report['probes'][0]['config']['tool_output_token_limit'])


if __name__ == '__main__':
    unittest.main()


class AgentEnvironmentScopeTests(unittest.TestCase):
    setUp = NativeEnvironmentTests.setUp
    tearDown = NativeEnvironmentTests.tearDown
    def test_author_and_verifier_share_private_home_and_cleanup_report(self):
        from types import SimpleNamespace
        from contextbase_runtime.agent import AnalysisAgent
        from contextbase_runtime.storage import ArtifactStore
        original = module.NativeEnvironment
        store = ArtifactStore(self.root / 'work')
        seen = []
        class Agent:
            session = SimpleNamespace(config={'nativeToolsPolicy': 'contextbase-native-tools/1'},
                store=store, source=SimpleNamespace(root=self.root / 'source'))
            def _execute_attempt_scoped(self, requirements, **kwargs):
                first = module.current()
                with module.scope() as second:
                    seen.extend([first.home, second.home])
                return 'author-and-verifier-result'
        with patch.object(module, 'NativeEnvironment', side_effect=lambda **kwargs: original(auth_source=self.auth, **kwargs)):
            result = AnalysisAgent._execute_attempt(Agent(), ['catalog'], timeout=5,
                inline_sources=False, runner=None, compact=False)
        self.assertEqual('author-and-verifier-result', result)
        self.assertEqual(seen[0], seen[1])
        self.assertFalse(seen[0].exists())
        report_path = next((store.root / 'native-environments').glob('*.json'))
        self.assertTrue(store.get('native-environments/' + report_path.name)['cleanupComplete'])
        self.assertEqual(self.raw, self.auth.read_bytes())

    def test_injected_runner_has_no_authentication_requirement(self):
        from types import SimpleNamespace
        from contextbase_runtime.agent import AnalysisAgent
        class Agent:
            session = SimpleNamespace(config={'nativeToolsPolicy': 'contextbase-native-tools/1'})
            def _execute_attempt_scoped(self, requirements, **kwargs):
                return 'injected-result'
        with patch.object(module, 'NativeEnvironment', side_effect=AssertionError('must not create auth scope')):
            self.assertEqual('injected-result', AnalysisAgent._execute_attempt(Agent(), ['catalog'],
                timeout=5, inline_sources=False, runner=lambda: None, compact=False))
