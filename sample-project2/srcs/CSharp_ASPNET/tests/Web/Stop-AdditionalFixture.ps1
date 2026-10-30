param([ValidateSet('Author','Audit')][string]$Scope='Author')
$ErrorActionPreference='Stop'
$sp2Root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$sp2Runtime=[IO.Path]::GetFullPath((Join-Path $sp2Root $(if($Scope -eq 'Author'){'.tmp/additional-ui-runtime'}else{'.tmp/audit-additional-runtime'})))
$sp2Record=Join-Path $sp2Runtime 'owned-host.json'
if(-not(Test-Path -LiteralPath $sp2Record -PathType Leaf)){throw 'Owned host record required.'}
$sp2Host=Get-Content -LiteralPath $sp2Record -Raw|ConvertFrom-Json
$sp2Expected=if($Scope -eq 'Author'){Join-Path $sp2Root '.tmp/bin/RuntimeObserver/Release/net10.0/RuntimeObserver.dll'}else{Join-Path $sp2Root 'build/publish/CareerManagement.Web.dll'}
$sp2Database=if($Scope -eq 'Author'){'SP2_WebFixture_ADDITIONAL_R20261030'}else{'SP2_WebFixture_AUDIT_ADD_R20261030'}
if([IO.Path]::GetFullPath($sp2Host.productFile) -cne [IO.Path]::GetFullPath($sp2Expected) -or $sp2Host.database -cne $sp2Database){throw 'Host ownership differs.'}
$sp2Process=Get-Process -Id $sp2Host.pid -ErrorAction SilentlyContinue
if($sp2Process){
 [void]$sp2Process.Handle
 $sp2Command=Get-CimInstance Win32_Process -Filter "ProcessId=$($sp2Host.pid)"
 if($sp2Process.ProcessName -cne 'dotnet' -or $sp2Process.StartTime.ToUniversalTime().Ticks -ne ([DateTimeOffset]$sp2Host.startedAt).UtcDateTime.Ticks -or -not $sp2Command.CommandLine.Contains($sp2Expected)){throw 'PID/start time/command no longer matches.'}
 Stop-Process -Id $sp2Process.Id -Force
 if(-not $sp2Process.WaitForExit(10000)){throw 'Owned host did not stop.'}
 $sp2Process.Dispose()
}
Write-Output "Owned $Scope host stopped. No database/configuration changed."
