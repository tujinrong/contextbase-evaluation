<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"SP2-BUILD-REPORT","version":"1.4","path":"sample-project2-build-report.md","sheets":[{"heading":"実行条件","kind":"GRID","sheet":"01_実行条件"},{"heading":"工程の状態","kind":"GRID","sheet":"02_工程の状態"},{"heading":"検証の範囲","kind":"GRID","sheet":"03_検証の範囲"}]} -->
# sample-project2 再生成報告

2026-10-30。実行ID `sp2-ui-regenerate-20261029`。利用者の依頼に従い、Access・CSharp_ASPNETを基本設計→詳細設計→実装の順に再生成している。基本設計と詳細設計は独立レビューを完了し、現在は実装・今回候補の検査を進めている。完成版のUI合格・配布確定は未完了。最新の工程状態は[実行記録](sample-project2/build/generation/pipeline.json)を参照する。

## 実行条件

|項目|内容|
|---|---|
|対象|sample-project2 / Access・CSharp_ASPNET。要件定義工程は再実行せず、確定済み条件を引き継ぐ|
|変更範囲|UI品質規約に沿うレイアウト、画面状態、操作の改善。認証・業務条件・表構造・既存データを保持|
|配置|仕様は各specRoot、ソースは各sourceRoot、最終成果物と今回の検査は固定build/、試行は.tmp/、履歴はGit|
|認証|各方式のQA-025 / DEMO認証条件を継承。既存利用者・ソルト付き検証情報を保持|
|品質|high / 改善3cycle。旧実行や旧成果物のPASSを今回の合格へ転記しない|

## 工程の状態

|工程|状態|今回の記録|
|---|---|---|
|基本設計|両方式の再生成・独立レビュー完了|[報告](sample-project2/build/basic-design/report.md)|
|詳細設計|両方式の再生成・独立レビュー完了。Webの遷移通信方式はDQA-UI05で技術修正して再確認|[報告](sample-project2/build/detail-design/report.md)|
|実装|進行中。完成版の最終検査・配布確定待ち|[工程記録](sample-project2/build/generation/pipeline.json)|

## 検証の範囲

|項目|状態|
|---|---|
|Access|作業候補のVBAコンパイル・通常11class初期化と45件のAPI回帰を実施。5表48列の既存データ・schemaのtyped digest不変を確認。独立属性検査の寸法差分を修正中。最終成果物の合格は未確定|
|Web|中間コンパイル0警告0エラー。画面・操作処理を実装中。最終publish/専用DB/browser/配布ソース再構築の検査は待機中|
|Access実画面|Windowsロックを確認したため入力を停止。解除の回答待ち。属性・API検査を実描画・実キー・IMEの合格としない|
|帳票|今回実装・PDF等の確認を継続中。旧PH-07の合格を引き継がない|
|最終整合性|今回の最終版が固定されるまでPENDING。旧実行のfinal-integrity PASSは失効|
|正式受入・採点|未実施。formalScore=null|

この文書は作業中の状態を示す。最終配布物・検査範囲は実装完了時に同じ固定パスへ更新する。
