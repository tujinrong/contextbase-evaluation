param([switch]$RunTests,[ValidateRange(1,3)][int]$Cycle=3)
$ErrorActionPreference='Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
dotnet restore CareerManagement.slnx --locked-mode --nologo
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
dotnet build CareerManagement.slnx -c Release --no-restore --nologo
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
if($RunTests){
  dotnet run --project tests/CareerManagement.Tests/CareerManagement.Tests.csproj -c Release --no-build -- --cycle $Cycle
  if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
}
dotnet publish src/CareerManagement.Web/CareerManagement.Web.csproj -c Release --no-build --no-restore -o build/publish --nologo
if($LASTEXITCODE -eq 0){Copy-Item -LiteralPath 'THIRD-PARTY-NOTICES.md','third-party' -Destination 'build/publish' -Recurse -Force}
exit $LASTEXITCODE
