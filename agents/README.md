<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"AGENT-INDEX","version":"8.11","path":"agents/README.md","sheets":[{"heading":"概要","kind":"GRID","sheet":"01_概要"},{"heading":"Agent一覧","kind":"LIST","sheet":"02_Agent一覧","key":["Agent-ID"]},{"heading":"実行コンテキスト","kind":"GRID","sheet":"03_実行コンテキスト"}]} -->
# Agent定義一覧

版8.11／2026-10-28。要件定義・基本設計・詳細設計の3担当を配置し、旧汎用仕様Agentの入口を廃止する。ContextBaseの明示incrementalによる分割調査・草稿保存・独立検証と継続を接続し、実行・採用・人手受入れは今回の報告で区別する。

## 概要

9種類の入口を置く。要件定義・基本設計・詳細設計を専用の契約とし、実装、Access再構築、3つの独立解析Agent、任意の逆解析互換入口と責務を分ける。Codexが契約と実行指示を読んで作業する。定義文書の存在だけで各工程を実行済みとしない。題材はprojectIdで選択し、全体規則と題材の正解を分離する。実行時に許可ファイルを列挙し、GitHub全体を無制限に参照させない。

取得・目録化はdiscovery-agent、関係構築はrelationship-agent、動作深化はbehavior-agentが独立して実行する。各自にpackage／CLI・source／request／workを持ち、reverse-agentに依存・importせず共通runtime（agents/reverses/shared/contextbase-runtime）を使用する。独立検証は各層の抽出と別task・文脈で実行し、それぞれのホストが採用する。

後続Agentはportable handoffを受け取り、同一request・ソースmanifest／内容を自身の原文で再検証する。前層workは不要、外部passは監査情報だけに使う。前提不足はneeds-prerequisites。reverse-agentは希望時だけ使う互換連続実行入口で、3Agentを統括しない。独立導入とportable受渡しの構造・合成検証は通過した。実モデル品質・人手受入れは別途未完了。

機能の意味・粒度・集計は[用語集](GLOSSARY.md)と[分類境界](reverses/shared/contextbase-runtime/docs/機能分類境界.md)、Tree-sitter事実は[索引契約](reverses/shared/contextbase-runtime/docs/ソース事実索引.md)、compactと明示repairは[短縮伝送契約](reverses/shared/contextbase-runtime/docs/短縮伝送と証拠一括検査.md)を正本とする。新workの[host取証](reverses/shared/contextbase-runtime/docs/ホスト取証プロトコル.md)に加え、[incremental](reverses/shared/contextbase-runtime/docs/分割調査・独立検証プロトコル.md)は元義務内の単位草稿、完全候補組立、局所／全体レビューの集約と継続を提供する。領域子集の正式交接・選択前提有効化と汎用再利用は未実装。実装範囲は[実装ガイド](reverses/reverse-agent/docs/ContextBase初期実装.md)、実モデル・採用と人手受入れは各成果案内で区別する。

配置は成果の責務で分類する。分類フォルダは起動制御やAgent間の上下関係を追加しない。

移動前のeditable環境は新しい配置で再導入する。封印済みworkや過去の検証JSONに記録された絶対パス・hashは書き換えず、配置変更を再解析・再採用の完了として扱わない。Windowsのdiscovery一括起動は各projectのrun-discovery.cmdを入口とする。

```text
agents/
├─ builds/
│  └─ build-agent/
├─ converts/
│  └─ access-rebuilder-agent/
├─ reverses/
│  ├─ discovery-agent/
│  ├─ relationship-agent/
│  ├─ behavior-agent/
│  ├─ reverse-agent/
│  └─ shared/contextbase-runtime/
└─ designs/
   ├─ requirement-agent/  （要件定義）
   ├─ basic-design-agent/
   └─ detail-design-agent/
```

## Agent一覧

