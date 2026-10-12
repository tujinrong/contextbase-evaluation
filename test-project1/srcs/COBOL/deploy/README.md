# Linux CGI配備

1. Linux x86_64にGnuCOBOL3.2/C11、ICU/OpenSSL/unixODBC開発ファイル、Microsoft ODBC Driver18を準備し取得版・ハッシュを確定します。このホストではLinux実機未実施です。
2. COBOLで `make all` / `make check` を実行し依存・ABIログを保存します。ソース変更時は旧record layoutの保持状態と共有しません。
3. 選択した空のSQLServer2022 DBへ `database/001_schema.sql` → `002_seed.sql` を適用。`odbc.ini.example` を基に保護したDSNを作成します。暗号化・証明書検証はCから明示します。資格情報をCGI入力で受けません。
4. CGI/CLIを静的公開領域から分離。非特権専用主体を使い、`build/runtime/` の書込みをその主体に限定します。描画一時ファイルに学生値を含むため700相当、umask077。正常終了時削除、強制終了残骸は配備者の期限付き清掃で削除します。
5. `deploy/student.cgi` を限定CGI入口、`assets/` を `/student-assets/` へ対応。直接バイナリーや保守CLIを公開しません。要求65536byte、CGI終了タイムアウト、HTTPSをWebサーバーにも設定します。
6. 共通認証済みWebサーバーが認証セッションからREMOTE_USER/ST_LOGIN_SESSION_ID/ST_TRUSTED_ROLEを設定。同名利用者ヘッダーは削除、CookieはSecure/HttpOnly。Viewer/Staff/Administratorはサーバー認可値。状態鍵32byteは秘密管理からSTUDENT_STATE_KEY_HEXに注入します。CSRFはowner/sessionと鍵のHMACで検証します。Cookie認証自体は共通認証サーバーの配備前提です。
7. CGI用サービスDB主体を最小権限に設定し有効権限を確認。CLIは別の管理者DB主体を使い、Tx内でもstudent_adminを検査。DDLはログイン/権限を自動付与しません。
8. 承認クラスをCLIで投入後、検索・新規・更新・確認・取消・削除、権限、期限/旧版/他者/別タブを実DB・ブラウザーで検査。監査失敗、同時定員、重複候補21件以上、COMMIT後切断、再起動復帰を含めます。
9. runtime-state-cleanup.sqlを配備者の定期保守で実行し期限切れ保持情報を消します。業務学生・監査ログは削除しません。

以上の配備・DB・ブラウザー試験は未実施です。Windows実行成功を配備合格へ流用しません。
