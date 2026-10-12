# SQL Server Express 入れ替え・DB作成の準備

2026-10-12、projectId=test-project1。状態は **Windows管理者権限待ち**。昇格要求はOSから「この操作はユーザーによって取り消されました」と返され、管理者プロセスは起動されていない。SQL削除、インストール、証明書・サーバー設定、DB作成、DB結合試験は未実施。[現PCの記録](preparation.json)。

常駐SQL Database Engineの登録・サービスはなし。SQLWriterとLocalDB 2016/2019/2025が残る。旧SQL Server2022の2026-08-19アンインストールログは成功だった。残存DBファイルを削除しない。SQLServerクライアント、SSMS、他アプリのSQLCompact等は今回のDBエンジン入れ替え対象ではない。

配布物はMicrosoft公式SQL Server2025 Express、CU9 17.0.5005.3、ODBC18.7.1.1を取得し、3ファイルともMicrosoft署名Valid。CU9 SHA256は公式KB5122048の値と一致。取得先・SHA256はpreparation.jsonのdownloadsを参照。

## 実行

リポジトリの通常PowerShellから次を実行し、WindowsのUACで「はい」を選ぶ。実行IDは新しい値にする。既存の実行記録・DBを置換しない。

```powershell
& 'D:\開発\contextbase-evaluation\agents\build-agent\scripts\Start-LocalSqlExpressSetup.ps1' -RunId '20261012-sqlserver-execute-01'
```

接続・昇格・変更をしない計画表示は同じコマンドへ `-PlanOnly` を加える。既に管理者PowerShellなら `Setup-LocalSqlExpressAndDatabases.ps1 -RunId '<new-id>' -Execute` を使える。

実行内容はLocalDB3版の登録済みMSIアンインストール、SQLEXPRESS新規導入、CU9、ODBC18、TCPループバック1433、localhostの検証可能なTLS証明書、Windows専用認証、CLR有効化＋strict security維持、WPF/VB独立アセンブリのexact SHA512 trust登録、次の独立DB作成と配備読取検証。手順ごとのログはtest-report/実行IDへ保存する。自動再起動・既存DBのdrop・データ捏造は行わない。途中失敗は保存して停止する。

| 方式 | 独立DB |
| --- | --- |
| CSharp_WPF | contextbase_test_project1_wpf |
| VB.NET_WinForms | contextbase_test_project1_vb |
| CSharp_ASPNET | contextbase_test_project1_mvc |
| Vue_CSharpAPI | contextbase_test_project1_vue |
| COBOL | contextbase_test_project1_cobol |

配備後の接続は `Server=tcp:localhost,1433;Database=<方式DB>;Integrated Security=True;Encrypt=True;TrustServerCertificate=False;`。SSMSではサーバー `localhost,1433`、Windows認証を選ぶ。これは配備成功後の設定予定であり、現在接続可能なDBを示していない。

## 検査範囲

今回の検査は非接続のPowerShell構文・計画・生成SQL構文・資源hash確認だけで、実SQL/DBの合格ではない。[工程制御の5件](root-checks.json)は構文3＋実WindowsPowerShell5.1計画2。Web10件、COBOL28件、WPF/VBは各16 SQLのTSql170構文エラー0。導入前レビューで照合順序を有効な `Japanese_XJIS_140_CI_AS` に訂正した。現在のsqlcmd16.0.1000.6に対応する -E -N と証明書検証を使う。原仕様はSQL2022を基準とする既存8.0/8.1/Access8.2入力335ファイルを凍結。ユーザー指定の最新版Express17は導入構成の明示変更として方式内の導入文書へ記録し、旧ハーネスのmajor16合格へ読み替えない。

導入管理ユーザーをsysadminとして登録する。管理者による配備読取検証は、非sysadminのWindowsアプリ主体での権限試験やアプリCRUD結合の合格を意味しない。別の非sysadminアプリWindows主体は未提供で、認可/保存/競合/監査/commit失敗試験は未実施。Accessは単一accdb、RPGはDb2のためSQLServerへの移植を行わない。

方式別の独立導入資料と新規準備結果:

- [WPF導入](../../srcs/CSharp_WPF/database/SQL2025-DEPLOYMENT.md)、[VB導入](../../srcs/VB.NET_WinForms/database/SQL2025-DEPLOYMENT.md)、[native準備結果](../20261012-sql2025-native-deployment-preparation.md)
- [MVC導入](../../srcs/CSharp_ASPNET/database/EXPRESS17.md)、[Vue導入](../../srcs/Vue_CSharpAPI/database/EXPRESS17.md)、[Web準備結果](../20261012-web-express17-provisioning-preparation.md)
- [COBOL導入](../../srcs/COBOL/database/windows-auth/README.md)、[COBOL準備28件](../20261012-build-11-cobol-sql-express-preparation.md)

Microsoft公式: [Express](https://www.microsoft.com/en-us/download/details.aspx?id=108836)、[CU9](https://www.microsoft.com/en-us/download/details.aspx?id=108788)、[更新履歴](https://learn.microsoft.com/en-us/troubleshoot/sql/releases/sqlserver-2025/build-versions)、[ODBC18](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server?view=sql-server-ver17)。
