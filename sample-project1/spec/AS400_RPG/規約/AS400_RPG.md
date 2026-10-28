<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"AS400_RPG-DOC-E461E85A4485","version":"8.3","path":"sample-project1/spec/AS400_RPG/規約/AS400_RPG.md","sheets":[{"heading":"RPG型・データ構造","kind":"GRID","sheet":"01_RPG型・データ構造"},{"heading":"ビルド・配備・エラー","kind":"GRID","sheet":"02_ビルド・配備・エラー"},{"heading":"共通規約の具体化","kind":"GRID","sheet":"03_共通規約の具体化"}],"isolationProfile":"AS400_RPG"} -->
# AS400／RPG 開発規約

| 項目 | 内容 |
| --- | --- |
| 版数・改訂日 | 8.3／2026-10-25 |
| 対象方式 | AS400／RPG |
| 適用 | 設計上の実装契約。製品コードの実装・コンパイルは未実施 |

開発入力：[学生検索詳細](../詳細仕様書/01_学生検索画面.md)／[学生登録詳細](../詳細仕様書/02_学生登録画面.md)／[共通実装](../共通/方式別/01_共通実装仕様.md)／[DB定義](../DB定義/Db2_for_i/01_DB定義書.md)／[方式別開発規約](AS400_RPG.md)／[共通開発規約](開発規約.md)。

## RPG型・データ構造

| 意味 | RPG型・表現 |
| --- | --- |
| ID・版 | int(20)の符号付き64bit。DDS非表示転送は19桁文字から検査して変換 |
| 人数・ページ | int(10)、定員NULL標識を別保持 |
| NULL標識 | int(5)、-1=NULL／0=値あり。SQLホスト変数へ併記 |
| 日付 | date、内部ISO日付char(10)と変換。生年月日の画面入力は和暦の分割項目 |
| 時点 | timestamp、UTCとして運用し表示時に日本時間へ変換 |
| 業務Unicode文字N | vargraphic(2*N) CCSID1200相当のUTF-16領域。scalar数Nを別検査 |
| ASCIIコード | varchar(N)、数字・大文字英字等を検証 |
| SQL真偽 | smallint 0/1、RPG側はindへ明示変換 |

`StudentWork`はqualified DS。物理列snake_caseをcamelCaseへ対応付けたサブフィールドを持つ。SQL NULL可の各項目について同名＋Indのint(5)を持ち、空文字・0・最小日付をNULLの代替にしない。API署名はStSaveStudent(work const、hints const、expectedVersion、confirmation const、result)とし、resultはResultKind、MessageId、FieldErrors、StudentId、RowVersionを持つ。

## ビルド・配備・エラー

DDSをCRTDSPF、SQLRPGLEをCRTSQLRPGI／モジュール→サービスプログラムとしてビルドし、COPYとバインダーシグネチャーを固定する。STUDAPP/STUDPGMのライブラリーリスト、実行activation group、SQL命名・日付形式・照合順・CCSIDを配置資料で固定。ジャーナルレシーバー・ジャーナル作成、全5表＋制御表へのジャーナル開始を検証してからコミットメント制御を開始する。

SQLSTATE23505は番号／マスタ重複、23503は参照、02000は呼出目的に応じ行なし、ROW_COUNT=0は版または不在、40xxx・ロック待ちは再確認、その他は受付番号付き共通エラー。SQLCOD<0で後続更新を続けない。

STUNICODEは製品標準で存在するという仮定ではなく、実装が必要な補助サービス。変換不能文字の保持・Unicodeエスケープ補助・全長編集・C ABIを稼働条件として試験する。実機未検証のためコンパイル済み・文字往復確認済みとは記載しない。

## 共通規約の具体化

本方式では[共通開発規約](開発規約.md)を適用し、業務ルールや項目長は[詳細仕様](../詳細仕様書/02_学生登録画面.md)と[DB定義](../DB定義/Db2_for_i/01_DB定義書.md)に一致させる。長さの計測単位はUnicodeスカラー値。処理系のバイト／コード単位の領域は余裕を確保し、業務最大長を拡大しない。

機能固有のイベントは機能別詳細、複数機能で使う接続・トランザクション・正規化・和暦・認可・確認・UI部品は方式別共通へ置く。コピーした定義の修正は同じ仕様IDを持つ文書へ同時に反映する。デザイナー生成物、業務ロジック、テスト資源を分ける。

ビルド設定・ライブラリ版・DB設定・文字コード・暦定義版を方式プロファイルに記録する。現行の採用版は仮定を維持し、勝手な最新版への変更は行わない。API署名や型を変更する際は両画面、共通、DB、試験条件を同一改訂で直す。

### Text系のレコード・キー・文字コード契約

