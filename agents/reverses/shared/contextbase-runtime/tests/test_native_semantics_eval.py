"""The semantic harness preserves blind inputs and never equates acceptance with truth."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from contextbase_runtime import contracts as c
from contextbase_runtime.roles import VERSION as ROLE_VERSION


RUNTIME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('evaluate_native_semantics', RUNTIME / 'tools/evaluate_native_semantics.py')
evaluation = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evaluation)


class NativeSemanticsEvaluationTests(unittest.TestCase):
    def setUp(self):
        home = RUNTIME / '.tmp'
        home.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=home)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.fixture = self.root / 'fixture'
        shutil.copytree(evaluation.FIXTURE, self.fixture)
        self.roles = {}
        for role in ('analysis', 'verification'):
            instruction = self.root / f'{role}.md'
            text = f'Independently inspect authorized source as {role}.\n'
            instruction.write_bytes(text.encode('utf-8'))
            self.roles[role] = {
                'schema': ROLE_VERSION, 'id': role, 'operation': role,
                'instructions_path': str(instruction.resolve()), 'instructions_text': text,
                'instructions_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
                'model': 'fixture-model', 'model_reasoning_effort': 'high',
                'configuration_sources': {'model': 'fixture', 'model_reasoning_effort': 'fixture'},
            }

    def run_arm(self, name, **kwargs):
        return evaluation.run_evaluation(self.root / name, self.roles, fixture=self.fixture,
                                         fingerprint=lambda: 'frozen-test-engine', **kwargs)

    def test_dry_run_does_not_create_agent_and_seals_only_source(self):
        class ForbiddenFactory:
            @classmethod
            def create(cls, *args, **kwargs):
                raise AssertionError('Dry run invoked agent creation')
        report = self.run_arm('dry', agent_factory=ForbiddenFactory)
        self.assertEqual('prepared', report['status'])
        self.assertEqual('dry-run-no-provider-calls', report['mode'])
        self.assertFalse((self.root / 'dry/analysis').exists())
        manifest = evaluation.load(self.root / 'dry/input-snapshot/manifest.json')
        self.assertEqual(['InputRules.cs'], [row['path'] for row in manifest['files']])
        self.assertFalse(report['judgingDeliveredToModel'])
        self.assertFalse(report['sourceProgramsExecuted'])
        self.assertEqual([], report['providers'])
        self.assertEqual('pending-manual-review', report['semanticVerdict'])

    def test_judging_must_match_source_before_any_session_exists(self):
        source = self.fixture / 'source/InputRules.cs'
        source.write_text(source.read_text('utf-8') + '// changed input\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'frozen source bytes'):
            self.run_arm('changed')
        self.assertFalse((self.root / 'changed').exists())

    def test_answers_accidentally_inside_source_are_rejected(self):
        shutil.copyfile(self.fixture / 'judging.json', self.fixture / 'source/judging.json')
        with self.assertRaisesRegex(ValueError, 'only regular C# files'):
            self.run_arm('leaked')
        self.assertFalse((self.root / 'leaked').exists())

    def test_same_work_cannot_overwrite_a_previous_arm(self):
        self.run_arm('existing')
        report_before = (self.root / 'existing/report.json').read_bytes()
        with self.assertRaises(FileExistsError):
            self.run_arm('existing')
        self.assertEqual(report_before, (self.root / 'existing/report.json').read_bytes())

    def test_work_cannot_modify_the_source_capsule(self):
        with self.assertRaisesRegex(ValueError, 'must not overlap'):
            evaluation.run_evaluation(self.fixture / 'source/new-work', self.roles,
                                      fixture=self.fixture, fingerprint=lambda: 'engine')
        self.assertFalse((self.fixture / 'source/new-work').exists())

    def test_injected_execution_gets_only_blind_source_request_and_frozen_roles(self):
        captured = {}
        fixture = self.fixture
        class FakeAgent:
            @classmethod
            def create(cls, source, work, request, **kwargs):
                captured.update(source=source, work=work, request=deepcopy(request), kwargs=deepcopy(kwargs))
                work.mkdir(parents=True)
                (work / 'candidates').mkdir()
                reference = {'path': 'InputRules.cs', 'startLine': 10, 'endLine': 14,
                             'sha256': evaluation.digest(fixture / 'source/InputRules.cs')}
                payload = {'answer': {'records': [{'key': 'value-a', 'kind': 'fact',
                            'name': 'A', 'statement': 'Synthetic claim for evidence inspection.',
                            'evidence': [reference]}]}}
                evaluation.write(work / 'candidates/candidate.json', {'payload': payload, 'sha256': c.digest(payload)})
                return cls()
            def run(self, *, timeout):
                captured['timeout'] = timeout
                return {'status': 'needs-investigation', 'session': {'acceptedRequirements': []}, 'actions': []}
        report = self.run_arm('executed', execute=True, timeout=42, agent_factory=FakeAgent)
        self.assertTrue(captured['kwargs']['native_mode'])
        self.assertTrue(captured['kwargs']['joint_analysis'])
        self.assertEqual(42, captured['timeout'])
        supplied = json.dumps(captured['request']) + json.dumps(captured['kwargs'])
        judging = evaluation.load(self.fixture / 'judging.json')
        for case in judging['cases']:
            self.assertNotIn(case['expected'], supplied)
            self.assertNotIn(case['counterclaim'], supplied)
        self.assertEqual(self.root / 'executed/capsule', captured['source'])
        self.assertEqual((self.fixture / 'source/InputRules.cs').read_bytes(),
                         (captured['source'] / 'InputRules.cs').read_bytes())
        self.assertEqual('needs-investigation', report['status'])
        review = evaluation.load(Path(report['reviewViewPath']))
        self.assertEqual('not-automatically-graded', review['semanticVerdict'])
        row = review['candidates'][0]['records'][0]
        self.assertEqual('/payload/answer/records/0', row['recordPointer'])
        self.assertTrue(row['citations'][0]['sourceReferenceValid'])
        self.assertIn('Normalize(value);', row['citations'][0]['excerpt'])
        self.assertTrue(all(row['status'] == 'pending' for row in review['manualResults']))

    def test_invalid_citation_is_reported_without_a_semantic_pass(self):
        self.run_arm('citation')
        from contextbase_runtime.sources import SourceAccess
        source = SourceAccess(self.root / 'citation/input-snapshot',
                              evaluation.load(self.root / 'citation/plan.json')['snapshotId'])
        reference = {'path': 'InputRules.cs', 'startLine': 10, 'endLine': 14, 'sha256': '0' * 64}
        checked = evaluation.citation_view(reference, source)
        self.assertFalse(checked['sourceReferenceValid'])
        self.assertIn('error', checked)
        self.assertNotIn('semanticVerdict', checked)

    def test_execution_failure_preserves_report_and_separate_checklist(self):
        class FailingAgent:
            @classmethod
            def create(cls, *args, **kwargs):
                raise RuntimeError('Controlled fixture failure')
        report = self.run_arm('failed', execute=True, agent_factory=FailingAgent)
        self.assertEqual('failed', report['status'])
        self.assertEqual('Controlled fixture failure', report['error']['message'])
        self.assertTrue((self.root / 'failed/report.json').is_file())
        self.assertTrue((self.root / 'failed/judging.json').is_file())
        self.assertEqual('pending-manual-review', report['semanticVerdict'])

    def test_checked_in_fixture_under_tests_is_copied_out_of_excluded_path(self):
        report = evaluation.run_evaluation(self.root / 'formal', self.roles,
            fixture=evaluation.FIXTURE, fingerprint=lambda: 'engine')
        self.assertEqual('prepared', report['status'])
        capsule = Path(report['sourceRoot'])
        self.assertEqual(['InputRules.cs'], [p.name for p in capsule.iterdir()])
        self.assertEqual((evaluation.FIXTURE / 'source/InputRules.cs').read_bytes(),
                         (capsule / 'InputRules.cs').read_bytes())


if __name__ == '__main__':
    unittest.main()
