# SQL Server 2025 Express 専用DB導入

2026-10-12の明示指示により、ローカルSQL Server 2025 Express（17.x）、Windows統合認証を新しい実行環境とする。方式内spec版8.0/8.1と既存DDLのSQL Server 2022基準は、この導入準備では変更していない。既定のDB互換性レベルは160。170を使う場合は`-CompatibilityLevel 170`を明示し、新しい実行証拠で検査する。SQL2025の実行成功はまだ確認していない。

DB名は`contextbase_test_project1_vb`に固定し、この方式内の次の資源だけを使用する。順番は001_schema.sql、002_seed.sql、native/000_sqlclr.sql、native/010_student_api.sql、native/020_master_api.sql。000のサーバー信頼登録を含む先頭batchは実行しない。埋め込みDLLのSHA512を再計算し、宣言されたhashとの一致を先に検査する。

SQLCLR SHA512: `80CB01ECF43DADE7644B55FE9583C74ED9F3B369997846401BC1E148A48CC9B780A62D356ECEF8E4B12167494F6BEACB34D868BAF10BE50250810ADED806F433`。

管理者はCLR enabled=1、CLR strict security=1、当該exact hashの信頼登録、localhostをSANに持つ信頼済みサーバー証明書を別工程で準備する。このスクリプトはグローバル設定・信頼登録・Windowsアカウント・SQL LOGINを作成/変更しない。[CLR strict security](https://learn.microsoft.com/en-us/sql/database-engine/configure-windows/clr-strict-security?view=sql-server-ver17)、[信頼するアセンブリーの登録](https://learn.microsoft.com/en-us/sql/relational-databases/system-stored-procedures/sys-sp-add-trusted-assembly-transact-sql?view=sql-server-ver17)の公式要件に従う。

調査済みのODBC sqlcmd 16.0.1000.6を使用する。`-E -N`でWindows認証・暗号化・証明書検証を要求し、`-C`による検証省略や未対応の`-Nm`/`-F`は使わない。接続先は`tcp:localhost,1433`。CertificateHostNameは接続先hostnameの確認値であり、証明書名を上書きしない。[sqlcmdの暗号化オプション](https://learn.microsoft.com/en-us/sql/tools/sqlcmd/sqlcmd-utility?view=sql-server-ver17)を参照。

```powershell
# この方式のディレクトリで実行する。Planは接続しない。
.\database\Install-ProjectDatabase2025.ps1 -Mode Plan -Server 'tcp:localhost,1433'

# 管理者による初回配備。既存DBがあれば停止し、drop/上書きしない。
.\database\Install-ProjectDatabase2025.ps1 -Mode DeployNew `
  -Server 'tcp:localhost,1433' -AppWindowsLogin 'DELL_DISKTOP1\tujin' `
  -AllowAdministrativeAppLogin -DatabaseOwnerLogin sa `
  -RunId 20261012-vb-deploy01

# 管理者によるread-only検証。AppWindowsLoginを省略する。
.\database\Install-ProjectDatabase2025.ps1 -Mode Validate `
  -Server 'tcp:localhost,1433' -RunId 20261012-vb-validate01
```

AppWindowsLoginは省略可能。指定時は既存の個別Windows LOGINを要求し、方式DBのUSERと選択した1役割を作成する。役割はstudent_viewer/student_staff/student_admin。閲覧はSELECT、Staff/Adminはprepare_save/persist_student、Adminだけdelete_student/save_class/save_codeを使用する。process_saveは直接EXEC不可、業務/確認表の直接DMLは禁止。`-AllowAdministrativeAppLogin`は初回管理配備だけの明示指定であり、sysadminを一般アプリ主体として検証済みにはしない。

現在Windowsユーザーを将来のアプリ主体にも使う場合、そのユーザーがDB ownerだと権限変更後もdboになる。`-DatabaseOwnerLogin sa`は既存の別ownerへDB所有者を割り当てる操作で、saへのSQL認証接続・有効化は行わない。USERを作る前に所有者を分ける。今回sysadmin降格やWindows管理者グループの追加は行わず、非sysadmin主体の認可・アプリSQL書込みは未実施として残す。

Validateは7表・3役割・5 native手続・5分類/70以上のコード、snapshot、TRUSTWORTHY OFF、配備アセンブリーのexact hashを検査し、read-onlyのnormalize_reasonでSQL Server内のCLRホスト実行を確認する。成功結果は実行時だけPASSとして保存する。

将来、実際の非sysadmin・非dbo・非db_ownerのWindows主体を用意した場合は、そのtokenで`-Mode ValidateApp -AppWindowsLogin '<MACHINE\user>'`を実行する。実セッションのsysadmin=0・DB USER・role・SELECT・直接DML拒否・公開EXEC可否を確認し、接続先と対象DBを固定する。管理者のEXECUTE AS USERによるメタ権限probeと、実Windowsセッションの認証試験を区別する。

CreateEmptyは新規DBと任意USERだけを作り、schema/seed/nativeは配備しない。PrepareOnlyは任意モードのSQLを方式内test-reportへ書き出し、SQL接続・実行をせずPREPARED_NOT_EXECUTEDと記録する。RunIdは新規値を要求し、既存のログ・レポートを上書きしない。途中失敗したDBも自動削除せず保持する。

既存のdatabase/testsハーネスはSQL2022 major16と初期emptyDBを要求するため、この配備済みSQL2025 DBへそのまま実行しない。SQL2025対応の試験前条件と新規fixtureを別工程で準備する。現在のPowerShell Parse/Plan/PrepareOnlyとTSql170Parserによる16 SQLファイルの構文検査は通過したが、実DB接続・SQL実行・CLRホスト・認可・CRUD・競合は未実施。新証拠はtest-report/20261012-sql2025-r3-setup-static-results.jsonに保存した。

R3のsqlcmd選択はGet-Command候補のProductMajorPart>=16を満たす最初の1件だけを使用する。FileVersionは年版で始まるため判定に使用しない。明示パスは1個のファイルとして解決し、旧ProductMajor9や欠落ファイルを拒否する。既定/明示modern・旧版拒否・欠落拒否・Parseの5件と、各16 SQL構文検査を接続なしで再実行して通過した。R2証拠は保持した。
