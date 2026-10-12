# COBOL SQL Server Express 導入準備

20261012-build-11-cobol-sql-express-preparation。projectId=test-project1、工程=Windows認証配備準備。専用DB=contextbase_test_project1_cobol。今回の非接続検査は 28/28。実行環境 Windows PowerShell 5.1.26100.9549。現在の入力仕様 42文書と配備資源のSHAは同名JSONへ固定しました。

database/windows-auth に新規導入、DBロール権限、既存Windows主体割当、DSN、読取り検証、本番exe CGI smoke、非接続検査、READMEを準備しました。既存001/002・アプリ・バイナリは変更していません。既存DBの削除/置換/自動修復やサーバーログイン作成はありません。別方式のDB/ソースへの依存はありません。

導入は Deploy-Database.ps1 -ServerInstance 'localhost\SQLEXPRESS' -Apply、初期検証は Test-Database.ps1 -ServerInstance 'localhost\SQLEXPRESS' -RequirePristineSeed -Execute。Windows主体割当/DSN/ODBC/CGI実exeの正確な手順は方式内 database/windows-auth/README.md に記載しました。CGI smokeは技術状態を書き、業務サンプルを作らない範囲です。

COBOLは固定DMLをWindows ODBC32で実行し、保存SQL手続き/SQLCLRを使用しません。ローカル実exeとコンパイル入力のハッシュを照合しましたが、今回その実exeやSQLを実行していません。バイナリの過去合格を新しいDB結合の合格へ流用しません。

rootからUAC昇格取消により再インストール未実施との連絡を受けました。今回の読取り時点では64-bit ODBC Driver18がなく17のみです。暗号化＋証明書検証を固定するため信頼済み証明書も必要です。保守CLIはstudent_admin所属をTx内で要求し、sysadmin/dboでは所属確認を通さないため非sysadminのWindows主体が必要ですが未提供です。

SQL接続/DB作成/DDL/seed/権限/DSN変更/ODBC接続/実CGI/保守CLI正常系/学生CRUD/確認/監査/競合は未実施です。Linux CGIと実Webサーバー/ブラウザーも未実施。これらは運用・試験環境の未提供であり新しい仕様構造問題とは判定しません。