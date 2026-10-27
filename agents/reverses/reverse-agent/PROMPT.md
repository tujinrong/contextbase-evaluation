# reverse-agent 互換連続実行の実行指示

版1.6／2026-10-26。通常の単層実行は [discovery-agent](../discovery-agent/PROMPT.md)、[relationship-agent](../relationship-agent/PROMPT.md)、[behavior-agent](../behavior-agent/PROMPT.md)へ直接依頼する。reverse-agentは親ではなく、明示された場合だけ使う互換連続実行入口である。

## 独立実行を選ぶ

各Agentは独立source／request／workを確定し、共有runtimeと自身のpackageだけを導入する。前層を自動起動せず、後続層はportable handoffと自身の原文で前提を再検証する。外部passは監査だけ、前層workは不要。前提不足はneeds-prerequisitesで返す。

requestはv2の元goal・全前提グラフを保持する。handoffは同一request・同一の可搬ソースmanifest／内容（絶対sourceRootを除く）に限定し、別範囲への汎用再利用へ広げない。入力・権限・原仕様隔離、QA、.tmp／build、根拠と独立採用は [共通条件](AGENT.md)および各独立Agentの契約に従う。

## 互換連続実行を明示した場合

[実装ガイド](docs/ContextBase初期実装.md)の互換CLIを使い、3層を扱う元目標と許可入力を固定する。独立Agentをreverse-agent経由で必ず起動する構成にはしない。step／verify／adopt、run、reviseの結果はその互換work内の状態である。

元目標外の補査や範囲拡大は自動化せず、未解決を保存する。旧v1・旧roleを推測変換しない。独立実行と互換実行の採用済み状態を、portable受渡しの受信再検証なしで共用しない。

## 報告

実際に使用したAgent・package・CLI、入力と受渡しの版・hash、scope、ローカルの検証・採用、未達と未実施を報告する。新配置の構造・合成検証は通過した。実モデル品質・人手受入れと区別して報告する。清掃済み試行の復元や再開は行わない。

単独CLIのretryは本層の既知候補へ明示した一度だけの再調査である。採用済み本層は先にreviseし、上流の訂正は新handoff／新workを使う。故障停止後は同requestでresumeする。
