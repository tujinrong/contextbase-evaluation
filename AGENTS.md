<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"REPO-AGENTS","version":"7.1","path":"AGENTS.md","sheets":[{"heading":"対象","kind":"GRID","sheet":"01_対象"},{"heading":"配置","kind":"GRID","sheet":"02_配置"},{"heading":"完了","kind":"GRID","sheet":"03_完了"}]} -->
# 作業Agent向けルーティング

版7.1／2026-10-24。生成物の履歴はGitで管理し、最終結果と作業用出力を分離する。

## 対象

まずdocsの全体規則とagentsの役割定義を読む。実行要求でprojectIdと工程を確定し、選択projectだけを対象とする。逆生成の評価実行では原仕様・spec-evalへの読取りを許可しない。

## 配置

全体の変更はdocs/agents、題材の仕様索引はtest-project*/spec、独立方式の原仕様正本はsrcs/方式ID/spec、評価はspec-evalへ隔離する。未来のtest-project2を自動作成しない。実装やDB実行を指示されていない段階では設計更新だけを行う。重複は許容、矛盾は修正。

全方式共通で、最終ソースは所定の正本を更新し、最終配布物・今回の最終検査記録・入出力manifestは各方式のbuild/の固定パスへ更新する。生成日・実行ID・attempt別の過去成果、backup、archiveを累積しない。履歴はGitを使用する。中間生成・失敗試行・コンパイル途中・隔離展開・キャッシュは各方式の.tmp/で処理し、.tmp/はGit管理しない。方式に属さない共通工程だけは担当Agentまたはprojectの.tmp/とbuild/を使う。入力・QA・正式な試験コード・fixtureは中間生成物として削除しない。

## 完了

入力/出力の版・ファイル・検査範囲・未実施を明示する。過去のレポートの合格を新改訂の検査結果として流用しない。
