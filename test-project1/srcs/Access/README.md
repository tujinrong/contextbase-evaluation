# Access 学生管理

配布成果は `StudentManagement.accdb` の１ファイルです。４フォーム、VBA、業務５表、制御表、評価用役割表、５分類70コードを内包します。学生・クラス・監査の初期件数は０です。外部リンク表、外部 DB、外部認証設定ファイルを必要としません。

この方式の入力は [spec](spec/README.md) だけです。生成器・ソース・DB資源・試験はこのフォルダーに閉じています。配置仕様は版8.1（DB索引の書式修正版8.2）、その他の独立業務仕様は版8.0です。最新版の利用者指示に従って単体構成へ変更した理由を [方式別仕様](spec/共通/方式別/Access/01_共通実装仕様.md) に記載しています。

Windows と Microsoft Access が必要です。実機確認は 64 bit Office / Access 16.0.20430.20146、ACE DAO 16.0.20430.20032。ファイルを Access で開くと `frmStudentSearch` が起動します。起動時は未検索、20件表示、在学・休学が対象です。新規・編集・論理削除は非連結フォームから明示保存します。

認証は Windows API `GetUserNameW` の実主体と内包 `t_app_role` の一致を検査します。生成時の Windows 利用者を Admin として設定しました。別の利用者へ渡す場合は、承認した主体と Reader/Staff/Admin の役割を管理者が配備時に設定します。秘密情報はありません。ファイルを直接編集できる利用者に対する強い権限境界は、このローカル評価構成の保証外です。

再生成には Python 3 と PowerShell、Access の VBA プロジェクト参照が許可された開発環境を使用します。Access フォルダーで実行します。

```powershell
python -X utf8 tools/generate_schema.py
./Build-Access.ps1 -CreateBackend -SingleFile -Compile -Backend "$PWD/build/approved-empty-staging.accdb"
```

出力が既にある場合は上書きせず停止します。必要な成果・証拠を保存して、別の出力名を `-Frontend` / `-Backend` で指定してください。ビルド中の staging ACCDB は初期物理表の組立材料です。配布成果から staging へのリンクはありません。`-InitialUser` / `-InitialRole` で承認した初期主体を指定できます。

`database/schema.sql` は列・索引・FK の生成資源です。ACE の DEFAULT、文字列空禁止、行内 ValidationRule、複合 FK の最終適用は `Build-Access.ps1` が DAO で行います。SQL だけで同じ最終構成になると扱わないでください。

マスタ保守は管理者向け VBA 入口 `MaintainClass` / `MaintainCode` です。入力は検証前文字列を持つ `Scripting.Dictionary`、更新は対象 ID と期待版を渡します。クラス年度＋コード、固定コードの意味、保護コードは変更できません。在籍人数より少ない定員や在学・休学中クラスの停止は拒否します。承認済み初期値の再適用は `ReapplyInitialMasters` で、同値は無変更、差分は停止します。通常学生画面へ保守画面を追加していません。

試験には新規の使い捨て ACCDB を `build` 内に生成し、`-IncludeTests -NoStartup` を指定します。`tests/Test-Application.ps1` は通常業務31・拡張77・実フォーム29項目を実行します。`tests/Test-Relationship74.ps1` は任意複合 FK の最小21項目、`tests/Test-Race.ps1` は異なる Access プロセスの最終１席を検証します。`tests/Test-Deployment.ps1` は配布成果の同一ハッシュのコピーを build 内に作り、初期状態・リンク不在・起動・制約を確認します。Access がコピーの内部メタデータを変更しても配布原本は開きません。試験用モジュールと業務サンプルは配布成果に含めません。

４試験の既定の報告先はこの方式の `test-report`、RunId は実行時刻＋一意値です。既存の報告は上書きせず停止します。集約する場合だけ `-ReportDirectory` に承認した集約先を明示します。単一ファイルの業務試験では roles.conf を作りません。仕様の版と入力ハッシュを実行ごとの JSON に含めます。

DAO 業務、権限、版競合、監査失敗の取消、確認情報の再照合、続柄 NULL 制約、実フォーム・確認ダイアログ、２プロセスの最終席競合、配布成果の19検査が通過しました。試験原本は選択プロジェクトの test-report に新規保存しました。Office 32 bit、共有切断、10,000／10,001件検索性能、確定応答喪失、画面の目視配置確認は未実施です。
