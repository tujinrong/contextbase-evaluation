<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"SP2-BASIC-DESIGN-REPORT","version":"1.6","path":"sample-project2/build/basic-design/report.md","sheets":[{"heading":"入力と改訂範囲","kind":"GRID","sheet":"01_入力と改訂範囲"},{"heading":"検査結果","kind":"LIST","sheet":"02_検査結果","key":["方式"]},{"heading":"未実施と引継ぎ","kind":"GRID","sheet":"03_未実施と引継ぎ"}]} -->
# 基本設計 再生成・検査記録

版1.6／2026-10-29／projectId=sample-project2／stage=basic-design／runId=sp2-ui-regenerate-20261029。

## 入力と改訂範囲

利用者の依頼により、Access・CSharp_ASPNETの基本→詳細→実装を順に再生成する。本記録は最初の基本工程だけを対象とする。基本設計Agent1.11・専用規則1.2・工程1.3と方式に該当するUI品質規約を採用した。方式別の入力ID・版・SHA、確定前提、改訂/継承、出力版は各固定manifestに保存した。

5画面・6機能・5表48列、DEMO認証、業務上限、社員・全経歴の原子保存、保存済み1人のExcel出力を継承した。要件本文・既存詳細・物理DB・アプリ・既存fixtureは変更していない。画面と対象の識別、一覧と編集領域、保存/反映/取消、自然なキー順、取消復帰の検索状態を具体化した。設計判断と利用者確定事項をQAで区別する。

## 検査結果

| 方式 | 改訂と検査 | 記録 |
| --- | --- | --- |
| Access | 12改訂・1追加、30対象文書・342リンク、既存83項目/17イベント・5表48列を保持。8静的断片、Mermaid28図。全役割11ptと個別幅、親識別、54条件を引継ぎ。独立指摘とrootの領域見出し指摘を解消 | [結果](../../srcs/Access/build/spec-generation/basic-design/report.md)、[manifest](../../srcs/Access/build/spec-generation/basic-design/manifest.json)、[独立レビュー](../../srcs/Access/build/spec-generation/basic-design/review.json) |
| CSharp_ASPNET | 13改訂、43文書・491リンク、既存83項目/17イベントと重要属性を保持。54図、42静的描画ケース。共通サイト枠、行編集、200件内部スクロールの既存例外、raw/適用済み条件と復帰を具体化。独立指摘5件を解消 | [結果](../../srcs/CSharp_ASPNET/build/spec-generation/basic-design/report.md)、[manifest](../../srcs/CSharp_ASPNET/build/spec-generation/basic-design/manifest.json)、[独立レビュー](../../srcs/CSharp_ASPNET/build/spec-generation/basic-design/review.json) |

## 未実施と引継ぎ

MD概要GRIDの同一断片を描画し、rootはAccess全8断片と改訂したF04/F06、Web通常6画面断片と狭幅2代表を目視した。静的構造、寸法計測、自己/独立意味レビュー、目視の対象を分けて記録した。これらは実Access・最終Web publishの動作や保存の証拠ではない。

次は詳細設計Agentへ方式別handoffと確定前提・QA・ID・版/SHAを渡す。Accessは全Form/Page/Dialogの物理部品・状態・9カテゴリと通常表示/復帰を、WebはURL/DTO/状態保持/共通部品と最終製品の検証を具体化する。Accessの保存後raw条件による再検索とWebの未適用状態での自動検索禁止は、それぞれの採用契約を維持する。

この基本工程では実装・ビルド・DB実行・実キー/IME/DPI・Excel/印刷・仕様Excel/PDF変換・利用者受入・正式採点を行っていない。後続工程の状態は[工程記録](../generation/pipeline.json)で管理する。formalScore=null。今回の固定JSONが対象版を示し、履歴はGitを使用する。
