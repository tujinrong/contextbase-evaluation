"""Wait for one pinned deadline, then capture/stop only latest recorded ownership.

Run in the session .tmp directory; the capture helper is frozen alongside it so
the helper's __file__.parents[4] repository contract remains unchanged.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid


CIM_QUERY_SCRIPT = r'''
$ErrorActionPreference='Stop'
$request=[Console]::In.ReadToEnd() | ConvertFrom-Json
$rows=@()
foreach($identity in $request.processes) {
  $number=[int]$identity.processId
  if($number -le 0) { throw 'Invalid process identity' }
  $found=@(Get-CimInstance Win32_Process -Filter "ProcessId = $number")
  $state='ABSENT'
  $observed=$null
  if($found.Count -gt 1) { $state='AMBIGUOUS' }
  elseif($found.Count -eq 1) {
    $p=$found[0]
    if($null -eq $p.CreationDate -or $null -eq $p.CommandLine) { $state='UNKNOWN' }
    else {
      $observed=[ordered]@{processId=[int]$p.ProcessId;parentProcessId=[int]$p.ParentProcessId;
        creationDate=$p.CreationDate.ToUniversalTime().ToString('o');commandLine=$p.CommandLine}
      if($null -eq $identity.creationDate) { $state='OBSERVED_IDENTITY' }
      elseif(([DateTimeOffset]$identity.creationDate).UtcDateTime.Ticks -eq $p.CreationDate.ToUniversalTime().Ticks -and
             $identity.commandLine -ceq $p.CommandLine) { $state='EXACT_IDENTITY_STILL_RUNNING' }
      else { $state='PID_REUSED_DIFFERENT_IDENTITY' }
    }
  }
  $rows += [ordered]@{processId=$number;state=$state;observed=$observed}
}
[ordered]@{checkedAt=[DateTime]::UtcNow.ToString('o');processes=$rows;readOnly=$true} |
  ConvertTo-Json -Depth 8 -Compress
'''


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_bytes(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data)


def write_json(path, value):
    write_bytes(path, (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))


def plain(path):
    value = Path(os.path.abspath(path))
    for item in (value, *value.parents):
        junction = getattr(item, 'is_junction', None)
        if item.is_symlink() or (junction is not None and junction()):
            raise ValueError('Linked paths are forbidden')
    return value.resolve()


def within(path, root):
    value = plain(path)
    value.relative_to(plain(root))
    return value


def aware(value):
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('Timezone-aware deadline required')
    return parsed.astimezone(timezone.utc)


def latest(directory):
    records = []
    for path in directory.glob('focus-continuation-handoff-*.json'):
        match = re.fullmatch(r'focus-continuation-handoff-(\d+)\.json', path.name)
        if not match:
            raise ValueError('Unrecognised continuation filename')
        records.append((int(match[1]), path))
    if not records:
        raise FileNotFoundError('No continuation record')
    path = plain(max(records, key=lambda item: item[0])[1])
    raw = path.read_bytes()
    value = json.loads(raw.decode('utf-8'))
    return path, raw, value, aware(value['deadline'])


def query_identities(identities, report, stem):
    request = report / (stem + '-request.json')
    write_json(request, {'processes': identities})
    stdout, stderr = report / (stem + '-stdout.log'), report / (stem + '-stderr.log')
    status = {'readOnly': True, 'state': 'UNKNOWN', 'exitCode': None}
    try:
        with request.open('rb') as incoming, stdout.open('xb') as out, stderr.open('xb') as err:
            options = {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {}
            proc = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command',
                '[Console]::InputEncoding=[Text.UTF8Encoding]::new();'
                '[Console]::OutputEncoding=[Text.UTF8Encoding]::new();' + CIM_QUERY_SCRIPT],
                stdin=incoming, stdout=out, stderr=err, timeout=30, shell=False, check=False, **options)
        status['exitCode'] = proc.returncode
        if proc.returncode != 0:
            raise RuntimeError('Read-only CIM query failed')
        response = json.loads(stdout.read_bytes().decode('utf-8'))
        rows = response.get('processes')
        requested = [item['processId'] for item in identities]
        if (response.get('readOnly') is not True or not isinstance(rows, list) or
                len(rows) != len(requested) or sorted(item['processId'] for item in rows) != sorted(requested)):
            raise ValueError('Incomplete CIM identity response')
        status.update(state='OBSERVED_RESPONSE', response=response)
    except (Exception, KeyboardInterrupt) as exc:
        status['error'] = {'type': type(exc).__name__, 'message': str(exc)}
        if isinstance(exc, KeyboardInterrupt):
            write_json(report / (stem + '-result.json'), status)
            raise
    write_json(report / (stem + '-result.json'), status)
    return status


def execute_helper(command, report):
    state = {'command': command, 'state': 'UNKNOWN', 'exitCode': None}
    try:
        with (report / 'helper-stdout.log').open('xb') as out, (report / 'helper-stderr.log').open('xb') as err:
            options = {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {}
            proc = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                timeout=180, shell=False, check=False, **options)
        state['exitCode'] = proc.returncode
        state['state'] = 'RETURNED_ZERO' if proc.returncode == 0 else 'RETURNED_NONZERO'
    except (Exception, KeyboardInterrupt) as exc:
        state['error'] = {'type': type(exc).__name__, 'message': str(exc)}
        if isinstance(exc, KeyboardInterrupt):
            write_json(report / 'helper-transport.json', state)
            raise
    write_json(report / 'helper-transport.json', state)
    return state


def captured_identities(capture):
    request = json.loads((capture / 'process-request.json').read_text(encoding='utf-8'))
    actions = json.loads((capture / 'process-actions.json').read_text(encoding='utf-8'))
    if (request.get('stop') is not True or actions.get('state') != 'OBSERVED_PROCESS_RESPONSE' or
            actions.get('stopRequested') is not True or not isinstance(actions.get('roots'), list)):
        raise ValueError('A complete stop observation is required')
    selected = {}
    for identity in request['processes'] + actions['processes']:
        number = identity['processId']
        if isinstance(number, bool) or not isinstance(number, int) or number <= 0:
            raise ValueError('Invalid captured PID')
        aware(identity['creationDate'])
        if not isinstance(identity['commandLine'], str) or not identity['commandLine']:
            raise ValueError('Captured command line required')
        record = {key: identity[key] for key in ('processId', 'creationDate', 'commandLine')}
        if number in selected and (aware(selected[number]['creationDate']) != aware(record['creationDate']) or
                                  selected[number]['commandLine'] != record['commandLine']):
            raise ValueError('Conflicting captured process identity')
        selected[number] = record
    if not selected:
        raise ValueError('No captured owner identities')
    return list(selected.values()), actions


def run(args, *, now=None, sleep=None, helper_call=None, query=None, runner=None):
    now = now or (lambda: datetime.now(timezone.utc))
    sleep, helper_call, query = sleep or time.sleep, helper_call or execute_helper, query or query_identities
    runner = plain(runner or __file__)
    repository = runner.parents[4]
    agent = repository / 'agents' / 'reverse-agent'
    directory = within(repository / args.handoff_dir, agent / 'test-report')
    report = within(repository / args.report, agent / 'test-report')
    report.mkdir(parents=True, exist_ok=False)
    outcome = {'state': 'UNKNOWN', 'ownedIdentitiesAbsentVerified': None,
               'processStopSucceeded': None, 'completeInferenceClaimed': False, 'completedScore': None}
    started = now()
    try:
        runner_raw = runner.read_bytes()
        write_bytes(report / 'source' / runner.name, runner_raw)
        write_json(report / 'started.json', {'startedAt': started.isoformat(), 'osPid': os.getpid(),
            'argv': sys.argv, 'cwd': str(Path.cwd()), 'runnerPath': str(runner),
            'runnerSha256': sha(runner_raw), 'handoffDirectory': str(directory), 'report': str(report),
            'stopSuccessClaimed': False})
        owner = query([{'processId': os.getpid()}], report, 'owner')
        if owner.get('state') != 'OBSERVED_RESPONSE':
            raise RuntimeError('Wrapper owner identity unavailable')
        owner_rows = owner['response']['processes']
        if len(owner_rows) != 1 or owner_rows[0].get('state') != 'OBSERVED_IDENTITY':
            raise RuntimeError('Wrapper owner identity incomplete')
        observed = owner_rows[0].get('observed')
        if not isinstance(observed, dict) or observed.get('processId') != os.getpid():
            raise RuntimeError('Wrapper owner PID mismatch')
        aware(observed['creationDate'])
        if not observed.get('commandLine'):
            raise RuntimeError('Wrapper owner command unavailable')
        write_json(report / 'owner-identity.json', observed)
        initial_path, initial_raw, initial_value, deadline = latest(directory)
        write_bytes(report / 'initial-handoff.json', initial_raw)
        helper = plain(runner.parent / args.helper)
        if helper.parent != runner.parent:
            raise ValueError('Helper must remain in the same session directory')
        helper_raw = helper.read_bytes()
        frozen = runner.parent / ('capture_owned_cycle-frozen-' + uuid.uuid4().hex[:12] + '.py')
        write_bytes(frozen, helper_raw)
        write_bytes(report / 'source' / 'capture_owned_cycle.py', helper_raw)
        write_json(report / 'scope.json', {'deadline': deadline.isoformat(), 'initialHandoffPath': str(initial_path),
            'initialHandoffSha256': sha(initial_raw), 'handoffDirectory': str(directory),
            'initialDirectoryEntries': sorted(p.name for p in directory.glob('focus-continuation-handoff-*.json')),
            'helperSourcePath': str(helper), 'helperSourceSha256': sha(helper_raw),
            'frozenHelperPath': str(frozen), 'frozenHelperSha256': sha(helper_raw),
            'runnerSha256': sha(runner_raw), 'latestSelection': 'highest numeric continuation suffix, same as capture helper',
            'deadlineTriggerDoesNotProveExactStopTime': True, 'realStopPreviouslyTested': False})
        cancel = within(repository / args.cancel_file, agent / 'test-report') if args.cancel_file else report / 'cancel-request.json'
        while now() < deadline:
            if cancel.exists():
                write_json(report / 'cancelled.json', {'at': now().isoformat(), 'signalPath': str(cancel),
                    'signalSha256': sha(cancel.read_bytes()), 'helperInvoked': False})
                outcome['state'] = 'CANCELLED_NO_HELPER'
                return outcome
            sleep(min(args.poll_seconds, max(0, (deadline - now()).total_seconds())))
        if cancel.exists():
            write_json(report / 'cancelled.json', {'at': now().isoformat(), 'signalPath': str(cancel),
                'signalSha256': sha(cancel.read_bytes()), 'helperInvoked': False})
            outcome['state'] = 'CANCELLED_NO_HELPER'
            return outcome
        current_path, current_raw, current_value, current_deadline = latest(directory)
        write_bytes(report / 'deadline-handoff.json', current_raw)
        write_json(report / 'deadline-callback.json', {'at': now().isoformat(), 'path': str(current_path),
            'sha256': sha(current_raw), 'deadline': current_deadline.isoformat(), 'initialDeadline': deadline.isoformat()})
        if current_deadline != deadline or now() < deadline:
            raise RuntimeError('Deadline changed or callback is premature; no helper invocation')
        if sha(frozen.read_bytes()) != sha(helper_raw) or sha(runner.read_bytes()) != sha(runner_raw):
            raise RuntimeError('Frozen helper or wrapper changed; no helper invocation')
        check_path, check_raw, _, check_deadline = latest(directory)
        if check_path != current_path or check_raw != current_raw or check_deadline != deadline:
            raise RuntimeError('Continuation changed during callback; no helper invocation')
        capture = report / 'deadline-capture'
        command = [sys.executable, str(frozen), '--handoff', current_path.relative_to(repository).as_posix(),
                   '--report', capture.relative_to(repository).as_posix(), '--stop-at-deadline']
        write_json(report / 'helper-command.json', {'at': now().isoformat(), 'command': command,
            'helperSha256': sha(helper_raw), 'authoritativeHandoffSha256': sha(current_raw)})
        transport = helper_call(command, report)
        # Always attempt a separate read-only check when capture identities exist,
        # including a failed helper transport. A stop request is not exit proof.
        identities, actions = captured_identities(capture)
        post = query(identities, report, 'post-stop')
        write_json(report / 'post-stop-observation.json', {'capturedIdentities': identities,
            'query': post, 'helperTransport': transport, 'stopRequestedIsNotStopSuccess': True})
        if transport.get('state') != 'RETURNED_ZERO' or post.get('state') != 'OBSERVED_RESPONSE':
            raise RuntimeError('Helper or independent post-stop observation incomplete')
        rows = post['response']['processes']
        requested = sorted(item['processId'] for item in identities)
        if len(rows) != len(identities) or sorted(item['processId'] for item in rows) != requested:
            raise ValueError('Post-stop identity response incomplete')
        if any(item.get('state') == 'EXACT_IDENTITY_STILL_RUNNING' for item in rows):
            outcome.update(state='EXACT_OWNED_IDENTITIES_REMAIN', ownedIdentitiesAbsentVerified=False)
        elif all(item.get('state') in {'ABSENT', 'PID_REUSED_DIFFERENT_IDENTITY'} for item in rows):
            if any(root.get('state') == 'OWNER_MISMATCH_NO_STOP' for root in actions['roots']):
                raise RuntimeError('Original owner mismatch; overall stop state remains unknown')
            outcome.update(state='CAPTURED_OWNED_IDENTITIES_ABSENCE_VERIFIED', ownedIdentitiesAbsentVerified=True)
        else:
            raise RuntimeError('Post-stop query contains unknown states')
        end_path, end_raw, _, end_deadline = latest(directory)
        if end_path != current_path or end_raw != current_raw or end_deadline != deadline:
            outcome.update(state='UNKNOWN_HANDOFF_CHANGED_DURING_CAPTURE', ownedIdentitiesAbsentVerified=None)
        write_json(report / 'ended-handoff-observation.json', {'at': now().isoformat(),
            'path': str(end_path), 'sha256': sha(end_raw), 'deadline': end_deadline.isoformat()})
    except KeyboardInterrupt as exc:
        outcome.update(state='CANCELLED_BY_KEYBOARD_INTERRUPT', errorType=type(exc).__name__)
        write_json(report / 'cancelled.json', {'at': now().isoformat(), 'type': type(exc).__name__,
            'stopSuccessClaimed': False, 'partialArtifactsRetained': True})
    except Exception as exc:
        outcome.update(state='UNKNOWN_FAILED_CLOSED', errorType=type(exc).__name__, error=str(exc))
        write_json(report / 'failed.json', {'at': now().isoformat(), **outcome})
    finally:
        write_json(report / 'finished.json', {'finishedAt': now().isoformat(), 'startedAt': started.isoformat(),
            **outcome, 'limitations': ['STOP_REQUESTED is not stop success',
                'Forced wrapper termination cannot run Python finalizers; started/raw artifacts still remain',
                'Capture helper may copy pre-stop artifacts before requesting stop; exact stop time is not guaranteed',
                'Reviewer/grading agents are controlled by the parent separately', 'No original or formal score modified']})
    return outcome


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--handoff-dir', required=True)
    parser.add_argument('--report', required=True)
    parser.add_argument('--helper', default='capture_owned_cycle.py')
    parser.add_argument('--cancel-file')
    parser.add_argument('--poll-seconds', type=float, default=1)
    args = parser.parse_args()
    if not 0 < args.poll_seconds <= 15:
        parser.error('poll-seconds must be greater than zero and at most 15')
    result = run(args)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['state'] in {'CAPTURED_OWNED_IDENTITIES_ABSENCE_VERIFIED', 'CANCELLED_NO_HELPER'} else 1


if __name__ == '__main__':
    sys.exit(main())
