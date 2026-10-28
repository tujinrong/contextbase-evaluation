<!-- spec-meta: {"schema":"spec-md/1.1","documentId":"ACCESS-BAS-STU-03-M_STUDENT","version":"8.1","path":"sample-project1/spec/Access/基本設計書/テーブル/01_m_student.md","layout":"TABLE","table":{"logicalName":"学生基本情報","physicalName":"m_student","profile":"論理","primaryKey":["student_id"],"fieldIds":{"student_id":"TBL-01-001","student_no":"TBL-01-002","student_name":"TBL-01-003","student_name_kana":"TBL-01-004","name_key":"TBL-01-005","kana_key":"TBL-01-006","birth_date":"TBL-01-007","gender_category":"TBL-01-008","gender_code":"TBL-01-009","postal_code":"TBL-01-010","prefecture_category":"TBL-01-011","prefecture_code":"TBL-01-012","address_line1":"TBL-01-013","address_line2":"TBL-01-014","phone_number":"TBL-01-015","email_address":"TBL-01-016","admission_date":"TBL-01-017","enrollment_category":"TBL-01-018","enrollment_status_code":"TBL-01-019","enrollment_end_date":"TBL-01-020","class_id":"TBL-01-021","emergency_contact_name":"TBL-01-022","relationship_category":"TBL-01-023","relationship_code":"TBL-01-024","emergency_phone_number":"TBL-01-025","remarks":"TBL-01-026","is_deleted":"TBL-01-027","deleted_at":"TBL-01-028","deleted_by":"TBL-01-029","delete_reason":"TBL-01-030","created_at":"TBL-01-031","created_by":"TBL-01-032","updated_at":"TBL-01-033","updated_by":"TBL-01-034","row_version":"TBL-01-035"}},"sheets":[{"sheet":"m_student","kind":"TABLE","sections":[{"heading":"テーブルヘッダー","kind":"HEADER"},{"heading":"項目詳細","kind":"LIST","key":["No"],"columns":["No","論理名","物理名","PK","NOT NULL","タイプ","長さ","初期値","説明"]}]}],"isolationProfile":"Access"} -->
# 学生基本情報 テーブル仕様書

## テーブルヘッダー

| 項目 | 内容 |
| --- | --- |
| 文書ID／版 | BAS-STU-03-M_STUDENT／8.1／2026-10-25 |
| 論理テーブル名 | 学生基本情報 |
| 物理テーブル名 | m_student |
| 対象／スキーマ | 論理／言語・DB製品非依存 |
| 用途／項目数 | 学生１人の基本情報・現在／最終所属を管理。 35項目。 |
| 主キー（順序） | student_id |
| 共通規則・制約 | [総合仕様・制約](../03_テーブル仕様書.md)／[記述・Excel配置規約](../../規約/全体/テーブル仕様書記述規約.md) |
| 長さ／初期値の基準 | 長さは業務上限。数字は整数桁.小数桁。初期値は業務設定。 |
| 項目IDの対応 | TBL-01-{Noを3桁}。メタ情報fieldIdsに対応を記録。 |
| 物理名の位置付け | 対応付けの参照名。実装言語・DB製品の指定ではない。 |
| 記号 | PK・NOT NULL：〇が該当、空欄は非該当。初期値なし・長さ対象外は空欄。条件付き必須は説明参照。 |

## 項目詳細

