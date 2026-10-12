# build-agent

対象は利用者が選んだtest-project1。契約はAGENT.md、起動指示はPROMPT.md。方式ごとのsrcs/方式/specから生成し、コード・DB資源・生成器・試験を当該方式内で完結させる。利用者の2026-10-12追加指示により、実行時SQL Server DBは1個を共有する。方式間の仕様・コードは独立を維持する。

工程制御だけをこのAgentに置く。preflight.mjsが現行仕様の構造と入力版/hashを固定し、問題ならreportへ保存して中断する。manifest.mjsは入力hashの変化がないことを確認して出力hashを保存する。履歴資料を現在の合格として使用しない。

```powershell
node agents/build-agent/scripts/preflight.mjs --project test-project1 --run-id UNIQUE-ID
node agents/build-agent/scripts/verify-independent.mjs UNIQUE-TEST-ID CSharp_ASPNET Vue_CSharpAPI
node agents/build-agent/scripts/check-isolation.mjs UNIQUE-ISOLATION-ID
python -X utf8 agents/build-agent/scripts/package-source.py UNIQUE-ID
python -X utf8 agents/build-agent/scripts/verify-packages.py UNIQUE-ID
node agents/build-agent/scripts/manifest.mjs --project test-project1 --run-id UNIQUE-ID
```

原仕様を含めない逆生成入力はpackage-source.pyで方式別ZIPを生成する。独立化用のisolate-*.mjsとsplit-dotnet-tests.mjsは旧入力からの一度限りの移送で、完了後の現行生成器ではない。
verify-packages.pyは各ZIPの全メンバーhashを照合し、当方式build/source-isolation-実行IDへ別々に展開して独立ビルドする。ZIPのproduction入口は除外仕様や試験を要求しない形へ変換し、変換前後hashを方式別に記録する。manifest.mjsは包装後に元ソースが変化していないことも確認する。既存ZIP・実行ID・展開先を上書きしない。

全体docs、他Agent、他project、spec-evalは変更しない。DB実機/対象処理系の欠如・配備未確認は試験報告へ記録する。

SQL Expressの新規導入を明示依頼された場合はStart-LocalSqlExpressSetup.ps1がWindowsのUAC承認を要求し、Setup-LocalSqlExpressAndDatabases.ps1が1個の空の共有DBを作成する。-PlanOnlyでは昇格・接続・変更をしない。既存SQLインスタンス/DB/実行記録を上書きしないので、導入済み環境でインストーラーを再実行しない。Create-SharedSqlDatabase.ps1の既定は計画、-Executeは存在しない共有DBの作成、-VerifyOnlyは読取り検証。接続はODBC18、tcp:127.0.0.1,1433、Windows認証、Encrypt=Yes、TrustServerCertificate=No、HostnameInCertificate=localhostを使う。

2026-10-12に旧LocalDB3版を削除し、Express2025 CU9/ODBC18を導入、contextbase_test_project1を空DBとして作成した。共有権限・同名SQLCLR契約が衝突するため、アプリの共有DB移行はreportへ記録して停止中。Accessの1accdb成果は保持し、SQLフロントエンド化とIBM i接続は仕様修正後に実装する。実測と未実施はtest-project1/test-report/20261012-shared-sql-validation-01/README.mdを参照。Repair-LocalSqlExpressConnection.ps1はIP SAN証明書の限定修復用だが、今回の修復UACは取消され未実行。ODBC18の期待証明書名指定で厳格TLS接続を実測した。
