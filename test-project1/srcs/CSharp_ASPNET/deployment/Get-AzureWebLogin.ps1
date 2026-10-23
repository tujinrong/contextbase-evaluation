param([switch]$ShowPassword,[switch]$CopyPassword)
$root = Split-Path $PSScriptRoot -Parent
$stateDirectory = Join-Path $root 'build/azure-free-state'
$state = Get-Content -LiteralPath (Join-Path $stateDirectory 'resources.json') -Raw | ConvertFrom-Json
$credential = Import-Clixml -LiteralPath (Join-Path $stateDirectory 'web-login.credential.xml')
if ($CopyPassword) { Set-Clipboard -Value $credential.GetNetworkCredential().Password }
[pscustomobject]@{ Url="https://$($state.hostName)/login"; UserName=$credential.UserName; Password=if($ShowPassword){$credential.GetNetworkCredential().Password}elseif($CopyPassword){'Copied to clipboard.'}else{'Use -ShowPassword or -CopyPassword locally.'} }
