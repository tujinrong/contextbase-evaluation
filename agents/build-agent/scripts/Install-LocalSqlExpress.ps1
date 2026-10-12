[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$WorkDirectory,
    [Parameter(Mandatory=$true)][string]$ReportDirectory,
    [Parameter(Mandatory=$true)][string]$WindowsAdministrator
)
$ErrorActionPreference = 'Stop'
$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Run this script in an elevated Windows PowerShell session.' }
$workspace = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
$allowed = [IO.Path]::GetFullPath((Join-Path $workspace 'test-project1')) + '\'
$WorkDirectory = [IO.Path]::GetFullPath($WorkDirectory)
$ReportDirectory = [IO.Path]::GetFullPath($ReportDirectory)
foreach ($path in @($WorkDirectory,$ReportDirectory)) { if (-not $path.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)) { throw "Path outside test-project1: $path" } }
if (Test-Path -LiteralPath (Join-Path $ReportDirectory 'installation.json')) { throw 'Existing run report must not be overwritten.' }
New-Item -ItemType Directory -Path $WorkDirectory,$ReportDirectory -Force | Out-Null
Start-Transcript -LiteralPath (Join-Path $ReportDirectory 'installation.raw.log') -NoClobber | Out-Null
$state = [ordered]@{ started=(Get-Date).ToString('o'); status='RUNNING'; administrator=$WindowsAdministrator; instance='SQLEXPRESS'; targetVersion='17.0.5005.3'; removed=@(); steps=@(); certificate=$null; error=$null }
function Save-State { $state | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $ReportDirectory 'installation.json') -Encoding UTF8 }
function Assert-MicrosoftSignature([string]$path) {
    $signature = Get-AuthenticodeSignature -LiteralPath $path
    if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'O=Microsoft Corporation') { throw "Microsoft signature verification failed: $path" }
    Get-FileHash -LiteralPath $path -Algorithm SHA256 | Format-List | Out-String | Write-Output
}
function Run-Setup([string]$executable,[string[]]$arguments,[string]$step) {
    Assert-MicrosoftSignature $executable
    $state.steps += [ordered]@{ name=$step; started=(Get-Date).ToString('o'); arguments=$arguments; exitCode=$null }
    Save-State
    $process = Start-Process -FilePath $executable -ArgumentList $arguments -WindowStyle Hidden -Wait -PassThru
    $state.steps[-1].exitCode = $process.ExitCode
    Save-State
    if ($process.ExitCode -notin @(0,3010)) { throw "$step failed with exit code $($process.ExitCode). See SQL Setup logs." }
    if ($process.ExitCode -eq 3010) { $state.rebootRequired = $true }
}
try {
    Save-State
    $inventory = [ordered]@{
        services=@(Get-CimInstance Win32_Service | Where-Object Name -match 'MSSQL|SQLBrowser|SQLWriter' | Select-Object Name,State,PathName)
        engineInstances=Get-ItemProperty -LiteralPath 'HKLM:\SOFTWARE\Microsoft\Microsoft SQL Server\Instance Names\SQL' -ErrorAction SilentlyContinue | Select-Object * -ExcludeProperty PSPath,PSParentPath,PSChildName,PSDrive,PSProvider
        packages=@(Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*' -ErrorAction SilentlyContinue | Where-Object DisplayName -match 'SQL Server|SQL.*LocalDB' | Select-Object DisplayName,DisplayVersion,PSChildName)
        localDbFiles=@(Get-ChildItem -LiteralPath "$env:LOCALAPPDATA\Microsoft\Microsoft SQL Server Local DB\Instances" -Recurse -File -ErrorAction SilentlyContinue | Select-Object FullName,Length)
        orphan2022Files=@(Get-ChildItem -LiteralPath 'C:\Program Files\Microsoft SQL Server\MSSQL16.SQLEXPRESS' -Recurse -File -ErrorAction SilentlyContinue | Select-Object FullName,Length)
    }
    $inventory | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $ReportDirectory 'before.json') -Encoding UTF8
    if ($inventory.engineInstances) { throw 'An unexpected registered SQL engine instance is present. Preserve its databases and use its version-specific Setup removal before proceeding.' }
    if (@(Get-Process sqlservr -ErrorAction SilentlyContinue).Count -gt 0) { throw 'A SQL engine is running; preserve its databases before removing it.' }
    # Database files left by an earlier uninstall are retained; no filesystem-based DB deletion.
    $bootstrap = Join-Path $WorkDirectory 'SQL2025-SSEI-Expr.exe'
    $cu = Join-Path $WorkDirectory 'SQLServer2025-KB5122048-x64.exe'
    Assert-MicrosoftSignature $bootstrap
    Assert-MicrosoftSignature $cu
    if ((Get-FileHash -LiteralPath $cu -Algorithm SHA256).Hash -ne '30F5A2F57DC82C8E5A497FDEBD15263840D160414E3D0049F174F9C4059D0994') { throw 'CU9 SHA256 differs from Microsoft KB5122048.' }
    $media = Join-Path $WorkDirectory 'media'
    New-Item -ItemType Directory -Path $media -Force | Out-Null
    Run-Setup $bootstrap @('/ACTION=Download','/MEDIATYPE=Core',('/MEDIAPATH="'+$media+'"'),'/LANG=en-US','/QUIET') 'Download official Express media'
    $core = @(Get-ChildItem -LiteralPath $media -Recurse -File -Filter 'SQLEXPR_x64_ENU.exe')
    if ($core.Count -ne 1) { throw 'Expected exactly one English Express core media executable.' }
    $extract = Join-Path $WorkDirectory 'extracted'
    Run-Setup $core[0].FullName @('/Q',('/X:"'+$extract+'"')) 'Extract signed Express media'
    $setup = Join-Path $extract 'setup.exe'
    Assert-MicrosoftSignature $setup
    # Remove installed LocalDB engines through their exact registered MSI products.
    foreach ($product in @(
        @{name='Microsoft SQL Server 2016 LocalDB';id='{6ADE0DC1-B026-4B37-8DD9-690473153EA2}'},
        @{name='Microsoft SQL Server 2019 LocalDB';id='{E5B3A478-C4C3-49E3-8384-A12D4B2008D4}'},
        @{name='Microsoft SQL Server 2025 LocalDB';id='{E9279A3D-A613-4CA7-8B09-A6C4C5C5AB5A}'}
    )) {
        $productKey = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\'+$product.id
        if (Test-Path -LiteralPath $productKey) {
            $msiLog = Join-Path $ReportDirectory ($product.name.Replace(' ','-')+'-uninstall.log')
            $process = Start-Process -FilePath "$env:SystemRoot\System32\msiexec.exe" -ArgumentList @('/x',$product.id,'/qn','/norestart','/L*v',('"'+$msiLog+'"')) -WindowStyle Hidden -Wait -PassThru
            $state.removed += @{ name=$product.name; productCode=$product.id; exitCode=$process.ExitCode }; Save-State
            if ($process.ExitCode -notin @(0,3010,1605)) { throw "LocalDB uninstall failed: $($product.name), $($process.ExitCode)" }
            if ($process.ExitCode -eq 3010) { $state.rebootRequired = $true }
        }
    }
    Run-Setup $setup @('/Q','/ACTION=Install','/FEATURES=SQLENGINE','/INSTANCENAME=SQLEXPRESS','/INSTANCEID=SQLEXPRESS','/IACCEPTSQLSERVERLICENSETERMS','/SUPPRESSPRIVACYSTATEMENTNOTICE','/UPDATEENABLED=False','/SQLSVCSTARTUPTYPE=Automatic','/SQLSVCACCOUNT="NT Service\MSSQL$SQLEXPRESS"',('/SQLSYSADMINACCOUNTS="'+$WindowsAdministrator+'"'),'/TCPENABLED=1','/NPENABLED=0','/BROWSERSVCSTARTUPTYPE=Disabled','/SQLCOLLATION=Japanese_XJIS_140_CI_AS','/INDICATEPROGRESS') 'Install SQL Server 2025 Express Windows authentication'
    Run-Setup $cu @('/Q','/ACTION=Patch','/INSTANCENAME=SQLEXPRESS','/IACCEPTSQLSERVERLICENSETERMS','/INDICATEPROGRESS') 'Apply CU9 KB5122048'
    $odbc = Join-Path $WorkDirectory 'msodbcsql18.msi'
    Assert-MicrosoftSignature $odbc
    if ((Get-FileHash -LiteralPath $odbc -Algorithm SHA256).Hash -ne '21EF69E4B942F18ACED55FA7C3A8D7263004E113A96690BAC7509645E1B1A310') { throw 'Verified ODBC Driver 18.7.1.1 installer changed.' }
    $odbcLog = Join-Path $ReportDirectory 'odbc18-install.log'
    $odbcProcess = Start-Process -FilePath "$env:SystemRoot\System32\msiexec.exe" -ArgumentList @('/i',('"'+$odbc+'"'),'/qn','/norestart','IACCEPTMSODBCSQLLICENSETERMS=YES','ADDLOCAL=ALL','/L*v',('"'+$odbcLog+'"')) -WindowStyle Hidden -Wait -PassThru
    $state.steps += @{name='Install ODBC Driver 18.7.1.1';exitCode=$odbcProcess.ExitCode}; Save-State
    if ($odbcProcess.ExitCode -notin @(0,3010)) { throw "ODBC install failed: $($odbcProcess.ExitCode)" }
    if ($odbcProcess.ExitCode -eq 3010) { $state.rebootRequired = $true }
    $instanceId = (Get-ItemProperty -LiteralPath 'HKLM:\SOFTWARE\Microsoft\Microsoft SQL Server\Instance Names\SQL').SQLEXPRESS
    if ($instanceId -ne 'MSSQL17.SQLEXPRESS') { throw "Unexpected new instance identity: $instanceId" }
    $network = "HKLM:\SOFTWARE\Microsoft\Microsoft SQL Server\$instanceId\MSSQLServer\SuperSocketNetLib"
    $tcp = Join-Path $network 'Tcp'
    Set-ItemProperty -LiteralPath $tcp -Name Enabled -Value 1
    Set-ItemProperty -LiteralPath $tcp -Name ListenOnAllIPs -Value 0
    foreach ($ipKey in Get-ChildItem -LiteralPath $tcp) {
        if ($ipKey.PSChildName -eq 'IPAll') { Set-ItemProperty -LiteralPath $ipKey.PSPath -Name TcpDynamicPorts -Value ''; Set-ItemProperty -LiteralPath $ipKey.PSPath -Name TcpPort -Value '1433'; continue }
        $ip = Get-ItemProperty -LiteralPath $ipKey.PSPath
        $loopback = $ip.IpAddress -in @('127.0.0.1','::1')
        Set-ItemProperty -LiteralPath $ipKey.PSPath -Name Enabled -Value ([int]$loopback)
        Set-ItemProperty -LiteralPath $ipKey.PSPath -Name TcpDynamicPorts -Value ''
        Set-ItemProperty -LiteralPath $ipKey.PSPath -Name TcpPort -Value '1433'
    }
    Import-Module PKI
    $san = '2.5.29.17={text}DNS='+$env:COMPUTERNAME+'&DNS=localhost&IPAddress=127.0.0.1&IPAddress=::1'
    $cert = New-SelfSignedCertificate -Type SSLServerAuthentication -Subject ('CN='+$env:COMPUTERNAME) -TextExtension $san -CertStoreLocation 'Cert:\LocalMachine\My' -Provider 'Microsoft RSA SChannel Cryptographic Provider' -KeySpec KeyExchange -KeyLength 2048 -HashAlgorithm SHA256 -KeyExportPolicy NonExportable -NotAfter (Get-Date).AddYears(2) -FriendlyName 'contextbase test-project1 local SQL Express'
    $publicCert = Join-Path $ReportDirectory 'localhost-sqlexpress.cer'
    Export-Certificate -Cert $cert -FilePath $publicCert | Out-Null
    Import-Certificate -FilePath $publicCert -CertStoreLocation 'Cert:\LocalMachine\Root' | Out-Null
    $keyPath = Join-Path "$env:ProgramData\Microsoft\Crypto\RSA\MachineKeys" $cert.PrivateKey.CspKeyContainerInfo.UniqueKeyContainerName
    $keyAcl = Get-Acl -LiteralPath $keyPath
    $keyRule = New-Object Security.AccessControl.FileSystemAccessRule('NT SERVICE\MSSQL$SQLEXPRESS','Read','Allow')
    $keyAcl.AddAccessRule($keyRule)
    Set-Acl -LiteralPath $keyPath -AclObject $keyAcl
    Set-ItemProperty -LiteralPath $network -Name Certificate -Value $cert.Thumbprint.ToLowerInvariant()
    Set-ItemProperty -LiteralPath $network -Name ForceEncryption -Value 1
    $state.certificate = @{ thumbprint=$cert.Thumbprint; subject=$cert.Subject; notAfter=$cert.NotAfter.ToString('o'); publicFile=$publicCert; privateKeyExported=$false }
    Restart-Service -Name 'MSSQL$SQLEXPRESS'
    $connection = New-Object System.Data.SqlClient.SqlConnection('Server=tcp:127.0.0.1,1433;Database=master;Integrated Security=True;Encrypt=True;TrustServerCertificate=False;Connect Timeout=3;Pooling=False;Application Name=contextbase SQL Express setup')
    try {
        for ($attempt=1; $attempt -le 10; $attempt++) {
            try { $connection.Open(); break } catch { if ($attempt -eq 10) { throw }; Start-Sleep -Seconds 1 }
        }
        $command=$connection.CreateCommand()
        $command.CommandText="SELECT CONVERT(nvarchar(128),SERVERPROPERTY('Edition')) edition, CONVERT(nvarchar(128),SERVERPROPERTY('ProductVersion')) version, CONVERT(int,SERVERPROPERTY('IsIntegratedSecurityOnly')) windows_only, ORIGINAL_LOGIN() original_login, (SELECT encrypt_option FROM sys.dm_exec_connections WHERE session_id=@@SPID) encrypt_option"
        $table = New-Object Data.DataTable; $table.Load($command.ExecuteReader())
        $row=$table.Rows[0]
        $state.server=@{edition=[string]$row.edition;version=[string]$row.version;windowsOnly=[int]$row.windows_only;originalLogin=[string]$row.original_login;encrypted=[string]$row.encrypt_option}
        if ($row.version -ne '17.0.5005.3' -or $row.edition -notmatch 'Express' -or [int]$row.windows_only -ne 1 -or $row.encrypt_option -ne 'TRUE') { throw 'Installed server edition/version/Windows authentication/TLS verification mismatch.' }
        $state.applicationDeployment='Deferred: shared schema, roles, CLR normalization and cross-client locking contract need correction. No CLR activation or assembly trust registration.'
    } finally { $connection.Dispose() }
    $state.status='PASSED'
} catch {
    $state.status='FAILED'; $state.error=$_.Exception.ToString(); Write-Error -Message $state.error -ErrorAction Continue
} finally {
    $state.finished=(Get-Date).ToString('o'); Save-State; Stop-Transcript | Out-Null
}
if ($state.status -ne 'PASSED') { exit 1 }
