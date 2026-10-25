param([switch]$ShowPassword)
$root = Split-Path $PSScriptRoot -Parent
$stateDirectory = Join-Path $root '.tmp/deployment-state'
$state = Get-Content -LiteralPath (Join-Path $stateDirectory 'resources.json') -Raw | ConvertFrom-Json
$credential = Import-Clixml -LiteralPath (Join-Path $stateDirectory 'sql-app.credential.xml')
[pscustomobject]@{ Server="$($state.server).database.windows.net,1433"; Database=$state.database; Authentication='SQL Server Authentication'; UserName=$credential.UserName; Encrypt=$true; TrustServerCertificate=$false; Password=if($ShowPassword){$credential.GetNetworkCredential().Password}else{'Use -ShowPassword to display locally.'} }
