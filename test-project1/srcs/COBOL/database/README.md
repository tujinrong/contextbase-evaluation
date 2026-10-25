# SQL ServerとWindows ODBC

対応するCOBOL専用DB仕様とコード定義から `tools/generate_database.mjs` が方式内SQLを生成します。DBへは接続しません。`001_schema.sql`、`002_seed.sql` は新規空DB用で、既存DBの移行/置換スクリプトではありません。業務5表89列＋技術2表、5分類70コード、クラス/学生/ログインは生成しません。既存共有DBへの実行は配備者の確認が必要です。

Windows x64 Microsoft ODBC Driver18の保護されたDSNを用意し、実行するプロセスへ `STUDENT_ODBC_DSN` を渡します。英数字/アンダースコア/ハイフンのDSN名だけを受理します。ブリッジは `DSN=...;Encrypt=Yes;TrustServerCertificate=No;` を使い、サイレント接続します。資格情報/証明書の準備は配備側で行い、ログ/Gitへ書きません。

UIはユーザー指定の認証なしサンプルで、固定sample-user/Administrator。これはDB権限の緩和を意味しません。DB接続主体は業務に必要な最小権限、保守CLIはTx内でstudent_admin所属を要求します。両方の保存監査actorはsample-userです。DB ORIGINAL_LOGIN()はアプリ利用者の入力へ置換しません。

保存と保守はTransaction所有の `test-project1:student-write` 排他ロックを取得します。検索SNAPSHOT、保存READ COMMITTED、楽観版、監査と同時COMMIT、失敗時ROLLBACKを維持します。状態payloadは接続sessionと起動メモリ鍵に束縛され、終了後の再利用はできません。期限削除SQLはdeploy/runtime-state-cleanup.sql。

[windows-auth](windows-auth/README.md) のDB配備補助は配備者向けです。DBのWindows統合認証と、今回対象外のアプリ認証を区別します。DB作成/DDL適用/学生CRUD/暗号化状態表/競合・監査失敗・接続断は今回実行していません。
