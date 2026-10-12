# Access 学生管理

配布成果は `StudentManagement.accdb` の１ファイルです。４フォーム、VBA、業務５表、制御表、評価用役割表、５分類70コードを内包します。学生・クラス・監査の初期件数は０です。外部リンク表、外部 DB、外部認証設定ファイルを必要としません。

2026-10-12 の実画面確認で、生成器の旧MDB形式、検索初期チェックのNULL、検索「すべて」の空表示、通知の中点「・」の文字化けを修正しました。現在は `NewCurrentDatabase(..., 12)` によりACCDBを生成し、初期チェックのFalseを明示します。現R6成果のSHA-256は `D1777167FD7423BF4399F05D006519FD5A8E005A6FEF2E56B1A8F11AAD73EC87`。旧成果は `build/20261012-evidence-01-backup/StudentManagement.pre-format-fix.accdb` に元のSHA-256 `838F5FE63826FCE58FACE6C5102D363AF41C3EF433D6B2D7229C8D5DE0C93DE5` のまま保存しています。同フォルダーにはR4を `StudentManagement.r4-before-all-display.accdb`、R5を `StudentManagement.r5-before-encoding.accdb` として保存し、R5のSHA-256 `0547CB5FF9D70C5F17F97D42E8D14E5EAEAB6D3CDEDD2B3F0DA9744960B22E2A` も保持しました。

この実機のシステムANSIコードページ936では、VBEへの `AddFromString` がU+30FBを `?` に変換していました。3モジュール内の該当23文字だけを `ChrW(&H30FB)` で構築します。全production VBA文字列リテラルを検査し、その他の非表現文字はありません。実VBAの58通知はUTF-8の方式内仕様原文とPowerShell側で完全一致を照合しました。期待値をVBEへ渡して同じ文字化けを起こす検査はしていません。

検索条件の初期表示は年度・学年・クラス・都道府県の「すべて」です。検索画面専用の選択値0／`*`は、フォームのReadCriteriaと候補連動でNULLへ戻します。学年「00」は実際の学年コードとして保持し、登録画面の値やDB契約へ選択用値を渡しません。クラス候補は年度降順、学年表示順、クラス表示順、コード、IDの順で、学年名称を表示します。不適合クラス解除時のW-STU-107通知も一般変更文言で上書きしません。

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

R5工程の新規試験は `test-project1/test-report/20261012-evidence-01/Access-r5/` に保存しています。業務137・続柄21・配布19、形式／初期Boolean10、検索表示／連動／警告21、別Accessプロセスの１席競合が通過しました。これらはR5時点の検査結果です。

最終R6の新規検査は `test-project1/test-report/20261012-evidence-01/Access-r6/` に保存しました。通知58・項目ラベル1・候補SQLと確認フォーム13・配布19の計91チェック、VBAコンパイル、PS5構文5本が通過しています。R5の業務137等はR6で再実行しておらず、新改訂の合格数に加算していません。配布原本は同一バイトのコピーで検査し、学生・クラス・監査0、試験モジュールなしを確認してから置換しました。撮影用の架空学生３件は `build/20261012-evidence-01-ui-r6/` の別DBだけにあります。共有SQLへの配備・接続・認可試験は実行していません。build-10の旧ソースZIPは今回更新していません。
