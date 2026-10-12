# RPG 部分生成・中断記録

記録日: 2026-10-12。対象: `test-project1`、build 工程。状態: **仕様の構造問題により全方式の生成を中断。RPG は部分生成であり、実装完了・ビルド成功・仕様適合ではない。**

root が確定した停止理由: Access DB 定義 7.2 の `spec/DB定義/Access/01_DB定義書.md` L38/L73 が要求する複合 FK と、同テーブル分冊 `テーブル/01_m_student.md` L46 の固定 NOT NULL `relationship_category` / L47 の任意 NULL `relationship_code` の組合せは、今回の通常のACE/DAO FK構成において部分 NULL を 3201 で拒否した。緊急連絡先3項目の全部未設定という業務契約をこの構成で永続化できない構造適合問題 STR-ACCESS-001 である。代替索引設定は未検証であり、Access全般で絶対に不可能という判定ではない。この再現・確定は root 側の検査による。RPG 担当が Access を独自に再実行した結果ではない。ユーザーの「構造的な問題は report に報告して中断」に従い、新規実装・仕様訂正・ビルドを停止し、別 Agent の仕様修正を待つ。

中断後の担当書込みは本報告のみ。既存 RPG 部分生成物と legacy 担当生成の database は保存し、再生成・修正していない。spec-eval 本文は未読。

## 入力版と検査範囲

| 入力 | 文書ID・版 |
| --- | --- |
| 詳細仕様書/AS400_RPG/01_学生検索画面.md | DET-AS400_RPG-SCR-STU-001 / 7.3 |
| 詳細仕様書/AS400_RPG/02_学生登録画面.md | DET-AS400_RPG-SCR-STU-002 / 7.0 |
| 共通/方式別/AS400_RPG/01_共通実装仕様.md | COM-AS400_RPG / 7.0 |
| docs/開発規約/AS400_RPG.md | DOC-E461E85A4485 / 7.0 |
| 共通03/04/06/07/08/09/11 | COM-STU-003/004/006/007/008/009/011 / 7.0 |
| 共通05/10 | COM-STU-005/010 / 7.3 |
| DB定義/Db2_for_i/01_DB定義書.md | DBDEF-DB2_FOR_I / 7.2 |
| Db2_for_i の6テーブル分冊（学生、クラス、分類、コード、履歴、ゲート） | DBDEF-DB2_FOR_I-* / 7.2 |

方式別の DS / 64bit ID / NULL 標識 / Unicode スカラー長 / 和暦4原入力、Db2 固定列、ゲート、確認待ちの解放、候補全件検査、原値保持の責務を読取りで確認した。RPG 固有の確定した構造ブロッカーはこの範囲ではなかった。ただし文書事前監査は実装適合検査の代わりではなく、全方式の停止理由を解除しない。過去の文書検査合格を今回の実装検査として流用していない。

## 保存した部分生成物

以下は `test-project1/srcs/AS400_RPG/` からの相対パス。RPG 担当の生成物は19ファイル。ソース本文は存在するが、単体・結合・コンパイル試験は未実施。

| ファイル | 仕様ID・生成範囲 |
| --- | --- |
| src/STUCOMMON.sqlrpgle | 共通01～05、16/17。ジョブ主体とグループによる認可、UTC/業務日、初期検査、原入力正規化、必須・日付・連絡先、厳密な和暦境界、和暦表示、LIKE エスケープ、hash、メッセージの処理本文 |
| src/STUSVC.sqlrpgle | SCR-STU-001 / EV-SRC / OP-COUNT / OP-PAGE、SCR-STU-002 / EV-REG / UPD、共通06～15。検索のパラメーターバインド、20/50/100件、10001上限判定、条件保持、ゲート、学生読込み、新規/更新/削除、マスタ存在・有効性・定員・期待版・確認・監査の処理本文 |
| src/STUMASTER.rpgleinc | 共通マスタ保守。StMaintainClass/Code の管理者・キー・版・保護・期間・定員・変更なし・履歴・確定単位の本文。STUSVC が COPY する |
| c/STUNICODE.c / c/STUNICODE.h | COM-AS400_RPG Unicode 補助。UTF-16スカラー検査、ICU NFKC・大文字化、カナ、番号・郵便・電話・メール、CCSID厳密変換、明示エスケープ、SHA-256 の C ABI 本文 |
| copy/STUTYPES.rpgleinc | StudentRaw / StudentWork / StudentRecord / SearchRaw / SearchCriteria / SearchContext / Confirmation / Result / マスタ命令の qualified DS、int(20)、NULL 標識、結果定数 |
| copy/STUPROTO.rpgleinc | 共通/サービス/C ABI/画面呼出しのプロトタイプ。StEdit の外部プログラムは未生成 |
| copy/STULOAD.rpgleinc | OP-STUDENT / REG。全19業務列と照合値2の明示 SQL ホスト変数読込み |
| copy/STUINSERT.rpgleinc | UPD。新規19入力・照合値2・固定分類・作成更新・版1の固定割当 |
| copy/STUUPDATE.rpgleinc | UPD。番号を除く18入力・照合値2・更新/版、ID+期待版+非削除条件 |
| copy/STUNORM.rpgleinc | 共通04/05、REG。19入力の raw 上限検査、正規化、NULL 標識、和暦生成、照合値再生成の固定割当 |
| copy/STUHASH.rpgleinc | 共通11。正規化された19業務値を NULL と値長で区別して hash に入力する割当 |
| copy/STUCHANGED.rpgleinc | 共通14 / UPD。変更した物理列名だけの監査 JSON 配列生成 |
| copy/STUTORAW.rpgleinc | REG-005 / EV-REG-002。DB 原値から画面 raw 値への移送。表示変換による置換値を保存入力にしないための割当 |
| copy/STUEDITIO.rpgleinc / copy/STUEDITOUT.rpgleinc | REG / UI 移送の固定呼出し列。呼出先 ReadEdited/Render と DDS は未生成のため、画面として動作しない |
| metadata/field-map.json | REG / UPD / CHK / N。19項目の順番、物理列、RPG型、raw/保存長、正規化方式、DDS名の対応 |
| tools/generate_sources.py | COPY、固定割当、項目対応の生成器。中断前に実行済み |
| tools/correct_messages.py | 共通05との結果メッセージID対応修正。中断前に実行済み。中断後は再実行していない |

