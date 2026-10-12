[CmdletBinding()]
param(
    [ValidateSet('Install','Verify','BindPrincipal')]
    [string] $Action = 'Verify',
    [string] $ServerInstance = '.\SQLEXPRESS',
    [string] $SqlCmdPath,
    [switch] $UseExistingEmptyDatabase,
    [string] $ApplicationPrincipal,
    [ValidateSet('Viewer','Staff','Administrator')]
    [string] $ApplicationRole = 'Staff',
    [switch] $RequireInitialEmptyData,
    [switch] $PlanOnly
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$databaseName = 'contextbase_test_project1_vue'
$projectMarker = 'test-project1/Vue_CSharpAPI'
$sqlDirectory = $PSScriptRoot
$files = @('001_schema.sql','002_seed.sql','003_web_permissions.sql','004_verify_deployment.sql')
foreach ($name in $files) {
    if (-not (Test-Path -LiteralPath (Join-Path $sqlDirectory $name) -PathType Leaf)) { throw "Missing local SQL input: $name" }
}
if ([string]::IsNullOrWhiteSpace($ServerInstance) -or $ServerInstance -match '[\r\n\x00]') { throw 'A server instance without control characters is required.' }
if ($Action -eq 'BindPrincipal' -and [string]::IsNullOrWhiteSpace($ApplicationPrincipal)) { throw 'BindPrincipal requires an existing Windows ApplicationPrincipal.' }
if ($ApplicationPrincipal -and ($ApplicationPrincipal.Length -gt 128 -or $ApplicationPrincipal -match '[\r\n\x00]')) { throw 'Invalid Windows principal name.' }
function Resolve-ModernSqlCmd([string] $ExplicitPath, [string[]] $CandidatePaths) {
    # Resource ProductVersion is SQL version (16.x), whereas FileVersion starts with year (2022.0160).
    # Inspect metadata and PE headers only. No candidate executable is started, including in PlanOnly.
    if ($ExplicitPath) { $paths = @($ExplicitPath) }
    elseif ($CandidatePaths) { $paths = @($CandidatePaths) }
    else { $paths = @(Get-Command sqlcmd -CommandType Application -All -ErrorAction SilentlyContinue | ForEach-Object { $_.Source } | Sort-Object -Unique) }
    $accepted = [System.Collections.Generic.List[object]]::new()
    foreach ($candidate in $paths) {
        try {
            $file = Get-Item -LiteralPath $candidate -ErrorAction Stop
            if ($file.PSIsContainer) { continue }
            $version = [System.Diagnostics.FileVersionInfo]::GetVersionInfo($file.FullName)
            if ($version.ProductMajorPart -lt 16 -or $version.OriginalFilename -ine 'SQLCMD.exe' -or $version.ProductName -notmatch '^Microsoft.*SQL Server') { continue }
            $reader = [System.IO.BinaryReader]::new([System.IO.File]::OpenRead($file.FullName))
            try {
                if ($reader.ReadUInt16() -ne 0x5a4d) { continue }
                [void]$reader.BaseStream.Seek(0x3c,[System.IO.SeekOrigin]::Begin)
                $peOffset = $reader.ReadInt32()
                if ($peOffset -lt 64 -or $peOffset -gt ($reader.BaseStream.Length - 6)) { continue }
                [void]$reader.BaseStream.Seek($peOffset,[System.IO.SeekOrigin]::Begin)
                if ($reader.ReadUInt32() -ne 0x00004550) { continue }
                $machine = $reader.ReadUInt16()
            } finally { $reader.Dispose() }
            $architecture = switch ($machine) { 0x8664 { 'x64' } 0x014c { 'x86' } default { 'unsupported' } }
            if ($architecture -eq 'unsupported') { continue }
            $accepted.Add([pscustomobject]@{
                Path=$file.FullName; ProductVersion=$version.ProductVersion; FileVersion=$version.FileVersion;
                SqlVersion=[version]::new($version.ProductMajorPart,$version.ProductMinorPart,$version.ProductBuildPart,$version.ProductPrivatePart);
                Architecture=$architecture; ArchitectureRank=([int]($architecture -eq 'x64'));
                Sha256=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
            })
        } catch { continue }
    }
    if ($accepted.Count -eq 0) { throw 'A Microsoft ODBC sqlcmd PE executable with ProductVersion major 16 or newer is required; Go sqlcmd and older clients are unsupported.' }
    return $accepted | Sort-Object @{Expression='ArchitectureRank';Descending=$true},@{Expression='SqlVersion';Descending=$true},@{Expression='Path';Descending=$false} | Select-Object -First 1
}
$sqlCmdInfo = Resolve-ModernSqlCmd -ExplicitPath $SqlCmdPath
$SqlCmdPath = $sqlCmdInfo.Path
function Sql-Literal([string] $Value) { return "N'" + $Value.Replace("'", "''") + "'" }
function Invoke-LocalSql([string] $Database, [string] $Query, [string] $Filename) {
    # -E is Windows authentication. -N requests encryption; omission of -C keeps certificate validation.
    # -x prevents sqlcmd variable expansion inside user names or source SQL. Never invoke a shell command string.
    $arguments = @('-S',$ServerInstance,'-E','-N','-b','-r','1','-l','15','-t','120','-f','65001','-x','-X1','-I','-d',$Database)
    if ($Filename) { $arguments += @('-i',(Join-Path $sqlDirectory $Filename)) }
    else { $arguments += @('-Q',$Query) }
    if ($PlanOnly) {
        Write-Output ([pscustomobject]@{ PlanOnly=$true; SqlCmdPath=$SqlCmdPath; Database=$Database; SqlFile=$Filename; Query=$Query; Arguments=$arguments })
        return
    }
    & $SqlCmdPath @arguments
    if ($LASTEXITCODE -ne 0) { throw "sqlcmd failed ($LASTEXITCODE); database is preserved. Input: $Filename" }
}
$dbLiteral = Sql-Literal $databaseName
$markerLiteral = Sql-Literal $projectMarker
$schemaHash = (Get-FileHash -LiteralPath (Join-Path $sqlDirectory '001_schema.sql') -Algorithm SHA256).Hash.ToLowerInvariant()
$seedHash = (Get-FileHash -LiteralPath (Join-Path $sqlDirectory '002_seed.sql') -Algorithm SHA256).Hash.ToLowerInvariant()
$permissionsHash = (Get-FileHash -LiteralPath (Join-Path $sqlDirectory '003_web_permissions.sql') -Algorithm SHA256).Hash.ToLowerInvariant()
$serverGuard = @"
SET NOCOUNT ON;
IF ISNULL(CONVERT(int,SERVERPROPERTY('ProductMajorVersion')),0)<>17 THROW 51200,N'SQL Server Express major 17 is required by this deployment request.',1;
IF ISNULL(CONVERT(nvarchar(128),SERVERPROPERTY('Edition')),N'') NOT LIKE N'%Express%' THROW 51201,N'Express edition is required.',1;
IF ISNULL(CONVERT(nvarchar(128),SERVERPROPERTY('MachineName')),N'<missing>')<>ISNULL(CONVERT(nvarchar(128),HOST_NAME()),N'<unknown>') THROW 51202,N'This script targets a local Windows SQL Server instance only.',1;
IF ISNULL(CONVERT(nvarchar(40),CONNECTIONPROPERTY('auth_scheme')),N'') NOT IN(N'NTLM',N'KERBEROS') THROW 51203,N'Windows integrated authentication is required.',1;
"@
if ($Action -eq 'Install') {
    $allowExisting = if ($UseExistingEmptyDatabase) { 1 } else { 0 }
    Invoke-LocalSql -Database 'master' -Query ($serverGuard + @"
IF DB_ID($dbLiteral) IS NULL BEGIN CREATE DATABASE [$databaseName]; END
ELSE IF $allowExisting<>1 THROW 51204,N'Database already exists. No replacement/drop is performed. Explicitly allow an existing empty dedicated database if appropriate.',1;
"@)
    Invoke-LocalSql -Database $databaseName -Query @"
SET NOCOUNT ON;
IF DB_NAME()<>$dbLiteral THROW 51205,N'Unexpected database.',1;
IF EXISTS(SELECT 1 FROM sys.objects WHERE is_ms_shipped=0)
 OR EXISTS(SELECT 1 FROM sys.database_principals WHERE name IN(N'student_viewer',N'student_staff',N'student_admin'))
 OR EXISTS(SELECT 1 FROM sys.extended_properties WHERE class=0 AND name=N'Contextbase.Project')
 THROW 51206,N'Dedicated database must be empty. Existing objects and data are never overwritten.',1;
"@
    foreach ($name in @('001_schema.sql','002_seed.sql','003_web_permissions.sql')) { Invoke-LocalSql -Database $databaseName -Filename $name }
    Invoke-LocalSql -Database $databaseName -Query @"
SET XACT_ABORT ON;
BEGIN TRANSACTION;
EXEC sys.sp_addextendedproperty @name=N'Contextbase.Project',@value=$markerLiteral;
EXEC sys.sp_addextendedproperty @name=N'Contextbase.SchemaSha256',@value=N'$schemaHash';
EXEC sys.sp_addextendedproperty @name=N'Contextbase.SeedSha256',@value=N'$seedHash';
EXEC sys.sp_addextendedproperty @name=N'Contextbase.PermissionsSha256',@value=N'$permissionsHash';
COMMIT;
"@
    $RequireInitialEmptyData = $true
}
Invoke-LocalSql -Database $databaseName -Query ($serverGuard + @"
IF DB_NAME()<>$dbLiteral THROW 51205,N'Unexpected database.',1;
IF NOT EXISTS(SELECT 1 FROM sys.extended_properties WHERE class=0 AND name=N'Contextbase.Project' AND CONVERT(nvarchar(128),value)=$markerLiteral)
 THROW 51207,N'Independent project deployment marker is absent or differs.',1;
IF NOT EXISTS(SELECT 1 FROM sys.extended_properties WHERE class=0 AND name=N'Contextbase.SchemaSha256' AND CONVERT(varchar(64),value)='$schemaHash')
 OR NOT EXISTS(SELECT 1 FROM sys.extended_properties WHERE class=0 AND name=N'Contextbase.SeedSha256' AND CONVERT(varchar(64),value)='$seedHash')
 OR NOT EXISTS(SELECT 1 FROM sys.extended_properties WHERE class=0 AND name=N'Contextbase.PermissionsSha256' AND CONVERT(varchar(64),value)='$permissionsHash')
 THROW 51208,N'Deployed SQL input hashes differ from the local production files.',1;
"@)
if ($ApplicationPrincipal -and $Action -in @('Install','BindPrincipal')) {
    $principalLiteral = Sql-Literal $ApplicationPrincipal
    $roleName = @{ Viewer='student_viewer'; Staff='student_staff'; Administrator='student_admin' }[$ApplicationRole]
    Invoke-LocalSql -Database $databaseName -Query @"
SET XACT_ABORT ON;
DECLARE @principal sysname=$principalLiteral,@role sysname=N'$roleName';
IF NOT EXISTS(SELECT 1 FROM sys.server_principals WHERE name=@principal AND type IN('U','G'))
 THROW 51209,N'An existing Windows server login/group is required. This script never creates or alters server logins.',1;
IF COALESCE(IS_SRVROLEMEMBER(N'sysadmin',@principal),1)<>0
 OR SUSER_SID(@principal)=(SELECT owner_sid FROM sys.databases WHERE database_id=DB_ID())
 THROW 51210,N'Application principal must be separate from sysadmin and database owner.',1;
IF EXISTS(SELECT 1 FROM sys.database_principals WHERE name=@principal AND (sid<>SUSER_SID(@principal) OR type NOT IN('U','G')))
 THROW 51211,N'Existing database principal conflicts with the Windows login.',1;
IF EXISTS(SELECT 1 FROM sys.database_role_members rm JOIN sys.database_principals u ON u.principal_id=rm.member_principal_id JOIN sys.database_principals r ON r.principal_id=rm.role_principal_id WHERE u.name=@principal AND r.name<>@role)
 THROW 51212,N'Existing role membership differs. Privileges are never automatically replaced.',1;
BEGIN TRANSACTION;
DECLARE @sql nvarchar(max);
IF DATABASE_PRINCIPAL_ID(@principal) IS NULL BEGIN SET @sql=N'CREATE USER '+QUOTENAME(@principal)+N' FOR LOGIN '+QUOTENAME(@principal)+N';'; EXEC sys.sp_executesql @sql; END;
IF NOT EXISTS(SELECT 1 FROM sys.database_role_members WHERE role_principal_id=DATABASE_PRINCIPAL_ID(@role) AND member_principal_id=DATABASE_PRINCIPAL_ID(@principal))
 BEGIN SET @sql=N'ALTER ROLE '+QUOTENAME(@role)+N' ADD MEMBER '+QUOTENAME(@principal)+N';'; EXEC sys.sp_executesql @sql; END;
COMMIT;
SELECT @principal AS WindowsPrincipal,@role AS DirectDatabaseRole;
"@
}
Invoke-LocalSql -Database $databaseName -Filename '004_verify_deployment.sql'
if ($RequireInitialEmptyData) {
    Invoke-LocalSql -Database $databaseName -Query @"
IF EXISTS(SELECT 1 FROM dbo.m_student) OR EXISTS(SELECT 1 FROM dbo.m_class)
 OR EXISTS(SELECT 1 FROM dbo.t_operation_log) OR EXISTS(SELECT 1 FROM dbo.t_confirmation) OR EXISTS(SELECT 1 FROM dbo.t_runtime_state)
 OR (SELECT COUNT(*) FROM dbo.m_code_category)<>5 OR (SELECT COUNT(*) FROM dbo.m_code)<>70
 THROW 51213,N'Initial deployment requires five categories / 70 codes and no invented business data.',1;
SELECT N'PASS initial deployment data' AS Result;
"@
}
Write-Output ([pscustomobject]@{
    Action=$Action; PlanOnly=[bool]$PlanOnly; Database=$databaseName; Project=$projectMarker;
    ConnectionString="Server=$ServerInstance;Database=$databaseName;Integrated Security=true;Encrypt=true;TrustServerCertificate=false;";
    ApplicationPrincipal=$ApplicationPrincipal; ApplicationRole=$ApplicationRole;
    SqlFiles=$files; SchemaSha256=$schemaHash; SeedSha256=$seedHash; PermissionsSha256=$permissionsHash;
    SqlCmd=$sqlCmdInfo
})
