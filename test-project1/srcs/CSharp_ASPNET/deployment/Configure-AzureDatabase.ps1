$ErrorActionPreference = 'Stop'
$stateDirectory = Join-Path $PSScriptRoot '../.tmp/deployment-state'
$state = Get-Content -LiteralPath (Join-Path $stateDirectory 'resources.json') -Raw | ConvertFrom-Json
function Invoke-Azure([string[]]$Arguments) {
    $result = & az @Arguments --subscription $state.subscription --only-show-errors --output json
    if ($LASTEXITCODE -ne 0) { throw "Azure operation failed: $($Arguments[0..2] -join ' ')" }
    if ($result) { ($result -join "`n") | ConvertFrom-Json }
}
$credential = Import-Clixml -LiteralPath (Join-Path $stateDirectory 'sql-admin.credential.xml')
$appCredentialFile = Join-Path $stateDirectory 'sql-app.credential.xml'
if (-not (Test-Path -LiteralPath $appCredentialFile)) {
    $password = 'Aa1!' + [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(24))
    [pscredential]::new('student_web',(ConvertTo-SecureString $password -AsPlainText -Force)) | Export-Clixml -LiteralPath $appCredentialFile
}
$appCredential = Import-Clixml -LiteralPath $appCredentialFile
$web = Invoke-Azure @('webapp','show','-g',$state.resourceGroup,'-n',$state.app)
$addresses = @($web.outboundIpAddresses -split ',' | Where-Object { $_ } | Select-Object -Unique)
foreach ($address in $addresses) {
    Invoke-Azure @('sql','server','firewall-rule','create','-g',$state.resourceGroup,'-s',$state.server,'-n',"web-$($address.Replace('.','-'))",'--start-ip-address',$address,'--end-ip-address',$address) | Out-Null
}
$clientIp = (Invoke-RestMethod -Uri 'https://api.ipify.org').Trim()
if ($clientIp -notmatch '^\d{1,3}(\.\d{1,3}){3}$') { throw 'Cannot determine deployment IPv4 address.' }
Invoke-Azure @('sql','server','firewall-rule','create','-g',$state.resourceGroup,'-s',$state.server,'-n','temporary-deployment-client','--start-ip-address',$clientIp,'--end-ip-address',$clientIp) | Out-Null
try {
    $env:CB_SQL_ADMIN_PASSWORD = $credential.GetNetworkCredential().Password
    $env:CB_SQL_APP_PASSWORD = $appCredential.GetNetworkCredential().Password
    & python (Join-Path $PSScriptRoot 'Initialize-AzureDatabase.py')
    if ($LASTEXITCODE -ne 0) { throw 'Azure SQL initialization or verification failed.' }
    $connection = "Server=tcp:$($state.server).database.windows.net,1433;Database=$($state.database);User ID=student_web;Password=$($appCredential.GetNetworkCredential().Password);Encrypt=True;TrustServerCertificate=False;Connect Timeout=120;"
    $env:CB_AZURE_SQL_CONNECTION = $connection
    & dotnet run --project (Join-Path $PSScriptRoot 'DatabaseSmoke/DatabaseSmoke.csproj') -c Release
    if ($LASTEXITCODE -ne 0) { throw 'Actual application service failed its Azure SQL read verification.' }
    $settingsFile = Join-Path $stateDirectory 'temporary-connection-settings.json'
    try {
        @{ConnectionStrings__StudentDb=$connection} | ConvertTo-Json | Set-Content -LiteralPath $settingsFile -Encoding utf8
        Invoke-Azure @('webapp','config','appsettings','set','-g',$state.resourceGroup,'-n',$state.app,'--settings',"@$settingsFile") | Out-Null
    } finally { if (Test-Path -LiteralPath $settingsFile) { Remove-Item -LiteralPath $settingsFile } }
} finally {
    Remove-Item Env:CB_SQL_ADMIN_PASSWORD,Env:CB_SQL_APP_PASSWORD,Env:CB_AZURE_SQL_CONNECTION -ErrorAction SilentlyContinue
    Invoke-Azure @('sql','server','firewall-rule','delete','-g',$state.resourceGroup,'-s',$state.server,'-n','temporary-deployment-client') | Out-Null
}
Write-Output 'Azure SQL initialized and application connection configured. Temporary client firewall access removed.'
