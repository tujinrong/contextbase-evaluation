<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"SP2-Access-DETAIL-QA","version":"1.6","path":"sample-project2/spec/Access/詳細設計QA.md","sheets":[{"heading":"適用と決定","kind":"GRID","sheet":"01_適用と決定"},{"heading":"採用と残件","kind":"LIST","sheet":"02_採用と残件","key":["QA-ID"]},{"heading":"工程状態","kind":"GRID","sheet":"03_工程状態"}]} -->
# Access 詳細設計QA・技術採用

版1.6／2026-10-30。stage=detail-design、generationMode=canonical-update。DQA-UI10の物理補助面を詳細採用する。

## 適用と決定

[既存QA](QA.md)と[要件](要件定義書.md)を保全し、QA-015～017を実装可能な契約へ詳細化する。詳細の技術採用は設計者判断であり、利用者の新たな承認でもAPI／DB／Officeの実証結果でもない。社員削除なし、5表、F01～F06のIDと業務値、認証あり、親版・明示経歴除去・200/20/99上限・SP2-DEMO-01を維持する。

## 採用と残件

| QA-ID | 既存対応 | 採用／残件 | 状態・確認条件 | 正本 |
| --- | --- | --- | --- | --- |
| DQA-A01 | QA-015、F01 | Windows CNG PBKDF2-HMAC-SHA256、600000反復、salt32byte／鍵32byte、ASCII版付きhex形式、64bit VBA PtrSafe/LongPtr/LongLong | 設計採用。Win64 ABI、パスワードUTF-8完全往復、既知vector・実速度・メモリー残存は未検証。QA-025の公開DEMO値以外の実秘密を配布せず、形式異常は認証失敗へ閉じる | [共通実装](共通/方式別/01_共通実装仕様.md) |
| DQA-A02 | QA-015・022、F01/F04/F05/F06 | ACCDB正規絶対パス由来Global mutex、UIメッセージ待ち最大10秒、private DAO Workspace、短い全体確定／一貫読取 | 設計採用。同一Windows実行主体・同端末2プロセスが対象。mutex DACL、同一ファイル別名、破棄mutex整合確認、DoEvents再入なし・Commit成否不明は実機未検証 | [共通実装](共通/方式別/01_共通実装仕様.md) |
| DQA-A03 | QA-015、T01～T05 | ACE実型、一般UnicodeのTEXT容量最大2単位/scalar、長文LONGTEXT、48元項目・原fieldIds、業務長独立検査 | 設計採用。Parameter.Type読取専用を踏まえ長文はtyped-key QueryDef＋同Workspace dynaset.Fields.Valueで書込む。Unicode補助文字・1000scalar・Null・ValidationRule・FK・採番を実ACEで未検証 | [DB定義](DB定義/Access/01_DB定義書.md) |
| DQA-A04 | QA-016、F05 | 専用Excel instance、明示テキストセル、全件全文読戻し、保存先内要求専用一時.xlsx、最終再認可、MoveFileExWで完成名へ確定 | 設計採用。実OfficeのFont/AutoFit/ページ境界、元改行／結合文字の復元、同名の外部変更競合、共有先filesystem・権限・容量不足・電源断時の失敗原子性は未検証。未完成物を最終名へ保存しない | [F05](詳細仕様書/05_経歴書出力.md)、[共通実装](共通/方式別/01_共通実装仕様.md) |
| DQA-A05 | QA-015、SP2-DEMO-01 | 新規stagingだけへの単一Tx投入・外部manifestによる所有確認は維持し、標準DEMOはQA-025の固定資格情報を採用。既存frmLoginの対話初期設定は明示モードだけ | 設計採用。5画面を追加せず配布時初期設定モードは無効。元の3分類9コード2利用者3社員3経歴と基準日を維持し、投入／再投入・既存編集保持は未実施 | [初期確認データ](共通/06_初期確認用データ.md)、[共通実装](共通/方式別/01_共通実装仕様.md) |
| DQA-A06 | QA-017 | Access Formの原点・Twips/pt・96DPI換算、標準未連結部品と明示DTO、基本HTML同一断片 | 設計採用。1366×768モックと実Accessの外枠/DPIを区別。125/150%・IME・Tab・MaxLengthに依存しないscalar入力・実ListBox全文到達は未検証 | [共通実装](共通/方式別/01_共通実装仕様.md)、各詳細 |
| DQA-A07 | QA-017、REQ-N-005 | 200社員／4000経歴／同時2人、検索2秒・Excel5秒、Office起動／手動保存除外を継承 | 目標案・未測定。機器／Office版／測定分位と判定基準は実装時に記録し、詳細の存在を達成済みにしない | [日付・データアクセス](共通/05_日付・データアクセス仕様.md) |
| DQA-A08 | QA-REQ-OPERATIONS | 保持期間、復旧時間／復旧点、配布後の運用責任、バックアップ保管先 | 未確定を継承。詳細で具体値を創作せず、稼働前に利用者と採用範囲を決定する。復元／障害注入も未実施 | [要件](要件定義書.md)、[既存QA](QA.md) |
| DQA-UI01 | 2026-10-29利用者追加指示、QA-017 | クラシックな標準Access部品、全text部品Yu Gothic UI11pt、項目別Twips、標準入力補助と共通適合検査を採用 | 利用者確定。生成と最終ACCDBの実測・実入力は今回のbuild記録で確認し、過去のPASSを流用しない | [UI生成条件](規約/UI生成条件.md) |
| DQA-AUTH01 | QA-025、F01、SP2-DEMO-01 | 利用者確定のadmin/staff・共通123、最小3/最大128、新規seed1.1、既存2利用者の認証移行 | 利用者確定。CNG/600000・役割・内部IDと業務行を維持し、実適用/認証結果は今回build記録で確認する | [DEMO認証条件](規約/DEMO認証条件.md) |
| DQA-UI02 | QA-026/027、共通09、F04 | FormHeaderにタイトル/親/標準Tabの空Page2つ、Detailに論理Pageの入力群、Footerに全体保存/取消。各Section別原点/属性/Resize・focus退避/再入抑止を選定 | 設計採用。実親と論理所属を分離し、Tab切替拒否で旧Page/raw/focus保持。2165回避・空Page→Detailキー・下端Tab可視性はbuild最初の実Formで未検証 | [UI部品・状態・検査契約](共通/方式別/02_UI部品・状態・検査契約.md) |
| DQA-UI03 | QA-027、F03/F06 | native非client帯を確保しF03部署列を220→198px相当、F06名称列293→268px相当へ配分。氏名3900/カナ4950/日付2250twipとF04一覧420pxは維持 | 設計採用。基本/詳細HTMLは同一で、native物理列との差を明記。F03-I09 readonly全文部品1980twip高＋内部scroll、F06右欄から最大長をキー/コピー確認。実scroll帯/行高は未検証 | [UI契約](共通/方式別/02_UI部品・状態・検査契約.md)、F03/F06 |
| DQA-UI04 | QA-028、DQA-A04、F05 | 手動改ページと可読サイズを両立するためZoom100/FitTo無効、横480～504pt/24列・縦720pt以内の実行高予算、HPageBreaks.Addで継続見出しを配置 | 設計採用。Microsoft一次資料を2026-10-29確認。各列3.0相当は初期近似、実ポイント幅で調整。実Excelの全件全文/印刷/境界が揃うまでPH-07は未検証 | [F05紙面契約](詳細仕様書/05_経歴書出力.md) |
| DQA-UI05 | QA-026、F01/F03/F04/F06 | 非連結TextBoxの不正rawを画面状態へ保ち、BeforeUpdate一律Cancelで閉じ込めず検索/反映/保存の中央検査で拒否。Password以外のInputMask/Formatは空 | 設計採用。受理上限/保存条件は不変。未完成番号/年月・過長値から取消/継続/保存拒否、Date/Integerへの失敗変換なし、busyのfocus所有Control例外と状態復帰を実キーで未検証 | [UI契約](共通/方式別/02_UI部品・状態・検査契約.md)、共通実装 |
| DQA-UI06 | QA-026、共通09、F03 | clsSearchReturnStateでraw4条件/検索状態/applied有無/結果/選択/位置/focusを別保持。取消は検索0、保存成功はraw同条件を再検査再検索 | 既存Access契約の詳細化。未検索/条件変更後からの新規取消、空白/全半角/大小保持、保存後raw不正でも保存成功維持を実機で未検証。他方式へ自動展開しない | [F03](詳細仕様書/03_社員検索画面.md)、UI契約 |
| DQA-UI07 | DQA-UI05、F03/F04/F06 | LimitToListを維持しNotInListでNewDataを別保持、acDataErrContinue＋当該Control.Undoでfocus拒否を解く。候補外rawの再表示はDQA-UI10の同一論理欄専用TextBoxへ移し、Combo.Text setterによる復元を廃止 | 設計採用。未知候補を追加/保存せず中央検査で拒否。UndoはControl表示だけの例外。Noの原文字可視/修正、Yes破棄、Esc、Timer復帰と認証期限非延長は新候補で再検証 | [UI契約](共通/方式別/02_UI部品・状態・検査契約.md)、Microsoft一次資料 |
| DQA-UI08 | DQA-UI02/03、独立build checkpoint2 | Accessは非表示Control下端もSection保存最小高に含み、標準TabにPage帯の最小高がある。F03全文欄を初期330twip/非表示・選択時1980/Detail9450へ展開。F04はTab900/Header2400を余白付きで再設計し、Detail7920キャンバスを維持する | 現候補5a45b637…e584の独立DesignViewでDetail9090、Tab780/Header2145を確認したことが改訂契機。最小実測値への追従ではなく固定領域の必要余白/スクロールを設計。新候補の属性・通常復帰/下端・全文キー/コピー・固定Footer到達は再検証。基本8HTML/11pt/入力幅/保存/DBは不変 | [物理UI契約](共通/方式別/02_UI部品・状態・検査契約.md)1.1、F03/F04 |
| DQA-UI09 | DQA-UI04、F05、Excel限定API/PDF小試験 | Excel CenterFooterの小数サイズコード&10.5はreadbackに残っても印字が約10ptかつ先頭に.5を出すため、Footerだけメイリオ整数11ptを採用。本文セル10.5/見出し11/表題18を維持し、氏名最大40字の1行＋他情報1行、数字先頭名のコード区切りを検査する | 現Office限定の小試験を作者とrootが独立PDF確認。&11は約11.04ptで余計な字なし。証拠はsourceRoot/build/test-results/independent-print-format.json（productPass=false）。製品帳票/実プレビュー/実印刷のPASSではなく、新候補の全文/継続/横1頁/非重なりを再検証 | [F05紙面契約](詳細仕様書/05_経歴書出力.md)1.2 |
| DQA-UI10 | DQA-UI05/06/07、F03/F04/F06、native f002診断 | Combo.Textによる候補外復元の2101を避け、6論理Comboごとに標準unbound TextBox＋標準付属Labelを固定対応で追加（12Control）。元L/T/H・W−360twip、Labelは元同Caption/矩形、全件11pt、初期hidden。F03部署/在籍、F04基本部署/在籍・経歴役割、F06分類。各Form1組計3組の共有案は複数Pendingを同時表示できないため撤回 | 詳細設計採用。既存の論理項目/8HTML/92項目/17イベント・LimitTrue/Bound1/正常候補・AcceptedCodes/F06 AcceptedCategory・保存/DB不変。Raw/Pendingだけ編集し全件表示、正常候補の明示選択だけ当該Pendingを解消。MSG016検索/反映/保存0、Noは原文/焦点、Yesは承認範囲だけ。自然Tab/逆Tab・AltDown/F4・Esc・Page/Busy・同時Pending・可視編集/末尾空白を独立期待値→新候補nativeで再検証。shadow保持だけを合格にしない | [物理UI契約1.2](共通/方式別/02_UI部品・状態・検査契約.md)、共通実装1.4、F03/F04詳細1.3/F06詳細1.2 |

