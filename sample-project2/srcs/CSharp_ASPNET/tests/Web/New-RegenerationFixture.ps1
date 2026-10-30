param([ValidateSet('Author','Audit')][string]$Scope='Author')
$ErrorActionPreference='Stop'
$sp2Root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$sp2Runtime=[IO.Path]::GetFullPath((Join-Path $sp2Root $(if($Scope -eq 'Author'){'.tmp/ui-regenerate-runtime'}else{'.tmp/audit-runtime'})))
$sp2Database=if($Scope -eq 'Author'){'SP2_WebFixture_UI_R20261029'}else{'SP2_WebFixture_AUDIT_R20261029'}
$sp2Port=if($Scope -eq 'Author'){5182}else{5183}
if(-not $sp2Runtime.StartsWith((Join-Path $sp2Root '.tmp')+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Owned scratch required.'}
foreach($sp2Path in @($sp2Root,(Join-Path $sp2Root '.tmp'),$sp2Runtime)){
 if((Test-Path -LiteralPath $sp2Path) -and ((Get-Item -LiteralPath $sp2Path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Linked fixture directory refused.'}
}
if(Test-Path -LiteralPath (Join-Path $sp2Runtime 'profile.json')){throw 'A fixture profile already exists; do not reuse or reset it.'}
$sp2Setup=Join-Path $sp2Root '.tmp/bin/CareerManagement.Setup/Release/net10.0/CareerManagement.Setup.dll'
if(-not(Test-Path -LiteralPath $sp2Setup -PathType Leaf)){throw 'Build the current Setup CLI first.'}
New-Item -ItemType Directory -Path $sp2Runtime -Force|Out-Null
$sp2Connection="Server=.\SQLEXPRESS;Database=$sp2Database;Integrated Security=True;Encrypt=True;TrustServerCertificate=True"
$env:SP2_CONNECTION_STRING=$sp2Connection
Push-Location -LiteralPath $sp2Runtime
try{
 & dotnet $sp2Setup create $sp2Database
 if($LASTEXITCODE -ne 0){throw 'New fixture creation refused; no existing database is reused.'}
 [ordered]@{database=$sp2Database;scope=$Scope;runId='sp2-ui-regenerate-20261029';createdAt=[DateTimeOffset]::UtcNow.ToString('o');owner='sample-project2/CSharp_ASPNET/SP2-DEMO-01';newDatabaseCreated=$true}|ConvertTo-Json|Set-Content -LiteralPath 'creation.json' -Encoding UTF8
 & dotnet $sp2Setup seed $sp2Database
 if($LASTEXITCODE -ne 0){throw 'Seed failed; owned creation metadata retained for diagnosis.'}
 & dotnet $sp2Setup seed $sp2Database
 if($LASTEXITCODE -ne 0){throw 'Idempotency check failed.'}
 $sp2Rsa=[Security.Cryptography.RSA]::Create(2048)
 try{
  $sp2Request=[Security.Cryptography.X509Certificates.CertificateRequest]::new('CN=localhost',$sp2Rsa,[Security.Cryptography.HashAlgorithmName]::SHA256,[Security.Cryptography.RSASignaturePadding]::Pkcs1)
  $sp2San=[Security.Cryptography.X509Certificates.SubjectAlternativeNameBuilder]::new();$sp2San.AddDnsName('localhost');$sp2San.AddIpAddress([Net.IPAddress]::Loopback);$sp2Request.CertificateExtensions.Add($sp2San.Build())
  $sp2Cert=$sp2Request.CreateSelfSigned([DateTimeOffset]::UtcNow.AddMinutes(-5),[DateTimeOffset]::UtcNow.AddDays(7))
  try{
   $sp2Password=[Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(24))
   $sp2Pfx=Join-Path $sp2Runtime 'server.pfx';[IO.File]::WriteAllBytes($sp2Pfx,$sp2Cert.Export([Security.Cryptography.X509Certificates.X509ContentType]::Pfx,$sp2Password))
  }finally{$sp2Cert.Dispose()}
 }finally{$sp2Rsa.Dispose()}
 [ordered]@{database=$sp2Database;connectionString=$sp2Connection;certificate=$sp2Pfx;certificatePassword=$sp2Password;url="https://localhost:$sp2Port";keys=(Join-Path $sp2Runtime 'keys');adminPassword='123';staffPassword='123';runId='sp2-ui-regenerate-20261029';scope=$Scope}|ConvertTo-Json|Set-Content -LiteralPath 'profile.json' -Encoding UTF8
}finally{Pop-Location}
Write-Output "New owned $Scope fixture prepared; DB=$sp2Database port=$sp2Port. Private certificate settings remain in .tmp."
