"""One-click environment preparation; no model, network or source app execution."""
from contextlib import nullcontext, redirect_stderr, redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch


AGENT_ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('discovery_repository_bootstrap', AGENT_ROOT / 'launch.py')
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='discovery bootstrap ')
        self.root = Path(self.temporary.name).resolve()
        self.agent = self.root / 'agents/reverses/discovery-agent'
        self.runtime = self.root / 'agents/reverses/shared/contextbase-runtime'
        for directory, name, module in (
            (self.agent, 'contextbase-discovery', 'contextbase_discovery'),
            (self.runtime, 'contextbase-runtime', 'contextbase_runtime'),
        ):
            (directory / 'src' / module).mkdir(parents=True)
            (directory / 'src' / module / '__init__.py').write_text('', encoding='utf-8')
            (directory / 'pyproject.toml').write_text(
                '[project]\nname = "' + name + '"\nversion = "0.1.0"\n'
                'dependencies = []\n[project.optional-dependencies]\nanalysis = []\n', encoding='utf-8')
        self.environment = self.agent / '.tmp/oneclick-environment'
        self.python = bootstrap.environment_python(self.environment)

    def tearDown(self):
        self.temporary.cleanup()

    def create_environment(self, directory):
        executable = bootstrap.environment_python(Path(directory))
        executable.parent.mkdir(parents=True, exist_ok=True)
        executable.write_bytes(b'synthetic interpreter')

    def install(self):
        with patch.object(bootstrap.venv, 'EnvBuilder') as builder, \
                patch.object(bootstrap, 'probe_environment', return_value=True), \
                patch.object(bootstrap.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0)) as run, \
                redirect_stdout(io.StringIO()):
            builder.return_value.create.side_effect = self.create_environment
            result = bootstrap.prepare_environment(self.agent)
        return result, builder, run

    def test_first_start_installs_only_runtime_analysis_and_discovery(self):
        result, builder, run = self.install()
        self.assertEqual(self.python, result)
        builder.return_value.create.assert_called_once_with(self.environment)
        command = run.call_args.args[0]
        self.assertEqual([str(self.runtime) + '[analysis]', str(self.agent)],
                         [command[i + 1] for i, value in enumerate(command) if value == '-e'])
        self.assertNotIn('reverse-agent', ' '.join(command))
        self.assertTrue((self.environment / 'installed.json').is_file())

    def test_unchanged_prepared_environment_reuses_without_pip_or_venv_creation(self):
        self.install()
        with patch.object(bootstrap.venv, 'EnvBuilder') as builder, \
                patch.object(bootstrap, 'probe_environment', return_value=True) as probe, \
                patch.object(bootstrap.subprocess, 'run') as run, redirect_stdout(io.StringIO()):
            self.assertEqual(self.python, bootstrap.prepare_environment(self.agent))
        builder.assert_not_called()
        run.assert_not_called()
        probe.assert_called_once()

    def test_changed_local_source_refreshes_dependencies_and_stamp(self):
        self.install()
        stamp = self.environment / 'installed.json'
        before = json.loads(stamp.read_text(encoding='utf-8'))
        (self.agent / 'src/contextbase_discovery/launch.py').write_text('version = 2\n', encoding='utf-8')
        with patch.object(bootstrap.venv, 'EnvBuilder') as builder, \
                patch.object(bootstrap, 'probe_environment', return_value=True), \
                patch.object(bootstrap.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0)) as run, \
                redirect_stdout(io.StringIO()):
            bootstrap.prepare_environment(self.agent)
        builder.assert_not_called()
        self.assertEqual(1, run.call_count)
        self.assertNotEqual(before['fingerprint'], json.loads(stamp.read_text(encoding='utf-8'))['fingerprint'])

    def test_unowned_existing_environment_is_preserved_and_not_installed(self):
        self.environment.mkdir(parents=True)
        sentinel = self.environment / 'keep.txt'
        sentinel.write_text('manual environment', encoding='utf-8')
        with patch.object(bootstrap.venv, 'EnvBuilder') as builder, patch.object(bootstrap.subprocess, 'run') as run:
            with self.assertRaisesRegex(bootstrap.BootstrapError, '所有'):
                bootstrap.prepare_environment(self.agent)
        self.assertEqual('manual environment', sentinel.read_text(encoding='utf-8'))
        builder.assert_not_called()
        run.assert_not_called()

    def test_failed_installation_does_not_launch_analysis_or_touch_previous_output(self):
        project = self.root / 'project with spaces'
        project.mkdir()
        config = project / 'contextbase.toml'
        config.write_text('schema = "synthetic"\n', encoding='utf-8')
        output = project / 'contextbase.json'
        output.write_text('previous adopted output', encoding='utf-8')
        with patch.object(bootstrap, '__file__', str(self.agent / 'launch.py')), \
                patch.object(bootstrap.venv, 'EnvBuilder') as builder, \
                patch.object(bootstrap.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1)) as run, \
                redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            builder.return_value.create.side_effect = self.create_environment
            self.assertEqual(1, bootstrap.main(['--config', str(config)]))
        self.assertEqual(1, run.call_count)
        self.assertIn('pip', run.call_args.args[0])
        self.assertNotIn('contextbase_discovery.launch', run.call_args.args[0])
        self.assertFalse((self.environment / 'installed.json').exists())
        self.assertEqual('previous adopted output', output.read_text(encoding='utf-8'))

    def test_owned_environment_must_pass_isolation_probe_before_launch(self):
        with patch.object(bootstrap.venv, 'EnvBuilder') as builder, \
                patch.object(bootstrap, 'probe_environment', return_value=False), \
                patch.object(bootstrap.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0)), \
                redirect_stdout(io.StringIO()):
            builder.return_value.create.side_effect = self.create_environment
            with self.assertRaisesRegex(bootstrap.BootstrapError, '検査に失敗'):
                bootstrap.prepare_environment(self.agent)
        self.assertFalse((self.environment / 'installed.json').exists())

    def test_os_lock_blocks_second_start_and_releases_after_failure(self):
        lock = self.root / 'start.lock'
        with self.assertRaisesRegex(RuntimeError, 'synthetic failure'):
            with bootstrap.preparation_lock(lock):
                with self.assertRaises(bootstrap.PreparationBusy):
                    with bootstrap.preparation_lock(lock):
                        self.fail('Concurrent startup entered the critical section')
                raise RuntimeError('synthetic failure')
        with bootstrap.preparation_lock(lock):
            pass

    def test_main_forwards_absolute_config_profile_and_child_exit_code(self):
        config = self.root / 'project.toml'
        config.write_text('', encoding='utf-8')
        with patch.object(bootstrap, 'preparation_lock', return_value=nullcontext()), \
                patch.object(bootstrap, 'prepare_environment', return_value=self.python), \
                patch.object(bootstrap.subprocess, 'run', return_value=subprocess.CompletedProcess([], 2)) as run:
            self.assertEqual(2, bootstrap.main(['--config', str(config), '--no-pause', '--profile', 'alternate']))
        command = run.call_args.args[0]
        self.assertEqual([str(self.python), '-I', '-X', 'utf8', '-m', 'contextbase_discovery.launch',
                          '--config', str(config.resolve()), '--profile', 'alternate'], command)
        self.assertEqual(config.parent, run.call_args.kwargs['cwd'])

    @unittest.skipUnless(os.name == 'nt', 'Windows command wrapper')
    def test_cmd_handles_checkout_spaces_other_cwd_and_nonzero_exit(self):
        checkout = self.root / 'checkout with spaces'
        project = checkout / 'test-project1'
        project.mkdir(parents=True)
        wrapper = project / 'run-discovery.cmd'
        shutil.copyfile(AGENT_ROOT.parents[2] / 'test-project1/run-discovery.cmd', wrapper)
        (project / 'contextbase.toml').write_text('', encoding='utf-8')
        fake_bootstrap = checkout / 'agents/reverses/discovery-agent/launch.py'
        fake_bootstrap.parent.mkdir(parents=True)
        fake_bootstrap.write_text(
            'import json,sys\n'
            'print(json.dumps({"arguments":sys.argv[1:]}))\n'
            'raise SystemExit(7)\n', encoding='utf-8')
        outside = self.root / 'another working directory'
        outside.mkdir()
        comspec = os.environ.get('COMSPEC', 'cmd.exe')
        command = f'"{comspec}" /d /s /c ""{wrapper}" --no-pause --profile alternate"'
        result = subprocess.run(command, cwd=outside, capture_output=True, text=True, encoding='utf-8', timeout=30)
        self.assertEqual(7, result.returncode, result.stdout + result.stderr)
        line = next(line for line in result.stdout.splitlines() if line.startswith('{'))
        args = json.loads(line)['arguments']
        self.assertEqual(str(project / 'contextbase.toml'), args[args.index('--config') + 1])
        self.assertEqual('alternate', args[args.index('--profile') + 1])


if __name__ == '__main__':
    unittest.main()
