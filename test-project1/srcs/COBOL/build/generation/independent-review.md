# COBOL Windows Text 独立レビュー

実行ID `20261025-regenerate`。ソース修正担当とは独立して、凍結済みCOBOL自身仕様と現ソースを読取り確認しました。現在、未解消の重大所見はありません。

共有した5所見は、同一パネルの待機入力消失、Ctrl+Home/Endの消費、F8取消後cursor喪失、不正年度/学年後の候補DB照会、DB障害時のMENU終了阻害です。修正後の分岐を再読し、いずれも解消を確認しました。

現ソースhashに一致する別担当のText 182/182（COBOL制御23＋合成INPUT_RECORDを使うnative159）を照合しました。native単独159は同じ159件の別記録であり、合計へ二重加算しません。このレビュー自身では実行試験をしていません。

固定sample-user/Administratorは利用者指定の認証なしサンプル契約です。実DB、物理キーボード、手動IME/glyph適合、本番受入、正式採点は未実施です。MENUの実exe noDSN起動/終了確認は別担当の最終検査記録へ分離します。

[全source/spec SHA-256・修正所見・証跡照合](independent-review.json)。formalScore=null。
