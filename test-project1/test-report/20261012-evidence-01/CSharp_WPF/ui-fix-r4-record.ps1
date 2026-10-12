Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../..'))
$utf8=[Text.UTF8Encoding]::new($false)
$way='test-project1/srcs/CSharp_WPF/'
function Full([string]$path){Join-Path $workspace $path}
function Hash([string]$path){[ordered]@{path=$path;sha256=(Get-FileHash -LiteralPath (Full $path) -Algorithm SHA256).Hash.ToLowerInvariant();bytes=(Get-Item -LiteralPath (Full $path)).Length}}
foreach($name in @('ui-fix-r4-results.json','ui-fix-r4-inputs.json','ui-fix-r4-report.md')){if(Test-Path -LiteralPath (Join-Path $PSScriptRoot $name)){throw 'Existing report protected'}}
$baseline=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'inputs.json') -Raw|ConvertFrom-Json
$spec=@($baseline.specFiles|ForEach-Object {$r=Hash $_.path;$r['version']=$_.version;[pscustomobject]$r})
$production=@($baseline.productionFiles|ForEach-Object {[pscustomobject](Hash $_.path)})
for($i=0;$i -lt $spec.Count;$i++){if($spec[$i].sha256 -ne $baseline.specFiles[$i].sha256.ToLowerInvariant()){throw 'Unexpected spec drift'}}
$cumulative=@()
for($i=0;$i -lt $production.Count;$i++){if($production[$i].sha256 -ne $baseline.productionFiles[$i].sha256.ToLowerInvariant()){$cumulative+=[ordered]@{path=$production[$i].path;beforeSha256=$baseline.productionFiles[$i].sha256.ToLowerInvariant();currentSha256=$production[$i].sha256}}}
$allowed=@(($way+'Services/NativeModels.cs'),($way+'ViewModels/StudentSearchViewModel.cs'),($way+'Views/StudentSearchView.xaml'),($way+'Views/StudentEditView.xaml'))
if($cumulative.Count -ne 4 -or @($cumulative|Where-Object {$_.path -notin $allowed}).Count){throw 'Unexpected cumulative UI source drift'}
$r4Changes=@()
foreach($relative in @('ViewModels/StudentSearchViewModel.cs','Views/StudentSearchView.xaml')){
    $before=Hash ('test-project1/test-report/20261012-evidence-01/CSharp_WPF/ui-fix-r4.before-'+[IO.Path]::GetFileName($relative))
    $after=Hash ($way+$relative)
    $r4Changes+=[ordered]@{path=$way+$relative;beforeSha256=$before.sha256;afterSha256=$after.sha256}
}
$testFiles=@('tests/GuiEvidence/Program.cs','tests/GuiEvidence/FixtureGateway.cs','tests/GuiEvidence/fixture.json','tests/GuiEvidence/GuiEvidence.csproj','tests/Smoke/Program.cs','tests/Smoke/NativeSmoke.csproj')|ForEach-Object {Hash ($way+$_)}
$now=[DateTimeOffset]::UtcNow.ToString('o')
$inputs=[ordered]@{runId='20261012-evidence-01-wpf-ui-fix-r4';recordedAtUtc=$now;specFiles=$spec;productionFiles=$production;testFiles=@($testFiles);baseline='test-report/20261012-evidence-01/CSharp_WPF/inputs.json'}
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'ui-fix-r4-inputs.json'),($inputs|ConvertTo-Json -Depth 10),$utf8)
$actual=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'ui-fix-r4.after-search.log') -Raw|ConvertFrom-Json
$self=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'ui-fix-r4.fixture-selftest.log') -Raw|ConvertFrom-Json
$smoke=[IO.File]::ReadAllText((Join-Path $PSScriptRoot 'ui-fix-r4.smoke.log'))
$red=[IO.File]::ReadAllText((Join-Path $PSScriptRoot 'ui-fix-r4.before-search.log'))
if(-not $actual.passed -or $actual.searchChecks.Count -ne 11 -or $self.passed -ne 15 -or $smoke -notmatch 'WPF smoke: 7 checks passed' -or $red -notmatch 'R4 applied-search incompatible class must clear ID and retain W-STU-107'){throw 'Fresh regression evidence mismatch'}
foreach($name in @('ui-fix-r4.after-build.log','ui-fix-r4.smoke-build.log')){
    $log=[IO.File]::ReadAllText((Join-Path $PSScriptRoot $name))
    if($log -notmatch '0 (Warning\(s\)|個の警告)' -or $log -notmatch '0 (Error\(s\)|エラー)'){throw 'Build evidence mismatch'}
}
$logNames=@('ui-fix-r4.before-build.log','ui-fix-r4.before-search.log','ui-fix-r4.after-build.log','ui-fix-r4.after-search.log','ui-fix-r4.fixture-selftest.log','ui-fix-r4.smoke-build.log','ui-fix-r4.smoke.log','ui-fix-r4.production.diff','ui-fix-r4.before-StudentSearchViewModel.cs','ui-fix-r4.before-StudentSearchView.xaml','ui-fix-r4.before-Program.cs')
$logs=@($logNames|ForEach-Object {Hash ('test-project1/test-report/20261012-evidence-01/CSharp_WPF/'+$_)})
$outputs=@('bin/Debug/net10.0-windows/StudentManagement.Wpf.dll','Core/bin/Debug/net10.0/StudentManagement.Core.dll','tests/GuiEvidence/bin/Debug/net10.0-windows/Wpf.GuiEvidence.exe','tests/GuiEvidence/bin/Debug/net10.0-windows/Wpf.GuiEvidence.dll')|ForEach-Object {Hash ($way+$_)}
$packageManifest=Get-Content -LiteralPath (Full 'test-project1/report/20261012-build-10-source-packages.json') -Raw|ConvertFrom-Json
$package=$packageManifest.packages|Where-Object {$_.profile -eq 'CSharp_WPF'}
$zipHash=Hash $package.file
if($zipHash.sha256 -ne $package.sha256){throw 'Frozen ZIP drift'}
$report=[ordered]@{
    runId='20261012-evidence-01-wpf-ui-fix-r4';projectId='test-project1';profile='CSharp_WPF';recordedAtUtc=$now;status='SEARCH_CLASS_WARNING_AND_UNASSIGNED_ENABLED_STATE_FIXED'
    issues=@('WPF-REVIEW-001: W-STU-107 overwritten after applied search','WPF-REVIEW-002: unassigned ON hierarchy controls not disabled')
    specBasis=@('spec/詳細仕様書/CSharp_WPF/01_学生検索画面.md:255 ON clears and disables hierarchy; OFF does not restore prior criteria','spec/詳細仕様書/CSharp_WPF/01_学生検索画面.md:256 incompatible class cleared with W-STU-107')
    productionChanges=$r4Changes;productionFilesChanged=2;cumulativeChangesFromInitialEvidence=$cumulative;testSourceChanges=@('tests/GuiEvidence/Program.cs actual Window regression and pausable fixture gateway only')
    behavior='Preserve class-cleared warning against generic draft message. Enable hierarchy only when idle and unassigned OFF; notify on busy, unassigned and candidate refresh/clear.'
    inputManifest='ui-fix-r4-inputs.json';specInputFiles=$spec.Count;specDocuments=@($spec|Where-Object {$_.path.EndsWith('.md')}).Count;specVersions=@($spec.version|Where-Object {$_}|Sort-Object -Unique);specShaDrift=0;baselineProductionFiles=$production.Count
    before=[ordered]@{buildExitCode=0;runExitCode=1;result='EXPECTED_FAILURE';failure='Applied search class cleared but warning overwritten with generic message';log='ui-fix-r4.before-search.log';disabledStateRegression='Added before fix but warning failure stopped the initial run first; disabled state issue was source-confirmed, then verified after fix.'}
    freshTests=@(
        [ordered]@{command='dotnet tests/GuiEvidence/bin/Debug/net10.0-windows/Wpf.GuiEvidence.dll --verify-startup search';exitCode=0;actualWindow=$actual;checkpoints=11;sqlIntegration=$false},
        [ordered]@{command='dotnet tests/GuiEvidence/bin/Debug/net10.0-windows/Wpf.GuiEvidence.dll --self-test';exitCode=0;passed=15;result=$self;sqlIntegration=$false},
        [ordered]@{command='dotnet tests/Smoke/bin/Debug/net10.0-windows/NativeSmoke.dll';exitCode=0;passed=7;windowsShown=0;sqlIntegration=$false}
    )
    builds=@([ordered]@{command='dotnet build tests/GuiEvidence/GuiEvidence.csproj --no-restore --nologo';exitCode=0;warnings=0;errors=0},[ordered]@{command='dotnet build tests/Smoke/NativeSmoke.csproj --no-restore --nologo';exitCode=0;warnings=0;errors=0})
    artifacts=$logs;outputAssemblies=@($outputs);fixture=Hash ($way+'tests/GuiEvidence/fixture.json');nullCriteriaMeaning='Unchanged: empty all option maps NULL; valid GRADE00 is retained; raw registration ID remains independent.'
    frozenSourceZip=[ordered]@{manifest='report/20261012-build-10-source-packages.json';file=$zipHash.path;sha256=$zipHash.sha256;changed=$false;containsCurrentUiFixes=$false;status='OLD_REVISION_FROZEN_NOT_UPDATED'}
    screenshotLauncher=[ordered]@{exe=$way+'tests/GuiEvidence/bin/Debug/net10.0-windows/Wpf.GuiEvidence.exe';command='--screen search';stop='Close window';state='Rebuilt, automated test Window closed, parent captures separately'}
    screenshotOperator='parent Agent';screenshotsByThisAgent=0;sqlConnections=0;sqlExecutions=0;notExecuted=@('SQL Server integration or SQLCLR hosting','DB identity/roles/authorization','Production CRUD/confirmation/concurrency/audit rollback','DPI150/200 matrix','Core/native normalization rerun for this UI-only fix','New/edit real startup rerun for this search-only fix')
    preserved='R1/R2/R3 evidence unchanged; pre-fix source/failed regression and new current lock are separate. Legacy ZIP kept immutable.'
}
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'ui-fix-r4-results.json'),($report|ConvertTo-Json -Depth 15),$utf8)
$md=[Collections.Generic.List[string]]::new()
$md.Add('# WPF 検索UI修正・再検査 R4')
$md.Add('')
$md.Add('検索済みの状態で上位条件に合わないクラスを解除するとW-STU-107が一般通知で上書きされる不具合と、未所属ONでも年度/学年/クラスが有効な不具合を修正した。既存検索詳細255-256行に従う局所実装修正であり、仕様・DB・Gateway契約は変更していない。')
$md.Add('')
$md.Add('SearchVMはクラス解除フラグを持ち、解除した場合のW-STU-107を一般変更通知より優先する。その他の条件変更通知は維持する。CanSelectClassCriteriaはIsIdleかつ未所属OFFで、busy/未所属/候補再生成/Clear時に通知する。検索XAMLの3ComboBoxだけにbindした。未所属OFFでも以前の条件は復元しない。')
$md.Add('')
$md.Add('同じ実Window回帰を修正前に実行し、検索済み状態のクラス解除警告が失われて期待失敗exit1になった。初回はここで停止したため、未所属非活性の修正前実行失敗まで確認したと主張しない。その欠陥はソース/仕様で確認し、修正後の実Windowで検証した。')
$md.Add('')
$md.Add('修正後の **実検索Window11状態PASS**：初期NULL、適合クラス選択/保持、検索済み不適合ClassId=null＋W-STU-107保持、通常未反映通知、Clear、未所属ONの解除＋3非活性、OFFの3活性＋null保持、非同期busyの3非活性、完了後の活性復帰、不適合解除。busyはテスト専用fixture検索をTaskで実際に保留してから解放し、実WPF IsEnabledを確認した。')
$md.Add('')
$md.Add('今回の同じ現行入力で **fixture自己試験15/15、Smoke7/7** を新規再実行した。撮影exeを含む本体/fixtureとSmokeビルドは警告0・エラー0。検査Windowは実Show/ContentRenderedを通過し、自動Closeした。画像撮影は親Agentが担当する。')
$md.Add('')
$md.Add('R4本体変更はSearchVMとSearchView.xamlの2ファイルだけ。テスト側はGuiEvidence Program.csへ意味のあるWindow回帰とfixture一時停止委譲を追加。方式内spec46入力（Markdown42文書、8.0/8.1）はSHA不変。初期evidenceからの本体累積差分はR2/R3を含む4ファイルで、それ以外の基準35本体入力は不変。')
$md.Add('')
$md.Add('|R4本体|修正前SHA256|修正後SHA256|')
$md.Add('|---|---|---|')
foreach($change in $r4Changes){$md.Add('|'+$change.path+'|'+$change.beforeSha256+'|'+$change.afterSha256+'|')}
$md.Add('')
$md.Add('生ログはui-fix-r4.before/after-search.log、fixture-selftest.log、smoke.logと各build.log。実差分production.diff、修正前スナップショット、入力lock ui-fix-r4-inputs.json、出力DLL/exe・ログSHAをui-fix-r4-results.jsonへ保存した。過去R1-R3は上書きしない。')
$md.Add('')
$md.Add('撮影入口は方式内 `tests/GuiEvidence/bin/Debug/net10.0-windows/Wpf.GuiEvidence.exe --screen search`。現行DLL/exeを再ビルド済み、通常の閉じる操作で停止する。fixtureには保存拒否/SQL未接続の制約がある。SQL接続/実行は0、DB認可/CRUD/SQLCLR hosting、DPI150/200%、Core/native再実行、新規/編集実起動のR4再実行は未実施。これらの旧合格は今回の新実行結果として流用しない。')
$md.Add('')
$md.Add('build10 source ZIPは旧改訂の凍結成果としてSHAを確認し保持、今回更新していない。今回修正を含むのは現行srcsとR4入力manifestであり、旧ZIPを現行修正版として使わない。')
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'ui-fix-r4-report.md'),($md -join "`n")+"`n",$utf8)
Write-Output 'WPF R4 saved: actual Window11, fixture15, Smoke7 PASS; spec unchanged; source ZIP frozen.'
