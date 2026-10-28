# relationship-agent 実行指示

版1.1／2026-10-26。[契約](AGENT.md)と[運用案内](README.md)を読み、独立したsource・request・workを指定する。

1. source-only入力と全前提グラフを含むv2 requestを確定する。relationshipの対象義務を明示し、入力根とworkを同一・親子にしない。
2. initで自身の原文を封印する。後続層はportable handoffを渡し、前層workへ接続しない。受信側の検証なしに旧合格を有効化しない。
3. runで本層だけを抽出・独立検証・ホスト採用する。必要ならrequirementsで限定する。needs-prerequisitesは入力不足として保存し、前層を自動実行しない。
4. statusで本層と元goalの未達を区別し、exportで全有効記録・未知・未閉鎖followup（raw履歴は監査用）を引き渡す。

```text
contextbase-relationship init --source SOURCE --request REQUEST.json --work WORK --handoff HANDOFF.json
contextbase-relationship run --work WORK
contextbase-relationship status --work WORK
contextbase-relationship index --work WORK
contextbase-relationship export --work WORK --output HANDOFF_OUT.json
```

runは必要に応じ --requirements ID...、--inline-sources、--timeout SECONDSを受ける。後続層の欠けた前提を本CLIで生成せず、利用者・ホストへ質問を返す。exportは受入れ済み自層成果が必要で、手動 --output はsource／work外の未作成パスにする。手動出力を上書きしない。revise／cancel／resumeは共通の状態操作として利用できるが、他層を本CLIで抽出しない。新CLIの最終検証状態は運用案内で確認する。

## 明示した再調査

```text
contextbase-relationship retry --work WORK --feedback CANDIDATE_SHA256
```

自層の既知候補だけをfeedbackに指定し、必要なら --requirements ID...／--inline-sources／--timeoutを加える。初稿拒否後も一度だけ再調査できる。同basisのrunは既存pendingを返し、自動の無限再試行にはしない。採用済み自層義務を変える場合は先にreviseする。外部前提を本層で書き直さず、新handoffを新workで受ける。故障停止時は同requestでresumeした後にretryする。

## 設定ファイルを使う場合

Agentディレクトリからの例。相対パスの解決基準はconfigファイルの位置である。

```text
contextbase-relationship paths --config ../../../sample-project1/contextbase.toml --profile csharp_aspnet
contextbase-relationship init --config ../../../sample-project1/contextbase.toml --profile csharp_aspnet
contextbase-relationship run --config ../../../sample-project1/contextbase.toml --profile csharp_aspnet
contextbase-relationship export --config ../../../sample-project1/contextbase.toml --profile csharp_aspnet
```

pathsは表示だけで原文封印・LLMを起動しない。init／run等の実行は依頼されたときに行う。--configを使う場合は明示source／request／work／handoff／outputを混在させない。status／index／retry／revise／cancel／resumeにも同じconfigと任意profileを指定できる。

固定出力は設定output/relationship-agent/contextbase.json。target.jsonの所有束縛とロック・原子更新を使い、別profile／source／goalへ上書きしない。手動 --output のfresh-only制約とは区別する。設定、結果未生成の状態は [プロジェクト出力案内](../../../sample-project1/spec-reverse/README.md)を参照する。現在、実業務のLLM解析は開始していない。

設定にはcsharp_wpfもあり、--profile csharp_wpfでsource・work・outputをWPF用へ分けられる。既定csharp_aspnetは変えず、今回どちらの実業務LLM解析も実行しない。
