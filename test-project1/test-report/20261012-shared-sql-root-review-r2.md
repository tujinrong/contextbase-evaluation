# 共有 SQL Server スクリプトの再レビュー R2

レビュー ID: `20261012-shared-sql-root-review-r2`。2026-10-12。対象 project: `test-project1`。AG-BUILD/PROMPTはユーザーのDB共有変更を反映した7.5。題材方式内仕様の変更/アプリ移行はこのレビューに含まれない。

**最新5スクリプトの静的検査と接続しないPlan2種は通過、前回の修正候補は解消、追加指摘なし**。これはSQLインストール、証明書修復、アプリ配備/認可の新たな実行合格ではない。初回報告とR2前の試験記録を上書きしていない。

## 入力と検査結果

| スクリプト | SHA-256 |
| --- | --- |
| `agents/build-agent/scripts/Install-LocalSqlExpress.ps1` | `F6B3CFF9FA403DCF35B7923A28E63D583F851CC615B884E53C42C53228526BCB` |
| `agents/build-agent/scripts/Setup-LocalSqlExpressAndDatabases.ps1` | `46467468F925125ADCE9A67BD7166983C2AAC71D9B72A29B4C4018B2F5F1D4B6` |
| `agents/build-agent/scripts/Start-LocalSqlExpressSetup.ps1` | `63BC5472897D821EC4C8EC1F3414C2479AF85868E085F5CFF108A33713449EAC` |
| `agents/build-agent/scripts/Repair-LocalSqlExpressConnection.ps1` | `4498444A2E4120F30968D9D488FB7B4CFCE88038F9F6D7188BB7D16C3E3325A0` |
| `agents/build-agent/scripts/Create-SharedSqlDatabase.ps1` | `D79248ED74C3B027D0B23820D436BD64806FEF139367EFC6EF58C03F44042AFF` |

| 検査 | 今回の結果 |
| --- | --- |
| Windows PowerShell5.1.26100.9549 ParseFile | 5ファイル、ParseError0 |
| ASTから抽出した定数SQLのTSql170Parser | 13文、ParseError0。SQLを送信していない |
| StartのPlanOnly → Setupの既定Plan | PS5終了0、PLAN_ONLY、共有DB1件、Execute=false |
| Createの既定Plan | PS5終了0、PLAN_ONLY、共有DB名固定、共有契約待ち。ODBC18/HostnameInCertificate=localhostをJSONで確認 |
| 入力hash | 検査前後一致、報告時の現ファイルとも5/5一致 |
| SQL/昇格/インストール/修復/DB作成のレビュー担当による実行 | NOT_RUN |

Planの実行コマンド:

```powershell
& "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -NoLogo -NoProfile -NonInteractive -File agents/build-agent/scripts/Start-LocalSqlExpressSetup.ps1 -RunId 20261012-review-r2-plan-start -PlanOnly
& "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -NoLogo -NoProfile -NonInteractive -File agents/build-agent/scripts/Create-SharedSqlDatabase.ps1 -RunId 20261012-review-r2-plan-create
```

最初のPlanはStartの5行目からSetupをExecuteなしで呼び、Setupの24行目でreturnする。二つ目はCreateの13行目でreturnする。DB接続オブジェクト生成、SQL実行、UAC、インストーラー、証明書/レジストリー/サービス変更に到達しない分岐だけを実行した。対象の実モードや `VerifyOnly` は呼び出していない。

## 修正の確認

初回 `REV-SHARED-SQL-001` の空DB判定は解消。Createの26行目でVerifyOnlyを含めsysadminを要求し、45-51行目でユーザーobjects、独自assembly、独自roleも0と検査する。表だけを0として空DB合格にする旧入力の判定は使用していない。違反オブジェクトを削除する処理は追加されていない。

追加で通知したStart/SetupのRunId上限差も解消。両方が `{0,42}`、先頭1文字込み最大43文字に一致する。Setupが作る `-shared` の7文字を加えてもCreateの最大50文字に収まる。StartはStart-Processの `-ErrorAction Stop` と非null/IDの確認を持ち、UAC取消時に空PIDを成功起動として通知する経路を抑止する。実UAC取消の再現試験は行っていない。

