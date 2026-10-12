[CmdletBinding()]
param([Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9][A-Za-z0-9_-]{0,42}$')][string]$RunId,[switch]$PlanOnly)
$ErrorActionPreference='Stop'
$setup=Join-Path $PSScriptRoot 'Setup-LocalSqlExpressAndDatabases.ps1'
if($PlanOnly) { & $setup -RunId $RunId; return }
$arguments=@('-NoProfile','-ExecutionPolicy','Bypass','-File',('"'+$setup+'"'),'-RunId',$RunId,'-Execute')
# Windows displays its own UAC consent dialog. A cancellation is propagated; it is not retried.
$process=Start-Process -FilePath "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -Verb RunAs -WindowStyle Hidden -ArgumentList $arguments -PassThru -ErrorAction Stop
if(-not $process -or -not $process.Id){throw 'No elevated process was started.'}
[pscustomobject]@{status='STARTED_AFTER_WINDOWS_ADMIN_APPROVAL';processId=$process.Id;runId=$RunId}
