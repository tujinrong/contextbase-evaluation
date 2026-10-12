Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$prefix = '20261012-evidence-01-VB.NET_WinForms-after-fix'
$way = 'test-project1/srcs/VB.NET_WinForms/'
$utf8 = [Text.UTF8Encoding]::new($false)
function Full([string]$relative) {Join-Path $workspace $relative}
function Fingerprint([string]$relative) {
    $path=Full $relative
    [ordered]@{path=$relative;sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant();bytes=(Get-Item -LiteralPath $path).Length}
}
foreach($suffix in @('.json','.md','.inputs.json')) {if(Test-Path -LiteralPath (Join-Path $PSScriptRoot ($prefix+$suffix))){throw 'Existing report protected'}}
$baselinePath='test-project1/test-report/20261012-evidence-01/VB.NET_WinForms/inputs.json'
$baseline=Get-Content -LiteralPath (Full $baselinePath) -Raw|ConvertFrom-Json
$production=@($baseline.productionFiles|ForEach-Object {[pscustomobject](Fingerprint $_.path)})
$spec=@($baseline.specFiles|ForEach-Object {$r=Fingerprint $_.path;$r['version']=$_.version;[pscustomobject]$r})
$sourceChanges=@()
for($i=0;$i -lt $production.Count;$i++) {
    if($production[$i].sha256 -ne $baseline.productionFiles[$i].sha256.ToLowerInvariant()) {
        $sourceChanges+=[ordered]@{path=$production[$i].path;beforeSha256=$baseline.productionFiles[$i].sha256.ToLowerInvariant();afterSha256=$production[$i].sha256}
    }
}
$allowed=@(($way+'Forms/FrmStudentEdit.Designer.vb'),($way+'Forms/FrmStudentEdit.vb'))
if($sourceChanges.Count -ne 2 -or @($sourceChanges|Where-Object {$_.path -notin $allowed}).Count){throw 'Unexpected production changes'}
$specDrift=@()
for($i=0;$i -lt $spec.Count;$i++){if($spec[$i].sha256 -ne $baseline.specFiles[$i].sha256.ToLowerInvariant()){$specDrift+=$spec[$i].path}}
if($specDrift.Count){throw 'Unexpected spec drift'}
$tests=@('Tests/StudentManagement.WinForms.Tests.vbproj','Tests/Program.vb','Tests/GuiEvidence/GuiEvidence.vbproj','Tests/GuiEvidence/Program.vb','Tests/GuiEvidence/InitialFocusRegression.vb','Tests/GuiEvidence/FixtureApplicationService.vb','Tests/GuiEvidence/FixtureService.vb','Tests/GuiEvidence/fixture.json','Tests/GuiEvidence/README.md','database/native/tests/Framework/NativeFramework.Tests.csproj','database/native/tests/Framework/Program.cs')|ForEach-Object {Fingerprint ($way+$_)}
$records=[ordered]@{
    id=$prefix+'-inputs';projectId='test-project1';profile='VB.NET_WinForms';recordedAtUtc=[DateTimeOffset]::UtcNow.ToString('o');baseline=$baselinePath
    specFiles=$spec;productionFiles=$production;testFiles=@($tests)
}
[IO.File]::WriteAllText((Join-Path $PSScriptRoot ($prefix+'.inputs.json')),($records|ConvertTo-Json -Depth 10),$utf8)
$guiLines=[IO.File]::ReadAllLines((Join-Path $PSScriptRoot ($prefix+'.gui-regression.raw.log')))
$guiResult=$guiLines[-1]|ConvertFrom-Json
$observations=@($guiLines[0..2]|ForEach-Object {($_|ConvertFrom-Json).initialObservation})
$boundary=Get-Content -LiteralPath (Join-Path $PSScriptRoot ($prefix+'.boundary.raw.log')) -Raw|ConvertFrom-Json
$fixture=Get-Content -LiteralPath (Join-Path $PSScriptRoot ($prefix+'.fixture.raw.log')) -Raw|ConvertFrom-Json
$framework=[IO.File]::ReadAllText((Join-Path $PSScriptRoot ($prefix+'.framework.raw.log')))
if($guiResult.passed -ne 18 -or $guiResult.failed -ne 0 -or $boundary.passed -ne 111 -or $fixture.passed -ne 15 -or $framework -notmatch 'PASS: 23 actual .NET Framework assembly assertions'){throw 'Fresh test evidence mismatch'}
foreach($suffix in @('.production-build.raw.log','.fixture-build.raw.log','.framework-build.raw.log')) {
    $log=[IO.File]::ReadAllText((Join-Path $PSScriptRoot ($prefix+$suffix)))
    if($log -notmatch '0 (Warning\(s\)|個の警告)' -or $log -notmatch '0 (Error\(s\)|エラー)'){throw 'Build evidence mismatch'}
}
$logSuffixes=@('.regression-before.raw.log','.regression-before-r2.raw.log','.gui-regression.raw.log','.boundary.raw.log','.fixture.raw.log','.framework.raw.log','.production-build.raw.log','.fixture-build.raw.log','.framework-build.raw.log','.production.diff','.before-designer.vb','.before-form.vb')
$logs=@($logSuffixes|ForEach-Object {Fingerprint ('test-project1/test-report/'+$prefix+$_)})
$outputs=@('bin/Debug/net10.0-windows/StudentManagement.WinForms.dll','Tests/GuiEvidence/bin/Debug/net10.0-windows/Vb.GuiEvidence.exe','Tests/GuiEvidence/bin/Debug/net10.0-windows/Vb.GuiEvidence.dll','database/native/Normalization/bin/Debug/net472/StudentNativeNormalization.dll')|ForEach-Object {Fingerprint ($way+$_)}
$captures=Get-Content -LiteralPath (Full 'test-project1/test-evidence/20261012-evidence-01/native-captures.json') -Raw|ConvertFrom-Json
$ownCaptures=@($captures|Where-Object {$_.file -like 'VB.NET_WinForms/*'})
foreach($capture in $ownCaptures){if((Fingerprint ('test-project1/test-evidence/20261012-evidence-01/'+$capture.file)).sha256 -ne $capture.sha256){throw 'Parent screenshot SHA mismatch'}}
$report=[ordered]@{
    id=$prefix;projectId='test-project1';profile='VB.NET_WinForms';recordedAtUtc=[DateTimeOffset]::UtcNow.ToString('o');issue='UI-OBS-VB-001';classification='implementation focus/scroll bug';structuralBlocker=$false
    sourceEvidence=@('Forms/FrmStudentEdit.Designer.vb:31 read-only message TextBox previously inherited TabStop=True','Forms/FrmStudentEdit.Designer.vb:50 fields previously retained default TabIndex','Forms/FrmStudentEdit.vb:14 Shown previously initialized asynchronously without selecting initial input')
    cause='Default tab selection can focus the read-only message or another off-screen control during Shown; no post-initialization focus/scroll target was set.'
    fix='Exclude message from tab traversal; set input/action tab order; after async Shown initialization queue first selectable input focus then scroll to top. Viewer focuses Back. Keep multiline scrollable message.'
    beforeObservation=[ordered]@{screen='new';focus='message';scrollY=-289;messageTabStop=$true;actualFormShown=$true;result='EXPECTED_FAILURE';log=$prefix+'.regression-before-r2.raw.log';parentEditObservation='AutoScroll 84 hid the first rows; parent preserved 06/07 screenshots'}
    harnessPreflight=[ordered]@{result='COMPILE_FAILURE_CORRECTED';cause='New test variable role shadowed VB Role enum (case-insensitive); renamed to testRole. Production unchanged at that stage.';log=$prefix+'.regression-before.raw.log'}
    sourceChanges=$sourceChanges;productionFilesChanged=2;specFilesChanged=0;specInputFiles=$spec.Count;specDocuments=@($spec|Where-Object {$_.path.EndsWith('.md')}).Count;specVersions=@($spec.version|Where-Object {$_}|Sort-Object -Unique);specShaDrift=0
    baselineProductionFiles=$production.Count;inputManifest=$prefix+'.inputs.json'
    testChanges=@('Tests/GuiEvidence/InitialFocusRegression.vb added','Tests/GuiEvidence/Program.vb --ui-regression entry added','Tests/GuiEvidence/GuiEvidence.vbproj includes new test module','Tests/GuiEvidence/README.md documents new test')
    specBasis=@('spec/共通/01_システム概要.md:79 headings/input/error/action order and long text access','spec/共通/04_共通UI部品設計.md:25 UI-14 long text editing/viewing','spec/共通/方式別/VB.NET_WinForms/01_共通実装仕様.md:97 ErrorProvider/messages, await async UI operation, do not update disposed Form')
    tests=@(
        [ordered]@{kind='own Core/control/wire boundaries';command='dotnet run --project Tests/StudentManagement.WinForms.Tests.vbproj --no-restore';exitCode=0;passed=$boundary.passed;sqlIntegration=$false},
        [ordered]@{kind='actual .NET Framework normalization wrappers';build='dotnet build database/native/tests/Framework/NativeFramework.Tests.csproj --no-restore --nologo';command='database/native/tests/Framework/bin/Debug/net472/NativeFramework.Tests.exe';exitCode=0;passed=23;sqlServerHosting=$false},
        [ordered]@{kind='existing own fixture presenter tests';command='dotnet run --project Tests/GuiEvidence/GuiEvidence.vbproj --no-restore -- --self-test';exitCode=0;passed=$fixture.passed;actualFormShown=$false;sqlIntegration=$false},
        [ordered]@{kind='new actual Form Shown/message-loop regression';command='dotnet run --project Tests/GuiEvidence/GuiEvidence.vbproj --no-restore -- --ui-regression';exitCode=0;passed=$guiResult.passed;actualFormShown=$true;observations=$observations;cases=$guiResult.cases;sqlIntegration=$false}
    )
    builds=[ordered]@{production='PASS 0 warnings 0 errors';fixture='PASS 0 warnings 0 errors';framework='PASS 0 warnings 0 errors'}
    fixtureData=Fingerprint ($way+'Tests/GuiEvidence/fixture.json');outputAssemblies=@($outputs);artifacts=$logs;parentScreenshots=$ownCaptures
    screenshotLauncher=[ordered]@{exe=$way+'Tests/GuiEvidence/bin/Debug/net10.0-windows/Vb.GuiEvidence.exe';arguments='--screen new|edit [--role admin|staff|viewer]';stop='Close form';testWindows='All regression windows automatically closed';operator='parent Agent only'}
    concreteAdapterLimitation='Production Form/Presenter/controls compile directly from way-local sources, but their concrete StudentApplicationService is replaced by a test-only same-name fixture adapter. Production DB authentication adapter is only built, not executed.'
    sqlConnections=0;sqlExecutions=0;screenshotsByThisAgent=0
    preserved='Original evidence-01 reports/logs/captures unchanged; new pre-fix source and regression logs retained. Test-harness compile failure retained distinctly.'
    notExecuted=@('Live SQL Server integration','Production DB identity/roles and authorization','SQL persistence/confirmation/concurrency/audit rollback','SQLCLR Server hosting','DPI150/200 percent matrix','Browser or native screenshots by this Agent')
}
[IO.File]::WriteAllText((Join-Path $PSScriptRoot ($prefix+'.json')),($report|ConvertTo-Json -Depth 14),$utf8)
$md=[Collections.Generic.List[string]]::new()
$md.Add('# VB 初期フォーカス・スクロール修正後検証')
$md.Add('')
$md.Add('初期表示で読み取り専用メッセージ欄へcaretが入り、学籍番号・氏名の先頭行が上に隠れる実装不具合を修正した。メッセージ欄をTab移動対象から外し、項目/操作のTab順を設定した。Shownの非同期初期化が終わった後、最初の編集可能入力にフォーカスを置いてスクロールを上端へ戻す。参照ロールでは戻るボタンへ置く。長文メッセージ欄は維持する。')
$md.Add('')
$md.Add('修正前の実Show回帰では新規のfocus=message、scrollY=-289、TabStop=trueを確認し期待失敗した。親の実撮影では編集のAutoScroll84を確認した。値の差は表示寸法に依存し、同じ先頭行消失を示す。')
$md.Add('')
$md.Add('修正後にSTAの実Form/メッセージループを動かした **GUI回帰18/18 PASS**。新規focus=studentNo、編集focus=studentName、参照focus=back、全てscrollY=0。先頭行可視、次Tab順、readonly/multiline/縦スクロール/高さ70のメッセージ保持、参照入力disabledも確認した。テスト窓は全て自動で閉じた。')
$md.Add('')
$md.Add('同じ現行入力で既存 **境界111/111、実.NET Framework wrapper23/23、撮影fixture15/15** を新規再実行した。本体/撮影fixture/Frameworkのビルドは全て警告0・エラー0。過去の合格を今回結果として流用していない。')
$md.Add('')
$md.Add('本体は FrmStudentEdit.Designer.vb と FrmStudentEdit.vb の2ファイルのみ変更。変更前後SHA、実差分 `.production.diff`、新入力ロック `.inputs.json`、出力DLL/fixture/生ログSHAをJSONに保存した。仕様46入力（Markdown42文書、8.0/8.1）は原SHA不変、仕様BUGは認めず変更なし。DB/業務仕様/認証adapterは変更していない。')
$md.Add('')
$md.Add('|本体ファイル|変更前SHA256|変更後SHA256|')
$md.Add('|---|---|---|')
foreach($change in $sourceChanges){$md.Add('|'+$change.path+'|'+$change.beforeSha256+'|'+$change.afterSha256+'|')}
$md.Add('')
$md.Add('GUI検証装置の初回コンパイルは変数roleと列挙RoleのVB大小文字名衝突で失敗した。testRoleへ装置だけ修正して、r2で本体修正前の不具合を実再現した。最初の失敗生ログも保存し、製品試験の失敗と混同しない。')
$md.Add('')
$md.Add('親の撮影入口は `srcs/VB.NET_WinForms/Tests/GuiEvidence/bin/Debug/net10.0-windows/Vb.GuiEvidence.exe --screen new` または `--screen edit`。再ビルド済み。通常のフォーム終了で停止する。元の06-edit-initial-scroll/07-edit-manual-scroll-top等の画像は保持し、親の修正後撮影を追加する。')
$md.Add('')
$md.Add('具体adapter制約：本体Form/Presenter/Controlsのソースを直接コンパイルするが、具象StudentApplicationServiceのみ同名のテスト用fixture委譲へ置換している。本番DB認証adapterは本体ビルドに含むが実行していない。SQL接続・実行は0。SQLCLRサーバー内実行、DB認可/保存/確認/競合/監査、DPI150/200%は未実施。共有SQL構造衝突の設計修正は対象外。画面撮影は親Agentが担当。')
[IO.File]::WriteAllText((Join-Path $PSScriptRoot ($prefix+'.md')),($md -join "`n")+"`n",$utf8)
Write-Output "VB report saved; production changes $($sourceChanges.Count), spec drift 0, fresh PASS 111+23+15+18."
