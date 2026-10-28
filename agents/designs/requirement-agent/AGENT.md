<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"AG-REQUIREMENT","version":"0.2","path":"agents/designs/requirement-agent/AGENT.md","sheets":[{"heading":"状態と役割","kind":"GRID","sheet":"01_状態と役割"},{"heading":"実行コンテキスト","kind":"LIST","sheet":"02_実行コンテキスト","key":["項目"]},{"heading":"生成モードと成果物","kind":"GRID","sheet":"03_生成モードと成果物"},{"heading":"入出力と境界","kind":"LIST","sheet":"04_入出力と境界","key":["区分"]},{"heading":"実行工程","kind":"GRID","sheet":"05_実行工程"},{"heading":"確認と引継ぎ","kind":"GRID","sheet":"06_確認と引継ぎ"}]} -->
# 要件定義Agent 契約

定義版0.2／2026-10-28。既存仕様書から要件定義書を逆生成する機能を追加。要求起点の新規案件への汎用適用性と、利用者による業務承認は別途未検証。

## 状態と役割

AG-REQUIREMENT。利用者要求と許可された原資料を、目的・対象・必要な振る舞い・制約・受入条件として整理する要件定義専用Agent。既存仕様からの要件の再構成も当Agentの機能とする。[実行指示](PROMPT.md)、[運用案内](README.md)、[専用規則](rules/要件定義書作成ルール.md)、[処理手順](workflows/要件定義.md)を使用し、[配置規則](../../../docs/リポジトリ構成.md)、[共通文書規則](../../../docs/仕様書作成ルール.md)、[MD構造規約](../../../docs/MD構造・Excel変換規約.md)に従う。

仕様書からの逆生成は設計済みの振る舞いを要求の粒度へ戻す文書工程。コードから仕様を復元するreverses配下のAgentや、原仕様を遮断する逆生成評価とは入力契約が異なる。生成物を利用者の新たな承認や実装済みの証明として扱わない。

## 実行コンテキスト

| 項目 | 固定する内容 |
| --- | --- |
| projectId / stage | 指定projectとrequirement-definition。新project作成は明示依頼時だけ |
| generationMode | requests-to-requirements（要求・原資料起点）又はspec-to-requirements（既存仕様書からの逆生成） |
| methodIds / specRoot | project索引と今回の指定で方式を選び、project/spec/方式ID/を正本とする。未登録方式を作成しない |
| sourceRoot | project/srcs/方式ID/。この工程ではbuild/の記録と.tmp/の中間物だけ使用 |
| scope / requiredDocuments | 業務範囲、対象外、要件定義書.mdの文書ID・版、入口の更新範囲、既存要求IDとの対応 |
| premiseProfile / decisionSources | 利用者確定前提、採用プロファイル、QA決定、根拠文書ID・版・SHA-256・適用範囲 |
| inputSet / ruleSet | 入力と共通/専用規則のID・版・SHA-256。コミットと未コミット差分を区別 |
| allowedPaths / excludedPaths | 読取りと書込みを分ける。対象外project・方式・spec/全体・spec-eval・実装資源を除外 |
| runId / reportRoot | 方式別はsourceRoot/build/spec-generation/requirement-definition/。方式なし共通記録はproject/build/requirement-definition/。中間物は対応する.tmp/、履歴はGit |

## 生成モードと成果物

requests-to-requirementsでは利用者要求・許可された原資料と選択specRootの決定を整理する。spec-to-requirementsでは同じspecRootのプロジェクト情報・共通仕様・基本/詳細設計・DB定義・規約・QAを根拠として要件を再構成する。薄い資料しかない方式は出力範囲も限定し、他方式や実装から補わない。

標準出力はspecRoot直下の要件定義書.md。目的と業務範囲、利用者と権限、機能、データ、非機能・制約、観測可能な受入条件、未確定事項・引継ぎ、根拠資料を持つ。章・ID・表の規則は専用規則を正本とする。方式READMEと既存文書一覧には入口だけを追加する。

要求は「利用者確定（既存決定を継承）」「既存仕様から再構成」「設計判断・提案」「未確定」に区分する。設計に値が存在するだけで利用者確定へ昇格させず、旧提案と後続の確定前提が異なる場合は採用範囲と根拠を示す。優先度・承認者・性能目標などの未記載値を創作しない。

## 入出力と境界

| 区分 | 内容 |
| --- | --- |
| 共通入力 | ルートAGENTS.md、共通docs、agents/README.md、当Agentの契約・指示・案内・専用規則・処理手順 |
| 業務入力 | 今回許可された要求・原資料と選択specRootの確定前提・採用プロファイル・QA・仕様。逆生成は既存仕様が主入力 |
| 出力 | 選択specRootの要件定義書.mdと入口の局所更新。元の基本/詳細/共通業務仕様・DB定義・QAを逆生成の都合で書き換えない |
| 最終記録 | 固定reportRootのmanifest.json、validation.json、report.md。対象・入出力版/ハッシュ・検査範囲・未決/未実施 |
| 中間物・保全 | 対応する.tmp/。原入力・QA・正式試験コード・fixture・既存ローカル変更を保持。run/attempt別のbackupを累積しない |
| 別工程 | 基本/詳細設計の改訂、アプリ・物理DB・帳票実ファイルの生成、実DB操作、Excel/PDF変換、受入試験の実施、正式採点 |

## 実行工程

[要件定義の処理手順](workflows/要件定義.md)を正本とし、入力と前提の固定、要求への再構成、検査と記録の順に進める。AIが資料の意味を読み本文を執筆する。スクリプトは保存・目録・ハッシュ・構造検査に限定し、固定の業務文章を埋めた生成器や他方式の文章置換を使用しない。

既回答は変更指示や新たな矛盾がなければ継承。新たな矛盾は根拠双方と影響要求IDをQAへ記録し、採用根拠なく一方を正解にしない。認証なしサンプル、共有DB、端末、ページング等の方式固有前提を他方式へ展開しない。

## 確認と引継ぎ

構造・リンク、要求から根拠、受入条件から要求、既存前提と方式固有差分を確認する。資料のID・版・SHA-256を実ファイルと照合し、生成途中の変更は影響を再確認。自己レビューと独立レビューを区別し、担当と対象版を記録する。

受入条件は期待結果の定義であり試験結果ではない。構造・本文レビュー・利用者承認・アプリ実行・受入試験・正式採点を分け、未採点ならformalScore=null。過去のPASSを今回の版へ転用しない。

[基本設計Agent](../basic-design-agent/AGENT.md)へ要求ID・文書版・確定前提・QA・根拠を渡す。[詳細設計Agent](../detail-design-agent/AGENT.md)は基本設計の採用版を踏まえる。同一実行内の契約切替でもよく、別Agent起動・別チャット送信を必須にしない。要件定義だけの依頼から後工程を自動開始しない。
