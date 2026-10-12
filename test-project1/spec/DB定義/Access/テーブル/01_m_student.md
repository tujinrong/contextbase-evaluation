<!-- spec-meta: {"schema":"spec-md/1.1","documentId":"DBDEF-ACCESS-M_STUDENT","version":"7.2","path":"test-project1/spec/DB定義/Access/テーブル/01_m_student.md","layout":"TABLE","table":{"logicalName":"学生基本情報","physicalName":"m_student","profile":"Access","primaryKey":["student_id"],"fieldIds":{"student_id":"DB-M_STUDENT-STUDENT_ID","student_no":"DB-M_STUDENT-STUDENT_NO","student_name":"DB-M_STUDENT-STUDENT_NAME","student_name_kana":"DB-M_STUDENT-STUDENT_NAME_KANA","name_key":"DB-M_STUDENT-NAME_KEY","kana_key":"DB-M_STUDENT-KANA_KEY","birth_date":"DB-M_STUDENT-BIRTH_DATE","gender_category":"DB-M_STUDENT-GENDER_CATEGORY","gender_code":"DB-M_STUDENT-GENDER_CODE","postal_code":"DB-M_STUDENT-POSTAL_CODE","prefecture_category":"DB-M_STUDENT-PREFECTURE_CATEGORY","prefecture_code":"DB-M_STUDENT-PREFECTURE_CODE","address_line1":"DB-M_STUDENT-ADDRESS_LINE1","address_line2":"DB-M_STUDENT-ADDRESS_LINE2","phone_number":"DB-M_STUDENT-PHONE_NUMBER","email_address":"DB-M_STUDENT-EMAIL_ADDRESS","admission_date":"DB-M_STUDENT-ADMISSION_DATE","enrollment_category":"DB-M_STUDENT-ENROLLMENT_CATEGORY","enrollment_status_code":"DB-M_STUDENT-ENROLLMENT_STATUS_CODE","enrollment_end_date":"DB-M_STUDENT-ENROLLMENT_END_DATE","class_id":"DB-M_STUDENT-CLASS_ID","emergency_contact_name":"DB-M_STUDENT-EMERGENCY_CONTACT_NAME","relationship_category":"DB-M_STUDENT-RELATIONSHIP_CATEGORY","relationship_code":"DB-M_STUDENT-RELATIONSHIP_CODE","emergency_phone_number":"DB-M_STUDENT-EMERGENCY_PHONE_NUMBER","remarks":"DB-M_STUDENT-REMARKS","is_deleted":"DB-M_STUDENT-IS_DELETED","deleted_at":"DB-M_STUDENT-DELETED_AT","deleted_by":"DB-M_STUDENT-DELETED_BY","delete_reason":"DB-M_STUDENT-DELETE_REASON","created_at":"DB-M_STUDENT-CREATED_AT","created_by":"DB-M_STUDENT-CREATED_BY","updated_at":"DB-M_STUDENT-UPDATED_AT","updated_by":"DB-M_STUDENT-UPDATED_BY","row_version":"DB-M_STUDENT-ROW_VERSION"}},"sheets":[{"sheet":"m_student","kind":"TABLE","sections":[{"heading":"テーブルヘッダー","kind":"HEADER"},{"heading":"項目詳細","kind":"LIST","key":["No"],"columns":["No","論理名","物理名","PK","NOT NULL","タイプ","長さ","初期値","説明"]}]}]} -->
# 学生基本情報 DB定義書

## テーブルヘッダー

| 項目 | 内容 |
| --- | --- |
| 文書ID／版 | DBDEF-ACCESS-M_STUDENT／7.2／2026-10-12 |
| 論理テーブル名 | 学生基本情報 |
| 物理テーブル名 | m_student |
| 対象／スキーマ | Access／非適用（ACE） |
| 用途／項目数 | 学生１人の基本情報・現在／最終所属を管理。 35項目。 |
| 主キー（順序） | student_id |
| 共通規則・制約 | [総合仕様・制約](../01_DB定義書.md)／[記述・Excel配置規約](../../../../../docs/テーブル仕様書記述規約.md) |
| 長さ／初期値の基準 | 長さは業務上限、タイプはDB型・容量。初期値はDB既定値。 |
| 項目IDの対応 | 物理列に対応する既存DB項目IDを維持。メタ情報fieldIdsに対応を記録。 |
| 基礎仕様 | [論理テーブル仕様](../../../基本設計書/03_テーブル仕様書.md)／[項目制約](../../../共通/09_項目制約定義.md) |
| 記号 | PK・NOT NULL：〇が該当、空欄は非該当。初期値なし・長さ対象外は空欄。条件付き必須は説明参照。 |

## 項目詳細

