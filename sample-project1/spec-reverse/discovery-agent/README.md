# discovery-agent 成果案内

**改名前test-project1の実行記録。** project移動後も証拠内のprojectId・絶対パス・hashは原値を保持する。新sample-project1は未解析で、現在の既定成果先は`spec-reverse/CSharp_ASPNET/`。ここに保持する旧成果・targetを新projectへ転用しない。ソースリンクは移動後の参照位置を示し、当時の根拠は記録されたsnapshotとhashで識別する。

2026-10-28。**保存済み7草稿の収束と23組の独立検証は完了。全体目録は範囲境界の根拠不足により未採用。確認入口は [review.md](review.md)。**

123記録と33分類の逐項検査はpass。全体catalogはfail、scopeはunknownで、新規blocking 1件とminor 1件を記録した。最終実行は`needs-investigation`・終了コード2・`published=false`。除外されたspec-evalについて、許可済みプロジェクト設定だけではコンパイル所属と目録への影響を確定できないという判定であり、漏れ機能の存在を確認したものではない。

候補・原草稿を変更せず、再抽出・fresh・後続Agentの起動を行わなかった。二つの後続待問にはreviewerが静的解答を返したが、全体未採用でありR／B層の完了や正式な未知解除ではない。

| 読むもの | 対象版と役割 |
| --- | --- |
| [review.md](review.md) | 今回の全検証結果、阻害根拠、未採用候補123件、版と実測 |
| [contextbase.json](contextbase.json) | 前回fullモードの保持正式成果。今回の候補ではない |
| [result/validation.json](result/validation.json) | 前回正式成果の独立検証。今回の検証として流用しない |
| [facts/facts-review.md](facts/facts-review.md)・[facts/validation.json](facts/validation.json)・[facts/source-facts.json](facts/source-facts.json) | 前回正式成果に付属する索引と検査 |
| [target.json](target.json) | profile・source・request・出力slotの所有保護 |

今回の候補SHA：`0e3ec3755be086e0cada0126aa00e144dbc6bd3f4a87ddf35f7ba21681372ee6`。保持正式成果SHA：`9c1f24b11ba15a7adc80a2497b19d2f989212eab1a613eafb7dbcb53ae0e627d`。今回snapshot：`55541f2412dae92232d1c3b56cad016766704637985151b31be1f738ac981dcf`。

最終の検証続行は65分21.0秒。修復前の試行を含むlauncher合計は101分26.7秒で、修正・試験・互換移行は別。上記は改名前workの記録である。移動後の通常起動は新profileの独立workを使い、旧凍結候補や検証断片を自動移行しない。未採用候補・検証・原応答・試験記録はGit対象外の.tmpに保存し、正式rootへ増やさない。