| No | 論理名 | 物理名 | PK | NOT NULL | タイプ | 長さ | 初期値 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 学生管理番号 | student_id | 〇 | 〇 | 数字 |  | 自動採番 | 自動。学生を内部的に識別。不変、欠番可。桁上限は採用DB定義を参照。 |
| 2 | 学籍番号 | student_no |  | 〇 | 文字 | 15 |  | 学校が付番。全学生で一意、削除後も再利用不可、変更不可。 |
| 3 | 学生氏名 | student_name |  | 〇 | 文字 | 8 |  | 原表記を保持。前後空白を除く。 |
| 4 | 学生氏名カナ | student_name_kana |  | 〇 | 文字 | 18 |  | 全角カナへ整えた表記。 |
| 5 | 氏名照合用情報 | name_key |  | 〇 | 文字 | 160 |  | 自動。氏名検索・候補比較用。氏名変更と同時に再作成。 |
| 6 | 氏名カナ照合用情報 | kana_key |  | 〇 | 文字 | 18 |  | 自動。カナの空白差を除いて比較する情報。 |
| 7 | 生年月日 | birth_date |  | 〇 | 日付 |  |  | 内部は日付、画面は和暦。DATE-R01の下限・業務日・入学日を検査。 |
| 8 | 性別のコード分類 | gender_category |  | 〇 | 文字 | 24 | GENDER | 自動固定。性別の値を他分類と誤認しないための分類情報。 |
| 9 | 性別 | gender_code |  | 〇 | 文字 | 1 | 0 | 未回答を許容。 |
| 10 | 郵便番号 | postal_code |  | 〇 | 文字 | 7 |  | 区切りなし。先頭ゼロを保持。 |
| 11 | 都道府県のコード分類 | prefecture_category |  | 〇 | 文字 | 24 | PREFECTURE | 自動固定。都道府県の分類。 |
| 12 | 都道府県 | prefecture_code |  | 〇 | 文字 | 2 |  | 国内都道府県。 |
| 13 | 住所1 | address_line1 |  | 〇 | 文字 | 45 |  | 市区町村・町域・番地。 |
| 14 | 住所2 | address_line2 |  |  | 文字 | 45 |  | 建物名・部屋番号。 |
| 15 | 本人電話 | phone_number |  |  | 文字 | 16 |  | 条件付き。国内または国番号付きの区切りなし表記。 |
| 16 | 本人メール | email_address |  |  | 文字 | 60 |  | 条件付き。共通形式に従う。共有可。 |
| 17 | 入学日 | admission_date |  | 〇 | 日付 |  |  | 生年月日以上、本日以前。 |
| 18 | 在籍区分のコード分類 | enrollment_category |  | 〇 | 文字 | 24 | ENROLLMENT_STATUS | 自動固定。在籍区分の分類。 |
| 19 | 在籍区分 | enrollment_status_code |  | 〇 | 文字 | 2 | 01 | 在学・休学・卒業・退学。 |
| 20 | 卒業・退学日 | enrollment_end_date |  |  | 日付 |  |  | 条件付き。卒業・退学なら必須。在学・休学なら空。 |
| 21 | 現在・最終所属クラス | class_id |  |  | 数字 |  |  | 条件付き。在学・休学は必須。学生1人につき最大1件。桁上限は採用DB定義を参照。 |
| 22 | 緊急連絡先氏名 | emergency_contact_name |  |  | 文字 | 8 |  | 一式指定時必須。続柄・電話と組で入力。 |
| 23 | 続柄のコード分類 | relationship_category |  |  | 文字 | 24 |  | 続柄未選択はNULL。選択時はRELATIONSHIPを処理設定し、続柄と同時更新。 |
| 24 | 緊急連絡先続柄 | relationship_code |  |  | 文字 | 2 |  | 一式指定時必須。父・母・その他等。未選択時は分類もNULL。一部だけのNULLは不可。 |
| 25 | 緊急連絡先電話 | emergency_phone_number |  |  | 文字 | 16 |  | 一式指定時必須。本人電話と同形式。 |
| 26 | 備考 | remarks |  |  | 文字 | 120 |  | 改行可。成績の管理対象ではない。 |
| 27 | 削除の状態 | is_deleted |  | 〇 | 真偽 |  | 未削除 | 自動。在籍区分と別に管理。 |
| 28 | 削除日時 | deleted_at |  |  | 日時 |  |  | 削除時に自動。未削除では空。 |
| 29 | 削除者 | deleted_by |  |  | 文字 | 64 |  | 削除時に自動。未削除では空。 |
| 30 | 削除理由 | delete_reason |  |  | 文字 | 60 |  | 削除時必須。空白だけは不可。未削除では空。 |
| 31 | 作成日時 | created_at |  | 〇 | 日時 |  |  | 自動。最初の保存日時。変更不可。 |
| 32 | 作成者 | created_by |  | 〇 | 文字 | 64 |  | 自動。認証された登録者。変更不可。 |
| 33 | 更新日時 | updated_at |  | 〇 | 日時 |  |  | 自動。実変更の保存時点。 |
| 34 | 更新者 | updated_by |  | 〇 | 文字 | 64 |  | 自動。認証された変更者。 |
| 35 | 更新管理番号 | row_version |  | 〇 | 数字 |  | 1 | 自動。新規1、実変更ごとに1加算、上限で停止。桁上限は採用DB定義を参照。 |