| 分類 | Agent-ID | 役割 | 契約文書 |
| --- | --- | --- | --- |
| designs | AG-REQUIREMENT | 要件定義専用（0.2）。要求起点と既存仕様からの逆生成 | [契約](designs/requirement-agent/AGENT.md)・[実行指示](designs/requirement-agent/PROMPT.md)・[運用案内](designs/requirement-agent/README.md) |
| designs | AG-BASIC-DESIGN | 基本設計専用。新規作成・改善・レビューと専用ルール・処理の管理 | [契約](designs/basic-design-agent/AGENT.md)・[実行指示](designs/basic-design-agent/PROMPT.md)・[運用案内](designs/basic-design-agent/README.md) |
| designs | AG-DETAIL-DESIGN | 詳細仕様書専用。新規作成・改善・レビューと専用ルール・処理の管理 | [契約](designs/detail-design-agent/AGENT.md)・[実行指示](designs/detail-design-agent/PROMPT.md)・[運用案内](designs/detail-design-agent/README.md) |
| builds | AG-BUILD | 仕様からシステム生成 | [build-agent](builds/build-agent/AGENT.md) |
| reverses | AG-DISCOVERY | 独立した取得・目録化 | [契約](reverses/discovery-agent/AGENT.md)・[実行](reverses/discovery-agent/PROMPT.md)・[案内](reverses/discovery-agent/README.md) |
| reverses | AG-RELATIONSHIP | 独立した関係構築 | [契約](reverses/relationship-agent/AGENT.md)・[実行](reverses/relationship-agent/PROMPT.md)・[案内](reverses/relationship-agent/README.md) |
| reverses | AG-BEHAVIOR | 独立した動作深化 | [契約](reverses/behavior-agent/AGENT.md)・[実行](reverses/behavior-agent/PROMPT.md)・[案内](reverses/behavior-agent/README.md) |
| reverses | AG-REVERSE | 任意の互換連続実行・旧仕様書経路の明示入口 | [契約](reverses/reverse-agent/AGENT.md)・[実行指示](reverses/reverse-agent/PROMPT.md)・[運用案内](reverses/reverse-agent/README.md) |
| converts | AG-ACCESS-REBUILDER | 指定AccessからASP.NET Core／C#／SQL Serverへ再構築。sample-project1で最大2回の生成・検証を実施 | [契約](converts/access-rebuilder-agent/AGENT.md)・[作成計画](converts/access-rebuilder-agent/docs/作成計画.md)・[運用案内](converts/access-rebuilder-agent/README.md) |

## 実行コンテキスト

基本設計専用の記述規則は[専用ルール](designs/basic-design-agent/rules/基本設計書作成ルール.md)、執筆・検査・描画・記録は[専用工程](designs/basic-design-agent/workflows/基本設計.md)へ集約する。詳細設計の[専用ルール](designs/detail-design-agent/rules/詳細設計書作成ルール.md)と[専用工程](designs/detail-design-agent/workflows/詳細設計.md)はdetail-design-agentへ保存する。要件定義の[専用規則](designs/requirement-agent/rules/要件定義書作成ルール.md)と[処理手順](designs/requirement-agent/workflows/要件定義.md)はrequirement-agentへ保存し、仕様書から要件への逆生成も同Agentが担当する。各担当は要求・既存ID・確定前提・QA・依存を引き継ぎ、他工程の専用ルールや処理を自身の正本として追加しない。旧汎用仕様Agentのフォルダは廃止した。

projectId、仕様セット版、方式ID、specRoot=project/spec/方式ID、sourceRoot=project/srcs/方式ID、入力コミット/ハッシュ、許可パス、除外パス、出力先、Agent定義版、実行IDを固定する。AG-REQUIREMENT／AG-BASIC-DESIGN／AG-DETAIL-DESIGNは各工程のspecRootを更新し、AG-BUILDは選択specRootの実装入力からsourceRootへ生成する。設計Agent／AG-BUILDの業務入力は選択方式のspecRoot内で閉じ、旧sourceRoot/specや他方式を代替入力にしない。AG-REQUIREMENTのspec-to-requirementsは選択specRootを読む仕様文書工程であり、コードからの逆生成評価と区別する。3つの解析AgentとAG-REVERSEは原仕様を読まず、選択source-only入力を使う。全Agentは最終正本を更新し、最終成果・検査結果はsourceRoot/build/の固定先へ更新する。中間結果はsourceRoot/.tmp/、方式を持たない共通作業は担当Agentまたはprojectの.tmp/を使う。過去生成結果の別名保存はせずGit履歴を使う。spec-evalは採点者の参照先で、逆生成Agentの実行権限・入力選択では移動後のproject/spec/全体とともに禁止し、選択ソース根の外へ物理的に隔離する。逆生成CLIのallowedPaths／excludedPathsはそのソース根内の相対パスに限定し、兄弟の仕様へ範囲を広げない。共有docsに業務正解を隠して隔離を迂回しない。

拒否草稿の限定回復は[明示repair契約](reverses/shared/contextbase-runtime/docs/短縮伝送と証拠一括検査.md)に従い、fresh workの未信頼seedからモデルが指定recordだけを置換する。旧成功を引き継がず、全体を機械・独立検証へ戻す。回復実績は実装ガイドで確認する。

AG-ACCESS-REBUILDERは利用者指定のAccessファイルを主入力とする移行工程で、AG-BUILDの仕様入力とは分ける。sample-project1ではAccess/build/StudentManagement.accdbから別のsourceRoot=srcs/Access-To-CSharp_ASPNET/へ再構築し、利用者の追加指示によりCSharp_ASPNETソースを読取り専用のWeb設計・実装の参考に使い、Accessの画面操作の同形再現は要求しない。既存原仕様・spec-evalは入力にせず、業務制約とUIの採用判断を分ける。利用者の実施指示により、最大2回の訓練で本体取得・C#／SQL生成・検証を行い、指定されたローカルSQLEXPRESSの新規専用DBを使用した。今回の台帳上限を超える反復は開始しない。
