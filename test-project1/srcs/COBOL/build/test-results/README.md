# COBOL 現行検査結果

build成功、host 86/86、追加回帰 95/95、静的検査 12/12。入力・バイナリーhashは現在のソースと照合済みです。

[build](host-build/host-build.json)、[host](host-tests/host-tests.json)、[追加回帰](compact/compact.json)、[静的検査](static/static.json)にコマンド・終了値と生ログを保存します。同名ファイルを最新結果で置換し、過去版はGit履歴で管理します。

Windowsホスト用CGI／保守CLIは[app](../app/windows/runtime.json)へ配置します。Linux CGI、実SQL、暗号化状態表統合、実時間期限、実ブラウザー、正式採点は未実施。候補読込みと確認状態I/Oにはfixtureを用い、訂正後CONFIRMは保存dispatchまでを検査します。formalScore=null。
