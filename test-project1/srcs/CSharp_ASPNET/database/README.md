# 当方式専用 SQL Server 2022

入力は../spec/DB定義/SQLServer。生成器とDDLは当方式内だけを使用する。

```powershell
node database/generate.mjs
```

管理者が空の専用DBに001_schema.sql、002_seed.sqlの順で適用する。ALLOW_SNAPSHOT_ISOLATION ON、照合・役割・権限をDDLの手順で設定する。生成器は接続、DB作成、DDL実行を行わない。初期値は5分類70コード、学生0・クラス0。


実機結合試験はtests/SqlServer.IntegrationTests.csproj。明示STUDENT_TEST_DB_CONNECTIONがない場合SKIP。供給する場合は空の専用contextbase_test_* DBを指定し、SQL Server2022、暗号化、証明書検証を満たす。既存DBを置換せず、DB作成・削除を行わない。