最新CreateはODBC Driver18、`tcp:127.0.0.1,1433`、`HostnameInCertificate=localhost`、Windows認証、Encrypt=Yes、TrustServerCertificate=Noで接続する。接続住所を明示IPにし、旧証明書の期待名をlocalhostへ明示する構成であり、証明書検証を省略する変更ではない。ODBCのConnectionTimeout代入は設定可能なAPIに沿う。[Microsoft: OdbcConnection.ConnectionTimeout](https://learn.microsoft.com/en-us/dotnet/api/system.data.odbc.odbcconnection.connectiontimeout?view=netframework-4.8.1)。

Installの新規インストール用コードとRepairの未実行コードはIP SAN付き証明書と厳格IP接続を準備する。Repairは旧証明書を保持する。今回のCreate成功がRepairの証明書差替成功を意味する扱いはしない。SANの `IPAddress=127.0.0.1&IPAddress=::1` は公式書式である。[Microsoft: New-SelfSignedCertificate, Example 9](https://learn.microsoft.com/en-us/powershell/module/pki/new-selfsignedcertificate?view=windowsserver2025-ps)。

Setupの旧5DBループとCLR/trust登録ループは撤去され、共有空DBだけを作る手順になっている。共有schema、role、正規化、排他は保留のまま。既存SQLインスタンスがある場合、Installは保存して停止するので、既に導入済みの現マシンでSetupを再インストール用に再実行するときの成功を本報告は保証しない。

## rootの実行記録を読取った結果

`test-report/20261012-shared-sql-create-01/shared-database.json` をファイルとして読んだ。レビュー担当はSQLへ再接続していない。同JSONの記録は次のとおり。

| 項目 | root実行記録の値 |
| --- | --- |
| 状態 | INFRASTRUCTURE_PASSED_MIGRATION_BLOCKED |
| 接続 | ODBC18、IP127.0.0.1、期待証明書名localhost、Trust=false |
| サーバ | Express Edition(64-bit)、17.0.5005.3、WindowsOnly1、encrypt_option TRUE |
| 実接続主体 | `MicrosoftAccount\tujinrong@hotmail.com`、sysadmin1。アプリの非管理主体検証ではない |
| 共有DB | contextbase_test_project1、ONLINE、compatibility160、Japanese_XJIS_140_CI_AS、owner=sa |
| ユーザー表/objects/assembly/role | 各0 |
| ユーザーDB一覧 | contextbase_test_project1の1件 |
| アプリ認可 | applicationAuthorizationVerified=false |

サーバのCLR有効値とtrusted_assemblies件数はこのCreate JSONの検査項目にない。本スクリプトがそれらを変更しないことは読取り確認したが、本レビュー単独でCLR0/trust0を実測したという記録にはしない。

rootはRepairのUACが取消され、起動PIDなし・修復未実行と報告している。したがってRepairの証明書差替/再起動/IP名前検証は **NOT_RUN**。今回のODBC Createは既存証明書のlocalhost名検証で成功したrootの別実行であり、IP SAN証明書が現在配備されたとの証拠ではない。

## 新規証拠ファイルと未実施

R2の生記録は同じtest-reportの以下へ新規保存した。

- `20261012-shared-sql-root-review-r2-results.json`
- `20261012-shared-sql-root-review-r2-ps5-parser.raw.json`
- `20261012-shared-sql-root-review-r2-plan-start.raw.json`
- `20261012-shared-sql-root-review-r2-plan-create.raw.json`

このレビューの全モードはSQL非接続。今回の実際のインストール/DB作成結果はrootの実行証拠と区別する。SQLCMD16/ODBC18/System.Dataの全ツールでの修復後接続、証明書差替、non-sysadminアプリ主体、CRUD/競合、CLR/共有schema/API、Access/RPG移行は本レビューで未実施。localhost接続拒否の原因も断定していない。
