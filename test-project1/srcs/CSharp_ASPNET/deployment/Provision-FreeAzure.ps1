param([switch]$Execute)
$ErrorActionPreference = 'Stop'
$subscription = '8a14b46b-69eb-4469-84f6-1d5e5750c20c'
$resourceGroup = 'rg-contextbase-student-demo'
$server = 'sql-contextbase-student-8a14b4'
$database = 'contextbase_test_project1_mvc'
$app = 'app-contextbase-student-8a14b4'
$plan = "/subscriptions/$subscription/resourceGroups/mcterp/providers/Microsoft.Web/serverfarms/ASP-mcterp-89b6"
$stateDirectory = Join-Path $PSScriptRoot '../build/azure-free-state'
function Invoke-AzureJson([string[]]$Arguments) {
    $result = & az @Arguments --subscription $subscription --only-show-errors --output json
    if ($LASTEXITCODE -ne 0) { throw "Azure operation failed: $($Arguments[0..2] -join ' '). No paid fallback is permitted." }
    if ($result) { ($result -join "`n") | ConvertFrom-Json }
}
if (-not $Execute) {
    [pscustomobject]@{ Subscription=$subscription; ResourceGroup=$resourceGroup; Plan=$plan; SqlServer=$server; Database=$database; App=$app; SqlFreeLimit=$true; ExhaustionBehavior='AutoPause' }
    return
}
$existingPlan = Invoke-AzureJson @('appservice','plan','show','--ids',$plan)
if ($existingPlan.sku.name -ne 'F1') { throw 'The selected plan must remain F1.' }
New-Item -ItemType Directory -Path $stateDirectory -Force | Out-Null
$credentialFile = Join-Path $stateDirectory 'sql-admin.credential.xml'
if (-not (Test-Path -LiteralPath $credentialFile)) {
    $password = 'Aa1!' + [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(24))
    $credential = [pscredential]::new('cbsetup', (ConvertTo-SecureString $password -AsPlainText -Force))
    $credential | Export-Clixml -LiteralPath $credentialFile
} else { $credential = Import-Clixml -LiteralPath $credentialFile }
Invoke-AzureJson @('group','create','--name',$resourceGroup,'--location','japanwest','--tags','project=contextbase-test-project1','purpose=student-demo') | Out-Null
$servers = @(Invoke-AzureJson @('sql','server','list','--resource-group',$resourceGroup))
if (-not ($servers | Where-Object name -eq $server)) {
    Invoke-AzureJson @('sql','server','create','--resource-group',$resourceGroup,'--name',$server,'--location','japanwest','--admin-user',$credential.UserName,'--admin-password',$credential.GetNetworkCredential().Password,'--minimal-tls-version','1.2') | Out-Null
}
$databases = @(Invoke-AzureJson @('sql','db','list','--resource-group',$resourceGroup,'--server',$server))
$db = $databases | Where-Object name -eq $database
if (-not $db) {
    $db = Invoke-AzureJson @('sql','db','create','--resource-group',$resourceGroup,'--server',$server,'--name',$database,'--edition','GeneralPurpose','--family','Gen5','--capacity','2','--compute-model','Serverless','--min-capacity','0.5','--auto-pause-delay','60','--max-size','32GB','--backup-storage-redundancy','Local','--use-free-limit','true','--free-limit-exhaustion-behavior','AutoPause')
}
if ($db.useFreeLimit -ne $true -or $db.freeLimitExhaustionBehavior -ne 'AutoPause') { throw 'Database free-limit safeguards were not confirmed; stop deployment.' }
$apps = @(Invoke-AzureJson @('webapp','list','--resource-group',$resourceGroup))
$web = $apps | Where-Object name -eq $app
if (-not $web) {
    $web = Invoke-AzureJson @('webapp','create','--resource-group',$resourceGroup,'--name',$app,'--plan',$plan,'--runtime','dotnet:10','--https-only','true')
}
if ($web.appServicePlanId -ine $plan) { throw 'The actual website is not bound to the expected F1 plan; stop deployment.' }
Invoke-AzureJson @('webapp','config','set','--resource-group',$resourceGroup,'--name',$app,'--use-32bit-worker-process','true','--always-on','false','--ftps-state','Disabled','--min-tls-version','1.2') | Out-Null
Invoke-AzureJson @('webapp','config','appsettings','set','--resource-group',$resourceGroup,'--name',$app,'--settings','ASPNETCORE_ENVIRONMENT=Production',"AllowedHosts=$($web.defaultHostName)",'EvaluationSession__Secret=') | Out-Null
$state = [ordered]@{ subscription=$subscription;resourceGroup=$resourceGroup;server=$server;database=$database;app=$app;plan=$plan;hostName=$web.defaultHostName;useFreeLimit=$db.useFreeLimit;freeLimitExhaustionBehavior=$db.freeLimitExhaustionBehavior }
$state | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $stateDirectory 'resources.json') -Encoding utf8
$state | ConvertTo-Json