三分類のうち本方式はText系とする。新画面も固定行桁・入力/保護・候補/確認/長文補助・キー割付・原Unicode DSの移送を先に定め、HTMLではpre/spanで表す。Webのクリック、カード、レスポンシブな配置変換を前提にしない。基準フォントMS Gothic 16px、半角セル8px・全角2セル、行高20pxの図で27×132を確認する。これは端末表示の設計確認値で実機フォント保証ではない。

| レコード | 入力とキー | 戻り先・確定境界 |
| --- | --- | --- |
| COND/SFLCTL/SFLROW | Enter選択優先/未選択検索、F4候補、F5クリア、F6新規、F7/F10前後DB頁、F8全文、F9順序、F11件数、F12メニュー、F15/F16先頭末尾DB頁、PageUp/Down取得頁内 | 未適用条件とAppliedCriteriaを分離。選択複数/不正は検索も呼出しもしない |
| EDSTUDENT | Enter原入力反映、F4候補、F5取消、F8全文、F9次エラー、F10検査保存、F12検索、F14再読込、F23削除確認 | 通常1画面。F10以外で一般項目をDB保存しない |
| PICK | 選択1を1件+Enter、F8全文、F12取消、PageUp/Down | 入力欄/順序/件数へ返す。カーソル項目に対応する候補だけを出す |
| LONGTXT | F6通常/Unicode切替、F10原項目反映、F12補助取消、PageUp/Down文字範囲 | 変更範囲・LF・Unicode位置を保持。参照でF10無効 |
| CNFRM_DUP | F10明示続行、F12取消、F8理由/候補全文、PageUp/Down候補 | REG-032～034。全候補を再検査してから保存 |
| CNFRM_DELETE | F23明示確定、F12取消、F8削除理由全文 | REG-026。ID/版/削除理由だけを渡す |
| CNFRM_DISCARD | F10明示破棄、F12取消 | どの操作要求から来たかを保持。Enterで破棄しない |

全入力データを必要とするキーはCF系で返し、カーソル位置と項目変更標識を取得してRaw DSへ退避してから処理する。本方式の案内付きFキーはCF系へ統一し、確認取消でも原入力の受信後に取消対象を判定する。同じDSPFで同番号をCA/CFの両方に定義しない。DDSの数値編集・VALUES・必須チェックで不正原入力や取消キーを閉じ込めず、文字領域として受けて処理側で検査する。検索の行選択EnterではREADCから1件に限定しRRNをresultRowsへ対応する。EXFMT対象は現在レコードだけ、補助/確認中の背面入力は受け付けない。表示の色だけでエラー/無効を識別させず文字と下線属性を併用する。

DBCS-openはSBCS/DBCS混在でSI/SOを含み、DBCS-graphicはSI/SOを含まないため同じ長さ計算を使わない。今回の混在入力窓はO型を基本とし、CCSID変換した物理長と132桁境界を独立検査する。表示の半角1/全角2セル検査だけでSI/SOや端末属性領域まで合格にしない。ソース/ジョブ/表示装置/DBのCCSIDと対応DBCS機能を配備値として確定し、変換不能なら元Unicodeを維持しLONGTXTの明示エスケープで編集する。単一のDBCS連続列を超える混在値も、符号化長超過を切捨てず補助へ送る。

