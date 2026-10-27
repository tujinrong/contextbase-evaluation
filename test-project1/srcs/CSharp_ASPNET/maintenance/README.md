# 当方式の管理者マスタ保守

共有DBでは`STUDENT_DATABASE_PROFILE=SharedAccess`と`STUDENT_DB_CONNECTION`を明示する。接続主体のsysadmin/db_owner、またはORIGINAL_LOGINに対応する`t_app_role`のAdminを検査する。2026-10-27に実DBの既存クラスを無変更保存し、版・データを変えないことを確認した。以下のstudent_admin記述はNative専用。

Core内のClassChange/CodeChangeを承認済みJSONで受け付ける。DBのORIGINAL_LOGIN()とstudent_adminを毎回再検査する。年度・コード・期間・定員・参照・期待版・理由・ゲート・監査を同一トランザクションで扱う。Native専用の実SQL結合は未実施。

```powershell
$env:STUDENT_DB_CONNECTION = 'Server=YOUR-SERVER;Database=YOUR-DB;Integrated Security=True;Encrypt=True;TrustServerCertificate=False'
dotnet run --project maintenance/StudentMaintenance.csproj -- class approved-class.json
dotnet run --project maintenance/StudentMaintenance.csproj -- code approved-code.json
```

このCLIは承認済みDB管理者の保守工程用。一般利用者の学生UI接続に管理者のDML権限を付与しない。JSONの項目はCore/MasterMaintenanceService.csに定義する。秘密と個人値を出力へ記録しない。
