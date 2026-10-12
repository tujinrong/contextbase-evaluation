# SQL再導入・共有DB構成評価の結果

2026-10-12／projectId=test-project1／工程=SQL Express再導入・共有空DB作成・移行契約検査。最終状態は **基盤作成済み、アプリ移行/生成中断**。

[入力manifest](20261012-sqlserver-12-inputs.json)335ファイル、独立仕様8.0/8.1（Access DB索引8.2）、build-agent契約7.5。[文書構造検査](20261012-sqlserver-12-structure.md)問題0。入力仕様は変更していない。契約7.4→7.5は利用者の「共有SQL Server DB、できればAccess/AS400も使用」という明示構成変更を工程指示へ反映したもので、各独立仕様の再設計を推測で行ったものではない。

実際に旧LocalDB3版を正規MSIで削除、Express2025 CU9/ODBC18.7.1.1を導入し、Windows認証の `contextbase_test_project1` 1個を作成。tcp:127.0.0.1,1433、ODBC18で証明書のlocalhost期待名を指定し厳格TLS接続を検証。DBはONLINE/compatibility160/Japanese_XJIS_140_CI_AS、独自objects/assemblies/roles=0。CLR0、strict1、trusted assembly0。旧方式別5DBは作成していない。SQL2022基準の現仕様に対し、最新版Express2025は明示導入構成として扱う。

今回の実機検査8/8（x64/x86各3、現行既存DB拒否/読取り検証2）は[新規test-report](../test-report/20261012-shared-sql-validation-01/README.md)へ記録した。最初のTCP接続失敗、修復UAC取消、AUTO_CLOSE閉DBのメタデータNULLによる初回検査失敗は保持した。修復UAC取消後、既存の信頼済み証明書を検証するODBC18経路で完了した。IP SAN証明書修復の実行成功とは記録しない。

共有DB導入の前提となるrole/DMLと同名CLR実体要求の競合、Access/IBM iの構成契約を[中断報告](20261012-shared-sql-migration-stop.md)へ記録した。5 SQL方式の基礎表/seed/保存ゲートは一致しているが、共有導入・業務DDL/seed・非sysadmin認可・CRUD/競合/取消/監査、Access/RPGの移行は仕様改訂待ちで停止。既存accdbは変更していない。

MVC/Vueの新規検証SQLの局所バグ（学生物理列期待33→35）だけ修正、現DDL全7表との照合と負例を含む新規20/20静的検査を保存。rootスクリプトは5DB導入ループ/CLR trust登録を廃止し共有空DB作成・検証へ切替、厳格TLS/既存DB拒否/独自objects検査を維持した。PS5構文、計画出力、定数SQL解析は[R2](../test-report/20261012-shared-sql-root-review-r2.md)と[AUTO_CLOSE修正後R3](../test-report/20261012-shared-sql-root-review-r3.md)へ記録。旧準備検査やアプリ試験の合格を新SQL/新script版へ流用していない。

コード/仕様の独立性は[今回の隔離検査](../test-report/20261012-sqlserver-12-isolation.md)、作業パスは[変更範囲](../test-report/20261012-shared-sql-validation-01/workspace-scope.json)を参照。リポジトリ変更はagents/build-agentとtest-project1のみ。spec-eval未読取/未変更。明示依頼されたSQL/Windows導入設定以外を変更していない。旧source ZIP build10は固定履歴として保持し、今回の配備資源を含めた再包装は未実施。

最終入力hash再照合・出力version/hashは[出力manifest](20261012-sqlserver-12-outputs.json)。manifestは中断中の移行を完成扱いにするものではない。
