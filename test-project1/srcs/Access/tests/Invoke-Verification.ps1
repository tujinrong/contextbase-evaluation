param()
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '../tools/GeneratedPaths.ps1')
$taskRoot=$script:AccessMethodRoot
$taskReport=Resolve-AccessReportPath (Join-Path $taskRoot 'build/test-results')
$taskScratch=Resolve-AccessGeneratedPath (Join-Path $taskRoot '.tmp/verification') '.tmp'
$taskFixture=Resolve-AccessGeneratedPath (Join-Path $taskRoot '.tmp/tests/application.accdb') '.tmp'
$taskRace=Resolve-AccessGeneratedPath (Join-Path $taskRoot '.tmp/tests/race.accdb') '.tmp'
$taskFinal=Resolve-AccessGeneratedPath (Join-Path $taskRoot 'build/StudentManagement.accdb') 'build'
Remove-AccessIntermediate $taskScratch
New-Item -ItemType Directory -Path $taskScratch,$taskReport -Force | Out-Null
$taskInputs=@(Get-ChildItem -LiteralPath (Join-Path $taskRoot 'spec') -Recurse -File | Sort-Object FullName | ForEach-Object {
    [ordered]@{file=$_.FullName.Substring($taskRoot.Length+1).Replace('\','/');sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash}
})
$taskInputs | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $taskReport 'inputs.json') -Encoding UTF8
$taskStarted=[DateTime]::UtcNow.ToString('o')
$taskSteps=New-Object 'Collections.Generic.List[object]'
foreach($taskName in @('application','relationship','race','deployment','build','build-fixture','path-validation','syntax')) {
    foreach($taskExtension in @('json','log')) {
        $taskPrevious=Resolve-AccessReportPath (Join-Path $taskReport ($taskName+'.'+$taskExtension))
        if(Test-Path -LiteralPath $taskPrevious){Remove-Item -LiteralPath $taskPrevious -Force}
    }
}
function Save-Verification([string]$Status,[string]$Failure) {
    $taskSummary=[ordered]@{status=$Status;startedAt=$taskStarted;completedAt=[DateTime]::UtcNow.ToString('o');steps=$taskSteps;failure=$Failure;specificationChanged=$false;formalScore=$null;notExecuted=@('Office 32-bit','manual pixel and keyboard acceptance','10000/10001 row performance','network interruption','commit-response loss','production deployment','shared SQL migration','reverse generation','formal scoring')}
    if(Test-Path -LiteralPath $taskFinal){$taskSummary.artifact=[ordered]@{file='build/StudentManagement.accdb';sha256=(Get-FileHash -LiteralPath $taskFinal -Algorithm SHA256).Hash;bytes=(Get-Item -LiteralPath $taskFinal).Length}}
    $taskSummary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $taskReport 'summary.json') -Encoding UTF8
}
function Invoke-VerificationStep([string]$Name,[string]$Script,[string[]]$Arguments) {
    $taskLog=Join-Path $taskScratch ($Name+'.log')
    $taskPreviousPreference=$ErrorActionPreference
    try {
        $ErrorActionPreference='Continue'
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Script @Arguments *> $taskLog
        $taskExit=$LASTEXITCODE
    } finally { $ErrorActionPreference=$taskPreviousPreference }
    Copy-Item -LiteralPath $taskLog -Destination (Join-Path $taskReport ($Name+'.log')) -Force
    $taskSteps.Add([ordered]@{name=$Name;exitCode=$taskExit;log=$Name+'.log'})
    if($taskExit -ne 0){throw "$Name failed; see build/test-results/$Name.log"}
    Get-Content -LiteralPath $taskLog
}
Save-Verification 'Running' ''
try {
    Invoke-VerificationStep 'build' (Join-Path $taskRoot 'Build-Access.ps1') @()
    $taskPublication=Get-Content -LiteralPath (Join-Path $taskReport 'summary.json') -Raw | ConvertFrom-Json
    if($taskPublication.status -ne 'VerificationRequired' -or $taskPublication.artifact.sha256 -ne (Get-FileHash -LiteralPath $taskFinal -Algorithm SHA256).Hash){throw 'Newly generated artifact inherited stale verification.'}
    [ordered]@{status='Passed';completedAt=[DateTime]::UtcNow.ToString('o');generatedStatus=$taskPublication.status;sha256=$taskPublication.artifact.sha256;previousAcceptanceInherited=$false} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskReport 'build-publication.json') -Encoding UTF8
    Save-Verification 'Running' ''
    Invoke-VerificationStep 'path-validation' (Join-Path $PSScriptRoot 'Test-GeneratedPaths.ps1') @()
    Invoke-VerificationStep 'build-fixture' (Join-Path $taskRoot 'Build-Access.ps1') @('-Frontend',$taskFixture,'-IncludeTests','-NoStartup')
    Invoke-VerificationStep 'application' (Join-Path $PSScriptRoot 'Test-Application.ps1') @('-Frontend',$taskFixture,'-Backend',$taskFixture,'-InputManifest','build/test-results/inputs.json')
    Invoke-VerificationStep 'relationship' (Join-Path $PSScriptRoot 'Test-Relationship74.ps1') @()
    Copy-Item -LiteralPath $taskFixture -Destination $taskRace -Force
    Invoke-VerificationStep 'race' (Join-Path $PSScriptRoot 'Test-Race.ps1') @('-Fixture',$taskRace)
    Invoke-VerificationStep 'deployment' (Join-Path $PSScriptRoot 'Test-Deployment.ps1') @()
    $taskSyntax=@(Get-ChildItem -LiteralPath $taskRoot -Recurse -Filter '*.ps1' | Where-Object {$_.FullName -notmatch '\\(?:build|\.tmp)\\'} | ForEach-Object {
        $taskTokens=$null;$taskErrors=$null
        [System.Management.Automation.Language.Parser]::ParseFile($_.FullName,[ref]$taskTokens,[ref]$taskErrors)|Out-Null
        [ordered]@{file=$_.FullName.Substring($taskRoot.Length+1).Replace('\','/');passed=$taskErrors.Count -eq 0;errors=@($taskErrors|ForEach-Object {$_.Message})}
    })
    $taskSyntax | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $taskReport 'syntax.json') -Encoding UTF8
    if(@($taskSyntax|Where-Object {-not $_.passed}).Count){throw 'PowerShell syntax check failed.'}
    foreach($taskInput in $taskInputs){if((Get-FileHash -LiteralPath (Join-Path $taskRoot $taskInput.file) -Algorithm SHA256).Hash -ne $taskInput.sha256){throw 'Specification changed during verification.'}}
    Save-Verification 'Passed' ''
} catch {
    Save-Verification 'Failed' $_.Exception.Message
    throw
}
Write-Output 'Access latest build and verification passed. See build/test-results/summary.json.'
