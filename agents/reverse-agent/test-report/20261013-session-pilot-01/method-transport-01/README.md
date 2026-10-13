# 作成方法の修正：中断の記録

2026-10-13。前段のread-only auditで、providerのsubprocess待機中にKeyboardInterruptが発生するとresult.jsonを残さず伝播することを人工再現した。旧状態の証跡は `../focus-method-review-02/reproduction-results.json`。既存の新しいAI原稿を中断して再現したものではない。

変更対象は `src/contextbase/ai/provider.py` と `src/contextbase/tests/test_ai_provider.py` のみ。中断時にはstatus/error_codeをinterrupted、interruption_typeをKeyboardInterruptとし、取得可能な部分eventsとusageをresult.jsonへ記録した後、KeyboardInterruptを呼出元へ伝播する。待機中断のテストではexit_code/answerはNULLであり、既にanswer.txtへ書かれた有効応答も成功回答として受理しない。原answer/events/stderrは改変しない。

複数の報告usageは別々に保持し、総量を推測しない。途中JSON行と既存エラーも元ログを残して検査情報へ記録する。event summaryを読めない場合でも、availability=falseと例外型を記録して中断状態を保持する。子孫process終了、完全なread隔離、未完了応答の意味的完全性を確認済みとは表記しない。

今回のtargeted検査は98件、29.365秒、exit 0。provider 46（新規4件を含む）、provenance 28、resume 24。対象5ファイルの検査前後SHA一致を `tests-before.json` と `tests-after.json` に記録し、raw outputは `tests.raw.log`。終了時刻は2026-10-13 06:54:53 JST。前改訂の273件合格をこの修正の結果へ流用しない。

model/configの上書き、入力アプリ実行、業務文章のPython組立て、業務条件の固定化は追加していない。すべて人工processによる検査で、外部CLI/model起動は0件。業務意味採点と、現在実行中のwriterが新provider版を読込済みであることは未検証。
