<!-- spec-meta: {"schema":"spec-md/1.1","documentId":"SP2-Access-DB-T02","version":"1.0","path":"sample-project2/spec/Access/DB定義/Access/テーブル/02_m_employee.md","layout":"TABLE","table":{"logicalName":"社員","physicalName":"m_employee","profile":"ACE","primaryKey":["employee_id"],"fieldIds":{"employee_id":"T02-001","employee_no":"T02-002","employee_name":"T02-003","employee_kana":"T02-004","department_category":"T02-005","department_code":"T02-006","employment_category":"T02-007","employment_status":"T02-008","join_date":"T02-009","career_summary":"T02-010","skills":"T02-011","qualifications":"T02-012","self_pr":"T02-013","updated_at":"T02-014","updated_by":"T02-015","revision":"T02-016"}},"sheets":[{"sheet":"m_employee","kind":"TABLE","sections":[{"heading":"テーブルヘッダー","kind":"HEADER"},{"heading":"項目詳細","kind":"LIST","key":["No"],"columns":["No","論理名","物理名","PK","NOT NULL","タイプ","長さ","初期値","説明"]}]}]} -->
# 社員 テーブル仕様書

## テーブルヘッダー

| 項目 | 内容 |
| --- | --- |
| 文書ID／版 | SP2-Access-DB-T02／1.0／2026-10-28 |
| 論理／物理名 | 社員／m_employee |
| 対象 | ACE／単一ACCDB内包。物理設計・実DB適用未実施 |
| 用途／項目数 | 社員基本情報と帳票共通記載／16項目 |
| 主キー（順序） | employee_id |
| 共通規則 | [ACE物理共通制約](../01_DB定義書.md)、[基本定義](../../../基本設計書/テーブル/02_m_employee.md) |
| 一意性／件数 | employee_noは一意。社員総数200人以下 |
| 長さ・空欄 | 業務上限。PK/NOT NULLの〇以外、初期値なし・長さ非該当は空欄 |
| 項目ID | T02-{No3桁}、fieldIdsと対応 |

## 項目詳細

| No | 論理名 | 物理名 | PK | NOT NULL | タイプ | 長さ | 初期値 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 社員管理ID | employee_id | 〇 | 〇 | COUNTER |  | 自動採番 | 内部識別。不変、欠番可。 |
| 2 | 社員番号 | employee_no |  | 〇 | TEXT(6) | 6 |  | 半角数字6桁、一意、不変、先頭ゼロ保持。 |
| 3 | 氏名 | employee_name |  | 〇 | TEXT(80) | 40 |  | 表示表記を保存し、検索用の正規化は照合時だけ行う。 |
| 4 | 氏名カナ | employee_kana |  | 〇 | TEXT(160) | 80 |  | 全角カナ・長音・中点・空白。半角カナは正規化する。 |
| 5 | 部署分類 | department_category |  | 〇 | TEXT(24) | 24 | DEPARTMENT | 自動固定、利用者は変更不可。 |
| 6 | 部署 | department_code |  | 〇 | TEXT(2) | 2 |  | 部署分類と複合で汎用コード参照。 |
| 7 | 在籍分類 | employment_category |  | 〇 | TEXT(24) | 24 | EMPLOYMENT_STATUS | 自動固定、利用者は変更不可。 |
| 8 | 在籍区分 | employment_status |  | 〇 | TEXT(2) | 2 | 01 | 在職01/休職02/退職03。社員を削除する属性ではない。 |
| 9 | 入社日 | join_date |  | 〇 | DATETIME |  |  | 1900-01-01以上、業務日以下。前職経歴の期間を制限しない。 |
| 10 | 職務要約 | career_summary |  |  | LONGTEXT | 1000 |  | 改行可。 |
| 11 | スキル・得意分野 | skills |  |  | LONGTEXT | 1000 |  | 自由記入。技術経験年数の自動集計はしない。 |
| 12 | 保有資格 | qualifications |  |  | LONGTEXT | 1000 |  | 1資格1行を目安に資格名・取得年月を自由記入。 |
| 13 | 自己PR | self_pr |  |  | LONGTEXT | 1000 |  | 改行可。 |
| 14 | 更新日時 | updated_at |  | 〇 | DATETIME |  |  | 保存確定時のUTC時点。新規時にも設定。 |
| 15 | 更新者 | updated_by |  | 〇 | TEXT(40) | 20 |  | 認証主体の利用者ID。利用者表の対応IDを記録。 |
| 16 | 更新版 | revision |  | 〇 | LONG | 10.0 | 1 | 1～2147483647。全経歴を含む集約の楽観版。 |
