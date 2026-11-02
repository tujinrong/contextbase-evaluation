"""Run-scoped cached-login environment, with no-turn bootstrap verification."""
from contextlib import contextmanager
from contextvars import ContextVar
import hashlib
import uuid
import json
import os
from pathlib import Path
import queue
import stat
import subprocess
import tempfile
import threading
import time

POLICY = 'contextbase-native-environment/1'
_CURRENT = ContextVar('contextbase_native_environment', default=None)
_SECRET_ENV = ('OPENAI_API_KEY', 'CODEX_API_KEY', 'OPENAI_BASE_URL', 'AZURE_OPENAI_API_KEY', 'OPENAI_API_BASE', 'CHATGPT_BASE_URL')
_CONFIG_KEYS = ('model', 'model_provider', 'model_reasoning_effort', 'project_doc_max_bytes', 'model_instructions_file',
                'tool_output_token_limit', 'web_search', 'features', 'agents')


def current():
    return _CURRENT.get()


class EnvironmentError(RuntimeError):
    pass


def _private(path):
    if os.name == 'nt':
        system = Path(os.environ.get('SystemRoot', 'C:/Windows')) / 'System32'
        result = subprocess.run([str(system / 'whoami.exe'), '/user', '/fo', 'csv', '/nh'],
                                capture_output=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        import csv
        sid = next(csv.reader(result.stdout.decode('ascii', 'replace').splitlines()))[1]
        if not sid.startswith('S-1-') or any(c not in 'S-0123456789' for c in sid):
            raise EnvironmentError('Cannot identify the current user for private runtime permissions')
        subprocess.run([str(system / 'icacls.exe'), str(path), '/inheritance:r', '/grant:r',
                        '*' + sid + ':(OI)(CI)F'], capture_output=True, check=True,
                       creationflags=subprocess.CREATE_NO_WINDOW)
    else:
        path.chmod(0o700)
        if path.stat().st_uid != os.getuid() or stat.S_IMODE(path.stat().st_mode) != 0o700:
            raise EnvironmentError('Private runtime directory permissions could not be enforced')


class NativeEnvironment:
    def __init__(self, *, auth_source=None, excluded_roots=()):
        original = Path(os.environ.get('CODEX_HOME', Path.home() / '.codex'))
        self.auth_source = Path(auth_source) if auth_source is not None else original / 'auth.json'
        self.excluded_roots = [Path(p).resolve() for p in excluded_roots]
        self.excluded_roots.extend(parent for parent in Path(__file__).resolve().parents if (parent / '.git').exists())
        self.identifier = uuid.uuid4().hex
        self.probes, self.disabled_skills = [], []
        self.cleaned, self.auth_changed = False, False

    def __enter__(self):
        if any(os.environ.get(key) for key in _SECRET_ENV):
            raise EnvironmentError('Native isolation does not support ambient API-key or endpoint overrides')
        # Cached ChatGPT credentials only. External keyring-only/API-key modes fail closed.
        if self.auth_source.is_symlink() or not self.auth_source.is_file() or self.auth_source.stat().st_size > 2_000_000:
            raise EnvironmentError('Native isolation requires an existing regular cached ChatGPT auth.json')
        raw = self.auth_source.read_bytes()
        try:
            auth = json.loads(raw)
            tokens = auth['tokens']
            valid = (auth.get('auth_mode') in (None, 'chatgpt') and not auth.get('OPENAI_API_KEY')
                     and all(isinstance(tokens.get(k), str) and tokens[k]
                             for k in ('id_token', 'access_token', 'refresh_token')))
        except (ValueError, KeyError, TypeError):
            valid = False
        if not valid:
            raise EnvironmentError('Cached ChatGPT file authentication is required; no API-key fallback or login is performed')
        self.temporary = tempfile.TemporaryDirectory(prefix='contextbase-native-home-')
        self.home = Path(self.temporary.name).resolve()
        self.temp_parent = self.home.parent
        try:
            if any(self.home == root or root in self.home.parents for root in self.excluded_roots):
                raise EnvironmentError('Private runtime home must be outside source, work and repository roots')
            _private(self.home)
            destination = self.home / 'auth.json'
            with destination.open('xb') as handle:
                handle.write(raw)
            if os.name != 'nt':
                destination.chmod(0o600)
            self.auth_digest = hashlib.sha256(raw).digest()
            self.context_token = _CURRENT.set(self)
            return self
        except BaseException:
            self.temporary.cleanup()
            raise

    def child_env(self):
        result = dict(os.environ)
        if any(result.get(key) for key in _SECRET_ENV):
            raise EnvironmentError('Native isolation does not support ambient API-key or endpoint overrides')
        result['CODEX_HOME'] = str(self.home)
        return result

    def prepare_role(self, cli, cwd, command, child_env, capability_spec=None):
        from .capabilities import normalize_capabilities, stage_skills, validate_capabilities
        capabilities = validate_capabilities(capability_spec or normalize_capabilities())
        selected = {str(path.resolve()) for path in
                    stage_skills(capabilities, Path(cwd) / '.agents' / 'skills')}
        self.disabled_skills = [path for path in self.disabled_skills if path not in selected]
        # Only -c overrides carry configuration; no inference command is launched.
        overrides = []
        for index, argument in enumerate(command[:-1]):
            if argument in ('-c', '--config'):
                overrides.extend(['-c', command[index + 1]])
        observed = self._probe(cli, cwd, overrides, child_env, self.disabled_skills)
        unwanted = [row['path'] for row in observed['skills']
                    if row['enabled'] and str(Path(row['path']).resolve()) not in selected]
        if unwanted:
            self.disabled_skills = sorted(set(self.disabled_skills + unwanted))
            observed = self._probe(cli, cwd, overrides, child_env, self.disabled_skills)
        enabled = {str(Path(row['path']).resolve()) for row in observed['skills'] if row['enabled']}
        if enabled != selected or observed['instructionSources'] != []:
            raise EnvironmentError('Native bootstrap contains unexpected Skills or file instructions')
        expected, output_limits, allowed_tools = {}, {}, None
        for index in range(0, len(overrides), 2):
            key, separator, text = overrides[index + 1].partition('=')
            prefix, suffix = 'mcp_servers.contextbase.tools.', '.output_token_limit'
            if separator and key.startswith(prefix) and key.endswith(suffix):
                output_limits[key[len(prefix):-len(suffix)]] = json.loads(text)
            if key == 'mcp_servers.contextbase.enabled_tools':
                allowed_tools = sorted(json.loads(text))
            if separator and (key in _CONFIG_KEYS or key.startswith(('features.', 'agents.'))):
                try:
                    expected[key] = json.loads(text)
                except ValueError:
                    raise EnvironmentError('Unsupported role bootstrap configuration encoding: ' + key)
        def setting(key):
            value = observed['config']
            for part in key.split('.'):
                value = value.get(part) if isinstance(value, dict) else None
            return value
        if any(setting(key) != value for key, value in expected.items()):
            raise EnvironmentError('Role bootstrap configuration differs from the actual execution overrides')
        if output_limits and observed.get('mcpToolOutputLimits') != output_limits:
            raise EnvironmentError('Native bootstrap MCP tool output limits differ from execution overrides')
        if allowed_tools is not None:
            servers = observed.get('mcpServers', [])
            if (len(servers) != 1 or servers[0]['name'] != 'contextbase'
                    or servers[0].get('toolsError') or servers[0].get('pluginId')
                    or sorted(servers[0]['tools']) != allowed_tools):
                raise EnvironmentError('Native bootstrap contains an unexpected MCP tool inventory')
        self.probes.append({key: observed[key] for key in ('enabledSkillCount', 'instructionSources', 'config', 'cliVersion')})
        self.probes[-1]['mcpToolOutputLimits'] = observed.get('mcpToolOutputLimits', {})
        self.probes[-1]['mcpServers'] = observed.get('mcpServers', [])
        self.probes[-1]['selectedSkills'] = sorted(selected)
        self.probes[-1]['capabilities'] = capabilities
        return self.skill_arguments(), self.report()

    def skill_arguments(self):
        if not self.disabled_skills:
            return []
        tables = '[' + ','.join('{path=' + json.dumps(path) + ',enabled=false}' for path in self.disabled_skills) + ']'
        return ['-c', 'skills.config=' + tables]

    def _probe(self, cli, cwd, overrides, child_env, disabled):
        additions = []
        if disabled:
            additions = ['-c', 'skills.config=[' + ','.join('{path=' + json.dumps(path) + ',enabled=false}' for path in disabled) + ']']
        return probe(cli, cwd, [*overrides, *additions], child_env)

    def report(self):
        return {'policy': POLICY, 'scopeId': self.identifier, 'authentication': 'copied-cached-chatgpt-file',
                'parentEnvironmentMutated': False, 'originalAuthWritten': False,
                'cleanupComplete': self.cleaned, 'privateAuthCacheChanged': self.auth_changed,
                'probes': list(self.probes),
                'limitation': 'instructionSources and Skills are bootstrap observations, not the complete model request. '
                              'Refreshing the private cached login may rotate a shared refresh token; '
                              'the original cache is never overwritten and no fallback login is performed.'}

    def __exit__(self, *exc):
        try:
            target = self.home / 'auth.json'
            if target.is_file():
                self.auth_changed = hashlib.sha256(target.read_bytes()).digest() != self.auth_digest
        finally:
            _CURRENT.reset(self.context_token)
            if (self.home.parent != self.temp_parent or self.home.is_symlink()
                    or not self.home.name.startswith('contextbase-native-home-')):
                raise EnvironmentError('Unsafe private runtime cleanup target')
            self.temporary.cleanup()
            self.cleaned = not self.home.exists()


@contextmanager
def scope(**kwargs):
    existing = current()
    if existing is not None:
        yield existing
    else:
        with NativeEnvironment(**kwargs) as environment:
            yield environment


def probe(cli, cwd, overrides, child_env):
    command = [str(cli), 'app-server', '--listen', 'stdio://', *overrides]
    options = {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {}
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, encoding='utf-8', env=child_env, cwd=cwd, **options)
    messages = queue.Queue()
    def read_stdout():
        for line in process.stdout:
            try:
                messages.put(json.loads(line))
            except ValueError:
                messages.put({'probeInvalid': True})
    threading.Thread(target=read_stdout, daemon=True).start()
    def read_stderr():
        for _ in process.stderr:
            pass
    threading.Thread(target=read_stderr, daemon=True).start()
    sequence = 0
    def rpc(method, params):
        nonlocal sequence
        sequence += 1
        process.stdin.write(json.dumps({'id': sequence, 'method': method, 'params': params}) + '\n')
        process.stdin.flush()
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            try:
                value = messages.get(timeout=max(.1, deadline - time.monotonic()))
            except queue.Empty:
                break
            if value.get('probeInvalid'):
                raise EnvironmentError('Invalid native bootstrap probe output')
            if value.get('id') == sequence:
                if 'error' in value:
                    raise EnvironmentError('Native bootstrap probe request failed: ' + method)
                return value['result']
        raise EnvironmentError('Native bootstrap probe timeout: ' + method)
    try:
        rpc('initialize', {'clientInfo': {'name': 'contextbase-bootstrap', 'version': '1'},
                           'capabilities': {'experimentalApi': True}})
        process.stdin.write(json.dumps({'method': 'initialized'}) + '\n'); process.stdin.flush()
        config = rpc('config/read', {'includeLayers': False, 'cwd': str(cwd)})['config']
        skills = rpc('skills/list', {'cwds': [str(cwd)], 'forceReload': True})
        if any(row.get('errors') for row in skills.get('data', [])):
            raise EnvironmentError('Native bootstrap Skills discovery failed')
        rows = [{'path': row['path'], 'enabled': row.get('enabled', False)}
                for group in skills.get('data', []) for row in group.get('skills', [])]
        thread = rpc('thread/start', {'cwd': str(cwd), 'ephemeral': True,
                     'approvalPolicy': 'never', 'sandbox': 'read-only'})
        sources = thread.get('instructionSources')
        if not isinstance(sources, list):
            raise EnvironmentError('CLI does not expose bootstrap instruction sources')
        inventory_params = {'limit': 100, 'threadId': thread['thread']['id']}
        inventory = rpc('mcpServerStatus/list', inventory_params)
        if inventory.get('nextCursor'):
            raise EnvironmentError('Native bootstrap MCP inventory exceeds the expected server set')
        servers = [{'name': row['name'], 'pluginId': row.get('pluginId'),
                    'tools': sorted(row.get('tools', {})), 'toolsError': row.get('toolsError')}
                   for row in inventory.get('data', [])]
        tools = config.get('mcp_servers', {}).get('contextbase', {}).get('tools', {})
        limits = {name: row.get('output_token_limit') for name, row in tools.items()
                  if isinstance(row, dict) and 'output_token_limit' in row}
        return {'config': {key: config.get(key) for key in _CONFIG_KEYS}, 'skills': rows,
                'mcpToolOutputLimits': limits,
                'mcpServers': servers,
                'enabledSkillCount': sum(row['enabled'] for row in rows), 'instructionSources': sources,
                'cliVersion': subprocess.check_output([str(cli), '--version'], text=True, **options).strip()}
    finally:
        if process.stdin:
            try:
                process.stdin.close()
            except OSError:
                pass
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill(); process.wait()
