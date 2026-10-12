# COBOL 新規試験・画面到達証拠

20261012-evidence-01／2026-10-12／Windows x64。SQL配備・共有DB・実データ・仕様・productionコードは変更していない。今回作ったデータは方式内 tests/20261012-evidence-01/input-fixtures.json の仮名３組と学籍番号だけであり、DBへの投入は０件。

| 検査 | 今回結果 | 根拠 |
| --- | --- | --- |
| 既存の実COBOL/Cホストバイナリー（ABI・和暦・整数・Unicode・HTTP・認証エラー・業務入力検証） | 86/86 PASS | 20261012-build-04-cobol-evidence-01-host-tests.json / .raw.log |
| 仮名・全半角学籍番号・カナ・不正番号の新規入力 | 9/9 PASS | input-fixture-results.json / .raw.log |
| 独立仕様hash・CALL/COPY・SQL契約・ABI・確認・隔離の静的検査 | 12/12 PASS | 20261012-build-04-cobol-evidence-01-static.json / .raw.log |
| GnuCOBOL 3.2.0 の28ソース構文検査 | 28/28 PASS | syntax-results.json / .raw.log |
| production C bridge を Zig 0.14.1 で別objectへコンパイル（Wall/Wextra/Werror） | exit 0、診断０ | bridge-compile-results.json / .raw.log |
| 実CGIをHTTPで実行した401/400 HTMLと実CSS | 3/3 PASS | http-host-v2/http-probe.json、cgi-http-*.json/html/raw.log |

既存バイナリーの source/binary build-evidence 一致を確認してから実行した。再リンクや既存exeの差替えは行っていない。旧ホスト試験スクリプトの出力名・内部 runId が build-04 固定なので、その元記録は改変せずこの新規ディレクトリーに保存した。実行日時、現在のsource/spec hash、新規実行IDは evidence.json に記録し、過去の合格を流用していない。

初回Pythonホストは Windows 標準出力の CRCRLF を解析できずHTTP502にした。本体の raw.log には実際の Status:401 とHTMLが残る。修正したのは tests 配下ホストの区切り解析のみで、HTML本文は CGI が出力したバイト列を保持した。初回失敗証拠を削除せず http-host-v2 に再実行を保存した。

追加の Zig cc -fsyntax-only 呼出しは FileNotFound で失敗した（原因未特定）。その診断も保存した。従来の正式 -c 指定では同じ production C ソースが exit0・診断０で新しい試験objectにコンパイルできた。syntax-results全コマンド31/31成功とは記載しない。

## 実画面と撮影範囲

現在稼働中の撮影用loopbackホストは PID 330936。URLは http://127.0.0.1:49191/student.cgi?action=INITIAL 、不正要求は http://127.0.0.1:49191/student.cgi?role=Administrator 。どちらも既存 production student.cgi.exe を毎要求実行している。静的仕様から作った画面モックではない。撮影担当はrootで、この担当はブラウザー/GUIを操作していない。

GETは上記２要求に限定し REMOTE_USER を空に固定、認証関連値/DSN/秘密鍵をプロセス環境から除去した。STMAIN.cob:33–40 と STAUTH の分岐どおり、認証401／パラメーター400はSTCONNECT前に拒否される。SQL接続・学生/クラス/監査書込みは０。正常の学生検索・登録画面にはDB接続が必要で、共有DB構造が未修正の今は NOT_RUN。401/400撮影を正常CRUD画面の合格証拠として扱わない。

ホストは test-only cgi_host.py。新規報告先へ `python -X utf8 tests/20261012-evidence-01/cgi_host.py --report-dir <新規報告先> --port 0` で再起動できる。cgi-host.json に実際のport/PID/source exe hashを記録する。撮影後はrootが該当PIDのcommand lineを確認して停止する。

## 入力・未実施

現在のspecは全46ファイル、Markdown版8.0が38件／8.1が4件。全ファイル版/hashは evidence.json のinputs。仮classId=1は未保存の入力ヒントで、存在する実クラスを仮定していない。入力fixtureは実データの移行や初期seedと分離する。

正常CRUD、保守、確認、監査取消、競合、確定応答喪失、共有SQL Windows認証接続、正常業務UIは共有DB契約が未修正かつ今回SQL実行禁止のため NOT_RUN。Linux CGIの配備も NOT_RUN。試験用入力検証と静的閉包はこれらの代替合格判定にならない。protected-source-check.json の141対象ファイルは前後同hash。
