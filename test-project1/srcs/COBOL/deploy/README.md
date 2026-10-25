# Windowsサンプル配布

ビルド手順は方式READMEのWindows `build.py` を使用します。最終 `build/app/windows/` の2exeを配布し、`runtime.json` のSHAを照合します。runtime DLLは含みません（runtimeLibrariesIncluded=false）。互換するWindows x64 GnuCOBOL 3.2/ICU78/OpenSSL3とその依存DLLを別途用意し、`Run-Sample.ps1 -RuntimeDirectory <runtimeディレクトリ>` から起動してください。スクリプトは当該プロセスだけPATHを追加し、既定は方式内SDK binです。Microsoft ODBC Driver18は別途必要です。

SQL Server 2022／Microsoft ODBC Driver18を用い、開発用DBへの保護されたWindows ODBC DSN名を `STUDENT_ODBC_DSN` としてプロセスへ渡します。TLS証明書検証とDB最小権限を維持し、接続文字列はGit/画面ログへ出力しません。DB作成/初期化/権限付与は自動実行しません。方式のdatabase配下の生成SQLをDB担当が確認して適用します。正式fixturesを配備初期DBへ混ぜません。

アプリは認証なしのサンプルです。固定sample-user/Administratorであり、本番認証・利用者別認可に適合するという意味ではありません。DB接続権限と管理者CLIのDB role確認は維持します。

実Console27行×132桁を確保してください。終了・切断・別起動でsessionとメモリ暗号鍵が失効し、以前の画面/確認は再利用できません。DB t_runtime_stateの期限切れ削除は保持した [runtime-state-cleanup.sql](runtime-state-cleanup.sql) を運用側で適用します。Linux/CGI配備は今回のtargetに含めません。

実DB、実glyph/IME/物理キー、本番受入は未実施です。
