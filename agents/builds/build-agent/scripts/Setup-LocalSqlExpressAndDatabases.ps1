[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9][A-Za-z0-9_-]{0,42}$')][string]$RunId,
    [switch]$Execute
)
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..'))
$project=Join-Path $workspace 'sample-project1'
$work=Join-Path $project '.tmp\sqlserver-setup'
$reports=Join-Path $project 'build\sql-setup'
$administrator=[Security.Principal.WindowsIdentity]::GetCurrent().Name
$plan=[ordered]@{
    status='PLAN_ONLY';project='sample-project1';runId=$RunId;server='tcp:127.0.0.1,1433'
    version='SQL Server 2025 Express CU9 17.0.5005.3';authentication='Windows only'
    windowsAdministrator=$administrator;executeRequested=[bool]$Execute
    removal='Exact MSI removal of installed LocalDB 2016/2019/2025 engines; old database files retained'
    install='SQLEXPRESS engine, CU9, ODBC18.7.1.1, loopback TCP1433, validated IP SAN TLS certificate'
    databases=@('contextbase_test_project1');databaseState='Empty, compatibility160, pending corrected shared deployment contract'
    databasePolicy='One shared SQL database; independently isolated project code and specifications'
    normalization='Deferred; no CLR activation or assembly trust registration'
    reports=$reports;existingDatabasePolicy='Refuse; no overwrite/drop'
    notRun=@('Shared schema/roles/locking deployment','Non-sysadmin application authentication and CRUD','Access SQL backend migration','IBM i SQL connectivity/Windows identity mapping')
}
if(-not $Execute){$plan | ConvertTo-Json -Depth 6;return}
$principal=New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if(-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Use Start-LocalSqlExpressSetup.ps1 for Windows administrator approval.'}
New-Item -ItemType Directory -Path $reports -Force | Out-Null
$plan.status='RUNNING';$plan.started=(Get-Date).ToString('o');$plan.completed=@();$plan.error=$null
function Save-Run {$plan | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $reports 'setup.json') -Encoding UTF8}
try {
    Save-Run
    $global:LASTEXITCODE=0
    & (Join-Path $PSScriptRoot 'Install-LocalSqlExpress.ps1') -WorkDirectory $work -ReportDirectory (Join-Path $reports 'installation') -WindowsAdministrator $administrator *>&1 | Tee-Object -FilePath (Join-Path $reports 'installation-launch.log')
    if($global:LASTEXITCODE -ne 0){throw 'SQL installation verification failed; DB creation stopped.'}
    $install=Get-Content -LiteralPath (Join-Path $reports 'installation\installation.json') -Raw | ConvertFrom-Json
    if($install.status -ne 'PASSED'){throw 'SQL installation did not pass; DB creation stopped.'}
    $plan.completed+='Express installation, Windows authentication and strict TLS verification';Save-Run
    $dbRun=$RunId+'-shared'
    $global:LASTEXITCODE=0
    & (Join-Path $PSScriptRoot 'Create-SharedSqlDatabase.ps1') -RunId $dbRun -Execute
    if($global:LASTEXITCODE -ne 0){throw 'Shared DB creation or verification failed.'}
    $dbReport=Join-Path $project 'build\shared-db\shared-database.json'
    $db=Get-Content -LiteralPath $dbReport -Raw | ConvertFrom-Json
    if($db.status -ne 'INFRASTRUCTURE_PASSED_MIGRATION_BLOCKED'){throw 'Shared DB verification did not pass.'}
    $plan.sharedDatabaseReport=$dbReport
    $plan.completed+='One empty shared DB created and verified'
    $plan.status='INFRASTRUCTURE_PASSED_MIGRATION_BLOCKED';$plan.applicationAuthorizationVerified=$false
} catch {$plan.status='FAILED';$plan.error=$_.Exception.ToString();Write-Error -Message $plan.error -ErrorAction Continue}
finally {$plan.finished=(Get-Date).ToString('o');Save-Run}
if($plan.status -eq 'FAILED'){exit 1}
