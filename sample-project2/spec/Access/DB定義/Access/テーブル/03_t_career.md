<!-- spec-meta: {"schema":"spec-md/1.1","documentId":"SP2-Access-DB-T03","version":"1.0","path":"sample-project2/spec/Access/DB定義/Access/テーブル/03_t_career.md","layout":"TABLE","table":{"logicalName":"社員経歴","physicalName":"t_career","profile":"ACE","primaryKey":["career_id"],"fieldIds":{"career_id":"T03-001","employee_id":"T03-002","start_month":"T03-003","end_month":"T03-004","company_name":"T03-005","project_name":"T03-006","description":"T03-007","duties":"T03-008","achievements":"T03-009","technologies":"T03-010","role_category":"T03-011","role_code":"T03-012","team_size":"T03-013","phases":"T03-014"}},"sheets":[{"sheet":"t_career","kind":"TABLE","sections":[{"heading":"テーブルヘッダー","kind":"HEADER"},{"heading":"項目詳細","kind":"LIST","key":["No"],"columns":["No","論理名","物理名","PK","NOT NULL","タイプ","長さ","初期値","説明"]}]}]} -->
# 社員経歴 テーブル仕様書

## テーブルヘッダー

| 項目 | 内容 |
| --- | --- |
| 文書ID／版 | SP2-Access-DB-T03／1.0／2026-10-28 |
| 論理／物理名 | 社員経歴／t_career |
| 対象 | ACE／単一ACCDB内包。物理設計・実DB適用未実施 |
| 用途／項目数 | 社員の会社・案件経歴／14項目 |
| 主キー（順序） | career_id |
| 共通規則 | [ACE物理共通制約](../01_DB定義書.md)、[基本定義](../../../基本設計書/テーブル/03_t_career.md) |
| 件数・順序 | 社員1人0～20件。出力は開始年月降順・経歴ID降順 |
| 長さ・空欄 | 業務上限。PK/NOT NULLの〇以外、初期値なし・長さ非該当は空欄 |
| 項目ID | T03-{No3桁}、fieldIdsと対応 |

## 項目詳細

| No | 論理名 | 物理名 | PK | NOT NULL | タイプ | 長さ | 初期値 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 経歴ID | career_id | 〇 | 〇 | COUNTER |  | 自動採番 | 不変。画面内の未保存行識別子と分ける。 |
| 2 | 社員管理ID | employee_id |  | 〇 | LONG |  |  | 社員の主キー参照。親のない明細は不可。 |
| 3 | 開始年月 | start_month |  | 〇 | DATETIME |  |  | 1900-01～業務年月、月初日で保存。 |
| 4 | 終了年月 | end_month |  |  | DATETIME |  |  | 開始年月以上、業務年月以下、月初日。NULLは継続中。 |
| 5 | 会社名 | company_name |  | 〇 | TEXT(200) | 100 |  | その経歴の所属会社。前職を含む。 |
| 6 | 案件名 | project_name |  | 〇 | TEXT(200) | 100 |  | 案件名または担当職務名。顧客等は匿名表記可。 |
| 7 | 業務概要 | description |  | 〇 | LONGTEXT | 1000 |  | 案件・職務の目的や概要。 |
| 8 | 担当業務 | duties |  | 〇 | LONGTEXT | 1000 |  | 本人の担当範囲。 |
| 9 | 実績・成果 | achievements |  |  | LONGTEXT | 1000 |  | 成果を自由記入。数値成果を必須にしない。 |
| 10 | 技術環境 | technologies |  |  | LONGTEXT | 500 |  | OS・言語/FW・DB等を1欄に自由記入。 |
| 11 | 役割分類 | role_category |  | 〇 | TEXT(24) | 24 | PROJECT_ROLE | 自動固定。 |
| 12 | 役割 | role_code |  | 〇 | TEXT(2) | 2 |  | 役割分類と複合で汎用コード参照。 |
| 13 | チーム人数 | team_size |  | 〇 | SHORT | 3.0 |  | 1～999の整数。個人担当も1として登録。 |
| 14 | 担当工程 | phases |  |  | LONGTEXT | 200 |  | 要件整理・設計・開発・運用等を自由記入。 |
