# COBOL独立仕様入力の再固定・再検査

2026-10-12。現行入力は `spec/` の46ファイル（文書42件：8.0が38件、8.1が4件、画像等4件）。入力manifestのSHA256は `7fdcf9357e52297d4f28cc7863ce8d0de3a86763b95f7fdc8c00e8820a439670`。

ホスト境界試験86/86、静的検査12/12を新しい記録IDで再実行し、すべて通過しました。旧検査結果を新入力の合格へ転用していません。

| 検査・固定 | 今回の結果 | 記録 |
| --- | --- | --- |
| 現行入力ロックとビルド対応 | 46ファイル一致、コンパイル入力45件・実行バイナリ6本のSHA256不変 | [20261012-build-04-cobol-isolation-28-input-lock.json](20261012-build-04-cobol-isolation-28-input-lock.json) |
| Windowsホスト境界・入力検証 | 86/86 PASS | [20261012-build-04-cobol-isolation-28-host-tests.json](20261012-build-04-cobol-isolation-28-host-tests.json)、[生ログ](20261012-build-04-cobol-isolation-28-host-tests.raw.log) |
| 入力/CALL/COPY/SQL/ABI/隔離静的検査 | 12/12 PASS | [20261012-build-04-cobol-isolation-29-static.json](20261012-build-04-cobol-isolation-29-static.json)、[生ログ](20261012-build-04-cobol-isolation-29-static.raw.log) |

成功ビルド `20261012-build-04-cobol-24-host-build.json` に記録されたコンパイル入力・バイナリのハッシュが、試験前後で現行ファイルと一致したため、再コンパイルは省略しました。ランタイムソースの全インベントリも旧25試験と一致しています。READMEの入力記述を8.0/8.1セットへ更新しました。

旧入力ロックはバイト一致で [20261012-build-04-cobol-pre-isolation-8.0-input-manifest.json](20261012-build-04-cobol-pre-isolation-8.0-input-manifest.json) に保存しました。旧成果物・試験ログは上書きしていません。

Linuxコンパイル/リンク/CGI、Linux依存lock、実SQLServer DDL/seed/CRUD/保守/有効権限、DBを伴う再起動復帰・競合/定員・監査取消・応答喪失、実ブラウザーUIは未実施です。今回の結果はWindowsホストと静的検査の範囲です。
