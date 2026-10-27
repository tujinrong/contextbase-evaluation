# relationship — 独立Agentへの互換参照

版2.0／2026-10-26。現行の責務正本は平級プロジェクト [relationship-agent](../../../relationship-agent/AGENT.md)へ移した。このURLは既存参照のために残し、reverse-agentの内部子Agentを定義しない。

relationship-agentは独自package・CLI・source・request・workで起動し、共通runtimeを直接使用する。reverse-agentをinstall・import・実行する必要はない。入力・出力・前提再検証・完了条件は上記の契約に従う。

reverse-agentの連続実行経路は明示的に選ぶ互換用途だけであり、独立Agentの親や配車元ではない。実装検証状態と残課題は [実装ガイド](../../docs/ContextBase初期実装.md)を参照する。
