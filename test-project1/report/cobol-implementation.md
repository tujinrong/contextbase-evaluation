# COBOL 部分生成・中断記録

記録版1.0／2026-10-12。projectId=test-project1。工程=build。担当=COBOL。**状態：全方式の構造問題確定により中断。COBOLは部分ソース生成のみで、実装完了・ビルド成功・稼働可能とは扱わない。**

## 中断理由と範囲

rootから、Access DB仕様7.2の必須複合FK（L38／L73）と学生の固定NOT NULL `relationship_category`（L46）＋任意NULL `relationship_code`（L47）が、今回の通常の実ACE/DAO FK構成でpartial NULLをDAO3201として拒否するという確定報告を受領した。構造適合問題 STR-ACCESS-001 としてユーザー指示「仕様書構造的な問題があれば、reportで報告書、中断」に従い、担当COBOLの追加生成・ソース修正・ビルドを停止した。代替索引設定は未検証であり、Access全般で絶対に不可能という判定ではない。制約回避や仕様の独断修正は行っていない。問題の実測・正確な元仕様パス/行・再開条件はrootの構造問題報告を正本とする。この担当はAccessのDAO実測を行っていない。

中断時点の`srcs/COBOL/`をそのまま保存した。中断後の書込みはこの報告書だけ。既存Web成果物、Webの39件検査結果・両.NETビルド・Vue型検査/bundle・npm監査0件の記録は保存し、COBOLの合格へ流用していない。

## 読取入力

全体docs・agentsの役割定義とbuild-agent契約を読んだ上で、COBOLの検索詳細7.3／登録詳細7.0、方式別共通7.0、COBOL開発規約7.0、プロジェクト共通開発規約7.0、共通03/07/08/09・項目長基準、共通05/10の局所修正版7.3、SQLServer DB定義7.2と関連表を入力にした。SQLServerの名称・型・SNAPSHOT・ゲート・監査・確定境界を参照した。spec-evalは読取・変更していない。入力ハッシュ・セット再固定はrootの生成記録を正本とする。

共有.NETのCoreを短くread-onlyで確認した。検索SNAPSHOT、保存ゲート、全候補取得と版ハッシュ、同一Txで学生/監査/確認消費、raw先行検査・固定コード桁の主要箇所では、短時間の確認範囲で確定した重大指摘はなかった。これは全面レビューや実DB適合試験ではない。rootが検索候補で占有人数を集計しない更新を担当した。Coreはこの担当から変更していない。

## 現存ファイルと仕様対応

| 仕様・責務 | 現存ファイル | 生成状態 |
| --- | --- | --- |
| SCR-STU-001、EV-SRC-001～006 | `cobol/STMAIN.cob`、`STSRCH.cob`、`STSTATE.cob` | CGI振分け、条件正規化、SNAPSHOT件数/ページ、上限・Applied条件・Revision・検索状態の処理を生成。画面出力は未生成 |
| SCR-STU-002、EV-REG-001/002/007 | `cobol/STEDIT.cob`、`STDATEOUT.cob` | 新規値、既存24列読込、和暦4入力への移送、読込時スナップショット・取消・再読込の処理を生成。画面は未生成 |
| EV-REG-004、共通04/05/08/09/13 | `STNORM.cob`、`STVALID.cob`、`STRULES.cob`、`STSAVE.cob` | 19保存項目、生成照合値2、コード/クラス/席増加/期間/旧版/番号不変、変更なし、学生書込/監査/確定の処理を生成。未コンパイル・未実行 |
| EV-REG-005、共通10/11 | `cobol/STDUP.cob` | 全候補ID・版をID順にハッシュ、表示データ最大20、正規化内容/主体/セッション/タブ/対象/旧版/期限照合・原子的消費の処理を生成。確認UIは未生成 |
| EV-REG-006 | `cobol/STDELT.cob` | 専用ID/版/理由/明示確認、管理者、削除属性だけ変更、監査同時確定を生成。専用UIは未生成 |
| 共通01/02/03 | `STAUTH.cob`、`STCLOCK.cob` | CGI信頼環境アダプター、CSRF、POST区別、DB時計/SNAPSHOT診断を生成。本番認証サーバー配備は未生成・未結合 |
| 共通14 | `cobol/STAUDIT.cob`、`sql/LOG-INSERT.sql` | 許可列名JSON・前後版・対象・実行者/時点/理由を記録するソース。個人情報値を監査へ複写しない処理を生成 |
| 共通16/17 | `STDATE.cob`、`STDATEOUT.cob`、`STISODATE.cob`、`copy/ST-DATE-INPUT.cpy` | 元号境界、実在日、年範囲、和暦表示のソースを生成。DATE-T適合試験は未実施 |
| ODBC/UTF-8/暗号/HTTP境界 | `bridge/student_bridge.c`、`student_abi.h`、`fields.h`、`sql_catalog.h` | ODBC W API、パラメーター、診断、UTF-8/UTF-16、ICU、暗号、URLデコード・65536byte・重複拒否・エスケープのCソースを生成。コンパイル未実施 |
| COPY/ABI | `copy/ST-APP.cpy`、`ST-LOCAL.cpy`、`ST-HELPERS.cpy`、`ST-FIELDS.cpy`、`ST-DB-REQUEST.cpy`、`ST-DB-RESULT.cpy`、`ST-REQUEST.cpy`、`ST-STUDENT.cpy`、`ST-SEARCH.cpy`、`ST-RESULT.cpy` | 11 COPY現存。DB request/resultとC headerは同じgenerator入力から生成。未結合 |
| 固定SQL | `sql/`の25ファイル | CLOCK/AUTH-ADMIN、コード/クラス候補、LOAD/UQ/CODE/CLASS/CAP/YEAR/COUNT/DUP/INSERT/UPDATE/DELETE/LOG、ソート4×方向2のLISTを生成 |
| 生成再現用 | `tools/generate.py`、`emit_cobol.py`、`emit_workflows.py`、`emit_search.py`、`abi-schema.json` | 手元で生成に使用。generator実行はCOBOL/Cコンパイルを意味しない |

