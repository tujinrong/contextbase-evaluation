$ErrorActionPreference='Stop'
$sp2Root=Split-Path -Parent $PSScriptRoot
$sp2Assets=Get-Content -LiteralPath (Join-Path $sp2Root '.tmp/obj/CareerManagement.Infrastructure/project.assets.json') -Raw -Encoding UTF8 | ConvertFrom-Json -AsHashtable
$sp2Packages=@()
$sp2LicenseRoot=Join-Path $sp2Root 'third-party/licenses'
foreach($sp2Key in ($sp2Assets.libraries.Keys | Sort-Object)){
 $sp2Library=$sp2Assets.libraries[$sp2Key]
 if($sp2Library.type -ne 'package'){continue}
 $sp2Nuspec=$null
 foreach($sp2Folder in $sp2Assets.packageFolders.Keys){
  $sp2Directory=Join-Path $sp2Folder $sp2Library.path
  if(Test-Path -LiteralPath $sp2Directory){$sp2Nuspec=Get-ChildItem -LiteralPath $sp2Directory -Filter '*.nuspec' | Select-Object -First 1;break}
 }
 $sp2License='not-declared-in-local-metadata';$sp2LicenseType='review-needed';$sp2ProjectUrl=$null
 if($sp2Nuspec){
  $sp2Destination=Join-Path $sp2LicenseRoot ($sp2Key.Replace('/','-'))
  New-Item -ItemType Directory -Path $sp2Destination -Force | Out-Null
  Copy-Item -LiteralPath $sp2Nuspec.FullName -Destination $sp2Destination -Force
  Get-ChildItem -LiteralPath $sp2Nuspec.DirectoryName -Recurse -File | Where-Object {$_.Name -match '(?i)^(licen[cs]e|notice|thirdpartynotices|copyright)' -and $_.Extension -notin '.dll','.pdb','.nupkg'} | ForEach-Object {
   $sp2Relative=[IO.Path]::GetRelativePath($sp2Nuspec.DirectoryName,$_.FullName)
   $sp2Target=Join-Path $sp2Destination $sp2Relative
   New-Item -ItemType Directory -Path (Split-Path -Parent $sp2Target) -Force | Out-Null
   Copy-Item -LiteralPath $_.FullName -Destination $sp2Target -Force
  }
  [xml]$sp2Xml=Get-Content -LiteralPath $sp2Nuspec.FullName -Raw -Encoding UTF8
  $sp2LicenseNode=$sp2Xml.SelectSingleNode('//*[local-name()="metadata"]/*[local-name()="license"]')
  if($sp2LicenseNode){$sp2License=$sp2LicenseNode.InnerText;$sp2LicenseType=$sp2LicenseNode.GetAttribute('type')}
  $sp2UrlNode=$sp2Xml.SelectSingleNode('//*[local-name()="metadata"]/*[local-name()="projectUrl"]')
  if($sp2UrlNode){$sp2ProjectUrl=$sp2UrlNode.InnerText}
 }
 $sp2Parts=$sp2Key.Split('/')
 $sp2Packages+=@{name=$sp2Parts[0];version=$sp2Parts[1];sha512=$sp2Library.sha512;license=$sp2License;licenseType=$sp2LicenseType;projectUrl=$sp2ProjectUrl;source='restored NuGet metadata; package licenses retained with package content'}
}
@{projectId='sample-project2';methodId='CSharp_ASPNET';format='dependency-inventory/1.0';sdk='10.0.401';observedRuntime='10.0.12';auditEvidence='build/test-results/nuget-audit.json';packages=$sp2Packages;direct=@('Microsoft.Data.SqlClient/6.1.3','ClosedXML/0.105.1','System.Security.Cryptography.Pkcs/10.0.13');securityCorrection=@{package='System.Security.Cryptography.Pkcs';version='10.0.13';checked='2026-10-29';official=@('https://github.com/dotnet/runtime/security/advisories/GHSA-846f-f764-76mx','https://github.com/dotnet/runtime/security/advisories/GHSA-2fmv-rv2c-59x7')};limitations=@('Inventory is not a legal opinion or a CycloneDX attestation. Read every declared license before redistribution.')} | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $sp2Root 'build/generation/dependencies.json') -Encoding UTF8
Write-Output ('Recorded {0} exact NuGet dependencies and declared licenses.' -f $sp2Packages.Count)
