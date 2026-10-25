# COBOL Windows Text サンプル

Windows x64／GnuCOBOL 3.2／Win32 Unicode Console／SQL Server・ODBC Driver18。ユーザー指定により認証は行わず、実行側が `sample-user`／`Administrator` を設定します。端末raw・REMOTE_USER・role環境変数は主体にしません。本番認証・認可への適合は対象外です。

## 起動・ビルド

PowerShellでこのディレクトリを開き、`python -X utf8 build.py --sdk <GnuCOBOL-UCRT-SDK> --cc <zig.exe>` を実行します。既存の方式内処理系があれば引数は省略できます。原仕様を含まないsource-only展開でもビルドできます。詳細な引数は `python build.py --help`。Python 3、Windows x64 GnuCOBOL 3.2/Cヘッダー・import libraries、ICU78、OpenSSL3、同bit C処理系が必要です。自動ダウンロード/インストールは行いません。依存版と取得済みパッケージhashは [dependencies.lock.json](dependencies.lock.json)。Linux実行は今回の対応対象に含めません。

最終配布は `build/app/windows/student-text.exe`、`student-maint.exe` とhash付き `runtime.json`。runtime DLLは自動bundleしません（runtimeLibrariesIncluded=false）。Windows x64 GnuCOBOL/ICU/OpenSSL等の互換runtimeを別途用意し、`Run-Sample.ps1 -RuntimeDirectory <runtime DLLディレクトリ>` で当該プロセスのPATHへ設定します。既定値は既存の方式内SDK binです。ODBC Driver18は別途導入済みである必要があります。起動は開発用の保護されたODBC User/System DSNを用意し、プロセスの `STUDENT_ODBC_DSN` にDSN名を設定して `Run-Sample.ps1` または配布ディレクトリの `student-text.exe`。DSN名は英数字/アンダースコア/ハイフンだけを許可します。接続資格情報はログ・Gitへ保存しません。最小27行×132桁の実Consoleが必要です。リダイレクトした標準入力やサイズ不足では起動しません。

共有DBの接続権限・TLS・業務検査・楽観版・監査は維持します。[deploy/README.md](deploy/README.md) と [database/README.md](database/README.md) を参照。DB作成・DDL適用はこの生成/ビルドでは実行しません。

## 操作

検索は学籍番号・氏名・クラスID・在籍区分の4条件、一覧8論理項目、取得頁20/50/100と4件表示窓を分離します。F5検索、F6クリア、F2新規、行番号+Enter編集、F3終了。PgUp/PgDnは表示窓、F7/F10は取得頁、Ctrl+Home/Endは取得先頭/最後。在籍欄だけSpaceでX/空欄を切替えます。

登録は全34項目の意味を維持し27×132へ配置します。F5登録/更新、F6取消、F9再読込、F3検索、F11論理削除。F4候補は6件×2行で全候補を辿れます。F8全文はF2通常/コードポイント表示、F5原rawへ反映、F12完全取消。Enterは検査だけでDB保存しません。LFはコードポイントU+000Aから明示入力します。重複/削除/変更破棄はN既定、明示Y+新しいF5だけ続行、F12取消。確認中の背景操作を拒否します。

起動ごとのsessionと暗号鍵はメモリ内だけに発行し、終了/別プロセスでは復帰しません。実キーだけidle期限を更新し、30分idleで失効します。検索/Editor/確認の正本はDB `t_runtime_state`、検索30分・確認10分・所有者/画面/期待revision付きCASです。

## 再生成・検査

実装入力は対応する `../../spec/COBOL` のみです。入力変更を意味確認してから `python -X utf8 tools/input_lock.py lock`、`python -X utf8 tools/regenerate.py`。後者はロックを照合し、Windows入口・COPY・業務・固定SQL38コマンド・DDLを再生成します。個別emitの途中結果を完成ソースとして扱わないでください。

今回の正式記録は [build/test-results/summary.json](build/test-results/summary.json)、[生成記録](build/generation/generation.md)。共通ABI/Unicode/日付等、production COBOL Text制御のterminal fixture、production Win32エンジンのsynthetic INPUT_RECORDを別に検査します。`tools/host_build.py` → `tools/host_tests.py` → `tools/static_check.py` → `tools/test_text.py` → `tools/write_report.py`。同じ `COBOL_RUN_ID` と入力/ソース/バイナリー/runner hashが一致した結果だけ最終集約へ載せます。

旧HTML/CGI専用 `tools/test_compact.py` と正式tests/fixtureは移行前の検査材料として保持し、Windows Textの合格へ数えません。旧配備資源は方式内 `.tmp/legacy-work/old-cgi-source` へ移動しました。過去の検査結果・途中コンパイル・toolchain/cacheは `.tmp/`、最終app/今回検査/generationは固定 `build/`、履歴はGitで管理します。

実Consoleのglyph/IME/物理キー、実SQL/暗号化状態表統合・競合保存、本番受入・正式採点は未実施です。formalScore=null。
