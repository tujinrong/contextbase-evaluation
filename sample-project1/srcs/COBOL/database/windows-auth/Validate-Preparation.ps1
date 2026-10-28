[CmdletBinding()]
param([string]$ReportDirectory,
      [ValidatePattern('^[A-Za-z0-9_-]+$')][string]$RunId=('cobol-sql-preparation-'+[DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss')+'-'+[Guid]::NewGuid().ToString('N')))
$ErrorActionPreference='Stop'
$root=(Get-Item -LiteralPath (Join-Path $PSScriptRoot '../..')).FullName
if ([string]::IsNullOrWhiteSpace($ReportDirectory)) {$ReportDirectory=Join-Path $root 'build/test-results/sql-preparation'}
$ReportDirectory=[IO.Path]::GetFullPath($ReportDirectory)
$allowedReportRoots=@((Join-Path $root 'build/test-results'),(Join-Path $root '.tmp'))
if(-not @($allowedReportRoots|Where-Object{$ReportDirectory.StartsWith([IO.Path]::GetFullPath($_)+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)}).Count){throw 'Results must remain in this method build/test-results or .tmp.'}
[void][IO.Directory]::CreateDirectory($ReportDirectory)
$prefix=Join-Path $ReportDirectory 'sql-preparation'
$checks=@();$logs=@();$hashes=@();$specs=@()
foreach($path in Get-ChildItem -LiteralPath $PSScriptRoot -Filter '*.ps1') {
    $tokens=$null;$errors=$null
    [void][Management.Automation.Language.Parser]::ParseFile($path.FullName,[ref]$tokens,[ref]$errors)
    $checks += [pscustomobject]@{id='PARSE_'+$path.Name;passed=@($errors).Count -eq 0;errors=@($errors|ForEach-Object{$_.Message})}
}
$plans=@(
    @('Deploy-Database.ps1',@{ServerInstance='localhost\SQLEXPRESS'}),
    @('Bind-WindowsPrincipal.ps1',@{ServerInstance='localhost\SQLEXPRESS';WindowsPrincipal='MACHINE\CobolApplication';Profile='Administrator'}),
    @('Register-Dsn.ps1',@{ServerInstance='localhost\SQLEXPRESS'}),
    @('Test-Database.ps1',@{ServerInstance='localhost\SQLEXPRESS'}),
    @('Test-Odbc.ps1',@{}),
    @('Test-CobolCgi.ps1',@{})
)
foreach($plan in $plans) {
    $path=Join-Path $PSScriptRoot $plan[0];$arguments=$plan[1]
    try { $output=& $path @arguments | Out-String; $checks += [pscustomobject]@{id='PLAN_'+$plan[0];passed=$output -match 'PLAN_ONLY'}; $logs += 'PLAN '+$path+"`r`n"+$output }
    catch { $checks += [pscustomobject]@{id='PLAN_'+$plan[0];passed=$false};$logs+=$_.Exception.ToString() }
}
$safeFiles=@(Get-ChildItem -LiteralPath $PSScriptRoot -File|Where-Object{$_.Extension -in @('.ps1','.sql')})
foreach($file in $safeFiles) {
    $source=[IO.File]::ReadAllText($file.FullName)
    # Statements, not documentation comments. Verify that neither destructive SQL nor server reconfiguration was introduced.
    $passed=$source -notmatch '(?im)^\s*(DROP\s+(DATABASE|TABLE)|ALTER\s+SERVER|EXEC(?:UTE)?\s+(?:sys\.)?sp_configure|CREATE\s+LOGIN)\b'
    $checks += [pscustomobject]@{id='SAFETY_'+$file.Name;passed=$passed}
}
$oldSchema=Join-Path $root 'database/001_schema.sql'
$checks += [pscustomobject]@{id='DDL_SEVEN_TABLES';passed=([regex]::Matches([IO.File]::ReadAllText($oldSchema),'(?im)^CREATE TABLE dbo\.').Count -eq 7)}
$checks += [pscustomobject]@{id='HOST_WINDOWS_ODBC32';passed=([IO.File]::ReadAllText((Join-Path $root 'tools/host_build.py')) -match "'-lodbc32'")}
$checks += [pscustomobject]@{id='BRIDGE_STRICT_TLS';passed=([IO.File]::ReadAllText((Join-Path $root 'bridge/student_bridge.c')) -match 'Encrypt=Yes;TrustServerCertificate=No;')}
$build=Get-Content -LiteralPath (Join-Path $root '.tmp/host/build-evidence.json') -Raw -Encoding UTF8|ConvertFrom-Json
$compiledMatch=[bool]$build.succeeded
foreach($entry in $build.compiledInputs.PSObject.Properties){if((Get-FileHash -LiteralPath (Join-Path $root $entry.Name) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.Value){$compiledMatch=$false}}
foreach($entry in $build.binaries.PSObject.Properties){if((Get-FileHash -LiteralPath (Join-Path $root ('.tmp/host/'+$entry.Name)) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.Value){$compiledMatch=$false}}
$checks += [pscustomobject]@{id='CURRENT_COMPILED_INPUT_AND_BINARY_HASHES';passed=$compiledMatch}
foreach($file in @(Get-ChildItem -LiteralPath $PSScriptRoot -File)+@(Get-Item -LiteralPath $oldSchema,(Join-Path $root 'database/002_seed.sql'))){$hashes += [pscustomobject]@{path=$file.FullName.Substring($root.Length+1).Replace('\','/');sha256=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash}}
foreach($file in Get-ChildItem -LiteralPath (Join-Path $root '../../spec/COBOL') -Filter '*.md' -Recurse){
    $source=[IO.File]::ReadAllText($file.FullName,[Text.Encoding]::UTF8)
    $version=if($source -match '"version"\s*:\s*"([^"]+)"'){$Matches[1]}else{'not_declared'}
    $specs += [pscustomobject]@{path=('../../spec/COBOL/'+$file.FullName.Substring(([IO.Path]::GetFullPath((Join-Path $root '../../spec/COBOL'))).Length+1).Replace('\','/'));version=$version;sha256=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash}
}
$drivers=@(Get-OdbcDriver -Platform '64-bit' | ForEach-Object {$_.Name})
$failed=@($checks|Where-Object{-not $_.passed})
$record=[ordered]@{runId=$RunId;recordedAt=[DateTime]::UtcNow.ToString('o');projectId='test-project1';profile='COBOL';status=$(if($failed.Count -eq 0){'PREPARATION_CHECKS_PASS_DB_NOT_EXECUTED'}else{'PREPARATION_CHECKS_FAIL'});powerShell=$PSVersionTable.PSVersion.ToString();database='contextbase_test_project1_cobol';checks=$checks;passed=$checks.Count-$failed.Count;total=$checks.Count;sqlExecuted=$false;dsnChanged=$false;serverChanged=$false;files=$hashes;specInputs=$specs;compiledBuildRecord=$build.buildRecord;odbcDrivers64=$drivers;limitations=@('root reported UAC elevation cancelled; reinstall not executed','ODBC Driver18 not present in inspected inventory','trusted server TLS certificate not supplied','non-sysadmin Windows maintenance identity not supplied','database deploy/verification/ODBC/compiled CGI not executed','student/master/confirmation/audit/concurrency and Linux web deployment not executed')}
$encoding=New-Object Text.UTF8Encoding $false
[IO.File]::WriteAllText($prefix+'.json',($record|ConvertTo-Json -Depth 9),$encoding)
[IO.File]::WriteAllText($prefix+'.raw.log',("VALIDATION Windows PowerShell "+$PSVersionTable.PSVersion.ToString()+"`r`n"+($checks|ConvertTo-Json -Depth 5)+"`r`n"+($logs-join"`r`n")+"`r`nODBC INVENTORY`r`n"+($drivers-join"`r`n")),$encoding)
$markdown=@"
# COBOL SQL Server Express 導入準備

$RunId。projectId=test-project1、工程=Windows認証配備準備。専用DB=contextbase_test_project1_cobol。今回の非接続検査は $($checks.Count-$failed.Count)/$($checks.Count)。実行環境 Windows PowerShell $($PSVersionTable.PSVersion)。現在の入力仕様 $($specs.Count)文書と配備資源のSHAは同名JSONへ固定しました。

database/windows-auth に新規導入、DBロール権限、既存Windows主体割当、DSN、読取り検証、本番exe CGI smoke、非接続検査、READMEを準備しました。既存001/002・アプリ・バイナリは変更していません。既存DBの削除/置換/自動修復やサーバーログイン作成はありません。別方式のDB/ソースへの依存はありません。

導入は Deploy-Database.ps1 -ServerInstance 'localhost\SQLEXPRESS' -Apply、初期検証は Test-Database.ps1 -ServerInstance 'localhost\SQLEXPRESS' -RequirePristineSeed -Execute。Windows主体割当/DSN/ODBC/CGI実exeの正確な手順は方式内 database/windows-auth/README.md に記載しました。CGI smokeは技術状態を書き、業務サンプルを作らない範囲です。

COBOLは固定DMLをWindows ODBC32で実行し、保存SQL手続き/SQLCLRを使用しません。ローカル実exeとコンパイル入力のハッシュを照合しましたが、今回その実exeやSQLを実行していません。バイナリの過去合格を新しいDB結合の合格へ流用しません。

rootからUAC昇格取消により再インストール未実施との連絡を受けました。今回の読取り時点では64-bit ODBC Driver18がなく17のみです。暗号化＋証明書検証を固定するため信頼済み証明書も必要です。保守CLIはstudent_admin所属をTx内で要求し、sysadmin/dboでは所属確認を通さないため非sysadminのWindows主体が必要ですが未提供です。

SQL接続/DB作成/DDL/seed/権限/DSN変更/ODBC接続/実CGI/保守CLI正常系/学生CRUD/確認/監査/競合は未実施です。Linux CGIと実Webサーバー/ブラウザーも未実施。これらは運用・試験環境の未提供であり新しい仕様構造問題とは判定しません。
"@
[IO.File]::WriteAllText($prefix+'.md',$markdown,$encoding)
Write-Output "$($record.status) $($record.passed)/$($record.total) $prefix.json"
if($failed.Count -ne 0){throw 'Preparation static/plan checks failed.'}
