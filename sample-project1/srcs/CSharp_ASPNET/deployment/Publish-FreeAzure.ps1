$taskSavedEnvironment=@{}
foreach($taskEnvName in @('DOTNET_CLI_HOME','NUGET_HTTP_CACHE_PATH','TEMP','TMP')) { $taskSavedEnvironment[$taskEnvName]=[Environment]::GetEnvironmentVariable($taskEnvName,'Process') }
try {
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$state = Get-Content -LiteralPath (Join-Path $root '.tmp/deployment-state/resources.json') -Raw | ConvertFrom-Json
$actualPlan = & az webapp show --resource-group $state.resourceGroup --name $state.app --subscription $state.subscription --query appServicePlanId -o tsv
if ($LASTEXITCODE -ne 0 -or $actualPlan -ine $state.plan) { throw 'The actual website is not bound to the expected F1 plan.' }
$plan = & az appservice plan show --ids $state.plan --subscription $state.subscription --query sku.name -o tsv
if ($LASTEXITCODE -ne 0 -or $plan -ne 'F1') { throw 'The deployment plan must be confirmed as F1.' }
$results = Join-Path $root 'build/test-results'
[void][IO.Directory]::CreateDirectory($results)
@{status='VERIFICATION_REQUIRED';reason='Standalone Azure publish does not execute current local tests';recordedAt=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $results 'results.json') -Encoding UTF8
'VERIFICATION_REQUIRED: standalone Azure publish does not execute current local tests.' | Set-Content -LiteralPath (Join-Path $results 'README.md') -Encoding UTF8
$publish = [IO.Path]::GetFullPath((Join-Path $root 'build/publish'))
$staging = [IO.Path]::GetFullPath((Join-Path $root '.tmp/deployment/publish'))
$previous = [IO.Path]::GetFullPath((Join-Path $root '.tmp/deployment/previous-publish'))
foreach($taskPath in @($publish,$staging,$previous)) {
    if(-not $taskPath.StartsWith([IO.Path]::GetFullPath($root)+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Output must stay within this method.' }
}
$env:DOTNET_CLI_HOME=Join-Path $root '.tmp/dotnet-home'
$env:NUGET_HTTP_CACHE_PATH=Join-Path $root '.tmp/nuget/http-cache'
$env:TEMP=Join-Path $root '.tmp/runtime'
$env:TMP=$env:TEMP
[void][IO.Directory]::CreateDirectory($env:TEMP)
if(Test-Path -LiteralPath $staging) { Remove-Item -LiteralPath $staging -Recurse -Force }
& dotnet publish (Join-Path $root 'StudentManagement.Web.csproj') -c Release -r win-x86 --self-contained true -p:RestoreLockedMode=true -o $staging
if ($LASTEXITCODE -ne 0) { throw 'Publish failed.' }
if(Test-Path -LiteralPath $previous) { Remove-Item -LiteralPath $previous -Recurse -Force }
if(Test-Path -LiteralPath $publish) { Move-Item -LiteralPath $publish -Destination $previous }
Move-Item -LiteralPath $staging -Destination $publish
foreach ($excluded in @('deployment','spec','spec-eval','tests','database','build')) {
    if (Test-Path -LiteralPath (Join-Path $publish $excluded)) { throw "Unexpected deployment input in publish directory: $excluded" }
}
$archive = Join-Path $root '.tmp/deployment/app.zip'
[void][IO.Directory]::CreateDirectory((Split-Path $archive -Parent))
Compress-Archive -Path (Join-Path $publish '*') -DestinationPath $archive -Force
Get-FileHash -LiteralPath $archive -Algorithm SHA256 | Select-Object Algorithm,Hash
& az webapp deploy --resource-group $state.resourceGroup --name $state.app --subscription $state.subscription --src-path $archive --type zip --clean true --restart true --timeout 600000 --only-show-errors --query '{id:id,status:status,complete:complete}' -o json
if ($LASTEXITCODE -ne 0) { throw 'Azure deployment did not report success; inspect remote state before retrying.' }

} finally {
    foreach($taskEnvName in $taskSavedEnvironment.Keys) { [Environment]::SetEnvironmentVariable($taskEnvName,$taskSavedEnvironment[$taskEnvName],'Process') }
}
