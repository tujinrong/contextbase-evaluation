$ErrorActionPreference='Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
dotnet run --project tests/CareerManagement.Tests/CareerManagement.Tests.csproj -c Release -- --prepare-http
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
$sp2Runtime=Get-Content -LiteralPath '.tmp/http-runtime/profile.json' -Raw -Encoding UTF8 | ConvertFrom-Json
if($sp2Runtime.database -cnotmatch '^SP2_WebFixture_Http_[a-f0-9]{12}$'){throw 'HTTP fixture name scope violation.'}
$env:SP2_DATABASE=$sp2Runtime.database
$env:SP2_FIXTURE='true'
$env:SP2_CONNECTION_STRING=$sp2Runtime.connectionString
$env:SP2_DATA_KEYS=$sp2Runtime.keys
$env:ASPNETCORE_URLS=$sp2Runtime.url
$env:ASPNETCORE_Kestrel__Certificates__Default__Path=$sp2Runtime.certificate
$env:ASPNETCORE_Kestrel__Certificates__Default__Password=$sp2Runtime.certificatePassword
$sp2Process=$null
$sp2Exit=1
try{
  $env:ASPNETCORE_CONTENTROOT=Join-Path (Get-Location).Path 'src/CareerManagement.Web'
  $sp2Process=Start-Process -FilePath 'dotnet' -ArgumentList @('.tmp/bin/CareerManagement.Web/Release/net10.0/CareerManagement.Web.dll') -WorkingDirectory (Get-Location).Path -WindowStyle Hidden -PassThru -RedirectStandardOutput '.tmp/http-runtime/stdout.log' -RedirectStandardError '.tmp/http-runtime/stderr.log'
  $sp2Ready=$false
  for($sp2Try=0;$sp2Try -lt 40;$sp2Try++){
    try{Invoke-WebRequest -Uri 'https://localhost:7444/account/login' -SkipCertificateCheck -TimeoutSec 1 | Out-Null;$sp2Ready=$true;break}catch{Start-Sleep -Milliseconds 200}
  }
  if(-not $sp2Ready){throw 'Private HTTPS fixture did not become ready.'}
  python -X utf8 tests/Web/http_contract.py .tmp/http-runtime/profile.json
  $sp2Exit=$LASTEXITCODE
}finally{
  if($sp2Process -and -not $sp2Process.HasExited){Stop-Process -Id $sp2Process.Id -Force}
  $sp2Sqlcmd='C:/Program Files/Microsoft SQL Server/Client SDK/ODBC/180/Tools/Binn/SQLCMD.EXE'
  # Exact generated name + database ownership marker are checked before deleting this private test database.
  $sp2Cleanup="IF NOT EXISTS(SELECT 1 FROM sys.extended_properties WHERE class=0 AND name=N'SP2Owner' AND CONVERT(nvarchar(200),value)=N'sample-project2/CSharp_ASPNET/SP2-DEMO-01') THROW 51000,'Owner mismatch',1; USE master; ALTER DATABASE [$($sp2Runtime.database)] SET SINGLE_USER WITH ROLLBACK IMMEDIATE; DROP DATABASE [$($sp2Runtime.database)];"
  & $sp2Sqlcmd -S '.\SQLEXPRESS' -E -C -b -d $sp2Runtime.database -Q $sp2Cleanup
  if($LASTEXITCODE -ne 0){$sp2Exit=1}
}
exit $sp2Exit
