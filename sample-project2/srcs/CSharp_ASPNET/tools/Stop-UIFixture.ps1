param([string]$ProfilePath='.tmp/ui-runtime/profile.json',[switch]$DropOwnedDatabase)
$ErrorActionPreference='Stop'
$sp2Root=[IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
Set-Location -LiteralPath $sp2Root
$sp2ProfilePath=[IO.Path]::GetFullPath((Join-Path $sp2Root $ProfilePath))
$sp2RuntimeRoot=[IO.Path]::GetFullPath((Join-Path $sp2Root '.tmp/ui-runtime'))
if($sp2ProfilePath -ne (Join-Path $sp2RuntimeRoot 'profile.json')){throw 'Only this method own UI runtime profile is allowed.'}
$sp2Cursor=$sp2RuntimeRoot
while($sp2Cursor -and $sp2Cursor.StartsWith($sp2Root,[StringComparison]::OrdinalIgnoreCase)){
  if((Test-Path -LiteralPath $sp2Cursor) -and ((Get-Item -LiteralPath $sp2Cursor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Reparse-point fixture path refused.'}
  if($sp2Cursor -eq $sp2Root){break};$sp2Cursor=[IO.Path]::GetDirectoryName($sp2Cursor)
}
$sp2Runtime=Get-Content -LiteralPath $sp2ProfilePath -Raw -Encoding UTF8|ConvertFrom-Json
if($sp2Runtime.database -cnotmatch '^SP2_WebFixture_UI_[a-f0-9]{12}$' -or $sp2Runtime.url -cne 'https://localhost:7445'){throw 'Owned UI fixture scope required.'}
$sp2Lifecycle=[ordered]@{projectId='sample-project2';profileId='CSharp_ASPNET';runId=(Get-Content -LiteralPath 'build/generation/inputs.json' -Raw|ConvertFrom-Json).runId;status='STARTED';database=$sp2Runtime.database;ownedPid=$null;ownedProcessExited=$null;databaseDropped=$false;existingResourcesPreserved=$true}
$sp2HostPath=Join-Path $sp2RuntimeRoot 'owned-host.json'
if(Test-Path -LiteralPath $sp2HostPath){
  $sp2Host=Get-Content -LiteralPath $sp2HostPath -Raw -Encoding UTF8|ConvertFrom-Json
  if($sp2Host.database -cne $sp2Runtime.database -or $sp2Host.profileSha256 -cne (Get-FileHash -LiteralPath $sp2ProfilePath -Algorithm SHA256).Hash){throw 'Fixture ownership metadata differs.'}
  $sp2Lifecycle.ownedPid=[int]$sp2Host.pid
  $sp2Process=Get-Process -Id $sp2Host.pid -ErrorAction SilentlyContinue
  if($sp2Process){
    [void]$sp2Process.Handle
    $sp2Command=Get-CimInstance Win32_Process -Filter "ProcessId=$($sp2Host.pid)"
    if($sp2Process.ProcessName -cne 'dotnet' -or $sp2Process.StartTime.ToUniversalTime().Ticks -ne ([DateTimeOffset]$sp2Host.startedAt).UtcDateTime.Ticks -or -not $sp2Command.CommandLine.Contains([string]$sp2Host.productFile)){throw 'Running process ownership no longer matches.'}
    Stop-Process -Id $sp2Process.Id -Force
    if(-not $sp2Process.WaitForExit(10000)){throw 'Owned UI host did not exit within ten seconds.'}
    $sp2Lifecycle.ownedProcessExited=$true
    $sp2Process.Dispose()
  }
}
if($DropOwnedDatabase){
  $sp2Sqlcmd='C:/Program Files/Microsoft SQL Server/Client SDK/ODBC/180/Tools/Binn/SQLCMD.EXE'
  $sp2Cleanup="IF NOT EXISTS(SELECT 1 FROM sys.extended_properties WHERE class=0 AND name=N'SP2Owner' AND CONVERT(nvarchar(200),value)=N'sample-project2/CSharp_ASPNET/SP2-DEMO-01') THROW 51000,'Owner mismatch',1; USE master; ALTER DATABASE [$($sp2Runtime.database)] SET SINGLE_USER WITH ROLLBACK IMMEDIATE; DROP DATABASE [$($sp2Runtime.database)];"
  & $sp2Sqlcmd -S '.\SQLEXPRESS' -E -C -b -d $sp2Runtime.database -Q $sp2Cleanup
  if($LASTEXITCODE -ne 0){throw 'Owned UI database cleanup failed; private profile retained for diagnosis.'}
  $sp2Lifecycle.databaseDropped=$true
  Remove-Item -LiteralPath $sp2ProfilePath -Force
  if(Test-Path -LiteralPath $sp2HostPath){Remove-Item -LiteralPath $sp2HostPath -Force}
}
$sp2Lifecycle.status='PASS'
$sp2Lifecycle.recordedAtUtc=[DateTimeOffset]::UtcNow.ToString('o')
$sp2Lifecycle|ConvertTo-Json -Depth 8|Set-Content -LiteralPath 'build/test-results/server-lifecycle.json' -Encoding UTF8
Write-Output 'Owned UI fixture shutdown completed.'
