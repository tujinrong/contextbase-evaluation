# Access 学生管理

2026-10-25、build-agent 7.7 / runId `20261025-regenerate` で [最新Access仕様](../../spec/Access/README.md) から更新しました。入力は `test-project1/spec/Access/`、ソースは `test-project1/srcs/Access/`。入力58ファイルの版・SHA-256は [generation/inputs.json](build/generation/inputs.json)、変更と実施範囲は [generation/generation.md](build/generation/generation.md) に記録します。

最終成果は [build/StudentManagement.accdb](build/StudentManagement.accdb) 1個です。5フォーム、VBA、業務5表、保存ゲート、評価用役割表、初期5分類70コードを内包し、学生・クラス・監査は0件、外部リンクはありません。初期の役割主体は生成時の Windows 利用者。最新のSHA-256と検証状態は [test-results/summary.json](build/test-results/summary.json) を参照してください。

検索は学籍番号前方一致・氏名照合値部分一致・クラスID・在籍集合の4条件。在籍の初期値は01/02、全解除は全区分です。全一致0～10000件を一括表示し、10001件以上は W-SRC-001 で旧一覧を消去します。旧範囲入力は空でも拒否し、検索クラス・関数・フォームに Page/PageSize を残しません。一覧は非表示学生ID＋7表示列で、氏名とカナを合成します。住所・本人電話・更新日時は一覧DTOへ返さず、更新日時の内部ソートは維持します。

検索状態は所有者・認証セッション・フォーム・30分期限・CriteriaFormatVersion=3・Revisionで照合します。旧形式1/2や版不明は W-SRC-002 で初期化。並び替え・編集復帰は最後に実行した AppliedCriteria を使用し、未実行条件の通知を保持します。選択学生IDと実際のListBoxスクロール位置を復元し、消えたIDを選択解除して位置を範囲内へ補正します。一覧内のスクロールはDBを呼びません。

検索・編集は標準の単票フォーム（Single Form）。本文18240×8640 twips（96dpi換算1216×576px）、9pt、通常入力360 twips、行ピッチ420 twips、ボタン390 twipsです。検索一覧は高さ4020 twips、編集は項目長に応じた2列配置。34論理項目・19保存入力、備考と理由の複数行入力、Shift+F2拡大入力を保持します。重複・論理削除・未保存破棄は別モーダルで取消を既定にします。未保存変更は読込時rawとの比較で判断し、入力を元に戻せば破棄確認は不要です。

Windows と Microsoft Access が必要です。今回の自動検査は64bit Access 16.0で実行しました。ファイルを開くと未検索の `frmStudentSearch` が起動します。評価構成のため、ファイルを直接変更できる利用者に対する強い権限境界は保証しません。採用済み単体ACEを維持し、共有SQL移行は実行していません。

```powershell
# リポジトリルートから入力を凍結
node agents/build-agent/scripts/preflight.mjs --project test-project1 --profile Access --run-id 20261025-regenerate
# Access ディレクトリで最終生成・専用fixture検査
./tests/Invoke-Verification.ps1 -RunId 20261025-regenerate
```

生成器は `.tmp/generation/` の作業DBへ表・VBA・フォームを作成し、ネイティブVBEコンパイラ（コマンド578無効化）を確認してAccessを閉じた後、最終ACCDBを置換します。生成直後は以前の検証を無効化し `VerificationRequired`、統合検証完了時だけ `Passed` になります。試験モジュールと業務サンプルは配布ACCDBへ含めません。

生成履歴はGitで管理します。`build/` の許可先は `StudentManagement.accdb`、最新の `test-results/`、工程制御の `generation/`、別工程の `spec-generation/`（今回未変更）、解析用 `source.zip`。source.zipと出力manifestは最終工程で更新します。試行・VBE作業・業務fixture・配布検査コピー・競合用barrierはGit対象外の `.tmp/` 内です。検証JSONと生ログは種類ごとの固定名で更新し、履歴階層を増やしません。試験コードとfixture定義はソースとして保持します。

今回の検査は業務31・拡張77・検索契約50・10000/10001件境界7・実フォーム66、複合FK21、配布19、別2プロセスの最終1席、出力パス境界8件、PowerShell構文17本です。具体的な最終状態は [検証記録](build/test-results/summary.json) に従います。過去のPASSは合算しません。仕様の局所誤記3件の修正と版更新は [local-spec-fix.json](build/generation/local-spec-fix.json) に列挙しました。

Office32bit、手動ピクセル・キーボード受入、10万行/20利用者性能、共有切断、確定応答喪失、本番配備、共有SQL移行、逆生成・正式採点は未実施です。10000/10001件の機能境界検査を性能保証とは扱いません。
