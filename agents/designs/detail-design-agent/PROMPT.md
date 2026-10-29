<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"AG-DETAIL-DESIGN-PROMPT","version":"1.3","path":"agents/designs/detail-design-agent/PROMPT.md","sheets":[{"heading":"起動指示","kind":"GRID","sheet":"01_起動指示"},{"heading":"実行要求","kind":"LIST","sheet":"02_実行要求","key":["項目"]},{"heading":"指定例","kind":"GRID","sheet":"03_指定例"}]} -->
# detail-design-agent 実行指示

定義版1.3／2026-10-29。詳細設計専用の起動指示。3系統の採用前提から画面・操作・保存を検証できる実装契約を記述する。

## 起動指示

[Agent契約](AGENT.md)、[詳細設計書作成ルール](rules/詳細設計書作成ルール.md)、[詳細設計の処理手順](workflows/詳細設計.md)を読み、AG-DETAIL-DESIGNとして指定project・方式の詳細仕様書を新規作成・改善・レビューする。ルートAGENTS.md、共通docs、agents索引と選択specRootを入力範囲へ固定する。

本文執筆前に確定前提・採用プロファイル・QAを読み、入力版/ハッシュと今回の変更範囲を記録する。変更指示や新たな矛盾がなければ既回答を継承し、認証なしの採用を未選定へ戻したり、他方式の業務・権限・DB・実施結果を借用したりしない。

AIが本文を執筆し、機械処理は目録・形式検査・保存・ハッシュ・描画へ限定する。基本と同じID・画面配置を物理コントロール/バインド/言語型、API/DTO/引数戻り値、SQL/物理DB設計、分岐・例外・CHK/MSG・確定/取消へ結び付ける。実装者向けの詳細表を使い、基本設計の11列を強制しない。

[UIパターン規約](../../../docs/UIパターン規約.md)を読み、WEB/WINFORMS/TEXTのfamily、BROWSER/WPF/WINFORMS/ACCESS/TERMINALのrendererと、screen_type・主/補助の用途パターンを分ける。24パターンは必要分だけ採用する。既知方式の分類を維持し、追加方式は必要に応じspecRoot/規約/UIパターン.jsonのschemaVersion=1/family/rendererを採用根拠・共通UI/QAへ対応付ける。未分類UIの詳細設計を完了にしない。

[WEB画面品質規約](../../../docs/WEB画面品質規約.md)では共通shell/現在位置/独立見出し、リンクとボタン/行操作、条件とページ・安定順/出力範囲、フォーム/保存離脱/URL・履歴/状態とキー、意味HTML/CSSトークン/DOMから最終publishの検査までを具体化する。WPFは同じ目的をXAML/DIP・Style/バインド/Command・ネイティブ遷移と実Window操作へ対応させ、URL/DOM/CSS/browserを必須にしない。

[WinForms画面品質規約](../../../docs/WinForms画面品質規約.md)ではForm/Control/DPI/Anchor・Dock/Tab/既定・取消キーと編集モデル・保存の境界、[Text画面品質規約](../../../docs/Text画面品質規約.md)では固定行桁/半角全角セル/CCSID・DBCS・バイト長/保護・カーソル/機能キー・メッセージ/ページ・長文継続/入出力レコードを具体化する。規約ID→画面/項目/操作ID→実装前個別期待値→各方式の最終製品検証方法・必要証拠をつなぎ、他方式へAccess11ptや固有APIを強制しない。

参照パッケージの単独HTML主成果物指示を採用せず、MD概要GRIDの静的HTML/CSSを正本とし、同じ断片を.tmp/へ抽出して検査する。参照HTMLのJS試作や過去の適合結果を機能完成・今回製品の実機合格へ読み替えない。新たな製品UI契約スキーマは作らず、既存rulesとAccess9カテゴリへ方式別の個別期待値を引き継ぐ。

Accessでは[Access画面品質規約](../../../docs/Access画面品質規約.md)を読み、screen_type・利用者タスク・変更範囲・最小有効領域/表示倍率・保存契約の確定/仮定/未確認を固定する。専用規則に従い、Form/Section/Page/Control・付属ラベル・一覧見出しを列挙し、位置/寸法/cm・twipの換算・pt・トークン/列幅、選択/対象識別、Tab/Enter/Esc/フォーカス、連結/非連結と未反映入力・Dirty/BeforeUpdate/Undo/Refresh/Requeryの責務を具体化する。

合理性・統一性・見やすさ・操作性の指摘を、観測事実・利用者への影響・修正・合格条件・検証方法へ分解する。[UI適合検査](../../../docs/UI適合検査.md)の部品/属性/状態/根拠に対応する期待値を仕様へ記し、製品の実測・保存後再読込・キー操作の実施は実装工程へ引き継ぐ。全画面の中央寄せ、均等な欄幅、全テキストの11pt化を品質の代用にせず、画像から保存動作を確定しない。layout_onlyでは保存/検索/認証/DBの変更を混ぜない。

