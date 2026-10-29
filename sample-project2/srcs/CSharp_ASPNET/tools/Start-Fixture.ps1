param([string]$ProfilePath = '.tmp/runtime/profile.json')
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
$sp2Runtime = Get-Content -LiteralPath $ProfilePath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($sp2Runtime.database -cnotmatch '^SP2_WebFixture_[A-Za-z0-9_]+$') { throw 'Fixture allowlist violation.' }
$env:SP2_DATABASE = $sp2Runtime.database
$env:SP2_FIXTURE = 'true'
$env:SP2_CONNECTION_STRING = $sp2Runtime.connectionString
$env:SP2_DATA_KEYS = $sp2Runtime.keys
$env:ASPNETCORE_URLS = $sp2Runtime.url
$env:ASPNETCORE_Kestrel__Certificates__Default__Path = $sp2Runtime.certificate
$env:ASPNETCORE_Kestrel__Certificates__Default__Password = $sp2Runtime.certificatePassword
dotnet run --project src/CareerManagement.Web/CareerManagement.Web.csproj -c Release --no-build --no-launch-profile
exit $LASTEXITCODE
