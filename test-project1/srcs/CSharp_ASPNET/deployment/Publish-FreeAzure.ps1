$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$state = Get-Content -LiteralPath (Join-Path $root 'build/azure-free-state/resources.json') -Raw | ConvertFrom-Json
$actualPlan = & az webapp show --resource-group $state.resourceGroup --name $state.app --subscription $state.subscription --query appServicePlanId -o tsv
if ($LASTEXITCODE -ne 0 -or $actualPlan -ine $state.plan) { throw 'The actual website is not bound to the expected F1 plan.' }
$plan = & az appservice plan show --ids $state.plan --subscription $state.subscription --query sku.name -o tsv
if ($LASTEXITCODE -ne 0 -or $plan -ne 'F1') { throw 'The deployment plan must be confirmed as F1.' }
$publish = Join-Path $root 'build/azure-f1-final/publish'
& dotnet publish (Join-Path $root 'StudentManagement.Web.csproj') -c Release -r win-x86 --self-contained true -o $publish
if ($LASTEXITCODE -ne 0) { throw 'Publish failed.' }
foreach ($excluded in @('deployment','spec','spec-eval','tests','database','build')) {
    if (Test-Path -LiteralPath (Join-Path $publish $excluded)) { throw "Unexpected deployment input in publish directory: $excluded" }
}
$archive = Join-Path $root 'build/azure-f1-final/app.zip'
Compress-Archive -Path (Join-Path $publish '*') -DestinationPath $archive -Force
Get-FileHash -LiteralPath $archive -Algorithm SHA256 | Select-Object Algorithm,Hash
& az webapp deploy --resource-group $state.resourceGroup --name $state.app --subscription $state.subscription --src-path $archive --type zip --clean true --restart true --timeout 600000 --only-show-errors --query '{id:id,status:status,complete:complete}' -o json
if ($LASTEXITCODE -ne 0) { throw 'Azure deployment did not report success; inspect remote state before retrying.' }
