# VB.NET / WinForms 学生管理

`SCR-STU-001` の学生検索と `SCR-STU-002` の登録・編集・参照・論理削除を実装する。フォーム、Designer、Presenter、業務サービスを分け、共有 `StudentManagement.Core` が正規化、認可、コード・クラス、定員、重複確認、版検査、監査、SQL Server の確定単位を受け持つ。

Windows と .NET 10 SDK（検査時 10.0.401）が必要。SQL Server の表と初期値は `../Database/SQLServer/` の手順で管理者が配置する。接続先は環境変数 `STUDENT_DB_CONNECTION` を指定する。

```powershell
$env:STUDENT_DB_CONNECTION = 'Server=localhost;Database=StudentManagement;Integrated Security=true;Encrypt=true;TrustServerCertificate=false'
dotnet build .\StudentManagement.WinForms.vbproj
dotnet run --project .\StudentManagement.WinForms.vbproj
```

実行主体は SQL Server の `ORIGINAL_LOGIN()`、ロールは `student_admin` / `student_staff` / `student_viewer` から取得する。管理者のみ削除、担当者は登録・更新、参照者は検索と参照を利用する。共有資格情報ではなく承認済み個別 DB 主体を設定する。

これは仕様で許可された、信頼するアプリケーション内サービスによる評価構成である。本番向け EXEC-only DB 更新入口と DB 側での正規化再生成は未実装であり、本番の強いセキュリティ境界として配備しない。ロールと直接 DML 権限の配備は別途必要。DB に接続した保存、競合、認可、履歴失敗の試験は未実施。

検索は raw 入力と適用済み条件を分離し、20/50/100 件、4 種類の並び順、10,000 件上限、30 分の画面保持期限を扱う。学生 ID・版・クラス ID は `Long` を維持する。登録の19業務項目、和暦4原入力、年度・学年補助、任意 NULL、元スナップショット、確認情報を分離する。不正日付は原文字列のまま保持する。重複確認と削除確認は取消を既定とし、確認理由を必須にする。

画面を表示せず DB に接続しない smoke 検査は次で実行する。実際の画面表示、IME、DPI、DB の往復はこの検査に含まない。

```powershell
dotnet run --project .\Tests\NativeSmoke.csproj
```

| 仕様 | 実装 |
| --- | --- |
| SCR-STU-001 / SRC / EV-SRC-001～006 / OP-PAGE | Forms/FrmStudentSearch.*、Presenters/StudentSearchPresenter.vb |
| SCR-STU-002 / REG / EV-REG / UPD | Forms/FrmStudentEdit.*、Presenters/StudentEditPresenter.vb |
| REG-005 / DATE-R01～06 / UI-15 | Controls/JapaneseBirthDateControl.vb、共有 JapaneseDateService |
| 任意日付の原入力保持 | Controls/NullableDateControl.vb |
| COM-VB.NET_WinForms / 共通01～17 | Application/StudentApplicationService.vb、共有 StudentManagement.Core |
| 共通11 / 重複・削除確認 | Forms/ConfirmationDialog.vb、共有サービス |

マスタ保守は共有の管理者 CLI を使用する。詳細な検査結果と未実施は `test-project1/report/native-implementation.md` を参照する。
