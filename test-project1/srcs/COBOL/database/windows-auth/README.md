# Windows 認証による COBOL 専用 SQL Server Express 導入

2026-10-12。DB は `contextbase_test_project1_cobol` に固定。SQL Server 2025 Express（17.x）を、既存 SQL Server 2022 用業務 DDL の評価先に使うユーザー指示に対応する配備資源です。業務仕様・型・上限は変更しません。スクリプトの既定動作は接続しない計画表示で、実 DB 検証は実行結果を別途保存するまで未実施です。

必要条件は 64-bit Windows PowerShell 5.1、配備管理者の Windows 認証、64-bit Microsoft ODBC Driver 18、接続名と一致する信頼済み SQL Server 証明書です。`Common.ps1` と既存 C ブリッジは暗号化と証明書検証を要求します。DSN の設定を含め、証明書検証を無効化する処理はありません。

COBOL ディレクトリを作業ディレクトリとして、まず計画を表示します。

```powershell
& database/windows-auth/Deploy-Database.ps1 -ServerInstance 'localhost\SQLEXPRESS'
& database/windows-auth/Register-Dsn.ps1 -ServerInstance 'localhost\SQLEXPRESS'
& database/windows-auth/Test-Database.ps1 -ServerInstance 'localhost\SQLEXPRESS'
& database/windows-auth/Test-Odbc.ps1
& database/windows-auth/Test-CobolCgi.ps1
```

SQL Server の導入・証明書・主体準備完了後、配備者が以下を実行します。これらの例は新規専用 DB を作り、DB 内の設定・権限または新しい DSN を作成します。

```powershell
& database/windows-auth/Deploy-Database.ps1 -ServerInstance 'localhost\SQLEXPRESS' -Apply
& database/windows-auth/Test-Database.ps1 -ServerInstance 'localhost\SQLEXPRESS' -RequirePristineSeed -Execute
# 既存の非sysadmin Windowsログインを使う。実際の承認済み主体名に置き換える。
& database/windows-auth/Bind-WindowsPrincipal.ps1 -ServerInstance 'localhost\SQLEXPRESS' -WindowsPrincipal 'MACHINE\CobolApplication' -Profile Administrator -Apply
# User DSN は実プログラムを実行する Windows 主体で作成する。
& database/windows-auth/Register-Dsn.ps1 -ServerInstance 'localhost\SQLEXPRESS' -Apply
& database/windows-auth/Test-Odbc.ps1 -Execute
& database/windows-auth/Test-CobolCgi.ps1 -Execute
```

`Deploy-Database.ps1` は DB が存在すると必ず停止します。削除、移行、既存データの置換、失敗後の自動修復、サーバー設定変更を行いません。新規作成後の失敗は専用 DB を残すため、ログを確認して配備者が次の措置を判断します。`001_schema.sql` の既存 `ALTER DATABASE CURRENT ... ALLOW_SNAPSHOT_ISOLATION ON` は専用 DB 内だけへ適用します。順序は `001_schema.sql`、`002_seed.sql`、`003_permissions.sql`。初期状態は分類5・コード70・クラス0・学生0・監査0です。

Windows サーバーログインはスクリプトで作成しません。`Bind-WindowsPrincipal.ps1` は既存 Windows ログインに専用 DB ユーザーと選択したロールだけを付与します。Viewer → Staff → Administrator の継承で、業務表の物理 DELETE や監査 UPDATE/DELETE は付与しません。CGI の信頼サービス主体には必要なロールを付け、画面利用者は Web サーバーが `REMOTE_USER`、`ST_LOGIN_SESSION_ID`、`ST_TRUSTED_ROLE` を発行します。利用者から直接環境変数や DB 資格情報を渡させません。ローカル smoke の環境主体は試験用であり、Web サーバー認証実装の証拠ではありません。

`student-maint.exe` はトランザクションごとに `IS_ROLEMEMBER('student_admin')=1` を要求します。sysadmin 接続は dbo となり、DB ロール所属を返さないため正常系の保守試験主体に使えません。DB 所有者以外の非sysadmin Windows 主体を使います。承認済み入力ファイルによる保守試験は、初期 DB と区別した fixture データとして記録してください。監査主体は CLI の `ORIGINAL_LOGIN()`（64スカラー以下）、CGI のサーバー認証主体です。

`Test-Odbc.ps1` は同じ DSN、暗号化、Windows Driver Manager で DB 名、Windows 認証、初期コード、DB ロールを読み取ります。`Test-CobolCgi.ps1` はビルド済み本番 `build/app/windows/student.cgi.exe` の全コンパイル入力・バイナリ SHA を照合し、新しい一時セッション・メモリー内乱数鍵で GET INITIAL を実行して、HTTP 200 と検索フォームを検証します。業務サンプルは作りませんが暗号化技術状態を DB に保存します。鍵は報告へ出しません。RunId は結果内のメタデータです。結果は既定 `build/test-results/sql-smoke/` の固定名を最新結果で置換します。

実 exe は `tools/host_build.py` が `-lodbc32` でリンクし、Windows Driver Manager を使用します。ICU/OpenSSL/GnuCOBOL の DLL は方式内 toolchain のプロセス限定 PATH からロードします。Linux CGI 配備、実 Web サーバー／ブラウザー、学生 CRUD、確認、競合、監査失敗、確定後応答喪失はこの smoke だけで合格にしません。

本方式は `sql/` の固定 SQL を `bridge/sql_catalog.h` へ組み込む直接 ODBC 実装であり、保存用 SQL 手続きや SQLCLR は不要です。`t_confirmation` は生成 DDL に存在しますが COBOL は暗号化した `t_runtime_state` を確認／検索状態に使います。別方式の DB／資源を参照しません。

根拠: [SQL Server 2025 Express](https://www.microsoft.com/en-us/download/details.aspx?id=108836)、[ODBC 接続属性](https://learn.microsoft.com/en-us/sql/connect/odbc/dsn-connection-string-attribute?view=sql-server-ver17)、[Driver 18 の暗号化変更](https://learn.microsoft.com/en-us/sql/connect/odbc/major-version-differences?view=sql-server-ver17)、[IS_ROLEMEMBER と dbo](https://learn.microsoft.com/en-us/sql/t-sql/functions/is-rolemember-transact-sql?view=sql-server-ver17)。
