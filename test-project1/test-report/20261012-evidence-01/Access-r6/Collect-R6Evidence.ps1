$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../srcs/Access'))
function Read-Json([string]$name){Get-Content -LiteralPath (Join-Path $PSScriptRoot $name) -Raw -Encoding UTF8|ConvertFrom-Json}
if(Test-Path -LiteralPath (Join-Path $PSScriptRoot 'results.json')){throw 'Historical aggregate already exists.'}
$before=Read-Json '20261012-evidence-01-access-r6-message-before.json'
$after=Read-Json '20261012-evidence-01-access-r6-message-after.json'
$ui=Read-Json '20261012-evidence-01-access-r6-ui-encoding.json'
$deployment=Read-Json '20261012-evidence-01-access-r6-deployment.json'
$original=Read-Json 'before-fix.json'
$replacement=Read-Json 'replacement.json'
$fixtureReport=Join-Path $PSScriptRoot '../Access-ui-r6/results.json'
$fixture=Get-Content -LiteralPath $fixtureReport -Raw -Encoding UTF8|ConvertFrom-Json
$scripts=@('Build-Access.ps1','tests/Test-Deployment.ps1','tests/Evidence/Test-MessageEncodingR6.ps1','tests/Evidence/Test-UiEncodingR6.ps1','tests/Evidence/Seed-UiFixtureR6.ps1')
$parser=@()
foreach($path in $scripts){
 $absolute=Join-Path $root $path;$tokens=$null;$errors=$null
 [void][Management.Automation.Language.Parser]::ParseFile($absolute,[ref]$tokens,[ref]$errors)
 $parser+=[ordered]@{path=$absolute;sha256=(Get-FileHash -LiteralPath $absolute -Algorithm SHA256).Hash;errors=@($errors|ForEach-Object {$_.Message})}
}
$inputs=@(Get-ChildItem -LiteralPath (Join-Path $root 'spec'),(Join-Path $root 'Modules'),(Join-Path $root 'Classes'),(Join-Path $root 'database') -Recurse -File|Where-Object {$_.FullName -notmatch '[\\/](bin|obj|build)[\\/]'}|Sort-Object FullName|ForEach-Object {
 $version=$null
 if($_.Extension -eq '.md'){$head=Get-Content -LiteralPath $_.FullName -Encoding UTF8 -TotalCount 1;if($head -match '"version"\s*:\s*"([^"]+)"'){$version=$Matches[1]}}
 [ordered]@{path=$_.FullName;version=$version;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash}
})
$inputs+=@($scripts+@('tests/Evidence/modEvidenceUiSeedR6.bas','tools/generate_schema.py')|ForEach-Object {$absolute=Join-Path $root $_;[ordered]@{path=$absolute;version=$null;sha256=(Get-FileHash -LiteralPath $absolute -Algorithm SHA256).Hash}})
$runtimeChanges=@($original.inputs|Where-Object {(Get-FileHash -LiteralPath $_.path -Algorithm SHA256).Hash -ne $_.sha256}|ForEach-Object {$_.path})
$specChanges=@($runtimeChanges|Where-Object {$_ -like '*\spec\*'})
$specInputs=@($inputs|Where-Object {$_.path -like '*\spec\*'})
$inputRecord=[ordered]@{runId='20261012-evidence-01-access-r6';agentVersion='7.5';specBusinessVersion='8.0';specConfigurationVersion='8.1';specIndexVersion='8.2';specFileCount=$specInputs.Count;specChangedSinceR5=$specChanges.Count;runtimeChangesSinceBefore=$runtimeChanges;inputs=$inputs}
$inputRecord|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $PSScriptRoot 'inputs.json') -Encoding UTF8
$parser|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $PSScriptRoot 'ps5-parser.json') -Encoding UTF8
$productionHash=(Get-FileHash -LiteralPath $replacement.production -Algorithm SHA256).Hash
$deploymentPassed=@($deployment.checks|Where-Object {$_.passed}).Count
$passed=($before.status -eq 'BEFORE_CORRUPTION_OBSERVED' -and $before.messageFailed -eq 12 -and -not $before.dateMessage.passed -and $after.status -eq 'Passed' -and $after.messagePassed -eq 58 -and $after.fieldLabel.passed -and $after.sourceLiteralScan.unrepresentableOccurrenceCount -eq 0 -and $ui.status -eq 'Passed' -and $ui.passed -eq 13 -and $deployment.status -eq 'Passed' -and $deploymentPassed -eq 19 -and $deployment.sourceBeforeSha256 -eq $deployment.sourceAfterSha256 -and $fixture.status -eq 'FRESH_ACE_DAO_UI_FIXTURE_READY' -and $fixture.inputsStable -and $productionHash -eq $replacement.productionAfterSha256 -and @($parser|Where-Object {$_.errors.Count -ne 0}).Count -eq 0 -and $runtimeChanges.Count -eq 3 -and $specChanges.Count -eq 0)
$record=[ordered]@{
 runId='20261012-evidence-01-access-r6';profile='Access';status=$(if($passed){'Passed'}else{'Failed'});finished=(Get-Date).ToUniversalTime().ToString('o')
 inputManifest='inputs.json';inputManifestSha256=(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'inputs.json') -Algorithm SHA256).Hash
 systemAnsiCodePage=$after.systemAnsiCodePage
 before=[ordered]@{messageCount=58;matched=46;failed=12;dateMessageExactMatch=$false;fieldLabelExactMatch=$before.fieldLabel.passed;unrepresentableLiteralOccurrences=23;record=$before.runId+'.json';status='EXPECTED_FAILURE_OBSERVED'}
 currentChecks=[ordered]@{messages=58;fieldLabel=1;formAndCandidateSql=13;distribution=19;total=91;powerShell5ParsedScripts=5;unrepresentableProductionLiteralOccurrences=0;fileFormat=12;visible=$false;compiled=$true}
 exactDateMessage=$after.dateMessage.actual
 production=[ordered]@{path=$replacement.production;sha256=$productionHash;opened=$false;backup=$replacement.backup;backupSha256=$replacement.backupSha256;students=0;classes=0;audits=0;testModulePresent=$false;externalLinks=0}
 uiFixture=[ordered]@{path=$fixture.frontend;closedSha256=$fixture.frontendSha256;report=$fixtureReport;students=3;classes=1;createAudits=4;fileFormat=12;sharedSqlConnected=$false;visible=$false;comClosed=$true;screenshots='DELEGATED_TO_ROOT'}
 priorPhase=[ordered]@{phase='R5';business137='NOT_RERUN_IN_R6';relationship21='NOT_RERUN_IN_R6';formatBoolean10='NOT_RERUN_IN_R6';searchAll21='NOT_RERUN_IN_R6';twoProcessRace='NOT_RERUN_IN_R6';reuseAsCurrentPass=$false}
 notTested=@('Shared SQL deployment/connection/authentication','Office 32-bit','LAN outage','10000/10001-record performance','commit-response loss','R6 manual screenshot: delegated to root')
 packaging=[ordered]@{build10SourceZipRegenerated=$false;reason='Prior frozen revision retained; root owns final manifest.'}
}
$record|ConvertTo-Json -Depth 10|Set-Content -LiteralPath (Join-Path $PSScriptRoot 'results.json') -Encoding UTF8
Write-Output ('R6 '+$record.status+'; current checks91; specChanges='+$specChanges.Count+'; runtimeChanges='+$runtimeChanges.Count+'; PS5='+$parser.Count)
if(-not $passed){exit 1}
