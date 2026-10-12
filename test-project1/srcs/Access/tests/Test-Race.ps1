param([Parameter(Mandatory=$true)][string]$Fixture,[ValidatePattern('^[A-Za-z0-9_-]+$')][string]$RunId=('access-race-'+[DateTime]::UtcNow.ToString('yyyyMMdd-HHmmssfff')+'-'+[Guid]::NewGuid().ToString('N').Substring(0,8)),[string]$ReportDirectory=(Join-Path $PSScriptRoot '../test-report'))
$ErrorActionPreference='Stop'
$taskFixture=[IO.Path]::GetFullPath($Fixture)
$taskOwned=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../build'))
if (-not $taskFixture.StartsWith($taskOwned+'\',[StringComparison]::OrdinalIgnoreCase) -or [IO.Path]::GetExtension($taskFixture) -ne '.accdb') { throw 'Disposable Access single-file fixture under Access/build required.' }
$taskReport=[IO.Path]::GetFullPath($ReportDirectory)
New-Item -ItemType Directory -Path $taskReport -Force | Out-Null
if (Test-Path -LiteralPath (Join-Path $taskReport "$RunId.json")) { throw 'Report already exists; choose a new RunId.' }
$taskInputs=@(Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot '../spec') -Recurse -File | Sort-Object FullName | ForEach-Object { @{path=$_.FullName;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash} })
$taskBarrier=Join-Path $taskOwned $RunId
if (Test-Path -LiteralPath $taskBarrier) { throw 'Race run directory already exists.' }
New-Item -ItemType Directory -Path $taskBarrier | Out-Null
$taskAccess=New-Object -ComObject Access.Application
try {
 $taskAccess.Visible=$false; $taskAccess.OpenCurrentDatabase($taskFixture)
 $taskPrepared=$taskAccess.Run('PrepareRaceFixture'); Write-Output "Preparation: $taskPrepared"
 if ($taskPrepared -ne 'Saved') { throw 'Race class preparation failed.' }
 $taskDb=$taskAccess.CurrentDb(); $taskRs=$taskDb.OpenRecordset('SELECT lock_bit FROM t_write_guard WHERE guard_id=1'); $taskGuardBefore=$taskRs.Fields.Item('lock_bit').Value; $taskRs.Close()
} finally { $taskAccess.Quit(2); [Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskAccess) | Out-Null }
$taskWorkers=@()
foreach ($taskNumber in 1..2) {
 $taskWorkers+=Start-Job -ArgumentList $taskFixture,$taskBarrier,$taskNumber -ScriptBlock {
  param($taskFile,$taskDirectory,$taskWorker)
  $ErrorActionPreference='Stop'
  Add-Type -TypeDefinition 'using System;using System.Runtime.InteropServices;public static class AccessRaceWindow{[DllImport("user32.dll")]public static extern uint GetWindowThreadProcessId(IntPtr h, out uint process);}'
  $taskApp=$null; $taskResult=[ordered]@{worker=$taskWorker;powerShellPid=$PID;accessPid=$null;readyAt=$null;startAt=$null;endAt=$null;result=$null;fatal=$null}
  try {
   $taskApp=New-Object -ComObject Access.Application; $taskApp.Visible=$false; $taskApp.OpenCurrentDatabase($taskFile)
   $taskOfficePid=[uint32]0; [void][AccessRaceWindow]::GetWindowThreadProcessId([IntPtr]$taskApp.hWndAccessApp(),[ref]$taskOfficePid)
   $taskResult.accessPid=$taskOfficePid; $taskResult.readyAt=[DateTime]::UtcNow.ToString('o')
   [IO.File]::WriteAllText((Join-Path $taskDirectory "ready-$taskWorker"),[string]$taskOfficePid)
   $taskDeadline=[DateTime]::UtcNow.AddSeconds(45)
   while (-not (Test-Path -LiteralPath (Join-Path $taskDirectory 'go'))) { if ([DateTime]::UtcNow -gt $taskDeadline) { throw 'Barrier timeout.' }; Start-Sleep -Milliseconds 100 }
   $taskResult.startAt=[DateTime]::UtcNow.ToString('o')
   $taskName=if ($taskWorker -eq 1) { 'キョウソウア' } else { 'キョウソウイ' }
   $taskResult.result=$taskApp.Run('RaceSaveFixture',"RACE-$taskWorker",$taskName)
   $taskResult.endAt=[DateTime]::UtcNow.ToString('o')
  } catch { $taskResult.fatal=$_.Exception.Message }
  finally {
   if ($null -ne $taskApp) { $taskApp.Quit(2); [Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskApp) | Out-Null }
   $taskResult | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $taskDirectory "worker-$taskWorker.json") -Encoding UTF8
   $taskResult
  }
 }
}
$taskDeadline=[DateTime]::UtcNow.AddSeconds(45)
while (@(Get-ChildItem -LiteralPath $taskBarrier -Filter 'ready-*').Count -lt 2) {
 if ([DateTime]::UtcNow -gt $taskDeadline) { throw 'Worker readiness timeout; evidence retained.' }
 Start-Sleep -Milliseconds 100
}
$taskPids=@(Get-ChildItem -LiteralPath $taskBarrier -Filter 'ready-*' | ForEach-Object { Get-Content -LiteralPath $_.FullName })
if ($taskPids[0] -eq $taskPids[1]) { throw 'Separate Access processes required.' }
[IO.File]::WriteAllText((Join-Path $taskBarrier 'go'),[DateTime]::UtcNow.ToString('o'))
Write-Output "Actual distinct Access process IDs: $($taskPids -join ', ')"
Wait-Job -Job $taskWorkers -Timeout 45 | Out-Null
$taskWorkerResults=@($taskWorkers | Receive-Job)
$taskAccess=New-Object -ComObject Access.Application
try {
 $taskAccess.Visible=$false; $taskAccess.OpenCurrentDatabase($taskFixture); $taskDb=$taskAccess.CurrentDb()
 $taskRs=$taskDb.OpenRecordset("SELECT Count(*) AS n FROM m_student s INNER JOIN m_class c ON s.class_id=c.class_id WHERE c.class_code='RACE-1' AND s.is_deleted=False AND s.enrollment_status_code IN ('01','02')")
 $taskSeats=$taskRs.Fields.Item('n').Value; $taskRs.Close()
 $taskRs=$taskDb.OpenRecordset("SELECT Count(*) AS n FROM t_operation_log WHERE target_table='m_student' AND operation_type='CREATE' AND target_key IN (SELECT CStr(student_id) FROM m_student WHERE student_no IN ('RACE-1','RACE-2'))")
 $taskAudits=$taskRs.Fields.Item('n').Value; $taskRs.Close()
 $taskRs=$taskDb.OpenRecordset('SELECT lock_bit FROM t_write_guard WHERE guard_id=1'); $taskGuard=$taskRs.Fields.Item('lock_bit').Value; $taskRs.Close()
} finally { $taskAccess.Quit(2); [Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskAccess) | Out-Null }
$taskPassed=$taskWorkerResults.Count -eq 2 -and @($taskWorkerResults | Where-Object { $_.result -like 'Saved|*' }).Count -eq 1 -and @($taskWorkerResults | Where-Object { $_.result -match '^(ValidationFailed|Conflict)\|E-STU-(102|105)' }).Count -eq 1 -and $taskSeats -eq 1 -and $taskAudits -eq 1 -and $taskGuard -eq (-not $taskGuardBefore)
$taskOutput=[ordered]@{runId=$RunId;specConfigurationVersion='8.1';specDatabaseIndexVersion='8.2';specBusinessVersion='8.0';inputs=$taskInputs;fixtureOnly=$true;fixture=$taskFixture;status=$(if ($taskPassed) {'Passed'} else {'Failed'});workers=$taskWorkerResults;distinctAccessProcesses=$true;finalOccupancy=$taskSeats;capacity=1;committedStudentCreateAudits=$taskAudits;guardBefore=$taskGuardBefore;guardAfter=$taskGuard;guardExpected='exactly one committed toggle';fixtureSha256=(Get-FileHash -LiteralPath $taskFixture -Algorithm SHA256).Hash}
$taskOutput | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $taskReport "$RunId.json") -Encoding UTF8
$taskWorkerResults | ForEach-Object { Write-Output "Worker $($_.worker): $($_.result) $($_.fatal)" }
Write-Output "Result: $($taskOutput.status), occupancy=$taskSeats / 1, student-create audits=$taskAudits"
if (-not $taskPassed) { exit 1 }
