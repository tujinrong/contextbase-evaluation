"""Public project-profile CLI behavior using synthetic sources and inference."""
from __future__ import annotations

from contextlib import contextmanager, redirect_stderr, redirect_stdout
from copy import deepcopy
import importlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_independent_agents import request, simulated_answer


AGENTS = (
    ('discovery', 'contextbase_discovery', 'discovery-agent'),
    ('relationship', 'contextbase_relationship', 'relationship-agent'),
    ('behavior', 'contextbase_behavior', 'behavior-agent'),
)


@contextmanager
def working_directory(path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


class ProjectConfigTests(unittest.TestCase):
    def setUp(self):
        home = Path(__file__).resolve().parents[1] / '.tmp'
        home.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='project-config-', dir=home)
        self.root = Path(self.temporary.name)
        self.project = self.root / 'project'
        self.source = self.project / 'srcs/sample'
        self.source.mkdir(parents=True)
        self.source_file = self.source / 'Registration.cs'
        self.source_file.write_text(
            'class Registration {\n bool Save(int value) { return value > 0; }\n}\n', encoding='utf-8')
        self.request_path = self.project / 'request.json'
        self.request = request()
        self.write_request()
        self.config = self.project / 'project.toml'
        self.profiles = {'csharp': {'source': 'srcs/sample', 'request': 'request.json',
                                   'output': 'spec-reverse', 'work': '.tmp/contextbase/csharp'}}
        self.write_config()
        self.calls = []
        self.statement_suffix = ''
        self.fail_next_verification = False

    def tearDown(self):
        self.temporary.cleanup()

    def write_request(self):
        self.request_path.write_text(json.dumps(self.request, ensure_ascii=False), encoding='utf-8')

    def write_config(self, path=None, profiles=None, default='csharp'):
        path = self.config if path is None else Path(path)
        profiles = self.profiles if profiles is None else profiles
        lines = ['schema = "contextbase-project/1"', 'default_profile = ' + json.dumps(default), '']
        for name, profile in profiles.items():
            lines.append('[profiles.' + name + ']')
            lines.extend(key + ' = ' + json.dumps(value) for key, value in profile.items())
            lines.append('')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('\n'.join(lines), encoding='utf-8')
        return path

    def cli(self, stage, command, *extra, profile=None, config=None, expected=0):
        module = next(item[1] for item in AGENTS if item[0] == stage)
        main = importlib.import_module(module + '.__main__').main
        argv = [command, '--config', str(self.config if config is None else config), *extra]
        if profile is not None:
            argv += ['--profile', profile]
        return self.invoke(main, argv, expected=expected)

    def invoke(self, main, argv, *, expected=0):
        with redirect_stdout(io.StringIO()) as stream, redirect_stderr(io.StringIO()) as errors:
            try:
                code = main(argv)
            except SystemExit as exc:
                code = exc.code
        text = stream.getvalue()
        result = json.loads(text) if text else {'stderr': errors.getvalue()}
        self.assertEqual(expected, code, (argv, result, errors.getvalue()))
        return result

    def provider(self, workspace, job, prompt, schema, timeout):
        context = json.loads(prompt[prompt.index('{"request":'):])
        self.calls.append(context)
        answer = simulated_answer(context)
        for record in answer.get('records', []):
            record['statement'] += self.statement_suffix
        if context['task']['operation'] == 'verify' and self.fail_next_verification:
            self.fail_next_verification = False
            answer['checks'][0]['status'] = 'fail'
        return {'exit_code': 0, 'metadata': {'status': 'passed'}, 'answer': answer}

    def run_agent(self, stage, *, expected=0, profile=None):
        with patch('contextbase_runtime.provider.run_job', side_effect=self.provider):
            return self.cli(stage, 'run', '--inline-sources', expected=expected, profile=profile)

    def paths(self, stage, **kwargs):
        return self.cli(stage, 'paths', **kwargs)

    def accepted_discovery(self):
        self.cli('discovery', 'init')
        self.assertEqual('complete', self.run_agent('discovery')['status'])
        return self.paths('discovery')

    def publish_discovery(self):
        paths = self.accepted_discovery()
        result = self.cli('discovery', 'export')
        self.assertEqual('exported', result['status'])
        return paths

    def revise_discovery(self, suffix):
        self.cli('discovery', 'revise', '--requirements', 'catalog', '--reason', 'Synthetic source re-investigation.')
        self.statement_suffix = suffix
        self.assertEqual('complete', self.run_agent('discovery')['status'])

    def test_paths_are_read_only_and_resolve_against_config_not_cwd(self):
        before = {p.relative_to(self.project).as_posix(): p.read_bytes()
                  for p in self.project.rglob('*') if p.is_file()}
        with patch('contextbase_runtime.provider.run_job') as provider:
            resolved = self.paths('discovery')
            elsewhere = self.root / 'unrelated-cwd'
            elsewhere.mkdir()
            with working_directory(elsewhere):
                relative_config = os.path.relpath(self.config, elsewhere)
                again = self.paths('discovery', config=relative_config)
            provider.assert_not_called()
        self.assertEqual(resolved, again)
        self.assertEqual('csharp', resolved['profile'])
        self.assertEqual(self.source, Path(resolved['source']))
        self.assertEqual(self.request_path, Path(resolved['request']))
        self.assertEqual(self.project / '.tmp/contextbase/csharp/discovery-agent', Path(resolved['work']))
        self.assertEqual(self.project / 'spec-reverse/discovery-agent/contextbase.json', Path(resolved['output']))
        self.assertIsNone(resolved['handoff'])
        self.assertFalse(Path(resolved['work']).exists())
        self.assertFalse((self.project / 'spec-reverse').exists())
        after = {p.relative_to(self.project).as_posix(): p.read_bytes()
                 for p in self.project.rglob('*') if p.is_file()}
        self.assertEqual(before, after)

    def test_default_profile_and_explicit_profile_have_separate_paths(self):
        self.profiles['java'] = {'source': 'srcs/other', 'request': 'request.json',
                                 'output': 'other-results', 'work': '.tmp/contextbase/java'}
        self.write_config()
        selected = self.paths('relationship', profile='java')
        self.assertEqual('java', selected['profile'])
        self.assertEqual(self.project / 'srcs/other', Path(selected['source']))
        self.assertEqual(self.project / '.tmp/contextbase/java/relationship-agent', Path(selected['work']))
        self.assertEqual(self.project / 'other-results/relationship-agent/contextbase.json', Path(selected['output']))
        self.assertEqual(self.project / 'other-results/discovery-agent/contextbase.json', Path(selected['handoff']))
        self.assertEqual('csharp', self.paths('relationship')['profile'])
        self.cli('relationship', 'paths', profile='missing', expected=1)

    def test_all_three_clis_accept_late_handoffs_without_running_upstream_agents(self):
        for stage, module, name in AGENTS:
            self.assertEqual(stage, self.cli(stage, 'init')['stage'])
        for stage in ('relationship', 'behavior'):
            result = self.run_agent(stage, expected=2)
            self.assertEqual('needs-prerequisites', result['status'])
        self.assertEqual([], self.calls)
        outputs = []
        works = []
        for index, (stage, module, name) in enumerate(AGENTS):
            start = len(self.calls)
            self.assertEqual('complete', self.run_agent(stage)['status'])
            local = self.calls[start:]
            self.assertEqual([stage], [item['task']['stage'] for item in local
                                       if item['task']['operation'] == 'extract'])
            if index:
                self.assertEqual('verify', local[0]['task']['operation'])
                self.assertIn('externalPremises', local[0])
            output = self.cli(stage, 'export')
            resolved = self.paths(stage)
            destination = self.project / 'spec-reverse' / name / 'contextbase.json'
            self.assertEqual(destination, Path(output['output']))
            self.assertTrue(destination.is_file())
            self.assertTrue(destination.with_name('target.json').is_file())
            outputs.append(destination)
            works.append(Path(resolved['work']))
        self.assertEqual(3, len(set(outputs)))
        self.assertEqual(3, len(set(works)))
        self.assertEqual(8, len(self.calls))
        self.assertEqual(8, len({item['task']['contextId'] for item in self.calls}))
        final = json.loads(outputs[-1].read_text(encoding='utf-8'))
        self.assertEqual(['catalog', 'links', 'rules'], final['payload']['acceptedRequirements'])

    def test_config_cannot_be_mixed_with_explicit_path_arguments(self):
        cases = [('discovery', 'init', '--source', str(self.source)),
                 ('discovery', 'init', '--request', str(self.request_path)),
                 ('discovery', 'status', '--work', str(self.project / 'manual-work')),
                 ('relationship', 'init', '--handoff', str(self.project / 'handoff.json')),
                 ('discovery', 'export', '--output', str(self.project / 'manual-result.json'))]
        with patch('contextbase_runtime.provider.run_job') as provider:
            for stage, command, flag, value in cases:
                with self.subTest(flag=flag):
                    self.cli(stage, command, flag, value, expected=1)
            provider.assert_not_called()
        self.assertFalse((self.project / '.tmp').exists())

    def test_updated_upstream_result_invalidates_existing_receiver_for_execution_and_export(self):
        for stage, module, name in AGENTS:
            self.cli(stage, 'init')
            self.run_agent(stage)
            self.cli(stage, 'export')
        relationship_output = Path(self.paths('relationship')['output'])
        previous = relationship_output.read_bytes()
        discovery_output = Path(self.paths('discovery')['output'])
        upstream_before = discovery_output.read_bytes()
        self.revise_discovery(' Updated upstream evidence.')
        self.cli('discovery', 'export')
        self.assertNotEqual(upstream_before, discovery_output.read_bytes())
        with patch('contextbase_runtime.provider.run_job') as provider:
            for command, extra in (('run', ['--inline-sources']),
                                   ('retry', ['--feedback', 'stale-feedback', '--inline-sources']),
                                   ('export', [])):
                with self.subTest(command=command):
                    result = self.cli('relationship', command, *extra, expected=1)
                    self.assertIn('stale', json.dumps(result).lower())
            self.assertEqual('relationship', self.cli('relationship', 'status')['stage'])
            self.assertEqual('cancelled', self.cli('relationship', 'cancel')['status'])
            self.assertEqual('active', self.cli('relationship', 'resume')['status'])
            # The fixed discovery result is present, so its newer fingerprint
            # also invalidates the behavior workspace's sealed ancestor evidence.
            for command in ('run', 'export'):
                result = self.cli('behavior', command, expected=1)
                self.assertIn('stale', json.dumps(result).lower())
            provider.assert_not_called()
        self.assertEqual(previous, relationship_output.read_bytes())

    def test_retracted_ancestor_obligation_invalidates_behavior_even_when_audit_is_unchanged(self):
        self.request['goal']['requirements'].append({
            'id': 'other_catalog', 'stage': 'discovery', 'scope': 'other-registration',
            'question': 'List a separately accepted synthetic function.', 'requires': []})
        self.write_request()
        for stage, module, name in AGENTS:
            self.cli(stage, 'init')
            self.assertEqual('complete', self.run_agent(stage)['status'])
            self.cli(stage, 'export')
        root_output = Path(self.paths('discovery')['output'])
        old_root = json.loads(root_output.read_text(encoding='utf-8'))
        self.assertEqual({'catalog', 'other_catalog'}, set(old_root['payload']['acceptedRequirements']))
        behavior_output = Path(self.paths('behavior')['output'])
        previous_behavior = behavior_output.read_bytes()
        with patch('contextbase_runtime.provider.run_job') as provider:
            # Withdrawing catalog needs no new candidate or review, so history
            # remains identical although the authoritative accepted set changes.
            self.cli('discovery', 'revise', '--requirements', 'catalog',
                     '--reason', 'Withdraw the accepted catalog obligation.')
            self.assertEqual('exported', self.cli('discovery', 'export')['status'])
            new_root = json.loads(root_output.read_text(encoding='utf-8'))
            self.assertEqual(['other_catalog'], new_root['payload']['acceptedRequirements'])
            self.assertEqual(old_root['payload']['audit'], new_root['payload']['audit'])
            self.assertNotEqual(old_root['sha256'], new_root['sha256'])
            for command in ('run', 'export'):
                with self.subTest(command=command):
                    result = self.cli('behavior', command, expected=1)
                    self.assertIn('stale', json.dumps(result).lower())
            provider.assert_not_called()
        self.assertEqual(previous_behavior, behavior_output.read_bytes())

    def test_profile_switch_cannot_reuse_an_initialized_workspace(self):
        self.cli('discovery', 'init')
        self.profiles['other'] = deepcopy(self.profiles['csharp'])
        self.write_config()
        with patch('contextbase_runtime.provider.run_job') as provider:
            self.cli('discovery', 'status', profile='other', expected=1)
            provider.assert_not_called()

    def test_source_path_change_cannot_rebind_existing_workspace(self):
        self.cli('discovery', 'init')
        other = self.project / 'srcs/other'
        other.mkdir()
        (other / 'Registration.cs').write_bytes(self.source_file.read_bytes())
        self.profiles['csharp']['source'] = 'srcs/other'
        self.write_config()
        with patch('contextbase_runtime.provider.run_job') as provider:
            self.cli('discovery', 'status', expected=1)
            provider.assert_not_called()

    def test_request_goal_change_cannot_rebind_existing_workspace(self):
        self.cli('discovery', 'init')
        self.request['goal']['question'] = 'A different analysis goal.'
        self.write_request()
        with patch('contextbase_runtime.provider.run_job') as provider:
            self.cli('discovery', 'run', '--inline-sources', expected=1)
            provider.assert_not_called()

    def test_overlapping_source_work_and_output_trees_are_refused_before_mutation(self):
        cases = [{'work': 'srcs/sample/.work'}, {'output': 'srcs/sample/.results'},
                 {'work': 'shared', 'output': 'shared'}, {'work': 'nested', 'output': 'nested/results'}]
        original = deepcopy(self.profiles['csharp'])
        for changes in cases:
            with self.subTest(changes=changes), patch('contextbase_runtime.provider.run_job') as provider:
                self.profiles['csharp'] = {**original, **changes}
                self.write_config()
                self.cli('discovery', 'paths', expected=1)
                provider.assert_not_called()
        self.assertFalse((self.source / '.work').exists())
        self.assertFalse((self.source / '.results').exists())
        self.assertFalse((self.project / 'shared').exists())
        self.assertFalse((self.project / 'nested').exists())

    def test_request_input_cannot_be_beneath_work_or_output(self):
        for location in ('.tmp/contextbase/csharp/request.json', 'spec-reverse/request.json'):
            with self.subTest(location=location):
                target = self.project / location
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(self.request_path.read_bytes())
                self.profiles['csharp']['request'] = location
                self.write_config()
                before = target.read_bytes()
                self.cli('discovery', 'paths', expected=1)
                self.assertEqual(before, target.read_bytes())

    def test_configuration_input_cannot_be_beneath_work_or_output(self):
        for tree in ('.tmp/contextbase/csharp', 'spec-reverse'):
            with self.subTest(tree=tree):
                nested = self.project / tree / 'nested-config.toml'
                profile = {key: str(self.project / value) for key, value in self.profiles['csharp'].items()}
                self.write_config(path=nested, profiles={'csharp': profile})
                before = nested.read_bytes()
                self.cli('discovery', 'paths', config=nested, expected=1)
                self.assertEqual(before, nested.read_bytes())

    def test_changed_source_cannot_use_a_stale_upstream_handoff(self):
        self.publish_discovery()
        self.source_file.write_text('class Registration {\n bool Save(int value) { return value > 1; }\n}\n',
                                    encoding='utf-8')
        with patch('contextbase_runtime.provider.run_job') as provider:
            self.cli('relationship', 'init', expected=1)
            provider.assert_not_called()

    def test_wrong_profile_upstream_result_is_not_accepted(self):
        self.publish_discovery()
        self.profiles['other'] = {**self.profiles['csharp'], 'work': '.tmp/contextbase/other'}
        self.write_config()
        with patch('contextbase_runtime.provider.run_job') as provider:
            self.cli('relationship', 'init', profile='other', expected=1)
            provider.assert_not_called()

    def test_config_export_is_idempotent_and_same_owner_can_publish_a_new_revision(self):
        paths = self.publish_discovery()
        artifact = Path(paths['output'])
        marker = artifact.with_name('target.json')
        first = artifact.read_bytes()
        owner = marker.read_bytes()
        with patch('contextbase_runtime.provider.run_job') as provider:
            repeated = self.cli('discovery', 'export')
            provider.assert_not_called()
        self.assertTrue(repeated['unchanged'])
        self.assertEqual(first, artifact.read_bytes())
        self.assertEqual(owner, marker.read_bytes())
        self.revise_discovery(' Revised synthetic detail.')
        changed = self.cli('discovery', 'export')
        self.assertFalse(changed['unchanged'])
        self.assertNotEqual(first, artifact.read_bytes())
        self.assertEqual(owner, marker.read_bytes())
        self.assertEqual([artifact], list(artifact.parent.glob('contextbase*.json')))

    def test_another_profile_cannot_overwrite_owned_fixed_results(self):
        paths = self.publish_discovery()
        artifact = Path(paths['output'])
        marker = artifact.with_name('target.json')
        before = (artifact.read_bytes(), marker.read_bytes())
        self.profiles['other'] = {**self.profiles['csharp'], 'work': '.tmp/contextbase/other'}
        self.write_config()
        self.cli('discovery', 'init', profile='other')
        self.run_agent('discovery', profile='other')
        self.cli('discovery', 'export', profile='other', expected=1)
        self.assertEqual(before, (artifact.read_bytes(), marker.read_bytes()))

    def test_changed_goal_cannot_overwrite_owned_fixed_results(self):
        paths = self.publish_discovery()
        artifact = Path(paths['output'])
        marker = artifact.with_name('target.json')
        before = (artifact.read_bytes(), marker.read_bytes())
        self.request['goal']['question'] = 'A different synthetic goal.'
        self.write_request()
        self.profiles['csharp']['work'] = '.tmp/contextbase/new-goal'
        self.write_config()
        self.cli('discovery', 'init')
        self.run_agent('discovery')
        self.cli('discovery', 'export', expected=1)
        self.assertEqual(before, (artifact.read_bytes(), marker.read_bytes()))

    def test_another_source_target_cannot_overwrite_owned_fixed_results(self):
        paths = self.publish_discovery()
        artifact = Path(paths['output'])
        marker = artifact.with_name('target.json')
        before = (artifact.read_bytes(), marker.read_bytes())
        another = self.project / 'srcs/another-target'
        another.mkdir()
        (another / 'Registration.cs').write_bytes(self.source_file.read_bytes())
        self.profiles['csharp'].update(source='srcs/another-target', work='.tmp/contextbase/another-target')
        self.write_config()
        self.cli('discovery', 'init')
        self.run_agent('discovery')
        self.cli('discovery', 'export', expected=1)
        self.assertEqual(before, (artifact.read_bytes(), marker.read_bytes()))

    def test_atomic_result_update_failure_preserves_old_artifact_and_owner(self):
        paths = self.publish_discovery()
        artifact = Path(paths['output'])
        marker = artifact.with_name('target.json')
        before = (artifact.read_bytes(), marker.read_bytes())
        self.revise_discovery(' Detail pending publication.')
        replace = os.replace
        def interrupted(source, destination):
            if Path(destination) == artifact:
                raise OSError('Simulated fixed-result replacement interruption')
            return replace(source, destination)
        with patch('contextbase_runtime.config.os.replace', side_effect=interrupted):
            self.cli('discovery', 'export', expected=1)
        self.assertEqual(before, (artifact.read_bytes(), marker.read_bytes()))
        self.assertFalse((artifact.parent / '.tmp/publication.lock').exists())
        self.assertEqual([], list((artifact.parent / '.tmp').glob('publish-*.json')))
        self.cli('discovery', 'export')
        self.assertNotEqual(before[0], artifact.read_bytes())

    def test_config_status_index_cancel_resume_and_explicit_retry_remain_public(self):
        self.cli('discovery', 'init')
        with patch('contextbase_runtime.provider.run_job') as provider:
            self.assertEqual('discovery', self.cli('discovery', 'status')['stage'])
            self.assertEqual('complete', self.cli('discovery', 'index')['files'][0]['status'])
            self.assertEqual('cancelled', self.cli('discovery', 'cancel')['status'])
            self.assertEqual('active', self.cli('discovery', 'resume')['status'])
            provider.assert_not_called()
        self.fail_next_verification = True
        failed = self.run_agent('discovery', expected=2)
        self.assertEqual('needs-investigation', failed['status'])
        feedback = failed['pending']['candidate']
        with patch('contextbase_runtime.provider.run_job', side_effect=self.provider):
            retried = self.cli('discovery', 'retry', '--feedback', feedback, '--inline-sources')
        self.assertEqual('complete', retried['status'])
        self.assertEqual(feedback, self.calls[-2]['task']['feedback'])

    def test_manual_export_still_requires_a_fresh_destination(self):
        main = importlib.import_module('contextbase_discovery.__main__').main
        work = self.project / 'manual-work'
        output = self.project / 'manual-export.json'
        self.invoke(main, ['init', '--source', str(self.source), '--request', str(self.request_path),
                           '--work', str(work)])
        with patch('contextbase_runtime.provider.run_job', side_effect=self.provider):
            self.invoke(main, ['run', '--work', str(work), '--inline-sources'])
        args = ['export', '--work', str(work), '--output', str(output)]
        self.invoke(main, args)
        before = output.read_bytes()
        self.invoke(main, args, expected=1)
        self.assertEqual(before, output.read_bytes())


if __name__ == '__main__':
    unittest.main()
