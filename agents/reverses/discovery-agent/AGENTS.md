# discovery-agent 作業規則

版1.4／2026-10-26。

- 共通の入力・権限・採用条件は [AGENT.md](AGENT.md)、操作は [PROMPT.md](PROMPT.md)を読む。reverse-agentを必須入口にしない。
- 変更は明示された本プロジェクトの実装・文書・作業先に限定し、他Agentや共有runtimeの無関係な変更をしない。
- 原文は読取り専用。原仕様・spec-eval・秘密情報を渡さず、入力コードやSQLを実行しない。人工QA・正式fixtureは中間物として削除しない。
- 前提を受け取っても外部passを信用して採用しない。自身のsourceに照合し、別文脈の検証を記録する。前提不足で前層を勝手に起動しない。
- 未解決は保存し、固定総予算・モデル呼出数だけで品質通過にしない。新実装の合成試験と実モデル・人手品質受入れを区別する。
- input/request/handoff/出力の版・hash、対象範囲、独立検証、未達・未実施を報告する。Gitへの登録・commitは指示に従う。

## 機能分類を判断する前

[用語集](../../GLOSSARY.md)と [機能分類境界](../shared/contextbase-runtime/docs/機能分類境界.md)に従い、主機能・子操作・共通の理由と反例を確認する。ソース取得範囲と集計範囲を分離し、現scopeの主階層だけを数える。role、画面、URL、トランザクション、CRUD名、CLI形態だけで階層を決めない。

分類未確認は別掲する。新taskのhost固定policy、typed classification、record単位とscope単位の独立検査、保留の追加採用条件を確認する。legacy taskの通過を新分類規則の合格として扱わない。新回帰・D実測の結果は実装ガイドで確認し、要追加調査・未採用と人手受入れ未実施を区別する。

今回の実行範囲はDだけ。新workで原文を固定し、旧結果は独立検証・採用の成功まで保持する。R／Bのプロセスや新作業ディレクトリを起動・生成しない。原仕様・spec-evalを読まず、原プログラム・SQL・DBを実行しない。

## 構文索引を使うとき

[ソース事実索引契約](../shared/contextbase-runtime/docs/ソース事実索引.md)に従い、モデル呼出し前に全inventoryとfact根拠を機械検査する。queryのtruncated、call未解決、entryの到達性未確認を報告し、全索引と原文から利用証跡を別文脈で検査する。確定したfact利用のpassとcatalog未採用を区別し、prompt縮小を実処理の速度改善へ換算しない。

## 証拠検査・伝送を軽量化するとき

[短縮伝送と証拠一括検査](../shared/contextbase-runtime/docs/短縮伝送と証拠一括検査.md)に従う。operation首尾の全snapshot確認と各evidenceの精確検査を維持し、compactは同taskのbindingだけで正規化する。alias展開で業務内容や未知を補わない。全原文を保持した現機構と、未実装のオンデマンド調査ループを区別する。
