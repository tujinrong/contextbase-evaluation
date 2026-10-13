"""Capture owned cycle evidence; optional stop is restricted to its recorded deadline.

This utility neither creates nor edits specifications, scores, or job result claims.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import shutil
import subprocess


PROCESS_SCRIPT = r'''
$ErrorActionPreference='Stop'
$request = [Console]::In.ReadToEnd() | ConvertFrom-Json
$all = @(Get-CimInstance Win32_Process)
$selected = @{}
$roots = @()
foreach ($owned in $request.processes) {
  $live = @($all | Where-Object ProcessId -eq $owned.processId)
  $state = 'NOT_RUNNING'
  if ($live.Count -eq 1) {
    $p=$live[0]
    $sameTime=([DateTimeOffset]$owned.creationDate).UtcDateTime.Ticks -eq $p.CreationDate.ToUniversalTime().Ticks
    if ($sameTime -and $p.CommandLine -ceq $owned.commandLine) {
      $state='EXACT_OWNER_MATCH'
      $selected[[string]$p.ProcessId]=$p
    } else { $state='OWNER_MISMATCH_NO_STOP' }
  }
  $roots += [ordered]@{processId=$owned.processId;role=$owned.role;state=$state}
}
do {
  $added=$false
  foreach ($p in $all) {
    $parent=$selected[[string]$p.ParentProcessId]
    if ($null -ne $parent -and !$selected.ContainsKey([string]$p.ProcessId) -and
        $p.CreationDate -ge $parent.CreationDate) {
      $selected[[string]$p.ProcessId]=$p
      $added=$true
    }
  }
} while ($added)
$actions=@()
$eligible=$request.stop -and [DateTimeOffset]::UtcNow -ge ([DateTimeOffset]$request.deadline)
if ($request.stop -and !$eligible) { throw 'Refuse stop before recorded deadline' }
# Freeze every selected identity before stopping. Re-check each PID immediately before acting.
foreach ($p in @($selected.Values | Sort-Object CreationDate -Descending)) {
  $state='OBSERVED_NO_STOP'
  if ($eligible) {
    $now=@(Get-CimInstance Win32_Process -Filter "ProcessId = $($p.ProcessId)")
    if ($now.Count -eq 0) { $state='ALREADY_EXITED' }
    elseif ($now.Count -ne 1 -or $now[0].CreationDate -ne $p.CreationDate -or
            $now[0].CommandLine -cne $p.CommandLine) { $state='IDENTITY_CHANGED_NO_STOP' }
    else {
      try { Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop; $state='STOP_REQUESTED' }
      catch { $state='STOP_ERROR'; $stopError=$_.Exception.Message }
    }
  }
  $actions += [ordered]@{processId=$p.ProcessId;parentProcessId=$p.ParentProcessId;
    creationDate=$p.CreationDate.ToUniversalTime().ToString('o');commandLine=$p.CommandLine;
    action=$state;error=$(if($state -eq 'STOP_ERROR'){$stopError}else{$null})}
}
[ordered]@{checkedAt=[DateTime]::UtcNow.ToString('o');stopRequested=[bool]$request.stop;
 deadline=$request.deadline;roots=$roots;processes=$actions} | ConvertTo-Json -Depth 8 -Compress
'''


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exclusive_json(path, data):
    with path.open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write('\n')


def within(path, root):
    value = path.resolve()
    value.relative_to(root.resolve())
    return value


def capture(root, target):
    records = []
    for source in sorted(root.rglob('*')):
        if not source.is_file() or {'runtime', 'runtime-code'}.intersection(source.relative_to(root).parts):
            continue
        relative = source.relative_to(root)
        record = {'path': relative.as_posix()}
        try:
            within(source, root)
            before = digest(source)
            output = target / relative
            output.parent.mkdir(parents=True, exist_ok=True)
            # target is a fresh directory; never overwrite an earlier evidence version.
            with source.open('rb') as incoming, output.open('xb') as outgoing:
                shutil.copyfileobj(incoming, outgoing)
            record.update(sourceSha256Before=before, copiedSha256=digest(output),
                          sourceSha256After=digest(source), bytes=output.stat().st_size)
            record['stableDuringCopy'] = (record['sourceSha256Before'] ==
                record['copiedSha256'] == record['sourceSha256After'])
        except Exception as exc:
            record['captureError'] = f'{type(exc).__name__}: {exc}'
        records.append(record)
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--handoff', required=True)
    parser.add_argument('--report', required=True)
    parser.add_argument('--stop-at-deadline', action='store_true')
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[4]
    agent = repository / 'agents' / 'reverse-agent'
    handoff_path = within(repository / args.handoff, agent / 'test-report')
    handoff = json.loads(handoff_path.read_text(encoding='utf-8'))
    # A stale continuation may describe a completed or different job. It cannot own this action.
    siblings = list(handoff_path.parent.glob('focus-continuation-handoff-*.json'))
    suffix = lambda p: int(p.stem.rsplit('-', 1)[1])
    if handoff_path != max(siblings, key=suffix):
        raise RuntimeError('Use the latest continuation record')
    deadline = datetime.fromisoformat(handoff['deadline'].replace('Z', '+00:00'))
    if deadline.tzinfo is None:
        raise RuntimeError('Deadline must have timezone')
    if args.stop_at_deadline and datetime.now(timezone.utc) < deadline:
        raise RuntimeError('Refuse stop before deadline; use capture without stop')
    job = within(repository / handoff['activeJobRoot'], agent / '.tmp')
    config_path = within(repository / handoff['activeConfig'], agent / '.tmp')
    config = json.loads(config_path.read_text(encoding='utf-8'))
    if (repository / config['jobs']).resolve() != job:
        raise RuntimeError('Config job root differs from continuation')
    if datetime.fromisoformat(config['deadline'].replace('Z', '+00:00')) != deadline:
        raise RuntimeError('Config deadline differs from continuation')
    round_key = f"round{int(config['revision'].split('.')[0])}"
    ownership_path = within(handoff_path.parent / handoff[round_key]['ownedProcessRecord'],
                            agent / 'test-report')
    ownership = json.loads(ownership_path.read_text(encoding='utf-8'))
    if (repository / ownership['configPath']).resolve() != config_path:
        raise RuntimeError('Ownership config differs from continuation')
    target = within(repository / args.report, agent / 'test-report')
    target.mkdir(parents=True, exist_ok=False)
    exclusive_json(target / 'scope.json', {
        'startedAt': datetime.now(timezone.utc).isoformat(), 'deadline': handoff['deadline'],
        'stopRequested': args.stop_at_deadline,
        'inputs': {str(p): digest(p) for p in (handoff_path, config_path, ownership_path, Path(__file__))},
        'jobRoot': str(job), 'completedScore': None,
        'scope': 'Process ownership and raw artifact capture only; no completion or grading inferred'})
    before = capture(job, target / 'before')
    exclusive_json(target / 'inventory-before.json', before)
    request = {'processes': ownership['processes'], 'deadline': handoff['deadline'],
               'stop': args.stop_at_deadline}
    exclusive_json(target / 'process-request.json', request)
    actions = {'state': 'UNKNOWN', 'stopRequested': args.stop_at_deadline,
               'limitations': ['No process stop outcome inferred without a complete validated response']}
    stdout = stderr = ''
    operation_error = None
    try:
        with (target / 'process-request.json').open('rb') as incoming:
            completed = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command',
                '[Console]::InputEncoding=[Text.UTF8Encoding]::new();'
                '[Console]::OutputEncoding=[Text.UTF8Encoding]::new();' + PROCESS_SCRIPT],
                stdin=incoming, capture_output=True, text=True, encoding='utf-8', timeout=60, check=True)
        stdout, stderr = completed.stdout, completed.stderr
        candidate = json.loads(stdout)
        if not isinstance(candidate, dict) or not all(key in candidate for key in ('roots', 'processes', 'stopRequested')):
            raise ValueError('Incomplete process response')
        actions = candidate
        actions['state'] = 'OBSERVED_PROCESS_RESPONSE'
    except (Exception, KeyboardInterrupt) as exc:
        operation_error = exc
        stdout = getattr(exc, 'stdout', None) or getattr(exc, 'output', None) or stdout
        stderr = getattr(exc, 'stderr', None) or stderr
        actions['error'] = {'type': type(exc).__name__, 'message': str(exc)}
    finally:
        for name, content in (('process-stdout.txt', stdout), ('process-stderr.txt', stderr)):
            raw = content if isinstance(content, bytes) else content.encode('utf-8')
            with (target / name).open('xb') as handle:
                handle.write(raw)
        exclusive_json(target / 'process-actions.json', actions)
    after = capture(job, target / 'after')
    exclusive_json(target / 'inventory-after.json', after)
    exclusive_json(target / 'result.json', {
        'finishedAt': datetime.now(timezone.utc).isoformat(),
        'stopRequested': args.stop_at_deadline, 'beforeFiles': len(before), 'afterFiles': len(after),
        'processOperationState': actions['state'],
        'completeInferenceClaimed': False, 'completedScore': None,
        'captureErrors': sum('captureError' in item for item in before + after),
        'limitations': ['Live files may change during pre-stop copy; stableDuringCopy is explicit',
                         'Missing provider result/answer remains incomplete',
                         'Review/grading agents are controlled separately by the parent agent']})
    print(json.dumps({'report': str(target), 'beforeFiles': len(before), 'afterFiles': len(after)},
                     ensure_ascii=False))
    if operation_error is not None:
        raise operation_error


if __name__ == '__main__':
    main()
