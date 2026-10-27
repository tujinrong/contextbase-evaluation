# discovery-agent 実行指示

版1.8／2026-10-27。[契約](AGENT.md)と[運用案内](README.md)を読み、独立したsource・request・workを指定する。

## 目録化・粒度レビューの参照

目録候補を作る、統合・分割する、件数を報告する前に [機能分類境界](../shared/contextbase-runtime/docs/機能分類境界.md)と [用語集](../../GLOSSARY.md)を読む。取得sourceの広さからWebだけの集計範囲を暗黙に決めず、actor・業務領域・対象範囲と主階層を指定する。

候補ごとに目的・対象・完了成果、子操作の利用文脈と主帰属、共通の共有責務を根拠付きで説明する。過分割と過統合を両方点検し、変更理由・反例・未確認を残す。期待件数へ合わせない。具体的な意味事例は正本を参照し、候補名をそのまま正解にしない。

新Dモードはホストが固定するcatalogPolicy=contextbase-catalog/1とtyped classificationに従う。正本の必須項目、実unknownに結び付く保留、同scopeの意味参照を記録する。非該当分類はnullとし、旧記録へnullを補う変換はしない。独立検証では主・子・共通・保留の全対象recordへ正確なkey／版hashのclassificationChecksを返す。scopeChecksは非意味分類を含む全viewを調べ、元scopeの零recordも見落とさない。

## 実行手順

1. source-only入力と全前提グラフを含むv2 requestを確定する。discoveryの対象義務を明示し、入力根とworkを同一・親子にしない。
2. initで自身の原文を封印する。後続層はportable handoffを渡し、前層workへ接続しない。受信側の検証なしに旧合格を有効化しない。
3. [ソース事実索引契約](../shared/contextbase-runtime/docs/ソース事実索引.md)に従ってvalidate-indexと必要なqueryで全台帳・構文観測を確認する。モデル呼出し前の機械検査passと、未解決call・入口候補等の制約を確認する。
4. runで本層だけを抽出・独立検証・ホスト採用する。必要ならrequirementsで限定する。needs-prerequisitesは入力不足として保存し、前層を自動実行しない。
5. statusで本層と元goalの未達を区別し、exportで全有効記録・未知・未閉鎖followup（raw履歴は監査用）を引き渡す。

```text
contextbase-discovery init --source SOURCE --request REQUEST.json --work WORK
contextbase-discovery run --work WORK
contextbase-discovery status --work WORK
contextbase-discovery index --work WORK
contextbase-discovery validate-index --work WORK
contextbase-discovery query --work WORK --kind entry
contextbase-discovery export --work WORK --output HANDOFF_OUT.json
```

runは必要に応じ --requirements ID...、--inline-sources、--timeout SECONDSを受ける。後続層の欠けた前提を本CLIで生成せず、利用者・ホストへ質問を返す。exportは受入れ済み自層成果が必要で、手動 --output はsource／work外の未作成パスにする。手動出力を上書きしない。revise／cancel／resumeは共通の状態操作として利用できるが、他層を本CLIで抽出しない。新CLIの最終検証状態は運用案内で確認する。

## 明示した再調査

```text
contextbase-discovery retry --work WORK --feedback CANDIDATE_SHA256
```

自層の既知候補だけをfeedbackに指定し、必要なら --requirements ID...／--inline-sources／--timeoutを加える。初稿拒否後も一度だけ再調査できる。同basisのrunは既存pendingを返し、自動の無限再試行にはしない。採用済み自層義務を変える場合は先にreviseする。外部前提を本層で書き直さず、新handoffを新workで受ける。故障停止時は同requestでresumeした後にretryする。

## 設定ファイルを使う場合

Agentディレクトリからの例。相対パスの解決基準はconfigファイルの位置である。

```text
contextbase-discovery paths --config ../../../test-project1/contextbase.toml --profile csharp_aspnet
contextbase-discovery init --config ../../../test-project1/contextbase.toml --profile csharp_aspnet
contextbase-discovery run --config ../../../test-project1/contextbase.toml --profile csharp_aspnet
contextbase-discovery export --config ../../../test-project1/contextbase.toml --profile csharp_aspnet
```

pathsは表示だけで原文封印・LLMを起動しない。init／run等の実行は依頼されたときに行う。--configを使う場合は明示source／request／work／handoff／outputを混在させない。status／index／retry／revise／cancel／resumeにも同じconfigと任意profileを指定できる。

