"""Native joint amendment routing and full-scope continuation without models."""
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
import io
import json
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from contextbase_runtime.cli import main
from contextbase_runtime.project_analysis import ProjectAnalysisAgent


class RecordingJoint:
    name = 'project-analysis'
    stage = None
    opened = []
    calls = []

    def __init__(self, work):
        self.opened.append(work)

    def amend_candidate(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return {'status': 'complete'}


class NativeAmendmentCliTests(unittest.TestCase):
    def setUp(self):
        RecordingJoint.opened = []
        RecordingJoint.calls = []

    def invoke(self, args):
        with redirect_stdout(io.StringIO()) as output, redirect_stderr(io.StringIO()) as errors:
            try:
                code = main(RecordingJoint, args)
            except SystemExit as error:
                code = error.code
        result = json.loads(output.getvalue()) if output.getvalue() else errors.getvalue()
        return code, result

    def base(self):
        return [
            'amend-candidate', '--work', 'new-work', '--from-work', 'prior-work',
            '--candidate', 'candidate-id', '--verification', 'verification-id',
        ]

    def test_native_dispatch_preserves_explicit_selection(self):
        code, result = self.invoke(self.base() + [
            '--finding', 'finding1', '--replace-key', 'record1', '--timeout', '42',
        ])
        self.assertEqual(0, code, result)
        self.assertEqual([Path('new-work')], RecordingJoint.opened)
        self.assertEqual([
            ((Path('prior-work'), 'candidate-id', 'verification-id', ['finding1']),
             {'replace_keys': ['record1'], 'timeout': 42}),
        ], RecordingJoint.calls)

    def test_invalid_native_options_reject_before_workspace_open(self):
        cases = [
            self.base() + ['--add-kind', 'entry'],
            self.base() + ['--compact'],
            self.base() + ['--inline-sources'],
            ['amend-candidate', '--work', 'new-work', '--from-work', 'prior', '--verification', 'v'],
            ['amend-candidate', '--work', 'new-work', '--bundle', 'bundle', '--verification', 'v'],
            self.base() + ['--bundle', 'bundle'],
        ]
        for args in cases:
            with self.subTest(args=args):
                code, _ = self.invoke(args)
                self.assertNotEqual(0, code)
                self.assertEqual([], RecordingJoint.opened)
                self.assertEqual([], RecordingJoint.calls)

    def test_project_method_installs_then_runs_entire_seed_scope(self):
        agent = ProjectAnalysisAgent.__new__(ProjectAnalysisAgent)
        agent.run = Mock(return_value={'status': 'needs-investigation'})
        install = Mock(return_value=(
            {'requirements': ['catalog', 'relationships', 'behavior']},
            {'schema': 'seed-spec'},
        ))
        runner = object()
        with patch.dict(sys.modules, {
            'contextbase_runtime.native_amendment': SimpleNamespace(install=install),
        }):
            result = agent.amend_candidate(
                Path('prior'), 'candidate', 'verification', ['f1'],
                replace_keys=['key'], timeout=77, runner=runner,
            )
        install.assert_called_once_with(
            agent, Path('prior'), 'candidate', 'verification', ['f1'], replace_keys=['key'],
        )
        agent.run.assert_called_once_with(
            requirements=['catalog', 'relationships', 'behavior'], timeout=77, runner=runner,
        )
        self.assertEqual('needs-investigation', result['status'])

    def test_install_failure_never_runs_provider(self):
        agent = ProjectAnalysisAgent.__new__(ProjectAnalysisAgent)
        agent.run = Mock()
        install = Mock(side_effect=ValueError('invalid custody'))
        with patch.dict(sys.modules, {
            'contextbase_runtime.native_amendment': SimpleNamespace(install=install),
        }):
            with self.assertRaisesRegex(ValueError, 'custody'):
                agent.amend_candidate('prior', 'c', 'v', replace_keys=[])
        agent.run.assert_not_called()
