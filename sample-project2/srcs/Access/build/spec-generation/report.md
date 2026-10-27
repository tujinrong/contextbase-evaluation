<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"SP2-Access-GENERATION-REPORT","version":"1.0","path":"sample-project2/srcs/Access/build/spec-generation/report.md","sheets":[{"heading":"対象","kind":"GRID","sheet":"01_対象"},{"heading":"検査","kind":"GRID","sheet":"02_検査"},{"heading":"未実施","kind":"GRID","sheet":"03_未実施"}]} -->
# Access 基本設計の今回記録

版1.0／2026-10-27／runId=sp2-basic-design-initial／stage=basic-design。

## 対象

projectId=sample-project2、methodId=Access。仕様セット1.0、specRoot=sample-project2/spec/Access/、sourceRoot=sample-project2/srcs/Access/。24文書の基本設計一式を新規作成した。入出力ファイル・版・SHA-256は同じディレクトリのmanifest.json、検査はvalidation.json、描画/目視はrender-review.jsonへ固定保存する。

## 検査

文書メタ情報、見出し、LIST、テーブル9列、項目ID、リンク、方式内依存、イベント6見出しを静的検査した。独立レビューの不一致を修正した。Edge headless・1366×768 CSS px・100%で画面6断片（登録2タブを含む）と帳票1断片を描画し、長文/エラーメッセージ差替え3ケースも点検した。画面の横はみ出しはなく、主要操作は通常表示で到達可能。帳票は縦増頁の構成見本である。

対象MDとHTML断片のSHA-256、ブラウザー版、計測と目視対象をrender-review.jsonに記録した。途中のHTML/画像は.tmp/の検査用で、恒久証跡リンクや別の仕様正本にしない。HTMLの表示結果とAccess実部品の制約検証は区別する。

## 未実施

利用者レビュー、詳細設計、物理DB定義、ACCDB/VBA生成、実DB作成/投入、ビルド、Access実機のキー入力/DPI/IME/認証/保存/競合、実Excel生成・読戻し・印刷、正式採点は未実施。formalScore=null。パスワード検証API・初期設定手順・排他・物理型・帳票印刷の具体化はQAの詳細工程残件。前回の検査結果を流用していない。
