<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"SP2-Access-GENERATION-REPORT","version":"1.2","path":"sample-project2/srcs/Access/build/spec-generation/report.md","sheets":[{"heading":"対象","kind":"GRID","sheet":"01_対象"},{"heading":"検査","kind":"GRID","sheet":"02_検査"},{"heading":"未実施","kind":"GRID","sheet":"03_未実施"}]} -->
# Access 基本設計の今回記録

版1.2／2026-10-28／runId=sp2-basic-design-item-controls／stage=basic-design。

## 対象

projectId=sample-project2、methodId=Access、仕様セット1.2。specRoot=sample-project2/spec/Access/、sourceRoot=sample-project2/srcs/Access/。機能6文書83項目を11列化し、グループ・コントロール・入力制限・フォーマット・初期値を追加した。DB見出しと文字数の括弧補足を省き、必須とDB関連、業務条件は保持した。QA-019と方式内規約を同期した。

## 検査

項目ID/名称/必須/DB2列を変更前と照合し、初期値・上限・候補・停止/未設定条件の移送を確認した。構造・リンク・DB名対応と独立レビューに未解決指摘はない。現在版の入力/出力ハッシュと検査範囲をmanifest.json、validation.jsonへ更新した。

画面/帳票HTML7断片とMermaid26定義（ER8図を含む）、テーブル5分冊は変更前と同一。render-review.jsonは不変確認を記録し、過去の描画を今回の製品確認へ流用しない。今回、画面や図の再描画は行っていない。

## 未実施

アプリ/物理DB定義の生成、ビルド、DB接続/更新/投入、実Excel生成/印刷、製品の入力/認証/保存/競合・DPI/IME、設計全体の受入・正式採点は未実施。formalScore=null。既存業務と詳細工程の残件を維持し、他projectや並行作業を変更しない。
