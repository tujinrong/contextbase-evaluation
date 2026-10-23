param([switch]$ResetPassword)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$stateDirectory = Join-Path $root 'build/azure-free-state'
$state = Get-Content -LiteralPath (Join-Path $stateDirectory 'resources.json') -Raw | ConvertFrom-Json
$credentialFile = Join-Path $stateDirectory 'web-login.credential.xml'
$pendingCredentialFile = Join-Path $stateDirectory 'web-login.pending.credential.xml'
$usePending = $ResetPassword -or (Test-Path -LiteralPath $pendingCredentialFile) -or -not (Test-Path -LiteralPath $credentialFile)
if ($usePending -and -not (Test-Path -LiteralPath $pendingCredentialFile)) {
    $password = 'Sm!' + [Convert]::ToBase64String([Security.Cryptography.RandomNumberGenerator]::GetBytes(18))
    [pscredential]::new('admin',(ConvertTo-SecureString $password -AsPlainText -Force)) | Export-Clixml -LiteralPath $pendingCredentialFile
}
$credential = Import-Clixml -LiteralPath $(if($usePending){$pendingCredentialFile}else{$credentialFile})
$hashFile = Join-Path $stateDirectory 'temporary-login-hash.txt'
$settingsFile = Join-Path $stateDirectory 'temporary-login-settings.json'
try {
    $env:CB_WEB_LOGIN_PASSWORD = $credential.GetNetworkCredential().Password
    & dotnet run --project (Join-Path $PSScriptRoot 'LoginPasswordHash/LoginPasswordHash.csproj') -c Release -- $hashFile
    if ($LASTEXITCODE -ne 0) { throw 'Login password hashing failed.' }
    $hash = (Get-Content -LiteralPath $hashFile -Raw).Trim()
    $settings = @{ LocalLogin__Enabled='true'; LocalLogin__Username=$credential.UserName; LocalLogin__PasswordHash=$hash; LocalLogin__Role='Administrator'; ASPNETCORE_ENVIRONMENT='Production'; EvaluationSession__Secret='' }
    $settings | ConvertTo-Json | Set-Content -LiteralPath $settingsFile -Encoding utf8
    & az webapp config appsettings set --resource-group $state.resourceGroup --name $state.app --subscription $state.subscription --settings "@$settingsFile" --only-show-errors --output none
    if ($LASTEXITCODE -ne 0) { throw 'Azure login configuration failed.' }
    if ($usePending) { Move-Item -LiteralPath $pendingCredentialFile -Destination $credentialFile -Force }
} finally {
    Remove-Item Env:CB_WEB_LOGIN_PASSWORD -ErrorAction SilentlyContinue
    foreach ($temporary in @($hashFile,$settingsFile)) { if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary } }
}
Write-Output 'Independent web login configured. Username: admin. Password retained in the local Windows-encrypted credential file.'
