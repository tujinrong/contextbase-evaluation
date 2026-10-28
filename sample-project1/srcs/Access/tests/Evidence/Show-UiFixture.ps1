param([Parameter(Mandatory=$true)][string]$Fixture,[Parameter(Mandatory=$true)][string]$ReportDirectory)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '../../tools/GeneratedPaths.ps1')
$taskFixture=Resolve-AccessGeneratedPath $Fixture '.tmp'
$taskReport=Resolve-AccessGeneratedPath $ReportDirectory '.tmp'
New-Item -ItemType Directory -Path $taskReport -Force | Out-Null
$taskStop=Join-Path $taskReport 'stop-ui.flag'
Remove-AccessIntermediate $taskStop
$taskOriginal=Join-Path $PSScriptRoot '../../build/StudentManagement.accdb'
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
