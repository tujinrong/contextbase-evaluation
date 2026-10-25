param([ValidatePattern('^[A-Za-z0-9_-]+$')][string]$RunId='manual')
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '../tools/GeneratedPaths.ps1')
$taskRoot=$script:AccessMethodRoot
$taskReport=Resolve-AccessReportPath (Join-Path $taskRoot 'build/test-results')
$taskWork=Resolve-AccessGeneratedPath (Join-Path $taskRoot '.tmp/source-isolation') '.tmp'
$taskZip=Resolve-AccessGeneratedPath (Join-Path $taskRoot 'build/source.zip') 'build'
$taskFinal=Resolve-AccessGeneratedPath (Join-Path $taskRoot 'build/StudentManagement.accdb') 'build'
$taskArchiveBefore=(Get-FileHash -LiteralPath $taskZip -Algorithm SHA256).Hash
$taskFinalBefore=(Get-FileHash -LiteralPath $taskFinal -Algorithm SHA256).Hash
$taskChecks=New-Object 'Collections.Generic.List[object]'
$taskStarted=[DateTime]::UtcNow.ToString('o');$taskFatal='';$taskState='Failed'
function Check-SourcePackage([bool]$Passed,[string]$Name){
    $taskChecks.Add([ordered]@{name=$Name;passed=$Passed})
    if(-not $Passed){throw $Name}
}
try {
    $taskPrepared=Get-Content -LiteralPath (Join-Path $taskReport 'source-package-validation.json') -Encoding UTF8 -Raw|ConvertFrom-Json
    Check-SourcePackage ($taskPrepared.runId -eq $RunId -and $taskPrepared.status -eq 'PASSED') 'current archive member hashes and isolated extraction passed'
    $taskOwn=@($taskPrepared.prepared|Where-Object {$_.profile -eq 'Access'})
    Check-SourcePackage ($taskOwn.Count -eq 1 -and $taskOwn[0].archiveSha256 -eq $taskArchiveBefore) 'isolated extraction belongs to this exact source archive'
    $taskBuilder=Join-Path $taskWork 'Build-Access.ps1'
    Check-SourcePackage (Test-Path -LiteralPath $taskBuilder -PathType Leaf) 'independent archive contains executable builder'
    Check-SourcePackage (-not (Test-Path -LiteralPath (Join-Path $taskWork 'tests')) -and -not (Test-Path -LiteralPath (Join-Path $taskWork 'spec'))) 'original specifications and test modules are excluded'
    $taskLog=Resolve-AccessGeneratedPath (Join-Path $taskRoot '.tmp/source-package/source-build.log') '.tmp'
    New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($taskLog)) -Force|Out-Null
    $taskPreference=$ErrorActionPreference
    try {
        $ErrorActionPreference='Continue'
        & powershell.exe -NoProfile -STA -ExecutionPolicy Bypass -File $taskBuilder -RunId $RunId *> $taskLog
        $taskExit=$LASTEXITCODE
    } finally {$ErrorActionPreference=$taskPreference}
    Copy-Item -LiteralPath $taskLog -Destination (Join-Path $taskReport 'source-package-build.log') -Force
    Check-SourcePackage ($taskExit -eq 0) 'standalone Access source-only build succeeded'
    $taskText=Get-Content -LiteralPath $taskLog -Raw
    $taskCompilerCount=([regex]::Matches($taskText,'Native VBE compiler completed')).Count
    Check-SourcePackage ($taskCompilerCount -ge 2) 'production modules and completed forms pass the native VBE compiler'
    $taskBuilt=Resolve-AccessGeneratedPath (Join-Path $taskWork 'build/StudentManagement.accdb') '.tmp'
    Check-SourcePackage (Test-Path -LiteralPath $taskBuilt -PathType Leaf) 'source-only build publishes a standalone ACCDB inside isolation'
    $taskEvidence=Get-Content -LiteralPath (Join-Path $taskWork 'build/test-results/inputs.json') -Encoding UTF8 -Raw|ConvertFrom-Json
    Check-SourcePackage ($taskEvidence.sourceOnly -eq $true -and $taskEvidence.specificationInputs -eq 'excluded') 'source-only rebuild declares original specification hashes unavailable'
    $taskEngine=New-Object -ComObject DAO.DBEngine.120
    $taskDb=$taskEngine.OpenDatabase($taskBuilt,$false,$true)
    $taskCounts=[ordered]@{}
    foreach($taskTable in @('m_code_category','m_code','m_class','m_student','t_operation_log')){
        $taskRs=$taskDb.OpenRecordset("SELECT Count(*) AS n FROM [$taskTable]")
        $taskCounts[$taskTable]=[int]$taskRs.Fields.Item('n').Value;$taskRs.Close();$taskRs=$null
    }
    Check-SourcePackage ($taskCounts.m_code_category -eq 5 -and $taskCounts.m_code -eq 70 -and $taskCounts.m_class -eq 4 -and $taskCounts.m_student -eq 12 -and $taskCounts.t_operation_log -eq 16) 'standalone package rebuild includes approved masters and fictitious sample rows'
    Check-SourcePackage (-not [bool]$taskDb.Properties.Item('StudentSampleBootstrapAllowed').Value) 'source-only distribution disables further bootstrap insertion'
    Check-SourcePackage ($taskDb.Properties.Item('StartupForm').Value -eq 'frmStudentSearch' -and $taskDb.Properties.Item('StudentBackendPath').Value -eq 'SELF') 'source-only distribution is configured for local single-file startup'
    $taskDb.Close();[Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskDb)|Out-Null;$taskDb=$null
    [Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskEngine)|Out-Null;$taskEngine=$null
    Check-SourcePackage ((Get-FileHash -LiteralPath $taskZip -Algorithm SHA256).Hash -eq $taskArchiveBefore) 'standalone build preserves the source archive'
    Check-SourcePackage ((Get-FileHash -LiteralPath $taskFinal -Algorithm SHA256).Hash -eq $taskFinalBefore) 'standalone build preserves the canonical ACCDB'
    $taskState='Passed'
} catch {$taskFatal=$_.Exception.Message;Write-Output $taskFatal}
finally {
    if($null -ne $taskDb){try{$taskDb.Close()}catch{};[Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskDb)|Out-Null}
    if($null -ne $taskEngine){[Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskEngine)|Out-Null}
    [GC]::Collect();[GC]::WaitForPendingFinalizers()
    [ordered]@{status=$taskState;runId=$RunId;startedAt=$taskStarted;completedAt=[DateTime]::UtcNow.ToString('o');archive='build/source.zip';archiveSha256=$taskArchiveBefore;canonicalBeforeSha256=$taskFinalBefore;canonicalAfterSha256=(Get-FileHash -LiteralPath $taskFinal -Algorithm SHA256).Hash;fixtureOnly=$true;nativeCompilation=($taskCompilerCount -ge 2);counts=$taskCounts;checks=$taskChecks;fatal=$taskFatal;formalScore=$null;notExecuted=@('Office 32-bit','production deployment','formal acceptance')}|ConvertTo-Json -Depth 7|Set-Content -LiteralPath (Join-Path $taskReport 'source-package-build.json') -Encoding UTF8
}
if($taskState -ne 'Passed'){exit 1}
Write-Output "Access standalone source-only package: $($taskChecks.Count) checks passed."
