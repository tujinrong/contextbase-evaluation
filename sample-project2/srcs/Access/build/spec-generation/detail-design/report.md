<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"SP2-Access-DETAIL-RESULT","version":"1.2","path":"sample-project2/srcs/Access/build/spec-generation/detail-design/report.md","sheets":[{"heading":"対象と出力","kind":"GRID","sheet":"01_対象と出力"},{"heading":"検査と限界","kind":"GRID","sheet":"02_検査と限界"},{"heading":"実装への引継ぎ","kind":"GRID","sheet":"03_実装への引継ぎ"}]} -->
# Access 詳細設計再生成・技術補正結果

版1.2／2026-10-30。runId=sp2-ui-regenerate-20261029、generationMode=canonical-update、change_scope=ui_behavior。今回の限定技術改訂はDQA-UI10。

## 対象と出力

[inputs.json](inputs.json)1.2へ76入力（直前詳細出力の自方式spec45、規則19、project配置3、基本記録9）のID/版/SHAを固定した。原生成gitHeadと今回改訂のGit文脈を別記し、前回入力/詳細manifestのSHAも保持する。ソース/ACCDBは業務入力にせず、Rootのf002診断を候補限定の技術制約の契機とした。

7正本文書を改訂し38文書を無変更継承した。UI共通1.2、共通実装1.4、F03/F04詳細1.3、F06詳細1.2、詳細QA1.5、方式索引1.13。6論理Comboへ専用TextBox6/標準付属Label6を設計し、既存127Controlから139Control/付属Label38となる。既存92項目/17イベント・5画面6機能5表48列・8HTML、11pt・確定入力幅・認証/保存/seed・DQA-UI08/09は不変。

Combo.Textで候補外rawを再表示する旧方式と3共有面の草案を廃し、6面の同時Pending/個別Page/文字編集・元Label置換・右矢印・自然Tab/逆Tab・明示候補選択・No/Yes範囲・MSG016ガードへ具体化した。L/T/Hは採用済み元Combo、Wは元W−360twip、Labelは元矩形を使い、製品実測から期待値を逆算していない。F06 Caption「分類」は基本HTMLと一致するnavigation表示例外で、必須/正常候補制約を変えない。

## 検査と限界

[validation.json](validation.json)：45文書、164H2、43LIST/587行、10TABLEの同48fieldIds、427参照、基本/詳細92項目/17イベント/各6見出し、8HTML厳密一致・54DUI＋Pending追加9条件・保護26文書を現SHAで再検査した。6面/6Labelの固定名/矩形式/初期flags/個別対応も静的確認した。

[render.json](render.json)・[render-review.json](render-review.json)は前回の8静的断片のハッシュと今回の完全同一性を結び、再描画未実施を明記する。新Pendingのネイティブ画面を描画した記録ではない。[diagrams.json](diagrams.json)は51図の内容ハッシュ不変を確認し、旧構文/SVG結果を同一図の範囲に限定する。本文改訂や新製品の動作へ合格を転記しない。

自己レビューは[design-review.md](design-review.md)、Rootが7文書の本文・Caption・Page focus・複数Pending・Tab/工程順を確認した独立意味レビューは[review.json](review.json)。実部品/新候補/実キー/IME/clipboard/倍率/DB/Excel/印刷・正式受入/採点は本工程未実施、formalScore=null。

## 実装への引継ぎ

[handoff.md](handoff.md)に6ownerの物理名/所属/寸法/字体/状態・守る保存境界と新検査を記した。Rootの仕様freeze後、build担当が通常preflightで新入力を固定し、そのSHAに監査担当がUI期待値を独立改訂/Rootレビューする。その後だけ作者が製品実装/新候補検査へ進む。旧UI契約・旧manifest・旧候補のPASSを新候補へ付け替えない。UI gate未完を本設計のPASSで埋めない。
