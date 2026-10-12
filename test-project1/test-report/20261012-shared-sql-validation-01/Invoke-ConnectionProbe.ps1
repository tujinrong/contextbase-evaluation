[CmdletBinding()]
param([Parameter(Mandatory=$true)][ValidateSet('x64','x86')][string]$ProbeName)
$ErrorActionPreference='Stop'
$out=Join-Path $PSScriptRoot ($ProbeName+'.json')
if(Test-Path -LiteralPath $out){throw 'Existing probe result must not be overwritten.'}
Start-Transcript -LiteralPath (Join-Path $PSScriptRoot ($ProbeName+'.raw.log')) -NoClobber | Out-Null
$state=[ordered]@{status='RUNNING';started=(Get-Date).ToString('o');architecture=([IntPtr]::Size*8);powershell=$PSVersionTable.PSVersion.ToString();readOnly=$true;tests=@();error=$null;notRun=@('Application authorization/CRUD','Access DAO/ADO program execution','IBM i runtime')}
$cs='Driver={ODBC Driver 18 for SQL Server};Server=tcp:127.0.0.1,1433;HostnameInCertificate=localhost;Database=contextbase_test_project1;Trusted_Connection=Yes;Encrypt=Yes;TrustServerCertificate=No;APP=contextbase shared DB read-only probe;'
$cn=New-Object System.Data.Odbc.OdbcConnection($cs);$cn.ConnectionTimeout=5
try {
    $expected=if($ProbeName -eq 'x64'){64}else{32}
    if($state.architecture -ne $expected){throw 'Incorrect process architecture.'}
    $driver=(Get-ItemProperty -LiteralPath 'HKLM:\SOFTWARE\ODBC\ODBCINST.INI\ODBC Driver 18 for SQL Server').Driver
    $state.driver=@{path=$driver;version=(Get-Item -LiteralPath $driver).VersionInfo.ProductVersion}
    $cn.Open();$cmd=$cn.CreateCommand()
    $cmd.CommandText="SELECT CONVERT(nvarchar(128),SERVERPROPERTY('Edition')) edition,CONVERT(nvarchar(128),SERVERPROPERTY('ProductVersion')) version,CONVERT(int,SERVERPROPERTY('IsIntegratedSecurityOnly')) windows_only,ORIGINAL_LOGIN() original_login,DB_NAME() database_name,encrypt_option,auth_scheme,net_transport,local_net_address,local_tcp_port FROM sys.dm_exec_connections WHERE session_id=@@SPID"
    $table=New-Object Data.DataTable;$table.Load($cmd.ExecuteReader());$r=$table.Rows[0]
    $state.connection=@{edition=[string]$r.edition;version=[string]$r.version;windowsOnly=[int]$r.windows_only;originalLogin=[string]$r.original_login;database=[string]$r.database_name;encrypted=[string]$r.encrypt_option;authScheme=[string]$r.auth_scheme;transport=[string]$r.net_transport;localAddress=[string]$r.local_net_address;port=[int]$r.local_tcp_port;trustServerCertificate=$false;hostnameInCertificate='localhost'}
    if($r.edition -notmatch 'Express' -or $r.version -ne '17.0.5005.3' -or [int]$r.windows_only -ne 1 -or $r.encrypt_option -ne 'TRUE' -or $r.auth_scheme -notin @('NTLM','KERBEROS') -or $r.net_transport -ne 'TCP' -or $r.local_net_address -ne '127.0.0.1' -or [int]$r.local_tcp_port -ne 1433 -or $r.database_name -ne 'contextbase_test_project1'){throw 'Connection metadata mismatch.'}
    $state.tests+=@{name='Windows authentication, strict TLS and shared DB connection';status='PASSED'}
    $cmd.CommandText="SELECT (SELECT COUNT(*) FROM sys.objects WHERE is_ms_shipped=0) objects,(SELECT COUNT(*) FROM sys.assemblies WHERE is_user_defined=1) assemblies,(SELECT COUNT(*) FROM sys.database_principals WHERE type='R' AND is_fixed_role=0 AND name<>N'public') application_roles"
    $table=New-Object Data.DataTable;$table.Load($cmd.ExecuteReader());$r=$table.Rows[0]
    $state.emptyDatabase=@{objects=[int]$r.objects;assemblies=[int]$r.assemblies;applicationRoles=[int]$r.application_roles}
    if([int]$r.objects -ne 0 -or [int]$r.assemblies -ne 0 -or [int]$r.application_roles -ne 0){throw 'Database is not empty.'}
    $state.tests+=@{name='Empty shared DB pending corrected deployment contract';status='PASSED'}
    $bad=New-Object System.Data.Odbc.OdbcConnection($cs.Replace('HostnameInCertificate=localhost','HostnameInCertificate=invalid.example'));$bad.ConnectionTimeout=5
    try {
        try {$bad.Open();throw 'Negative TLS probe accepted a mismatched hostname.'} catch {
            if($bad.State -eq 'Open'){throw}
            $err=$_.Exception.ToString()
            if($err -notmatch 'SSL Provider|certificate|証明書|プリンシパル'){throw}
            $state.rejectedCertificateName=@{hostname='invalid.example';error=$err}
        }
    } finally {$bad.Dispose()}
    $state.tests+=@{name='Mismatched certificate hostname rejected';status='PASSED'}
    $state.status='PASSED'
} catch {$state.status='FAILED';$state.error=$_.Exception.ToString();Write-Error -Message $state.error -ErrorAction Continue}
finally {$cn.Dispose();$state.finished=(Get-Date).ToString('o');$state | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $out -Encoding UTF8;Stop-Transcript | Out-Null}
if($state.status -ne 'PASSED'){exit 1}
