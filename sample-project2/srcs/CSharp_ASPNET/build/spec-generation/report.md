<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"SP2-CSharp_ASPNET-GENERATION-REPORT","version":"1.1","path":"sample-project2/srcs/CSharp_ASPNET/build/spec-generation/report.md","sheets":[{"heading":"対象","kind":"GRID","sheet":"01_対象"},{"heading":"検査","kind":"GRID","sheet":"02_検査"},{"heading":"未実施","kind":"GRID","sheet":"03_未実施"}]} -->
# CSharp_ASPNET 基本設計の今回記録

版1.1／2026-10-27／runId=sp2-basic-design-items-db／stage=basic-design。

## 対象

projectId=sample-project2、methodId=CSharp_ASPNET、仕様セット1.1。specRoot=sample-project2/spec/CSharp_ASPNET/、sourceRoot=sample-project2/srcs/CSharp_ASPNET/。項目一覧を6列化し、必須を独立、DBの論理テーブル名/項目名を明記、他属性を備考へ集約した。検索ER/結合条件、社員16+経歴14項目の保存、コード8項目の更新、認証制御・帳票非更新を具体化した。

## 検査

方式内24文書と今回の報告の構造・参照・DB名対応を検査した。機能6文書・83項目のIDと必須/上限等の意味を保持し、DB関連をテーブル分冊の論理名へ対応付けた。独立レビューの重要指摘は修正確認済み。今回の入出力と対象版/ハッシュはmanifest.jsonとvalidation.jsonに記録する。

Mermaid/Edge headlessでER8図を描画した。画面/帳票HTML7断片とテーブル5分冊は変更なしを確認した。画面を再描画・操作したことや実DBの合格とは区別する。render-review.jsonに現在版のERソース/MDハッシュ・描画条件とHTML不変を記録し、一時画像の恒久リンクは残さない。

## 未実施

物理DDL/SQL・アプリ実装・ビルド・DB作成/接続/更新/投入、製品画面の入力/認証/保存/IME/競合、実Excel生成・印刷、設計全体の利用者受入、正式採点は未実施。formalScore=null。詳細工程残件と他projectの並行作業を変更せず、過去の描画PASSを今回の動作結果へ流用しない。
