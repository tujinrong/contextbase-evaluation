<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"CSHARP-ASPNET-SHARED-DB","version":"1.1","path":"sample-project1/spec/CSharp_ASPNET/DB定義/SQLServer/共有DBプロファイル.md","sheets":[{"heading":"適用","kind":"GRID","sheet":"01_適用"},{"heading":"型と項目の対応","kind":"LIST","sheet":"02_型と項目の対応","key":["項目"]},{"heading":"接続・主体・排他","kind":"GRID","sheet":"03_接続・主体・排他"},{"heading":"配備と検証","kind":"GRID","sheet":"04_配備と検証"}]} -->
# 共有DBプロファイル

版1.1／2026-10-28。利用者の同一DB利用指示を固定する。

## 適用

`CSharp_ASPNET`を`Access-To-CSharp_ASPNET`と同じローカルSQL Server DBで動作させる。接続先は`.\SQLEXPRESS`、DBは`AccessRebuilderTraining_01a17be7`。既存の7表とデータを使用し、再作成・初期化・Native用DDLの適用は行わない。

通常の独立DB契約は`StudentDatabase:Profile=Native`として維持する。明示した`SharedAccess`では本文の既存DB互換契約を優先する。画面項目・検索4条件・一覧7列・登録34項目は維持し、物理型の違いをデータアクセス層で吸収する。他方式ソースへの実行時参照は設けない。

## 型と項目の対応

| 項目 | 共有DBの物理契約 | C#側の対応 |
| --- | --- | --- |
| 学生・クラス等のID、row_version | int | long DTOへ拡張して読み、書込み前にint範囲を検査 |
| コード桁数 | int | 数値変換で取得し、Nativeのsmallint前提を外す |
| 生年月日・適用日等 | nvarchar(10)、yyyy-MM-dd | DateOnlyとの明示変換。空値・NULLを区別し業務検査を維持 |
| 作成・更新日時 | datetime2、UTC | UTCのDateTimeOffsetへ変換し、保存時はUtcDateTime |
| 監査correlation_id | nvarchar(36) | GuidのD形式文字列で読み書き |
| 学籍番号・郵便番号・コード | 文字列 | 先頭ゼロを保持。物理列名は既存DBへ合わせる |
| 確認トークン | Webサーバー内の既存状態ストア | WebTokensを使用し、共有DBにないt_confirmation等へ接続しない |

## 接続・主体・排他

`SharedTrainingSql`は`SharedDatabaseTraining`環境、HTTPS、loopbackに限定する。Windows統合認証、Encrypt=Trueとし、ローカルSQLEXPRESSの開発証明書に限り明示したTrustServerCertificate=Trueを許可する。Nativeの証明書検証条件は維持する。

確認用主体は`verification-admin`。要求ごとに`t_app_role`を参照し、Reader→Viewer、Staff→Staff、Admin→Administratorとする。未登録・未知役割は拒否する。主体・接続先・DBへスコープを固定した暗号化Secure Cookieを使用する。この環境外では確認用Cookieを受け付けない。通常のLocalLoginと評価主体は従来の明示有効化条件に従う。

共有DBのSnapshot設定を変更せず、読取りはSerializableを使用する。保存では両アプリ共通の`t_write_guard`行を同一トランザクションでロックし、重複・定員・版の検査と書込みを直列化する。無変更保存は版・監査・ガードを更新しない。楽観排他と論理削除を維持する。

マスターCLIで共有DBを扱う場合は`STUDENT_DATABASE_PROFILE=SharedAccess`を明示する。実接続のsysadmin/db_owner、またはORIGINAL_LOGINに対応するAdmin権限を検査し、DBロールの新規付与は行わない。

## 配備と検証

Debug/Releaseとも既定は共有DB用で、保存済みの`https`も同じ接続設定を使用する。旧独立DBは`Native`を選び接続・認証を設定する。方式内`StudentManagement.slnx`を開き、`StudentManagement.Web`と`SharedTrainingSql`を選択する。共有DBへ`database/001_schema.sql`、`002_seed.sql`、空DB専用の旧結合試験を実行しない。

共有DB試験は`tests/SharedDatabase`を使用する。新しい合成学籍番号で作成・更新・競合・削除を検証し、作成行は論理削除する。監査行は残す。既存TRN001/TRN002、DB構造、もう一方のアプリソースの変更有無を実行前後に確認する。実行結果は方式内`build/test-results/`、入力・出力manifestは`build/generation/`へ固定保存する。正式採点と外部認証・本番配備は別工程である。
