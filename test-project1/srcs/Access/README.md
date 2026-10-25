# Access 学生管理

2026-10-25、build-agent 7.8 / runId `20261025-access-quality`。対象は [Access仕様](../../spec/Access/README.md) と利用者の今回の品質改善・初期データ要求です。入力は `test-project1/spec/Access/`、ソースは `test-project1/srcs/Access/`。凍結入力の版・SHA-256は [generation/inputs.json](build/generation/inputs.json)、旧仕様との要求差分は [user-overrides.json](build/generation/user-overrides.json)、仕様への引継ぎは [仕様問題報告](../../../test-project1-spec-bug-report.md) に記録します。

最終成果は [build/StudentManagement.accdb](build/StudentManagement.accdb) 1個です。5フォーム、VBA、業務5表、保存ゲート、評価用役割表、初期5分類70コード、架空クラス4件・学生12件・初期監査16件を内包し、外部リンクはありません。通常の在籍/休学検索は9件です。初期の役割主体は生成時の Windows 利用者。最新のSHA-256と検証状態は [test-results/summary.json](build/test-results/summary.json) を参照してください。

検索は学籍番号前方一致・氏名照合値部分一致・クラスID・在籍集合の4条件。在籍の初期値は01/02、全解除は全区分です。全一致0～10000件を一括表示し、10001件以上は W-SRC-001 で旧一覧を消去します。旧範囲入力は空でも拒否し、検索クラス・関数・フォームに Page/PageSize を残しません。一覧は非表示学生ID＋7表示列で、氏名とカナを合成します。住所・本人電話・更新日時は一覧DTOへ返さず、更新日時の内部ソートは維持します。

検索状態は所有者・認証セッション・フォーム・30分期限・CriteriaFormatVersion=3・Revisionで照合します。旧形式1/2や版不明は W-SRC-002 で初期化。並び替え・編集復帰は最後に実行した AppliedCriteria を使用し、未実行条件の通知を保持します。選択学生IDと実際のListBoxスクロール位置を復元し、消えたIDを選択解除して位置を範囲内へ補正します。一覧内のスクロールはDBを呼びません。

検索・編集は標準の単票フォーム（Single Form）。本文11pt、通常入力390 twips、ボタン420 twipsを基準とし、見出しは標準Rectangleと文字幅に応じたラベルです。検索一覧は高さ4020 twips、編集は項目長に応じた2列配置。学籍番号は新規で入力でき、既存は変更不可、管理番号は自動採番です。郵便番号は `000\-0000;1;_` の入力マスクで3桁–4桁表示、保存は先頭ゼロを含む数字7桁です。全角数字・許可ハイフンの貼付は全体を正規化・検査し、余分な桁を切り捨てません。34論理項目・19保存入力、備考と理由の複数行入力、Shift+F2拡大入力を保持します。重複・論理削除・未保存破棄は別モーダルで取消を既定にします。未保存変更は読込時rawとの比較で判断し、入力を元に戻せば破棄確認は不要です。

Windows と Microsoft Access が必要です。今回の自動検査は64bit Access 16.0で実行しました。ファイルを開くと未検索の `frmStudentSearch` が起動します。評価構成のため、ファイルを直接変更できる利用者に対する強い権限境界は保証しません。採用済み単体ACEを維持し、共有SQL移行は実行していません。

```powershell
# リポジトリルートから入力を凍結
node agents/build-agent/scripts/preflight.mjs --project test-project1 --profile Access --run-id 20261025-access-quality
# Access ディレクトリで最終生成・専用fixture検査
./tests/Invoke-Verification.ps1 -RunId 20261025-access-quality
```

生成器は `.tmp/generation/` の作業DBへ表・VBA・フォーム・確認用サンプルを作成し、ネイティブVBEコンパイラ（コマンド578無効化）を確認してAccessを閉じた後、最終ACCDBを置換します。生成直後は以前の検証を無効化し `VerificationRequired`、統合検証完了時だけ `Passed` になります。試験モジュール・異常系fixtureは配布ACCDBへ含めません。`-IncludeTests` は初期業務データが空の隔離fixtureを作り、専用試験がサンプル再投入の冪等性・利用者変更保護を検査します。サンプルは [database/sample-data.json](database/sample-data.json) に定義し、初回の基準日/年度をDBへ保存、Form_Loadでは再投入しません。

生成履歴はGitで管理します。`build/` の許可先は `StudentManagement.accdb`、最新の `test-results/`、工程制御の `generation/`、別工程の `spec-generation/`（今回未変更）、解析用 `source.zip`。source.zipと出力manifestは最終工程で更新します。試行・VBE作業・業務fixture・配布検査コピー・競合用barrierはGit対象外の `.tmp/` 内です。検証JSONと生ログは種類ごとの固定名で更新し、履歴階層を増やしません。試験コードとfixture定義はソースとして保持します。

郵便の貼付はキーボード・Ribbon・native貼付を同じ検査へ接続します。技術上、郵便欄のフォーカス中だけWindowsのcallbackを登録するため、VBA開発時はその欄から離れてからIDEのReset/コード変更を行ってください。通常のフォーカス離脱・フォーム終了では解除し、その状態も自動試験します。Clipboard試験は元データを一時的に暗号化退避し、復元の内容一致を確認して退避物を削除します。

VBAの`DoCmd.RunCommand acCmdPaste`直呼出しはRibbonコマンドと異なり、マスクが貼付原文を切り詰めることを診断で確認しています。生成アプリの貼付APIには使わず、郵便欄は`PostalPaste`へ接続します。API診断の観測値はpostal-paste記録に残し、実Ribbon・専用右クリックメニュー・キー経路の合格と区別します。保存サービスへの直接入力も別途7桁を検査します。

ソース配布は [build/source.zip](build/source.zip)。正式な試験コード・原仕様は含めず、標準Accessで独立生成できるBuilder・VBA・DB定義を含みます。作成/隔離ハッシュ確認後、`tests/Test-SourcePackage.ps1 -RunId 20261025-access-quality` がZIPだけからネイティブコンパイルと初期データを再検査し、元ACCDBを変更しないことを確認します。

統合検査は業務・拡張・検索契約・10000/10001件境界・既存実フォーム、複合FK、別2プロセスの最終1席に加え、サンプルデータ、ネイティブの実入力/読込/保存、郵便貼付、配布物の初期件数と試験コード混入、出力パスとPowerShell構文を実行します。同一Accessプロセスでフォーム試験を10回繰り返し、業務件数の保持とプロセスの正常終了も検査します。一覧描画中のDB再照会を避け、callback識別子とフォーカス中のウィンドウの寿命を管理します。具体的な検査数と最終状態は [検証記録](build/test-results/summary.json) に従います。過去のPASSは合算しません。仕様の局所誤記3件の過去修正は [local-spec-fix.json](build/generation/local-spec-fix.json) として区別します。

Office32bit、他のWindows DPI/IME構成での利用者受入、10万行/20利用者性能、共有切断、確定応答喪失、本番配備、共有SQL移行、逆生成・正式採点は未実施です。10000/10001件の機能境界検査を性能保証とは扱いません。
