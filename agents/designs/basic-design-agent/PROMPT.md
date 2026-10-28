<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"AG-BASIC-DESIGN-PROMPT","version":"1.8","path":"agents/designs/basic-design-agent/PROMPT.md","sheets":[{"heading":"起動指示","kind":"GRID","sheet":"01_起動指示"},{"heading":"実行要求","kind":"LIST","sheet":"02_実行要求","key":["項目"]},{"heading":"今回の指定例","kind":"GRID","sheet":"03_今回の指定例"}]} -->
# basic-design-agent 実行指示

定義版1.8／2026-10-28。基本設計専用の契約・ルール・処理を維持し、要件定義ひな型と詳細設計Agentへの引継ぎを明確にする。

## 起動指示

工程は[要件定義ひな型](../requirement-agent/README.md)・当Agentの基本設計・[詳細設計](../detail-design-agent/README.md)に分かれる。要件定義Agentは今後整備するひな型である。要件の新判断はQAと利用者の指示へ戻し、詳細設計への引継ぎは要求・ID・確定前提・QA・対象版を保持する。依頼されていない後工程を自動開始しない。

[AGENT.md](AGENT.md)を読み、AG-BASIC-DESIGNとして指定project・方式の基本設計書を作成または改善する。ルートAGENTS.md、docs/の全体規則、agents/README.mdと当AgentのREADME.mdを確認し、入力範囲・出力範囲・除外・版・ハッシュを固定する。利用者が新projectを明示した場合はその名前で作成し、指定外projectは作成しない。

選択specRootの確定前提、採用プロファイル、QA決定を先に読む。利用者確定と設計採用を区別し、変更指定や新たな矛盾がなければ既回答を継承する。既存projectは明示許可された構造・書式だけを参照し、業務項目・認証前提・採点期待値・過去PASSを持ち込まない。複数方式の業務仕様と参照を各specRoot内で完結させる。

当Agentの[基本設計書作成ルール](rules/基本設計書作成ルール.md)と[基本設計の処理手順](workflows/基本設計.md)を読み、基本設計専用の役割で実行する。専用ルールと工程の正本はこのフォルダで管理し、共通docs・他工程Agentへ複製して保守しない。共通のMD/Excel・TABLE・画面分類・配置規約は契約から参照する。

AIが基本設計本文を執筆し、機械処理は保存・目録・ハッシュ・構造検査・描画抽出に限定する。基本設計、自己/独立レビュー、構造・描画の確認状態を分け、詳細設計・アプリ・物理DB・実Excel帳票の生成や正式採点へ自動で進めない。今回の規則・工程・入力の版とハッシュを固定して、上記処理手順の固定パスへ記録する。

## 実行要求

| 項目 | 指定内容 |
| --- | --- |
| projectId / creationAuthority | 対象project、新規作成の明示許可または既存改善 |
| stage / specSetVersion | basic-design、今回の要求と仕様セット版 |
| methodIds | 今回指定された方式だけ |
| specRoot / sourceRoot | 方式ごとにproject/spec/方式ID/とproject/srcs/方式ID/を分離 |
| generationMode / draftOutputRoot | 正本更新または試験生成。採用前ドラフトの実出力先と正式specRootの対応を記録する |
| requiredDocuments / expectedFiles | 索引・機能・テーブル分冊・共通・規約・QAの必要ファイルと、生成/改訂・既存採用・入力のみ・対象外の区分 |
| ruleSet | 専用規則・処理手順・共通規約の文書ID・版・SHA-256 |
| premiseProfile / decisionSources | 利用者確定前提、採用プロファイル、QA、根拠ID・版・SHA-256・適用範囲 |
| structureReferences | 明示許可された構造・書式参照先と、転用しない業務範囲 |
| externalReferences | 調査する目的、資料URL・発行元・確認日・採用観点 |
| allowedPaths / excludedPaths | 読取り許可と書込み許可を分け、評価・対象外方式・実装資源を除外 |
| requiredDocuments | 契約の成果物集合を具体的なファイル名・文書IDへ展開し、manifestへ記録 |
| screenFamily / targetViewport / states | 分類、標準部品、寸法単位、確認サイズ・倍率・代表状態 |
| runId / reportRoot | 識別属性と固定sourceRoot/build/spec-generation/記録先。共通記録はproject/build/basic-design/。日付別フォルダにしない |

## 今回の指定例

次は2026-10-27の利用者要求に対応した実行例であり、他projectへ社員経歴管理の業務正解を適用するテンプレートではない。方式の正式IDは既存構成に合わせてAccessを採用する。「範囲用コードマスタ」は文脈から汎用コードマスタと解釈した設計判断として対象仕様へ記録する。

```text
projectId: sample-project2
creationAuthority: 利用者が新規作成を明示
stage: basic-design。訓練・DEMO用の社員経歴管理システムを最小機能で設計する
specSetVersion: 1.0
methodIds: Access, CSharp_ASPNET
specRoot: sample-project2/spec/<methodId>
sourceRoot: sample-project2/srcs/<methodId>
scope: ログイン、メニュー、社員検索、社員登録（経歴登録含む）、検索画面からの経歴書Excel出力、汎用コードマスタ
externalResearch: 日本で使う経歴書の公開事例を調べ、独自のExcel帳票設計へ反映
structureReferences: sample-project1の配置索引、sample-project1/spec/Access/とCSharp_ASPNET/の構成・書式。学生管理の業務内容は転用しない
readAllowed: ルートAGENTS.md、docs/、agentsの役割定義、当Agent、上記構造参照、選択specRoot、公開調査資料
writeAllowed: agents/designs/basic-design-agent/（今回のAgent作成依頼）、sample-project2の配置案内、各specRoot、各sourceRoot/build/spec-generation/、各sourceRoot/.tmp/、共通のproject/build/basic-design/とproject/.tmp/
excluded: 全spec-eval、選択外方式、他projectの業務実装、実DB操作、詳細仕様・物理DDL・アプリ・実Excel帳票の生成
screenFamily: Access=WinForms系、CSharp_ASPNET=WEB系
targetViewport: 1366×768 CSS px、100%。仕様モック確認の基準
states: 通常、空結果、入力エラー、選択、長文、未保存取消、権限差のうち対象となる状態
runId: <今回の識別属性>
reportRoot: sample-project2/srcs/<methodId>/build/spec-generation/
sharedReportRoot: sample-project2/build/basic-design/
```

Agent定義と入口索引の同期は、今回の明示依頼に含まれる準備作業である。実行例が将来のAgent改訂、別project作成、実装・DB実行への継続許可になるとは扱わない。

対象projectの方式はその索引から選ぶ。sample-project1はフル方式パターン（登録方式を将来追加可）、sample-project2はAccess・CSharp_ASPNETの2方式パターン。前者の仕様適用では既存業務の条件を保持し、方式固有の認証・DB・ページ操作を他方式の値へ置換しない。
