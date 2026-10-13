# 第6稿・期限後の既存証跡保存

期限は2026-10-13T03:20:58Z。rootの中断観測は03:21:08Z。本保存は期限前の既存観察と証跡の保存、およびSHA256だけの再検査であり、期限後に画像閲覧・原文読解・レビュー・評価・生成・描画・実停止を開始していない。

実閲覧した新稿PNGは69件。各path/SHA/viewedAt/detailは `final-deadline-persistence-manifest.json` の `viewedImagesBeforeDeadline` と `viewed-batch-01.json`〜`viewed-batch-08.json` に保存。最後の記録時刻は03:20:39Z、全69件を含む期限内 `partial-manifest-03-before-deadline.json` の保存時刻は03:20:40.502192Z。期限後閲覧0件、境界不明0件。期限内partialのSHAは `14c2ad12b1469273012ce9ff3e22526595798c4e64821c251d59e4eda567e895`。

| 新稿 | 図 | layout | 全文tile | 原寸実閲覧合計 | 承認 |
| --- | ---: | ---: | ---: | ---: | --- |
| student-search | 16 | 3 | 11 | 30 | source-only bounded true、独立JSONを維持 |
| student-editor | 22 | 3 | 14 | 39 | null、全量意味照合未完了 |
| 全体 | 38 | 6 | 25 | 69 | null |

検索MDは `4a0fe4056d701e3a51ab58e693212de094f1d781d38a6258bbc332d4e99d07cc`。既存 `student-search-review.json` は限定されたraw source・本文・番号手順・局所図・結果説明と静的投影の承認。`unresolved` はこの独立形式のscope/preserve/unknown注記であり、非空unresolvedの承認を拒否するCLI text REVIEWの未解決質問と同一ではない。CLI guardの変更・適用除外や全体PASSへの合算は行わない。

編集MDは `0c10e37c99ede863745128b4a36977eff3436b3f323d635fcca0f4c36f9fc594`。39PNGはすべて実閲覧したが、全項目の原文→番号手順→局所図→結果説明の意味照合は期限内に完了しなかった。既に観察した範囲に新たな確定欠陥はないが、欠陥不存在・全量合格は認定しない。既存のlate-context、Reset guard、catch順、key NULL、返却値合流、静的DOM等の観察は `student-editor-partial-observations-final.json` に保存し、承認nullを維持した。期限後に判断を補っていない。

現在生成済みPNGの未閲覧は0件。未描画の全mode組合せ、狭幅、実HTTP/binder/MVC/DB/競合/取消/応答配信、全参考設計契約の意味適合、正式採点は未実施・未認定。32原文ファイルの読取範囲は9件のsource-read台帳、参考設計は許可11ファイル中4ファイル・13範囲だけを2件のreference-read台帳に保存。参考設計意図と観測されたsource動作は分けた。検索raw Markdownの範囲読取と全文画像の閲覧、編集全文画像の閲覧は別の証拠であり、全raw Markdown行の独立走査を主張しない。カプセルはlegacy-v1 unsealedで、sealed-v2とは扱わない。

期限後のSHAだけの再検査では、launch26（入力8/runtime13/control5）、source32、capsule43 source＋許可参考11、AIraw/draft/MD/canonical render原本とcopy、69PNG、既存証跡のdriftはすべて0。本文・source・productionは変更なし。原仕様や期待値の本文を読まずに179原本をSHAだけで再検査し、179不変・0変更・0missingを `../focus-protected-check-06-native-final-01.json` に排他保存した。

最終保存SHA:

- `final-deadline-persistence-manifest.json`: `e73f34ee8f9fa1d8ea43b77823f6376d4e4400cc7c9e370251f1766e13b80ca2`
- `student-editor-partial-observations-final.json`: `0d7a0a513c67cf16c78c977b5b1f9a8452adba942e671fd29b00e01739fd972d`
- `../focus-protected-check-06-native-final-01.json`: `adf902ae2fac6c4c7862eafec49ee272ae7535d36665bc72b9ab200259cf1974`

保存工程の失敗も成功へ丸めない。準備helperの初回は排他出力名衝突で最後に失敗し、旧記録を保持して別名でSHA検査を完了した。private partial helperの初回partial02試行はtext-freezeとのglob混在でKeyErrorとなり、対象未作成のままnative-only filterを直して再実行した。期限後のmetadata表示ではnullにGetTypeを呼んだPowerShell診断が出たが、保存済み記録への変更や追加読解はない。最終排他保存scriptはexit0、既存証跡drift0で完了した。過去稿の合格や旧画像は本稿承認へ流用していない。
