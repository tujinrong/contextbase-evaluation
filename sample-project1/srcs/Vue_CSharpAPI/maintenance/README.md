# 当方式の管理者マスタ保守

Core内のClassChange/CodeChangeを承認済みJSONで受け付ける。DBのORIGINAL_LOGIN()とstudent_adminを毎回再検査する。年度・コード・期間・定員・参照・期待版・理由・ゲート・監査を同一トランザクションで扱う。実SQL結合は未実施。

```powershell
$env:STUDENT_DB_CONNECTION = 'Server=YOUR-SERVER;Database=YOUR-DB;Integrated Security=True;Encrypt=True;TrustServerCertificate=False'
dotnet run --project maintenance/StudentMaintenance.csproj -- class approved-class.json
dotnet run --project maintenance/StudentMaintenance.csproj -- code approved-code.json
```

このCLIは承認済みDB管理者の保守工程用。一般利用者の学生UI接続に管理者のDML権限を付与しない。JSONの項目はCore/MasterMaintenanceService.csに定義する。秘密と個人値を出力へ記録しない。
