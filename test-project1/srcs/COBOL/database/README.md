# SQL Server 2022

入力は方式内 `../spec/DB定義/SQLServer` と `../spec/共通/10_業務コード定義.md`（版8.0）です。`../tools/generate_database.mjs` はローカルSQLを生成し、DBへ接続しません。

```powershell
node tools/generate_database.mjs
```

選択した空の評価用DBへ `001_schema.sql`、`002_seed.sql` の順に適用します。001は新規作成用で、既存DBの移行スクリプトではありません。SQL Server 2022、SC対応照合順序、SNAPSHOT許可を使用します。業務5表89列に確認情報と検索状態の技術2表を加えています。コードは5分類70値、実クラス・学生・ログインは作りません。

上記コマンドはCOBOLディレクトリを作業ディレクトリにします。暗号化接続と証明書検証が必要です。`deploy/odbc.ini.example`を基に保護されたDSNを用意し、`STUDENT_ODBC_DSN`で指定します。秘密情報をソースへ記載しません。

ロール `student_viewer`、`student_staff`、`student_admin` には、ユーザーや権限を自動で割り当てません。配備者が認証と有効権限を設定します。CGIはサーバー認証した信頼サービス主体を使い、CLIは管理者DB主体をTx内で再検査します。最小権限と直接DB資格情報を公開しない配備が必要です。

全業務書込みと保守は `test-project1:student-write` のトランザクション所有排他ロックを取得します。実DBでのDDL適用、競合、監査失敗時の取消、接続断試験は未実施です。
