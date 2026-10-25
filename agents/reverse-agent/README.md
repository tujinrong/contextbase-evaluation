# reverse-agent — ソースから ContextBase を構築・検証する

版8.1／2026-10-24。統一入口の内部を、取得・調査・独立検証の3役割に分ける。仕様書生成は下流の責務とする。

## 入口と状態

[AGENT.md](AGENT.md)が共通の役割・入力・出力・採用契約、[PROMPT.md](PROMPT.md)が依頼方法、[AGENTS.md](AGENTS.md)が作業上の規則である。今回追加したのは文書上の役割定義であり、3役割を自動起動する新しい CLI、共通制御、schema、store の実装は今後行う。手動で依頼する場合も、候補提出と正本への採用・範囲受入れを分ける。

| 内部役割 | 担当 | 主な成果 |
| --- | --- | --- |
| [discovery-agent](roles/discovery/AGENT.md) | 取得と初期理解 | システム概要・機能・テーブル／データ・共通候補、構造索引、被覆と未知 |
| [investigation-agent](roles/investigation/AGENT.md) | 目標に沿う関係調査と動作深化 | 関係、条件、値、状態、異常、呼出差の根拠付き候補差分 |
| [review-agent](roles/review/AGENT.md) | 各ラウンドと最終範囲の独立原文確認 | 漏れ・誤り・矛盾、確認範囲、追加調査要求、検証結果 |

調査ラウンドは理解を深める順序、Agent は責務の分担である。関係調査と動作深化は investigation-agent 内で往復し、review-agent は全段階を横断する。初期目録だけが必要なら取得・検証で返し、有効な索引があれば必要な調査から進める。

3役割は共通の snapshot、SourceAccess、ID、store、adapter を使用する。共通制御が依頼、版、競合、採用、受入れと再開を管理し、各役割は作業領域へ候補または指摘を提出する。役割を分けただけで高速化を確認済みとは扱わない。

## 設計と実装計画

- [ContextBase 段階的抽出・検証設計](docs/ContextBase分轮提取与验证流程.md)：D01～D12、初期目録、関係・動作調査、独立検証、役割間の受渡し。
- [ContextBase 実装計画](docs/ContextBase実装計画.md)：P0～P8 の開発順序、各役割と共通基盤、成果物、完了条件、今後の試験。

対象の二言語・projectId は未選定である。現存する AI facts、旧 ContextBase の状態、過去の試験結果を新契約の実装・正確性・性能確認へ読み替えない。

## 既存コードと旧仕様書生成経路

現在のコードには、文書単位の AI plan／analysis／draft／review、機械解析の foundation／detail／specification、docsite の HTML／PDF／Excel 変換が残っている。今回、コード・CLI・既存 ContextBase・QA・output は変更していない。新しい契約と現行実装は同じ状態ではない。

旧経路を明示選択する場合は、[旧契約・実行説明](docs/legacy/README.md)を読む。旧 README のコマンドは新しい3役割の起動方法ではない。過去の訓練許可、参考設計、採点結果、制限時間はその当時の範囲に限定する。

文書の整理・執筆・変換を担当する下流 Agent の配置と、旧コードの移管は未決定である。[全体 Agent 一覧](../README.md)も ContextBase までの責務と内部3役割に同期している。詳細な現行契約は本ディレクトリの AGENT.md を入口とする。

最終正本は共通制御による採用手順を守って更新する。最終検査記録は対象方式build/、候補・中間生成・試行は同方式.tmp/へ配置し、過去生成世代はGitで管理する。方式のない共通工程だけ担当Agentまたはproject内のbuild/・.tmp/を使う。入力・QA・解析正本・正式fixtureを一時生成物として削除しない。
