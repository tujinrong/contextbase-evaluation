# 汎用AI工程の再レビュー

2026-10-13。初回 `generic-workflow-review.md/json` は当時の記録として保存し、本書で修正後の範囲を区別する。原業務ソース・設計本文・評価期待表は読んでいない。実AI呼出し、業務意味採点、全27文書の生成完了確認は行っていない。

| 指摘 | 今回の状態 | 確認した範囲 |
| --- | --- | --- |
| GWF-001 | 修正確認 | CLIのplan/document/reviewへdeadlineを渡す。plan修正文脈とiterate入口も接続。別フェーズai-cli-01の11件mock PASSを参照し、この再レビューの新規実行件数へ加算しない。 |
| GWF-002 | 修正確認 | ReviewStructureConflictは原approvedを変更せず保持する。iterationはapprovalAccepted=falseで構造指摘と前原稿を次AIへ渡す。provider/入力/時間の失敗は継続成功へ丸めない。 |
| GWF-003 | 未解決、独立入口を実装予定 | 現計画にsubject inventoryと文書の対応表がない。新plan_reviewでAIが対象・粒度・欠落を発見する。業務表数は検証していない。 |
| GWF-004 | batchの修正確認 | kind=analysis-reportを既定出版対象から除外し、明示batch指定も拒否する。単独document APIに出力先の役割検証はないため、別report rootへの配線は呼出側の責務として残る。 |
| GWF-005 | 未解決、独立入口を実装予定 | 解析のsourcePathsReadはAI自己申告であり実読取の証明ではない。計画レビューの探索範囲・根拠・不足を保存しても、tool読取の完全性検証とは分ける。 |
| GWF-006 | 未解決、独立入口を実装予定 | promptはhelperの宣言と到達性を区別するが、既存plan/analysis schemaに探索範囲と状態の型付き欄がない。新レビューで確認済み・宣言のみ・含まれる範囲で未検出・不明を分ける。 |
| GWF-007 | 一部修正、独立入口を実装予定 | plan revision_contextは全文をAIへ渡し別jobで改訂できる。独立計画批評・subject対応・split/mergeの継承履歴は既存plan schemaにはない。レビューで対応を保存してもID継承を自動保証するものではない。 |
| GWF-008 | 通常の計画不備経路は修正確認 | bound plan/snapshotをworker起動前に検査。job名はID由来ハッシュ、選択数・全計画数・未選択を区別。future.result自体の想定外例外や終了時snapshot検査例外はsummary外へ伝播するため、全障害の報告保証までは確認していない。 |
| GWF-009 | 修正確認 | source/reference祖先のspec-evalとresolve前リンク/reparseを拒否し、reference内部も検査する。別フェーズai-capsule-entry-01の17件（うち入口8件）を参照し、実junction検証と混同しない。既存live capsuleは変更していない。 |

追加したanalysis-repairは、manifestを業務fact根拠にした応答を捨てず、検査失敗と前応答を新しいAI解析へ渡す。再訂正が不正ならdraftへ進まない。これは根拠位置・basisの契約検査であり、本文の業務意味を機械が補正した結果ではない。

今回のread-onlyレビューには新規テスト実行を含めない。root報告のiteration9/provenance26/CLI11は別実行の主張であり、当報告のPASS件数として流用しない。レビュー対象コードのSHA256は併記JSONへ固定する。構造検査・AI承認・正式評価・実行試験の範囲を区別する方針を維持する。