| No | 論理名 | 物理名 | PK | NOT NULL | タイプ | 長さ | 初期値 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 学生管理番号 | student_id | 〇 | 〇 | COUNTER | 10.0 | 自動採番 | 自動。学生を内部的に識別。不変、欠番可。 |
| 2 | 学籍番号 | student_no |  | 〇 | TEXT(30) | 15 |  | 学校が付番。全学生で一意、削除後も再利用不可、変更不可。 |
| 3 | 学生氏名 | student_name |  | 〇 | TEXT(16) | 8 |  | 原表記を保持。前後空白を除く。 |
| 4 | 学生氏名カナ | student_name_kana |  | 〇 | TEXT(36) | 18 |  | 全角カナへ整えた表記。 |
| 5 | 氏名照合用情報 | name_key |  | 〇 | LONGTEXT | 160 |  | 自動。氏名検索・候補比較用。氏名変更と同時に再作成。 |
| 6 | 氏名カナ照合用情報 | kana_key |  | 〇 | TEXT(36) | 18 |  | 自動。カナの空白差を除いて比較する情報。 |
| 7 | 生年月日 | birth_date |  | 〇 | TEXT(10) |  |  | 内部は日付、画面は和暦。DATE-R01の下限・業務日・入学日を検査。固定下限1900-01-01／保存時業務日以下。 |
| 8 | 性別のコード分類 | gender_category |  | 〇 | TEXT(48) | 24 |  | 自動固定。性別の値を他分類と誤認しないための分類情報。固定値GENDER。 |
| 9 | 性別 | gender_code |  | 〇 | TEXT(2) | 1 |  | 必須・未回答。未回答を許容。新規入力初期値0を保存入口が設定。FK:(gender_category,gender_code)→m_code(category_id,code_value)。 |
| 10 | 郵便番号 | postal_code |  | 〇 | TEXT(14) | 7 |  | 区切りなし。先頭ゼロを保持。 |
| 11 | 都道府県のコード分類 | prefecture_category |  | 〇 | TEXT(48) | 24 |  | 自動固定。都道府県の分類。固定値PREFECTURE。 |
| 12 | 都道府県 | prefecture_code |  | 〇 | TEXT(4) | 2 |  | 国内都道府県。FK:(prefecture_category,prefecture_code)→m_code(category_id,code_value)。 |
| 13 | 住所1 | address_line1 |  | 〇 | TEXT(90) | 45 |  | 市区町村・町域・番地。 |
| 14 | 住所2 | address_line2 |  |  | TEXT(90) | 45 |  | 建物名・部屋番号。 |
| 15 | 本人電話 | phone_number |  |  | TEXT(32) | 16 |  | 条件付き。国内または国番号付きの区切りなし表記。 |
| 16 | 本人メール | email_address |  |  | TEXT(120) | 60 |  | 条件付き。共通形式に従う。共有可。 |
| 17 | 入学日 | admission_date |  | 〇 | TEXT(10) |  |  | 生年月日以上、本日以前。固定下限1900-01-01／保存時業務日以下。 |
| 18 | 在籍区分のコード分類 | enrollment_category |  | 〇 | TEXT(48) | 24 |  | 自動固定。在籍区分の分類。固定値ENROLLMENT_STATUS。 |
| 19 | 在籍区分 | enrollment_status_code |  | 〇 | TEXT(4) | 2 |  | 必須・在学。在学・休学・卒業・退学。新規入力初期値01を保存入口が設定。FK:(enrollment_category,enrollment_status_code)→m_code(category_id,code_value)。 |
| 20 | 卒業・退学日 | enrollment_end_date |  |  | TEXT(10) |  |  | 条件付き。卒業・退学なら必須。在学・休学なら空。固定下限1900-01-01／保存時業務日以下。 |
| 21 | 現在・最終所属クラス | class_id |  |  | LONG | 10.0 |  | 条件付き。在学・休学は必須。学生1人につき最大1件。FK:m_class.class_id。 |
| 22 | 緊急連絡先氏名 | emergency_contact_name |  |  | TEXT(16) | 8 |  | 一式指定時必須。続柄・電話と組で入力。 |
| 23 | 続柄のコード分類 | relationship_category |  | 〇 | TEXT(48) | 24 |  | 自動固定。続柄の値が空でも分類情報を保持。固定値RELATIONSHIP。 |
| 24 | 緊急連絡先続柄 | relationship_code |  |  | TEXT(4) | 2 |  | 一式指定時必須。父・母・その他等。FK:(relationship_category,relationship_code)→m_code(category_id,code_value)。 |
| 25 | 緊急連絡先電話 | emergency_phone_number |  |  | TEXT(32) | 16 |  | 一式指定時必須。本人電話と同形式。 |
| 26 | 備考 | remarks |  |  | TEXT(240) | 120 |  | 改行可。成績の管理対象ではない。 |
| 27 | 削除の状態 | is_deleted |  | 〇 | YESNO |  | False | 自動・未削除。在籍区分と別に管理。 |
| 28 | 削除日時 | deleted_at |  |  | DATETIME |  |  | 削除時に自動。未削除では空。 |
| 29 | 削除者 | deleted_by |  |  | TEXT(128) | 64 |  | 削除時に自動。未削除では空。 |
| 30 | 削除理由 | delete_reason |  |  | TEXT(120) | 60 |  | 削除時必須。空白だけは不可。未削除では空。 |
| 31 | 作成日時 | created_at |  | 〇 | DATETIME |  |  | 自動。最初の保存日時。変更不可。 |
| 32 | 作成者 | created_by |  | 〇 | TEXT(128) | 64 |  | 自動。認証された登録者。変更不可。 |
| 33 | 更新日時 | updated_at |  | 〇 | DATETIME |  |  | 自動。実変更の保存時点。 |
| 34 | 更新者 | updated_by |  | 〇 | TEXT(128) | 64 |  | 自動。認証された変更者。 |
| 35 | 更新管理番号 | row_version |  | 〇 | LONG | 10.0 | 1 | 自動。新規1、実変更ごとに1加算、上限で停止。2147483647到達後の加算を拒否。 |
