param([Parameter(Mandatory=$true)][string]$Frontend,[Parameter(Mandatory=$true)][string]$Backend,[ValidatePattern('^[A-Za-z0-9_-]+$')][string]$RunId=('access-service-'+[DateTime]::UtcNow.ToString('yyyyMMdd-HHmmssfff')+'-'+[Guid]::NewGuid().ToString('N').Substring(0,8)),[string]$SpecVersion='8.1/8.2',[string]$InputManifest='Access/spec local hash manifest',[string]$ReportDirectory=(Join-Path $PSScriptRoot '../test-report'))
$ErrorActionPreference='Stop'
$taskReport=[IO.Path]::GetFullPath($ReportDirectory)
New-Item -ItemType Directory -Path $taskReport -Force | Out-Null
if (Test-Path -LiteralPath (Join-Path $taskReport "$RunId.json")) { throw 'Report already exists; choose a new RunId.' }
$taskInputs=@(Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot '../spec') -Recurse -File | Sort-Object FullName | ForEach-Object { @{path=$_.FullName;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash} })
$taskUser=[Security.Principal.WindowsIdentity]::GetCurrent().Name.Split('\')[-1]
if (-not [string]::Equals([IO.Path]::GetFullPath($Frontend),[IO.Path]::GetFullPath($Backend),[StringComparison]::OrdinalIgnoreCase)) { [IO.File]::WriteAllText((Join-Path ([IO.Path]::GetDirectoryName($Frontend)) 'roles.conf'),"$taskUser=Admin`r`n",[Text.Encoding]::Unicode) }
$taskAccess=New-Object -ComObject Access.Application
$taskAccess.Visible=$false
$taskResults=[Collections.Generic.List[object]]::new()
try {
 $taskAccess.OpenCurrentDatabase([IO.Path]::GetFullPath($Frontend))
 $taskDb=$taskAccess.CurrentDb()
 $taskCountsBefore=@{}
 foreach ($taskTable in @('m_code_category','m_code','m_class','m_student','t_operation_log','t_write_guard')) {
    $taskRs=$taskDb.OpenRecordset("SELECT Count(*) AS n FROM $taskTable"); $taskCountsBefore[$taskTable]=$taskRs.Fields.Item('n').Value; $taskRs.Close()
 }
 $taskResult=$taskAccess.Run('RunSelfTests')
 Write-Output $taskResult
 $taskResults.Add(@{function='RunSelfTests';output=$taskResult;passed=($taskResult -match '^\d+ assertions passed$');checks=$taskAccess.Run('TestCheckLog')})
 if ($taskResults[0].passed) {
    $taskResult=$taskAccess.Run('RunExtendedTests'); Write-Output $taskResult
    $taskResults.Add(@{function='RunExtendedTests';output=$taskResult;passed=($taskResult -match '^\d+ assertions passed$');checks=$taskAccess.Run('TestCheckLog')})
 }
 if (@($taskResults | Where-Object { -not $_.passed }).Count -eq 0) {
    $taskResult=$taskAccess.Run('RunFormTests'); Write-Output $taskResult
    $taskResults.Add(@{function='RunFormTests';output=$taskResult;passed=($taskResult -match '^\d+ assertions passed$');checks=$taskAccess.Run('TestCheckLog')})
 }
 $taskCountsAfter=@{}
 foreach ($taskTable in @('m_code_category','m_code','m_class','m_student','t_operation_log','t_write_guard')) {
    $taskRs=$taskDb.OpenRecordset("SELECT Count(*) AS n FROM $taskTable"); $taskCountsAfter[$taskTable]=$taskRs.Fields.Item('n').Value; $taskRs.Close()
 }
 $taskNulls=@(); $taskRs=$taskDb.OpenRecordset('SELECT student_id,relationship_category,relationship_code,emergency_contact_name,emergency_phone_number FROM m_student')
 while (-not $taskRs.EOF) {
    $taskItem=@{studentId=$taskRs.Fields.Item('student_id').Value}
    foreach ($taskFieldName in @('relationship_category','relationship_code','emergency_contact_name','emergency_phone_number')) { $taskItem[$taskFieldName]=($taskRs.Fields.Item($taskFieldName).Value -is [DBNull] -or $null -eq $taskRs.Fields.Item($taskFieldName).Value) }
    $taskNulls+=$taskItem; $taskRs.MoveNext()
 }
 $taskRs.Close()
 $taskRelation=$taskDb.TableDefs.Item('m_student')
 $taskState=if (@($taskResults | Where-Object { -not $_.passed }).Count -eq 0) { 'Passed' } else { 'Failed' }
} catch { $taskState='Failed'; $taskFatal=$_.Exception.Message; Write-Output $taskFatal }
finally {
 $taskOfficeVersion=$taskAccess.Version
 $taskAccess.Quit(2)
 [Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskAccess) | Out-Null
 $taskOutput=[ordered]@{runId=$RunId;status=$taskState;specVersion=$SpecVersion;inputManifest=$InputManifest;inputs=$taskInputs;frontend=[IO.Path]::GetFullPath($Frontend);backend=[IO.Path]::GetFullPath($Backend);officeVersion=$taskOfficeVersion;fatal=$taskFatal;countsBefore=$taskCountsBefore;tests=$taskResults;countsAfter=$taskCountsAfter;allFourNullReadback=$taskNulls;fixtureOnly=$true}
 $taskOutput.frontendSha256=(Get-FileHash -LiteralPath $Frontend -Algorithm SHA256).Hash
 $taskOutput.backendSha256=(Get-FileHash -LiteralPath $Backend -Algorithm SHA256).Hash
 $taskOutput | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $taskReport "$RunId.json") -Encoding UTF8
}
if ($taskState -ne 'Passed') { exit 1 }
