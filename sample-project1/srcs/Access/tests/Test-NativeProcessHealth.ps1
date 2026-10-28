[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$StartedAt,
    [ValidatePattern('^[A-Za-z0-9_-]+$')][string]$RunId='manual',
    [string]$ExistingProcessIds='',
    [string]$ReportDirectory=''
)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '../tools/GeneratedPaths.ps1')
if(-not $ReportDirectory){$ReportDirectory=Join-Path $script:AccessMethodRoot 'build/test-results'}
$taskReport=Resolve-AccessReportPath $ReportDirectory
New-Item -ItemType Directory -Path $taskReport -Force|Out-Null
$taskFrom=[DateTimeOffset]::Parse($StartedAt).UtcDateTime
$taskTo=[DateTime]::UtcNow
$taskExcluded=@($ExistingProcessIds -split ','|Where-Object {$_ -match '^\d+$'}|ForEach-Object {[int]$_})
$taskEvents=@();$taskFatal=$null
try {
    try{$taskCandidates=@(Get-WinEvent -FilterHashtable @{LogName='Application';Id=1000;StartTime=$taskFrom.ToLocalTime();EndTime=$taskTo.ToLocalTime()} -ErrorAction Stop)}
    catch{if($_.FullyQualifiedErrorId -like 'NoMatchingEventsFound*'){$taskCandidates=@()}else{throw}}
    foreach($taskEvent in $taskCandidates){
        $taskXml=[xml]$taskEvent.ToXml();$taskData=@{}
        foreach($taskValue in $taskXml.Event.EventData.Data){$taskData[$taskValue.Name]=[string]$taskValue.'#text'}
        if($taskData['AppName'] -ine 'MSACCESS.EXE'){continue}
        $taskPidText=$taskData['ProcessId'];$taskPid=0
        if($taskPidText -match '^0x[0-9a-f]+$'){$taskPid=[Convert]::ToInt32($taskPidText.Substring(2),16)}
        elseif($taskPidText -match '^\d+$'){$taskPid=[int]$taskPidText}
        if($taskPid -in $taskExcluded){continue}
        $taskEvents+=[ordered]@{time=$taskEvent.TimeCreated.ToUniversalTime().ToString('o');eventId=1000;processId=$taskPid;application=$taskData['AppName'];module=$taskData['ModuleName'];exceptionCode=$taskData['ExceptionCode'];offset=$taskData['FaultingOffset'];reportId=$taskData['IntegratorReportId']}
    }
}catch{$taskFatal=$_.Exception.Message}
$taskStatus=if(-not $taskFatal -and $taskEvents.Count -eq 0){'Passed'}else{'Failed'}
[ordered]@{status=$taskStatus;runId=$RunId;startedAt=$taskFrom.ToString('o');completedAt=$taskTo.ToString('o');scope='Windows Application Error events for Access processes during this verification window; pre-existing user processes excluded';existingProcessIds=$taskExcluded;applicationCrashEvents=$taskEvents;singleEarlierCrashRootCauseProven=$false;fatal=$taskFatal;formalScore=$null}|ConvertTo-Json -Depth 6|Set-Content -LiteralPath (Join-Path $taskReport 'native-process-health.json') -Encoding UTF8
Write-Output ("Native Access process health: $taskStatus, crashes=$($taskEvents.Count)")
if($taskStatus -ne 'Passed'){exit 1}
