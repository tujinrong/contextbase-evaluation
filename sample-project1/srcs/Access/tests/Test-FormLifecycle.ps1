[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$Fixture,
    [ValidatePattern('^[A-Za-z0-9_-]+$')][string]$RunId='manual',
    [string]$ReportDirectory=''
)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '../tools/GeneratedPaths.ps1')
$taskRoot=$script:AccessMethodRoot
$taskSource=Resolve-AccessGeneratedPath $Fixture '.tmp'
$taskDatabase=Resolve-AccessGeneratedPath (Join-Path $taskRoot '.tmp/tests/lifecycle.accdb') '.tmp'
if($taskSource -eq $taskDatabase){throw 'The populated source fixture and lifecycle copy must be distinct.'}
if(-not $ReportDirectory){$ReportDirectory=Join-Path $taskRoot 'build/test-results'}
$taskReport=Resolve-AccessReportPath $ReportDirectory
New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($taskDatabase)),$taskReport -Force|Out-Null
$taskRecord=Join-Path $taskReport 'form-lifecycle.json'
$taskStarted=[DateTime]::UtcNow
$taskOriginalHash=(Get-FileHash -LiteralPath $taskSource -Algorithm SHA256).Hash
$taskSources=@('Build-Access.ps1','tests/Test-FormLifecycle.ps1')
foreach($taskFolder in @('Modules','Classes','database')) {
    $taskSources+=@(Get-ChildItem -LiteralPath (Join-Path $taskRoot $taskFolder) -Recurse -File|ForEach-Object {$_.FullName.Substring($taskRoot.Length+1).Replace('\','/')})
}
$taskInventory=@($taskSources|Sort-Object -Unique|ForEach-Object {[ordered]@{file=$_;sha256=(Get-FileHash -LiteralPath (Join-Path $taskRoot $_) -Algorithm SHA256).Hash}})
[ordered]@{status='Running';runId=$RunId;startedAt=$taskStarted.ToString('o');sourceSha256=$taskOriginalHash;formalScore=$null}|ConvertTo-Json|Set-Content -LiteralPath $taskRecord -Encoding UTF8
$taskIterations=New-Object 'Collections.Generic.List[object]'
$taskChecks=New-Object 'Collections.Generic.List[object]'
$taskApp=$null;$taskProcess=$null;$taskFatal=$null;$taskQuitError=$null;$taskOwnedId=0;$taskExitCode=$null;$taskExitObserved=$false;$taskForcedTermination=$false
$taskBeforeCounts=$null;$taskAfterCounts=$null;$taskVersion=$null;$taskEvents=@()
function Add-LifecycleCheck([string]$Name,[bool]$Passed,[string]$Detail='') {
    $taskChecks.Add([ordered]@{name=$Name;passed=$Passed;detail=$Detail})
    Write-Output "$(if($Passed){'PASS'}else{'FAIL'}): $Name $Detail"
}
function Read-LifecycleCounts($Application) {
    $taskCountDb=$null;$taskCountRows=$null
    $taskCounts=[ordered]@{}
    try {
        $taskCountDb=$Application.CurrentDb()
        foreach($taskTable in @('m_code_category','m_code','m_class','m_student','t_operation_log','t_write_guard')) {
            $taskCountRows=$taskCountDb.OpenRecordset("SELECT Count(*) AS n FROM [$taskTable]",4)
            $taskCounts[$taskTable]=[long]$taskCountRows.Fields.Item('n').Value
            $taskCountRows.Close()
            [Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskCountRows)|Out-Null
            $taskCountRows=$null
        }
    } finally {
        if($null -ne $taskCountRows){try{$taskCountRows.Close()}catch{};[Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskCountRows)|Out-Null;$taskCountRows=$null}
        if($null -ne $taskCountDb){try{$taskCountDb.Close()}catch{};[Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskCountDb)|Out-Null;$taskCountDb=$null}
    }
    return ,$taskCounts
}
function Counts-Equal($First,$Second) {
    foreach($taskTable in $First.Keys){if($First[$taskTable] -ne $Second[$taskTable]){return $false}}
    return $true
}
Add-Type -TypeDefinition @'
using System;using System.Runtime.InteropServices;
public static class AccessLifecycleProcess {
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hwnd,out uint processId);
}
'@
$taskExistingIds=@(Get-Process MSACCESS -ErrorAction SilentlyContinue|Select-Object -ExpandProperty Id)
try {
    Copy-Item -LiteralPath $taskSource -Destination $taskDatabase -Force
    $taskApp=New-Object -ComObject Access.Application
    $taskApp.Visible=$false
    [uint32]$taskProcessId=0
    [void][AccessLifecycleProcess]::GetWindowThreadProcessId([IntPtr]([long]$taskApp.hWndAccessApp()),[ref]$taskProcessId)
    $taskOwnedId=[int]$taskProcessId
    if($taskOwnedId -eq 0 -or $taskOwnedId -in $taskExistingIds){throw 'Access did not create a uniquely owned test process.'}
    $taskProcess=Get-Process -Id $taskOwnedId
    [void]$taskProcess.Handle
    $taskOwnedStart=$taskProcess.StartTime.ToUniversalTime()
    if($taskOwnedStart -lt $taskStarted.AddSeconds(-2)){throw 'Owned Access process predates this test.'}
    $taskVersion=[string]$taskApp.Version
    $taskApp.OpenCurrentDatabase($taskDatabase)
    $taskBeforeCounts=Read-LifecycleCounts $taskApp
    Add-LifecycleCheck 'Populated fixture contains students and classes' ($taskBeforeCounts['m_student'] -gt 0 -and $taskBeforeCounts['m_class'] -gt 0)
    for($taskRound=1;$taskRound -le 10;$taskRound++) {
        $taskRoundStarted=[DateTime]::UtcNow
        $taskOutput=[string]$taskApp.Run('RunFormTests')
        $taskCheckLog=[string]$taskApp.Run('TestCheckLog')
        $taskCounts=Read-LifecycleCounts $taskApp
        $taskPassed=$taskOutput -match '^\d+ assertions passed$'
        $taskSame=Counts-Equal $taskBeforeCounts $taskCounts
        $taskIterations.Add([ordered]@{iteration=$taskRound;startedAt=$taskRoundStarted.ToString('o');completedAt=[DateTime]::UtcNow.ToString('o');output=$taskOutput;passed=$taskPassed;businessCountsUnchanged=$taskSame;counts=$taskCounts;checks=$taskCheckLog})
        Add-LifecycleCheck ("Same-process form lifecycle iteration $taskRound") ($taskPassed -and $taskSame) $taskOutput
        if(-not $taskPassed -or -not $taskSame){throw "Lifecycle iteration $taskRound failed or changed business counts."}
    }
    $taskAfterCounts=Read-LifecycleCounts $taskApp
    Add-LifecycleCheck 'All ten iterations leave business and audit counts unchanged' (Counts-Equal $taskBeforeCounts $taskAfterCounts)
} catch {$taskFatal=$_.Exception.ToString()+[Environment]::NewLine+$_.ScriptStackTrace;Write-Output $taskFatal}
finally {
    if($null -ne $taskApp) {
        try{$taskApp.CloseCurrentDatabase()}catch{$taskQuitError='CloseCurrentDatabase: '+$_.Exception.Message}
        [GC]::Collect();[GC]::WaitForPendingFinalizers()
        try{$taskApp.Quit(2)}catch{$taskQuitError=($taskQuitError+' Quit: '+$_.Exception.Message).Trim()}
        try{[Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskApp)|Out-Null}catch{$taskQuitError=($taskQuitError+' Release: '+$_.Exception.Message).Trim()}
        $taskApp=$null
        [GC]::Collect();[GC]::WaitForPendingFinalizers()
    }
    if($null -ne $taskProcess) {
        try {
            $taskExitObserved=$taskProcess.WaitForExit(10000)
            if($taskExitObserved){$taskExitCode=$taskProcess.ExitCode}
            elseif($taskOwnedId -notin $taskExistingIds){
                $taskCurrent=Get-Process -Id $taskOwnedId -ErrorAction SilentlyContinue
                if($taskCurrent -and $taskCurrent.StartTime.ToUniversalTime() -eq $taskOwnedStart){Stop-Process -Id $taskOwnedId -Force;$taskForcedTermination=$true}
            }
        } catch {$taskQuitError=($taskQuitError+' Process observation: '+$_.Exception.Message).Trim()}
        $taskProcess.Dispose()
    }
    Add-LifecycleCheck 'Owned Access process exits normally without forced termination' ($taskExitObserved -and $taskExitCode -eq 0 -and -not $taskForcedTermination -and -not $taskQuitError) ("pid=$taskOwnedId exit=$taskExitCode error=$taskQuitError")
    if($taskOwnedId -gt 0) {
        $taskPidPattern='0x'+$taskOwnedId.ToString('x')+'\b'
        $taskEvents=@(Get-WinEvent -FilterHashtable @{LogName='Application';Id=1000;StartTime=$taskStarted.ToLocalTime()} -ErrorAction SilentlyContinue |Where-Object {$_.Message -match 'MSACCESS.EXE' -and $_.Message -match $taskPidPattern}|ForEach-Object {[ordered]@{time=$_.TimeCreated.ToUniversalTime().ToString('o');eventId=$_.Id;message=$_.Message}})
    }
    Add-LifecycleCheck 'No native application-crash event for the owned process' ($taskEvents.Count -eq 0)
    $taskFinalSourceHash=(Get-FileHash -LiteralPath $taskSource -Algorithm SHA256).Hash
    Add-LifecycleCheck 'Original populated fixture is byte-for-byte unchanged' ($taskFinalSourceHash -eq $taskOriginalHash) $taskFinalSourceHash
    $taskChanged=@($taskInventory|Where-Object {(Get-FileHash -LiteralPath (Join-Path $taskRoot $_.file) -Algorithm SHA256).Hash -ne $_.sha256})
    Add-LifecycleCheck 'Product and test sources stay frozen during lifecycle execution' ($taskChanged.Count -eq 0) ($taskChanged.file -join ';')
    $taskFailures=@($taskChecks|Where-Object {-not $_.passed}).Count
    $taskStatus=if(-not $taskFatal -and $taskFailures -eq 0 -and $taskIterations.Count -eq 10){'Passed'}else{'Failed'}
    [ordered]@{status=$taskStatus;runId=$RunId;startedAt=$taskStarted.ToString('o');completedAt=[DateTime]::UtcNow.ToString('o');sourceFixture=$taskSource;sourceSha256=$taskOriginalHash;sourceSha256After=$taskFinalSourceHash;testFixture='.tmp/tests/lifecycle.accdb';fixtureOnly=$true;sourceFiles=$taskInventory;officeVersion=$taskVersion;apartment=[Threading.Thread]::CurrentThread.GetApartmentState().ToString();ownedProcess=$taskOwnedId;exitObserved=$taskExitObserved;processExitCode=$taskExitCode;forcedTermination=$taskForcedTermination;quitError=$taskQuitError;completedIterations=$taskIterations.Count;iterations=$taskIterations;countsBefore=$taskBeforeCounts;countsAfter=$taskAfterCounts;passed=@($taskChecks|Where-Object {$_.passed}).Count;failed=$taskFailures;checks=$taskChecks;applicationCrashEvents=$taskEvents;formalScore=$null;scope='Ten same-process RunFormTests iterations with actual native forms and unchanged business/audit counts; normal Access process exit required';notExecuted=@('root-cause proof for the earlier intermittent crash','Office 32-bit','production/shared database');fatal=$taskFatal}|ConvertTo-Json -Depth 12|Set-Content -LiteralPath $taskRecord -Encoding UTF8
}
if($taskStatus -ne 'Passed'){exit 1}
