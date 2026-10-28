<!-- spec-meta: {"schema":"spec-md/1.1","documentId":"SP2-CSharp_ASPNET-DB-T04","version":"1.0","path":"sample-project2/spec/CSharp_ASPNET/DB定義/SQLServer/テーブル/04_m_code_category.md","layout":"TABLE","table":{"logicalName":"コード分類","physicalName":"m_code_category","profile":"SQLServer2022","primaryKey":["category_id"],"fieldIds":{"category_id":"T04-001","category_name":"T04-002"},"schema":"dbo"},"sheets":[{"sheet":"m_code_category","kind":"TABLE","sections":[{"heading":"テーブルヘッダー","kind":"HEADER"},{"heading":"項目詳細","kind":"LIST","key":["No"],"columns":["No","論理名","物理名","PK","NOT NULL","タイプ","長さ","初期値","説明"]}]}]} -->
# コード分類 物理テーブル定義

## テーブルヘッダー

| 項目 | 内容 |
| --- | --- |
| 文書ID／版 | SP2-CSharp_ASPNET-DB-T04／1.0／2026-10-28 |
| 論理／物理名 | コード分類／dbo.m_code_category |
| 対象DB | SQL Server 2022 Express、SampleProject2_Career（専用新規DBの設計） |
| 主キー（構成順） | category_id |
| 項目数 | 2 |
| 対応論理定義 | [基本テーブル](../../../基本設計書/テーブル/04_m_code_category.md)。fieldIdsと項目順/業務長を保持 |
| 制約・索引・更新境界 | PK(category_id)、固定3分類のCHECK。通常アプリで追加/変更/削除不可。 |
| 共通定義 | [DB定義](../01_DB定義書.md)。型容量/NULL/既定値、同時保存ゲート、接続・取消・初期設定の正本 |
| 型・長さ・NULL | タイプは実SQL型、長さは従前の業務上限。NOT NULLの〇以外はNULL可。空欄は初期値なし/非適用、明示値0/01/1は保持 |
| 実施状態 | 物理設計のみ。DDL/SQL実行・投入・製品検証未実施 |

## 項目詳細

| No | 論理名 | 物理名 | PK | NOT NULL | タイプ | 長さ | 初期値 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 分類ID | category_id | 〇 | 〇 | varchar(24) | 24 |  | DEPARTMENT、EMPLOYMENT_STATUS、PROJECT_ROLEのいずれか。 |
| 2 | 分類名 | category_name |  | 〇 | nvarchar(80) | 40 |  | 部署、在籍区分、案件役割。 容量はUTF-16単位、長さ列の業務上限はRuneで別検査。 原値保持はLatin1_General_100_BIN2。 |
