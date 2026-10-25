# COBOL Windows Text 生成記録

実行ID `20261025-regenerate`。状態 **REGENERATED / Windows認証なしサンプル**。入力は自身specRoot44ファイル＋全体規則16、通常preflight60入力・findings0で凍結。原仕様のWindows/no-auth改訂は担当者が確定し、その後の凍結版だけを実装入力にしました。版/SHAはinputs.jsonと../input-manifest.json、実装対応はspec-source-map.json。

- COBOL-COM-COBOL v8.5
- COBOL-COM-COBOL-WINDOWS v1.0
- COBOL-DET-COBOL-SCR-STU-001 v8.6
- COBOL-DET-COBOL-SCR-STU-002 v8.6

ユーザーのWindows指定と認証なし指定により、Win32 Unicode Console/GnuCOBOL3.2、sample-user/Administratorを採用。端末入力や環境roleを主体にせず、random session/起動memory鍵/idle30分/DB正本/CAS/10分確認を維持します。以前の未選定中断はinterruption.jsonで解消を記録し、実Console適合・実DB未実施とは区別します。

STMAIN/STAUTH/STRENDERをTextへ再生成し、STEVENT/STTEXTREQ/STREFと別envelopeを追加。4検索条件、8論理一覧、取得20/50/100と表示4件、編集全34項目、F4候補6件、F8原raw往復、エラー一覧と専用確認N既定/Y+F5、Enter非保存をCOBOLへ接続しました。Cは汎用native入力/表示と既存Unicode/暗号/ODBC境界だけです。SQL38コマンド、7表・5分類70コード、保存19/18入力・生成照合値/日付/版/監査を維持。DBへ適用していません。

Windows x64 GnuCOBOL3.2構文/C変換＋Zig0.14.1リンクで2exeと各probeをbuild。SearchContext追加のABI境界ずれはpad4を追加し、正式ABI testを変更せず再build/再検査しました。共通境界85/85（旧HTTP decoder11件は互換境界として明記、actualsample session内部35assertを含む）、production COBOLのterminal transport fixture23、native synthetic INPUT_RECORD159でText182/182、静的18/18を今回版で実行。run/input/source/binary/runner SHAを照合、静的検査は実際に読んだSQL/DDL/文書hashも別に照合します。

今回のコマンド: `python -X utf8 tools/input_lock.py lock`、`tools/regenerate.py`、`tools/host_build.py`、`tools/host_tests.py`、`tools/static_check.py`、`tools/test_text.py`、`tools/write_report.py`。COBOL_RUN_IDを同じ実行IDへ設定。コマンド/exit/rawログは../test-results、コンパイル途中・toolchain/cache/旧CGI資源は方式.tmp、最終app/今回検査/generationは固定build、履歴はGitで管理します。2exeのruntime DLLは自動bundleせず、外部Windows runtimeをRun-Sample.ps1 -RuntimeDirectoryで指定します。

旧CGI/HTML専用正式tests/fixturesとtools/test_compact.pyは保持し、旧95PASSを今回Text適合へ流用しません。未実施は実Console glyph/IME/物理キー、実SQL/暗号状態表/同時保存/監査失敗・実時間期限、本番受入・正式採点。認証は意図して対象外。formalScore=null。source.zip/outputs manifestは固定buildへ更新し、Gitで履歴を管理します。

## 最終起動・配布検査

現在の実student-text.exeをhidden Windows Consoleで起動し、DSN未設定のE-COM-004表示、F12で未検索画面へ復帰、F3終了とConsole解放を13/13項目で確認しました。DB起動失敗のため期待終了コードは1です。正常DB接続sessionの終了0・物理キー/IME受入は未実施です。詳細は [windows-startup.json](../test-results/windows-startup.json)。

全7方式のソースZIPは独立展開してメンバーとhashを照合しました。COBOLは原仕様・tests・toolsを含まない107ファイルのZIPからWindowsの本体・保守2exeを再コンパイル/リンクできました。SDK/runtimeは外部依存です。ほか6方式のZIP検査はhash/展開に限ります。配布物のビルドは実DB・手動受入を示しません。
