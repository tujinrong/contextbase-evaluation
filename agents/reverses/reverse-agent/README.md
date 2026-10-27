# reverse-agent — ソースから ContextBase を構築・検証する

版8.7／2026-10-26。reverse-agentは任意の互換連続実行入口。3つの解析Agentは平級の独立プロジェクトへ分離する。新配置の構造・合成検証は通過した。仕様書生成は下流の責務とする。

## 独立プロジェクトの入口

| Agent | package／CLI | モジュール | 契約 |
| --- | --- | --- | --- |
| discovery-agent | contextbase-discovery | contextbase_discovery | [取得・目録化](../discovery-agent/AGENT.md) |
| relationship-agent | contextbase-relationship | contextbase_relationship | [関係構築](../relationship-agent/AGENT.md) |
| behavior-agent | contextbase-behavior | contextbase_behavior | [動作深化](../behavior-agent/AGENT.md) |

各自のsource／request／workで起動し、共通runtimeをagents/reverses/shared/contextbase-runtimeから使う。reverse-agentのinstall・import・統括実行は不要。後続層はportable handoffを受信し、自身の原文で前提を独立再検証する。前層workは不要で、外部passを信用して有効化しない。

各CLIは自層だけを抽出・独立検証・host採用する。前提不足はneeds-prerequisites。reverse-agentのanalysis-pipelineは3packageを追加導入した場合の任意連続実行入口で、各公開run／exportを使う。旧extractは旧v2互換として別に残し、その合格を独立導入の証明にしない。詳しい導入と受渡しは [実装ガイド](docs/ContextBase初期実装.md)にまとめる。

共通のC#／Java構文adapterはcallを未解決候補として返し、型束縛・データフロー・framework／SQL専用解析は未実装。実モデルの業務品質、人手受入れ、汎用P6再利用、長期運用も未完了である。

## 試行資産の状態

2026-10-26、利用者の指定により、2プロジェクトの reverse-agent 試行用ソース複製・設定・結果の清掃を完了した。元のプロジェクトは保持する。旧作業領域はresumeできず、再試行は対象範囲・request・作業領域を新たに確定する。

異なる2言語の小規模試行で共通フローを検証するD06は維持する。次の業務対象と人手照合基準は改めて選定し、旧結果を新しい受入れ根拠へ流用しない。汎用実装と合成ソースの単体テストは保持する。

## 設計・計画・既存経路

- [段階的抽出・検証設計](docs/ContextBase段階的抽出・検証フロー.md)：v0.9、D01～D12と新しい層分担。
- [実装計画](docs/ContextBase実装計画.md)：v0.7、P0～P8の移行・部分実装と残作業。
- [初期実装ガイド](docs/ContextBase初期実装.md)：現CLIの操作、request、制約。

既存の文書単位 AI plan／analysis／draft／review、foundation／detail／specification、docsite の変換処理は残る。[旧契約・実行説明](docs/legacy/README.md)を明示選択した場合だけ使い、新しい extract と区別する。旧 ContextBase、identities、人工QA、既存outputを自動移行・置換しない。

固定の総時間・総トークン予算は設けない。互換経路では単独stepと連続実行runを提供し、独立Agentのrunは自層だけを扱う。未定義の補査を自動生成する長期修復ループは提供しない。個別応答 timeout は資源保護であり、総予算ではない。cancel は古い返却の採用を防ぐが、実行中プロセスの即時停止を保証しない。store の hash は整合性検査であり認証ではない。

文書の整理・執筆・変換を担当する下流 Agent の配置と、旧コードの移管は未決定である。[全体 Agent 一覧](../../README.md)も ContextBaseまでの責務と平級3Agentの独立実行設計に同期している。詳細な現行契約は本ディレクトリの AGENT.md を入口とする。

最終正本は共通制御による採用手順を守って更新する。最終検査記録は対象方式build/、候補・中間生成・試行は同方式.tmp/へ配置し、過去生成世代はGitで管理する。方式のない共通工程だけ担当Agentまたはproject内のbuild/・.tmp/を使う。入力・QA・解析正本・正式fixtureを一時生成物として削除しない。