| DQA-UI11 | 2026-10-30利用者追加指示、全Form/Tab/Dialog | タイトルが小さい、文字サイズとTextBox高が合わない指摘を横展開する。AUI-05a～05bの役割階層と実行高/余白/境界の組合せを採用し、旧タイトル11ptを維持する指定は再設計対象とする | 利用者の変更指示確定。Agent規約へ反映済み。基本/詳細の全画面・モック・寸法・期待値と製品への全面反映は未実施、後続再設計で実施する。本文11ptの維持とタイトル11ptの維持を混同せず、既存候補を新規約適合としない | [Access品質規約](../../../docs/Access画面品質規約.md)、共通UI/物理UI契約の次回改訂 |
| DQA-ENC01 | 2026-10-30利用者追加指示、全VBA/固定文言/MSG | 日本語VBAテキストはCP932（Windows版Shift-JIS、BOMなし）。文書/JSON/PythonのUTF-8、Form native exportのUTF-16 BOM、VBA String/DBのUnicodeは維持。ホストACPに依存しないASCII/ChrW輸送、厳密往復、変換不能時停止を採用する | 利用者指示に基づく文字コード修正。現在ホストACP936で33モジュール意味一致・11文字列の実行/再取込み・5Form文言・4MSGを限定確認。対象版/範囲はsourceRoot/build/test-results/japanese-encoding.json。ACP932の別Windows環境・VBE自体の日本語UI・全画面操作の合格へ拡張しない | [開発規約](規約/開発規約.md)、[Access品質規約](../../../docs/Access画面品質規約.md) |

