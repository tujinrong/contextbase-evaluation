Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$prefix = '20261012-evidence-01-CSharp_ASPNET-after-fix'
$utf8 = [Text.UTF8Encoding]::new($false)
function Full([string]$relative) { Join-Path $workspace $relative }
function HashRecord([string]$relative) {
    $path = Full $relative
    [ordered]@{file=$relative;sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant();bytes=(Get-Item -LiteralPath $path).Length}
}
foreach($suffix in @('.json','.md','.inputs.json','.diff')) {
    if(Test-Path -LiteralPath (Join-Path $PSScriptRoot ($prefix+$suffix))) { throw "Existing report protected: $prefix$suffix" }
}
$oldInput = Get-Content -LiteralPath (Join-Path $PSScriptRoot '20261012-evidence-01-CSharp_ASPNET.inputs.json') -Raw | ConvertFrom-Json
$current = @($oldInput.files | ForEach-Object {
    $r = HashRecord $_.file
    $r['version'] = $_.version
    $r['documentId'] = $_.documentId
    [pscustomobject]$r
})
$changes = @()
for($i=0;$i -lt $current.Count;$i++) {
    if($current[$i].sha256 -ne $oldInput.files[$i].sha256) {
        $changes += [ordered]@{file=$current[$i].file;beforeSha256=$oldInput.files[$i].sha256;afterSha256=$current[$i].sha256}
    }
}
$allowed = @('test-project1/srcs/CSharp_ASPNET/Views/Shared/_MessagePanel.cshtml','test-project1/srcs/CSharp_ASPNET/tests/Program.cs')
if($changes.Count -ne 2 -or @($changes | Where-Object {$_.file -notin $allowed}).Count -gt 0) { throw 'Unexpected source drift' }
$oldVue = Get-Content -LiteralPath (Join-Path $PSScriptRoot '20261012-evidence-01-Vue_CSharpAPI.inputs.json') -Raw | ConvertFrom-Json
$vueChanges = @($oldVue.files | Where-Object {(HashRecord $_.file).sha256 -ne $_.sha256})
if($vueChanges.Count) { throw 'Vue changed unexpectedly' }
$spec = @($current | Where-Object {$_.file -like '*/spec/*' -and $_.documentId})
$contract = [IO.File]::ReadAllText((Join-Path $PSScriptRoot ($prefix+'.contract.raw.log')))
$build = [IO.File]::ReadAllText((Join-Path $PSScriptRoot ($prefix+'.host-build-r2.raw.log')))
$red = [IO.File]::ReadAllText((Join-Path $PSScriptRoot ($prefix+'.regression-before.raw.log')))
if($contract -notmatch 'MVC contract checks: 42 passed' -or $red -notmatch 'FAILED: UI-OBS-MVC-001 initial search has no empty error panel') { throw 'Regression evidence mismatch' }
if($build -notmatch '0 (Warning\(s\)|個の警告)' -or $build -notmatch '0 (Error\(s\)|エラー)') { throw 'Build evidence mismatch' }
$now = [DateTimeOffset]::UtcNow.ToString('o')
$input = [ordered]@{id=$prefix+'-inputs';recordedAtUtc=$now;root='test-project1/srcs/CSharp_ASPNET';baseline='20261012-evidence-01-CSharp_ASPNET.inputs.json';files=$current}
[IO.File]::WriteAllText((Join-Path $PSScriptRoot ($prefix+'.inputs.json')),($input|ConvertTo-Json -Depth 12),$utf8)
$before = [IO.File]::ReadAllText((Join-Path $PSScriptRoot ($prefix+'.before-partial.cshtml'))).TrimEnd("`r","`n")
$after = [IO.File]::ReadAllText((Full $allowed[0])).TrimEnd("`r","`n")
$beforeLines = $before -split '\r?\n'
$afterLines = $after -split '\r?\n'
if($beforeLines.Count -ne 3 -or $afterLines.Count -ne 3 -or $beforeLines[0] -ne $afterLines[0] -or $beforeLines[2] -ne $afterLines[2]) { throw 'Unexpected partial diff' }
$diff = "--- before/Views/Shared/_MessagePanel.cshtml`n+++ after/Views/Shared/_MessagePanel.cshtml`n@@ -1,3 +1,3 @@`n " + $beforeLines[0] + "`n-" + $beforeLines[1] + "`n+" + $afterLines[1] + "`n " + $beforeLines[2] + "`n"
[IO.File]::WriteAllText((Join-Path $PSScriptRoot ($prefix+'.diff')),$diff,$utf8)
$logNames = @('.regression-before.raw.log','.contract.raw.log','.host-build-r2.raw.log','.stop-before-host.raw.log')
$logHashes = @($logNames | ForEach-Object {HashRecord ('test-project1/test-report/'+$prefix+$_)})
$assemblies = @(
    'test-project1/srcs/CSharp_ASPNET/bin/Release/net10.0/StudentManagement.Web.dll',
    'test-project1/srcs/CSharp_ASPNET/Core/bin/Release/net10.0/StudentManagement.Core.dll',
    'test-project1/srcs/CSharp_ASPNET/tests/EvidenceHost/bin/Release/net10.0/EvidenceHost.dll'
) | ForEach-Object {HashRecord $_}
$captures = Get-Content -LiteralPath (Full 'test-project1/test-evidence/20261012-evidence-01/web-captures.json') -Raw | ConvertFrom-Json
$afterCaptures = @($captures | Where-Object {$_.file -in @('CSharp_MVC/08-after-fix-search.jpg','CSharp_MVC/09-after-fix-new.jpg')})
foreach($capture in $afterCaptures) {
    if((HashRecord ('test-project1/test-evidence/20261012-evidence-01/'+$capture.file)).sha256 -ne $capture.sha256) { throw 'Screenshot SHA mismatch' }
}
$checks = @(
    'Initial search has no empty error panel',
    'Initial search has no empty hidden summary bullet',
    'New registration has no empty error panel',
    'New registration has no empty hidden summary bullet',
    'Existing BigInt edit has no empty error panel',
    'Existing edit has no empty hidden summary bullet',
    'Actual stale-context global validation stays visible',
    'Actual model-binding validation returns 422 and stays visible',
    'Service field validation returns 422 and stays visible in real Razor summary',
    'Normal reset information stays visible',
    'Reset information creates no empty error panel'
)
$report = [ordered]@{
    id=$prefix;projectId='test-project1';profile='CSharp_ASPNET';recordedAtUtc=$now
    issue='UI-OBS-MVC-001';classification='implementation UI bug';severity='minor';structuralBlocker=$false
    cause='Unconditionally rendered validation summary receives the message/error padding and border even when MVC renders only an empty hidden list item.'
    fix='Render the error summary only when ViewData.ModelState.ErrorCount > 0; preserve the independent information panel.'
    sourceChanges=$changes;productionFilesChanged=1;testFilesChanged=1;specFilesChanged=0
    specBasis=@('spec/共通/04_共通UI部品設計.md:13 UI-02 information/warning/error distinction','spec/共通/04_共通UI部品設計.md:53 preserve input and associated errors')
    inputManifest=$prefix+'.inputs.json';inputFiles=$current.Count;specDocuments=$spec.Count;specVersions=@($spec.version|Sort-Object -Unique)
    specShaDrift=0;baselineInput='20261012-evidence-01-CSharp_ASPNET.inputs.json';vueBaselineInput='20261012-evidence-01-Vue_CSharpAPI.inputs.json';vueInputsChecked=$oldVue.files.Count;vueInputChanges=$vueChanges.Count
    tests=@(
        [ordered]@{kind='Before-fix regression reproduction';command='dotnet run --project tests/WebContracts.csproj -c Release --no-restore';exitCode=-532462766;result='EXPECTED_FAILURE';failure='Initial search has empty error panel';log=$prefix+'.regression-before.raw.log'},
        [ordered]@{kind='After-fix real HTTP/controller/Razor contracts';command='dotnet run --project tests/WebContracts.csproj -c Release --no-restore';exitCode=0;assertions=42;newAssertions=11;sqlIntegration=$false;log=$prefix+'.contract.raw.log'},
        [ordered]@{kind='After-fix screenshot host build';command='dotnet build tests/EvidenceHost/EvidenceHost.csproj -c Release --no-restore';exitCode=0;warnings=0;errors=0;log=$prefix+'.host-build-r2.raw.log'}
    )
    newRegressionChecks=$checks;outputAssemblies=$assemblies;logs=$logHashes
    fixture=HashRecord 'test-project1/srcs/CSharp_ASPNET/tests/EvidenceHost/fixture-data.json'
    host=[ordered]@{url='https://localhost:7441/__evidence/login?role=Staff';startup='dotnet tests/EvidenceHost/bin/Release/net10.0/EvidenceHost.dll --port=7441 --minutes=60';lifetimeMinutes=60;stop='POST https://localhost:7441/__evidence/stop';session=40387;runtimeLog=$prefix+'.host-runtime-r2.log';runtimeLogMutable=$true;state='Restarted after fix for parent final UI captures';vueHost='7442 unchanged'}
    preserved='All original evidence-01 reports/logs/captures retained. Before-fix regression and partial retained as separate new evidence.'
    screenshotOperator='parent Agent only';parentAfterFixCaptures=$afterCaptures;uiOperationsByThisAgent=0;sqlConnections=0;sqlExecutions=0
    notExecuted=@('Live SQL Server integration','Shared schema/role/CLR repair','Production authentication or DB-role authorization','SQL persistence/concurrency/audit rollback','Final browser captures by this Agent')
    limitations=@('IStudentService is a fake/read-only fixture; real Razor/controller HTTP rendering is tested, SQL behavior is not.','Parent visually confirmed fixed initial/new screens; existing edit is covered by the fresh real Razor contract.','Earlier Core and Vue passes remain historical evidence and were not claimed as fresh after-fix executions.')
}
[IO.File]::WriteAllText((Join-Path $PSScriptRoot ($prefix+'.json')),($report|ConvertTo-Json -Depth 14),$utf8)
$md = [Collections.Generic.List[string]]::new()
$md.Add('# MVC UI-OBS-MVC-001 修正後検証')
$md.Add('')
$md.Add('初期検索・新規・編集画面の空エラー枠は、本体の共通Razor部分がエラー0件でも常時描画される実装不具合だった。`ModelState.ErrorCount > 0` のときだけエラー要約を描画する修正を行い、情報表示は維持した。')
$md.Add('')
$md.Add('仕様 `共通/04_共通UI部品設計.md` のUI-02（13行）および入力エラー保持（53行）に沿う局所修正であり、仕様変更は不要。DB・共通サービス・他方式の本体は変更していない。')
$md.Add('')
$md.Add('修正対象は `_MessagePanel.cshtml:2`、追加検証は `tests/Program.cs:44` 以降の11項目。初期・新規・既存編集で空パネル/空bulletなし、実際の全体エラー・モデルバインドエラー・サービス入力エラーは可視、通常情報も可視を実HTTP・本体Controller・実Razorで確認した。')
$md.Add('')
$md.Add('修正前に追加回帰検証を実行して初期検索の空枠で期待どおり失敗した。修正後の同じ契約試験は **42/42 PASS**、撮影ホスト再ビルドは **警告0・エラー0**。偽サービスを使う描画契約検証であり、SQL実統合の合格ではない。')
$md.Add('')
$md.Add('入力は方式内107ファイルを新しい `.inputs.json` に保存。原証跡からの差分は許可されたRazor1ファイルと契約試験1ファイルのみ。仕様42文書（8.0/8.1）はSHA不変。Vue方式の124入力は全件SHA不変。')
$md.Add('')
$md.Add('|変更ファイル|修正前SHA256|修正後SHA256|')
$md.Add('|---|---|---|')
foreach($c in $changes){$md.Add('|'+$c.file+'|'+$c.beforeSha256+'|'+$c.afterSha256+'|')}
$md.Add('')
$md.Add('修正前の部分ソース、期待失敗生ログ、修正後試験生ログ、ビルド生ログ、停止生ログ、差分、新しい入力ロックを別名保存した。元のevidence-01結果・画面・ログは上書きしていない。詳細の出力DLL・ログSHAは同名JSON。')
$md.Add('')
$md.Add('MVC 7441は修正後DLLで再起動済み。親Agentは `https://localhost:7441/__evidence/login?role=Staff` から新しいセッションを開始して最終撮影する。寿命60分、停止は `POST /__evidence/stop`。生ログ `'+$prefix+'.host-runtime-r2.log` は稼働中なので可変。Vue7442は変更・再起動していない。')
$md.Add('')
$md.Add('親Agentは修正後の実ブラウザーで空枠消失を確認し、`test-evidence/20261012-evidence-01/CSharp_MVC/08-after-fix-search.jpg`、`09-after-fix-new.jpg` を保存した。メタデータの画像SHAを実ファイルと照合済み。既存編集の空エラー非表示も本回42件の実Razor契約で確認済み。')
$md.Add('')
$md.Add('このAgentのUI操作・画面撮影・SQL接続・SQL実行は0。共有SQLのroles/CLR構造衝突修正、実DB・本番認証/認可、保存/競合/監査ロールバックは未実施。元のCore/Vue検証を本修正の新実行結果として流用していない。')
[IO.File]::WriteAllText((Join-Path $PSScriptRoot ($prefix+'.md')),($md -join "`n")+"`n",$utf8)
Write-Output "Report saved: $prefix; source inputs $($current.Count), spec $($spec.Count), authorized changes $($changes.Count), Vue changed $($vueChanges.Count), contracts 42 PASS."
