# 当方式専用 SQL Server 2022

入力は../../../spec/Vue_CSharpAPI/DB定義/SQLServer。生成器とDDLは当方式内だけを使用する。

```powershell
node database/generate.mjs
```

管理者が空の専用DBに001_schema.sql、002_seed.sqlの順で適用する。ALLOW_SNAPSHOT_ISOLATION ON、照合・役割・権限をDDLの手順で設定する。生成器は接続、DB作成、DDL実行を行わない。初期値は5分類70コード、学生0・クラス0。


実機結合試験はtests/SqlServer.IntegrationTests.csproj。明示STUDENT_TEST_DB_CONNECTIONがない場合SKIP。供給する場合は空の専用contextbase_test_* DBを指定し、SQL Server2022、暗号化、証明書検証を満たす。既存DBを置換せず、DB作成・削除を行わない。

2026-10-12の最新Express 17.x・Windows認証への導入要求は [EXPRESS17.md](EXPRESS17.md) と Deploy-Database.ps1 を参照する。7表の既存001/002は維持し、方式専用の役割権限003と読取検証004を追加した。準備時点ではSQL未実行。現行のmajor16・空DB専用結合試験とは検査範囲を分ける。
