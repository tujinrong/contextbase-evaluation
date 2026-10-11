<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"REPO-AGENTS","version":"7.0","path":"AGENTS.md","sheets":[{"heading":"対象","kind":"GRID","sheet":"01_対象"},{"heading":"配置","kind":"GRID","sheet":"02_配置"},{"heading":"完了","kind":"GRID","sheet":"03_完了"}]} -->
# 作業Agent向けルーティング

版7.0／2026-10-11。設計・評価基準。アプリ実装・実機試験・逆生成採点は未実施。

## 対象

まずdocsの全体規則とagentsの役割定義を読む。実行要求でprojectIdと工程を確定し、選択projectだけを対象とする。逆生成の評価実行では原仕様・spec-evalへの読取りを許可しない。

## 配置

全体の変更はdocs/agents、題材の仕様はtest-project*/spec、評価はtest-project*/spec-eval。未来のtest-project2を自動作成しない。実装やDB実行を指示されていない段階では設計更新だけを行う。重複は許容、矛盾は修正。

## 完了

入力/出力の版・ファイル・検査範囲・未実施を明示する。過去のレポートの合格を新改訂の検査結果として流用しない。
