# COBOL Windows Text サンプル 検査結果

今回の入力・現在のコンパイル対象・実行バイナリー・各runnerのSHAを照合済みです。Windows x64ビルド成功、共通境界 85/85、Text制御 182/182、静的検査 18/18。

[ビルド](host-build/host-build.json)、[共通境界](host-tests/host-tests.json)、[Text](text/text.json)、[静的検査](static/static.json)に今回のコマンド・終了値・生ログを記録します。旧HTTP decoder 11件は互換境界で、端末適合の件数へ読み替えません。旧HTML/CGI専用検査は正式ソースを保持し、今回targetの合格へ数えません。

画面・入力制御はproduction COBOLとsynthetic terminal fixture、Win32エンジンはsynthetic INPUT_RECORDを使用します。実Consoleのglyph/IME/物理キー、実SQL/暗号化状態表/同時保存、本番受入は未実施です。認証はユーザー指定により行わず、sample-user/Administrator固定。formalScore=null。
