# AI本文の機械構造検査

実行ID：20261013-tuning-01-structure-validator／2026-10-13。synthetic単体45件、終了値0、PASS。結果は[JSON](structure-validator-results.json)、[生ログ](structure-validator-tests.raw.log)へ保存した。実LLM・業務原本・原仕様・評価仕様は使用していない。

`validate_document(content, path)` は公開先の相対POSIX MDパスを受け、severity/code/detail/locationを持つfindings配列を返す。severityはERROR。空配列は機械構造の合格だけを表し、AIの意味レビューや原本忠実度の合格とは別判定である。関数は本文を読み取り、書換え・ファイル読取り・外部URLアクセスをしない。

検査は実spec-metaコメントのJSON/必須属性/重複、実h2章と宣言の一対一・順序、章とsheet名の重複・Excel名の基本制約、LISTの単一Markdown表・元行の矩形・ヘッダー・宣言キーの一意・混入、出力/参照パスの保護、画面HTMLの静的性を対象にした。common/DB文書の章名を固定しない。spec-md/1.1のTABLEは宣言したHEADER/LISTを一つのsheetへ対応できる。先頭ゼロは文字列として区別し、同じキーをMarkdown装飾だけで別物にはしない。

肯定例と、欠落・ragged行・列追加・キー重複/空欄・メタJSON異常・重複・不正パス・LISTへの文章/HTML/画像の混入等の負例を確認した。初回41件は2負例が失敗した。Markdown parserがfile/javascript URIを参照として解析する前に除外していたため、検査用parseでは対象URIも解析し、後段で拒否するよう修正した。描画やURLアクセスはしていない。[初回ログ](structure-validator-before.raw.log)を保持し、最終45件へ読み替えない。

実行：Python3.11.9、方式内`.tmp/pydeps`のmarkdown-itを利用し、`python -B -m unittest contextbase.tests.test_ai_validation -v`。一時試行は`.tmp`、生ログは今回test-reportへバイト不変で複製した。user/global Python環境は変更していない。

最終validation.py SHA-256：`30A8B44ED94175D25C7223912415CF919810EE8EE95541ECE96BC949E29FA0FF`。専用test_ai_validation.py：`B064CBB3B391806BAC5E00126A24216BA75F3B61CF7331F339ED29488CFC7F14`。生ログ：`E383A336157CA9179807711D68BDFFC2B8AEC1CC074682E30A12CB40816E8828`。

未実施・限界：本文の責務/状態/条件/データ/例外の意味、source-fidelity、Mermaid構文・意味、画像/参照先/アンカーの実在、画像描画、Excel変換/読戻しは検査していない。GRID内の一般表の業務属性・章の説明充足も判定しない。パス検査は文字列上の保護で、実行時のファイルシステム隔離・symlink境界を保証しない。構造判定で意味レビューの指摘や未解決を相殺しない。

実装の変更範囲は `src/contextbase/ai/validation.py` と専用 `src/contextbase/tests/test_ai_validation.py` の新規追加だけ。provider凍結版、root所有のworkflow/capsule/prompts、既存生成器/検査器、業務プログラム、原仕様は変更していない。構造validatorのworkflowへの接続と実AI原稿の検査は親Agentの結合工程で行う。
