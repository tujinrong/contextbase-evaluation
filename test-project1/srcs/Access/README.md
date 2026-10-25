# Access 学生管理

2026-10-25 配置更新：仕様入力は `test-project1/spec/Access/`、ソースと生成出力は `test-project1/srcs/Access/` に分離します。入力ロックは生成時の版・ハッシュを保持し、新しい仕様で再生成する際に検査して更新します。この配置更新ではアプリ・DBの再生成と実行試験を行っていません。

2026-10-24の運用配置に従い、最終成果は [build/StudentManagement.accdb](build/StudentManagement.accdb) 1個です。最新のSHA-256と検証結果は [build/test-results/summary.json](build/test-results/summary.json) を参照してください。5フォーム、VBA、業務5表、ゲート、評価用役割表、初期5分類70コードを内包し、学生・クラス・監査は0件です。外部リンクはありません。初期の役割主体は生成時の Windows 利用者です。

検索は学籍番号前方一致・氏名照合値部分一致・クラスID・在籍集合の4条件です。在籍は初期01/02、全解除は全区分。`clsSearchCriteria` に旧条件プロパティを残さず、raw辞書の未知・廃止キーは空でも拒否します。一覧は非表示学生ID＋7列のネイティブListBox。氏名とカナを合成し、長い値は全文欄へ表示します。住所・電話・更新日時は一覧DTOから除外し、更新日時ソートは内部で保持します。

検索状態は状態ID・所有者・認証セッション・フォーム・30分期限・CriteriaFormatVersion=2・Revisionで照合します。同期DAO処理でもBusy/状態更新ガードを使い、同じ版の再入と古い検索・クリア・復帰を拒否します。未実行条件をページ移動へ混ぜません。

検索・編集フォームの本文は18400×9600 twips（96dpi換算で約1227×640px）、入力は510 twips（34px相当）、文字は9pt（12px相当）です。編集は34論理項目と19業務入力を保持し、上段基本情報と下段3列に配置しました。備考・理由は複数行、長文は Shift+F2 の拡大入力で確認できます。重複・論理削除・未保存破棄を別のモーダルフォームで表示し、取消を既定にします。

仕様正本は [test-project1/spec/Access](../../spec/Access/README.md) 内だけです。今回の主要改訂は検索/登録8.1・共通データアクセス8.2です。方式内仕様のSHA-256は [build/test-results/inputs.json](build/test-results/inputs.json) に記録します。仕様本文・画像・render記録は変更していません。DB構成は承認済みの単体ACEを維持し、共有SQLへの移行は実行していません。

Windows と Microsoft Access が必要です。今回の環境は64bit Access `16.0.20527.20088`。ファイルを開くと `frmStudentSearch` が起動します。未検索・20件・在学/休学が初期状態です。評価構成のため、ファイルを直接変更できる利用者に対する強い権限境界は保証しません。

```powershell
# 最新の最終成果を更新
./Build-Access.ps1
# 最新成果を生成し、専用fixtureと同一バイトコピーで検証
./tests/Invoke-Verification.ps1
```

生成器の既定は単体ACCDB・新規初期表・ネイティブVBEコンパイルです。作業DBは `.tmp/generation/` に作り、Accessを閉じてから `build/StudentManagement.accdb` を固定名で置換します。失敗途中のDBを最終成果へ昇格しません。VBEコンパイルはコマンド578の完了状態で確認します。外部出力・再解析ポイント・最終成果への試験モジュール混入は拒否します。生成時は以前の試験記録を消去し、検証状態を `VerificationRequired` に戻します。統合検証の完了時だけ `Passed` になります。

生成履歴はGitで管理します。`build/` の許可先は `StudentManagement.accdb`、最新の `test-results/`、工程制御の `generation/`、解析用 `source.zip` です。Access生成・検証段階ではACCDBと試験記録を更新し、その後のpreflight・package・manifest工程が `generation/` と `source.zip` を追加・更新します。日時/run-idごとの成果やバックアップを増やさず、検証結果JSON・生ログは種類ごとの固定名で更新します。staging、VBE作業、業務fixture、配布検査コピー、競合用barrier、補助試験の出力は `.tmp/` 内です。`.tmp/` はGit対象外です。

今回の旧 `build/` とルート直下の旧ACCDBは、最終成果の再生成・ハッシュ照合後に `.tmp/legacy-work/` へ同一ボリュームで移動しました。旧成果整理には可逆な移動を採用し、コピーによる履歴の増殖は行っていません。配置・保護対象の照合結果は `build/test-results/layout.json` と `source-inventory.json` です。配置監査にはAccess生成・検証段階の実在項目と、後続の工程制御が追加する許可先を分けて記録します。

`database/schema.sql` の列・索引・FKに加え、DAOのフィールド設定・行入力規則・Relationを生成器が適用します。試験用ACCDBは `.tmp/tests/application.accdb` へ `-IncludeTests -NoStartup` で生成します。VBAの試験専用プロパティと `.tmp` パスを照合し、配布成果を試験DBとして開きません。正式な試験コード・fixture定義・原仕様はソースとして保持します。

マスタ保守は `MaintainClass` / `MaintainCode`、初期値の再照合は `ReapplyInitialMasters` です。画面に保守機能は増やしていません。

最新の検査状態は [build/test-results/summary.json](build/test-results/summary.json)、詳細は同ディレクトリの `application.json`・`relationship.json`・`deployment.json`・`race.json` です。今回の配置変更後にネイティブコンパイル、業務31・拡張77・検索契約42・実フォーム39、複合FK21・配布19・別2プロセス最終1席、出力パス境界8件を再実行してPASSしました。生成直後の未検証状態とPowerShell構文17本も確認しています。過去のPASSは合算しません。

Office32bit、手動のピクセル/キーボード確認、10000/10001件性能、共有切断、確定応答喪失、本番データ・本番配備、共有SQL移行、逆生成・正式採点は未実施です。原仕様の業務契約は変更していません。
