# 学生管理 AS400_RPG

2026-10-25 配置更新：仕様入力は `test-project1/spec/AS400_RPG/`、ソースと生成出力は `test-project1/srcs/AS400_RPG/` に分離します。入力ロックは生成時の版・ハッシュを保持し、新しい仕様で再生成する際に検査して更新します。この配置更新ではアプリ・DBの再生成と実行試験を行っていません。

`../../spec/AS400_RPG/` の専用仕様セットを入力とする独立プロジェクトです。SQLRPGLE、DDS、ILE C、CL、Db2定義、初期データ、生成器はこのディレクトリー内で完結します。別方式のライブラリー、共通プロジェクト、共有生成器を参照しません。

現行検査ではWindows上の既存C補助35件と、製品と同じ検索状態ゲート・キー検査・ブロック補正Cの42件をコンパイルして実行しました。SQLRPGLE/DDS/CL/バインド/Db2/5250は IBM i 環境がないため未コンパイル・未実行です。静的な参照確認はその代わりの合格判定にはなりません。今回の結果は [方式内の試験状態](build/test-results/summary.json) を参照してください。

`src/STUSRCH.sqlrpgle` と `STUEDIT.sqlrpgle` が画面、`STUSVC.sqlrpgle` と `STUMASTER.rpgleinc` が業務・保守処理、`STUCOMMON.sqlrpgle` が認可・日付・正規化・メッセージ・確認照合です。`STUMNT.sqlrpgle` は承認済み IFS 入力の管理者保守入口です。C 補助は厳密な UTF16、ICU、置換を許さないCCSID変換、明示エスケープとSHA256を実装します。

2026-10-23の専用仕様8.1／共通8.2へ更新しました。検索は学籍番号・氏名・全年度クラス・在籍集合の4条件です。条件原文と実行済み条件を分け、20/50/100件取得と8学生×2物理行のサブファイルを分けて管理します。PageUp/Downは同じ取得ページ内を8学生ずつ送り、F7/F10は前／次DB取得ページ、F15/F16は先頭／最後DB取得ページへ進みます。端点・未検索・0件・上限超過ではDB再取得しません。F9は固定4ソート・方向を巡回、F11は20／50／100を巡回し、実行済み条件のまま先頭へ戻します。2=編集、5=参照、9=表示長文の全文参照、EnterまたはF14で選択行を処理します。行番号の表示値を対象IDとして保存しません。F4候補、F5クリア、F6新規、F12復帰、F20項目エラー一覧です。候補選択だけで再検索しません。

登録はEDBASE（基本・住所・本人連絡先）とEDENROLL（在籍・所属・緊急連絡先・備考・理由）の通常2パネルです。REG-001～034は更新情報・操作と別確認画面を含めて維持します。F9でrawを退避して切替、F4候補、F8全文・Unicode入力、F10全項目検査・保存、F5編集取消、F14再読込、F12復帰、F23管理者削除、F20全項目エラーです。最初の項目エラーがあるパネルへ戻します。field指定は19入力の番号、20元号/21年/22月/23日/24操作理由、25年度/26学年です。氏名、備考等は表示不能や桁超過のとき元値を保持します。F8の補助モードだけで `\u{20BB7}` と `\\` を解釈し、普通の入力では解釈しません。確認はF12取消が既定、F10が明示続行です。確認画面F8で0を指定すると理由の全文、1～10を指定すると候補の全文を開きます。

現行検査はWindows Cホスト35件、製品C状態ゲート42件、参照／幅など静的91件、検索・DDS配置静的32件、状態・候補・生成器の静的25件がPASSです。SQLRPGLE／DDS／CLのネイティブコンパイル、Db2、5250、CCSID往復、保存・競合の実行は未実施です。[今回の試験記録](build/test-results/README.md)。formalScore=null。

初期登録の性別0、在籍01、入学日は業務日、年度補助は当年度です。終了状態の修正はAdminと理由を再検査します。保存時はDBゲート取得後に認可、対象版、マスタ、期間、定員、番号、全重複候補を再確認します。確認中はトランザクションを保持せず、再要求で10分期限、実行主体/ジョブ/画面、内容、全候補ID/版を照合します。保存成功は学生と監査のCOMMIT後に通知し、確定不明時は検索での確認を案内します。削除入口へ編集中の業務値を渡しません。

## IBM i での配備

IBM i 7.5、RPG/SQL/ILE Cコンパイラー、ICU option39、27×132とCCSID1399を扱える5250端末が必要です。まず `../../spec/AS400_RPG/規約/開発規約.md` と [配備手順](docs/deployment.md) の条件を確認してください。ICUの採用版とUnicodeデータは実機で記録し、C試験を再実行して固定します。

このディレクトリーを UTF8 のまま `/stuapp/source` へ転送し、ファイルCCSIDを1208として管理します。開発管理者が `database/schema.sql` を空の STUDAPP へ適用し、`cl/JOURNAL.clle` の6表をジャーナル開始してから `database/seed.sql` を適用します。DB実行はこのWindows試験では行っていません。SQLスクリプトの再適用による初期値の上書きを禁止し、既存値との差分を確認してください。

