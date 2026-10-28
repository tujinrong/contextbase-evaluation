[CmdletBinding()]
param([Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9][A-Za-z0-9_-]{0,49}$')][string]$RunId)
$ErrorActionPreference='Stop'
$principal=New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if(-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Use an elevated Windows PowerShell session.'}
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..'))
$report=Join-Path $workspace 'sample-project1\build\sql-repair'
New-Item -ItemType Directory -Path $report -Force | Out-Null
Start-Transcript -LiteralPath (Join-Path $report 'repair.raw.log') -Force | Out-Null
$state=[ordered]@{status='RUNNING';started=(Get-Date).ToString('o');server='tcp:127.0.0.1,1433';databaseCreated=$false;oldCertificateRetained=$true;error=$null}
function Save-State {$state | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $report 'repair.json') -Encoding UTF8}
try {
    Save-State
    $id=(Get-ItemProperty -LiteralPath 'HKLM:\SOFTWARE\Microsoft\Microsoft SQL Server\Instance Names\SQL').SQLEXPRESS
    if($id -ne 'MSSQL17.SQLEXPRESS'){throw 'Repair applies only to the newly installed SQLEXPRESS17 instance.'}
    $network='HKLM:\SOFTWARE\Microsoft\Microsoft SQL Server\'+$id+'\MSSQLServer\SuperSocketNetLib'
    $state.previousCertificate=(Get-ItemProperty -LiteralPath $network).Certificate
    # Verify the target through the existing trusted certificate before changing its binding.
    $pre=New-Object System.Data.Odbc.OdbcConnection('Driver={ODBC Driver 18 for SQL Server};Server=tcp:127.0.0.1,1433;HostnameInCertificate=localhost;Database=master;Trusted_Connection=Yes;Encrypt=Yes;TrustServerCertificate=No;')
    $pre.ConnectionTimeout=10
    try {
        $pre.Open();$cmd=$pre.CreateCommand()
        $cmd.CommandText="SELECT CONVERT(nvarchar(128),SERVERPROPERTY('ProductVersion'))+'|'+CONVERT(nvarchar(128),SERVERPROPERTY('Edition'))+'|'+CONVERT(nvarchar(1),SERVERPROPERTY('IsIntegratedSecurityOnly'))"
        $state.before=[string]$cmd.ExecuteScalar()
        if($state.before -notmatch '^17\.0\.5005\.3\|Express Edition \(64-bit\)\|1$'){throw 'Unexpected server version, edition or authentication.'}
    } finally {$pre.Dispose()}
    Import-Module PKI
    $san='2.5.29.17={text}DNS='+$env:COMPUTERNAME+'&DNS=localhost&IPAddress=127.0.0.1&IPAddress=::1'
    $cert=New-SelfSignedCertificate -Type SSLServerAuthentication -Subject ('CN='+$env:COMPUTERNAME) -TextExtension $san -CertStoreLocation 'Cert:\LocalMachine\My' -Provider 'Microsoft RSA SChannel Cryptographic Provider' -KeySpec KeyExchange -KeyLength 2048 -HashAlgorithm SHA256 -KeyExportPolicy NonExportable -NotAfter (Get-Date).AddYears(2) -FriendlyName 'contextbase test-project1 SQL Express loopback IP TLS'
    $public=Join-Path $report 'sqlexpress-loopback.cer'
    Export-Certificate -Cert $cert -FilePath $public | Out-Null
    Import-Certificate -FilePath $public -CertStoreLocation 'Cert:\LocalMachine\Root' | Out-Null
    $keyPath=Join-Path "$env:ProgramData\Microsoft\Crypto\RSA\MachineKeys" $cert.PrivateKey.CspKeyContainerInfo.UniqueKeyContainerName
    $acl=Get-Acl -LiteralPath $keyPath
    $acl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule('NT SERVICE\MSSQL$SQLEXPRESS','Read','Allow')))
    Set-Acl -LiteralPath $keyPath -AclObject $acl
    Set-ItemProperty -LiteralPath $network -Name Certificate -Value $cert.Thumbprint.ToLowerInvariant()
    Set-ItemProperty -LiteralPath $network -Name ForceEncryption -Value 1
    $state.certificate=@{thumbprint=$cert.Thumbprint;subject=$cert.Subject;notAfter=$cert.NotAfter.ToString('o');san=$san;privateKeyExported=$false;publicFile=$public}
    Save-State
    Restart-Service -Name 'MSSQL$SQLEXPRESS'
    $cn=New-Object System.Data.SqlClient.SqlConnection('Server=tcp:127.0.0.1,1433;Database=master;Integrated Security=True;Encrypt=True;TrustServerCertificate=False;Connect Timeout=3;Pooling=False;')
    try {
        for($attempt=1;$attempt -le 10;$attempt++) {
            try {$cn.Open();break} catch {if($attempt -eq 10){throw};Start-Sleep -Seconds 1}
        }
        $cmd=$cn.CreateCommand()
        $cmd.CommandText="SELECT CONVERT(nvarchar(128),SERVERPROPERTY('Edition')) edition, CONVERT(nvarchar(128),SERVERPROPERTY('ProductVersion')) version,CONVERT(int,SERVERPROPERTY('IsIntegratedSecurityOnly')) windows_only, ORIGINAL_LOGIN() original_login,(SELECT encrypt_option FROM sys.dm_exec_connections WHERE session_id=@@SPID) encrypt_option"
        $table=New-Object Data.DataTable;$table.Load($cmd.ExecuteReader());$r=$table.Rows[0]
        $state.serverVerification=@{edition=[string]$r.edition;version=[string]$r.version;windowsOnly=[int]$r.windows_only;originalLogin=[string]$r.original_login;encrypted=[string]$r.encrypt_option;trustServerCertificate=$false}
        if($r.version -ne '17.0.5005.3' -or $r.edition -notmatch 'Express' -or [int]$r.windows_only -ne 1 -or $r.encrypt_option -ne 'TRUE'){throw 'Post-repair connection verification failed.'}
    } finally {$cn.Dispose()}
    $state.status='PASSED'
} catch {$state.status='FAILED';$state.error=$_.Exception.ToString();Write-Error -Message $state.error -ErrorAction Continue}
finally {$state.finished=(Get-Date).ToString('o');Save-State;Stop-Transcript | Out-Null}
if($state.status -ne 'PASSED'){exit 1}
