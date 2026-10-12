# Web 2方式・Express17導入の準備検査

2026-10-12。projectId=test-project1。SQL Serverのインストール・SQL実行は行わず、方式別導入ファイルを準備した。rootの管理者起動はUAC取消によりインストール未実施。

| 方式 | 固定DB名 | 方式内の導入入口 |
| --- | --- | --- |
| CSharp_ASPNET | contextbase_test_project1_mvc | srcs/CSharp_ASPNET/database/Deploy-Database.ps1 |
| Vue_CSharpAPI | contextbase_test_project1_vue | srcs/Vue_CSharpAPI/database/Deploy-Database.ps1 |

各方式に独立した `Deploy-Database.ps1`、`003_web_permissions.sql`、`004_verify_deployment.sql`、`EXPRESS17.md` を追加し、database/READMEを更新した。001_schema.sql・002_seed.sqlは変更していない。どちらも7表・104物理列・7FK、5分類70コード、学生0・クラス0を初期状態とする。他方式ソースやライブラリーへの参照は追加していない。

PowerShell 7.6.5で10/10の未接続検査を実行した。対象は2入口の完全構文parse、各Install/Verify/BindPrincipalのPlanOnly出力、Windows認証・暗号化・証明書検証の引数、禁止されたDB削除・サーバー設定・ログイン変更の不在、Verifyの読取専用、principalのSQL literal escape、principal省略拒否。SQL接続0・SQL実行0。SQL文のサーバー側parse・実権限・DB整合・アプリ結合は未実施。

導入はWindows認証のsqlcmd（ODBC）を `-E -N -x -X1` で呼び出す。TLS証明書検証を維持し、パスワード・`-C`を使用しない。Express major17・ローカルWindows接続を確認し、指定DBが未作成なら作成する。既存DBは既定で拒否し、`-UseExistingEmptyDatabase` 明示時だけ空DBを使用する。既存データ・オブジェクト・方式markerがあれば停止する。001→002→003→入力hashのDB内extended property記録→004の順。途中失敗のDBも削除しない。

DB内権限はViewer=業務4表SELECT、Staff=Viewer継承＋学生INSERT/UPDATE＋履歴INSERT、Administrator=Staff継承＋クラス/コードINSERT/UPDATE。学生・マスタの物理削除、履歴改変、分類保守にはDENYを設定する。未使用の確認/状態テーブルDML、サーバーログイン、sysadmin/db_owner付与、サーバー全体の設定変更は追加しない。ApplicationPrincipalの任意指定は、既存WindowsサーバーログインをDBユーザー/1役割に関連付けるだけで、sysadmin・DB所有者・既存の異なる役割を拒否する。

rootが同名の空DBを先に作成した場合の実コマンド:

```powershell
pwsh -NoProfile -File test-project1/srcs/CSharp_ASPNET/database/Deploy-Database.ps1 -Action Install -ServerInstance '.\SQLEXPRESS' -UseExistingEmptyDatabase
pwsh -NoProfile -File test-project1/srcs/Vue_CSharpAPI/database/Deploy-Database.ps1 -Action Install -ServerInstance '.\SQLEXPRESS' -UseExistingEmptyDatabase
pwsh -NoProfile -File test-project1/srcs/CSharp_ASPNET/database/Deploy-Database.ps1 -Action Verify -ServerInstance '.\SQLEXPRESS' -RequireInitialEmptyData
pwsh -NoProfile -File test-project1/srcs/Vue_CSharpAPI/database/Deploy-Database.ps1 -Action Verify -ServerInstance '.\SQLEXPRESS' -RequireInitialEmptyData
```

DBを各スクリプトが新規作成する場合は `-UseExistingEmptyDatabase` を外す。`-PlanOnly` を付ければSQLクライアントも起動しない。sqlcmdがPATHにない場合は `-SqlCmdPath` を指定する。実際のinstance名と信頼できる証明書の接続ホスト名へServerInstanceを合わせる。

現行CoreはEncrypt=Mandatory/TrustServerCertificate=falseを強制する。未信頼のExpress自己署名証明書ではアプリ接続不可。また、現行database/testsはmajor16・空DB限定で自身が001/002を適用するため、Express17・導入済みDBでそのまま実行しない。今後の明示的結合試験で対応する。管理者/sysadminの導入成功を実アプリWindows主体の最小権限・利用者認可の合格として扱わない。

同名JSONに各入力hashと各PlanOnlyの実出力、生ログに実計画を保存した。旧報告や旧試験結果は上書きしていない。処理系・TLS・Windows主体によるライブSQL検証、MVC/API画面の結合試験は未実施。

技術根拠: [Microsoft sqlcmd](https://learn.microsoft.com/en-us/sql/tools/sqlcmd/sqlcmd-utility?view=sql-server-ver17)、[database roles](https://learn.microsoft.com/en-us/sql/relational-databases/security/authentication-access/database-level-roles?view=sql-server-ver17)、[connection authentication](https://learn.microsoft.com/en-us/sql/t-sql/functions/connectionproperty-transact-sql?view=sql-server-ver17)。
