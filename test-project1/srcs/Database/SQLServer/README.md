# SQL Server 2022

入力はDB定義7.2、共通コード定義7.3です。`generate.mjs` は仕様の表とコード表からローカルSQLを生成します。DBへ接続しません。

```powershell
node test-project1/srcs/Database/SQLServer/generate.mjs
```

選択した空の評価用DBへ `001_schema.sql`、`002_seed.sql` の順に適用します。001は新規作成用で、既存DBの移行スクリプトではありません。SQL Server 2022、SC対応照合順序、SNAPSHOT許可を使用します。業務5表89列に確認情報と検索状態の技術2表を加えています。コードは5分類70値、実クラス・学生・ログインは作りません。

暗号化接続とサーバー証明書検証が必要です。各アプリの `STUDENT_DB_CONNECTION` 等の設定手順を参照してください。秘密情報をソースへ記載しないでください。

ロール `student_viewer`、`student_staff`、`student_admin` には、自動でユーザーや権限を割り当てません。配備者が評価用DBの認証・権限を設定します。Webはサーバー側の信頼された接続、ネイティブは個別DB主体の評価用アダプターです。ネイティブ本番規約のEXEC-only保存入口・サーバー側正規化を含むストアドプロシージャは未実装です。現在の直接DML型アダプターへ本番の強い権限制御があると扱えません。

全業務書込みと保守は `test-project1:student-write` のトランザクション所有排他ロックを取得します。実DBでのDDL適用、競合、監査失敗時の取消、接続断試験は未実施です。
