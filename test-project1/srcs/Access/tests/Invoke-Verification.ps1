param([ValidatePattern('^[A-Za-z0-9_-]+$')][string]$RunId='manual')
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '../tools/GeneratedPaths.ps1')
$taskRoot=$script:AccessMethodRoot
$taskReport=Resolve-AccessReportPath (Join-Path $taskRoot 'build/test-results')
$taskScratch=Resolve-AccessGeneratedPath (Join-Path $taskRoot '.tmp/verification') '.tmp'
$taskFixture=Resolve-AccessGeneratedPath (Join-Path $taskRoot '.tmp/tests/application.accdb') '.tmp'
$taskRace=Resolve-AccessGeneratedPath (Join-Path $taskRoot '.tmp/tests/race.accdb') '.tmp'
$taskSampleFixture=Resolve-AccessGeneratedPath (Join-Path $taskRoot '.tmp/tests/sample-data.accdb') '.tmp'
$taskFinal=Resolve-AccessGeneratedPath (Join-Path $taskRoot 'build/StudentManagement.accdb') 'build'
Remove-AccessIntermediate $taskScratch
New-Item -ItemType Directory -Path $taskScratch,$taskReport -Force | Out-Null
$taskInputs=@(Get-ChildItem -LiteralPath (Join-Path $taskRoot '../../spec/Access') -Recurse -File | Sort-Object FullName | ForEach-Object {
    [ordered]@{file=('../../spec/Access/'+$_.FullName.Substring(([IO.Path]::GetFullPath((Join-Path $taskRoot '../../spec/Access'))).Length+1).Replace('\','/'));sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash}
})
$taskInputs | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $taskReport 'inputs.json') -Encoding UTF8
$taskStarted=[DateTime]::UtcNow.ToString('o')
$taskExistingAccessPids=(@(Get-Process MSACCESS -ErrorAction SilentlyContinue|Select-Object -ExpandProperty Id) -join ',')
if(-not $taskExistingAccessPids){$taskExistingAccessPids='0'}
$taskSteps=New-Object 'Collections.Generic.List[object]'
$taskSourceInputs=@(Get-ChildItem -LiteralPath $taskRoot -Recurse -File | Where-Object {$_.FullName -notmatch '\\(?:build|\.tmp)\\'} | Sort-Object FullName | ForEach-Object {
    [ordered]@{file=$_.FullName.Substring($taskRoot.Length+1).Replace('\','/');sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash}
})
foreach($taskName in @('application','form-lifecycle','relationship','race','deployment','build','build-fixture','build-sample-fixture','sample-data','native-quality','native-process-health','postal-paste','postal-clipboard-protection','path-validation','syntax','format-initial-state','message-encoding')) {
    foreach($taskExtension in @('json','log')) {
        $taskPrevious=Resolve-AccessReportPath (Join-Path $taskReport ($taskName+'.'+$taskExtension))
        if(Test-Path -LiteralPath $taskPrevious){Remove-Item -LiteralPath $taskPrevious -Force}
    }
}
function Save-Verification([string]$Status,[string]$Failure) {
    $taskSummary=[ordered]@{status=$Status;runId=$RunId;startedAt=$taskStarted;completedAt=[DateTime]::UtcNow.ToString('o');steps=$taskSteps;failure=$Failure;specificationChangedDuringVerification=$false;verifiedSources='build/test-results/verified-sources.json';userOverrides='build/generation/user-overrides.json';preFreezeLocalSpecFixes='build/generation/local-spec-fix.json';formalScore=$null;notExecuted=@('Office 32-bit','human acceptance on other Windows DPI and IME configurations','100000-row / 20-user performance benchmark','network interruption','commit-response loss','production deployment','shared SQL migration','reverse generation','formal scoring')}
    if(Test-Path -LiteralPath $taskFinal){$taskSummary.artifact=[ordered]@{file='build/StudentManagement.accdb';sha256=(Get-FileHash -LiteralPath $taskFinal -Algorithm SHA256).Hash;bytes=(Get-Item -LiteralPath $taskFinal).Length}}
    $taskSummary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $taskReport 'summary.json') -Encoding UTF8
}
function Invoke-VerificationStep([string]$Name,[string]$Script,[string[]]$Arguments) {
    $taskLog=Join-Path $taskScratch ($Name+'.log')
    $taskPreviousPreference=$ErrorActionPreference
    try {
        $ErrorActionPreference='Continue'
        & powershell.exe -NoProfile -STA -ExecutionPolicy Bypass -File $Script @Arguments *> $taskLog
        $taskExit=$LASTEXITCODE
    } finally { $ErrorActionPreference=$taskPreviousPreference }
    Copy-Item -LiteralPath $taskLog -Destination (Join-Path $taskReport ($Name+'.log')) -Force
    $taskSteps.Add([ordered]@{name=$Name;exitCode=$taskExit;log=$Name+'.log'})
    if($taskExit -ne 0){throw "$Name failed; see build/test-results/$Name.log"}
    Get-Content -LiteralPath $taskLog
}
Save-Verification 'Running' ''
try {
    Invoke-VerificationStep 'build' (Join-Path $taskRoot 'Build-Access.ps1') @('-RunId',$RunId)
    $taskPublication=Get-Content -LiteralPath (Join-Path $taskReport 'summary.json') -Raw | ConvertFrom-Json
    if($taskPublication.status -ne 'VerificationRequired' -or $taskPublication.artifact.sha256 -ne (Get-FileHash -LiteralPath $taskFinal -Algorithm SHA256).Hash){throw 'Newly generated artifact inherited stale verification.'}
    [ordered]@{status='Passed';completedAt=[DateTime]::UtcNow.ToString('o');generatedStatus=$taskPublication.status;sha256=$taskPublication.artifact.sha256;previousAcceptanceInherited=$false} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskReport 'build-publication.json') -Encoding UTF8
    $taskSourceInputs | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $taskReport 'verified-sources.json') -Encoding UTF8
    Save-Verification 'Running' ''
    Invoke-VerificationStep 'path-validation' (Join-Path $PSScriptRoot 'Test-GeneratedPaths.ps1') @()
    Invoke-VerificationStep 'postal-clipboard-protection' (Join-Path $PSScriptRoot 'Test-PostalClipboardProtection.ps1') @('-RunId',$RunId)
    Invoke-VerificationStep 'build-fixture' (Join-Path $taskRoot 'Build-Access.ps1') @('-Frontend',$taskFixture,'-IncludeTests','-NoStartup','-RunId',$RunId)
    Invoke-VerificationStep 'application' (Join-Path $PSScriptRoot 'Test-Application.ps1') @('-Frontend',$taskFixture,'-Backend',$taskFixture,'-InputManifest','build/generation/inputs.json','-RunId',$RunId)
    Invoke-VerificationStep 'form-lifecycle' (Join-Path $PSScriptRoot 'Test-FormLifecycle.ps1') @('-Fixture',$taskFixture,'-RunId',$RunId,'-ReportDirectory',$taskReport)
    Invoke-VerificationStep 'relationship' (Join-Path $PSScriptRoot 'Test-Relationship74.ps1') @('-RunId',$RunId)
    Copy-Item -LiteralPath $taskFixture -Destination $taskRace -Force
    Invoke-VerificationStep 'race' (Join-Path $PSScriptRoot 'Test-Race.ps1') @('-Fixture',$taskRace,'-RunId',$RunId)
    Invoke-VerificationStep 'build-sample-fixture' (Join-Path $taskRoot 'Build-Access.ps1') @('-Frontend',$taskSampleFixture,'-IncludeTests','-NoStartup','-RunId',$RunId)
    Invoke-VerificationStep 'sample-data' (Join-Path $PSScriptRoot 'Test-SampleData.ps1') @('-Database',$taskSampleFixture,'-RunId',$RunId)
    Invoke-VerificationStep 'deployment' (Join-Path $PSScriptRoot 'Test-Deployment.ps1') @('-RunId',$RunId)
    Invoke-VerificationStep 'native-quality' (Join-Path $PSScriptRoot 'Test-AccessNativeQuality.ps1') @('-Database',$taskFinal,'-RunId',$RunId,'-ReportDirectory',$taskReport)
    Invoke-VerificationStep 'postal-paste' (Join-Path $PSScriptRoot 'Test-PostalPaste.ps1') @('-Database',$taskFinal,'-RunId',$RunId,'-ReportDirectory',$taskReport)
    $taskEvidence=Resolve-AccessGeneratedPath (Join-Path $taskRoot '.tmp/evidence/current.accdb') '.tmp'
    $taskEvidenceReport=Resolve-AccessGeneratedPath (Join-Path $taskScratch 'evidence') '.tmp'
    New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($taskEvidence)) -Force | Out-Null
    Copy-Item -LiteralPath $taskFinal -Destination $taskEvidence -Force
    Invoke-VerificationStep 'format-initial-state' (Join-Path $PSScriptRoot 'Evidence/Test-FormatAndInitialState.ps1') @('-Frontend',$taskEvidence,'-Backend',$taskEvidence,'-RunId',$RunId,'-ReportDirectory',$taskEvidenceReport)
    Invoke-VerificationStep 'message-encoding' (Join-Path $PSScriptRoot 'Evidence/Test-MessageEncodingR6.ps1') @('-Database',$taskEvidence,'-RunId',$RunId,'-ReportDirectory',$taskEvidenceReport,'-Phase','After')
    foreach($taskName in @('format-initial-state.json','message-encoding.json')){Copy-Item -LiteralPath (Join-Path $taskEvidenceReport $taskName) -Destination (Join-Path $taskReport $taskName) -Force}

    $taskSyntax=@(Get-ChildItem -LiteralPath $taskRoot -Recurse -Filter '*.ps1' | Where-Object {$_.FullName -notmatch '\\(?:build|\.tmp)\\'} | ForEach-Object {
        $taskTokens=$null;$taskErrors=$null
        [System.Management.Automation.Language.Parser]::ParseFile($_.FullName,[ref]$taskTokens,[ref]$taskErrors)|Out-Null
        [ordered]@{file=$_.FullName.Substring($taskRoot.Length+1).Replace('\','/');passed=$taskErrors.Count -eq 0;errors=@($taskErrors|ForEach-Object {$_.Message})}
    })
    $taskSyntax | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $taskReport 'syntax.json') -Encoding UTF8
    if(@($taskSyntax|Where-Object {-not $_.passed}).Count){throw 'PowerShell syntax check failed.'}
    foreach($taskInput in $taskInputs){if((Get-FileHash -LiteralPath (Join-Path $taskRoot $taskInput.file) -Algorithm SHA256).Hash -ne $taskInput.sha256){throw 'Specification changed during verification.'}}
    foreach($taskInput in $taskSourceInputs){if((Get-FileHash -LiteralPath (Join-Path $taskRoot $taskInput.file) -Algorithm SHA256).Hash -ne $taskInput.sha256){throw ('Source changed during verification: '+$taskInput.file)}}
    Invoke-VerificationStep 'native-process-health' (Join-Path $PSScriptRoot 'Test-NativeProcessHealth.ps1') @('-StartedAt',$taskStarted,'-RunId',$RunId,'-ExistingProcessIds',$taskExistingAccessPids,'-ReportDirectory',$taskReport)
    Save-Verification 'Passed' ''
} catch {
    Save-Verification 'Failed' $_.Exception.Message
    throw
}
Write-Output 'Access latest build and verification passed. See build/test-results/summary.json.'
