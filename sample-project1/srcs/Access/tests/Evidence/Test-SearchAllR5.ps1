[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$Frontend,[Parameter(Mandatory=$true)][string]$ReportDirectory)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '../../tools/GeneratedPaths.ps1')
$profileRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$owned=[IO.Path]::GetFullPath((Join-Path $profileRoot '.tmp/evidence'))
$fixture=Resolve-AccessGeneratedPath $Frontend '.tmp'
if(-not $fixture.StartsWith($owned+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Disposable R5 build required.'}
$report=Resolve-AccessGeneratedPath $ReportDirectory '.tmp'
$resultPath=Join-Path $report 'search-all-regression.json'
New-Item -ItemType Directory -Path $report -Force|Out-Null
$access=$null;$component=$null
try {
 $access=New-Object -ComObject Access.Application;$access.Visible=$false
 $access.OpenCurrentDatabase($fixture)
 $component=$access.VBE.ActiveVBProject.VBComponents.Add(1);$component.Name='modEvidenceSearchAllR5'
 if($component.CodeModule.CountOfLines -gt 0){$component.CodeModule.DeleteLines(1,$component.CodeModule.CountOfLines)}
 $source=Join-Path $PSScriptRoot 'modEvidenceSearchAllR5.bas'
 $component.CodeModule.AddFromString(((Get-Content -LiteralPath $source -Raw -Encoding UTF8) -replace '(?m)^Attribute VB_Name.*\r?\n',''))
 $access.DoCmd.Save(5,'modEvidenceSearchAllR5');$access.DoCmd.RunCommand(126)
 $output=$access.Run('EvidenceSearchAllR5');Write-Output $output
 $passed=$output -match '^PASS\|checks=21\r?\n'
} catch {$fatal=$_.Exception.ToString();Write-Output $fatal}
finally {
 if($null -ne $component){[Runtime.InteropServices.Marshal]::FinalReleaseComObject($component)|Out-Null;$component=$null}
 if($null -ne $access){$officeVersion=$access.Version;try{$access.CloseCurrentDatabase()}catch{};$access.Quit(2);[Runtime.InteropServices.Marshal]::FinalReleaseComObject($access)|Out-Null;$access=$null}
 [GC]::Collect();[GC]::WaitForPendingFinalizers()
 [ordered]@{runId='20261012-evidence-01-access-r5-search-all';status=$(if($passed -and -not $fatal){'Passed'}else{'Failed'});checks=21;output=$output;fatal=$fatal;officeVersion=$officeVersion;fixture=$fixture;fixtureSha256=(Get-FileHash -LiteralPath $fixture -Algorithm SHA256).Hash;fixtureOnly=$true;visible=$false;sqlConnectionsOpened=0;sourceModuleSha256=(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'modEvidenceSearchAllR5.bas') -Algorithm SHA256).Hash}|ConvertTo-Json -Depth 6|Set-Content -LiteralPath $resultPath -Encoding UTF8
}
if(-not $passed -or $fatal){exit 1}
