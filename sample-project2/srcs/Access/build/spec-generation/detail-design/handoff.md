<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"SP2-Access-DETAIL-HANDOFF","version":"1.2","path":"sample-project2/srcs/Access/build/spec-generation/detail-design/handoff.md","sheets":[{"heading":"固定契約","kind":"GRID","sheet":"01_固定契約"},{"heading":"実装と検査","kind":"GRID","sheet":"02_実装と検査"},{"heading":"未実施と境界","kind":"GRID","sheet":"03_未実施と境界"}]} -->
# Access 詳細から実装への引継ぎ

版1.2／2026-10-30。runId=sp2-ui-regenerate-20261029。DQA-UI10の現版/SHAは[manifest](manifest.json)、Rootの独立意味所見は[review](review.json)。DQA-UI08/09も継承する。

## 固定契約

DEMO admin/ADMIN・staff/STAFF・共通123、3～128scalar、既存ID/役割/業務行、単体ACCDB、5表48列、seed1.1、200/20/99上限、社員全体1Tx・明示経歴除去・結果不明再保存禁止を保持する。基本8HTMLは厳密一致、92項目/17イベント・54DUIを保持し、補助面の9条件を追加する。

物理UI正本1.2、方式別共通01 1.4、F03/F04詳細1.3、F06詳細1.2、詳細QA1.5。既存の11pt・氏名3900/カナ4950/日付2250・入力480/操作510・Form幅18900twipを保持する。F03全文欄の初期330/Hidden→選択1980/Detail9450、F04 Header2400/Tab900/Detail7920、F05 Footer整数11ptも不変。

DQA-UI10は6Comboごとに固定されたTextBoxと付属Labelの12Controlを追加する。F03部署/在籍、F04部署/在籍/役割、F06分類のTextBox名はtxtPending_＋元Combo名、Label名はlbl_＋TextBox名。計139Control/付属Label38・5Form/2Page/15Sectionで、業務fieldや基本論理項目を追加しない。3共有面の草案は撤回した。正本の12行inventoryと6矩形表を実装/期待値の同じ根拠とする。

## 実装と検査

全6TextBox/LabelはYu Gothic UI11pt、初期hidden。TextBoxはunbound、L/T/H=元Combo、W=元Combo.W−360twip、Labelは元同Caption/矩形。F06 Captionは元/補助とも「分類」（navigation横Labelの必須印例外）。Pendingかつowner Page可視の時だけ専用面を同時表示し、元Labelを隠す。元Combo/矢印・LimitTrue/Bound1/正常候補・AcceptedCodes/F06 AcceptedCategoryを維持する。不正rawを正規候補に加えず、補助ChangeはRaw/Pendingだけ更新する。

全Pending表示同期とfocus回復を分ける。通常の移動やTimerで先頭Pendingへfocusを奪わず、No/復帰/中央MSG016だけ指定論理欄へ回復する。既存TabIndexは維持し追加入力を実Section末尾へ固定owner順に採番、Form.KeyDownの正逆Tabで元Combo位置に置換する。Alt+Down/F4/矢印は実候補へ渡し、選ばずEscは原文へ戻る。正常候補の明示選択だけ当該Pendingを消し、同値再選択/開閉だけ/偶然の名称一致を区別する。畳む前は元Combo/可視選択Page.SetFocus/安全Buttonへ退避し、TabControl.SetFocusを使わない。

Search/反映/保存は全Pendingの中央MSG016ガードでサービス/DAO0。F04反映は役割Pendingを拒否し、親Pendingを消さない。Noは全raw/文字/対象/Page/focusを保持し、Yesは承認された親子/明細/コードの範囲だけ破棄。F03新規はPendingも無検証捕捉、無編集取消は検索0で2補助面とも可視復元。保存成功は既存Access契約のraw再検査再検索、Pendingは014＋016/検索0で保存成功を維持する。

全139Control/全管理文字・実Label付属・Section/Page・Enabled/Locked/TabStop・表示/修正可能性・同時Pending・実候補選択・busy・DB再読込を新候補から観測する。原文がshadowに残るだけ/入力面空欄/旧採用値表示は不合格。F05の新候補Excel/PDF/全件全文/継続/横1頁/非重なりは別に再検証し、旧PDFの合格を転記しない。

## 未実施と境界

spec意味レビュー/freeze→通常preflightで新入力凍結（製品生成なし）→そのSHAへ独立UI期待値改訂/Rootレビュー→製品実装/新候補観測の順とする。この詳細工程ではsrc/tests/UI契約/ACCDB/DBを変更・実行しない。通常preflightは後続build担当が実施する。

既存最終ACCDB全5表/資格情報/ID/版を型付きdigest/schemaで保全し、Forms/VBAだけを更新する。fresh source-only再構築は別所有fixture、利用者Officeは触らない。旧候補のnative/PDF/API合格は新候補へ流用しない。IME/clipboard/倍率/最終製品GUI/DB保存再読込/帳票/受入の状態は個別記録とし、未実施をPASSへ変えない。formalScore=null。
