$ErrorActionPreference='Stop'
$sp2Root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location -LiteralPath $sp2Root
function Get-Sp2InitialNative {
 $sp2Secret=Join-Path ([Environment]::GetFolderPath('ApplicationData')) 'Microsoft/UserSecrets/sample-project2-CareerManagement.Web-46b7ea90-705d-4b68-a0ea-d681622fe9ae/secrets.json'
 $sp2Paths=@('.tmp/runtime/profile.json','.tmp/ui-regenerate-runtime/profile.json','.tmp/audit-runtime/profile.json','src/CareerManagement.Web/Properties/launchSettings.json')
 $sp2Items=@(foreach($sp2Path in $sp2Paths){[ordered]@{file=$sp2Path;sha256=(Get-FileHash -LiteralPath $sp2Path -Algorithm SHA256).Hash.ToLowerInvariant()}})
 if(-not(Test-Path -LiteralPath $sp2Secret -PathType Leaf)){throw 'Native user-secrets unavailable; no initialization may start.'}
 $sp2Items+=@([ordered]@{file='existing native Web user-secrets';sha256=(Get-FileHash -LiteralPath $sp2Secret -Algorithm SHA256).Hash.ToLowerInvariant()})
 $sp2Items
}
$sp2Before=@(Get-Sp2InitialNative);$sp2Started=[DateTimeOffset]::UtcNow.ToString('o')
& python -B -X utf8 tests/independent/source-package-validation.py
if($LASTEXITCODE -ne 0){throw 'New ZIP ordinary initialization failed. Existing databases must not be recreated.'}
$sp2After=@(Get-Sp2InitialNative)
if(($sp2Before|ConvertTo-Json -Depth 15 -Compress) -cne ($sp2After|ConvertTo-Json -Depth 15 -Compress)){throw 'Native protected data changed during new ZIP build/initialization.'}
$sp2Proof=[ordered]@{runId='sp2-ui-regenerate-20261029';status='PASS_NATIVE_INITIAL_ZIP_BUILD_AND_INITIALIZATION_PROTECTION';startedAt=$sp2Started;endedAt=[DateTimeOffset]::UtcNow.ToString('o');beforeNative=$sp2Before;afterNative=$sp2After;sourceSha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant();scope='Native PowerShell parent wraps current final source ZIP normal build plus NEW owned final ZIP database create/seed/SKIP; historical prior4a missing native interval is not reassigned.';formalScore=$null}
$sp2ProofFile='build/test-results/source-package-initial-native.json'
[IO.File]::WriteAllText((Join-Path $sp2Root $sp2ProofFile),($sp2Proof|ConvertTo-Json -Depth 30)+"`n",[Text.UTF8Encoding]::new($false))
& (Join-Path $PSScriptRoot 'source-package-preservation.ps1')
if($LASTEXITCODE -ne 0){throw 'Current ZIP supplementary native build/SKIP failed.'}
$sp2File='build/test-results/source-package-validation.json'
$sp2Record=Get-Content -LiteralPath $sp2File -Raw|ConvertFrom-Json -AsHashtable
$sp2Record.initialProtectedInputObservability=[ordered]@{method='Native PowerShell parent around current final build/create/seed/SKIP';initialNativeUserSecretsBeforeAfterShaObserved=$true;nativeAllProfilesAndUserSecretsUnchanged=$true;evidence=[ordered]@{file=$sp2ProofFile;sha256=(Get-FileHash -LiteralPath $sp2ProofFile -Algorithm SHA256).Hash.ToLowerInvariant()}}
$sp2Record.historicalPriorCandidate=[ordered]@{artifactSha256='4a60763579584af38749462f9792b51179249447080d610d2d9049a9bd3af651';archiveSha256='28abd72baa695bb29d837b953ccfb3e4169c8d3b8d84a3c2c09ec511b0ee6b75';initialNativeUserSecretsBeforeAfterShaObserved=$false;scope='Past initial Store-Python interval remains NOT_MEASURED; no retrospective PASS. Current new final ZIP interval is separately observed.'}
$sp2Record.protectedProfileAndUserSettingsUnchanged=[ordered]@{currentInitialNativeAllProtectedVerified=$true;supplementaryNativeProfilesAndUserSecretsVerified=$true}
$sp2Record.protectionScope='Current Native parent covers initial final-ZIP build/create/seed/SKIP and separate supplementary build/SKIP. Historical missing4a interval remains distinct.'
$sp2Record.measurementSources+=@([ordered]@{file='tests/independent/source-package-final.ps1';sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()})
[IO.File]::WriteAllText((Join-Path $sp2Root $sp2File),($sp2Record|ConvertTo-Json -Depth 100)+"`n",[Text.UTF8Encoding]::new($false))
Write-Output 'Final source ZIP rebuilt and initialized; initial and supplementary native guards both measured unchanged.'
