# 学生管理 AS400_RPG

方式内の `spec/` 専用仕様セットを入力とする独立プロジェクトです。SQLRPGLE、DDS、ILE C、CL、Db2定義、初期データ、生成器はこのディレクトリー内で完結します。別方式のライブラリー、共通プロジェクト、共有生成器を参照しません。

現時点で Windows 上の C 補助はコンパイルと35件の実行試験が成功しています。SQLRPGLE/DDS/CL/バインド/Db2/5250は IBM i 環境がないため未コンパイル・未実行です。静的な参照確認はその代わりの合格判定にはなりません。今回の結果は [方式内の試験状態](metadata/test-status.json) を参照してください。

`src/STUSRCH.sqlrpgle` と `STUEDIT.sqlrpgle` が画面、`STUSVC.sqlrpgle` と `STUMASTER.rpgleinc` が業務・保守処理、`STUCOMMON.sqlrpgle` が認可・日付・正規化・メッセージ・確認照合です。`STUMNT.sqlrpgle` は承認済み IFS 入力の管理者保守入口です。C 補助は厳密な UTF16、ICU、置換を許さないCCSID変換、明示エスケープとSHA256を実装します。

検索は条件原文と実行済み条件を分け、20/50/100件取得と10行のサブファイルを分けて管理します。F9で取得済みページ内の次10行、PageUp/DownでSQLの前後ページ、F7/F10で先頭/最後へ進みます。2=編集、5=参照、9=11列の全文参照、EnterまたはF14で選択行を処理します。行番号の表示値を対象IDとして保存しません。F4候補、F5クリア、F6新規、F3終了、F20項目エラー一覧です。候補選択だけで再検索しません。

登録はF7前パネル/F9次パネル、F4候補、F8全文・Unicode入力、F10保存、F5編集取消、F14再読込、F12復帰、F23管理者削除、F20全項目エラーです。field指定は19入力の番号、20元号/21年/22月/23日/24操作理由、25年度/26学年です。氏名、備考等は表示不能や桁超過のとき元値を保持します。F8の補助モードだけで `\u{20BB7}` と `\\` を解釈し、普通の入力では解釈しません。確認はF12取消が既定、F10が明示続行です。確認画面F8で0を指定すると理由の全文、1～10を指定すると候補の全文を開きます。

初期登録の性別0、在籍01、入学日は業務日、年度補助は当年度です。終了状態の修正はAdminと理由を再検査します。保存時はDBゲート取得後に認可、対象版、マスタ、期間、定員、番号、全重複候補を再確認します。確認中はトランザクションを保持せず、再要求で10分期限、実行主体/ジョブ/画面、内容、全候補ID/版を照合します。保存成功は学生と監査のCOMMIT後に通知し、確定不明時は検索での確認を案内します。削除入口へ編集中の業務値を渡しません。

## IBM i での配備

IBM i 7.5、RPG/SQL/ILE Cコンパイラー、ICU option39、27×132とCCSID1399を扱える5250端末が必要です。まず `spec/規約/開発規約.md` と [配備手順](docs/deployment.md) の条件を確認してください。ICUの採用版とUnicodeデータは実機で記録し、C試験を再実行して固定します。

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

Python 3.11以降と、この方式内の `build/toolchain` に取得した Zig/ICU を使います。`tools/prepare_c_host.py` は公式配布をローカルに展開し、OSの設定を変更しません。

```text
python tools/prepare_c_host.py
python tools/test_host.py --run-id 20261012-run1 --run-id UNIQUE-RUN-ID
```

生ログとJSONは `build/test-results` へ出力します。`--report-dir` を明示すれば実行記録を指定先へエクスポートできます。`build` のコンパイラー、DLL、EXE、PDB、キャッシュはソース成果物と区別します。

```text
python tools/generate_database.py
python tools/generate_messages.py
python tools/format_rpg.py
```

DB生成器は `spec/DB定義/Db2_for_i` と `spec/共通/10_業務コード定義.md` だけを読みます。その他の生成スクリプトは開発時の部分生成器であり、現在の手書き業務・画面処理の全体を再生成しません。配備時は確定済みソースを使用してください。[仕様対応](metadata/spec-mapping.json) と [入力ハッシュ](metadata/spec-inputs.json) を保存しています。
