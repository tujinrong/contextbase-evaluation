"""CLI contract: explicit stages, independent verification, and honest exit codes."""

from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from contextbase.analysis.__main__ import main
from contextbase.analysis import contracts


class AnalysisCliTests(unittest.TestCase):
    def invoke(self, arguments):
        output = io.StringIO()
        with redirect_stdout(output):
            code = main(arguments)
        return code, json.loads(output.getvalue())

    def test_step_routes_all_stages_and_feedback(self):
        with patch('contextbase.analysis.__main__.Session') as session_type:
            session = session_type.open.return_value
            session.execute.return_value = {'status': 'candidate', 'id': 'new-candidate'}
            for stage in ('discovery', 'relationship', 'behavior'):
                with self.subTest(stage=stage):
                    code, result = self.invoke([
                        'step', '--stage', stage, '--requirements', 'one', 'two',
                        '--feedback', 'prior-candidate', '--timeout', '12.5',
                        '--inline-sources', '--work', 'workspace',
                    ])
                    self.assertEqual(0, code)
                    self.assertEqual('new-candidate', result['id'])
                    session_type.open.assert_called_with(Path('workspace'))
                    session.execute.assert_called_with(
                        stage, requirements=['one', 'two'], feedback='prior-candidate',
                        timeout=12.5, inline_sources=True,
                    )

    def test_manual_extraction_and_verification_do_not_execute_provider(self):
        with patch('contextbase.analysis.__main__.Session') as session_type:
            session = session_type.open.return_value
            session.prepare.return_value = {'id': 'manual-extract'}
            session.prepare_verification.return_value = {'id': 'manual-verify'}
            code, result = self.invoke(['step', '--stage', 'relationship', '--prepare-only',
                                        '--requirements', 'relations', '--feedback', 'earlier', '--work', 'work'])
            self.assertEqual((0, 'manual-extract'), (code, result['id']))
            session.prepare.assert_called_once_with('relationship', requirements=['relations'], feedback='earlier')
            code, result = self.invoke(['verify', '--candidate', 'candidate', '--prepare-only', '--work', 'work'])
            self.assertEqual((0, 'manual-verify'), (code, result['id']))
            session.prepare_verification.assert_called_once_with('candidate')
            session.execute.assert_not_called()
            session.verify.assert_not_called()
            session.run.assert_not_called()

    def test_verification_has_its_own_route_and_context_options(self):
        with patch('contextbase.analysis.__main__.Session') as session_type:
            session = session_type.open.return_value
            session.verify.return_value = {'id': 'verification'}
            code, result = self.invoke(['verify', '--candidate', 'candidate', '--timeout', '90',
                                        '--inline-sources', '--work', 'work'])
            self.assertEqual(0, code)
            self.assertEqual('verification', result['id'])
            session.verify.assert_called_once_with('candidate', timeout=90.0, inline_sources=True)
            session.execute.assert_not_called()

    def test_run_success_and_unfinished_status_exit_codes(self):
        with patch('contextbase.analysis.__main__.Session') as session_type:
            session = session_type.open.return_value
            for status, expected in [('complete', 0), ('scope-complete', 0),
                                     ('needs-investigation', 2), ('stopped', 2),
                                     ('cancelled', 2), ('active', 2), ('failed', 2)]:
                with self.subTest(status=status):
                    session.run.return_value = {'status': status, 'remainingRequirements': ['pending']}
                    code, result = self.invoke(['run', '--requirements', 'one', 'two', '--timeout', '45',
                                                '--inline-sources', '--work', 'work'])
                    self.assertEqual(expected, code)
                    self.assertEqual(status, result['status'])
                    session.run.assert_called_with(requirements=['one', 'two'], timeout=45.0, inline_sources=True)

    def test_revise_is_explicit_host_operation(self):
        with patch('contextbase.analysis.__main__.Session') as session_type:
            session = session_type.open.return_value
            session.revise.return_value = {'status': 'active', 'invalidatedRequirements': ['catalog', 'relations']}
            code, result = self.invoke(['revise', '--requirements', 'catalog', '--reason', 'new evidence', '--work', 'work'])
            self.assertEqual(0, code)
            self.assertEqual(['catalog', 'relations'], result['invalidatedRequirements'])
            session.revise.assert_called_once_with(['catalog'], 'new evidence')

    def test_init_resume_and_submit_load_json_as_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'request.json'
            request = {'projectId': 'example', 'goal': {'id': 'goal'}}
            path.write_text(json.dumps(request), encoding='utf-8-sig')
            with patch('contextbase.analysis.__main__.Session') as session_type:
                session_type.create.return_value.status.return_value = {'status': 'active'}
                session_type.open.return_value.resume.return_value = {'status': 'active'}
                session_type.open.return_value.submit.return_value = {'id': 'manual'}
                code, _ = self.invoke(['init', '--source', 'source', '--request', str(path), '--work', 'work'])
                self.assertEqual(0, code)
                session_type.create.assert_called_once_with(Path('source'), Path('work'), request)
                self.invoke(['resume', '--request', str(path), '--work', 'work'])
                session_type.open.return_value.resume.assert_called_once_with(request)
                self.invoke(['submit', '--task', 'task', '--answer', str(path), '--work', 'work'])
                session_type.open.return_value.submit.assert_called_once_with('task', request)

    def test_status_index_and_adopt_do_not_start_extraction(self):
        with patch('contextbase.analysis.__main__.Session') as session_type:
            session = session_type.open.return_value
            session.status.return_value = {'status': 'active'}
            session.source.snapshot_id = 'snapshot'
            session.index.return_value = [{'path': 'Example.cs', 'status': 'complete'}]
            session.adopt.return_value = {'status': 'scope-complete'}
            self.assertEqual(0, self.invoke(['status', '--work', 'work'])[0])
            code, result = self.invoke(['index', '--work', 'work'])
            self.assertEqual(0, code)
            self.assertEqual('snapshot', result['snapshotId'])
            self.assertEqual('Example.cs', result['files'][0]['path'])
            self.assertEqual(0, self.invoke(['adopt', '--candidate', 'candidate', '--work', 'work'])[0])
            session.adopt.assert_called_once_with('candidate')
            session.execute.assert_not_called()
            session.verify.assert_not_called()
            session.run.assert_not_called()

    def test_cancel_reason(self):
        with patch('contextbase.analysis.__main__.Session') as session_type:
            session_type.open.return_value.cancel.return_value = {'status': 'cancelled'}
            code, _ = self.invoke(['cancel', '--reason', 'user-request', '--work', 'work'])
            self.assertEqual(0, code)
            session_type.open.return_value.cancel.assert_called_once_with('user-request')

    def test_legacy_role_is_rejected_with_migration_hint(self):
        for legacy in (['--role', 'investigation'], ['--role=review']):
            with self.subTest(legacy=legacy), patch('contextbase.analysis.__main__.Session') as session_type:
                error = io.StringIO()
                with redirect_stderr(error), self.assertRaises(SystemExit) as raised:
                    main(['step', *legacy, '--work', 'work'])
                self.assertEqual(2, raised.exception.code)
                self.assertIn('--stage', error.getvalue())
                self.assertIn('verify', error.getvalue())
                session_type.open.assert_not_called()

    def test_missing_work_and_invalid_stage_fail_before_session_access(self):
        cases = [ ['status'], ['step', '--stage', 'investigation', '--work', 'work'],
                  ['verify', '--work', 'work'], ['revise', '--requirements', 'one', '--work', 'work'] ]
        for arguments in cases:
            with self.subTest(arguments=arguments), patch('contextbase.analysis.__main__.Session') as session_type:
                with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
                    main(arguments)
                self.assertEqual(2, raised.exception.code)
                session_type.open.assert_not_called()

    def test_failures_and_ctrl_c_have_json_and_nonzero_exit(self):
        for failure, expected, status in [(ValueError('bad binding'), 1, 'failed'),
                                          (OSError('missing input'), 1, 'failed'),
                                          (RuntimeError('provider failed'), 1, 'failed'),
                                          (KeyboardInterrupt(), 130, 'interrupted')]:
            with self.subTest(failure=type(failure).__name__), patch('contextbase.analysis.__main__.Session') as session_type:
                session_type.open.return_value.run.side_effect = failure
                code, result = self.invoke(['run', '--work', 'work'])
                self.assertEqual(expected, code)
                self.assertEqual(status, result['status'])

    def test_real_session_runs_three_stages_with_independent_verification(self):
        # This is hand-written source data. Only the adapter parses it; no
        # compiler, input code, database, or real model is invoked.
        with tempfile.TemporaryDirectory(prefix='contextbase-cli-') as temporary:
            root = Path(temporary).resolve()
            source = root / 'source'
            source.mkdir()
            text = 'class Probe { public bool Positive(int value) { return value > 0; } }\n'
            (source / 'Probe.cs').write_bytes(text.encode('utf-8'))
            evidence = {'path': 'Probe.cs', 'startLine': 1, 'endLine': 1,
                        'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest()}
            requirements = [
                {'id': stage, 'question': 'Inspect the synthetic source at this stage.',
                 'stage': stage, 'scope': 'probe',
                 'requires': [] if index == 0 else [contracts.STAGES[index - 1]]}
                for index, stage in enumerate(contracts.STAGES)
            ]
            request = {'schema': contracts.VERSION, 'projectId': 'cli-synthetic',
                       'goal': {'id': 'three-stages', 'question': 'Analyze the synthetic fixture.',
                                'requirements': requirements},
                       'allowedPaths': ['Probe.cs'], 'excludedPaths': []}
            request_path = root / 'request.json'
            request_path.write_text(json.dumps(request), encoding='utf-8')
            work = root / 'work'
            code, initial = self.invoke(['init', '--source', str(source), '--request', str(request_path),
                                          '--work', str(work)])
            self.assertEqual(0, code)
            self.assertEqual(0, initial['version'])
            calls = []

            def synthetic_provider(workspace, job_dir, prompt, schema, timeout):
                context = json.loads(prompt[prompt.index('{"request":'):])
                task = context['task']
                calls.append((task['operation'], task['stage'], task['contextId'], list(task['requirements'])))
                self.assertEqual(work / 'snapshot', workspace)
                self.assertGreater(timeout, 0)
                if task['operation'] == 'verify':
                    answer = {'taskId': task['id'], 'candidateSha256': task['candidate'],
                              'viewSha256': task['viewSha256'],
                              'checks': [{'requirement': identifier, 'status': 'pass',
                                          'reason': 'Checked the synthetic source.', 'evidence': [evidence]}
                                         for identifier in task['requirements']],
                              'unknownChecks': [], 'findings': [], 'unknowns': []}
                    self.assertEqual([], task['unknownBindings'])
                else:
                    records = []
                    coverage = []
                    by_id = {item['id']: item for item in task['goalRequirements']}
                    for identifier in task['requirements']:
                        key = identifier + '.record'
                        records.append({'key': key, 'ownerRequirement': identifier,
                                        'kind': {'discovery': 'function', 'relationship': 'relation',
                                                 'behavior': 'fact'}[task['stage']],
                                        'name': 'Synthetic observation',
                                        'statement': 'Positive returns whether value is greater than zero.',
                                        'basis': 'observed-source', 'evidence': [evidence],
                                        'dependsOn': [dep + '.record' for dep in by_id[identifier]['requires']]})
                        coverage.append({'requirement': identifier, 'status': 'supported',
                                         'recordKeys': [key], 'evidence': [evidence]})
                    answer = {'taskId': task['id'], 'records': records, 'coverage': coverage,
                              'unknowns': [], 'followups': []}
                return {'answer': answer, 'exit_code': 0, 'metadata': {'status': 'passed'}, 'usage': None}

            # Patch the process boundary rather than passing runner=. That
            # exercises real host-owned provenance and adoption validation.
            with patch('contextbase.ai.provider.run_job', side_effect=synthetic_provider):
                code, result = self.invoke(['run', '--inline-sources', '--work', str(work)])
            self.assertEqual(0, code, result)
            self.assertEqual('complete', result['status'])
            self.assertEqual(3, result['session']['version'])
            self.assertEqual([], result['session']['remainingRequirements'])
            self.assertEqual(list(contracts.STAGES), result['session']['acceptedRequirements'])
            self.assertEqual([(operation, stage) for stage in contracts.STAGES for operation in ('extract', 'verify')],
                             [(operation, stage) for operation, stage, _, _ in calls])
            self.assertEqual(6, len({context for _, _, context, _ in calls}))
            self.assertEqual(list(contracts.STAGES), calls[-1][3])
            code, reopened = self.invoke(['status', '--work', str(work)])
            self.assertEqual(0, code)
            self.assertEqual(result['session']['revision'], reopened['revision'])
            self.assertEqual(text.encode('utf-8'), (source / 'Probe.cs').read_bytes())


if __name__ == '__main__':
    unittest.main()
