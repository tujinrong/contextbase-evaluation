<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"AG-SPEC-PROMPT","version":"8.1","path":"agents/spec-agent/PROMPT.md","sheets":[{"heading":"起動指示","kind":"GRID","sheet":"01_起動指示"},{"heading":"実行要求の指定項目","kind":"LIST","sheet":"02_実行要求","key":["項目"]},{"heading":"今回のPilot指定例","kind":"GRID","sheet":"03_Pilot指定例"}]} -->
# spec-agent 実行指示

定義版8.1／2026-10-24。実行要求と併せてCodexへ渡す。

## 起動指示

`agents/spec-agent/AGENT.md`を読み、AG-SPECとして仕様書を作成・改善する。ルートAGENTS.md、全体docs、agentsの役割定義を確認し、次の実行コンテキストを記録してから選択projectの入力を読む。利用者の明示パスを優先し、指定外project・方式・spec-eval・アプリ実装を変更しない。

AIが要求と入力仕様を読み、設計判断と仕様本文を直接執筆する。既存ID・QA・入力を保ち、変更した検索条件を画面・項目・イベント・入出力へ反映する。少数の必要な条件と省スペースの配置を、対象業務の操作に即して説明する。汎用Agentへ業務固有の正解を埋めない。

対象MDを正本として、画面の埋込みHTML・単独HTML・PNGを同じ内容へ同期する。固定した画面サイズで描画し、PNGの目視、切れ・重なり・スクロールを確認して対象版と結果を保存する。機械検査はAIの本文執筆や意味レビューを代替しない。

方式内build/spec-generation/の固定レポートへ今回runId属性と入出力の版・SHA-256、変更根拠、影響範囲、検査結果、QA、未実施を残す。過去のPASSを流用せず、仕様・構造・描画・実装・実機・正式採点を分ける。正式採点をしていなければformalScore=nullを維持する。

## 実行要求の指定項目

| 項目 | 指定内容 |
| --- | --- |
| projectId | 実在する対象project |
| stage | 新規作成、既存改善、レビューの別と今回の要求 |
| methodId | 対象方式。全方式と明示された場合だけ複数を対象にする |
| specRoot | 仕様正本のパス。利用者が指定したパスをそのまま採用 |
| allowedPaths / excludedPaths | 読取り許可、書込み許可、除外。範囲を広げる必要があれば独立して進められる部分を進め、残る影響を記録 |
| runId / reportRoot | 今回の実行識別と固定の最終記録先 |
| targetViewport / states | 確認サイズ・倍率・代表状態。未指定のサイズは契約の既定値、状態は対象の変更から選ぶ |

## 今回のPilot指定例

以下は2026-10-23の利用者要求を再現する指定例であり、他projectへ学生管理の条件を持ち込むテンプレートではない。runIdは今回の識別属性であり、出力先の世代分けに使わない。

```text
projectId: test-project1
stage: 既存改善。小規模の学生管理を前提に検索条件を必要なものへ絞り、検索画面を省スペースで合理的に配置する。主要操作がなるべく1画面に収まる仕様へ改善する。
methodId: CSharp_ASPNET
specRoot: test-project1/srcs/CSharp_ASPNET/spec
readAllowed: ルートAGENTS.md、docs/、agentsの役割定義、上記specRoot内の仕様・既存画面資源・QA
writeAllowed: 上記specRoot、test-project1/srcs/CSharp_ASPNET/build/spec-generation/
excluded: 全spec-eval、別project、他方式、アプリ実装・DB実行資源、buildの配布物と他検査結果（上記spec-generationだけ書込み許可）
runId: <今回の識別>
reportRoot: test-project1/srcs/CSharp_ASPNET/build/spec-generation/
targetViewport: 1366×650 CSS px、100%（768px高ディスプレイのブラウザー本文領域を想定）
additionalViewport: 1280×650 CSS px。狭幅・200%では縦スクロールを許容
states: 変更画面の通常・空結果・入力エラー・長い代表値等。実際に確認した状態を記録する
```

既存検索条件の整理によって基本・詳細・共通仕様へ影響する箇所を同期し、登録・更新項目や権限・DB保存制約と検索条件を混同しない。アプリ実装、実DB操作、正式採点はこのPilotの工程に含めない。
