# SQL Server Express 17.x の独立導入

2026-10-12の利用者指示により、Windows統合認証のローカルExpress 17.xへ当方式のDBを導入する手順を準備した。SQL Server 2022を設計対象とした既存001/002 SQLは変更していない。17.xでの実SQL適合は未実施。

対象DBは `contextbase_test_project1_vue` に固定する。当フォルダーのDDL・seed・権限SQLだけを使用し、他方式のDBやソースには依存しない。

1. Windows管理者がSQL Server Express 17.xを別途導入する。sqlcmdをPATHに配置するか `-SqlCmdPath` へ実行ファイルを渡す。
2. SQL Serverの証明書を信頼できる発行者・接続ホスト名と整合する構成にする。本スクリプトは `-E -N` を使用し、`-C`・SQLパスワード・サーバー全体の設定変更は使用しない。現行Coreも `Encrypt=Mandatory;TrustServerCertificate=false` を強制するため、未信頼の自己署名証明書ではアプリ試験はできない。
3. 管理者が当方式の導入・読取検証を実行する。新規DBを作る権限、または既存の空DBにDDLを適用する権限が必要になる。既存DBは既定で拒否し、削除・置換・migrationを行わない。

```powershell
# まず未接続の計画を確認。SQL実行は一切しない。
pwsh -NoProfile -File database/Deploy-Database.ps1 -Action Install -ServerInstance '.\SQLEXPRESS' -PlanOnly

# 新規の専用DBを作成し、001→002→003→入力hash記録→004の順に適用。
pwsh -NoProfile -File database/Deploy-Database.ps1 -Action Install -ServerInstance '.\SQLEXPRESS'

# 管理者が先に同名の空DBを作成した場合だけ、明示的に空DB使用を指定。
pwsh -NoProfile -File database/Deploy-Database.ps1 -Action Install -ServerInstance '.\SQLEXPRESS' -UseExistingEmptyDatabase

# 導入済みDBの読取検証。初期データ状態も必要なら追加のswitchを指定。
pwsh -NoProfile -File database/Deploy-Database.ps1 -Action Verify -ServerInstance '.\SQLEXPRESS' -RequireInitialEmptyData
```

`001_schema.sql` は7表・104物理列・7FK・CHECK・索引・3役割とDB内SNAPSHOT分離を設定する。`002_seed.sql` は5分類70コードだけを登録し、学生・クラスを作らない。既存seed値に差分があれば上書きせず停止する。`003_web_permissions.sql` は信頼するWebアプリサービス向けのDB内権限、`004_verify_deployment.sql` は構造・有効なFK/CHECK・seedキー・役割の明示権限を読取り検証する。導入時だけ、DBのextended propertyへ当方式識別子と001/002/003のSHA256を記録する。途中で失敗したDBも保存し、自動削除や再作成は行わない。

| DB役割 | 許可する当方式アプリ操作 |
| --- | --- |
| student_viewer | 学生・クラス・分類・コードのSELECT |
| student_staff | viewerを継承。学生INSERT/UPDATE、操作履歴INSERT。学生の物理DELETEと履歴UPDATE/DELETEをDENY |
| student_admin | staffを継承。クラス・コードINSERT/UPDATE。マスタ物理DELETEと分類INSERT/UPDATE/DELETEをDENY |

現在の.NET Web状態・確認情報はサーバーメモリーに保存するため、`t_confirmation` / `t_runtime_state` へのDML権限を追加しない。学生の認可は信頼するサーバー認証主体とCore、マスタ保守CLIはDB接続主体の `student_admin` を都度確認する。DBのDML権限はサービス主体向けであり、直接SQLを実行できる一般利用者へ配布しない。

必要なら、別途作成済みのWindowsサーバーログインをDBユーザーへ関連付ける。サーバーログインの作成・変更は本スクリプトの範囲外。sysadmin・DB所有者・競合する既存の役割を拒否し、DB内ユーザー作成と明示的に選択した役割追加だけを行う。

```powershell
pwsh -NoProfile -File database/Deploy-Database.ps1 -Action BindPrincipal -ServerInstance '.\SQLEXPRESS' -ApplicationPrincipal 'COMPUTER\app-user' -ApplicationRole Staff
```

アプリ接続例（秘密情報なし）:

```text
Server=.\SQLEXPRESS;Database=contextbase_test_project1_vue;Integrated Security=true;Encrypt=true;TrustServerCertificate=false;
```

API起動プロセスの `ConnectionStrings__StudentDb` へ設定する。Windows認証はDB接続の認証であり、Web利用者のCookie認証を自動設定するものではない。

既存 `database/tests/SqlServer.IntegrationTests.csproj` はSQL Server major16と空の専用DBを要求し、自ら001/002を適用する。Express17・導入済みDBに対してそのまま実行しない。今後の結合試験で17.x・導入DB対応を実施し、新しい実行証拠を保存する。管理者・sysadminでのSQL成功を最小権限や利用者認可の合格として扱わない。実アプリサービスのWindows主体で有効な権限とTLSを別途確認する。

根拠: [sqlcmd](https://learn.microsoft.com/en-us/sql/tools/sqlcmd/sqlcmd-utility?view=sql-server-ver17)、[DB役割](https://learn.microsoft.com/en-us/sql/relational-databases/security/authentication-access/database-level-roles?view=sql-server-ver17)。
