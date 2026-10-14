# 検索基本稿round-01の本文・図意味照合

対象は今回指定された基本稿SHA `0ab365e4e26027ed78823df0c5e1c9f6844d65619e4abcdfadf18fd39314fa53`、全637行。固定source checklist SHA `40e184c35018ec8efe31915a91c48ab35a4ebb70670e61bc8d35c7d0a4aa4242` で、全53動作、40項目グループ、9フロー/1ERの意味、画面材料をAIが独立照合した。原仕様・spec-eval・採点・旧稿は読んでいない。コード、プロンプト、元fact、checklist、稿は編集していない。

重要な意味欠陥なし。34動作が責務範囲で含まれる、18動作が登録全仕様等として対象外、1動作がHTTP共通補足不足。検索12条件/11列、6主要イベント、4結果、単位、候補下書き/適用状態、options版省略、Resumeページ補正差、commit/Unknown/303の境界を保持している。

解析AC-01の上限超過時「一覧を表示しない」は稿で解消している。95-96行の静的HTMLに11列header/空tbody/pagerがあり、110行は上限超過時の空tbodyと無効pagerを明示している。

軽微な指摘は3点。

- DC-01: HTTP共通設定不足が継続。WebHostSetup:14/22/25にあるcookie属性と期間、no-store/CSP/nosniff/no-referrer/HTTPS redirectは本文へ具体記載されていない。
- DC-02: 図511行のUnknown判定はAND/OR括弧なしで曖昧。本文522行の式は正確。図だけでも「書込開始済み AND（commit試行済み OR rollback不成功）」と読めるよう明確化が望ましい。
- DC-03: 589行の「学生の所属は任意」は列/FK nullabilityとして正しいが、DDLの01/02はclass必須という限定が省略されている。ER説明に在学/休学は必須、卒業/退学は任意というCHECK条件を添えると、未所属の意味を拡張せずに済む。

初期/正常/0件/上限超過/検証エラー/Viewer差分の画面材料は本文のHTML・状態差分表・一覧定義に残っている。完成画像の切れ・重なり・可読性は未レビューであり、親Agentの稿SHA固定render/native view_image確認に委ねる。

現稿は親Agent既知の構造不備により**採用不可**。意味照合で重要欠陥がないことは、spec-meta・見出し・矩形表・描画の合格へ置換しない。新稿は別SHAで再検査する。

`document-comparison-01.json` に全対応と現稿の実引用・行SHAを保存した。report SHAは `702fb394fdc77014a184e02ba7d4db4dfd393aae3e8b788bbe9b7313a6ad8234`。
