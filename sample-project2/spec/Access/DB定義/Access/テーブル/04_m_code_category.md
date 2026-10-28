<!-- spec-meta: {"schema":"spec-md/1.1","documentId":"SP2-Access-DB-T04","version":"1.0","path":"sample-project2/spec/Access/DB定義/Access/テーブル/04_m_code_category.md","layout":"TABLE","table":{"logicalName":"コード分類","physicalName":"m_code_category","profile":"ACE","primaryKey":["category_id"],"fieldIds":{"category_id":"T04-001","category_name":"T04-002"}},"sheets":[{"sheet":"m_code_category","kind":"TABLE","sections":[{"heading":"テーブルヘッダー","kind":"HEADER"},{"heading":"項目詳細","kind":"LIST","key":["No"],"columns":["No","論理名","物理名","PK","NOT NULL","タイプ","長さ","初期値","説明"]}]}]} -->
# コード分類 テーブル仕様書

## テーブルヘッダー

| 項目 | 内容 |
| --- | --- |
| 文書ID／版 | SP2-Access-DB-T04／1.0／2026-10-28 |
| 論理／物理名 | コード分類／m_code_category |
| 対象 | ACE／単一ACCDB内包。物理設計・実DB適用未実施 |
| 用途／項目数 | 固定分類／2項目 |
| 主キー（順序） | category_id |
| 共通規則 | [ACE物理共通制約](../01_DB定義書.md)、[基本定義](../../../基本設計書/テーブル/04_m_code_category.md) |
| 件数・変更 | 3行固定。保守画面で追加/変更/削除しない |
| 長さ・空欄 | 業務上限。PK/NOT NULLの〇以外、初期値なし・長さ非該当は空欄 |
| 項目ID | T04-{No3桁}、fieldIdsと対応 |

## 項目詳細

| No | 論理名 | 物理名 | PK | NOT NULL | タイプ | 長さ | 初期値 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 分類ID | category_id | 〇 | 〇 | TEXT(24) | 24 |  | DEPARTMENT、EMPLOYMENT_STATUS、PROJECT_ROLEのいずれか。 |
| 2 | 分類名 | category_name |  | 〇 | TEXT(80) | 40 |  | 部署、在籍区分、案件役割。 |
