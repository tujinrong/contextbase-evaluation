# test-project1 試験データ・画面証拠・不具合修正

実行ID **20261012-evidence-01**、projectId **test-project1**。工程は既存生成プログラムの新規試験、実画面撮影、局所実装BUGの修正です。逆生成・採点は実行していません。変更先はagents/build-agentとtest-project1のみです。

## 入力版と検査範囲

入力はAG-BUILD7.5、REPO-AGENTS7.0、各方式内の原仕様8.0/8.1（Access DB索引8.2）。[入力manifest](20261012-evidence-01-inputs.json)の335ファイルはworking treeのSHA-256を固定しています。spec-eval・他project・過去レポートを入力へ含めていません。

[事前構造検査](20261012-evidence-01-structure.md)はmetadata、章/sheet対応、LIST形状/キー、TABLE列/fieldId/PK、イベント節、ローカル参照の存在を検査し、検出0件でした。全仕様の意味的一貫性やアプリの動作合格を示す結果ではありません。事前検査後の仕様変更は0件です。今回の不具合は原仕様に対する実装の不一致と判定し、本体と関連試験装置を修正しました。

## 出力

- [今回の試験報告](../test-report/20261012-evidence-01/README.md)：方式別の実行コマンド、処理系、終了値、生ログ、fixture、修正phase、未実施。
- [画面エビデンスHTML](../test-evidence/20261012-evidence-01/test-evidence.html)：原JPEGを埋め込んだ単独ファイル。[整合性JSON](../test-evidence/20261012-evidence-01/capture-integrity.json)と[完全デコード検証](../test-report/20261012-evidence-01/evidence-decode-verification.json)に実ファイル/hash/寸法を記録。
- [修正後の配布accdb](../srcs/Access/StudentManagement.accdb)：1個の実ACE成果物。試験学生/クラス/監査は含めず、試験fixtureと分離。旧MDB形式の成果はbyte exactバックアップとしてAccess/build/20261012-evidence-01-backupに保持。
- [修正後の出力manifest](20261012-evidence-01-outputs.json)：335入力のhash再照合、現行ソース/hash、変更文書の版/hash、最終配布accdbのhashを記録。

出力版は実行IDと方式別の修正phaseです。MVCはafter-fix、VBはafter-fix、WPFはui-fix-r4、AccessはR6を最終修正段階とします。初期phaseや途中R2/R3/R4/R5の記録は、その当時のソース・実行の証拠として保持し、最終sourceの再試験へ読み替えません。build-10の7方式ZIP/lockは旧改訂の凍結版で、今回は更新していません。agent-input/READMEにも明記しました。

画像43件、固有SHA-256は42件、明示的重複1件。全43件のJPEG完全デコードとHTML埋込みバイト一致はPASSで、原画像を変更していません。Access最終原本のSHA-256は `D1777167FD7423BF4399F05D006519FD5A8E005A6FEF2E56B1A8F11AAD73EC87`。FileFormat12のACEで業務データ/外部リンク/試験モジュールは0です。[終了確認](../test-report/20261012-evidence-01/close-verification.json)で撮影専用ホストの待受終了とAccess原本不変を再確認しました。

## 試験結果と不具合

VB/WPF/MVC/Vueは各方式に独立した3学生・2クラスのfixture、Accessは独立ACEに3学生・1クラスのfixtureを用意しました。COBOL/RPGは方式内で独立した架空入力3組を用意し、利用可能な処理系で実入力検査を行いました。方式間でソース、仕様、fixture、ビルド資源を共用していません。

MVCの空エラー枠、VBの初期フォーカス/スクロール、WPFの新規ClassId変換クラッシュ・検索候補表示/選択保持・未所属時の非活性/解除警告、Accessの出力形式・初期Boolean・検索候補表示/順序/解除警告・VBEコードページによる文字化けを修正しました。各最終phaseの回帰は個別報告を参照してください。画面証拠も修正前と修正後を分けています。試験装置側の初回失敗と修正も別記録で保持しています。

Access R6は実通知58・項目ラベル1・フォーム/DAO13・配布19の91チェックがPASSです。R5の業務137/FK21/初期状態10/検索21/２プロセス競合はR6で再実行していません。R6実画面では空入力の保存操作に対して、生年月日通知の中点3文字が仕様本文と一致することを確認しました。[R6報告](../test-report/20261012-evidence-01/Access-r6/README.md)と[修正後実画面](../test-evidence/20261012-evidence-01/Access/09-invalid-date-after-final-fix.jpg)を参照してください。

[最終隔離監査](../test-report/20261012-evidence-01/isolation-audit-final.md)は855ファイル/1511参照の検出0件、補助の110プロジェクト項目/47 fixtureファイルの方式間参照0件です。入力335件、DB資源31件、旧7 ZIP/lockのSHA-256は不変で、最終R6 accdbと旧838Fバックアップも記録値に一致しました。これは静的隔離と成果物整合性の検査であり、共有SQL業務やIBM i実行の合格ではありません。

SQLへ業務テストデータを投入していません。VB/WPF/MVC/Vueのfixtureは保存・削除を拒否し、実SQLの正常CRUDや監査/認可の証拠として扱っていません。COBOLの実CGI撮影は401/400だけ、RPGの5250撮影はNOT_RUNです。

## 継続中の構造中断と未実施

[共有SQL移行中断](20261012-shared-sql-migration-stop.md)は未解消です。roleのDENY/DML契約、WPF/VBのSQLCLR assembly識別、AccessのSELF/ACEと共有SQLの責務、IBM iの接続・認証・トランザクション契約に別Agentの構造修正が必要です。業務DDL・共有schema・共有SQLへの移行生成は停止を維持しました。

共有SQL Server ExpressのWindows認証/暗号化/空DBは[初期の読取検証](../test-report/20261012-evidence-01/sql-readonly.json)と[最終の13条件の読取検証](../test-report/20261012-evidence-01/sql-readonly-final.json)で確認しました。最終検査はSELECT4本、DDL/DML0件です。これはsysadmin主体のインフラ読取で、アプリの非sysadmin認可や正常CRUDの検証ではありません。

共有SQL業務配備/データ投入/CRUD/監査/競合/実認可/SQLCLR hosting、Access・AS400の共有SQL接続、IBM iコンパイル/Db2/5250、Linux CGI配備、Office32bit、IME/DPI/切断/性能等の網羅受入、逆生成と採点は未実施です。
