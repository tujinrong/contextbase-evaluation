# 学生管理 AS400_RPG

2026-10-25 / `20261025-regenerate`。仕様入力は `../../spec/AS400_RPG/` の42ファイル（README8.5、登録詳細8.6、方式別共通8.4）です。通常preflightで全体規則を含む58ファイルを凍結しました。[生成記録](build/generation/generation.md) に入力版・実変更・検査範囲を記録しています。登録詳細の削除理由2欄目の一意な誤参照だけを8.5→8.6へ局所修正し、local-spec-fix.jsonに前後hashを保存しました。QA・正式fixtureは変更していません。

最新Text仕様から、5250通常編集を **EDSTUDENTの1画面** に再生成しました。全19保存入力とREG-001～034を維持し、備考3窓・理由2窓を原Unicode DSへ対応付けます。DDSの可視桁・プログラムバイト・SI/SOと前後属性セルを分けて配置します。生年月日元号は10スカラー用のvarucs2(20)、年度/学年も原入力を正規化済み補助値から分離しました。新規の入学日は空欄です。

検索は4条件、7論理列、1学生2物理行×8件、SQL20/50/100件を分けて保持します。Enterは選択欄の有効な2=編集または5=参照がちょうど1件ならその行だけ、未選択なら検索します。複数/不正選択は処理を進めません。F8はカーソル行の保護全文、F9は8ソート/方向、F11は3取得件数のPICKです。F7/F10は前後DBページ、F15/F16は先頭/最後、PageUp/Downは同じDBページ内だけです。

登録はEnterで入力反映、F4候補、F8全文、F9次エラー、F10全項目検査/保存、F5編集取消、F14再読込、F12復帰、F23削除です。候補PICKは1を1件選んでEnter、8件窓、取消F12で元値を保ちます。LONGTXTは128バイト窓で通常/Unicode表示をF6で明示切替し、通常の `\u{...}` は文字どおり保持します。Unicodeモードだけ `\u{HEX}` / `\n` / `\\` を復号します。補助内Enter/ページ移動は保存せず、F10だけ原入力へ反映、F12は補助変更を破棄します。原LFと物理折返しを分離し、補助文字/エスケープの途中で切りません。

重複確認は最大20候補を8件窓で表示しF10明示続行、削除は別原理由2窓とF23明示確定、破棄はF10です。F12取消を既定としEnterでは確定しません。保存の認可・対象版・全入力・全候補・10分期限・監査同一Txの再検査を維持しています。検索状態はCriteriaFormatVersion2、owner/job/window、正64bit revision、30分期限、旧形式の全初期化、満杯拒否です。

今回実行するWindows製品C試験は57件（Text窓/原入力上限22件を含む）、状態ゲートC42件です。RPG/DDS参照・配置・生成器の静的検査も実行し、[試験結果](build/test-results/README.md) へ固定保存します。**IBM i SQLRPGLE/ILE C/DDS/CLコンパイル・バインド・Db2・5250・IME/CCSID往復は未実施**で、ソース変更はネイティブ実行合格ではありません。formalScore=null。

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
python -X utf8 tools/test_host.py --run-id 20261025-regenerate
python -X utf8 tools/test_compact.py --run-id 20261025-regenerate
python -X utf8 tools/test_state.py --run-id 20261025-regenerate
python tools/write_report.py
```

生ログとJSONは `build/test-results/` の固定名を最新結果で置換します。過去版はGit履歴で管理し、実行IDはJSON内のメタデータに残します。`--report-dir` は方式内build/test-resultsまたは.tmp配下だけを指定できます。試行・隔離検査は.tmpを指定してください。処理系は `.tmp/toolchain/`、ホスト試験exe・pdbは `.tmp/host/`、キャッシュは `.tmp/cache/`、生成器の隔離検査は `.tmp/` へ置きます。正式なtestsとfixtureは保持します。IBM iの最終バイナリーは本環境で作成できないため `build/app/native-status.json` へ未ビルドを記録します。親工程の固定メタデータは `build/generation/`、ソース配布は `build/source.zip` です。

```text
python -X utf8 tools/generate_sources.py
python -X utf8 tools/generate_database.py
python tools/generate_messages.py
python tools/generate_dds.py
python tools/format_rpg.py
```

DB生成器は `../../spec/AS400_RPG/DB定義/Db2_for_i` と `../../spec/AS400_RPG/共通/10_業務コード定義.md` だけを読みます。DDSの現行生成器は `generate_dds.py` と `screen_layout.py` です。`generate_sources.py` の型と表示容量も現行へ更新しましたが、その他の開発時部分生成器を連続実行して業務・画面全体を再生成する手順ではありません。旧 `finish_ui.py` は現行画面を旧3パネルへ上書きしないよう起動を停止しました。配備時は確定済みソースを使用してください。[仕様対応](metadata/spec-mapping.json) と [入力ハッシュ](build/input-manifest.json) を保存しています。


現在のABIはCOMMON V2 / SVC V3 / UNICODE V2です。原元号/補助DSとText窓C関数を含め、BUILD.clleで全モジュール・DDS・binder・プログラムを再構築し、新しい専用ジョブで検証してください。旧バイナリー/旧STUDAGとの混在は未検証です。
