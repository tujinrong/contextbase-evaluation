# 共有SQL Server DB移行の中断報告

2026-10-12／projectId=test-project1／工程=ローカルSQL再導入・共有DB構成への変更評価。状態は **SQL基盤・空共有DBの作成完了、アプリ移行・生成停止**。

最新の利用者指示に従い、DBは `contextbase_test_project1` 1個を共有する。各方式のコード、仕様、ビルド、試験装置は独立を維持する。Accessは1個のaccdbフロントエンドと共有SQLバックエンドの構成が可能。AS400/IBM iからの利用は接続基盤とWindows主体の対応を確定できた場合に採用する。新しい構成要求を旧独立仕様の内部バグとは扱わない。

入力は独立仕様8.0/8.1（Access DB索引8.2）とbuild-agent工程契約7.5。[今回の入力manifest](20261012-sqlserver-12-inputs.json)は335ファイル、[文書構造検査](20261012-sqlserver-12-structure.md)は問題0。機械的な文書構造合格は、以下の共有配置契約の整合性合格ではない。spec-evalは読取り/変更なし。

| 問題 | 根拠と影響 | 再開条件 |
| --- | --- | --- |
| SHARED-SQL-ROLE-001 | Nativeのstudent_viewerへのDML DENYが、Web/COBOLの包含ロールを通じstaff/adminへ継承される。直接DMLのGRANTと同居すると業務更新が拒否される。 | Native・Web・CGIの主体、許可DB入口、ロール構成を同時に成立する形へ改訂し、非sysadmin/非dbo主体で検証可能にする。 |
| SHARED-SQL-ENTRY-002 | WPF/VBが同じStudentNativeNormalization名へ異なるbinary SHA512を厳密要求する。両専用導入/検証を無変更で同じDBへ適用できない。 | 配置する正規化入口の名前・所有・版・実体と各方式の導入/呼出/検証を一致させる。 |
| SHARED-SQL-DEPLOY-003 | 各方式は従来の別DB名と単独markerに固定されている。 | 共有DB名・重複DDLの扱い・独立配備手順・markerを各方式の完全な仕様内で確定する。 |
| SHARED-ACCESS-001〜005 | 現accdbはSELF/ACE、独自ローカル役割、32bit ID/数値版、DAO Workspaceとt_write_guardに固定。SQL接続への置換だけでは同じ主体・保存/監査・確認・排他保証にならない。 | 1accdbのSQL接続アダプター、SQL主体/役割、型、サーバー側保存境界・確認・正規化・時刻・全方式の共通ゲートをAccess独立仕様へ確定する。 |
| SHARED-RPG-001（本報告の集約ID） | 現SQLRPGLEはDb2/IBM iに依存。JDBC/DRDA等の接続経路はあるが、WindowsローカルSSPI主体を遠隔IBM iからそのまま使えない。 | 採用するIBM i/JVM/driver、接続方式、到達可能なendpoint、Windows主体対応（Kerberos等）、型・同一接続Tx・全方式の排他を確定する。 |

ファイル・行・相反する記載・入力SHA256の詳細は [5 SQL方式の比較](20261012-shared-sql-schema-assessment.md)、[Access調査](20261012-shared-sql-access-assessment.md)、[RPG調査](20261012-shared-sql-rpg-assessment.md)を参照。5 SQL方式の001実行DDLと002 seedは一致し、基礎表7個106物理列（学生35）、分類5件/コード70件を共有できる。SQL5方式の保存ゲート名も一致する。一方、Access/Db2のローカルゲートをそのまま共有SQLへ持ち込む保証は未確定。

局所バグLOCAL-VERIFY-004は、MVC/Vue検証SQLの学生期待列数33→35だけを修正した。DDL全7表との照合と負例を含む[新規静的検査20/20](../test-report/20261012-web-deployment-column-validation-r3-final.md)を保存した。本体DDL・仕様・アプリコード・既存accdbは変更していない。この訂正は共有配置の構造衝突を解消しない。

実際に作成したDBは空（user objects/assemblies/application rolesすべて0）。CLR有効化・信頼登録・業務DDL/seed・権限導入・共有CRUD・Access/RPG移行は実施していない。[SQL基盤の新規実測結果](../test-report/20261012-shared-sql-validation-01/README.md)とアプリ結合未実施を区別する。別Agentによる各独立仕様の改訂と再開指示後、新しい入力版/hash/実行IDで検査し、実装・非管理者認可・CRUD・競合・取消・監査を検証する。
