[CmdletBinding()]
param(
    [ValidateSet('Plan','CreateEmpty','DeployNew','Validate','ValidateApp')][string]$Mode='Plan',
    [string]$Server='localhost\SQLEXPRESS',
    [string]$SqlcmdPath='sqlcmd.exe',
    [string]$CertificateHostName='localhost',
    [string]$AppWindowsLogin='',
    [string]$DatabaseOwnerLogin='',
    [switch]$AllowAdministrativeAppLogin,
    [switch]$PrepareOnly,
    [ValidateSet('student_viewer','student_staff','student_admin')][string]$ApplicationRole='student_admin',
    [ValidateSet(160,170)][int]$CompatibilityLevel=160,
    [string]$RunId=''
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$projectProfile='VB.NET_WinForms'
$database='contextbase_test_project1_vb'
$sqlFiles=@('001_schema.sql','002_seed.sql','native/000_sqlclr.sql','native/010_student_api.sql','native/020_master_api.sql')
$encoding=New-Object Text.UTF8Encoding($false)
function HashBytes([byte[]]$Bytes,[string]$Algorithm) {
    $algorithmInstance=[Security.Cryptography.HashAlgorithm]::Create($Algorithm)
    try { return [BitConverter]::ToString($algorithmInstance.ComputeHash($Bytes)).Replace('-','') }
    finally { $algorithmInstance.Dispose() }
}
function Literal([string]$Value) { return "N'"+$Value.Replace("'","''")+"'" }
function Identifier([string]$Value) { return '['+$Value.Replace(']',']]')+']' }
function Resolve-ProjectSqlcmd([string]$Requested) {
    $candidates=@()
    if([IO.Path]::IsPathRooted($Requested) -or $Requested.Contains('\') -or $Requested.Contains('/')) {
        $explicit=$ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Requested)
        if(-not [IO.File]::Exists($explicit)) { throw 'The explicitly selected sqlcmd executable is absent.' }
        $candidates=@($explicit)
    } else {
        $candidates=@(Get-Command $Requested -CommandType Application -All -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -Unique)
    }
    foreach($candidate in $candidates) {
        $versionInfo=[Diagnostics.FileVersionInfo]::GetVersionInfo($candidate)
        # FileVersion begins with the release year; ProductMajorPart is the SQL tool major.
        if($versionInfo.ProductMajorPart -ge 16) { return [IO.Path]::GetFullPath($candidate) }
    }
    throw 'A modern ODBC sqlcmd with ProductMajorPart >= 16 is required; legacy SQL90 tools are refused.'
}
$inputs=@()
foreach($relative in $sqlFiles) {
    $full=Join-Path $PSScriptRoot $relative
    if(-not [IO.File]::Exists($full)) { throw "Missing project resource: $relative" }
    $inputs+= [ordered]@{file=$relative;sha256=(HashBytes ([IO.File]::ReadAllBytes($full)) 'SHA256')}
}
$clr=[IO.File]::ReadAllText((Join-Path $PSScriptRoot 'native/000_sqlclr.sql'))
$hashMatch=[regex]::Match($clr,'sys\.trusted_assemblies WHERE hash=0x([0-9A-Fa-f]{128})\)')
$hexMatch=[regex]::Match($clr,'CREATE ASSEMBLY StudentNativeNormalization FROM 0x([0-9A-Fa-f]+) WITH')
if(-not $hashMatch.Success -or -not $hexMatch.Success) { throw 'Exact SQLCLR bytes/hash are required; run the local Build-Native first.' }
$assemblyHash=$hashMatch.Groups[1].Value.ToUpperInvariant()
$hex=$hexMatch.Groups[1].Value
if($hex.Length%2 -ne 0) { throw 'Malformed embedded SQLCLR byte sequence.' }
$assemblyBytes=New-Object byte[] ($hex.Length/2)
for($i=0;$i -lt $assemblyBytes.Length;$i++) { $assemblyBytes[$i]=[Convert]::ToByte($hex.Substring($i*2,2),16) }
if((HashBytes $assemblyBytes 'SHA512') -ne $assemblyHash) { throw 'Embedded assembly differs from its reviewed SHA512.' }
$record=[ordered]@{profile=$projectProfile;database=$database;mode=$Mode;server=$Server;recordedAt=[DateTime]::UtcNow.ToString('o');status='PLAN';engineMajor=17;compatibilityLevel=$CompatibilityLevel;authentication='Windows integrated';encrypt='mandatory; certificate validated';sqlClrSha512=$assemblyHash;inputs=$inputs;applicationLogin=$AppWindowsLogin;applicationRole=$ApplicationRole;databaseOwnerLogin=$DatabaseOwnerLogin;allowAdministrativeAppLogin=[bool]$AllowAdministrativeAppLogin;actualApplicationSessionVerified=$false;phases=@();notRun=@('application CRUD/concurrency/commit failures','real Windows application-role sessions');scope='Deployment and read-only database validation; no server configuration or trusted-assembly registration.'}
if([string]::IsNullOrWhiteSpace($AppWindowsLogin)) { $record.notRun+= 'application identity/permission probes (no non-sysadmin identity supplied)' }
$sqlcmd=Resolve-ProjectSqlcmd $SqlcmdPath
$toolInfo=[Diagnostics.FileVersionInfo]::GetVersionInfo($sqlcmd)
$record.sqlcmd=[ordered]@{path=$sqlcmd;productVersion=$toolInfo.ProductVersion;productMajor=$toolInfo.ProductMajorPart;fileVersion=$toolInfo.FileVersion}
if($Mode -eq 'Plan') { $record | ConvertTo-Json -Depth 8; return }
if($RunId -notmatch '^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$') { throw 'A safe, new RunId is required for evidence preservation.' }
$reportDirectory=Join-Path (Split-Path $PSScriptRoot -Parent) 'test-report'
[IO.Directory]::CreateDirectory($reportDirectory) | Out-Null
if(@(Get-ChildItem -LiteralPath $reportDirectory -Filter ($RunId+'-*')).Count -ne 0) { throw 'Evidence for this RunId already exists; use a different RunId.' }
$recordPath=Join-Path $reportDirectory ($RunId+'-sql2025-deployment.json')
$machine=[regex]::Escape($env:COMPUTERNAME)
if($Server -notmatch ('^(?:(?:tcp|lpc):)?(?:localhost|127\.0\.0\.1|\.|'+$machine+')(?:\\SQLEXPRESS)?(?:,[0-9]+)?$')) { throw 'Only the local explicitly selected SQLEXPRESS endpoint is permitted.' }
$endpointHost=$Server -replace '^(?:tcp|lpc):','' -replace '(?:\\.*|,.*)$',''
if($endpointHost -eq '.') { $endpointHost=$env:COMPUTERNAME }
if($CertificateHostName -ne '' -and -not [string]::Equals($endpointHost,$CertificateHostName,[StringComparison]::OrdinalIgnoreCase)) { throw 'CertificateHostName is an endpoint check only; use a server endpoint whose actual hostname matches the certificate.' }
if($AppWindowsLogin.Length -gt 128 -or ($AppWindowsLogin -ne '' -and $AppWindowsLogin -notmatch '^[^\\]+\\[^\\]+$')) { throw 'AppWindowsLogin must name an existing MACHINE\user or DOMAIN\user Windows login.' }
if($DatabaseOwnerLogin.Length -gt 128 -or ($DatabaseOwnerLogin -ne '' -and $DatabaseOwnerLogin -eq $AppWindowsLogin)) { throw 'Database owner must differ from the application login.' }
if($AllowAdministrativeAppLogin -and $Mode -notin @('CreateEmpty','DeployNew')) { throw 'Administrative application identity is permitted only for initial deployment, never for authorization validation.' }
if($Mode -eq 'ValidateApp' -and $AppWindowsLogin -eq '') { throw 'ValidateApp requires the actual Windows application login.' }
$step=0
function Invoke-ProjectSql([string]$Name,[string]$Catalog,[string]$Query,[string]$InputFile='') {
    $script:step++
    if($PrepareOnly) {
        $preparedFile=Join-Path $reportDirectory ($RunId+'-'+$script:step.ToString('00')+'-'+$Name+'.sql')
        if($InputFile -ne '') { $Query=[IO.File]::ReadAllText($InputFile) }
        [IO.File]::WriteAllText($preparedFile,$Query,$encoding)
        $script:record.phases+= [ordered]@{name=$Name;database=$Catalog;executed=$false;sql=[IO.Path]::GetFileName($preparedFile)}
        return
    }
    $outputFile=Join-Path $reportDirectory ($RunId+'-'+$script:step.ToString('00')+'-'+$Name+'.log')
    $arguments=@('-S',$Server,'-d',$Catalog,'-E','-N','-b','-r','1','-l','15','-t','120','-x','-X1','-u','-o',$outputFile)
    if($InputFile -ne '') { $arguments+=@('-f','65001','-i',$InputFile) } else { $arguments+=@('-Q',$Query) }
    & $sqlcmd @arguments
    $exitCode=$LASTEXITCODE
    $script:record.phases+= [ordered]@{name=$Name;database=$Catalog;exitCode=$exitCode;log=[IO.Path]::GetFileName($outputFile)}
    if($exitCode -ne 0) { throw "sqlcmd failed at $Name; see $outputFile" }
}
try {
    $serverQuery=@"
SET NOCOUNT ON;
IF CONVERT(int,SERVERPROPERTY('ProductMajorVersion'))<>17 THROW 51120,'SQL Server 2025 (17.x) is required.',1;
IF CONVERT(nvarchar(128),SERVERPROPERTY('Edition')) NOT LIKE N'%Express%' THROW 51121,'The explicitly requested Express edition is required.',1;
IF CONVERT(nvarchar(128),SERVERPROPERTY('MachineName'))<>$(Literal $env:COMPUTERNAME) THROW 51122,'Only the local machine is permitted.',1;
IF CONVERT(varchar(20),CONNECTIONPROPERTY('auth_scheme')) NOT IN ('NTLM','KERBEROS') THROW 51123,'Windows integrated authentication is required.',1;
SELECT SERVERPROPERTY('ProductVersion') product_version,SERVERPROPERTY('Edition') edition,ORIGINAL_LOGIN() deployment_login;
"@
    if($Mode -notin @('CreateEmpty','ValidateApp')) {
        $serverQuery+=@"
IF CONVERT(int,(SELECT value_in_use FROM sys.configurations WHERE name='clr enabled'))<>1 THROW 51124,'DBA must explicitly enable CLR before deployment.',1;
IF CONVERT(int,(SELECT value_in_use FROM sys.configurations WHERE name='clr strict security'))<>1 THROW 51125,'CLR strict security must remain enabled.',1;
IF NOT EXISTS(SELECT 1 FROM sys.trusted_assemblies WHERE hash=0x$assemblyHash) THROW 51126,'DBA must independently register this exact reviewed assembly hash.',1;
"@
    }
    if($AppWindowsLogin -ne '') {
        $serverQuery+=@"
IF NOT EXISTS(SELECT 1 FROM sys.server_principals WHERE name=$(Literal $AppWindowsLogin) AND type='U') THROW 51127,'A pre-created individual Windows application login is required.',1;
"@
        if($Mode -eq 'ValidateApp') {
            $serverQuery+=@"
IF ORIGINAL_LOGIN()<>$(Literal $AppWindowsLogin) THROW 51128,'Run ValidateApp under the actual intended Windows token.',1;
IF COALESCE(IS_SRVROLEMEMBER('sysadmin'),1)<>0 THROW 51128,'The actual Windows session must not be sysadmin.',1;
"@
        } elseif(-not $AllowAdministrativeAppLogin) {
            $serverQuery+=@"
IF COALESCE(IS_SRVROLEMEMBER('sysadmin',$(Literal $AppWindowsLogin)),1)<>0 THROW 51128,'Application login cannot be sysadmin; initial admin deployment requires its explicit separate switch.',1;
"@
        }
    }
    if($DatabaseOwnerLogin -ne '' -and $Mode -in @('CreateEmpty','DeployNew')) { $serverQuery+="IF NOT EXISTS(SELECT 1 FROM sys.server_principals WHERE name=$(Literal $DatabaseOwnerLogin)) THROW 51147,'The chosen existing owner login is absent.',1;" }
    if($AppWindowsLogin -ne '' -and $DatabaseOwnerLogin -eq '' -and $Mode -in @('CreateEmpty','DeployNew')) { $serverQuery+="IF SUSER_SID($(Literal $AppWindowsLogin))=SUSER_SID() THROW 51148,'Choose another DatabaseOwnerLogin before creating the application user.',1;" }
    Invoke-ProjectSql 'server-preconditions-readonly' 'master' $serverQuery
    if($Mode -in @('CreateEmpty','DeployNew')) {
        Invoke-ProjectSql 'create-new-project-db' 'master' @"
IF DB_ID($(Literal $database)) IS NOT NULL THROW 51129,'Existing DB is preserved. Use Validate, or supply another approved fixture through a separate operation.',1;
EXEC(N'CREATE DATABASE $(Identifier $database)');
EXEC(N'ALTER DATABASE $(Identifier $database) SET COMPATIBILITY_LEVEL = $CompatibilityLevel');
"@
        if($DatabaseOwnerLogin -ne '') { Invoke-ProjectSql 'assign-separate-database-owner' 'master' ("ALTER AUTHORIZATION ON DATABASE::$(Identifier $database) TO $(Identifier $DatabaseOwnerLogin);") }
        if($AppWindowsLogin -ne '') {
            Invoke-ProjectSql 'create-app-user' $database ("CREATE USER $(Identifier $AppWindowsLogin) FOR LOGIN $(Identifier $AppWindowsLogin);")
        }
        if($Mode -eq 'DeployNew') {
            foreach($relative in $sqlFiles) {
                $file=Join-Path $PSScriptRoot $relative
                if($relative -eq 'native/000_sqlclr.sql') {
                    # Only DB batches are executed; the server-trust registration batch is omitted.
                    $batches=[regex]::Split($clr,'(?im)^GO\s*\r?$')
                    $file=Join-Path $reportDirectory ($RunId+'-000-database-only.sql')
                    [IO.File]::WriteAllText($file,($batches | Select-Object -Skip 1) -join "`r`nGO`r`n",$encoding)
                }
                Invoke-ProjectSql ('deploy-'+[IO.Path]::GetFileNameWithoutExtension($relative)) $database '' $file
            }
            if($AppWindowsLogin -ne '') {
                Invoke-ProjectSql 'grant-single-application-role' $database ("ALTER ROLE $(Identifier $ApplicationRole) ADD MEMBER $(Identifier $AppWindowsLogin);")
            }
        }
    }
    if($Mode -notin @('CreateEmpty','ValidateApp')) {
        $validation=@"
SET NOCOUNT ON;
IF DB_NAME()<>$(Literal $database) THROW 51130,'Unexpected database.',1;
IF (SELECT is_trustworthy_on FROM sys.databases WHERE database_id=DB_ID())<>0 THROW 51131,'TRUSTWORTHY must remain OFF.',1;
IF (SELECT compatibility_level FROM sys.databases WHERE database_id=DB_ID())<>$CompatibilityLevel THROW 51132,'Unexpected database compatibility level.',1;
IF (SELECT snapshot_isolation_state FROM sys.databases WHERE database_id=DB_ID())<>1 THROW 51133,'Snapshot isolation was not deployed.',1;
IF (SELECT COUNT(*) FROM sys.tables WHERE schema_id=SCHEMA_ID('dbo') AND name IN ('m_student','m_class','m_code','m_code_category','t_operation_log','t_confirmation','t_runtime_state'))<>7 THROW 51134,'Project tables are incomplete.',1;
IF (SELECT COUNT(*) FROM dbo.m_code_category)<>5 OR (SELECT COUNT(*) FROM dbo.m_code)<70 THROW 51135,'Seed definitions are incomplete.',1;
IF (SELECT COUNT(*) FROM sys.database_principals WHERE type='R' AND name IN ('student_viewer','student_staff','student_admin'))<>3 THROW 51136,'Application roles are incomplete.',1;
IF (SELECT COUNT(*) FROM sys.procedures WHERE schema_id=SCHEMA_ID('student_api') AND name IN ('prepare_save','persist_student','delete_student','save_class','save_code'))<>5 THROW 51137,'Native procedures are incomplete.',1;
IF NOT EXISTS(SELECT 1 FROM sys.assemblies a JOIN sys.assembly_files f ON f.assembly_id=a.assembly_id AND f.file_id=1 WHERE a.name='StudentNativeNormalization' AND a.permission_set_desc='SAFE_ACCESS' AND HASHBYTES('SHA2_512',f.content)=0x$assemblyHash) THROW 51138,'Deployed assembly differs from the exact reviewed binary.',1;
DECLARE @normalization xml=TRY_CONVERT(xml,student_api.normalize_reason(N'導入検証理由'));
IF @normalization IS NULL OR @normalization.value('(/normalized/@ok)[1]','varchar(5)')<>'true' THROW 51139,'SQL Server CLR hosting failed.',1;
SELECT DB_NAME() database_name,compatibility_level,snapshot_isolation_state,is_trustworthy_on FROM sys.databases WHERE database_id=DB_ID();
SELECT (SELECT COUNT(*) FROM dbo.m_student) students,(SELECT COUNT(*) FROM dbo.m_class) classes,(SELECT COUNT(*) FROM dbo.m_code_category) categories,(SELECT COUNT(*) FROM dbo.m_code) codes;
"@
        Invoke-ProjectSql 'database-and-sqlclr-readonly-validation' $database $validation
    }
    if($Mode -in @('DeployNew','Validate','ValidateApp')) {
        if($AppWindowsLogin -ne '' -and -not $AllowAdministrativeAppLogin) {
            $writeAllowed=0;$adminAllowed=0
            if($ApplicationRole -in @('student_staff','student_admin')) { $writeAllowed=1 }
            if($ApplicationRole -eq 'student_admin') { $adminAllowed=1 }
            $permissionQuery=@"
SET NOCOUNT ON;
BEGIN TRY
 IF USER_NAME()<>$(Literal $AppWindowsLogin) THROW 51140,'Unexpected application database identity.',1;
 IF USER_NAME() IN ('dbo','guest') OR COALESCE(IS_MEMBER('db_owner'),1)<>0 THROW 51140,'Application user must not be owner or guest.',1;
 IF COALESCE(IS_MEMBER('$ApplicationRole'),0)<>1 THROW 51141,'Expected application role membership is absent.',1;
 IF COALESCE(HAS_PERMS_BY_NAME('dbo.m_student','OBJECT','SELECT'),0)<>1 OR COALESCE(HAS_PERMS_BY_NAME('dbo.m_class','OBJECT','SELECT'),0)<>1 THROW 51142,'Read permissions are incomplete.',1;
 IF COALESCE(HAS_PERMS_BY_NAME('dbo.m_student','OBJECT','INSERT'),0)<>0 OR COALESCE(HAS_PERMS_BY_NAME('dbo.m_student','OBJECT','UPDATE'),0)<>0 OR COALESCE(HAS_PERMS_BY_NAME('dbo.m_student','OBJECT','DELETE'),0)<>0 THROW 51143,'Direct student DML must be denied.',1;
 IF COALESCE(HAS_PERMS_BY_NAME('student_api.process_save','OBJECT','EXECUTE'),0)<>0 THROW 51144,'Private process_save must be inaccessible.',1;
 IF COALESCE(HAS_PERMS_BY_NAME('student_api.prepare_save','OBJECT','EXECUTE'),0)<>$writeAllowed OR COALESCE(HAS_PERMS_BY_NAME('student_api.persist_student','OBJECT','EXECUTE'),0)<>$writeAllowed THROW 51145,'Save entry permissions are incorrect.',1;
 IF COALESCE(HAS_PERMS_BY_NAME('student_api.delete_student','OBJECT','EXECUTE'),0)<>$adminAllowed OR COALESCE(HAS_PERMS_BY_NAME('student_api.save_class','OBJECT','EXECUTE'),0)<>$adminAllowed OR COALESCE(HAS_PERMS_BY_NAME('student_api.save_code','OBJECT','EXECUTE'),0)<>$adminAllowed THROW 51146,'Administrator entry permissions are incorrect.',1;
 SELECT USER_NAME() application_user,IS_MEMBER('$ApplicationRole') role_member;
END TRY
BEGIN CATCH
 THROW;
END CATCH;
"@
            if($Mode -eq 'ValidateApp') {
                $permissionQuery="IF COALESCE(IS_SRVROLEMEMBER('sysadmin'),1)<>0 THROW 51140,'Actual application session cannot be sysadmin.',1;"+$permissionQuery
                Invoke-ProjectSql 'actual-windows-application-permissions' $database $permissionQuery
                $record.actualApplicationSessionVerified=$true
                $record.notRun=@('application CRUD/concurrency/commit failures','administrative schema/SQLCLR hosting validation (use Validate separately)')
            } else {
                $permissionQuery="EXECUTE AS USER = $(Literal $AppWindowsLogin);"+$permissionQuery+"`r`nREVERT;"
                Invoke-ProjectSql 'application-permission-probes' $database $permissionQuery
                $record.notRun=@('application CRUD/concurrency/commit failures','real Windows application-role sessions (permission probes use EXECUTE AS USER)')
            }
        } elseif($AllowAdministrativeAppLogin) {
            $record.notRun+= 'application permissions: supplied login is allowed administratively only; run ValidateApp after privilege change'
        }
    }
    $record.status='PASS'
    if($PrepareOnly) {
        $record.status='PREPARED_NOT_EXECUTED';$record.actualApplicationSessionVerified=$false
        $record.notRun+= 'all SQL statements and all connections (PrepareOnly)'
    }
    if($Mode -eq 'CreateEmpty') { $record.notRun+= 'schema/seed/native deployment and SQLCLR hosting (CreateEmpty only)' }
} catch {
    $record.status='FAILED';$record.error=$_.Exception.Message
    throw
} finally {
    [IO.File]::WriteAllText($recordPath,($record | ConvertTo-Json -Depth 8),$encoding)
    Write-Output "Evidence: $recordPath"
}
