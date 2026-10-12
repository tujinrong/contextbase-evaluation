# C# / WPF 学生管理

`SCR-STU-001` の学生検索と `SCR-STU-002` の登録・編集・参照・論理削除を実装する。Views / ViewModels / Commands / Services を分ける。共有 `StudentManagement.Core` が正規化、日付、DB 認可、マスタ、定員、候補全件の確認、版、監査と SQL Server の保存単位を受け持つ。

Windows と .NET 10 SDK（検査時 10.0.401）が必要。表と初期値は `../Database/SQLServer/` の手順で管理者が配置する。環境変数に承認済み個別 DB 主体の接続先を設定する。

```powershell
$env:STUDENT_DB_CONNECTION = 'Server=localhost;Database=StudentManagement;Integrated Security=true;Encrypt=true;TrustServerCertificate=false'
dotnet build .\StudentManagement.Wpf.csproj
dotnet run --project .\StudentManagement.Wpf.csproj
```

`ORIGINAL_LOGIN()` と DB の `student_admin` / `student_staff` / `student_viewer` ロールで権限を決める。管理者のみ削除、担当者は登録・更新、参照者は検索・参照を利用する。

これは仕様で許可された、信頼するアプリケーション内サービスによる評価構成である。本番向け EXEC-only DB 更新入口と DB 側での正規化再生成は未実装であり、本番の強いセキュリティ境界として配備しない。実 DB のロール、DML 権限、保存、競合、監査失敗は未試験。

一覧は11表示項目、和暦生年月日、西暦日本時間の更新日時を表示する。raw 検索条件と適用済み条件、入力モデルと正規化値を分離する。20/50/100 件、4 項目のソート、10,000 件上限、30 分保持を扱う。ID・版は `long`。和暦4原入力と任意日付の不正文字列を補正せず保持する。画面単位の Busy と取消・破棄で非同期処理を制御する。重複候補と理由、論理削除と理由は取消が既定の独立した確認画面で扱う。

両ネイティブ画面の表示なし / DB 接続なし smoke 検査:

```powershell
dotnet run --project ..\VB.NET_WinForms\Tests\NativeSmoke.csproj
```

| 仕様 | 実装 |
| --- | --- |
| SCR-STU-001 / SRC / EV-SRC-001～006 / OP-PAGE | StudentSearchView / StudentSearchViewModel |
| SCR-STU-002 / REG / EV-REG / UPD | StudentEditView / StudentEditViewModel / EditModel |
| 共通11 / 重複・削除確認 | DialogService / 共有 StudentManagement.Core |
| COM-CSharp_WPF / 共通01～17 / DATE-R01～06 | StudentGateway / 共有 StudentManagement.Core |
| 非同期例外・多重実行・破棄 | AsyncCommand / ViewModel / NavigationService |

マスタ保守は共有管理者 CLI を使用する。実際の画面表示・IME・DPI・読み上げ、SQL Server 往復は smoke 検査に含まない。入力版と未実施は `test-project1/report/native-implementation.md` を参照する。
