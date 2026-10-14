# 検索詳細稿round-01の独立source意味照合

対象は旧R1詳細稿SHA `23cdaa90a44f3e55b1bd174d6e9e8762ad083526418d3f08b2932958ba8f6875`、全文954行。固定checklist SHA `40e184c35018ec8efe31915a91c48ab35a4ebb70670e61bc8d35c7d0a4aa4242` で53動作、40項目グループ、11図（10フロー・1FK/JOIN関係図）、画面の状態材料をAIが独立照合した。根拠25組のraw source/indexedのSHAを固定checklistへ再照合した。原仕様・spec-eval・採点・未承認の旧稿は読んでいない。コード、プロンプト、fact、原ソース、checklist、稿は変更していない。

重要な意味指摘は2件。

- **DC-04／同日検索の矛盾**: 項目表168行の入学日終了「両端指定時は開始以下にならないこと」は終了＞開始を要求する。原ソース `Core/SqlServerStudentService.cs:120–122` は開始＞終了だけを拒否するため、同日を許す。稿167・322行、345–346行の両端を含むSQLは正しい。「終了日は開始日以上（同日可）」への局所文言修正が必要。
- **DC-05／結果不明後の検索確認案内不足**: 稿796–803行にUnknown判定、先行catch、非Savedの303なしはあるが、全文に再送・再保存を避け検索で結果を確認する案内がない。原ソース `Core/SqlServerStudentService.cs:319–323` と `Infrastructure/WebPresentation.cs:28–30` に明示されている。検索への復帰境界として案内を補足し、成功・失敗を断定しない。登録token全詳細は検索の責務へ拡張しない。

軽微なDC-06はCookie属性・30分slide、HTTPS redirect、CSPのself/frame-ancestors noneの具体設定不足。193–225行にCSRF・要求サイズ・値数とno-store/nosniff/no-referrer/CSP名はあり、解析時の不足は一部改善している。根拠は `Infrastructure/WebHostSetup.cs:14–15,22–25`。

全53動作の対応は矛盾1、必須欠落2、含まれる32、対象外18。40項目は矛盾1、含まれる15、対象外24。これは責務別の対応分類であり、仕様書得点ではない。検索12条件/11列、6イベント、4結果、文字数単位、候補下書き/適用済み条件、options版省略、Resume補正差、メモリとDB、commit/303/読込版は概ね保持されている。FK図はDDLとJOINを別の線にし、940行で在学・休学のclass必須CHECKを限定している。

初期Viewer静的HTML、非Viewer新規・編集の差分、正常/0件/超過/検証異常の状態材料は本文にある。完成画像の切れ・重なり・可読性は**未レビュー**。親Agentの稿SHA固定render/native確認と別に扱う。

この旧R1は既知の構造不備があり、canonical採用しない。search03最新稿は別SHAで同じ固定checklistへ再照合する。旧稿の確認結果を新稿の合格へ流用しない。

全引用、source行SHA、手動対応は `document-comparison-02.json` に保存。report SHAは `a1936b7d0b86ec6179ddfefe0f89f253310c8b4cb043b7e9ad74b5ea2ce11994`。初回JSONの静的HTML引用行位置を確定前に補正し、判定を変えず `citation-history/` へ元の記録を保護した。
