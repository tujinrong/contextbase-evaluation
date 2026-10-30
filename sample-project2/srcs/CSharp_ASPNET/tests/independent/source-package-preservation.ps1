$ErrorActionPreference='Stop'
$sp2Root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$sp2Report=Join-Path $sp2Root 'build/test-results/source-package-preservation.json'
$sp2Initial=Join-Path $sp2Root 'build/test-results/source-package-validation.json'
$sp2Workload=Join-Path $sp2Root 'build/test-results/source-package-preservation-workload.json'
function Get-Sp2NativeProtected {
 $sp2User=Join-Path ([Environment]::GetFolderPath([Environment+SpecialFolder]::ApplicationData)) 'Microsoft/UserSecrets/sample-project2-CareerManagement.Web-46b7ea90-705d-4b68-a0ea-d681622fe9ae/secrets.json'
 $sp2Items=@(foreach($sp2Name in @('.tmp/runtime/profile.json','.tmp/ui-regenerate-runtime/profile.json','.tmp/audit-runtime/profile.json','src/CareerManagement.Web/Properties/launchSettings.json')){
  $sp2Path=Join-Path $sp2Root $sp2Name;$sp2Exists=Test-Path -LiteralPath $sp2Path -PathType Leaf
  [ordered]@{name=$sp2Name;exists=$sp2Exists;sha256=$(if($sp2Exists){(Get-FileHash -LiteralPath $sp2Path -Algorithm SHA256).Hash.ToLowerInvariant()}else{$null})}
 })
 $sp2Exists=Test-Path -LiteralPath $sp2User -PathType Leaf
 $sp2Items+=@([ordered]@{name='existing Web user-secrets';exists=$sp2Exists;sha256=$(if($sp2Exists){(Get-FileHash -LiteralPath $sp2User -Algorithm SHA256).Hash.ToLowerInvariant()}else{$null})})
 return $sp2Items
}
function Get-Sp2Record($sp2Path,$sp2Name){[ordered]@{file=$sp2Name;sha256=(Get-FileHash -LiteralPath $sp2Path -Algorithm SHA256).Hash.ToLowerInvariant();bytes=(Get-Item -LiteralPath $sp2Path).Length}}
$sp2Started=[DateTimeOffset]::UtcNow.ToString('o')
$sp2Before=@(Get-Sp2NativeProtected)
if(-not ($sp2Before|Where-Object name -eq 'existing Web user-secrets').exists){throw 'Native user-secrets is not observable; do not assert preservation.'}
Push-Location -LiteralPath $sp2Root
try{
 & python -B -X utf8 tests/independent/source-package-preservation.py
 if($LASTEXITCODE -ne 0){throw 'Supplementary ZIP workload failed; no DB reset or recreation permitted.'}
 $sp2After=@(Get-Sp2NativeProtected)
 if(($sp2Before|ConvertTo-Json -Depth 10 -Compress) -cne ($sp2After|ConvertTo-Json -Depth 10 -Compress)){throw 'Native protected profiles/user-secrets changed.'}
 $sp2Result=[ordered]@{schemaVersion=1;projectId='sample-project2';profileId='CSharp_ASPNET';runId='sp2-ui-regenerate-20261029';startedAt=$sp2Started;endedAt=[DateTimeOffset]::UtcNow.ToString('o');status='PASS_SUPPLEMENTARY_NATIVE_PROTECTION';scope='Native PowerShell parent surrounds ordinary packaged Build.ps1 and existing owned ZIP DB seed SKIP. Store-Python child filesystem view is not used to establish user-secrets existence.';beforeNative=$sp2Before;afterNative=$sp2After;nativeProfileAndUserSecretsUnchanged=$true;databaseRecreated=$false;dropOrResetExecuted=$false;initialUserSecretsInterval='NOT_MEASURED: initial Store Python guard returned exists=false; no native before/after SHA was captured in that interval.';workload=(Get-Sp2Record $sp2Workload 'build/test-results/source-package-preservation-workload.json');measurementSources=@((Get-Sp2Record $PSCommandPath 'tests/independent/source-package-preservation.ps1'),(Get-Sp2Record (Join-Path $PSScriptRoot 'source-package-preservation.py') 'tests/independent/source-package-preservation.py'));formalScore=$null}
 [IO.File]::WriteAllText($sp2Report,($sp2Result|ConvertTo-Json -Depth 30)+"`n",[Text.UTF8Encoding]::new($false))
 $sp2Record=Get-Content -LiteralPath $sp2Initial -Raw -Encoding UTF8|ConvertFrom-Json -AsHashtable
 $sp2Record.initialProtectedInputObservability=[ordered]@{method='Store Python filesystem view';initialNativeUserSecretsBeforeAfterShaObserved=$false;actualNativeUserSecretsExistenceNotEstablishedByInitialPythonFalse=$true;limitationRetained=$sp2Result.initialUserSecretsInterval}
 $sp2Record.protectedProfileAndUserSettingsUnchanged=[ordered]@{initialOtherProfilesVerified=$true;initialNativeUserSecrets='NOT_MEASURED';supplementaryNativeProfilesAndUserSecretsVerified=$true}
 $sp2Record.supplementaryNativeProtection=Get-Sp2Record $sp2Report 'build/test-results/source-package-preservation.json'
 $sp2Record.protectionScope='Native existing user-secrets exists/hash verified only in supplementary ZIP build and seed SKIP. No retrospective native PASS is assigned to original creation/seed interval.'
 [IO.File]::WriteAllText($sp2Initial,($sp2Record|ConvertTo-Json -Depth 100)+"`n",[Text.UTF8Encoding]::new($false))
 [ordered]@{status=$sp2Result.status;databaseRecreated=$false;nativeUserSecretsObserved=$true}|ConvertTo-Json -Compress
}finally{Pop-Location}
