# 学生検索・登録 focus round 05 独立意味評価

EVALUATOR ONLY — 期待値と行別評価を生成入力へ渡さない。

対象はCSharp_ASPNET詳細画面2冊のみ。生成5.0、原仕様8.0、採点表7.4。同じsource43/reference11のtraining-assisted。
**元281行／316点。観測一致289点、不足20点、矛盾0点、未裁定7点。**
正式完了点・率・95%判定はnull。必要整数点301、保留を分母から外さない。
元分類に基づく重大矛盾0件。

| 対象 | 元行数 | 元満点 | 確認済 | 不足 | 矛盾 | 未裁定 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 学生検索 | 120 | 147 | 140 | 3 | 0 | 4 |
| 学生登録・編集 | 161 | 169 | 149 | 17 | 0 | 3 |

新規255一致・21不足・0矛盾・5保留。
各担当が新稿全文と元行を再読し、最終理由と現版根拠を元の項目・criterion・操作で照合した。親評価者も全281最終理由と元文脈の一覧を再読した。隣接行・旧点・単語・描画合格を意味の証明にしない。
現在の評価/再読記録をexclusive-createで保存し、固定byte snapshotを残した。訂正はexact旧byte・別version・transitionが必要で既存を上書きしない。

機械検査：281元ID/配点と文脈結合、4673根拠範囲、128固定pin=入力88+両候補各20、58現行原入力、起動runtime13のSHA一致。
保存runner・config・許可入力・plan/capsuleを照合。後続driver/provider改修を起動版へ遡及しない。
両MDは公開/凍結/完了draft-result/AI raw本文が一致。実4推論のresult/answer/events/checkpoint/handoffが完了し、freshAnalysisフラグを実施証明にしていない。
4つの実promptに固定全計画のID/pathと安全批評が存在する。実scopeはlegacy-v1 raw-indexed unsealedでsealed v2とは称さない。

[合算JSON](detail-evaluation.json)、[根拠/ハッシュ検査](detail-validation.json)、[検索](search-evaluation.md)、[登録](editor-evaluation.md)。
実アプリ/実DB/ビルド/競合試験、原品質軸全面、他文書/1408点全体は未実施。
