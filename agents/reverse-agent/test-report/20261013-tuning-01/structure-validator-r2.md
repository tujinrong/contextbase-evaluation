# 構造validator R2 独立指摘の修正

2026-10-13。親Agentの許可により、独立read-onlyレビュー3指摘を局所修正した。既存45件と追加6件の51件を再実行し、終了値0、全件PASS。[結果JSON](structure-validator-r2-results.json)と[最終生ログ](structure-validator-r2-tests.raw.log)を保存した。以前の45件報告は当時の版の記録として保持し、現行版の検査結果へ流用しない。

追加6件を修正前のコードへ当て、[修正前生ログ](structure-validator-r2-before.raw.log)で2 TypeError、3誤判定を再現した。schema=[]/kind={}の例外、HTMLコメントとCSSコメント・文字列のurl例の誤検出、エスケープ縦棒キーの重複見逃しが失敗した。実style属性の危険URLは修正前後とも拒否できた。修正前ソース・専用45件testsも別名保存し、SHA-256をJSONへ記録した。

修正は、set membershipの前の文字列型確認、実table lexerが生成する表示値によるキー比較、実style要素/属性をtinycss2のURL tokenとして走査する処理である。元MDの行・値・回答本文は書き換えない。元行による矩形検査は維持し、parserの空欄補完や切捨てで不正行を合格にしない。意味や特定業務のkeywordを判定する処理は追加していない。

最終validation.py SHA-256：`4F10BEBBFE116078E6B93C5DF95512B22406B04C0A034CC8A5F559015D7DA7AA`。専用tests：`B7DE10A8C1A9ED1F6670391AA1C9F7C6D74C1B540F8BAB800449E4009D59D9E3`。最終ログ：`623E9092F412EBEC9F92A18E0BD11B028B0D7ABEAC7D6684EDFE6B4A62EE8E7C`。

実行はPython3.11.9、方式内`.tmp/pydeps`、`python -B -m unittest contextbase.tests.test_ai_validation -v`。試行は`.tmp`、今回test-reportへログをバイト不変で複製した。providerの凍結SHA `9FC4FE95CF7FD000EBD1EA7C350489F50F9244A49DF2205BD9DCBB5683F96BDD` は不変を確認した。root所有のworkflow/prompts/capsule、共通docs、業務プログラム、原仕様、評価仕様は変更していない。

51件はsynthetic機械構造の回帰であり、AI意味承認、原本忠実度、参照先・画像実在、Mermaidの意味、実画面、Excel変換の合格ではない。これらの未実施とcaller所有の実行隔離は[元構造報告](structure-validator.md)の限界を継続する。