参考（2026-10-25確認）：[IBM DSPSIZ](https://www.ibm.com/docs/en/i/7.5.0?topic=80-dspsiz-display-size-keyword-display-files)は24×80/27×132のサイズ指定を説明する。[IBM DBCSファイル](https://www.ibm.com/docs/en/i/7.4.0?topic=support-how-indicate-dbcs-file)は混在/専用/graphicとSI/SOの相違を説明する。27×132採用、上表の割付と補助の符号化手順は本プロジェクトの設計判断である。[IBM CFキー](https://www.ibm.com/docs/en/i/7.4.0?topic=80-cfnn-command-function-keyword-display-files)と[IBM CAキー](https://www.ibm.com/docs/en/i/7.4.0?topic=80-cann-command-attention-keyword-display-files)は変更データ送信の相違を説明する。[IBM CFキー](https://www.ibm.com/docs/en/i/7.4.0?topic=80-cfnn-command-function-keyword-display-files)と[IBM CAキー](https://www.ibm.com/docs/en/i/7.4.0?topic=80-cann-command-attention-keyword-display-files)は変更データ送信の相違を説明する。DDSコンパイル・CCSID往復・実端末キー配送は未実施。

PICKの対象はカーソル欄の分類を保持する。検索クラス/登録クラス/性別/都道府県/在籍/続柄/元号/学年は既存候補IDの抽出・順序・停止値規則に従う。検索のF9は学籍番号/氏名/入学日/更新日時×昇順/降順の8固定選択肢、F11は20/50/100の3固定選択肢を同じ候補レコードへ表示する。複数選択・候補にない値は原入力と元画面を保持しエラー、取消は元値を変えない。候補取得失敗・0件は選択不可の文字案内でF12を残す。

レコード内の入力位置は行桁順で一意とし、1つの継続欄は同じ論理項目ID/Raw DSへ対応する。F8と候補復帰時は元項目ID・カーソル位置・原入力・期待版・未保存状態を復元する。PICKとLONGTXTは1レコードだけを表示し、背面キーを実行しない。項目エラーは20～21行の状態と対象IDを示し、F9で次エラーへ巡回する。住所等の長い項目名やエラー文はメッセージ領域内で改行して保持し、件数超過/末尾/障害を同じ状態にしない。


エスケープ導入記号はU+005Cである。端末/フォントにより円記号の字形で表示されても符号値で区別し、U+00A5を導入記号へ読み替えない。Raw DSは未変更値と変更範囲を保持し、空欄の下線・物理折返し・画面用末尾案内を保存値へ混ぜない。

### DDS物理名・属性とSI/SOの予約

埋込み図のdata-panelは画面状態名である。COND_SFLCTLはCOND/SFLCTL/SFLROWの合成表示、EDSTUDENTは通常編集、CNFRM_DUP/CNFRM_DELETE/CNFRM_DISCARDは物理レコードCNFRMの状態違いであり、長い状態名をDDSレコード名にしない。DDSのレコード名・フィールド名は10文字以内とする。data-recordとdata-dds-nameを実装時の名称対応に使い、UI項目IDや業務DSの長い名前とは区別する。

| 表示用途 | DDSレコード/フィールド | 原DSとの対応 |
| --- | --- | --- |
| 検索一覧の選択/番号/氏名/カナ/生年月日 | SFLROW/ROPT・RSTUNO・RNAME・RKANA・RBIRTH | resultRowsの対象IDと原Unicode、和暦文字列 |
| 検索一覧の年度/学年/クラスコード/名称/在籍 | SFLROW/RYEAR・RGRADE・RCCODE・RCNAME・RSTATUS | studentIdと同じ行の表示窓 |
| 件数/検索日時 | SFLCTL/RCOUNT・SRCHTIME | totalCount/RangeFrom/RangeTo・searchedAt |
| 更新情報/所属参考人数 | EDSTUDENT/UPDINFO・CLCOUNT | UPDATEDAT/UPDATEDBY・OCCUPANCY/CAPACITYは内部構成値で、表示は書式化した1フィールド |
| 重複候補件数/削除理由 | CNFRM/DUPCNT・DELREAS1・DELREAS2 | duplicateCandidates・deleteReason。状態に応じ入力可否を切替 |
| 候補/全文補助 | PICK/OPT、LONGTXT/TEXT | candidateSelection・longTextDraft。原項目IDと復帰位置はジョブDS |

data-col=C、data-width=Wは**可視の配置窓**である。各データフィールドについて直前C-1を開始属性、直後C+Wを終了属性用として空ける。隣接フィールドの開始/終了属性を共有する場合も予約1セルを残し、ラベル文字を置かない。HTMLにはdata-attribute-col/data-end-attribute-colを記録する。先頭入力欄は2桁目以降、最右の窓は130桁目までに終わり、属性/余白を含め132桁に収める。長い操作案内は1つの保護定数行として扱い、案内内のキー文字列それぞれを実入力フィールドにしない。

data-program-bytes=DはDDSプログラム領域の設計バイト上限で、混在O型は原則D=WとしSI/SOもDに含める。したがってW個の日本語文字が入力できるという意味ではない。例えばEKANAはW=74/D=74で全角36字1連続列なら72+SO/SI2=74バイトだが、半角/全角の交互列でDを超えるRawはF8補助へ退避する。住所欄W=112/D=112はraw45スカラーと別上限、LONGTXTのASCIIエスケープ窓はW=128/D=128で開始属性1桁目・終了属性130桁目を予約する。物理継続欄は1欄ごとにDを検査して、SI/SOのペア・DBCS文字・エスケープを分断しない。元Unicodeの全長はRaw DSに保有し、物理窓へ収まらないことを理由に切り捨てない。

モックの全角2/半角1セル検査と、実DDSの表示長・プログラム長・属性セル・SI/SO往復は別検査とする。文字変換後にDと表示窓Wを両方確認し、属性予約へはみ出さないことをDDS展開一覧と実エミュレーターで確認する。この実機確認は未実施であり、ブラウザーの寸法合格は代替しない。

参照（2026-10-25確認）：[IBM DDS命名](https://www.ibm.com/docs/en/i/7.4.0?topic=terms-dds-naming-conventions)、[IBM DDS長さと属性](https://www.ibm.com/docs/en/i/7.4.0?topic=44-length-display-files-positions-30-through-34)。名称10文字、表示/プログラム長と前後属性の区別に適用した。上記の割付・予約・F8退避は本プロジェクトの設計判断である。
