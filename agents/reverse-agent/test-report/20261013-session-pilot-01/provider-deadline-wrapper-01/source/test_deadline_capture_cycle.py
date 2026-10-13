"""Synthetic wrapper timing/transport checks; no actual process stop or CIM."""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import uuid

session = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('deadline_wrapper_under_test', session / 'deadline_capture_cycle.py')
wrapper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wrapper)
report_root = session.parents[1] / 'test-report' / session.name / 'provider-deadline-wrapper-01'
run_root = session / ('dwtest-' + uuid.uuid4().hex[:8])


class WrapperChecks(unittest.TestCase):
    def setUp(self):
        self.repo = run_root / hashlib.sha256(self._testMethodName.encode('utf-8')).hexdigest()[:8]
        self.agent = self.repo / 'agents' / 'reverse-agent'
        self.local_session = self.agent / '.tmp' / 'session'
        self.local_session.mkdir(parents=True)
        self.runner = self.local_session / 'deadline_capture_cycle.py'
        self.runner.write_bytes((session / 'deadline_capture_cycle.py').read_bytes())
        (self.local_session / 'capture_owned_cycle.py').write_bytes((session / 'capture_owned_cycle.py').read_bytes())
        self.handoffs = self.agent / 'test-report' / 'session'
        self.handoffs.mkdir(parents=True)
        self.report = self.handoffs / 'wrapper'
        self.at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.deadline = self.at + timedelta(seconds=3)
        self.args = argparse.Namespace(handoff_dir='agents/reverse-agent/test-report/session',
            report='agents/reverse-agent/test-report/session/wrapper', helper='capture_owned_cycle.py',
            cancel_file=None, poll_seconds=1)
        self.put_handoff(1)
        self.calls = []
        self.queries = []
        self.sleep_calls = []
        self.identities = [{'processId': 12345, 'creationDate': '2025-12-31T23:59:00Z',
                            'commandLine': 'synthetic owned task'}]
        self.post_state = 'ABSENT'
        self.helper_state = 'RETURNED_ZERO'

    def put_handoff(self, number, deadline=None):
        path = self.handoffs / f'focus-continuation-handoff-{number:02}.json'
        path.write_text(json.dumps({'deadline': (deadline or self.deadline).isoformat(),
            'activeJobRoot': f'agents/reverse-agent/.tmp/session/jobs-{number}',
            'activeConfig': 'agents/reverse-agent/.tmp/session/config.json'}), encoding='utf-8')
        return path

    def now(self):
        return self.at

    def sleep(self, seconds):
        self.sleep_calls.append(seconds)
        self.at += timedelta(seconds=seconds)

    def query(self, identities, report, stem):
        self.queries.append((identities, stem))
        if stem == 'owner':
            observed = {'processId': identities[0]['processId'], 'parentProcessId': 54321,
                'creationDate': '2025-12-31T23:59:30Z', 'commandLine': 'synthetic wrapper'}
            rows = [{'processId': observed['processId'], 'state': 'OBSERVED_IDENTITY', 'observed': observed}]
        else:
            rows = [{'processId': item['processId'], 'state': self.post_state, 'observed': None} for item in identities]
        response = {'readOnly': True, 'processes': rows}
        result = {'state': 'OBSERVED_RESPONSE', 'response': response}
        wrapper.write_json(report / (stem + '-request.json'), {'processes': identities})
        wrapper.write_bytes(report / (stem + '-stdout.log'), json.dumps(response).encode('utf-8'))
        wrapper.write_bytes(report / (stem + '-stderr.log'), b'')
        wrapper.write_json(report / (stem + '-result.json'), result)
        return result

    def helper(self, command, report):
        self.calls.append((command, self.at))
        capture = self.repo / command[command.index('--report') + 1]
        capture.mkdir()
        wrapper.write_json(capture / 'process-request.json', {'stop': True, 'processes': self.identities})
        wrapper.write_json(capture / 'process-actions.json', {'state': 'OBSERVED_PROCESS_RESPONSE',
            'stopRequested': True, 'roots': [{'processId': 12345, 'state': 'EXACT_OWNER_MATCH'}],
            'processes': [{**self.identities[0], 'action': 'STOP_REQUESTED'}]})
        wrapper.write_json(capture / 'scope.json', {'synthetic': True})
        wrapper.write_json(capture / 'result.json', {'completeInferenceClaimed': False})
        wrapper.write_bytes(report / 'helper-stdout.log', b'synthetic helper raw output\n')
        wrapper.write_bytes(report / 'helper-stderr.log', b'synthetic helper diagnostic\n')
        state = {'state': self.helper_state, 'exitCode': 0 if self.helper_state == 'RETURNED_ZERO' else 1}
        wrapper.write_json(report / 'helper-transport.json', state)
        return state

    def invoke(self, **changes):
        return wrapper.run(self.args, now=self.now, sleep=changes.get('sleep', self.sleep),
            helper_call=changes.get('helper', self.helper), query=changes.get('query', self.query), runner=self.runner)

    def test_deadline_uses_latest_record_and_separate_absence_check(self):
        def advance(seconds):
            self.sleep(seconds)
            if self.at >= self.deadline:
                self.put_handoff(2)
        result = self.invoke(sleep=advance)
        self.assertEqual('CAPTURED_OWNED_IDENTITIES_ABSENCE_VERIFIED', result['state'])
        self.assertTrue(result['ownedIdentitiesAbsentVerified'])
        self.assertIsNone(result['processStopSucceeded'])
        command, invoked_at = self.calls[0]
        self.assertGreaterEqual(invoked_at, self.deadline)
        self.assertIn('agents/reverse-agent/test-report/session/focus-continuation-handoff-02.json', command)
        self.assertIn('--stop-at-deadline', command)
        frozen = Path(command[1])
        self.assertEqual(self.local_session, frozen.parent)
        self.assertEqual(self.repo, frozen.parents[4])
        self.assertEqual((session / 'capture_owned_cycle.py').read_bytes(), frozen.read_bytes())
        self.assertEqual(['owner', 'post-stop'], [stem for _, stem in self.queries])
        self.assertTrue((self.report / 'finished.json').exists())

    def test_changed_deadline_fails_closed_without_invocation(self):
        def advance(seconds):
            self.sleep(seconds)
            if self.at >= self.deadline:
                self.put_handoff(2, self.deadline + timedelta(seconds=30))
        result = self.invoke(sleep=advance)
        self.assertEqual('UNKNOWN_FAILED_CLOSED', result['state'])
        self.assertEqual([], self.calls)
        self.assertTrue((self.report / 'failed.json').exists())

    def test_same_file_mutation_during_callback_fails_closed(self):
        original = wrapper.latest
        calls = []
        def changed(directory):
            calls.append(1)
            value = original(directory)
            if len(calls) == 2:
                path = value[0]
                path.write_text(path.read_text(encoding='utf-8') + '\n', encoding='utf-8')
            return value
        with patch.object(wrapper, 'latest', side_effect=changed):
            result = self.invoke()
        self.assertEqual('UNKNOWN_FAILED_CLOSED', result['state'])
        self.assertEqual([], self.calls)

    def test_helper_error_preserves_raw_and_never_claims_success(self):
        self.helper_state = 'RETURNED_NONZERO'
        result = self.invoke()
        self.assertEqual('UNKNOWN_FAILED_CLOSED', result['state'])
        self.assertIsNone(result['ownedIdentitiesAbsentVerified'])
        self.assertEqual(b'synthetic helper raw output\n', (self.report / 'helper-stdout.log').read_bytes())
        self.assertEqual(['owner', 'post-stop'], [stem for _, stem in self.queries])

    def test_stop_requested_with_owned_identity_remaining_is_not_success(self):
        self.post_state = 'EXACT_IDENTITY_STILL_RUNNING'
        result = self.invoke()
        self.assertEqual('EXACT_OWNED_IDENTITIES_REMAIN', result['state'])
        self.assertFalse(result['ownedIdentitiesAbsentVerified'])
        self.assertIsNone(result['processStopSucceeded'])

    def test_unknown_post_query_does_not_turn_request_into_success(self):
        self.post_state = 'UNKNOWN'
        result = self.invoke()
        self.assertEqual('UNKNOWN_FAILED_CLOSED', result['state'])
        self.assertIsNone(result['ownedIdentitiesAbsentVerified'])

    def test_missing_helper_actions_remains_unknown(self):
        def incomplete(command, report):
            state = self.helper(command, report)
            capture = self.repo / command[command.index('--report') + 1]
            (capture / 'process-actions.json').write_text('{}', encoding='utf-8')
            return state
        result = self.invoke(helper=incomplete)
        self.assertEqual('UNKNOWN_FAILED_CLOSED', result['state'])
        self.assertIsNone(result['processStopSucceeded'])

    def test_cancel_signal_preserves_started_cancelled_finished_without_helper(self):
        signal = self.handoffs / 'cancel.json'
        signal.write_text('{"synthetic":true}', encoding='utf-8')
        self.args.cancel_file = signal.relative_to(self.repo).as_posix()
        result = self.invoke()
        self.assertEqual('CANCELLED_NO_HELPER', result['state'])
        self.assertEqual([], self.calls)
        for name in ('started.json', 'cancelled.json', 'finished.json'):
            self.assertTrue((self.report / name).exists())

    def test_keyboard_interrupt_saves_cancelled_finished_without_stop(self):
        def interrupt(seconds):
            raise KeyboardInterrupt
        result = self.invoke(sleep=interrupt)
        self.assertEqual('CANCELLED_BY_KEYBOARD_INTERRUPT', result['state'])
        self.assertEqual([], self.calls)
        self.assertTrue((self.report / 'cancelled.json').exists())

    def test_frozen_helper_mutation_fails_closed(self):
        def advance(seconds):
            self.sleep(seconds)
            if self.at >= self.deadline:
                next(self.local_session.glob('capture_owned_cycle-frozen-*.py')).write_bytes(b'synthetic mutation')
        result = self.invoke(sleep=advance)
        self.assertEqual('UNKNOWN_FAILED_CLOSED', result['state'])
        self.assertEqual([], self.calls)

    def test_incomplete_owner_identity_prevents_wait_and_helper(self):
        def unknown(identities, report, stem):
            value = self.query(identities, report, stem)
            value['state'] = 'UNKNOWN'
            return value
        result = self.invoke(query=unknown)
        self.assertEqual('UNKNOWN_FAILED_CLOSED', result['state'])
        self.assertEqual([], self.calls)
        self.assertEqual([], self.sleep_calls)

    def test_handoff_change_during_capture_downgrades_absence_to_unknown(self):
        def changed(command, report):
            state = self.helper(command, report)
            self.put_handoff(2)
            return state
        result = self.invoke(helper=changed)
        self.assertEqual('UNKNOWN_HANDOFF_CHANGED_DURING_CAPTURE', result['state'])
        self.assertIsNone(result['ownedIdentitiesAbsentVerified'])

    def test_readonly_cim_script_contains_no_stop_operation(self):
        self.assertIn('Get-CimInstance Win32_Process', wrapper.CIM_QUERY_SCRIPT)
        for forbidden in ('Stop-Process', 'TerminateProcess', 'Invoke-CimMethod', 'Remove-CimInstance'):
            self.assertNotIn(forbidden, wrapper.CIM_QUERY_SCRIPT)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--attempt', type=int, default=2)
    options = parser.parse_args()
    if options.attempt <= 0:
        parser.error('attempt must be positive')
    report_root.mkdir(parents=True, exist_ok=True)
    pin_paths = [session / 'deadline_capture_cycle.py', session / 'capture_owned_cycle.py', Path(__file__)]
    digest = lambda: [{'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()} for path in pin_paths]
    before = digest()
    with (report_root / f'synthetic-tests-{options.attempt:02}.log').open('x', encoding='utf-8', newline='\n') as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(WrapperChecks))
    after = digest()
    record = {'testsRun':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),
        'result':'PASS' if result.wasSuccessful() and before == after else 'FAIL',
        'beforePins':before,'afterPins':after,'codePinsUnchanged':before == after,
        'syntheticRoot':str(run_root),'realProcessStopPerformed':False,'realCimQueryPerformed':False,
        'productionWrapperStarted':False,'sourceOrDraftOrScoreModified':False}
    wrapper.write_json(report_root / f'synthetic-tests-{options.attempt:02}.json', record)
    print(json.dumps({key:record[key] for key in ('testsRun','failures','errors','skips','result','codePinsUnchanged')},ensure_ascii=False))
    sys.exit(0 if record['result']=='PASS' else 1)
