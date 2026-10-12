[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
$repoRoot=Split-Path -Parent $projectRoot
$utf8=[Text.UTF8Encoding]::new($false)
$baseline=Get-Content -LiteralPath (Join-Path $projectRoot 'report/20261012-sqlserver-12-inputs.json') -Raw -Encoding UTF8|ConvertFrom-Json
foreach($way in @('CSharp_ASPNET','Vue_CSharpAPI')) {
    $stem='20261012-evidence-01-'+$way
    foreach($extension in @('json','md','inputs.json')){if(Test-Path -LiteralPath (Join-Path $PSScriptRoot ($stem+'.'+$extension))){throw 'Existing evidence must not be overwritten.'}}
    $root=Join-Path $projectRoot ('srcs/'+$way)
    Push-Location -LiteralPath $root
    try {$relative=@(& rg --files --hidden --glob '!**/bin/**' --glob '!**/obj/**' --glob '!**/build/**' --glob '!**/node_modules/**' --glob '!**/.git/**' --glob '!**/test-report/**' | Sort-Object)}
    finally {Pop-Location}
    if($LASTEXITCODE -ne 0){throw 'Own-project input inventory failed.'}
    $files=@(foreach($entry in $relative){
        $path=Join-Path $root $entry
        $version=$null;$documentId=$null
        if($entry -like 'spec\*' -and [IO.Path]::GetExtension($entry) -eq '.md'){
            $first=[IO.File]::ReadLines($path)|Select-Object -First 1
            $match=[regex]::Match($first,'<!-- spec-meta: (?<json>.+) -->')
            if($match.Success){$meta=$match.Groups['json'].Value|ConvertFrom-Json;$version=$meta.version;$documentId=$meta.documentId}
        }
        [pscustomobject]@{file=('test-project1/srcs/'+$way+'/'+$entry.Replace('\','/'));sha256=(Get-FileHash -LiteralPath $path).Hash.ToLowerInvariant();bytes=(Get-Item -LiteralPath $path).Length;version=$version;documentId=$documentId}
    })
    $spec=@($files|Where-Object {$_.documentId})
    $mismatch=@(foreach($file in $spec){$prior=@($baseline.files|Where-Object {$_.file -eq $file.file});if($prior.Count -ne 1 -or $prior[0].sha256 -cne $file.sha256){$file.file}})
    if($mismatch.Count -ne 0){throw 'Own specification drifted from the current input lock.'}
    $contractLog=Join-Path $PSScriptRoot ($stem+'-contract.raw.log')
    $coreLog=Join-Path $PSScriptRoot ($stem+'-core.raw.log')
    $fixtureLog=Join-Path $PSScriptRoot ($stem+'-fixture.raw.log')
    $contractText=[IO.File]::ReadAllText($contractLog)
    $coreText=[IO.File]::ReadAllText($coreLog)
    $fixtureText=[IO.File]::ReadAllText($fixtureLog)
    $contractMatch=[regex]::Match($contractText,'contract checks: (\d+) passed')
    $coreMatch=[regex]::Match($coreText,'PASS (\d+) independent boundary assertions')
    $fixtureMatch=[regex]::Match($fixtureText,'PASS fixture [^:]+: (\d+) checks')
    if(-not $contractMatch.Success -or -not $coreMatch.Success -or -not $fixtureMatch.Success){throw 'Actual execution success markers are missing.'}
    $contracts=[int]$contractMatch.Groups[1].Value;$core=[int]$coreMatch.Groups[1].Value;$fixture=[int]$fixtureMatch.Groups[1].Value
    $port=if($way -eq 'CSharp_ASPNET'){7441}else{7442}
    $contractProject=if($way -eq 'CSharp_ASPNET'){'tests/WebContracts.csproj'}else{'tests/ApiContracts.csproj'}
    $mainDll=if($way -eq 'CSharp_ASPNET'){'bin/Release/net10.0/StudentManagement.Web.dll'}else{'backend/bin/Release/net10.0/StudentManagement.Api.dll'}
    $artifacts=@(foreach($relativeDll in @($mainDll,'Core/bin/Release/net10.0/StudentManagement.Core.dll','tests/EvidenceHost/bin/Release/net10.0/EvidenceHost.dll')){$full=Join-Path $root $relativeDll;[pscustomobject]@{file=('test-project1/srcs/'+$way+'/'+$relativeDll);sha256=(Get-FileHash -LiteralPath $full).Hash.ToLowerInvariant();bytes=(Get-Item -LiteralPath $full).Length}})
    $fixturePath=Join-Path $root 'tests/EvidenceHost/fixture-data.json'
    $testData=Get-Content -LiteralPath $fixturePath -Raw -Encoding UTF8|ConvertFrom-Json
    $observations=@()
    if($way -eq 'CSharp_ASPNET'){
        $observations+= [pscustomobject]@{id='UI-OBS-MVC-001';severity='minor';observer='parent Agent via real browser';behavior='Initial/edit/new screens show an empty validation-summary red frame and empty bullet';captureReferences=@('01','03','06');runtimeChanged=$false;structuralBlocker=$false}
        $observations+= [pscustomobject]@{id='CAPTURE-MVC-005';classification='INVALID_CAPTURE';observer='parent Agent';behavior='tab.screenshot(fullPage:false) returned a blank capture; native CUA getScreenshot was valid and used instead';applicationFailure=$false}
        $observations+= [pscustomobject]@{id='UI-MVC-PARENT-CHECKS';observer='parent Agent via real browser';checks=@('Search shows 2 default status rows','Exact BigInt student edit screen opens','Required input browser native bubble appears');sqlIntegration=$false}
    }
    $logPaths=@($contractLog,$coreLog,$fixtureLog,(Join-Path $PSScriptRoot ($stem+'-host-build.raw.log')))
    if($way -eq 'Vue_CSharpAPI'){$logPaths+=(Join-Path $PSScriptRoot ($stem+'-typecheck.raw.log'))}
    $logs=@(foreach($path in $logPaths){[pscustomobject]@{file=('test-project1/test-report/'+[IO.Path]::GetFileName($path));sha256=(Get-FileHash -LiteralPath $path).Hash.ToLowerInvariant();bytes=(Get-Item -LiteralPath $path).Length}})
    $record=[ordered]@{
        id=$stem;projectId='test-project1';profile=$way;stage='build evidence';recordedAtUtc=[DateTime]::UtcNow.ToString('o');
        inputManifest=$stem+'.inputs.json';inputFiles=$files.Count;specDocuments=$spec.Count;specVersions=@($spec.version|Sort-Object -Unique);specShaMismatchAgainstSqlserver12=$mismatch;
        tests=@([pscustomobject]@{kind='own Core boundary';command='dotnet run --project tests/Core/StudentManagement.Core.Tests.csproj -c Release --no-restore';exitCode=0;assertions=$core;sqlIntegration=$false},[pscustomobject]@{kind='own HTTP/controller contract';command=('dotnet run --project '+$contractProject+' -c Release --no-restore');exitCode=0;assertions=$contracts;fixture='Existing fake IStudentService in own contract test';sqlIntegration=$false},[pscustomobject]@{kind='new screenshot fixture service';command='dotnet run --project tests/EvidenceHost/EvidenceHost.csproj -c Release --no-restore -- --self-check';exitCode=0;assertions=$fixture;sqlIntegration=$false});
        screenshotFixture=[pscustomobject]@{file=('test-project1/srcs/'+$way+'/tests/EvidenceHost/fixture-data.json');sha256=(Get-FileHash -LiteralPath $fixturePath).Hash.ToLowerInvariant();synthetic=$testData.Synthetic;students=$testData.Students.Count;classes=$testData.Classes.Count;codes=$testData.Codes.Count;studentNumbers=$testData.Students.Draft.StudentNo;studentIds=@($testData.Students.StudentId|ForEach-Object {$_.ToString()});lookupSource='Own independent database/002_seed.sql';persistence='rejected';databaseServiceRemoved=$true};
        host=[pscustomobject]@{url=('https://localhost:'+$port+'/__evidence/login?role=Staff');statusUrl=('https://localhost:'+$port+'/__evidence/status');startup=('dotnet tests/EvidenceHost/bin/Release/net10.0/EvidenceHost.dll --port='+$port+' --minutes=60');lifetimeMinutes=60;stop=('POST https://localhost:'+$port+'/__evidence/stop or Ctrl+C');transport='Existing QA .NET development certificate; not production TLS validation';state='Started for parent screenshot session; runtime log is still live';runtimeLog=('test-project1/test-report/'+$stem+'-host.runtime.log')};
        screenshotOperator='parent Agent only';screenshotDirectory='test-project1/test-evidence/20261012-evidence-01';uiOperationsByThisAgent=0;parentObservations=$observations;
        outputAssemblies=$artifacts;logs=$logs;productionOrSpecEditsByThisTask=0;addedScope='Own tests/EvidenceHost only, plus new reports';sqlConnectionsByThisAgent=0;sqlExecutionsByThisAgent=0;elevationsByThisAgent=0;
        notExecuted=@('Shared SQL Server schema or role/CLR repair','Live SQL Server integration','Production authentication and DB-role authorization','SQL persistence, delete, concurrency and audit rollback','Browser operation and screenshots by this Agent');
        limitations=@('Host uses real production rendering/controllers but a synthetic read-only IStudentService; mock HTTP results are not SQL integration passes','Existing production/source records are preserved; no served Vue bundle regeneration','Shared DB deployment remains stopped for reported role/CLR structural collisions')
    }
    if($way -eq 'Vue_CSharpAPI'){$record['frontendTypecheck']=[pscustomobject]@{command='npm.cmd run typecheck';node='24.16.0';exitCode=0;emitsFiles=$false;bundleRebuilt=$false}}
    $manifest=[ordered]@{id=$stem+'-inputs';recordedAtUtc=$record.recordedAtUtc;root=('test-project1/srcs/'+$way);baselineSpecLock='20261012-sqlserver-12-inputs.json';files=$files;excluded=@('bin','obj','build','frontend/node_modules','spec-eval');evaluativeOraclesRead=$false}
    [IO.File]::WriteAllText((Join-Path $PSScriptRoot ($stem+'.inputs.json')),($manifest|ConvertTo-Json -Depth 6)+"`n",$utf8)
    [IO.File]::WriteAllText((Join-Path $PSScriptRoot ($stem+'.json')),($record|ConvertTo-Json -Depth 8)+"`n",$utf8)
    $lines=[Collections.Generic.List[string]]::new()
    foreach($line in @(('# '+$way+' 新規テストと画面撮影入口'),'',('2026-10-12／projectId=test-project1／build／'+$stem+'。'),'',('今回の新規実行：Core境界 '+$core+'件、実HTTP/Controller契約 '+$contracts+'件、撮影fixture '+$fixture+'件がすべて成功。'),'','契約テストは各方式の既存fake service、撮影ホストは実画面と新しい合成読取fixtureを使用。SQL Server統合や更新業務の合格ではない。','',('入力：独立spec '+$spec.Count+'文書（版'+(($spec.version|Sort-Object -Unique)-join '/')+'）、source/fixtureを含む'+$files.Count+'ファイル。現specのsqlserver-12 lockとのSHA差分0。詳細hashは同名.inputs.json。'),'','テストデータは仮名3学生、明示TEST2026-0001～0003、2テストクラス、当方式seed由来70コード。実在の学生情報を使用していない。既定01/02検索2件、状態全offで3件。大きなIDは9007199254740993～9007199254740995。保存・削除は撮影サービスで拒否し、fixtureを変更しない。','',('撮影入口：'+$record.host.url),'',('起動（方式ルート）：`'+$record.host.startup+'`。最大60分で自動停止。停止は`'+$record.host.stop+'`。当方式tests/EvidenceHost/README.mdも参照。'),'','既存QA開発証明書を使用。状態JSONのHTTPS確認だけcurl -kを使い、実TLSや認証基盤の適合に流用していない。Cookieは撮影ホスト専用。SQLサービスのDI登録は削除している。','',('画面操作・撮影は親Agentがtest-project1/test-evidence/20261012-evidence-01へ出力する。このAgentのUI操作・撮影は0件。'))){$lines.Add($line)}
    if($way -eq 'CSharp_ASPNET'){
        $lines.Add('');$lines.Add('親の実ブラウザー確認：検索2行、BigInt学生の編集、必須入力native bubble。SQL未実施。')
        $lines.Add('');$lines.Add('UI-OBS-MVC-001（軽微）：初期・編集・新規の空validation-summary赤枠/空bulletが恒常表示（親スクショ01/03/06）。本体変更は行わず観察として報告。構造ブロッカーではない。')
        $lines.Add('');$lines.Add('CAPTURE-MVC-005：tab.screenshot(fullPage:false)の空白画像はINVALID_CAPTURE。CUA getScreenshotは正常で撮影方法を切り替えたとの親報告。撮影装置の失敗をアプリ失敗や合格に混ぜない。')
    }else{$lines.Add('');$lines.Add('Vue型検査はNode24.16.0／vue-tsc --noEmitで成功。既存wwwroot配信物を再生成・上書きしていない。')}
    $lines.Add('');$lines.Add('変更は新規tests/EvidenceHostと本回レポートだけ。本体DDL・仕様・runtimeコード・共有DBは変更せず、既存記録を保存する。共有role/SQLCLRの構造衝突が未解消のため、DB導入の停止を維持する。')
    $lines.Add('');$lines.Add('未実施：実SQL統合、実認証基盤/DBロール認可、永続保存/削除、競合・監査取消、当Agentの画面撮影。親の画面証拠と別レポートを合わせて確認する。')
    $lines.Add('');$lines.Add('| 入力/出力 | SHA256 |');$lines.Add('| --- | --- |')
    $lines.Add('| fixture-data.json | '+$record.screenshotFixture.sha256+' |')
    foreach($artifact in $artifacts){$lines.Add('| '+$artifact.file+' | '+$artifact.sha256+' |')}
    $lines.Add('');$lines.Add('JSONは実行コマンド・合成データ・出力assembly・生ログSHAを記録する。runtimeログはホスト稼働中のため最終hashを固定していない。')
    [IO.File]::WriteAllText((Join-Path $PSScriptRoot ($stem+'.md')),($lines -join "`n")+"`n",$utf8)
    [pscustomobject]@{Profile=$way;Core=$core;Contracts=$contracts;Fixture=$fixture;Spec=$spec.Count;SpecVersions=($record.specVersions-join '/');InputFiles=$files.Count;SpecMismatch=$mismatch.Count;Report=$stem+'.md'}|ConvertTo-Json -Compress
}
