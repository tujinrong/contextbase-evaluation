# テキスト承認と範囲外未実施の混在確認

2026-10-13。test-project1 / CSharp_ASPNET / 第4稿。原仕様・spec-eval・評価期待値は未読。原稿、原ソース、既存レビュー、productionを変更していない。AI解析・執筆・描画を起動していない。

実際の検索レビュー `focus-round-04/488af9821732c8f6/independent-review/review-verified.json` は findings=0、approved=false。unresolved は画像未閲覧とMVC/取消/配信の実行未確認だけで、前者は原文照合で重大矛盾を確認しなかったと明記する。後者も現行原稿の静的推論を動作保証へ変更しないという留保で、具体的な本文欠陥を挙げていない。handoffのreviewScopeはtext-source-and-structure、visualFidelityVerified=false、正式採点falseである。この記録からは視覚・実行未実施をテキスト承認に含める範囲混在を確認できる。未知の本文欠陥がないことの全面保証とはしない。

第4稿が実際に使ったprompt.txtは旧規則「疑問が未解決ならunknownを残し、PASSに丸めません」で、テキスト承認対象の明示がない。現在のprompts.py:96-101には次回用のテキスト範囲分離が追加されている。この新規則を稼働済み第4稿へ適用した扱いにしない。

ただし現在workflow.py:497-498はapprovedと非空unresolvedの組合せを無条件に拒否する。次回用promptの「範囲外未実施をunresolvedへ残しつつテキスト承認する」と両立しない。schemaはその組合せを許す。check_scope.pyはこの正確なAST節だけを安全なメモリ入力で実行し、既存不承認は維持、同じ範囲外unknownを残した承認は拒否、空unresolvedの承認は通ることを3ケースで確認した。providerやアプリを実行していない。result.jsonに6入力のSHA、節の行番号、実際の留保、入力不変を保存した。

次回用の修正は、未解決な本文・根拠・構造の疑問と、範囲外の視覚/実行/正式採点の未実施を構造上区別して、前者とmajor/critical・構造不正は引き続き承認阻止すること。後者をテキスト承認の阻止条件へ含めず、handoffのfalse/unknownを維持すること。単にunresolvedの全無視や語彙による自動分類で承認しない。既存REVIEW JSONを承認へ書き換えず、新しいAIの判断を新規jobとして保存する。

本件は工程監査である。第4稿の全画像/原文照合はfocus-review-round-04へ別途保存する。
