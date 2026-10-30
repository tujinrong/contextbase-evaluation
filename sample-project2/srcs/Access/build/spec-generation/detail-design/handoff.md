<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"SP2-Access-DETAIL-HANDOFF","version":"1.1","path":"sample-project2/srcs/Access/build/spec-generation/detail-design/handoff.md","sheets":[{"heading":"固定契約","kind":"GRID","sheet":"01_固定契約"},{"heading":"実装と検査","kind":"GRID","sheet":"02_実装と検査"},{"heading":"未実施と境界","kind":"GRID","sheet":"03_未実施と境界"}]} -->
# Access 詳細から実装への引継ぎ

版1.1／2026-10-30。runId=sp2-ui-regenerate-20261029。DQA-UI08/09の技術補正を含む現版/SHAは[manifest](manifest.json)、独立所見は[review](review.json)。

## 固定契約

DEMO admin/ADMIN・staff/STAFF・共通123、3～128scalar、既存ID/役割/業務行、単体ACCDB、5表48列、seed1.1、200/20/99上限、社員全体1Tx・明示経歴除去・結果不明再保存禁止を保持する。基本8HTMLは厳密一致、92項目/17イベントと全54DUIを継承する。

UI正本は物理UI1.1、F03/F04/F05詳細1.2。11pt、氏名3900/カナ4950/日付2250、入力480/操作510、Form幅18900、経歴一覧6300/詳細11580twipは不変。F03全文TextBoxは初期330/HiddenでDetail7500、選択時1980/Detail9450、解除はfocus退避後に畳む。F04はHeader基準2400/Tab900/TabTop1365、親Label折返し増分はHeaderへ加え、Detail設計7920は縮めない。

## 実装と検査

新候補で全127Control/15Section/5Form/空Page2/出力Surface/標準Dialog8、全管理文字のFontと実親/論理所属・状態を測る。固定Header/Tab/Footer、空Page→Detail、通常復帰/下端、未反映確認拒否で旧Page/キー/raw/focus保持、2165回避を実キーで検証する。最小native帯の実測を期待値へ転記して通さない。

TextBox rawはString、Password以外InputMask/Format空。Combo accepted code/表示/Pendingを分け、NotInListのNewData捕捉＋表示だけUndo、Noで同raw、Yesで承認範囲だけ破棄。Tab/行/コード切替にもPending拒否を適用する。F03の新規はPendingでも無検証捕捉し、取消は検索0、保存成功だけraw再検査再検索。保存後のPending拒否はF03自身で014＋016を示し、閉じたF04へ例外を返して再保存しない。

F05はZoom100/FitTo無効、各列実幅20～21pt/総480～504pt、頁行高720pt以内、全20経歴/元LF/型/継続見出し/手動境界/横1頁を保存再Openと製品PDF/実プレビューで検証する。Footerだけ整数11pt（本文セル10.5は維持）、40字氏名を1行/残り次行、数字先頭氏名の書式コード誤解釈と&escapeも確認する。APIや小試験PDFだけでPH07を合格にしない。

## 未実施と境界

Windowsロック中はnative操作/代替入力注入を止める。TopVisibleEmployeeIdは宣言だけで完了にせず、先頭可視行と選択を別に捕捉/復帰/観測する。検証できないAPIや選択IDを先頭IDの代替にしない。未実装と未実施を具体的に分け、UI gateは未完のまま維持する。

既存最終ACCDBの全5表/資格情報/ID/版を型付きdigest/schemaで保全し、Forms/VBAだけ更新する。fresh source-only再構築は別DEMO seed、利用者Officeは触らない。旧候補PASSは無効、新候補compile/API/保全/ZIPを完了し、native未検証なら候補を明示して正式outputsを確定しない。正式受入/採点は未実施、formalScore=null。
