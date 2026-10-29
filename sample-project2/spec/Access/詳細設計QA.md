<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"SP2-Access-DETAIL-QA","version":"1.1","path":"sample-project2/spec/Access/詳細設計QA.md","sheets":[{"heading":"適用と決定","kind":"GRID","sheet":"01_適用と決定"},{"heading":"採用と残件","kind":"LIST","sheet":"02_採用と残件","key":["QA-ID"]},{"heading":"工程状態","kind":"GRID","sheet":"03_工程状態"}]} -->
# Access 詳細設計QA・技術採用

版1.1／2026-10-29。stage=detail-design、generationMode=canonical-update。

## 適用と決定

[既存QA](QA.md)と[要件](要件定義書.md)を保全し、QA-015～017を実装可能な契約へ詳細化する。詳細の技術採用は設計者判断であり、利用者の新たな承認でもAPI／DB／Officeの実証結果でもない。社員削除なし、5表、F01～F06のIDと業務値、認証あり、親版・明示経歴除去・200/20/99上限・SP2-DEMO-01を維持する。

## 採用と残件

| QA-ID | 既存対応 | 採用／残件 | 状態・確認条件 | 正本 |
| --- | --- | --- | --- | --- |
| DQA-A01 | QA-015、F01 | Windows CNG PBKDF2-HMAC-SHA256、600000反復、salt32byte／鍵32byte、ASCII版付きhex形式、64bit VBA PtrSafe/LongPtr/LongLong | 設計採用。Win64 ABI、パスワードUTF-8完全往復、既知vector・実速度・メモリー残存は未検証。固定秘密を配布せず、形式異常は認証失敗へ閉じる | [共通実装](共通/方式別/01_共通実装仕様.md) |
| DQA-A02 | QA-015・022、F01/F04/F05/F06 | ACCDB正規絶対パス由来Global mutex、UIメッセージ待ち最大10秒、private DAO Workspace、短い全体確定／一貫読取 | 設計採用。同一Windows実行主体・同端末2プロセスが対象。mutex DACL、同一ファイル別名、破棄mutex整合確認、DoEvents再入なし・Commit成否不明は実機未検証 | [共通実装](共通/方式別/01_共通実装仕様.md) |
| DQA-A03 | QA-015、T01～T05 | ACE実型、一般UnicodeのTEXT容量最大2単位/scalar、長文LONGTEXT、48元項目・原fieldIds、業務長独立検査 | 設計採用。Parameter.Type読取専用を踏まえ長文はtyped-key QueryDef＋同Workspace dynaset.Fields.Valueで書込む。Unicode補助文字・1000scalar・Null・ValidationRule・FK・採番を実ACEで未検証 | [DB定義](DB定義/Access/01_DB定義書.md) |
| DQA-A04 | QA-016、F05 | 専用Excel instance、明示テキストセル、全件全文読戻し、保存先内要求専用一時.xlsx、最終再認可、MoveFileExWで完成名へ確定 | 設計採用。実OfficeのFont/AutoFit/ページ境界、元改行／結合文字の復元、同名の外部変更競合、共有先filesystem・権限・容量不足・電源断時の失敗原子性は未検証。未完成物を最終名へ保存しない | [F05](詳細仕様書/05_経歴書出力.md)、[共通実装](共通/方式別/01_共通実装仕様.md) |
| DQA-A05 | QA-015、SP2-DEMO-01 | 既存frmLoginの配布前初期設定モードで2利用者の秘密を別々に二度入力、新規stagingだけへ単一Tx投入、外部manifestで所有と再投入を確認 | 設計採用。5画面を追加せず配布時初期設定モードは無効。元の3分類9コード2利用者3社員3経歴と基準日を維持し、投入／再投入・既存編集保持は未実施 | [初期確認データ](共通/06_初期確認用データ.md)、[共通実装](共通/方式別/01_共通実装仕様.md) |
| DQA-A06 | QA-017 | Access Formの原点・Twips/pt・96DPI換算、標準未連結部品と明示DTO、基本HTML同一断片 | 設計採用。1366×768モックと実Accessの外枠/DPIを区別。125/150%・IME・Tab・MaxLengthに依存しないscalar入力・実ListBox全文到達は未検証 | [共通実装](共通/方式別/01_共通実装仕様.md)、各詳細 |
| DQA-A07 | QA-017、REQ-N-005 | 200社員／4000経歴／同時2人、検索2秒・Excel5秒、Office起動／手動保存除外を継承 | 目標案・未測定。機器／Office版／測定分位と判定基準は実装時に記録し、詳細の存在を達成済みにしない | [日付・データアクセス](共通/05_日付・データアクセス仕様.md) |
| DQA-A08 | QA-REQ-OPERATIONS | 保持期間、復旧時間／復旧点、配布後の運用責任、バックアップ保管先 | 未確定を継承。詳細で具体値を創作せず、稼働前に利用者と採用範囲を決定する。復元／障害注入も未実施 | [要件](要件定義書.md)、[既存QA](QA.md) |
| DQA-UI01 | 2026-10-29利用者追加指示、QA-017 | クラシックな標準Access部品、全text部品Yu Gothic UI11pt、項目別Twips、標準入力補助と共通適合検査を採用 | 利用者確定。生成と最終ACCDBの実測・実入力は今回のbuild記録で確認し、過去のPASSを流用しない | [UI生成条件](規約/UI生成条件.md) |

## 工程状態

今回作成するのはMarkdownの詳細仕様・方式別共通・DB物理設計・開発規約・本QAと入口である。SQL／VBAシグネチャ・処理説明を記述しても、ソースファイル・DDLファイル・ACCDB・実Excelを生成／実行した意味ではない。基本・要件・既存共通・元QAは変更しない。

構造・原ID・リンク・HTML同一性・自己／独立レビュー・描画・実機・実DB・実Excel／印刷・利用者受入・正式採点を分ける。検査は対象版ハッシュ付きのsourceRoot/build/spec-generation/記録に従い、実行試験は未実施、formalScore=null。後工程は別の実行指示を要する。
