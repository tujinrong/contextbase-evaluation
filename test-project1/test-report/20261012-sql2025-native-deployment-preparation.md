# WPF / VB SQL2025導入準備

2026-10-12。導入環境の明示変更はSQL Server 2025 Express17.x・Windows統合認証、対象DBはcontextbase_test_project1_wpfとcontextbase_test_project1_vb。方式内の既存spec8.0/8.1・native資源を読み、各方式database配下へ独立したInstall-ProjectDatabase2025.ps1とSQL2025-DEPLOYMENT.mdを新規保存した。旧成果物・旧試験報告は上書きしていない。

両方式ともPowerShell Parse/Plan/PrepareOnlyを通過し、TSql170Parserによる方式ごと16 SQLファイルが構文エラー0件。新しいR2試験は既存ODBC sqlcmd16.0.1000.6に合わせた-E -N（証明書検証、-C/-F/-Nmなし）を対象とし、現行script SHA256一致を確認した。旧static証拠は保持した。SQL接続・SQL実行・サーバ設定変更は行っていない。

適用順は方式内の001_schema.sql、002_seed.sql、native/000_sqlclr.sql（先頭servertrust batch除外）、010_student_api.sql、020_master_api.sql。DBは新規時だけ作成し、既存DBは拒否、途中失敗したDBも自動削除しない。サーバー設定・exact hash trust登録は管理者の別工程であり、scriptはCLR enabled1/strict1と登録済みhashをread-onlyで前確認する。

| 方式 | 専用DB | SQLCLR SHA512 |
| --- | --- | --- |
| WPF | contextbase_test_project1_wpf | A5889EAA82A078761A59AD48F79472437671FB8AFAECFA2706948AC9DD95915A727F0717500CF01BA0DB4CF5F4EC32C5B5609F4F5D49D739616AE1D73E6D5468 |
| VB | contextbase_test_project1_vb | 80CB01ECF43DADE7644B55FE9583C74ED9F3B369997846401BC1E148A48CC9B780A62D356ECEF8E4B12167494F6BEACB34D868BAF10BE50250810ADED806F433 |

役割はstudent_viewer/student_staff/student_admin。通常主体はSELECTと承認したnative EXEC入口だけを使用する。管理配備はAppWindowsLogin省略も可能。現在ユーザーを指定した初回配備はAllowAdministrativeAppLoginとDatabaseOwnerLogin saを明示し、USERと役割を作ってもsysadminの認可・アプリSQL書込みを検証済みとしない。所有者を別ログインへ分ける操作はsa接続やsa有効化ではない。今回sysadmin降格・Windows管理者グループの追加は実施していない。

管理者Validateは7表・3役割・5手続・コードseed・snapshot・TRUSTWORTHY OFF・exact配備DLL・read-only SQLCLR関数を確認する。将来のValidateAppは実際の非sysadmin・非dbo・非db_ownerのWindows tokenで認証/権限を確認する。現時点で実SQL2025の配備・CLRホスト・認可・アプリCRUD・競合は未実施。既存major16限定・初期emptyDB用ハーネスは配備済みSQL2025 DBへそのまま適用できず、将来の統合試験前条件を新しく準備する必要がある。明示構成変更と実行環境の留保であり、新しい仕様構造問題は確認していない。

- WPF: srcs/CSharp_WPF/database/Install-ProjectDatabase2025.ps1、SQL2025-DEPLOYMENT.md、test-report/20261012-sql2025-r2-setup-static-results.json
- VB: srcs/VB.NET_WinForms/database/Install-ProjectDatabase2025.ps1、SQL2025-DEPLOYMENT.md、test-report/20261012-sql2025-r2-setup-static-results.json

各方式ディレクトリでDeployNewを-Server tcp:localhost,1433 -AppWindowsLogin DELL_DISKTOP1\tujin -AllowAdministrativeAppLogin -DatabaseOwnerLogin sa -RunId <新ID>として管理者実行し、別IDのValidateはAppWindowsLoginを省略する。SqlcmdPathには既存ODBCツールの絶対パスを指定できる。PrepareOnlyを付ければ同じSQLを実行せずレビュー用に保存する。
