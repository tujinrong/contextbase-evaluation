# 共有 SQL Server 修復・空 DB 作成スクリプトの読取りレビュー

レビュー ID: `20261012-shared-sql-root-review`。2026-10-12。対象 project: `test-project1`。対象は `agents/build-agent/scripts/Repair-LocalSqlExpressConnection.ps1` と `Create-SharedSqlDatabase.ps1` の本レビュー時点の内容。仕様・アプリコードは変更していない。レビュー対象スクリプトの実行、SQL接続/実行、証明書作成、サーバ設定変更、昇格は行っていない。

結論は **静的検査で構文エラーなし、修正候補1件**。修復・DB作成の実成功やアプリ認可の合格を示す報告ではない。実RUNの結果はrootの別実行記録による。

## 検査方法と入力

Windows PowerShell `5.1.26100.9549` の `System.Management.Automation.Language.Parser.ParseFile` で2ファイルを解析した。対象コードを呼び出す、dot-sourceする、`Invoke-Expression` で実行する操作はしていない。

各 `$cmd.CommandText` の定数文字列だけをASTから取り出し、`Microsoft.SqlServer.TransactSql.ScriptDom.TSql170Parser` で解析した。SQLをDBへ送信していない。証明書書式とODBC APIはMicrosoft一次資料で補足確認した。

| 読取り入力 | SHA-256 |
| --- | --- |
| `agents/build-agent/scripts/Repair-LocalSqlExpressConnection.ps1` | `4498444A2E4120F30968D9D488FB7B4CFCE88038F9F6D7188BB7D16C3E3325A0` |
| `agents/build-agent/scripts/Create-SharedSqlDatabase.ps1` | `5271491C4ABD2333B6290A01A05D129B955CD9C652579BD680065F850D685FF8` |

| 検査 | 結果 | 限界 |
| --- | --- | --- |
| PowerShell 5.1 AST、2ファイル | 各 ParseError 0 | API、権限、実サーバの状態を評価する実行試験ではない |
| 定数SQL、Repair2件＋Create7件 | 9件 ParseError 0 | 照合順序の実在やSQL動作、認可、証明書、接続の合格ではない |
| 証明書SAN指定 | 公式構文と整合 | 生成された証明書の実バイト/プロバイダー動作は未検査 |
| SQL/サーバ/証明書の実操作 | NOT_RUN | rootの実行記録と区別 |

## 確定した修正候補

`REV-SHARED-SQL-001`、優先度P2。`Create-SharedSqlDatabase.ps1:40-42` は空DBを `SELECT COUNT(*) FROM sys.tables WHERE is_ms_shipped=0` だけで判定する。ユーザーのview/procedure/function等、表以外のオブジェクトがあるDBでも件数0となり、`EMPTY_PENDING_SHARED_DATABASE_CONTRACT` / `INFRASTRUCTURE_PASSED_MIGRATION_BLOCKED` の空DB判定を通る。新規DBがmodelからそれらを継承した場合と、既存DBに対する `-VerifyOnly` の両方が対象になる。

共有契約を配備する前の空DBを保証する目的なら、ユーザーオブジェクト全体と独自アセンブリー等も確認する。メタデータ不可視により件数0が返る主体を許可しないため、この管理配備専用検査では `VerifyOnly` もsysadmin等の十分なメタデータ参照権限を要求する。違反を見つけた場合は報告して停止し、オブジェクトや既存DBを削除しない。

この指摘は新規sysadmin配備で対象DBを削除する問題を見つけたという意味ではなく、空DB合格の範囲を表だけに狭めてしまう判定の修正候補である。本レビュー担当は対象スクリプトを編集していない。

## 読取りで確認した制限と安全性

Repair はレジストリーのSQLEXPRESSが `MSSQL17.SQLEXPRESS` のときに限定し、旧証明書を保持する。変更前の接続はODBC18、Windows認証、暗号化と証明書検証を要求し、証明書名は既存のlocalhostを明示する。version `17.0.5005.3`、Express64bit、WindowsOnlyを確認してから証明書変更へ進む。

新SANはDNSのコンピューター名/localhostとIPの127.0.0.1/::1で、Microsoftの公式例9と同じ `IPAddress=` 書式を使う。秘密鍵はCSP、KeyExchange、RSA2048/SHA256、NonExportableで、公開証明書だけをファイル/LocalMachine Rootへ保存し、秘密鍵ACLへSQLサービスのReadを追加する。書式と静的内容は確認したが、証明書/秘密鍵の作成やACL設定は実行していない。[Microsoft: New-SelfSignedCertificate, Example 9](https://learn.microsoft.com/en-us/powershell/module/pki/new-selfsignedcertificate?view=windowsserver2025-ps)。

証明書バインド/ForceEncryptionとSQLEXPRESS再起動後の接続先は `tcp:127.0.0.1,1433`、`Integrated Security=True;Encrypt=True;TrustServerCertificate=False`、Pooling=False。接続待ちは有限で、version/Express/WindowsOnly/encrypt_optionを再照合する。接続失敗時にTLSや証明書検証を緩和するフォールバックはない。スクリプト内の修復後検査はSystem.Data.SqlClientであり、ODBC18/SQLCMD16の修復後厳格接続が成功したとの判定は含めない。

ODBCの `ConnectionTimeout` はsetterを持つAPIであり、接続前の代入は仕様に沿う。SQLClientの読み取り専用タイムアウトプロパティとの混同による指摘はしていない。[Microsoft: OdbcConnection.ConnectionTimeout](https://learn.microsoft.com/en-us/dotnet/api/system.data.odbc.odbcconnection.connectiontimeout?view=netframework-4.8.1)。

Create のDB名は `contextbase_test_project1` に固定。実行しない既定モードは計画を返す。`Execute`/`VerifyOnly`は同時指定を拒否し、新しいRunIdのディレクトリーを要求する。Windows認証、暗号化、証明書検証、17.0.5005.3/Express/WindowsOnlyを確認し、作成にはsysadminを要求する。既存DBの存在時はCREATEを拒否し、DROP/既存DB上書きや再seedは行わない。作成後はcompatibility160、Japanese_XJIS_140_CI_AS、sa所有、ONLINEを照合する。旧方式別DBが存在する場合も報告して停止し、削除する処理はない。

共有schema/role/SQLCLR正規化/排他の配備は含まれず、アプリWindows主体の認可・CRUD、Access移行、IBM i接続も未実施として明示する。エラーではFAILEDを保存し、作成済みDBを自動削除しない。現在仕様修正を待つ空DBインフラとアプリ移行完了を区別している。

## 未実施とレビューの版境界

本報告の判定は上記SHA-256の2入力に限る。rootが指摘を修正した入力に対して、この解析結果を新たな合格として流用しない。対象変更があれば新しいhashで再読取りが必要。今回は既存レポートを上書きしていない。

実証していない事項: ループバックのTCP接続、証明書名/チェーンの実検証、ODBC18/SQLCMD16の修復後接続、SQLサービス再起動、DB作成/メタデータ、照合順序の利用可否、non-sysadminの個別主体/role/拒否、CLR/共有API配備、全方式CRUD/競合。localhostの接続拒否の原因も本レビューでは断定していない。
