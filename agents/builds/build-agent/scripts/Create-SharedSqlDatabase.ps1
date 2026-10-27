[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9][A-Za-z0-9_-]{0,49}$')][string]$RunId,
    [switch]$Execute,
    [switch]$VerifyOnly
)
$ErrorActionPreference='Stop'
if($Execute -and $VerifyOnly){throw 'Choose Execute or VerifyOnly.'}
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..'))
$report=Join-Path $workspace 'test-project1\build\shared-db'
$database='contextbase_test_project1'
$state=[ordered]@{status='PLAN_ONLY';project='test-project1';server='tcp:127.0.0.1,1433';provider='ODBC Driver 18 for SQL Server';hostnameInCertificate='localhost';database=$database;authentication='Windows only';encrypt=$true;trustServerCertificate=$false;compatibilityLevel=160;schemaStatus='EMPTY_PENDING_SHARED_DATABASE_CONTRACT';existingDatabasePolicy='Refuse creation if present; never drop or overwrite';notRun=@('Shared schema/roles/normalization/locking deployment','Non-sysadmin application authentication and CRUD','Access linked SQL backend migration','IBM i connection and Windows identity mapping')}
if(-not $Execute -and -not $VerifyOnly){$state | ConvertTo-Json -Depth 6;return}
New-Item -ItemType Directory -Path $report -Force | Out-Null
$state.status='RUNNING';$state.started=(Get-Date).ToString('o');$state.databaseCreated=$false;$state.error=$null
function Save-State {$state | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $report 'shared-database.json') -Encoding UTF8}
$cn=New-Object System.Data.Odbc.OdbcConnection('Driver={ODBC Driver 18 for SQL Server};Server=tcp:127.0.0.1,1433;HostnameInCertificate=localhost;Database=master;Trusted_Connection=Yes;Encrypt=Yes;TrustServerCertificate=No;APP=contextbase shared DB provisioning;')
$cn.ConnectionTimeout=10
try {
    Save-State;$cn.Open();$cmd=$cn.CreateCommand()
    $cmd.CommandText="SELECT CONVERT(nvarchar(128),SERVERPROPERTY('Edition')) edition,CONVERT(nvarchar(128),SERVERPROPERTY('ProductVersion')) version,CONVERT(int,SERVERPROPERTY('IsIntegratedSecurityOnly')) windows_only,ORIGINAL_LOGIN() original_login,IS_SRVROLEMEMBER('sysadmin') sysadmin,(SELECT encrypt_option FROM sys.dm_exec_connections WHERE session_id=@@SPID) encrypt_option"
    $table=New-Object Data.DataTable;$table.Load($cmd.ExecuteReader());$r=$table.Rows[0]
    $state.serverVerification=@{edition=[string]$r.edition;version=[string]$r.version;windowsOnly=[int]$r.windows_only;originalLogin=[string]$r.original_login;sysadmin=[int]$r.sysadmin;encrypted=[string]$r.encrypt_option}
    if($r.version -ne '17.0.5005.3' -or $r.edition -notmatch 'Express' -or [int]$r.windows_only -ne 1 -or $r.encrypt_option -ne 'TRUE'){throw 'Server edition/version/Windows authentication/TLS mismatch.'}
    if([int]$r.sysadmin -ne 1){throw 'Provisioning verification requires an administrator for complete metadata visibility; application identity tests are separate.'}
    $cmd.CommandText="SELECT COUNT(*) FROM sys.databases WHERE name=N'contextbase_test_project1'"
    $exists=[int]$cmd.ExecuteScalar()
    if($Execute) {
        if($exists -ne 0){throw 'Shared database already exists; no modification was performed.'}
        if([int]$r.sysadmin -ne 1){throw 'Provisioning requires a server administrator; application identity tests are separate.'}
        $cmd.CommandText='CREATE DATABASE [contextbase_test_project1] COLLATE Japanese_XJIS_140_CI_AS;'
        [void]$cmd.ExecuteNonQuery();$state.databaseCreated=$true;Save-State
        $cmd.CommandText='ALTER DATABASE [contextbase_test_project1] SET COMPATIBILITY_LEVEL=160; ALTER AUTHORIZATION ON DATABASE::[contextbase_test_project1] TO [sa];'
        [void]$cmd.ExecuteNonQuery()
    } elseif($exists -ne 1){throw 'Shared database does not exist.'}
    # Express may close an idle AUTO_CLOSE database, making sys.databases.collation_name NULL.
    # Open this database before reading its metadata; VerifyOnly does not change its options.
    $cn.ChangeDatabase($database)
    $cmd.CommandText="SELECT name,state_desc,compatibility_level,collation_name,SUSER_SNAME(owner_sid) owner_name FROM sys.databases WHERE name=N'contextbase_test_project1'"
    $table=New-Object Data.DataTable;$table.Load($cmd.ExecuteReader());$r=$table.Rows[0]
    $state.databaseVerification=@{name=[string]$r.name;state=[string]$r.state_desc;compatibilityLevel=[int]$r.compatibility_level;collation=[string]$r.collation_name;owner=[string]$r.owner_name}
    if($r.state_desc -ne 'ONLINE' -or [int]$r.compatibility_level -ne 160 -or $r.collation_name -ne 'Japanese_XJIS_140_CI_AS' -or $r.owner_name -ne 'sa'){throw 'Shared database metadata mismatch.'}
    $cmd.CommandText='SELECT COUNT(*) FROM sys.tables WHERE is_ms_shipped=0'
    $state.userTableCount=[int]$cmd.ExecuteScalar()
    if($state.userTableCount -ne 0){throw 'Expected empty shared DB pending a corrected shared deployment contract.'}
    $cmd.CommandText='SELECT COUNT(*) FROM sys.objects WHERE is_ms_shipped=0'
    $state.userObjectCount=[int]$cmd.ExecuteScalar()
    $cmd.CommandText='SELECT COUNT(*) FROM sys.assemblies WHERE is_user_defined=1'
    $state.userAssemblyCount=[int]$cmd.ExecuteScalar()
    $cmd.CommandText="SELECT COUNT(*) FROM sys.database_principals WHERE type='R' AND is_fixed_role=0 AND name<>N'public'"
    $state.applicationRoleCount=[int]$cmd.ExecuteScalar()
    if($state.userObjectCount -ne 0 -or $state.userAssemblyCount -ne 0 -or $state.applicationRoleCount -ne 0){throw 'User objects, assemblies or application roles already exist; shared deployment remains blocked.'}
    $cn.ChangeDatabase('master')
    $cmd.CommandText="SELECT name FROM sys.databases WHERE database_id>4 ORDER BY name"
    $reader=$cmd.ExecuteReader();$names=@();while($reader.Read()){$names += $reader.GetString(0)};$reader.Dispose()
    $state.userDatabases=$names
    if(@($names | Where-Object {$_ -match '^contextbase_test_project1_(wpf|vb|mvc|vue|cobol)$'}).Count -ne 0){throw 'Obsolete profile-specific database exists; report it rather than deleting it.'}
    $state.status='INFRASTRUCTURE_PASSED_MIGRATION_BLOCKED';$state.applicationAuthorizationVerified=$false
} catch {$state.status='FAILED';$state.error=$_.Exception.ToString();Write-Error -Message $state.error -ErrorAction Continue}
finally {$cn.Dispose();$state.finished=(Get-Date).ToString('o');Save-State}
if($state.status -eq 'FAILED'){exit 1}
