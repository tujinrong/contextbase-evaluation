# AS400_RPG 現行検査結果

Windows Cホスト 57件、製品C状態ゲート 42件、参照等の静的検査 94件、検索・DDS配置 46件、状態・候補・生成器 25件がPASS。全記録のsource hashを現ソースへ照合済みです。

[host](host/rpg-results.json)、[配置](compact/compact-static.json)、[状態](state/state.json)にコマンド・終了値・生ログを保存します。同名結果を最新へ置換し、履歴はGitで管理します。ホスト試験exeは .tmp/host に置きます。

SQLRPGLE／DDS／CLのネイティブコンパイル、バインド、Db2、5250、CCSID往復、保存・競合は未実施。Cホスト検査や静的検査をIBM i合格へ転記しません。formalScore=null。
