"""Installed public CLIs in isolated processes; all inference is synthetic.

Each receiver gets only a portable JSON handoff and a new source root. This
proves process/import/file independence, not live-model or business accuracy.
"""
from __future__ import annotations

import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


AGENTS = (
    ('discovery', 'contextbase_discovery', 'contextbase-discovery'),
    ('relationship', 'contextbase_relationship', 'contextbase-relationship'),
    ('behavior', 'contextbase_behavior', 'contextbase-behavior'),
)

# The child deliberately does not import test_independent_agents: its imports
# would load all three agent implementations and conceal package coupling.
CHILD = r'''
import importlib.abc
import importlib.metadata
import io
import json
import os
from pathlib import Path
import sys
from contextlib import redirect_stdout
from unittest.mock import patch

config = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
if list(Path.cwd().iterdir()):
    raise AssertionError('The process must start from an empty working directory')
blocked = {'contextbase', 'docsite', 'specgen'} | set(config['otherPackages'])
allowed = set(sys.stdlib_module_names) | set(sys.builtin_module_names) | {
    config['module'], 'contextbase_runtime', 'jsonschema', 'jsonschema_specifications',
    'attrs', 'attr', 'referencing', 'rpds', 'typing_extensions',
    'tree_sitter', 'tree_sitter_c_sharp', 'tree_sitter_java'}
attempted_imports = []
declined_optional_imports = []
class IsolatedImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        root = fullname.split('.')[0]
        if root in blocked:
            attempted_imports.append(fullname)
            raise ImportError('Forbidden package in isolated agent: ' + fullname)
        if root not in allowed:
            declined_optional_imports.append(fullname)
            raise ImportError('Package outside the runtime dependency allowlist: ' + fullname)
sys.meta_path.insert(0, IsolatedImports())

forbidden = [os.path.normcase(os.path.abspath(p)) for p in config['forbiddenPaths']]
file_attempts = []
def audit(event, args):
    if event not in {'open', 'os.listdir', 'os.scandir'} or not args:
        return
    value = args[0]
    if not isinstance(value, (str, bytes, os.PathLike)):
        return
    path = os.path.normcase(os.path.abspath(os.fsdecode(value)))
    if any(path == prefix or path.startswith(prefix + os.sep) for prefix in forbidden):
        file_attempts.append({'event': event, 'path': path})
        raise AssertionError('The receiver accessed a producer path: ' + path)
sys.addaudithook(audit)

entries = [entry for entry in importlib.metadata.distribution(config['distribution']).entry_points
           if entry.group == 'console_scripts']
if len(entries) != 1 or entries[0].name != config['distribution']:
    raise AssertionError('The installed agent must own its console entry point')
main = entries[0].load()
contexts = []
def bind_facts(context, answer, evidence):
    task = context['task']
    if 'sourceFactsSha256' not in task:
        return
    answer['sourceFactsSha256'] = task['sourceFactsSha256']
    if task['operation'] == 'verify':
        answer['factUsageCheck'] = {'status': 'pass', 'reason': 'Synthetic independent fact relevance check.',
                                   'evidence': [evidence]}
        return
    structure = context['structure']
    facts = [dict(zip(structure[key]['columns'], row))
        for key in ('symbols', 'calls', 'entries', 'imports') for row in structure[key]['rows']]
    answer['factUsage'] = []
    for record in answer['records']:
        available = [fact['id'] for fact in facts if any(
            structure['files'][fact['file']]['path'] == ref['path']
            and fact['startLine'] <= ref['endLine'] and ref['startLine'] <= fact['endLine']
            for ref in record['evidence'])]
        answer['factUsage'].append({'recordKey': record['key'], 'factIds': available[:1],
            'reason': 'Synthetic overlapping source fact.' if available else 'No indexed fact overlaps this source evidence.'})

def synthetic(workspace, job, prompt, schema, timeout):
    context = json.loads(prompt[prompt.index('{"request":'):])
    contexts.append(context)
    task = context['task']
    entry = context['inventory']['files'][0]
    evidence = {'path': entry['path'], 'startLine': 1, 'endLine': 2, 'sha256': entry['sha256']}
    if task['operation'] == 'verify':
        answer = {'taskId': task['id'], 'candidateSha256': task['candidate'],
            'viewSha256': task['viewSha256'],
            'checks': [{'requirement': key, 'status': 'pass', 'reason': 'Synthetic source check.',
                        'evidence': [evidence]} for key in task['requirements']],
            'unknownChecks': [{'unknownId': item['id'], 'unknownSha256': item['sha256'],
                'status': 'non-blocking', 'blocksRequirements': [],
                'reason': 'Synthetic scope check.', 'evidence': [evidence]}
                for item in task['unknownBindings']], 'findings': [], 'unknowns': []}
        if task.get('catalogPolicy') == 'contextbase-catalog/1':
            answer['classificationChecks'] = [
                {'key': item['key'], 'recordSha256': item['sha256'], 'status': 'pass',
                 'reason': 'Synthetic classification check.', 'evidence': [evidence]}
                for item in task['classificationBindings']]
            assigned = set(task['requirements'])
            scopes = list(dict.fromkeys(item['scope'] for item in task['goalRequirements']
                if item['id'] in assigned and item['stage'] == 'discovery'))
            answer['scopeChecks'] = [{'scope': scope, 'status': 'pass',
                'reason': 'Synthetic scope coverage check.', 'evidence': [evidence]} for scope in scopes]
    else:
        obligations = {item['id']: item for item in task['goalRequirements']}
        records = [{'key': key + '.record', 'ownerRequirement': key,
            'kind': {'discovery': 'function', 'relationship': 'relation', 'behavior': 'fact'}[task['stage']],
            'name': key, 'statement': 'Synthetic source claim for ' + key,
            'basis': 'observed-source', 'evidence': [evidence],
            'dependsOn': [dep + '.record' for dep in obligations[key]['requires']]}
            for key in task['requirements']]
        if task.get('catalogPolicy') == 'contextbase-catalog/1':
            for item in records:
                key = item['ownerRequirement']
                item['classification'] = {
                    'category': 'main', 'scope': obligations[key]['scope'], 'area': 'Synthetic area',
                    'actors': ['Synthetic operator'], 'businessObject': 'Synthetic record',
                    'purpose': 'Process the record', 'trigger': 'Submit', 'outcome': 'Processed',
                    'rationale': 'Observed source responsibility', 'alternative': 'Considered an internal operation',
                    'entryRefs': [key + '.entry']}
            records += [{'key': key + '.entry', 'ownerRequirement': key, 'kind': 'entry', 'name': key + ' entry',
                'statement': 'Synthetic source entry for ' + key, 'basis': 'observed-source',
                'evidence': [evidence], 'dependsOn': [], 'classification': None} for key in task['requirements']]
        answer = {'taskId': task['id'], 'records': records,
            'coverage': [{'requirement': key, 'status': 'supported',
                          'recordKeys': [key + '.record'] + ([key + '.entry'] if task.get('catalogPolicy') == 'contextbase-catalog/1' else []),
                          'evidence': [evidence]} for key in task['requirements']],
            'unknowns': [], 'followups': []}
    bind_facts(context, answer, evidence)
    return {'answer': answer, 'exit_code': 0, 'metadata': {'status': 'passed'}}

commands = []
def invoke(argv):
    with redirect_stdout(io.StringIO()) as stream:
        code = main(argv)
    output = json.loads(stream.getvalue())
    commands.append({'command': argv[0], 'exitCode': code, 'result': output})
    return code, output

args = ['init', '--source', config['source'], '--request', config['request'], '--work', config['work']]
if config['handoff']:
    args += ['--handoff', config['handoff']]
with patch('contextbase_runtime.provider.run_job', side_effect=synthetic):
    code, initialized = invoke(args)
    if code != 0:
        raise AssertionError(initialized)
    code, result = invoke(['run', '--work', config['work'], '--inline-sources'])
    if config['missingPrerequisites']:
        if code != 2 or result['status'] != 'needs-prerequisites' or contexts:
            raise AssertionError('Missing prerequisites must stop before any inference')
    else:
        if code != 0 or result['status'] != 'complete':
            raise AssertionError(result)
        code, exported = invoke(['export', '--work', config['work'], '--output', config['output']])
        if code != 0:
            raise AssertionError(exported)
    code, status = invoke(['status', '--work', config['work']])
    if code != 0:
        raise AssertionError(status)
loaded = sorted(name for name in sys.modules if name.split('.')[0] in blocked)
if attempted_imports or loaded or file_attempts:
    raise AssertionError({'imports': attempted_imports, 'loaded': loaded, 'paths': file_attempts})
report = {'pid': os.getpid(), 'stage': config['stage'], 'commands': commands,
          'contexts': contexts, 'status': status, 'forbiddenImports': attempted_imports,
          'loadedForbiddenPackages': loaded, 'producerPathAccesses': file_attempts,
          'declinedOptionalImports': declined_optional_imports,
          'consoleScript': {'name': entries[0].name, 'value': entries[0].value}}
Path(config['report']).write_text(json.dumps(report, ensure_ascii=False), encoding='utf-8')
'''


