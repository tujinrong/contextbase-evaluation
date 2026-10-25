# Windows DB配備補助（今回未実行）

このディレクトリのPowerShellはDB担当がSQL Server/ODBC DSN/DBロールを確認する補助資源です。今回の生成・ビルドではサーバー導入、DB作成、DDL/seed適用、Windows主体の作成/権限付与を実行しません。計画表示と変更操作の区別は各スクリプトの引数を確認してください。共有DBの選択は方式ルートのdatabase/README.mdと現在の配備指示を正とし、補助スクリプトに残る以前の専用DB名を無条件で適用しません。

DBのWindows統合認証は接続側の保護です。UIは今回ユーザー指定により認証を行わずsample-user/Administrator固定で動きます。REMOTE_USER、ST_LOGIN_SESSION_ID、ST_TRUSTED_ROLEはWindows Text製品の主体に使いません。student-maintはDB側student_adminを保存単位内で確認し、監査actorはsample-userです。

Deploy-Database.ps1/Register-Dsn.ps1/Bind-WindowsPrincipal.ps1/Test-Database.ps1/Test-Odbc.ps1はDB配備者が対象DBと接続主体をレビューしてから使用します。既存DBの削除/上書きや証明書検証の無効化は行いません。

`Test-CobolCgi.ps1` は旧CGI用の正式検査ソースとして保持しています。現Windows Textの検査から選択せず、そのHTTPフォーム判定を端末の合格へ使いません。現製品は `build/app/windows/student-text.exe`、ビルドは `build.py`、今回結果は `build/test-results/summary.json` です。

実DB接続・DB配備・glyph/IME/物理キーは未実施です。本番認証適合と正式採点は対象外/未実施です。
