[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$ServerInstance,
      [Parameter(Mandatory=$true)][ValidateLength(1,128)][string]$WindowsPrincipal,
      [ValidateSet('Viewer','Staff','Administrator')][string]$Profile='Viewer', [switch]$Apply)
. "$PSScriptRoot/Common.ps1"
$roles = @{ Viewer='student_viewer'; Staff='student_staff'; Administrator='student_admin' }
if (-not $Apply) {
    [pscustomobject]@{Status='PLAN_ONLY';Database=$script:CobolDatabase;Principal=$WindowsPrincipal;Role=$roles[$Profile];RequiresExistingWindowsLogin=$true;CreatesServerLogin=$false}
    return
}
$connection = New-CobolSqlConnection $ServerInstance $script:CobolDatabase
try {
    $connection.Open()
    $command = $connection.CreateCommand()
    try {
        $command.CommandText = @'
IF DB_NAME()<>N'contextbase_test_project1_cobol' THROW 51101,N'Wrong COBOL database.',1;
IF NOT EXISTS(SELECT 1 FROM sys.server_principals WHERE name=@principal AND type IN ('U','G'))
  THROW 51102,N'An existing Windows login/group is required. No server login is created.',1;
IF IS_SRVROLEMEMBER('sysadmin',@principal)=1 OR SUSER_SID(@principal)=(SELECT owner_sid FROM sys.databases WHERE database_id=DB_ID())
  THROW 51103,N'Use a non-sysadmin Windows identity that is not the database owner; CLI tests require student_admin membership.',1;
DECLARE @sid varbinary(85)=SUSER_SID(@principal);
IF EXISTS(SELECT 1 FROM sys.database_principals WHERE name=@principal AND sid<>@sid)
  THROW 51104,N'An existing user of this name maps to a different principal.',1;
DECLARE @ddl nvarchar(max);
IF NOT EXISTS(SELECT 1 FROM sys.database_principals WHERE name=@principal)
BEGIN
  SET @ddl=N'CREATE USER '+QUOTENAME(@principal)+N' FOR LOGIN '+QUOTENAME(@principal)+N';';
  EXEC sys.sp_executesql @ddl;
END;
IF NOT EXISTS(SELECT 1 FROM sys.database_role_members m JOIN sys.database_principals r ON r.principal_id=m.role_principal_id JOIN sys.database_principals u ON u.principal_id=m.member_principal_id WHERE r.name=@role AND u.name=@principal)
BEGIN
  SET @ddl=N'ALTER ROLE '+QUOTENAME(@role)+N' ADD MEMBER '+QUOTENAME(@principal)+N';';
  EXEC sys.sp_executesql @ddl;
END;
SELECT @principal AS windows_principal,@role AS assigned_role;
'@
        [void]$command.Parameters.Add('@principal',[Data.SqlDbType]::NVarChar,128); $command.Parameters['@principal'].Value=$WindowsPrincipal
        [void]$command.Parameters.Add('@role',[Data.SqlDbType]::NVarChar,128); $command.Parameters['@role'].Value=$roles[$Profile]
        [void]$command.ExecuteNonQuery()
    } finally { $command.Dispose() }
    Write-Output "BOUND_EXISTING_WINDOWS_LOGIN $WindowsPrincipal $Profile"
} finally { $connection.Dispose() }
