# SQL Express再導入・共有空DBの実測結果

2026-10-12／projectId=test-project1／実行版=20261012-sqlserver-12。最終状態 **SQL基盤合格・共有空DB作成済み、アプリ移行は構造契約の修正待ち**。

旧LocalDB2016/2019/2025は登録済みMSIによるアンインストールが各exit0、現在のLocalDBパッケージ数0。SQL Server 2025 Express、CU9、ODBC18の導入も各exit0。実接続でExpress Edition (64-bit)、ProductVersion `17.0.5005.3`、Windows専用認証=1を確認した。ユーザーDBは `contextbase_test_project1` の1個だけ。業務DDL・seed・役割・CLRは未導入。

| 実測項目 | 結果 |
| --- | --- |
| DB名・状態 | contextbase_test_project1／ONLINE |
| TCP | 127.0.0.1:1433、待受は127.0.0.1/::1だけ |
| 認証 | Windows、実SQL主体MicrosoftAccount\\tujinrong@hotmail.com、NTLM、sysadmin=1（配備検証主体） |
| 暗号化 | Encrypt=Yes、TrustServerCertificate=No、HostnameInCertificate=localhost、実encrypt_option=TRUE |
| 処理系 | WindowsPowerShell5.1.26100.9549、ODBC Driver18.7.1.1のx64/x86 |
| DB設定 | compatibility160、Japanese_XJIS_140_CI_AS、owner=sa（SQLログインsaは無効） |
| 空DB | user tables/objects/assemblies/application roles=0 |
| サーバーCLR | clr enabled=0、clr strict security=1、trusted assemblies=0 |
| 証明書 | DNS SAN=DELL_DISKTOP1/localhost、拇印EA75140011543C259D2761C2F89EB779F45BD2EF、有効期限2028-10-12、LocalMachine Root登録済み、ForceEncryption=1 |

接続確認用の資格情報なし設定:

```text
Driver={ODBC Driver 18 for SQL Server};Server=tcp:127.0.0.1,1433;
HostnameInCertificate=localhost;Database=contextbase_test_project1;
Trusted_Connection=Yes;Encrypt=Yes;TrustServerCertificate=No;
```

インストール直後の`tcp:localhost,1433`確認は接続拒否で失敗した。待受とIP指定ODBC接続を実測し、このレポートの成功経路に切り替えた。証明書をIP SANへ差し替える修復のUACは取消、昇格PIDなし、修復スクリプト未実行。IP SANを配備済みとは記録しない。既存証明書のDNS名localhostを期待名として指定して検証したので、証明書信頼の迂回はしていない。localhost文字列がこの環境の各クライアントで失敗する原因は未断定。今後のアプリ接続設定も採用するdriverの期待証明書名指定を含めて検証する。

今回の実機検査は **8/8 PASS**:

| 検査 | x64 | x86 | 証拠 |
| --- | --- | --- | --- |
| Windows認証・厳格TLS・指定共有DBへのTCP接続 | PASS | PASS | [x64.json](x64.json)、[x86.json](x86.json) |
| 空DB、独自assembly/roleなし | PASS | PASS | 同上 |
| 期待証明書名invalid.exampleはSSL Provider/08001で拒否 | PASS | PASS | 同上の負例エラー |
| 現行作成スクリプトは既存DBを変更せずexit1で拒否 | PASS | — | [current-version-guards.json](current-version-guards.json) |
| 現行VerifyOnlyによる読取り再検証 | PASS | — | [Verify02](../20261012-shared-sql-verify-02/shared-database.json) |

接続試験は[実行装置](Invoke-ConnectionProbe.ps1)、[x64生ログ](x64.raw.log)、[x86生ログ](x86.raw.log)。現在の作成/検証スクリプトSHA256は`439E7B31FED8264CA8563924AC2578E78A3717D0D9C7018CA4BD86B7B86D554D`。[実作成記録](../20261012-shared-sql-create-01/shared-database.json)、[現行版の既存DB拒否](../20261012-shared-sql-existing-02/shared-database.json)、[最終実環境](final-inventory.json)を保存した。

初回VerifyOnlyはExpressのAUTO_CLOSE閉DBでcollation_nameがNULLになり失敗した。[失敗記録](../20261012-shared-sql-verify-01/shared-database.json)を保持し、対象DBを開いてからメタデータを読む局所修正後のVerify02で成功した。DB設定・schema・データは変更せず、DB再オープンによるエンジンI/Oは生じ得る。[Microsoft sys.databases](https://learn.microsoft.com/en-us/sql/relational-databases/system-catalog-views/sys-databases-transact-sql?view=sql-server-ver17)にこのNULL条件が明記されている。AUTO_CLOSEは初期値ONのまま。

実コマンド（今回のExecute実行IDは再使用しない）:

```powershell
./agents/build-agent/scripts/Create-SharedSqlDatabase.ps1 -RunId 20261012-shared-sql-create-01 -Execute
./agents/build-agent/scripts/Create-SharedSqlDatabase.ps1 -RunId 20261012-shared-sql-verify-02 -VerifyOnly
```

静的準備検査は[R2 rootレビュー](../20261012-shared-sql-root-review-r2.md)、[現行CreateのR3差分レビュー](../20261012-shared-sql-root-review-r3.md)、[MVC/Vue期待列数訂正20/20](../20261012-web-deployment-column-validation-r3-final.md)。これらと実SQL接続8件は別の検査範囲。最初の導入/接続失敗は[installation.json](../20261012-sqlserver-execute-01/installation/installation.json)のFAILEDのまま保持し、後の成功へ上書きしない。

共有roleのDENY/GRANT競合、同名SQLCLRの異なる実体要求、Access/IBM i接続・認可・排他契約を[中断報告](../../report/20261012-shared-sql-migration-stop.md)へ保存した。現在の5方式基礎DDL/seedは一致するが、構造衝突を推測で解消していない。アプリ認可・共有CRUD・監査・取消・競合・Accessフロントエンド移行・IBM i実機は未実施。配備検証のsysadmin成功をアプリ認可の合格として扱わない。旧ビルド10のアプリ試験を共有DB試験へ流用しない。

リポジトリ変更はagents/build-agentとtest-project1のみ。明示依頼されたSQL/Windows導入設定は実施した。既存DBファイルのfilesystem削除、他project/全体docs/他Agentの変更、spec-evalの読取り/変更は行っていない。