固定出力は設定output/discovery-agent/contextbase.json。target.jsonの所有束縛とロック・原子更新を使い、別profile／source／goalへ上書きしない。手動 --output のfresh-only制約とは区別する。実行済み範囲・人手レビュー状態は [プロジェクト出力案内](../../../test-project1/spec-reverse/README.md)を参照する。

設定にはcsharp_wpfもあり、--profile csharp_wpfでsource・work・outputをWPF用へ分けられる。既定csharp_aspnetは変えず、他profileの解析は個別の実行要求に従う。

## 今回のD単独再実行

source／request／固定outputは維持し、新work .tmp/contextbase/csharp_aspnet-compact-repairで明示repairを実行した。旧work・旧結果は新候補の独立検証と採用が済むまで保持し、採用後だけ固定discovery成果を原子的に更新する。比較材料は旧work／.tmpに残し、正式archiveを作らない。

R／Bを起動・作成しない。実測件数・検証・採用・失敗の状態は確定結果に従って記録し、LLMが答えたことや形式合格だけで人手受入れ済みとしない。

作者はホスト固定sourceFactsSha256と全recordのfactUsageを返す。独立検証者は全索引とinventoryからfactUsageCheckを返し、passを追加採用条件とする。詳細な検査条件は索引契約へ集約する。今回の新機構の構造・合成回帰は確認済みで実Dは69候補の独立検証を完了し、fact利用はpass・catalogは要追加調査で未採用である。

作者はtask.recordKinds内のkindだけを返し、factUsageの各factに対応する正確なpath・行・hashを同record.evidenceへ記録する。跨ファイルの支持factも省略しない。層外kindや根拠位置不一致はhostで拒否し、元応答の手作業書換えで通過させない。

## 明示compactで実行する場合

[短縮伝送と証拠一括検査](../shared/contextbase-runtime/docs/短縮伝送と証拠一括検査.md)を読み、source-fact対応Dでだけ--compactを指定する。出力はtaskの厳密schemaとwireSha256に従い、evidence.fileとfact参照は同taskのaliasを使う。理由は目録深度で簡潔にし、必要な候補・未解決・反例は残す。

```text
contextbase-discovery run --config ../../../test-project1/contextbase.toml --profile csharp_aspnet --inline-sources --compact
```

既定はcanonical互換である。compactでも原文は全量であり、必要原文だけを取り寄せる複数回の調査ループは未実装。新規回帰・実D結果は実装ガイドに記録した。候補化とfact利用の支持、catalog未採用を区別する。

followup.pathsはtask.authorizedSourcePathsの封印inventory内だけを指定する。omittedの不足材料はpaths:[]でquestion／unknownへ説明し、未取得pathを原文根拠にしない。requirementとunknown関連・阻害IDはtask schemaの元goal集合に従い、ホストの範囲検査も維持する。

## 拒否草稿を明示修復するとき

fresh D workをinitし、[短縮伝送契約のrepair手順](../shared/contextbase-runtime/docs/短縮伝送と証拠一括検査.md)に従って--from-work／--task／--recordを指定する。seedは未信頼で、旧合格を継承しない。指定recordの全置換だけをモデルへ依頼し、必要な追加削除やscope変更はunresolvedで返す。ホストは推測修正せず、合成全体を通常機械gateと独立verifyへ通す。

```text
contextbase-discovery repair --work FRESH_WORK --from-work OLD_WORK --task OLD_TASK --record common.date --inline-sources --compact
```

新規抽出の所要時間と明示修復の所要時間は分けて報告する。最終回帰は確認済みだが、実repairは独立検証を完了したがcatalog未解決で未採用である。

## 独立画面と共通実装の区別

主機能は業務とシステムの独立利用者タスクを含む。専用ログイン画面は主機能候補として記録し、認証サービスやセッション処理だけで代用しない。メニューは[分類境界](../shared/contextbase-runtime/docs/機能分類境界.md)に従い、選択肢の表示と別機能への遷移だけなら共通ナビゲーションと技術入口として記録する。専用Controller／View、顧客専用表示、役割でのリンク出し分けを主機能の根拠にせず、移動を超える独立した情報成果や処理を原文で確認する。読取専用の状況集約等も対象となり、DB書込みは必須条件ではない。作者と独立検証者は同じ基準で、ナビゲーションの過剰計上と独立した利用者タスクの過統合を確認する。画面数や予定件数へ合わせず、詳細・確認・子画面は親目的を確認する。

本規則の実モデル再抽出・独立検証と合成契約検査を分離し、最新の実施状態は成果READMEと実装ガイドで確認する。旧passを新規則へ流用せず、再実行時はfresh workを使う。
