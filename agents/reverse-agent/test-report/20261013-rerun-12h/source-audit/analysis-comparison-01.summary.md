# 検索AI解析素材の独立照合

固定source checklist SHA `40e184c35018ec8efe31915a91c48ab35a4ebb70670e61bc8d35c7d0a4aa4242` と、指定された基本/詳細analysis-verified JSONのSHAを確認して照合した。基本57・詳細45の全statement、unresolved、coverageNotesを読んだ。本文・旧稿・原仕様・評価期待値・採点情報は読んでいない。コード、プロンプト、元ファクトも編集していない。

主要な検索項目・条件・6イベント・4結果分岐・単位・DB/メモリ・保存確定と検索復帰の境界に重要欠陥なし。全53 source動作を検索文書責務で分類し、40項目グループと6画面/図材料観点を照合した。登録全項目・重複dialog・保存token等は検索文書の対象外とした。対象外は欠落扱いしていない。

|素材|含まれる|矛盾|必須欠落|対象外|
|---|---:|---:|---:|---:|
|検索基本|33|1|1|18|
|検索詳細|34|0|1|18|

軽微な指摘は2点。

- AC-01: 基本F018の「tooManyでは…一覧を表示しない」は、table領域を非表示にする解釈を招く。Search.cshtml:7は状態メッセージを分岐し、:8は11列header/空tbody/pager領域を常時描画する。結果行がなく、件数/検索時刻を表示しないと明確化すれば整合する。詳細F027は空itemsを正しく保持している。
- AC-02: CSRF/本文制限はあるが、WebHostSetup:14のcookie属性/期間、:22のCSP/nosniff/no-referrer、:25のHTTPS redirectは具体素材が未収録。補足のHTTP共通境界として軽微な不足。主要機能の分岐は欠落していない。

`analysis-comparison-01.json` に全動作の責務理由、status、実fact引用、JSON pointer、source行範囲とSHAを保存した。report SHAは `aa8e9946898d805d0f8f2b2244e5b1508e5efdc7196d24ee53de873227c79bee`。`record_analysis_comparison_01.py` はAIの手動対応をJSONへ記録し、実引用・SHA・全ID対応を検証するだけで、業務網羅判定や仕様書採点を自動計算しない。

これは解析素材の検査であり、仕様書得点ではない。本文の表・6下位見出し・フロー/関連図への意味保持、初期/正常/異常/閲覧・編集の材料保持と画像は、生成稿到着後に別稿SHAで検査する。
