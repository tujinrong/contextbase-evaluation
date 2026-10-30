$ErrorActionPreference='Stop'
$sp2Root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location -LiteralPath $sp2Root
$sp2Profile=Get-Content -LiteralPath '.tmp/runtime/profile.json' -Raw|ConvertFrom-Json
if($sp2Profile.database -cne 'SP2_WebFixture_20261029' -or $sp2Profile.url -cne 'https://localhost:7443'){throw 'Existing DEMO profile differs.'}
if(Get-NetTCPConnection -State Listen -LocalPort 7443 -ErrorAction SilentlyContinue){throw 'Existing port is occupied; never stop an unverified process.'}
function Get-Sp2Sha([string]$sp2File){(Get-FileHash -LiteralPath $sp2File -Algorithm SHA256).Hash.ToLowerInvariant()}
function Get-Sp2Protected {
 $sp2Secret=Join-Path ([Environment]::GetFolderPath('ApplicationData')) 'Microsoft/UserSecrets/sample-project2-CareerManagement.Web-46b7ea90-705d-4b68-a0ea-d681622fe9ae/secrets.json'
 $sp2Items=@(foreach($sp2Name in @('.tmp/runtime/profile.json','src/CareerManagement.Web/Properties/launchSettings.json')){[ordered]@{file=$sp2Name;sha256=(Get-Sp2Sha $sp2Name)}})
 if(-not(Test-Path -LiteralPath $sp2Secret -PathType Leaf)){throw 'Native user-secrets not observable; do not infer preservation.'}
 $sp2Items+=@([ordered]@{file='native existing Web user-secrets';sha256=(Get-Sp2Sha $sp2Secret)})
 $sp2Items
}
function Invoke-Sp2Read([string]$sp2Query){
 $sp2Guard="SET NOCOUNT ON;IF DB_NAME()<>N'SP2_WebFixture_20261029' THROW 51000,'Wrong DEMO',1;IF NOT EXISTS(SELECT 1 FROM sys.extended_properties WHERE class=0 AND name=N'SP2Owner' AND CONVERT(nvarchar(200),value)=N'sample-project2/CSharp_ASPNET/SP2-DEMO-01') THROW 51000,'Wrong owner',1;"
 $sp2Value=& sqlcmd -S '.\SQLEXPRESS' -E -C -b -d 'SP2_WebFixture_20261029' -f 65001 -y 0 -Q ($sp2Guard+$sp2Query)
 if($LASTEXITCODE -ne 0){throw 'Read-only DEMO snapshot failed.'}
 (($sp2Value -join '').Trim())
}
function Get-Sp2Database {
 $sp2Keys=[ordered]@{m_app_user='user_id';m_code_category='category_id';m_code='category_id,code';m_employee='employee_id';t_career='career_id'}
 $sp2Rows=@(foreach($sp2Table in $sp2Keys.Keys){
  $sp2Value=Invoke-Sp2Read ("SELECT * FROM dbo."+$sp2Table+" ORDER BY "+$sp2Keys[$sp2Table]+" FOR JSON PATH,INCLUDE_NULL_VALUES;")
  if(-not $sp2Value){throw 'No snapshot value; do not infer empty rows.'}
  $sp2Hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($sp2Value))).ToLowerInvariant()
  [ordered]@{table=$sp2Table;rows=@($sp2Value|ConvertFrom-Json).Count;allValuesSha256=$sp2Hash}
 })
 $sp2Schema=Invoke-Sp2Read 'SELECT t.name AS table_name,c.column_id,c.name,c.system_type_id,c.max_length,c.precision,c.scale,c.is_nullable FROM sys.tables t JOIN sys.columns c ON t.object_id=c.object_id WHERE t.is_ms_shipped=0 ORDER BY t.name,c.column_id FOR JSON PATH,INCLUDE_NULL_VALUES;'
 [ordered]@{tables=$sp2Rows;schemaSha256=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($sp2Schema))).ToLowerInvariant()}
}
$sp2Before=@(Get-Sp2Protected);$sp2DbBefore=Get-Sp2Database
$sp2Artifact=(& node --input-type=module -e "import {hashArtifact} from '../../../agents/builds/build-agent/scripts/ui-conformance.mjs';console.log(JSON.stringify(hashArtifact('build/publish')));")|ConvertFrom-Json
if($LASTEXITCODE -ne 0){throw 'Published artifact hash failed.'}
$sp2Started=[DateTimeOffset]::UtcNow.ToString('o')
& (Join-Path $sp2Root 'tools/Start-Fixture.ps1') -ProfilePath '.tmp/runtime/profile.json' -Published
if($LASTEXITCODE -ne 0){throw 'Existing profile host failed to launch.'}
$sp2Http=$null
for($sp2Attempt=0;$sp2Attempt -lt 40;$sp2Attempt++){
 try{$sp2Http=Invoke-WebRequest -Uri 'https://localhost:7443/account/login' -SkipCertificateCheck -TimeoutSec 2;break}catch{Start-Sleep -Milliseconds 150}
}
if($null -eq $sp2Http -or $sp2Http.StatusCode -ne 200){throw 'Public login not available; no authentication attempts made.'}
$sp2After=@(Get-Sp2Protected);$sp2DbAfter=Get-Sp2Database
if(($sp2Before|ConvertTo-Json -Depth 20 -Compress) -cne ($sp2After|ConvertTo-Json -Depth 20 -Compress) -or ($sp2DbBefore|ConvertTo-Json -Depth 20 -Compress) -cne ($sp2DbAfter|ConvertTo-Json -Depth 20 -Compress)){throw 'Existing DEMO data/settings changed.'}
$sp2Host=Get-Content -LiteralPath '.tmp/runtime/owned-host.json' -Raw|ConvertFrom-Json -DateKind String
$sp2Result=[ordered]@{projectId='sample-project2';profileId='CSharp_ASPNET';runId='sp2-ui-regenerate-20261029';recordedAtUtc=[DateTimeOffset]::UtcNow.ToString('o');status='CURRENT_PUBLISHED_HOST_RUNNING_PUBLIC_LOGIN_HTTP_VERIFIED';launchMethod='Published';pid=$sp2Host.pid;ownedPid=$sp2Host.pid;startedAt=$sp2Host.startedAt;port=7443;productFile='build/publish/CareerManagement.Web.dll';productSha256=$sp2Host.productSha256.ToLowerInvariant();artifactSha256=$sp2Artifact.sha256;url=$sp2Profile.url;database=$sp2Profile.database;publicLoginHttpStatus=$sp2Http.StatusCode;existingProfileSha256=$sp2Before[0].sha256;existingLaunchSettingsSha256=$sp2Before[1].sha256;existingProfileAndLaunchSettingsUnchanged=$true;databaseDdlOrSeedExecuted=$false;demoLoginOrBusinessMutationExecuted=$false;visualStudioCurrentRunStatus='NOT_RETESTED_OR_MODIFIED';scope='Exact existing owned DEMO profile/DB restarted with final candidate, public login GET only, native protected files and all five table values/schema measured unchanged.';formalScore=$null}
[IO.File]::WriteAllText((Join-Path $sp2Root 'build/generation/demo-runtime.json'),($sp2Result|ConvertTo-Json -Depth 30)+"`n",[Text.UTF8Encoding]::new($false))
$sp2Proof=[ordered]@{runId=$sp2Result.runId;status='PASS_EXISTING_DEMO_RESTART_PRESERVATION';startedAt=$sp2Started;endedAt=[DateTimeOffset]::UtcNow.ToString('o');artifact=$sp2Artifact;beforeNative=$sp2Before;afterNative=$sp2After;beforeDatabase=$sp2DbBefore;afterDatabase=$sp2DbAfter;sourceSha256=(Get-Sp2Sha $PSCommandPath);demoRuntimeSha256=(Get-Sp2Sha 'build/generation/demo-runtime.json');scope=$sp2Result.scope;formalScore=$null}
[IO.File]::WriteAllText((Join-Path $sp2Root 'build/test-results/demo-restart-preservation.json'),($sp2Proof|ConvertTo-Json -Depth 50)+"`n",[Text.UTF8Encoding]::new($false))
Write-Output 'Existing owned DEMO restarted; public login200 and five tables/native settings unchanged.'
