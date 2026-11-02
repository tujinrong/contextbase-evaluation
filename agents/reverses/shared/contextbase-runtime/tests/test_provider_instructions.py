"""Analysis and verification jobs explicitly select separate CLI base instructions."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import tomllib
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from contextbase_runtime import controller, provider


class ProviderInstructionTests(unittest.TestCase):
    def setUp(self):
        home = Path(__file__).resolve().parents[1] / '.tmp'
        home.mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(prefix='analysis-role-', dir=home)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.workspace = self.root / 'source'
        self.workspace.mkdir()
        self.job = self.root / '解析 job'
        self.cli = self.root / 'codex.exe'
        self.cli.write_bytes(b'not executed')
        self.instructions = self.root / 'analysis.md'
        self.instructions.write_bytes('あなたはソース解析者です。\r\n根拠と未確定を分ける。\n'.encode('utf-8'))
        self.verification_instructions = self.root / 'verification.md'
        self.verification_instructions.write_bytes('あなたは独立した検証者です。\r\n候補を根拠と照合する。\n'.encode('utf-8'))
        self.role = 'analysis'
        self.commands = []

    def cli_result(self, command, **options):
        self.commands.append(command)
        config = next(value for value in command if value.startswith('model_instructions_file='))
        path = Path(tomllib.loads(config)['model_instructions_file'])
        self.assertTrue(path.is_absolute())
        expected = self.verification_instructions if self.role == 'verification' else self.instructions
        self.assertEqual(expected.read_bytes(), path.read_bytes())
        self.assertFalse(options['shell'])
        self.assertEqual(self.workspace, options['cwd'])
        self.assertNotIn('--model', command)
        self.assertNotIn('--ignore-user-config', command)
        options['stdout'].write(b'{"type":"turn.completed","usage":{"input_tokens":1}}\n')
        options['stdout'].flush()
        Path(command[command.index('--output-last-message') + 1]).write_text('{"ok":true}', encoding='utf-8')
        return subprocess.CompletedProcess(command, 0)

    def run_job(self, launch=None, *, instruction_role='analysis'):
        self.role = instruction_role
        with patch.object(provider, 'ANALYSIS_INSTRUCTIONS', self.instructions), \
                patch.object(provider, 'VERIFICATION_INSTRUCTIONS', self.verification_instructions), \
                patch.object(provider, 'resolve_cli', return_value=self.cli), \
                patch.object(provider.subprocess, 'run', side_effect=launch or self.cli_result):
            result = provider.run_job(self.workspace, self.job, 'Read supplied evidence.',
                                      timeout_seconds=5, instruction_role=instruction_role)
        self.assertEqual(result, json.loads((self.job / 'result.json').read_text(encoding='utf-8')))
        return result

    def test_job_uses_exact_saved_base_instructions_in_cli_override(self):
        expected = self.instructions.read_bytes()
        result = self.run_job()
        self.assertEqual('passed', result['metadata']['status'])
        self.assertEqual({'ok': True}, result['answer'])
        metadata = result['metadata']
        self.assertEqual('contextbase-role-instructions/1', metadata['model_instructions_policy'])
        self.assertEqual('analysis', metadata['model_instructions_role'])
        saved = Path(metadata['model_instructions_path'])
        self.assertEqual(self.job / 'model-instructions.md', saved)
        self.assertEqual(expected, saved.read_bytes())
        self.assertEqual(hashlib.sha256(expected).hexdigest(), metadata['model_instructions_sha256'])
        self.assertEqual(1, len(self.commands))

    def test_missing_instructions_fail_before_cli_without_default_fallback(self):
        self.instructions.unlink()
        result = self.run_job()
        self.assertEqual('invalid_model_instructions', result['metadata']['status'])
        self.assertIsNone(result['answer'])
        self.assertEqual([], self.commands)

    def test_verification_job_uses_its_own_template_and_metadata(self):
        result = self.run_job(instruction_role='verification')
        self.assertEqual('passed', result['metadata']['status'])
        self.assertEqual('verification', result['metadata']['model_instructions_role'])
        self.assertEqual(hashlib.sha256(self.verification_instructions.read_bytes()).hexdigest(),
                         result['metadata']['model_instructions_sha256'])
        self.assertEqual(self.verification_instructions.read_bytes(),
                         (self.job / 'model-instructions.md').read_bytes())

    def test_missing_verification_template_does_not_fall_back_to_analysis(self):
        self.verification_instructions.unlink()
        result = self.run_job(instruction_role='verification')
        self.assertEqual('invalid_model_instructions', result['metadata']['status'])
        self.assertEqual('verification', result['metadata']['model_instructions_role'])
        self.assertIsNone(result['answer'])
        self.assertEqual([], self.commands)

    def test_invalid_role_is_rejected_before_job_creation(self):
        for role in ('verify', 'coding', '', None, False, []):
            with self.subTest(role=role), patch.object(provider.subprocess, 'run') as launch:
                with self.assertRaisesRegex(ValueError, 'instruction_role'):
                    provider.run_job(self.workspace, self.job, 'Read evidence.', instruction_role=role)
                launch.assert_not_called()
                self.assertFalse(self.job.exists())

    def test_empty_or_invalid_utf8_instructions_fail_before_cli(self):
        for number, contents in enumerate((b' \r\n', b'\xff')):
            self.instructions.write_bytes(contents)
            self.job = self.root / ('invalid-' + str(number))
            result = self.run_job()
            self.assertEqual('invalid_model_instructions', result['metadata']['status'])
            self.assertIsNone(result['answer'])
        self.assertEqual([], self.commands)

    def test_saved_instructions_changed_during_cli_are_not_accepted(self):
        def mutate(command, **options):
            result = self.cli_result(command, **options)
            (self.job / 'model-instructions.md').write_text('changed', encoding='utf-8')
            return result
        result = self.run_job(mutate)
        self.assertEqual('model_instructions_changed', result['metadata']['status'])
        self.assertIsNone(result['answer'])

    def test_template_changed_during_cli_is_not_accepted(self):
        def mutate(command, **options):
            result = self.cli_result(command, **options)
            self.instructions.write_text('changed', encoding='utf-8')
            return result
        result = self.run_job(mutate)
        self.assertEqual('model_instructions_changed', result['metadata']['status'])
        self.assertIsNone(result['answer'])

    def test_verification_template_changed_during_cli_is_not_accepted(self):
        def mutate(command, **options):
            result = self.cli_result(command, **options)
            self.verification_instructions.write_text('changed', encoding='utf-8')
            return result
        result = self.run_job(mutate, instruction_role='verification')
        self.assertEqual('model_instructions_changed', result['metadata']['status'])
        self.assertIsNone(result['answer'])

    def test_instruction_content_is_part_of_engine_identity(self):
        runtime = Path(controller.__file__).parent
        resources = {'analysis_instructions.md': self.instructions,
                     'verification_instructions.md': self.verification_instructions}
        paths = SimpleNamespace(with_name=lambda name: resources.get(name, runtime / name))
        with patch.object(controller, 'Path', return_value=paths):
            before = controller.engine_fingerprint()
            self.instructions.write_text('異なる解析方針', encoding='utf-8')
            self.assertNotEqual(before, controller.engine_fingerprint())
            before = controller.engine_fingerprint()
            self.verification_instructions.write_text('異なる検証方針', encoding='utf-8')
            self.assertNotEqual(before, controller.engine_fingerprint())

    def test_package_configuration_includes_analysis_template(self):
        root = Path(__file__).resolve().parents[1]
        project = tomllib.loads((root / 'pyproject.toml').read_text(encoding='utf-8'))
        resources = project['tool']['setuptools']['package-data']['contextbase_runtime']
        self.assertIn('analysis_instructions.md', resources)
        self.assertIn('verification_instructions.md', resources)

    def test_three_public_agents_select_role_base_for_extract_and_independent_verify(self):
        from test_independent_agents import (IndependentAgentTests, DiscoveryAgent,
                                             RelationshipAgent, BehaviorAgent, request,
                                             simulated_answer)
        fixture = IndependentAgentTests()
        fixture.setUp()
        self.addCleanup(fixture.tearDown)
        calls = []
        real_run = provider.subprocess.run

        def infer(command, **options):
            config = next((value for value in command if value.startswith('model_instructions_file=')), None)
            if config is None:
                # The trusted parser worker also uses subprocess.run; keep it
                # real and substitute only the Codex inference process.
                return real_run(command, **options)
            instructions = Path(tomllib.loads(config)['model_instructions_file'])
            prompt = options['stdin'].read().decode('utf-8')
            context = json.loads(prompt[prompt.index('{"request":'):])
            expected = (provider.VERIFICATION_INSTRUCTIONS if context['task']['operation'] == 'verify'
                        else provider.ANALYSIS_INSTRUCTIONS)
            self.assertEqual(expected.read_bytes(), instructions.read_bytes())
            calls.append((context['task']['stage'], context['task']['operation']))
            answer = simulated_answer(context)
            Path(command[command.index('--output-last-message') + 1]).write_text(
                json.dumps(answer, ensure_ascii=False), encoding='utf-8')
            options['stdout'].write(b'{"type":"turn.completed","usage":{"input_tokens":1}}\n')
            options['stdout'].flush()
            return subprocess.CompletedProcess(command, 0)

        handoff = None
        with patch.object(provider, 'resolve_cli', return_value=self.cli), \
                patch.object(provider.subprocess, 'run', side_effect=infer):
            for agent_type in (DiscoveryAgent, RelationshipAgent, BehaviorAgent):
                agent = agent_type.create(fixture.source, fixture.root / agent_type.stage,
                                          request(), handoff=handoff)
                self.assertEqual('complete', agent.run(inline_sources=True)['status'])
                handoff = agent.export()
        self.assertEqual({'discovery', 'relationship', 'behavior'}, {stage for stage, _ in calls})
        for stage in ('discovery', 'relationship', 'behavior'):
            self.assertIn((stage, 'extract'), calls)
            self.assertIn((stage, 'verify'), calls)

    def test_incremental_upstream_and_local_reviews_keep_verification_role_across_rounds(self):
        from test_incremental_agents import IncrementalAgentTests, RelationshipAgent
        fixture = IncrementalAgentTests()
        fixture.setUp()
        self.addCleanup(fixture.tearDown)
        discovery = fixture.create()
        self.assertEqual('complete', fixture.run_agent(discovery)['status'])
        relationship = fixture.create(RelationshipAgent, handoff=discovery.export())
        real_run = provider.subprocess.run
        calls = []

        def infer(command, **options):
            config = next((value for value in command if value.startswith('model_instructions_file=')), None)
            if config is None:
                return real_run(command, **options)
            instructions = Path(tomllib.loads(config)['model_instructions_file'])
            prompt = options['stdin'].read().decode('utf-8')
            context = json.loads(prompt.rsplit('\n', 1)[1])
            task = context['task']
            expected = (provider.VERIFICATION_INSTRUCTIONS if task['operation'] == 'verify'
                        else provider.ANALYSIS_INSTRUCTIONS)
            self.assertEqual(expected.read_bytes(), instructions.read_bytes())
            calls.append((task['stage'], task['operation'], context['evidenceDialog']['round']))
            response = fixture.provider(options['cwd'], instructions.parent, prompt, None, options['timeout'])
            Path(command[command.index('--output-last-message') + 1]).write_text(
                json.dumps(response['answer'], ensure_ascii=False), encoding='utf-8')
            options['stdout'].write(b'{"type":"turn.completed","usage":{"input_tokens":1}}\n')
            options['stdout'].flush()
            return subprocess.CompletedProcess(command, 0)

        with patch.object(provider, 'resolve_cli', return_value=self.cli), \
                patch.object(provider.subprocess, 'run', side_effect=infer):
            self.assertEqual('complete', relationship.run()['status'])
        for stage in ('discovery', 'relationship'):
            self.assertIn((stage, 'verify', 1), calls)
            self.assertTrue(any(s == stage and operation == 'verify' and number > 1
                                for s, operation, number in calls))
        self.assertTrue(any(operation == 'extract' for _, operation, _ in calls))


if __name__ == '__main__':
    unittest.main()