legacy 担当の既存出力として `database/schema.sql`、`schema.json`、`seed.sql`、`seed.json` の4ファイルを確認した。RPG 担当はこれらを変更しておらず、実DBに実行していない。

## 本文を生成した処理と完了の境界

処理本文として、業務保存と監査の同一確定単位、保存後の直前 IDENTITY 取得、論理削除に編集 raw 値を渡さない入口、照合候補の ID/版を全件走査して20件表示と分離する hash、利用者/ジョブ/画面/対象/版/全業務値/全候補/10分期限を結び付ける確認 DS を記述した。確認中の画面待ちを Tx 内へ置く画面コードはまだ生成していない。

これらは「本文生成済み」の範囲であり、完成した実行オブジェクトではない。COPY と C ABI の処理系適合、バインドとプログラムの参照閉鎖、全チェックとメッセージの対応の最終検査は途中で停止した。既知の残件として、STUSVC L107 の終了区分訂正拒否に残った `E-COM-001` は認可拒否の `E-COM-002` への見直しが必要。StMessage は一部のみ具体文言があり、全58件の文言・置換パラメーター・画面項目エラー表示の完成は未了。構造問題による停止後はこれらを修正していない。

## 未生成・未実装

- STUSRCH / STUEDIT の画面プログラム、DDS STUSCHD / STUEDTD、COND/SFLCTL/SFLROW/EDBASE/EDENROLL/EDNOTE/CNFRM/LONGTXT。READC と RRN→ID、全11表示列の横/全文表示、Fキー、権限による UI 制御、入力保持、編集取消・再読込・破棄確認は未実装。
- C 補助を使う5250表示アダプター、変換不能文字の注意と原Unicodeの保持、通常入力でエスケープを解釈しない制御、F8 の明示 Unicode 入力、長文全範囲編集の画面実装。C にエンコード/デコードの本文はあるが、画面から利用できない。
- STUMNT の固定承認 IFS ファイル読込み・形式検査・結果表示。StMaintainClass/Code の処理本文はあるが、保守投入プログラムは未生成。
- STUBND のバインダー署名、BNDDIR、DDS/C/SQLRPGLE の CL ビルド・配備、activation group/CCSID/暦版/有限ロック待ちの設定、ジャーナル開始、最小権限の所有者・採用権限・直接 DML 制限、承認済み認可設定の配備。
- README、起動設定例、実機試験資源、PROGRAM/EXPORT/COPY/DDS/CL 全参照の閉鎖検査。COPY に未生成 UI 呼出しが残ることを確認しており、自己完結するパッケージではない。

## 未コンパイル・未試験

Windows 上で Python 生成器の実行とファイル/手続き定義の列挙を実施した。IBM i の CRTSQLRPGI / CRTDSPF / ILE C コンパイラーは使っていない。C コンパイラーもこの担当環境で見つからず、STUNICODE のビルド・リンク・SHA試験を行っていない。IBM の ICU Option 39 と RPG UTF-16型/SQLホスト変数の資料は参照したが、資料参照は実機検査結果ではない。

未実施: Db2 DDL/seed 実行、全表ジャーナルとコミットメント定義、起動、業務 CRUD/マスタ/監査の往復、DAO以外のこの方式の実DB検査、2ジョブ競合・最終席・版・確認期限/候補変更・異常終了 rollback、5250 27×132/SFL10行と20/50/100件、CCSID/補助漢字/絵文字/結合文字/全長/エスケープ往復、ジョブ権限と直接 DML 制限、性能。

中断時の主要ソース SHA-256（本報告作成前の読取り計算）:

| ファイル | SHA-256 |
| --- | --- |
| src/STUCOMMON.sqlrpgle | 381AF09B4DB4C964C90A7556DD87261E2F3E1F73CA176CF83F659076C8C14933 |
| src/STUSVC.sqlrpgle | A6FA558960341888B44176C9BE47D1521C2528FBC0FD7EAD5A157CC54A51D374 |
| src/STUMASTER.rpgleinc | 3C273ADD4EC2526DB7AE80EF0FFE2E2B25FFDA385AF4AA651668846DDBE5CB33 |
| c/STUNICODE.c | 264D7057BE56559A52C95841009EB9EF787A46AC9EAC0066CE78BF993B7F05F9 |

資料: [IBM i ICU APIs](https://www.ibm.com/docs/en/i/7.5.0?topic=category-international-components-unicode-apis)、[RPG UCS-2/VARUCS2](https://www.ibm.com/docs/en/i/7.4?topic=type-ucs-2-format)、[Db2 PREPARE](https://www.ibm.com/docs/ssw_ibm_i_74/db2/rbafzpreph2.htm)、[IBM i group profile entries](https://www.ibm.com/docs/ja/i/7.5.0?topic=services-group-profile-entries-view)。
