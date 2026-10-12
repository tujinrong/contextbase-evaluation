# AI CLI配線の局所修正

2026-10-13。production変更はsrc/contextbase/ai/__main__.pyだけ、新規テストはtest_ai_cli.pyだけである。plan／document／reviewへdeadline、planへrevision_contextを渡し、mode-aware説明へ変更した。iterate入口とmax-rounds（既定3）を追加し、plan／document ID／outputを必須にした。batchの既存配線は維持した。workflow、batch、iteration、promptsは変更していない。

[unittest-r2.raw.log](unittest-r2.raw.log) はmock11件PASS。モデル呼出、原本、業務プログラム、SQL、GUIは実行していない。最初のtest_ai_cli.pyに括弧の不足があり、テスト読込前にSyntaxErrorとなった[初回ログ](unittest.raw.log)を保持して修正した。productionの誤起動や失敗を成功へ補完していない。

テストは各入口のdeadline／修正文脈／timeout／選択／review有無／round数の引渡し、必須引数、不成功の非0終了、主contextbase CLIのAI委譲を検査した。試行は.tmp。迭代のAI意味精度、実deadline到達までの運転、既存liveジョブへの効果は検査していない。既にmoduleがロードされたプロセスの挙動を、新CLIの検査結果へ置き換えない。
