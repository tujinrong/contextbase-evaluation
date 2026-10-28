# 当方式専用 SQL Server 2022

入力は../../../spec/CSharp_WPF/DB定義/SQLServer。生成器とDDLは当方式内だけを使用する。

```powershell
node database/generate.mjs
```

管理者が空の専用DBに001_schema.sql、002_seed.sqlの順で適用する。ALLOW_SNAPSHOT_ISOLATION ON、照合・役割・権限をDDLの手順で設定する。生成器は接続、DB作成、DDL実行を行わない。初期値は5分類70コード、学生0・クラス0。

native配下にDB側Raw正規化用SQLCLR、prepare_save/persist_student/delete_student、権限・配備手順を収容する。配備手順は[native](native/README.md)を参照。
実機結合試験はtests/SqlServer.IntegrationTests.csproj。明示STUDENT_TEST_DB_CONNECTIONがない場合SKIP。供給する場合は空の専用contextbase_test_* DBを指定し、SQL Server2022、暗号化、証明書検証を満たす。既存DBを置換せず、DB作成・削除を行わない。
native試験には同じサーバー・DBのSTUDENT_TEST_NATIVE_DB_CONNECTIONも必要。これは既存のアプリ用DBユーザー（dbo/db_owner/sysadmin以外）を指定する。セットアップ用接続が当該fixture内のstudent_adminへ追加して、001/002とnativeの000/010/020を適用する。DBAが別途CLRを有効化し、000に記録された正確なassembly hashを信頼登録済みであることをDDL前に確認する。ハーネスはサーバー設定・信頼登録を変更しない。いずれかの接続がない場合、DBを開く前にSKIPする。