## 工程状態

初版で作成した詳細/物理設計/QAを継承し、今回はrunId=sp2-ui-regenerate-20261029のui_behavior差分だけを更新する。基本の採用値/54条件を全6機能詳細・方式別共通・開発規約・本QA/入口へ同期する。要件/基本/元QA・認証/業務/seedを変更せず、物理DBは5表48列/キー/型の設計整合点検のみ。SQL/VBAのシグネチャや処理説明を記してもソース/DDL/ACCDB/実Excelを生成・実行した意味ではない。

構造・原ID・リンク・HTML同一性・自己／独立レビュー・描画・実機・実DB・実Excel／印刷・利用者受入・正式採点を分ける。検査は対象版ハッシュ付きのsourceRoot/build/spec-generation/記録に従い、実行試験は未実施、formalScore=null。後工程は別の実行指示を要する。

2026-10-30のDQA-UI08/09はbuildで見つかったネイティブ制約を担当詳細へ戻した最小技術改訂であり、利用者の業務条件や基礎UIの再設計ではない。初回詳細時点の未実施と、その後の候補別build検査を区別し、旧候補の属性/API合格を新候補へ転記しない。

DQA-UI10の改訂契機は、f002の所有native診断で候補外Combo.Text代入がSetFocus成功後/可視Timer後とも2101となり、rawは保持できても入力面が空欄だった事実である。これは一般APIの仕様断定や新TextBoxの合格証拠ではない。期待矩形/字体は従来採用値と360twip予約域の式から設計し、実コード/新実測から逆算しない。spec意味レビュー/freeze→通常preflightで新入力凍結（製品生成なし）→そのSHAへ独立UI期待値改訂/Rootレビュー→製品実装/新候補観測の順とする。期待値の採用根拠を旧入力manifestへ束縛しない。本詳細工程ではsrc/tests/UI契約/ACCDB/DBを更新・実行しない。

F06の元/補助横LabelはともにCaption「分類」（※なし）・幅480twipを採用する。基本/詳細HTMLに一致するnavigation分類用の表示例外であり、編集コードの必須印とは役割を区別する。Null不可/固定3正常候補/採用キー・保存検査は弱めず、字体縮小・幅の実測追従を行わない。