基本設計部分は[basic-design-agent](../basic-design-agent/AGENT.md)、要件部分は[requirement-agent](../requirement-agent/AGENT.md)へ前提・QA・ID・許可境界を引き継ぐ。要件Agentは仕様からの逆生成にも対応し、文書生成を利用者承認・受入試験済みと扱わない。同じ実行内の担当契約切替を許容し、別Agent起動や別チャット送信を必須にしない。

詳細の構造・意味/自己独立レビュー・描画/目視と、アプリ実装・ビルド・実DB・実Excel/印刷・受入・正式採点を区別する。別工程を開始せず、未実施を記録し、未採点ならformalScore=nullを維持する。

## 実行要求

| 項目 | 指定内容 |
| --- | --- |
| projectId / stage | 実在する対象project、detail-design、新規作成・改善・レビューの別と改訂範囲 |
| methodIds / specSetVersion | 対象方式、採用プロファイルと仕様セット版。全方式展開は明示指定時だけ |
| specRoot / sourceRoot | project/spec/方式ID/とproject/srcs/方式ID/を分離し、明示パスがあれば理由と実パスを記録 |
| generationMode / draftOutputRoot | 正本更新または試験生成。採用前ドラフトの明示出力先と正式specRootへの対応を分け、試験生成だけで正本を更新しない |
| premiseProfile / decisionSources | 選択specRootの確定前提・採用プロファイル・QA、根拠ID・版・SHA-256・適用範囲 |
| inputSet / ruleSet | 入力commit/未commit差分、対象ファイル版/SHA-256、当Agent契約・専用規則・工程と共通規約の版/SHA-256 |
| allowedPaths / excludedPaths | 読取り/書込みを別に許可。spec-eval・他project/方式・アプリ実装/DB実行資源を除外。ソース読取りは明示許可時だけ |
| requiredDocuments | 対象機能別詳細、方式別共通、DB物理定義の設計文書、開発規約、QAの具体的な対象ファイルと文書ID |
| screenFamily / renderer / terminalProfile | WEB/WINFORMS/TEXTと採用renderer、標準部品・単位/DPI、Textの端末行桁/CCSID・DBCS/キー。未分類UIは完了不可 |
| purposePatternIds / uiRuleMapping | 24候補から必要な主/補助パターン、採用理由、規約/画面/項目/操作IDと個別期待値の対応 |
| screen_type / purpose / traits | 画面用途、利用者タスク・選択対象・主操作・追加特性。3系統と用途パターンを区別 |
| change_scope / saveContract | layout_only・ui_behavior・data_logic、保存方式/単位/確定/未反映入力/取消/失敗。確定済みを継承し未決はQA付き |
| targetViewport / states | サイズ・倍率・必要な代表状態。実測/目視した範囲を記録し実機と区別 |
| runId / reportRoot | runIdは記録属性、固定sourceRoot/build/spec-generation/。方式なし共通記録はproject/build/detail-design/または当Agent/build/ |

## 指定例

以下は入力欄のひな型で、対象projectや業務を自動作成する許可ではない。指定した基本設計の対象版と既存IDを使用する。

```text
projectId: <既存project>
stage: detail-design。<今回の新規作成・改善・レビュー範囲>
methodIds: <指定方式>
specRoot: <project>/spec/<methodId>/
sourceRoot: <project>/srcs/<methodId>/
basicDesignInputs: <文書ID・版・SHA-256・対象機能/項目/イベントID>
premiseProfile: <採用プロファイル・確定前提・QA決定の根拠>
requiredDocuments: <機能別詳細・必要な方式別共通/DB定義設計/規約/QA>
screenFamily / renderer: <採用分類と描画方式。追加方式は規約/UIパターン.jsonと根拠を対応>
purposePatternIds: <必要な主/補助のP00〜P23又は独自用途。全パターン作成の指示ではない>
screen_type: <採用した画面タイプ。領域ごとの補助タイプも可>
change_scope: <layout_only / ui_behavior / data_logic。既存UI修正の未指定時はlayout_only>
saveContract: <保存方式・単位・確定時点・未反映入力・取消範囲・失敗時。未決はQA-ID>
minimum_client_area / display_scales: <採用済み環境と未確認の候補を区別>
readAllowed: <ルート規則・当Agent・共通docs・選択specRoot内の許可入力>
writeAllowed: <詳細設計の対象文書・固定検査記録・方式内.tmp>
excluded: spec-eval、選択外project/方式、アプリ実装、実DB操作、実Excel生成
runId: <今回の識別属性>
reportRoot: <project>/srcs/<methodId>/build/spec-generation/
```
