param([string]$ProfilePath = '.tmp/runtime/profile.json',[switch]$Published)
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
if($Published){
  $sp2Publish=[IO.Path]::GetFullPath((Join-Path (Get-Location).Path 'build/publish'))
  $sp2RuntimeRoot=[IO.Path]::GetFullPath((Split-Path -Parent $ProfilePath))
  $sp2Scratch=[IO.Path]::GetFullPath((Join-Path (Get-Location).Path '.tmp'))
  if(-not $sp2RuntimeRoot.StartsWith($sp2Scratch+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'An owned .tmp runtime is required.'}
  $sp2Dll=Join-Path $sp2Publish 'CareerManagement.Web.dll'
  if(-not (Test-Path -LiteralPath $sp2Dll -PathType Leaf)){throw 'The final published product must exist first.'}
  $env:ASPNETCORE_CONTENTROOT=$sp2Publish
  $sp2Process=Start-Process -FilePath dotnet -ArgumentList @(('"'+$sp2Dll+'"'),'--contentRoot',('"'+$sp2Publish+'"')) -WorkingDirectory $sp2Publish -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $sp2RuntimeRoot 'host-stdout.log') -RedirectStandardError (Join-Path $sp2RuntimeRoot 'host-stderr.log')
  [ordered]@{pid=$sp2Process.Id;startedAt=$sp2Process.StartTime.ToUniversalTime().ToString('o');database=$sp2Runtime.database;profileSha256=(Get-FileHash -LiteralPath $ProfilePath -Algorithm SHA256).Hash;productFile=$sp2Dll;productSha256=(Get-FileHash -LiteralPath $sp2Dll -Algorithm SHA256).Hash;url=$sp2Runtime.url}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $sp2RuntimeRoot 'owned-host.json') -Encoding UTF8
  Write-Output "Published fixture host started; owned PID $($sp2Process.Id)."
  exit 0
}
dotnet run --project src/CareerManagement.Web/CareerManagement.Web.csproj -c Release --no-build --no-launch-profile
exit $LASTEXITCODE