現在16 COBOLプログラム、11 COPY、25固定SQL、C bridge/header群を保持している。`tools/__pycache__/`のPython一時生成物も中断時点のまま残る。空の`tests/`・`deploy/`ディレクトリーは試験・配備実装の存在を意味しない。

## 入出力の生成範囲

19保存入力は`ST-NORMAL`の1～19と固定SQL保存列へ対応し、氏名・カナ照合値を20～21へ生成する。生年月日は元号/年/月/日の4rawからISO日付へ変換する。rawは別`ST-RAW`に保持。選択補助・確認理由・ID/版・Context等を業務19列へ無制限コピーしないソースを生成した。

検索は12親条件（学籍番号、氏名、カナ、年度、学年、クラス、未所属、在籍4値、都道府県、電話、入学日開始/終了）とpage/pageSize/許可ソートを生成。`ST-COUNT`と8個の固定`ST-LIST-*`は同じ述語を使用する。一覧のSQLは11表示項目＋IDに限定するため、年度/学年とコード/クラス名を別取得列として数えると13列である。住所2・メール・緊急連絡・備考を一覧SQLへ出していない。和暦を実HTMLへ表示する部品は中断時点で未生成。

業務判定はCOBOLのSTNORM/STVALID/STRULES/STDUP/STSAVE/STAUDITに置き、Cは接続・バインド・固定SQL・HTTP/Unicode/暗号とopaque stateの型境界を担当する方針で生成した。Cの`STSTATEIO`はCOBOLの`STSTATE`と別シンボル。主処理は.NET Coreを呼ぶ構成にしていない。

## 静的棚卸し結果と未実施

中断後は読取だけで、既存ファイル・CALL/COPY名を棚卸しした。全16プログラムに現れる4種類のCOPY参照は現存する。CALLのCOBOL/C定義照合では、**`STRENDER`が未定義でCALL参照は閉じていない。** この照合は文字列名の棚卸しであり、リンカー検証やABI適合を意味しない。SQL catalogは25固定コマンドを保持するが、全COBOL呼出しについてバインド数・型・順序をコンパイル/結合検査していない。

ABIの想定はLinux x86_64、little endian、pointer8byte、ST_PARAM24、ST_DB_REQUEST976、ST_DB_RESULT40、ST_VALUE1032。C `_Static_assert`とCOPYの明示paddingを生成したが、Cコンパイラでassertを実行していない。COBOL側sizeof/offset呼出し試験・SQLWCHAR実ABI検査は未実施。

環境確認ではcobc/gcc/clangが見つからず、wslはディストリビューション未導入だった。GnuCOBOL3.2 Linux・unixODBC・Microsoft ODBC18・ICU・OpenSSLの依存版固定/実ビルドは未実施。構文エラー・リンクエラー・境界バグの可能性を残す。DBへ接続せず、SQLを実行していない。

未生成・未実装を次に明示する。

- `STRENDER`、`STMLOOK`、`STMSG`、画面HTML・CSS・離脱/確認JavaScript。2画面を実際に表示/操作できない。
- CGI公開外の`student-maint`／`STMAINT`、クラス・コード保守の業務フローと保存SQL。`AUTH-ADMIN.sql`の存在だけでは保守実装済みではない。
- 成功Flash一回消費、必須マスタ初期設定の包括的診断、画面候補のselectable/停止/期間外注記の提示、保守同名警告などの提示側。
- Makefile、実リンク設定、依存version lock、run/配備設定、ABI資料、README、CI、静的適合テストと実行試験。rootがREADMEの中断ラベルを担当する。
- CGIプロセス再起動を跨ぐ状態往復、UTF-8最大境界、URL不正、2接続/最終席競合、確認失効・再確認、監査失敗/通信断、実認証・ブラウザー・負荷・受入の試験。

保存/検索/状態等の部分ソースがあることと、全規則の実行適合は分ける。未生成部をstubで代替して完了とはしていない。仕様構造の修正とrootの再開指示までは、追加実装を行わない。
