param([Parameter(Mandatory=$true)][string]$Fixture,[Parameter(Mandatory=$true)][string]$ReportDirectory)
$ErrorActionPreference='Stop'
$taskFixture=[IO.Path]::GetFullPath($Fixture)
$taskAllowed=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../build/')).TrimEnd('\')+'\'
if (-not $taskFixture.StartsWith($taskAllowed,[StringComparison]::OrdinalIgnoreCase) -or [IO.Path]::GetFileName($taskFixture) -notlike '20261012-build-04-access-single-evidence-01*.accdb') { throw 'Only this run disposable UI fixture under Access/build is allowed.' }
$taskReport=[IO.Path]::GetFullPath($ReportDirectory)
$taskReportRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../../test-report/20261012-evidence-01/')).TrimEnd('\')+'\'
if (-not $taskReport.StartsWith($taskReportRoot,[StringComparison]::OrdinalIgnoreCase)) { throw 'Only this run report subdirectory is allowed.' }
New-Item -ItemType Directory -Path $taskReport -Force | Out-Null
$taskStop=Join-Path $taskReport 'stop-ui.flag'
if (Test-Path -LiteralPath $taskStop) { throw 'Stop flag already exists.' }
$taskOriginal=Join-Path $PSScriptRoot '../../StudentManagement.accdb'
$taskOriginalHash=(Get-FileHash -LiteralPath $taskOriginal -Algorithm SHA256).Hash
$taskAccess=New-Object -ComObject Access.Application
try {
 $taskAccess.OpenCurrentDatabase($taskFixture)
 $taskAccess.DoCmd.OpenForm('frmStudentSearch')
 $taskAccess.Visible=$true
 @{fixture=$taskFixture;backend='ACE SELF fixture';fileFormat=$taskAccess.CurrentProject.FileFormat;form='frmStudentSearch';visible=$true;sqlConnected=$false;startedAt=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskReport 'ui-ready.json') -Encoding UTF8
 Write-Output 'Disposable Access fixture ready for requested interactive screenshots.'
 $taskDeadline=[DateTime]::UtcNow.AddMinutes(30)
 while (-not (Test-Path -LiteralPath $taskStop) -and [DateTime]::UtcNow -lt $taskDeadline) { Start-Sleep -Milliseconds 500 }
} finally {
 try { $taskAccess.CloseCurrentDatabase() } finally { $taskAccess.Quit(2); [Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskAccess) | Out-Null; $taskAccess=$null }
 [GC]::Collect(); [GC]::WaitForPendingFinalizers()
 $taskAfter=(Get-FileHash -LiteralPath $taskOriginal -Algorithm SHA256).Hash
 if ($taskAfter -ne $taskOriginalHash) { throw 'Original Access artifact hash changed.' }
 @{fixture=$taskFixture;fixtureSha256=(Get-FileHash -LiteralPath $taskFixture -Algorithm SHA256).Hash;originalSha256=$taskAfter;originalUnchanged=$true;closedAt=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskReport 'ui-closed.json') -Encoding UTF8
}
