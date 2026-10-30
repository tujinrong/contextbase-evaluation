<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"SP2-Access-DETAIL-RESULT","version":"1.1","path":"sample-project2/srcs/Access/build/spec-generation/detail-design/report.md","sheets":[{"heading":"対象と出力","kind":"GRID","sheet":"01_対象と出力"},{"heading":"検査と限界","kind":"GRID","sheet":"02_検査と限界"},{"heading":"実装への引継ぎ","kind":"GRID","sheet":"03_実装への引継ぎ"}]} -->
# Access 詳細設計再生成・技術補正結果

版1.1／2026-10-30。runId=sp2-ui-regenerate-20261029、generationMode=canonical-update、change_scope=ui_behavior。DQA-UI08/09はbuildから担当詳細へ戻した最小技術改訂である。

## 対象と出力

[inputs.json](inputs.json)1.1へ補正前の76入力（自方式spec45、規則19、project配置3、基本記録9）のID/版/SHAを凍結した。直前の詳細manifest SHAはf6ca6e6a9fc6fd82887154d77b65c3dc9cdfb65ab15930b65c39474040e3d659。ソース/ACCDBを業務仕様の代替入力にせず、限定実機確認は技術制約を発見した根拠として区別した。

45正本文書のうち7文書を技術補正し38文書を無変更継承する。物理UI共通1.1、F03/F04/F05詳細1.2、方式別共通01 1.3、詳細QA1.4、方式索引1.12。5画面/6機能/5表48列、既存92項目/17イベント、11pt・氏名3900/カナ4950/日付2250・経歴一覧6300/詳細11580twip、認証/保存/seedは変更しない。要件/基本/元QA/DB定義と8HTML断片は保持する。

DQA-UI08：Accessの非表示Control下端/標準Tab最小帯を踏まえ、F03全文欄を初期330/Hidden、選択時1980/Detail9450へ展開する。F04はTab900/Header2400を余白込みで設計し、Detail設計7920を保持する。測定下限780/Header2145をそのまま期待値へ写していない。親/Tab/Footer固定と通常復帰・下端/キー到達は新候補で再検証する。

DQA-UI09：Excel Footerの小数書式コード&10.5は読戻しに残っても約10pt/.5文字混入となった。限定API/PDF小試験とroot独立確認に基づきFooterだけ整数11ptとし、本文セル10.5/見出し11/表題18を保つ。数字先頭名の書式境界・氏名40字全文/2行・改ページ/印字の確認を引き継ぐ。これは製品帳票/実印刷合格ではない。

## 検査と限界

[validation.json](validation.json)：45文書、164H2、43LIST/586行、10TABLE（論理5/物理5の同48fieldIds）、423参照、基本/詳細92項目/17イベント/各6見出し、8HTMLバイト一致、54DUI、保護26文書を新改訂で再検査した。

[render.json](render.json)と[render-review.json](render-review.json)：現詳細8断片をheadless Edge/1366×768/100%で再描画。基本と同じ静的断片の確認で、改訂したnative Header/Tab/全文欄や実操作を証明しない。[diagrams.json](diagrams.json)は現51図の構文/SVG確認。自己レビューは[design-review.md](design-review.md)、独立の新11候補/76入力SHA確認は[review.json](review.json)へ固定し、[manifest.json](manifest.json)で照合する。

旧build候補5a45b637…e584は全11classコンパイルと全5表typed data/schema保持・45件APIを確認したが、その合格は本改訂後の製品へ転記しない。Windowsロック中のnative描画/キー/IME/clipboard、通常復帰/Tab、TopVisibleEmployeeId捕捉復帰、DPI、製品印刷/実プレビュー、受入/正式採点は別の未完状態でformalScore=null。

## 実装への引継ぎ

[handoff.md](handoff.md)へ採用値と新検査、未実装/未検証を記した。buildはこの再固定manifestから通常preflightを再実行し、独立UI契約を新ID/版/SHAへ再固定してから新候補を測る。過去の属性/描画/API/印刷PASSで新候補を代表させない。UI gateの未実施/FAILを強制的にPASSへ変えない。
