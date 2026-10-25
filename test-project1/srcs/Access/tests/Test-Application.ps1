param([string]$Frontend='',[string]$Backend='',[ValidatePattern('^[A-Za-z0-9_-]+$')][string]$RunId='application',[string]$SpecVersion='8.1/8.2',[string]$InputManifest='Access/spec local hash manifest',[string]$ReportDirectory='')
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '../tools/GeneratedPaths.ps1')
if (-not $ReportDirectory) { $ReportDirectory=Join-Path $script:AccessMethodRoot 'build/test-results' }
if (-not $Frontend) { $Frontend=Join-Path $script:AccessMethodRoot '.tmp/tests/application.accdb' }
if (-not $Backend) { $Backend=$Frontend }
$taskReport=Resolve-AccessReportPath $ReportDirectory
New-Item -ItemType Directory -Path $taskReport -Force | Out-Null
$Frontend=Resolve-AccessGeneratedPath $Frontend '.tmp'
$Backend=Resolve-AccessGeneratedPath $Backend '.tmp'
Remove-AccessIntermediate (Join-Path ([IO.Path]::GetDirectoryName($Frontend)) 'fixture-progress.log')
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
    $taskResult=$taskAccess.Run('RunSearchContractTests'); Write-Output $taskResult
    $taskResults.Add(@{function='RunSearchContractTests';output=$taskResult;passed=($taskResult -match '^\d+ assertions passed$');checks=$taskAccess.Run('TestCheckLog')})
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
 if ($null -ne $taskRs) { try { $taskRs.Close() } catch {}; if ([Runtime.InteropServices.Marshal]::IsComObject($taskRs)) { [Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskRs) | Out-Null }; $taskRs=$null }
 if ($null -ne $taskRelation) { if ([Runtime.InteropServices.Marshal]::IsComObject($taskRelation)) { [Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskRelation) | Out-Null }; $taskRelation=$null }
 if ($null -ne $taskDb) { $taskDb.Close(); [Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskDb) | Out-Null; $taskDb=$null }
 [GC]::Collect(); [GC]::WaitForPendingFinalizers()
 $taskAccess.CloseCurrentDatabase()
 $taskAccess.Quit(2)
 [Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskAccess) | Out-Null
 $taskAccess=$null
 [GC]::Collect(); [GC]::WaitForPendingFinalizers()
 $taskOutput=[ordered]@{runId=$RunId;completedAt=[DateTime]::UtcNow.ToString('o');status=$taskState;specVersion=$SpecVersion;inputManifest=$InputManifest;inputs=$taskInputs;frontend=[IO.Path]::GetFullPath($Frontend);backend=[IO.Path]::GetFullPath($Backend);officeVersion=$taskOfficeVersion;fatal=$taskFatal;countsBefore=$taskCountsBefore;tests=$taskResults;countsAfter=$taskCountsAfter;allFourNullReadback=$taskNulls;fixtureOnly=$true}
 $taskOutput.frontendSha256=(Get-FileHash -LiteralPath $Frontend -Algorithm SHA256).Hash
 $taskOutput.backendSha256=(Get-FileHash -LiteralPath $Backend -Algorithm SHA256).Hash
 $taskOutput | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $taskReport 'application.json') -Encoding UTF8
}
if ($taskState -ne 'Passed') { exit 1 }
