"""Completed analysis reuse: synthetic provenance and tamper tests, no live AI."""
from contextlib import redirect_stdout, redirect_stderr
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from contextbase.ai import capsule, prompts, schemas, workflow
from contextbase.ai import __main__ as cli


class AnalysisResumeTests(unittest.TestCase):
    def setUp(self):
        temporary_root = Path(__file__).resolve().parents[3] / '.tmp'
        temporary_root.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='ai-resume-', dir=temporary_root)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        source = self.root / 'source'; source.mkdir()
        (source / 'Widget.cs').write_text('class Widget {}\n', encoding='utf-8')
        self.snapshot = self.root / 'snapshot'
        capsule.create(source, self.snapshot, project_id='synthetic-widget')
        self.doc = {'id': 'WIDGET', 'path': 'spec/widget.md', 'title': '部品', 'kind': 'basic',
                    'sourcePaths': ['Widget.cs'], 'responsibilities': ['原本で観測した宣言を説明する']}
        self.plan_file = self.bound_plan(self.root / 'plan', self.doc)
        self.definition = workflow.select_document(self.plan_file, 'WIDGET')
        self.analysis = {'documentId': 'WIDGET', 'sourcePathsRead': ['Widget.cs'],
                         'facts': [{'id': 'F1', 'topic': '宣言', 'statement': '部品型を宣言する。',
                                    'basis': 'observed-source',
                                    'references': [{'path': 'Widget.cs', 'startLine': 1, 'endLine': 1}]}],
                         'unresolved': [], 'coverageNotes': ['人工fixture']}
        meta = {'schema': 'spec-md/1.0', 'documentId': 'WIDGET', 'version': 'fixture-1',
                'path': self.doc['path'], 'sheets': [{'heading': '概要', 'kind': 'GRID', 'sheet': '01_概要'}]}
        self.content = '<!-- spec-meta: ' + json.dumps(meta, ensure_ascii=False) + ' -->\n# 部品\n\n## 概要\n\n人工fixtureの原稿。\n'
        self.calls = []

    def bound_plan(self, directory, definition):
        directory.mkdir()
        answer = directory / 'answer.txt'
        answer.write_text(json.dumps({'systemSummary': '人工fixture', 'documents': [definition], 'unresolved': []},
                                     ensure_ascii=False), encoding='utf-8')
        result = workflow.bind_existing_plan(self.snapshot, answer,
                                            capsule.verification_state(self.snapshot)['manifestSha256'])
        return Path(result['planFile'])

    def provider(self, snapshot, job, prompt, schema, timeout):
        self.calls.append((job.name, schema, prompt))
        job.mkdir(parents=True)
        if schema == schemas.ANALYSIS:
            answer = json.loads(json.dumps(self.analysis))
        else:
            self.assertEqual(schema, schemas.DRAFT)
            answer = {'documentId': 'WIDGET', 'path': self.doc['path'], 'content': self.content,
                      'factCorrections': ['原文再確認による人工fixture訂正'], 'unresolved': []}
        answer_bytes = json.dumps(answer, ensure_ascii=False, indent=4).encode('utf-8')
        (job / 'answer.txt').write_bytes(answer_bytes)
        capsule.write_json(job / 'schema.json', schema)
        (job / 'prompt.txt').write_bytes(prompt.encode('utf-8'))
        metadata = {'status': 'passed', 'schema_supplied': True, 'workspace': str(snapshot),
                    'reference_mode': 'source-only', 'training_reference_authorized': False,
                    'error_events': [], 'invalid_event_lines': [],
                    'answer_sha256': capsule.sha256(answer_bytes),
                    'prompt_sha256': capsule.sha256(prompt.encode('utf-8'))}
        result = {'exit_code': 0, 'metadata': metadata, 'answer': answer}
        capsule.write_json(job / 'result.json', result)
        return result

    def legacy(self, name='legacy', provider_directory='analysis'):
        job = self.root / name
        context = '\n対象文書計画:\n' + json.dumps(self.definition, ensure_ascii=False, indent=2)
        with patch.object(workflow, 'run_job', side_effect=self.provider):
            answer = workflow._bound_job(self.snapshot, job / provider_directory,
                                         prompts.ANALYZE + context, schemas.ANALYSIS, 1800,
                                         capsule.verification_state(self.snapshot))
        capsule.write_json(job / 'analysis-verified.json', answer)
        return job

    def checkpoint(self):
        job = self.legacy()
        workflow.recover_analysis_checkpoint(self.snapshot, self.definition, job)
        self.calls.clear()
        return job

    def resume(self, job, **kwargs):
        return workflow.document(self.snapshot, self.definition, self.root / 'fresh-job',
                                 self.root / 'fresh-output', analysis_job=job, **kwargs)

    def rewrite(self, path, mutate):
        value = capsule._load_json(path); mutate(value)
        path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')

    def assert_rejected_before_ai(self, job):
        with patch.object(workflow, 'run_job') as model, self.assertRaises((OSError, ValueError)):
            self.resume(job)
        model.assert_not_called()
        self.assertFalse((self.root / 'fresh-output').exists())

    def test_completed_analysis_resumes_only_a_fresh_ai_draft_and_preserves_responses(self):
        job = self.checkpoint()
        originals = {str(path.relative_to(job)): path.read_bytes() for path in job.rglob('*') if path.is_file()}
        critique = {'previousIndependentReview': {'approved': False, 'findings': [], 'unresolved': ['人工指摘']}}
        with patch.object(workflow, 'run_job', side_effect=self.provider):
            result = self.resume(job, revision_context=critique)
        self.assertEqual(['draft'], [call[0] for call in self.calls])
        self.assertIn('previousIndependentReview', self.calls[0][2])
        self.assertFalse(result['analysisExecutedInThisJob'])
        self.assertEqual(['原文再確認による人工fixture訂正'], result['factCorrections'])
        self.assertEqual(self.content, (self.root / 'fresh-output' / self.doc['path']).read_text(encoding='utf-8'))
        self.assertEqual(originals, {str(path.relative_to(job)): path.read_bytes() for path in job.rglob('*') if path.is_file()})
        resume = capsule._load_json(self.root / 'fresh-job/analysis-resume.json')
        self.assertEqual(capsule.sha256((job / 'analysis-handoff.json').read_bytes()), resume['checkpointSha256'])

    def test_draft_interruption_keeps_automatic_checkpoint_without_new_analysis_claim(self):
        def interrupted(*args):
            if args[3] == schemas.DRAFT:
                raise RuntimeError('synthetic draft interruption')
            return self.provider(*args)
        job = self.root / 'interrupted-job'
        with patch.object(workflow, 'run_job', side_effect=interrupted), self.assertRaises(RuntimeError):
            workflow.document(self.snapshot, self.definition, job, self.root / 'old-output')
        checkpoint = capsule._load_json(job / 'analysis-handoff.json')
        self.assertEqual('same-job:analysis-verified-before-draft', checkpoint['origin'])
        self.assertEqual(self.doc, checkpoint['document'])
        self.calls.clear()
        with patch.object(workflow, 'run_job', side_effect=self.provider):
            result = self.resume(job)
        self.assertFalse(result['analysisExecutedInThisJob'])
        self.assertEqual(['draft'], [call[0] for call in self.calls])

    def test_legacy_requires_explicit_recovery_and_records_deferred_origin(self):
        job = self.legacy()
        self.assert_rejected_before_ai(job)
        raw = (job / 'analysis/answer.txt').read_bytes()
        with patch.object(workflow, 'run_job') as model:
            result = workflow.recover_analysis_checkpoint(self.snapshot, self.definition, job)
        model.assert_not_called()
        self.assertEqual('deferred-bind:legacy-provider-and-before-after-evidence-verified', result['origin'])
        self.assertEqual(raw, (job / 'analysis/answer.txt').read_bytes())
        self.assertFalse(result['aiResponseBytesModified'])
        self.assertEqual(capsule.verification_state(self.snapshot)['scope'], result['capsuleIntegrityScope'])

    def test_repaired_completed_analysis_uses_repair_provider_evidence(self):
        job = self.legacy(provider_directory='analysis-repair')
        checkpoint = workflow.recover_analysis_checkpoint(self.snapshot, self.definition, job)
        self.assertEqual('analysis-repair', checkpoint['providerDirectory'])

    def test_verified_fact_tamper_is_rejected(self):
        job = self.checkpoint()
        self.rewrite(job / 'analysis-verified.json', lambda value: value['facts'][0].update(statement='tampered'))
        self.assert_rejected_before_ai(job)

    def test_original_provider_answer_tamper_is_rejected(self):
        job = self.checkpoint(); (job / 'analysis/answer.txt').write_text('{}', encoding='utf-8')
        self.assert_rejected_before_ai(job)

    def test_provider_result_tamper_is_rejected(self):
        job = self.checkpoint()
        self.rewrite(job / 'analysis/result.json', lambda value: value['metadata'].update(status='timeout'))
        self.assert_rejected_before_ai(job)

    def test_passed_provider_result_bytes_are_pinned_even_if_answer_is_unchanged(self):
        job = self.checkpoint()
        self.rewrite(job / 'analysis/result.json', lambda value: value['metadata'].update(seconds=123))
        self.assert_rejected_before_ai(job)

    def test_provider_schema_tamper_is_rejected(self):
        job = self.checkpoint(); (job / 'analysis/schema.json').write_text('{}', encoding='utf-8')
        self.assert_rejected_before_ai(job)

    def test_checkpoint_hash_tamper_is_rejected(self):
        job = self.checkpoint()
        self.rewrite(job / 'analysis-handoff.json', lambda value: value.update(analysisSha256='0' * 64))
        self.assert_rejected_before_ai(job)

    def test_checkpoint_integrity_scope_cannot_be_relabelled(self):
        job = self.checkpoint()
        self.rewrite(job / 'analysis-handoff.json', lambda value: value.update(capsuleIntegrityScope='stronger-unverified-claim'))
        self.assert_rejected_before_ai(job)

    def test_older_checkpoint_without_added_scope_label_keeps_verified_compatibility(self):
        job = self.checkpoint()
        self.rewrite(job / 'analysis-handoff.json', lambda value: value.pop('capsuleIntegrityScope'))
        with patch.object(workflow, 'run_job', side_effect=self.provider):
            result = self.resume(job)
        self.assertFalse(result['analysisExecutedInThisJob'])
        self.assertEqual(capsule.verification_state(self.snapshot), result['snapshot'])

    def test_changed_source_is_rejected(self):
        job = self.checkpoint(); (self.snapshot / 'sources/Widget.cs').write_text('class Different {}\n')
        self.assert_rejected_before_ai(job)

    def test_another_bound_plan_cannot_reuse_analysis_even_for_same_document(self):
        job = self.checkpoint()
        other_plan = self.bound_plan(self.root / 'other-plan', self.doc)
        self.definition = workflow.select_document(other_plan, 'WIDGET')
        self.assert_rejected_before_ai(job)

    def test_changed_plan_or_handoff_is_rejected(self):
        job = self.checkpoint(); self.plan_file.write_text('{}', encoding='utf-8')
        self.assert_rejected_before_ai(job)

    def test_document_kind_boundary_cannot_be_changed_when_reusing_analysis(self):
        job = self.checkpoint()
        other = {**self.doc, 'kind': 'analysis-report'}
        plan = self.bound_plan(self.root / 'report-plan', other)
        self.definition = workflow.select_document(plan, 'WIDGET')
        self.assert_rejected_before_ai(job)

    def test_legacy_snapshot_after_mismatch_is_not_recovered(self):
        job = self.legacy()
        self.rewrite(job / 'analysis-snapshot-after.json', lambda value: value.update(status='INPUT_CHANGED'))
        with self.assertRaises(ValueError):
            workflow.recover_analysis_checkpoint(self.snapshot, self.definition, job)
        self.assertFalse((job / 'analysis-handoff.json').exists())

    def test_legacy_provider_response_disagreement_is_not_recovered(self):
        job = self.legacy()
        self.rewrite(job / 'analysis/result.json', lambda value: value['answer'].update(documentId='OTHER'))
        with self.assertRaises(ValueError):
            workflow.recover_analysis_checkpoint(self.snapshot, self.definition, job)
        self.assertFalse((job / 'analysis-handoff.json').exists())

    def test_legacy_invalid_evidence_is_not_recovered_even_when_provider_passed(self):
        self.analysis['facts'][0]['references'][0]['endLine'] = 999
        job = self.legacy()
        with self.assertRaises(ValueError):
            workflow.recover_analysis_checkpoint(self.snapshot, self.definition, job)
        self.assertFalse((job / 'analysis-handoff.json').exists())

    def test_legacy_reference_mode_mismatch_is_not_recovered(self):
        job = self.legacy()
        self.rewrite(job / 'analysis/result.json', lambda value: value['metadata'].update(reference_mode='training-assisted'))
        with self.assertRaises(ValueError):
            workflow.recover_analysis_checkpoint(self.snapshot, self.definition, job)
        self.assertFalse((job / 'analysis-handoff.json').exists())

    def test_legacy_original_prompt_must_match_current_document_definition(self):
        job = self.legacy()
        prompt_file = job / 'analysis/prompt.txt'
        prompt = prompt_file.read_text(encoding='utf-8').replace('原本で観測した宣言を説明する', '別の責務')
        prompt_file.write_text(prompt, encoding='utf-8')
        self.rewrite(job / 'analysis/result.json', lambda value: value['metadata'].update(prompt_sha256=capsule.sha256(prompt.encode('utf-8'))))
        with self.assertRaises(ValueError):
            workflow.recover_analysis_checkpoint(self.snapshot, self.definition, job)
        self.assertFalse((job / 'analysis-handoff.json').exists())

    def test_checkpoint_mutation_during_draft_prevents_publication(self):
        job = self.checkpoint()
        def changed(*args):
            answer = self.provider(*args)
            self.rewrite(job / 'analysis-handoff.json', lambda value: value.update(bindingCreatedAt='tampered'))
            return answer
        with patch.object(workflow, 'run_job', side_effect=changed), self.assertRaises(ValueError):
            self.resume(job)
        self.assertFalse((self.root / 'fresh-output').exists())

    def test_fresh_job_cannot_be_inside_original_analysis_or_snapshot(self):
        job = self.checkpoint()
        for new_job in (job / 'new-job', self.snapshot / 'new-job'):
            with patch.object(workflow, 'run_job') as model, self.assertRaises(ValueError):
                workflow.document(self.snapshot, self.definition, new_job, self.root / 'output', analysis_job=job)
            model.assert_not_called()

    def test_existing_draft_output_is_not_overwritten(self):
        job = self.checkpoint(); target = self.root / 'fresh-output' / self.doc['path']
        target.parent.mkdir(parents=True); target.write_text('previous output', encoding='utf-8')
        self.assert_rejected_before_ai_existing_output(job)
        self.assertEqual('previous output', target.read_text(encoding='utf-8'))

    def assert_rejected_before_ai_existing_output(self, job):
        with patch.object(workflow, 'run_job') as model, self.assertRaises(FileExistsError):
            self.resume(job)
        model.assert_not_called()

    def test_cli_explicit_recovery_and_reuse_are_forwarded_without_claiming_new_analysis(self):
        job = self.legacy()
        args = ['document', '--snapshot', str(self.snapshot), '--job', str(self.root / 'fresh-job'),
                '--plan', str(self.plan_file), '--document-id', 'WIDGET', '--output', str(self.root / 'fresh-output'),
                '--analysis-job', str(job), '--recover-analysis-job']
        with patch.object(workflow, 'run_job', side_effect=self.provider), redirect_stdout(io.StringIO()):
            self.assertEqual(0, cli.main(args))
        self.assertEqual('deferred-bind:legacy-provider-and-before-after-evidence-verified',
                         capsule._load_json(job / 'analysis-handoff.json')['origin'])
        self.assertEqual(['analysis', 'draft'], [call[0] for call in self.calls])

    def test_cli_recovery_requires_analysis_job_and_document_command(self):
        for arguments in (['document', '--recover-analysis-job'], ['plan', '--analysis-job', str(self.root / 'old')]):
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                cli.main(arguments + ['--snapshot', str(self.snapshot), '--job', str(self.root / 'new')])


if __name__ == '__main__':
    unittest.main()