CL源はソースファイルへコピーして CRTBNDCL で作成してください。例:

```text
CRTSRCPF FILE(QTEMP/QCLSRC) RCDLEN(112) CCSID(1399)
ADDPFM FILE(QTEMP/QCLSRC) MBR(BUILD) SRCTYPE(CLLE)
CPYFRMSTMF FROMSTMF('/stuapp/source/cl/BUILD.clle') TOMBR('/qsys.lib/qtemp.lib/qclsrc.file/build.mbr') MBROPT(*REPLACE) STMFCODPAG(1208)
CRTBNDCL PGM(QTEMP/STUBUILD) SRCFILE(QTEMP/QCLSRC) SRCMBR(BUILD)
CALL QTEMP/STUBUILD
```

BUILDがDDS、C、共通/業務サービス、STUBND、画面・保守プログラムを順に作成します。6表のSQLパッケージ、バインドリスト、コンパイルスプールを保存し、致命診断があれば使用を止めて修正します。`cl/SECURITY.clle` は管理者レビュー後に適用します。画面実行は `cl/START.clle` をコンパイルし、そのプログラムをクリーンな専用ジョブから起動します。STUDAGとジョブ共通のコミットメント定義、有限のDB待ち時間を採用します。管理者保守は `cl/MAINTAIN.clle` をSTUMAINTとしてコンパイルし、管理者だけに起動を許可して、葉ファイル名のCHAR(64)引数で呼び出します。保守用CLと起動CLは所有者権限を採用せず、呼出先が毎要求のDB主体を検査します。

## ローカルの試験と生成

Python 3.11以降と、この方式内の `.tmp/toolchain` に取得した Zig/ICU を使います。`tools/prepare_c_host.py` は公式配布をローカルに展開し、OSの設定を変更しません。

```text
python tools/prepare_c_host.py
python tools/test_host.py
python tools/test_compact.py
python tools/test_state.py
python tools/write_report.py
```

生ログとJSONは `build/test-results/` の固定名を最新結果で置換します。過去版はGit履歴で管理し、実行IDはJSON内のメタデータに残します。`--report-dir` は方式内build/test-resultsまたは.tmp配下だけを指定できます。試行・隔離検査は.tmpを指定してください。処理系は `.tmp/toolchain/`、ホスト試験exe・pdbは `.tmp/host/`、キャッシュは `.tmp/cache/`、生成器の隔離検査は `.tmp/` へ置きます。正式なtestsとfixtureは保持します。IBM iの最終バイナリーは本環境で作成できないため `build/app/native-status.json` へ未ビルドを記録します。親工程の固定メタデータは `build/generation/`、ソース配布は `build/source.zip` です。

```text
python tools/generate_database.py
python tools/generate_messages.py
python tools/generate_dds.py
python tools/format_rpg.py
```

DB生成器は `../../spec/AS400_RPG/DB定義/Db2_for_i` と `../../spec/AS400_RPG/共通/10_業務コード定義.md` だけを読みます。DDSの現行生成器は `generate_dds.py` と `screen_layout.py` です。`generate_sources.py` の型と表示容量も現行へ更新しましたが、その他の開発時部分生成器を連続実行して業務・画面全体を再生成する手順ではありません。旧 `finish_ui.py` は現行画面を旧3パネルへ上書きしないよう起動を停止しました。配備時は確定済みソースを使用してください。[仕様対応](metadata/spec-mapping.json) と [入力ハッシュ](build/input-manifest.json) を保存しています。

02ではCriteriaFormatVersion=2と正64bit Revisionを適用した。検索状態の正本はSTUSVCのジョブ内レジストリーで、所有者・ジョブ・画面ID・期待Revisionを照合してから形式版と30分期限を検査する。古いRevision／他者は正本・一覧を上書きしない。形式欠落／旧形式／期限切れはraw・実行済み条件・結果・ページ・20件・学籍番号昇順を全初期化してW-SRC-002を通知する。期限済みslotが他画面へ再利用された後の古い復帰は、現在の利用者・ジョブの確認後に新しい空contextを発行し、旧データを復元しない。レジストリー64件のlive上書きはせず、満杯は明示エラー。F5は同じslotのRevisionを更新し、F12はslotを解放する。未知／廃止入力キーはE-SRC-001で拒否する。

重複候補のSQL投影・返却DS・CNFRMは学籍番号・氏名・和暦生年月日・クラスだけ。全候補ID／版は内部の確認hash計算へ限定する。確認取消・編集取消・再読込・終了で当該owner/job/editorの確認を解放し、確認領域の満杯でもlive tokenを追い出さない。取得結果減少時の端末blockを補正し、未検索の日時に疑似初期日付を表示しない。

STUSVCのbinder signatureはV2。配備時は新しいSTUSTATE C moduleを含む全モジュール・サービス・画面をBUILD.clleで再構築し、旧ジョブのSTUDAGを引き継がず専用の新規ジョブで起動する。古いバイナリーとの混在を検証済みとして扱わない。RPG registry、Db2、確認UI、DDS/5250の実行は未実施。旧finish_services.py／finalize_behavior.pyは一度限りの旧移送用で、現行V2を巻き戻さないよう停止した。
