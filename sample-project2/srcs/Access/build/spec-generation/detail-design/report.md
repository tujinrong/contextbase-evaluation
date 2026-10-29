<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"SP2-Access-DETAIL-RUN","version":"1.0","path":"sample-project2/srcs/Access/build/spec-generation/detail-design/report.md","sheets":[{"heading":"入出力と成果物","kind":"GRID","sheet":"01_入出力と成果物"},{"heading":"文書と描画の確認","kind":"GRID","sheet":"02_文書と描画の確認"},{"heading":"採用判断と未実施","kind":"GRID","sheet":"03_採用判断と未実施"}]} -->
# Access 詳細設計の今回記録

版1.0／2026-10-29。projectId=sample-project2、stage=detail-design、generationMode=canonical-update、AG-DETAIL-DESIGN 1.1。

## 入出力と成果物

[方式別一覧](../../../../../spec/Access/README.md)から詳細6機能、方式別共通1件、DB総則/5TABLE、開発規約、詳細設計QAの15新規文書を参照できる。各新規文書は1.0。基本設計と同じ83項目・17イベントを物理部品/変数/型・API/引数戻り値・SQL/パラメーター・期待件数・確定/取消・CHK/MSGと復帰へ対応付けた。基本5表48論理項目を維持した物理DB定義は設計文書で、実DBへ適用していない。

入力は同方式内の要件定義書1.0・基本設計・QA・プロジェクト情報・共通・論理TABLE・採用規約。対象25文書のID・版・SHA-256と今回の出力は[manifest](manifest.json)に固定。既存の要件/基本/共通/QAを編集せず、詳細工程の採用と残件は詳細設計QAへ分けた。

## 文書と描画の確認

spec-meta/LIST/TABLE9列・fieldIds、リンク/方式内依存、基本との全項目/イベントID、物理型/NULL/長さ/キーを検査してPASS。画面/帳票HTMLは基本と同じ断片をLF正規化後に照合した。今回のMDから再抽出し、Edge 156.0.4314.42で21静的画面/帳票モックケース、Mermaid 12.2.0で23図を解析・描画した。抽出方法、MD/断片/画像ハッシュ、サイズ/倍率/計測と目視したサンプルは[描画記録](render-review.json)へ残した。

通常/狭幅は正本モック、エラー/空/未選択/参照/長文は状態又は値だけを一時DOMへ適用した静的fixtureである。後者は実装側の状態遷移・入力制限・権限を実証しない。描画の成功と、基本との配置一致・業務意味・実機動作を分ける。

作成担当が自己確認し、独立担当/root/req_desktopが原要件/基本/QAと新しい詳細/共通/物理DBを横断レビューした。指摘修正後の文書ハッシュを固定し、rootが最終構造/参照/保全検査を実行した。[検査結果](validation.json)の状態は文書工程に限定される。

## 採用判断と未実施

認証・API・排他・物理型・帳票生成/保存・初期設定手段は詳細工程の設計採用として具体化した。既存の200社員/20経歴/2シート等の設計採用、利用者確定と未承認の区分を継承し、新たな利用者承認として扱わない。社員削除や独立監査表を追加せず、経歴明示除去/親子全体保存/最終監査属性を維持した。

採用APIの動作・実機DPI/IME・DAO/SqlClient・実DB制約・競合/性能/回復・実Excel/印刷は未実施であり、詳細設計QAの受渡し条件に残す。アプリ実装・ACCDB・DB作成/接続/投入・仕様書Excel/PDF変換・利用者受入・正式採点も未実施。formalScore=null。既存の要件逆生成/基本設計のbuild記録は上書きしていない。
