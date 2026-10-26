# reverse-agent — ソースから ContextBase を構築・検証する

版8.6／2026-10-26。設計上の3子Agentを取得・目録化、関係構築、動作深化に分ける。独立検証は共通能力とする。仕様書生成は下流の責務とする。

## 現在の入口と実装範囲

実行権限・入力選択ではproject/spec/全体とproject/spec-eval/を禁止し、選択する --source の外へ物理的に隔離する。--source はsourceRoot=project/srcs/方式ID/または隔離したsource-only入力に限定し、projectルートへ広げない。CLIのallowedPaths／excludedPathsは --source 内の相対パスだけを指定する別の層であり、兄弟のproject/specを列挙したり ../ で根の外を参照したりしない。

[AGENT.md](AGENT.md)が共通契約、[PROMPT.md](PROMPT.md)が依頼方法、[AGENTS.md](AGENTS.md)が作業規則である。現CLIは `python -m contextbase extract`。インストール、request、実行順序は [ContextBase 初期実装](docs/ContextBase初期実装.md)を参照する。

v2のanalysis パッケージは、封印した選択ソース、C#／Java の Tree-sitter 構文索引、1役割ごとのモデル実行、独立 review、ホストによる adopt、状態保存、cancel／resume を実装している。既定グラフのready queueと明示reviseを実装した。任意の自動補査修復、cross-session P6再利用、人手正解表の受入れは未完了である。

## 新設計の3子Agent

| 子Agent | 主責務 | 主な成果 |
| --- | --- | --- |
| [discovery](roles/discovery/AGENT.md) | 取得・目録化 | 概要、機能、入口、データ、共通候補、被覆と未知 |
| [relationship](roles/relationship/AGENT.md) | 関係構築 | 接続、方向、条件、根拠、未解決関係 |
| [behavior](roles/behavior/AGENT.md) | 動作深化 | 条件、値、状態、順序、例外、副作用、呼出差 |

各領域の検証済み前提を使い、必要な層だけを調べる。relationshipも関係判断に条件・引数を読み、behaviorも不明関係を補査へ返す。アダプター、原文、保存、独立検証は共通であり、層ごとに複製しない。検証は作者と異なるtask・文脈で実行し、ホストが採用・範囲受入れを判断する。第4の抽出子Agentにはしない。

現CLIはv2 request（schema、stage／scope／requires）とstep --stage／verify／run／reviseを使う。関係は同scopeの目録、動作は同scopeの関係を前提とする。旧v1／ --role は自動変換しない。

runは検証済み局所を先へ進め、阻害・グラフ外補査は保存して止まる。同basisの反復で新モデルを呼ばない。reviseは義務・版固定record依存の下流を撤回でき、step --feedbackで原文再調査する。未知は関連先と阻害先を分け、別taskのverifyが根拠付きで影響を確認する。

## 試行資産の状態

2026-10-26、利用者の指定により、2プロジェクトの reverse-agent 試行用ソース複製・設定・結果の清掃を完了した。元のプロジェクトは保持する。旧作業領域はresumeできず、再試行は対象範囲・request・作業領域を新たに確定する。

異なる2言語の小規模試行で共通フローを検証するD06は維持する。次の業務対象と人手照合基準は改めて選定し、旧結果を新しい受入れ根拠へ流用しない。汎用実装と合成ソースの単体テストは保持する。

## 設計・計画・既存経路

- [段階的抽出・検証設計](docs/ContextBase分轮提取与验证流程.md)：v0.8、D01～D12と新しい層分担。
- [実装計画](docs/ContextBase実装計画.md)：v0.6、P0～P8の移行・部分実装と残作業。
- [初期実装ガイド](docs/ContextBase初期実装.md)：現CLIの操作、request、制約。

既存の文書単位 AI plan／analysis／draft／review、foundation／detail／specification、docsite の変換処理は残る。[旧契約・実行説明](docs/legacy/README.md)を明示選択した場合だけ使い、新しい extract と区別する。旧 ContextBase、identities、人工QA、既存outputを自動移行・置換しない。

固定の総時間・総トークン予算は設けない。単独stepと既定グラフを進めるrunを提供する。未定義の補査を自動生成する長期修復ループは提供しない。個別応答 timeout は資源保護であり、総予算ではない。cancel は古い返却の採用を防ぐが、実行中プロセスの即時停止を保証しない。store の hash は整合性検査であり認証ではない。

文書の整理・執筆・変換を担当する下流 Agent の配置と、旧コードの移管は未決定である。[全体 Agent 一覧](../README.md)も ContextBaseまでの責務と新しい3子Agent設計に同期している。詳細な現行契約は本ディレクトリの AGENT.md を入口とする。

最終正本は共通制御による採用手順を守って更新する。最終検査記録は対象方式build/、候補・中間生成・試行は同方式.tmp/へ配置し、過去生成世代はGitで管理する。方式のない共通工程だけ担当Agentまたはproject内のbuild/・.tmp/を使う。入力・QA・解析正本・正式fixtureを一時生成物として削除しない。