def request():
    return {'schema': 'contextbase-analysis/2', 'projectId': 'synthetic-process-isolation',
        'goal': {'id': 'inspect', 'question': 'Inspect a synthetic registration flow.',
            'requirements': [
                {'id': 'catalog', 'stage': 'discovery', 'scope': 'registration',
                 'question': 'Find declared processing.', 'requires': []},
                {'id': 'links', 'stage': 'relationship', 'scope': 'registration',
                 'question': 'Find its connections.', 'requires': ['catalog']},
                {'id': 'rules', 'stage': 'behavior', 'scope': 'registration',
                 'question': 'Find its conditions.', 'requires': ['links']}]},
        'allowedPaths': ['.'], 'excludedPaths': []}


class AgentIsolationTests(unittest.TestCase):
    def setUp(self):
        home = Path(__file__).resolve().parents[1] / '.tmp'
        home.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='agent-isolation-', dir=home)
        self.root = Path(self.temporary.name)
        self.request_path = self.root / 'request.json'
        self.request_path.write_text(json.dumps(request()), encoding='utf-8')
        self.forbidden = []

    def tearDown(self):
        self.temporary.cleanup()

    def launch(self, descriptor, handoff=None, *, missing=False):
        stage, module, distribution = descriptor
        source = self.root / ('input-' + stage)
        source.mkdir()
        (source / 'Registration.cs').write_text(
            'class Registration {\n bool Save(int value) { return value > 0; }\n}\n', encoding='utf-8')
        cwd = self.root / ('empty-cwd-' + stage)
        cwd.mkdir()
        work = self.root / ('work-' + stage)
        output = self.root / (stage + '-handoff.json')
        report_path = self.root / (stage + '-report.json')
        config = {'stage': stage, 'module': module, 'distribution': distribution,
            'otherPackages': [item[1] for item in AGENTS if item[0] != stage],
            'source': str(source), 'work': str(work), 'request': str(self.request_path),
            'handoff': str(handoff) if handoff else None, 'output': str(output),
            'report': str(report_path), 'missingPrerequisites': missing,
            'forbiddenPaths': list(self.forbidden)}
        config_path = self.root / (stage + '-bootstrap.json')
        config_path.write_text(json.dumps(config), encoding='utf-8')
        python = sys.executable
        environments = os.environ.get('CONTEXTBASE_ISOLATED_PYTHONS_DIR')
        if environments:
            executable = Path(environments).expanduser() / stage / (
                'Scripts/python.exe' if os.name == 'nt' else 'bin/python')
            self.assertTrue(executable.is_file(), 'Missing isolated agent interpreter: ' + str(executable))
            # Keep a POSIX venv's bin/python symlink rather than resolving it to
            # the base interpreter, which would lose the isolated site-packages.
            python = str(executable.absolute())
        completed = subprocess.run([python, '-I', '-X', 'utf8', '-c', CHILD, str(config_path)],
            cwd=cwd, capture_output=True, text=True, encoding='utf-8', timeout=180,
            shell=False, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        self.assertEqual([], list(cwd.iterdir()), 'CLI must use explicit paths rather than its current directory')
        report = json.loads(report_path.read_text(encoding='utf-8'))
        self.assertEqual([], report['forbiddenImports'])
        self.assertEqual([], report['loadedForbiddenPackages'])
        self.assertEqual([], report['producerPathAccesses'])
        self.assertEqual(distribution, report['consoleScript']['name'])
        self.assertEqual(module + '.__main__:main', report['consoleScript']['value'])
        return report, source, work, output

    def retire_producer(self, source, work):
        """The producer process has exited; old and moved paths are denied later."""
        retired = self.root / 'unavailable-producers'
        retired.mkdir(exist_ok=True)
        for original in (source, work):
            destination = retired / original.name
            original.rename(destination)
            self.assertFalse(original.exists())
            self.forbidden += [str(original), str(destination)]

    def test_three_installed_clis_transfer_without_other_agents_or_producer_paths(self):
        reports = []
        roots = []
        handoff = None
        for index, descriptor in enumerate(AGENTS):
            report, source, work, handoff = self.launch(descriptor, handoff)
            reports.append(report)
            roots.append(source)
            calls = report['contexts']
            extracts = [item for item in calls if item['task']['operation'] == 'extract']
            self.assertEqual([descriptor[0]], [item['task']['stage'] for item in extracts])
            self.assertTrue(all(item['agent']['stage'] == descriptor[0] for item in calls))
            if index:
                self.assertEqual('verify', calls[0]['task']['operation'])
                self.assertEqual(AGENTS[index - 1][0], calls[0]['task']['stage'])
                self.assertIn('externalPremises', calls[0])
                prior_ids = ['catalog'] if index == 1 else ['catalog', 'links']
                for identifier in prior_ids:
                    self.assertEqual('external-reverified', report['status']['receipts'][identifier]['origin'])
            payload = json.loads(handoff.read_text(encoding='utf-8'))
            self.assertNotIn('sourceRoot', payload['payload']['source'])
            encoded = json.dumps(payload)
            for producer_path in [*self.forbidden, str(source), str(work)]:
                self.assertNotIn(producer_path.replace('\\', '\\\\'), encoded)
            for producer_path in self.forbidden:
                self.assertNotIn(producer_path.replace('\\', '\\\\'), json.dumps(calls))
            # launch() used subprocess.run, so this producer has already exited.
            self.retire_producer(source, work)
        self.assertEqual(3, len({str(path.resolve()) for path in roots}))
        contexts = [item['task']['contextId'] for report in reports for item in report['contexts']]
        self.assertEqual(8, len(contexts))
        self.assertEqual(8, len(set(contexts)))
        self.assertEqual([2, 3, 3], [len(report['contexts']) for report in reports])
        self.assertEqual(['catalog', 'links', 'rules'], payload['payload']['acceptedRequirements'])
        self.assertEqual(4, len(payload['payload']['records']))

    def test_later_installed_clis_stop_before_provider_without_handoff(self):
        for descriptor in AGENTS[1:]:
            with self.subTest(stage=descriptor[0]):
                report, source, work, output = self.launch(descriptor, missing=True)
                run = next(item for item in report['commands'] if item['command'] == 'run')
                self.assertEqual(2, run['exitCode'])
                self.assertEqual('needs-prerequisites', run['result']['status'])
                self.assertEqual([], report['contexts'])
                self.assertFalse(output.exists())
                self.assertEqual([], report['status']['acceptedRequirements'])

    def test_installed_metadata_declares_only_runtime_and_agent_owned_entrypoints(self):
        for stage, module, distribution in AGENTS:
            with self.subTest(stage=stage):
                installed = importlib.metadata.distribution(distribution)
                self.assertEqual(['contextbase-runtime==0.1.0'], installed.requires)
                entries = [entry for entry in installed.entry_points if entry.group == 'console_scripts']
                self.assertEqual([(distribution, module + '.__main__:main')],
                                 [(entry.name, entry.value) for entry in entries])
        runtime = importlib.metadata.distribution('contextbase-runtime')
        self.assertEqual([], [entry for entry in runtime.entry_points if entry.group == 'console_scripts'])


if __name__ == '__main__':
    unittest.main()
