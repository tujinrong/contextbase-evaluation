# source-only 投影helper 技術レビュー

対象は `prepare_state_projection.py` SHA `2d3380b3a6e886381ecf8d7826f0b636088f88eb285e1e9468b4245fbd319c11`。原仕様・spec-eval・training-assisted・採点は未読。helper、原稿、原ソースを変更していない。

旧SHAで通過したCSS `image-set()`文字列URLと重複meta refresh属性は、新SHAではともに拒否された。エスケープ、webkit、inline CSS、大小文字属性等を含む20 HTMLケース、3パスケース、5原稿位置ケースが期待通り。source04 runtimeの124ファイルは固定receiptと一致した。新たな重要技術欠陥は見つからなかった。

実行したのはASTで取り出した6関数・クラス定義だけ。トップレベルのAI発注、ソース不変gate等は静的読取りで確認した。provider、ブラウザ、通信、renderer、原App、DB、SQL、配置は未実行。

パス検査は現在の基本05・詳細04を許可し、role外パスを拒否する。見出し・行・SHA照合は架空見出し、誤行、誤SHA、節外範囲を拒否する。一方、位置の実在だけでは意味の一致を証明しない。状態配列のminItems=1は全状態の網羅を証明しない。許可suffixと基本/詳細folder prefixの組み合わせ、基本1件・詳細1件の組を機械的には限定していないが、今回の呼出対象は指定された別種2稿である。

この結果は親Agent管理下でAI投影を発注するための技術検査として扱える。HTMLの完全な非実行性、正本との意味一致、状態網羅、native画像合格、原アプリの動作合格、原評価表の合格は未確認。厳格renderer処理と独立したsource/canonical/画像レビューが必要。

詳細証跡: `state-projection-gate-probe-01.json`（旧不具合）、`state-projection-gate-probe-02.json`（新SHA再検証）、`state-projection-helper-review-01.json`（AI判断）。業務本文・図の独立比較は `document-comparison-03.json` に保存済み。
