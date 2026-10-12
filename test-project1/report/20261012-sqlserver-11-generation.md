# SQL Express・Windows認証・独立DB導入の準備結果

2026-10-12。projectId=test-project1、工程=ローカルSQLエンジン入れ替え/独立DB導入準備。最終状態は **Windows管理者承認待ち**。OSからUAC起動取消が返され、管理者processは起動されていない。削除・新規インストール・DB作成・実DB試験は未実施。

入力は[manifest](20261012-sqlserver-11-inputs.json)335ファイル、[構造検査](20261012-sqlserver-11-structure.md)問題0。独立仕様8.0/8.1、Access索引8.2、build-agent契約7.4。原仕様と既存生成アプリは変更しない。SQL2022 baselineに対する最新版Express2025 17.xはユーザーによる明示的導入構成変更で、各方式の専用導入文書へ記録する。spec-evalは読取/変更なし。

追加出力はagents/build-agent/scriptsのInstall-LocalSqlExpress.ps1、Setup-LocalSqlExpressAndDatabases.ps1、Start-LocalSqlExpressSetup.ps1、およびWPF/VB/MVC/Vue/COBOLそれぞれのdatabase配下の独立導入・権限・検証資源。root工程制御は方式内の資源を呼び出すだけで、方式相互のDB・コード・仕様共有を導入しない。Access accdbとRPG/Db2は変更しない。現行逆生成source ZIP 20261012-build-10は固定の旧包装結果として保持し、新しい配備資源を含む再包装はこの工程で実施していない。

実施した検査: root3構文＋WindowsPowerShell5.1計画2、Web10、COBOL28の非接続検査、WPF/VB Plan/PrepareOnly＋各16 SQLのTSql170エラー0。[独立性検査](../test-report/20261012-sqlserver-11-isolation.json)は7方式808ファイル1506参照、問題0。実アプリのmajor16統合ハーネス、SQL17実DDL/CLR/CRUD/権限/競合は未実施で、旧ビルドの合格を流用していない。

公式Express/CU9/ODBC18.7.1.1配布ファイルはtest-project1/build/sqlserver-20261012へ取得し、Microsoft署名Valid、CU9公式SHA256一致。インストール予定はSQLEXPRESS/Windows専用認証/ローカルTCP1433/localhost証明書検証/CLR strict維持、独立DB5個。旧LocalDB2016/2019/2025の登録済みMSIを削除する予定。ユーザーDBファイルのfilesystem削除は行わない。Unexpected registered instance/processがあれば保全して停止する。

[実環境記録と再開手順](../test-report/20261012-sqlserver-preparation-01/README.md)に配布SHA、OSの取消理由、実コマンド、DB名、アプリ認可の未実施を記録した。作業ファイルの変更範囲はagents/build-agentとtest-project1だけ。外部SQL/Windows管理変更は明示依頼されたが今回は実行されていない。最終source/doc hashは[今回の出力manifest](20261012-sqlserver-11-outputs.json)を参照。
