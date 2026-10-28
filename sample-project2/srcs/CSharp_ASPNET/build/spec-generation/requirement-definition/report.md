<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"SP2-CSharp_ASPNET-REQUIREMENT-RUN","version":"1.0","path":"sample-project2/srcs/CSharp_ASPNET/build/spec-generation/requirement-definition/report.md","sheets":[{"heading":"入出力と範囲","kind":"GRID","sheet":"01_入出力と範囲"},{"heading":"確認結果","kind":"GRID","sheet":"02_確認結果"},{"heading":"残件と未実施","kind":"GRID","sheet":"03_残件と未実施"}]} -->
# CSharp_ASPNET 要件定義書の仕様逆生成

版1.0／2026-10-28。projectId=sample-project2、stage=requirement-definition、generationMode=spec-to-requirements、AG-REQUIREMENT 0.2。

## 入出力と範囲

[要件定義書](../../../../../spec/CSharp_ASPNET/要件定義書.md) 1.0を同方式の既存仕様から作成し、READMEへ入口を追加した。業務根拠は19文書。文書ID・版・SHA-256・適用範囲は[manifest](manifest.json)で固定する。原資料の基本設計・共通・QAを変更していない。

機能要件25、データ要件7、非機能/制約9、受入条件30、未確定事項/引継ぎ7件。既存の利用者確定と設計採用・詳細工程残件を区別し、今回の利用者承認として扱わない。

## 確認結果

構造・LIST・リンク・方式内依存・資料ID/版/ハッシュ・全要件の受入対応を検査してPASS。全41要件に対応する受入条件があり、実施状態はすべて未実施。[検査記録](validation.json)に対象ハッシュと範囲を保存した。

自己確認担当は/root/req_web、独立レビュー担当は/root/req_desktop、最終機械検査担当は/root。社員経歴管理の6機能・5画面・5表、認証あり、社員削除なし・経歴明示除去の全体保存、帳票の整合読取と再認可、定義済み初期データを原資料と照合した。ASP.NET Core MVCとSQL Server、Web側認証/認可、完全生成後のダウンロードと応答開始後の失敗境界を継承。

## 残件と未実施

200社員/20経歴、ADMIN/STAFF、2シート様式、排他10秒等は既存の設計採用として継承。初期データSP2-DEMO-01の3社員/3経歴/2利用者/3分類9コードは定義済みであり、未定義へ戻していない。暗号API・初期設定・物理制約・排他実装・実機印刷等の詳細工程残件は要件書のQAへ引き継いだ。

利用者承認、基本/詳細設計改訂、アプリ、実DB、実Excel帳票/印刷、実機/性能/受入、仕様書Excel/PDF変換、正式採点は未実施。formalScore=null。今回の文書検査を過去の基本設計試験・製品試験の結果へ読み替えない。
