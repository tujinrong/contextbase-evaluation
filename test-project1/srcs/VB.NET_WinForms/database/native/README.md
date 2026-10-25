# VB.NET WinForms 専用DB入口

この方式のSQLCLR純関数、T-SQL保存・削除・マスタ保守入口を独立した資源として保持する。アプリケーションはVB.NET、DB側SQLCLRはSQL ServerのSAFE .NET Framework4.7.2ライブラリーとしてC#を採用する。当方式内のソースから独自DLLとSHA512を生成し、他方式のDLL・ソース・生成器を参照しない。

```powershell
./database/native/Build-Native.ps1
```

管理者が承認済み空DBへ当方式の001_schema.sqlと002_seed.sqlを適用し、CLR有効化を管理者が明示承認してから000_sqlclr.sql、010_student_api.sql、020_master_api.sqlを順に配置する。clr strict securityは維持し、TRUSTWORTHYを有効化しない。配備器は自動でDBを作成・更新しない。000内のtrusted assembly登録は配備管理者の操作であり、実DBへの適用は未実施。

prepare_save/persist_student/delete_student/save_class/save_codeはDBの実主体・役割・同一ゲート・最新データ・Raw再正規化・版・候補全件hash・監査を検査する。内部COMMITはなく、VBのSqlServerStudentService/MasterMaintenanceServiceが確定後だけ成功を通知する。一般主体の表直接DMLは禁止し、固定手続の所有者連鎖を使う。

本物のSQL Server 2022へのCLR配備、DB役割、トランザクション・競合・監査失敗は未結合。ソース生成や純関数試験は実DB配備成功の証明ではない。メッセージ定義は当VBのDomain/NativeMessages.vb。

学校年度はraw Unicode scalar最大4→共通NFKC/trim→ASCII西暦4桁・1900～9998の順で検査する。重複候補の返却列はstudent_no/student_name/birth_date/class_nameのみで、住所・電話・在籍区分などを返さない。生年月日はVB側が和暦に表示変換する。候補集合のID/版はDB内の確認用hash計算にだけ使用する。

database/native/tests/Framework/NativeFramework.Tests.csprojは当方式の配備対象と同じDLLを実CLR4.0.30319.42000上で試験し、23件PASS。000_sqlclr.sqlのSHA512と試験ロードDLLの一致も確認した。SQL Server内でのホスト実行は未実施。

配置更新: Build-Native.ps1の最終生成SQLは `build/database/native/`、SQLCLR DLL/bin/objは `.tmp/dotnet/`。原本のdatabase/native SQLとメッセージソースは通常buildでは変更しない。配備には今回生成されたbuild/database/nativeの000/010/020を使う。構文結果はbuild/test-results/sql-syntax.jsonへ固定更新する。
