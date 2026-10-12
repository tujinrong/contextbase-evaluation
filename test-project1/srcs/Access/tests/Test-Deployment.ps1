param([string]$Database=(Join-Path $PSScriptRoot '../StudentManagement.accdb'),[ValidatePattern('^[A-Za-z0-9_-]+$')][string]$RunId=('access-deployment-'+[DateTime]::UtcNow.ToString('yyyyMMdd-HHmmssfff')+'-'+[Guid]::NewGuid().ToString('N').Substring(0,8)),[string]$ReportDirectory=(Join-Path $PSScriptRoot '../test-report'),[string]$SourceDatabase)
$ErrorActionPreference='Stop'
$taskReport=[IO.Path]::GetFullPath($ReportDirectory)
New-Item -ItemType Directory -Path $taskReport -Force | Out-Null
if (Test-Path -LiteralPath (Join-Path $taskReport "$RunId.json")) { throw 'Report already exists; choose a new RunId.' }
$taskSource=if ($SourceDatabase) { [IO.Path]::GetFullPath($SourceDatabase) } else { [IO.Path]::GetFullPath($Database) }
if ($SourceDatabase) { $taskFile=[IO.Path]::GetFullPath($Database) }
else {
 $taskFile=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot "../build/$RunId.accdb"))
 New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($taskFile)) -Force | Out-Null
 if (Test-Path -LiteralPath $taskFile) { throw 'A fresh deployment copy is required; choose a new RunId.' }
 Copy-Item -LiteralPath $taskSource -Destination $taskFile
}
$taskBeforeHash=(Get-FileHash -LiteralPath $taskFile -Algorithm SHA256).Hash
$taskSourceHash=(Get-FileHash -LiteralPath $taskSource -Algorithm SHA256).Hash
$taskAccess=New-Object -ComObject Access.Application
$taskCounts=@{}; $taskTables=@(); $taskRelations=@(); $taskModules=@(); $taskForms=@(); $taskChecks=@()
function Check-Deployment([bool]$condition,[string]$name) { $script:taskChecks+=@{name=$name;passed=$condition}; Write-Output "$(if($condition){'PASS'}else{'FAIL'}): $name" }
try {
 $taskAccess.Visible=$false; $taskAccess.OpenCurrentDatabase($taskFile); $taskDb=$taskAccess.CurrentDb()
 $taskHealth=$taskAccess.Run('DeploymentHealth'); Write-Output $taskHealth
 Check-Deployment ($taskHealth -like 'PASS|*') 'actual startup/form/DAO service health'
 foreach ($taskTd in $taskDb.TableDefs) {
  if ($taskTd.Name -like 'MSys*') { continue }
  $taskTables+=@{name=$taskTd.Name;connect=$taskTd.Connect;validationRule=$taskTd.ValidationRule}
  $taskRs=$taskDb.OpenRecordset("SELECT Count(*) AS n FROM [$($taskTd.Name)]"); $taskCounts[$taskTd.Name]=$taskRs.Fields.Item('n').Value; $taskRs.Close()
 }
 Check-Deployment (@($taskTables | Where-Object {$_.connect -ne ''}).Count -eq 0) 'all physical tables local; no external links'
 Check-Deployment ($taskCounts.m_code_category -eq 5 -and $taskCounts.m_code -eq 70) 'initial five categories / seventy codes'
 Check-Deployment ($taskCounts.m_class -eq 0 -and $taskCounts.m_student -eq 0 -and $taskCounts.t_operation_log -eq 0) 'no sample class/student/audit in final binary'
 Check-Deployment ($taskCounts.t_write_guard -eq 1 -and $taskCounts.t_app_role -eq 1) 'one gate and one embedded evaluation subject'
 $taskRs=$taskDb.OpenRecordset('SELECT lock_bit FROM t_write_guard WHERE guard_id=1'); $taskLock=$taskRs.Fields.Item('lock_bit').Value; $taskRs.Close()
 Check-Deployment ($taskLock -eq $false) 'deployment health rolls gate back'
 foreach ($taskRelationSpec in (Get-Content -LiteralPath (Join-Path $PSScriptRoot '../database/relations.json') -Encoding UTF8 -Raw | ConvertFrom-Json)) {
  $taskRelation=$taskDb.Relations.Item($taskRelationSpec.name); $taskFields=@()
  foreach ($taskField in $taskRelation.Fields) { $taskFields+=@{parent=$taskField.Name;child=$taskField.ForeignName} }
  $taskRelations+=@{name=$taskRelation.Name;attributes=$taskRelation.Attributes;parent=$taskRelation.Table;child=$taskRelation.ForeignTable;fields=$taskFields}
  Check-Deployment (($taskRelation.Attributes -band (2+256+4096)) -eq 0) "enforced noncascade relation $($taskRelation.Name)"
 }
 foreach ($taskName in @('relationship_category','relationship_code')) {
  $taskField=$taskDb.TableDefs.Item('m_student').Fields.Item($taskName)
  Check-Deployment (-not $taskField.Required -and -not $taskField.AllowZeroLength -and $taskField.DefaultValue -eq '') "optional $taskName has true NULL/no default"
 }
 foreach ($taskComponent in $taskAccess.VBE.ActiveVBProject.VBComponents) { $taskModules+=@{name=$taskComponent.Name;kind=$taskComponent.Type;lines=$taskComponent.CodeModule.CountOfLines} }
 foreach ($taskObject in $taskAccess.CurrentProject.AllForms) { $taskForms+=$taskObject.Name }
 Check-Deployment ($taskForms.Count -eq 4) 'all four generated executable forms'
 Check-Deployment (@($taskModules | Where-Object {$_.name -eq 'modSelfTests'}).Count -eq 0) 'test-only module excluded from final binary'
 Check-Deployment ($taskDb.Properties.Item('StartupForm').Value -eq 'frmStudentSearch' -and $taskDb.Properties.Item('StudentBackendPath').Value -eq 'SELF') 'single file is configured as startup executable'
 $taskSeed=Get-Content -LiteralPath (Join-Path $PSScriptRoot '../database/seed.json') -Encoding UTF8 -Raw | ConvertFrom-Json
 $taskProtected=0; $taskRs=$taskDb.OpenRecordset('SELECT Count(*) AS n FROM m_code WHERE category_id="ENROLLMENT_STATUS" AND is_protected=True'); $taskProtected=$taskRs.Fields.Item('n').Value; $taskRs.Close()
 Check-Deployment ($taskProtected -eq 4) 'all four enrollment codes are protected'
 $taskState=if (@($taskChecks | Where-Object {-not $_.passed}).Count -eq 0) {'Passed'} else {'Failed'}
} catch { $taskState='Failed'; $taskFatal=$_.Exception.Message; Write-Output $taskFatal }
finally {
 $taskVersion=$taskAccess.Version
 if ($null -ne $taskDb) { $taskDb.Close(); [Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskDb) | Out-Null; $taskDb=$null }
 $taskField=$null; $taskRelation=$null; $taskRs=$null; $taskTd=$null; $taskComponent=$null; $taskObject=$null
 [GC]::Collect(); [GC]::WaitForPendingFinalizers()
 $taskAccess.CloseCurrentDatabase()
 $taskAccess.Quit(2); [Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskAccess) | Out-Null
 [GC]::Collect(); [GC]::WaitForPendingFinalizers()
 $taskInputs=@(Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot '../spec') -Recurse -File | Sort-Object FullName | ForEach-Object { @{path=$_.FullName;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash} })
 $taskOutput=[ordered]@{runId=$RunId;status=$taskState;specConfigurationVersion='8.1';specDatabaseIndexVersion='8.2';specBusinessVersion='8.0';database=$taskFile;databaseBeforeSha256=$taskBeforeHash;databaseSha256=(Get-FileHash -LiteralPath $taskFile -Algorithm SHA256).Hash;sourceDatabase=$taskSource;sourceBeforeSha256=$taskSourceHash;sourceAfterSha256=(Get-FileHash -LiteralPath $taskSource -Algorithm SHA256).Hash;exactSourceCopy=($taskBeforeHash -eq $taskSourceHash);officeVersion=$taskVersion;fixtureOnly=($taskFile -ne $taskSource);health=$taskHealth;counts=$taskCounts;checks=$taskChecks;physicalTables=$taskTables;relations=$taskRelations;forms=$taskForms;modules=$taskModules;fatal=$taskFatal;inputs=$taskInputs;notTested=@('Office 32-bit','LAN outage','manual pixel/layout review','10000/10001-record search performance','commit-response loss')}
 $taskOutput | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $taskReport "$RunId.json") -Encoding UTF8
}
if ($taskState -ne 'Passed') { exit 1 }
