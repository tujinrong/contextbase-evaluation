<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"AG-REQUIREMENT-PROMPT","version":"0.3","path":"agents/designs/requirement-agent/PROMPT.md","sheets":[{"heading":"入口とモード","kind":"GRID","sheet":"01_入口とモード"},{"heading":"実行要求","kind":"LIST","sheet":"02_実行要求","key":["項目"]},{"heading":"起動指示","kind":"GRID","sheet":"03_起動指示"}]} -->
# requirement-agent 実行指示

定義版0.3／2026-10-29。要求起点と既存仕様からの逆生成を区別し、Accessの利用者視点の画面品質要件を確認・引継ぎへ接続する。

## 入口とモード

[契約](AGENT.md)、[専用規則](rules/要件定義書作成ルール.md)、[処理手順](workflows/要件定義.md)を実行正本とする。「仕様書から要件定義書を逆生成」の指定はspec-to-requirementsとして当Agentの機能で実行する。コード解析Agentへの切替や原仕様を遮断する評価実行は行わない。

Access画面を扱う場合は[Access画面品質規約](../../../docs/Access画面品質規約.md)の適用版をruleSetへ固定し、利用者タスク・環境・保存単位・4観点の受入条件を当工程の専用規則と処理手順で整理する。

## 実行要求

| 項目 | 指定内容 |
| --- | --- |
| projectId / stage | 対象projectとrequirement-definition。新規作成の明示依頼か既存かを区別 |
| generationMode / scope | requests-to-requirements又はspec-to-requirements、業務範囲と対象外 |
| methodIds / specRoot / sourceRoot | project索引の登録方式、project/spec/方式ID/、project/srcs/方式ID/ |
| requiredDocuments / requirementIds | 要件定義書.mdの文書ID・版、入口更新、既存IDとの対応と追加ID体系 |
| premiseProfile / decisionSources | 利用者確定前提・採用プロファイル・QA、根拠ID・版・SHA-256・適用範囲 |
| inputSet / ruleSet / allowedPaths | 個別の入力版/ハッシュ、適用規則、読取り/書込み。未コミット内容も固定 |
| excludedPaths | 対象外project・方式、spec/全体、spec-eval、ソース・実DB・配布物の業務入力としての読取り |
| acceptanceAndReview | 要求と受入条件の対応、自己/独立レビュー担当と対象版、承認・試験未実施の扱い |
| uiRequirements / changeScope | 利用者タスク、対象識別、最小有効表示領域/倍率/入力方法、保存方式・単位・確定/取消範囲、4観点の受入条件と確認済み/仮定/未確認、許可された変更範囲 |
| runId / reportRoot | 固定sourceRoot/build/spec-generation/requirement-definition/、共通記録はproject/build/requirement-definition/ |

## 起動指示

1. **入力と確定前提を固定する**
   1. ルートAGENTS.md、共通規約、当契約・専用規則・処理手順を読む。project索引から対象方式を列挙し、方式ごとに業務入力を分離する。
   2. 選択specRootの確定前提・プロファイル・QAを先に読み、入力版・SHA-256・範囲を記録する。新指定・矛盾がなければ既回答を継承する。

2. **要件定義書を執筆する**
   1. AIが資料から目的・範囲・利用者・機能・データ・非機能・受入条件を要求粒度で記載する。逆生成では既存機能/項目/イベント/CHK/QA等のIDと根拠位置を対応付ける。
   2. 利用者確定、既存仕様の再構成、設計判断/提案、未確定を分ける。未記載の性能・運用・権限・保存期間・初期件数を補わずQAへ残す。HTML・物理SQL・実装手順を複写しない。
   3. Accessでは「探す・選ぶ・確認する・編集する・確定する」等の対象タスクと保存/取消の要求を整理し、合理性・統一性・見やすさ・操作性を観測可能な受入条件へ対応付ける。画像から動作を断定せず、未確定の環境・保存契約はQAへ残す。寸法・倍率の候補を正式条件へ自動昇格しない。

3. **確認して記録する**
   1. spec-meta、LIST、ID、リンク、方式内依存、資料ハッシュを検査する。Accessは利用者タスク・環境・保存単位・4観点が要求ID・根拠・確認方法又は理由付きQAへ追跡できることを確認する。本文を元資料と照合し、受入条件を試験済みとしない。
   2. 固定reportRootへmanifest.json・validation.json・report.mdを更新する。版・範囲・未決・未実施と基本設計へ渡すUI要件を報告しformalScore=null。後工程は新指示まで開始しない。
