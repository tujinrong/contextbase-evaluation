<!-- spec-meta: {"schema":"spec-md/1.1","documentId":"ACCESS-BAS-STU-03-M_STUDENT","version":"0.1","path":"sample-project1/srcs/Access/build/spec-generation/design-generation-check/spec/Access/基本設計書/テーブル/01_m_student.md","layout":"TABLE","table":{"logicalName":"学生基本情報","physicalName":"m_student","profile":"論理","primaryKey":["student_id"],"fieldIds":{"student_id":"TBL-01-001","student_no":"TBL-01-002","student_name":"TBL-01-003","student_name_kana":"TBL-01-004","name_key":"TBL-01-005","kana_key":"TBL-01-006","birth_date":"TBL-01-007","gender_category":"TBL-01-008","gender_code":"TBL-01-009","postal_code":"TBL-01-010","prefecture_category":"TBL-01-011","prefecture_code":"TBL-01-012","address_line1":"TBL-01-013","address_line2":"TBL-01-014","phone_number":"TBL-01-015","email_address":"TBL-01-016","admission_date":"TBL-01-017","enrollment_category":"TBL-01-018","enrollment_status_code":"TBL-01-019","enrollment_end_date":"TBL-01-020","class_id":"TBL-01-021","emergency_contact_name":"TBL-01-022","relationship_category":"TBL-01-023","relationship_code":"TBL-01-024","emergency_phone_number":"TBL-01-025","remarks":"TBL-01-026","is_deleted":"TBL-01-027","deleted_at":"TBL-01-028","deleted_by":"TBL-01-029","delete_reason":"TBL-01-030","created_at":"TBL-01-031","created_by":"TBL-01-032","updated_at":"TBL-01-033","updated_by":"TBL-01-034","row_version":"TBL-01-035"}},"sheets":[{"sheet":"m_student","kind":"TABLE","sections":[{"heading":"テーブルヘッダー","kind":"HEADER"},{"heading":"項目詳細","kind":"LIST","key":["No"],"columns":["No","論理名","物理名","PK","NOT NULL","タイプ","長さ","初期値","説明"]}]}],"isolationProfile":"Access","generationStatus":"verification-draft","inputSpecRoot":"sample-project1/spec/Access/"} -->
# 学生基本情報 テーブル仕様書

## テーブルヘッダー

| 項目 | 内容 |
| --- | --- |
| 文書ID／版 | BAS-STU-03-M_STUDENT／0.1／2026-10-28 |
| 生成状態 | verification-draft。基本設計Agentの試験生成・未採用 |
| 入力文書版 | ACCESS-BAS-STU-03-M_STUDENT／8.1。35項目を継承 |
| 論理テーブル名 | 学生基本情報 |
| 物理テーブル名 | m_student |
| 対象／スキーマ | 論理／言語・DB製品非依存 |
| 用途／項目数 | 学生1人の基本属性、現在・最終所属、削除状態と管理情報を保持。35項目 |
| 主キー（順序） | student_id |
| 共通規則・制約 | [総合仕様・制約](../03_テーブル仕様書.md)／[記述規約](../../規約/全体/テーブル仕様書記述規約.md) |
| 長さ／初期値の基準 | 長さは業務上限。数字は整数桁.小数桁。初期値は業務設定 |
| 項目IDの対応 | TBL-01-{Noを3桁}。既存fieldIdsと項目順を維持 |
| 物理名の位置付け | 対応確認用。実DB型・容量・制約は[Access分冊](../../DB定義/Access/テーブル/01_m_student.md)を保持 |
| 記号 | PK・NOT NULLは〇／空欄。初期値なし・長さ対象外は空欄。条件付き必須は説明参照 |

## 項目詳細

| No | 論理名 | 物理名 | PK | NOT NULL | タイプ | 長さ | 初期値 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 学生管理番号 | student_id | 〇 | 〇 | 数字 |  | 自動採番 | 内部識別子を自動付番する。登録後不変、欠番可。桁上限は採用DB定義に従う。 |
| 2 | 学籍番号 | student_no |  | 〇 | 文字 | 15 |  | 学校が付番。全学生で一意、登録後不変。削除後も再利用しない。 |
| 3 | 学生氏名 | student_name |  | 〇 | 文字 | 8 |  | 前後空白を除いた原表記を保持する。 |
| 4 | 学生氏名カナ | student_name_kana |  | 〇 | 文字 | 18 |  | 全角カナへ正規化した表記を保持する。 |
| 5 | 氏名照合用情報 | name_key |  | 〇 | 文字 | 160 |  | 氏名検索・候補比較の自動生成値。氏名変更と同じ保存単位で再作成する。 |
| 6 | 氏名カナ照合用情報 | kana_key |  | 〇 | 文字 | 18 |  | カナの空白差を除いて比較する情報を自動生成する。 |
| 7 | 生年月日 | birth_date |  | 〇 | 日付 |  |  | 日付で保存し和暦表示する。DATE-R01の下限・業務日・入学日との整合を確認する。 |
| 8 | 性別のコード分類 | gender_category |  | 〇 | 文字 | 24 | GENDER | 性別の分類を固定設定し、他分類の同じ値との混同を防ぐ。 |
| 9 | 性別 | gender_code |  | 〇 | 文字 | 1 | 0 | 未回答も有効な選択値として許容する。 |
| 10 | 郵便番号 | postal_code |  | 〇 | 文字 | 7 |  | 区切りなしの文字列で保存し、先頭ゼロを維持する。 |
| 11 | 都道府県のコード分類 | prefecture_category |  | 〇 | 文字 | 24 | PREFECTURE | 都道府県の分類を自動で固定設定する。 |
| 12 | 都道府県 | prefecture_code |  | 〇 | 文字 | 2 |  | 国内都道府県のコード値を保持する。 |
| 13 | 住所1 | address_line1 |  | 〇 | 文字 | 45 |  | 市区町村・町域・番地を保持する。 |
| 14 | 住所2 | address_line2 |  |  | 文字 | 45 |  | 建物名・部屋番号等を保持する。 |
| 15 | 本人電話 | phone_number |  |  | 文字 | 16 |  | 連絡手段として条件付き必須。国内または国番号付きの区切りなし表記。 |
| 16 | 本人メール | email_address |  |  | 文字 | 60 |  | 共通形式に従う連絡手段。条件付き必須で、他学生との共有を許容する。 |
| 17 | 入学日 | admission_date |  | 〇 | 日付 |  |  | 生年月日以上、本日以前であることを確認する。 |
| 18 | 在籍区分のコード分類 | enrollment_category |  | 〇 | 文字 | 24 | ENROLLMENT_STATUS | 在籍区分の分類を自動で固定設定する。 |
| 19 | 在籍区分 | enrollment_status_code |  | 〇 | 文字 | 2 | 01 | 在学・休学・卒業・退学のいずれかを保存する。 |
| 20 | 卒業・退学日 | enrollment_end_date |  |  | 日付 |  |  | 卒業・退学では必須。在学・休学では空とする。 |
| 21 | 現在・最終所属クラス | class_id |  |  | 数字 |  |  | 在学・休学では必須。学生1人につき最大1件。桁上限は採用DB定義に従う。 |
| 22 | 緊急連絡先氏名 | emergency_contact_name |  |  | 文字 | 8 |  | 緊急連絡先の指定時、続柄・電話と一式で必須とする。 |
| 23 | 続柄のコード分類 | relationship_category |  |  | 文字 | 24 |  | 続柄未選択はNULL。選択時はRELATIONSHIPを処理設定し、続柄と同時保存する。 |
| 24 | 緊急連絡先続柄 | relationship_code |  |  | 文字 | 2 |  | 父・母等の値。一式指定時は必須。未選択時は分類もNULL。一方だけのNULLは不可。 |
| 25 | 緊急連絡先電話 | emergency_phone_number |  |  | 文字 | 16 |  | 緊急連絡先一式の指定時に必須。本人電話と同じ形式を用いる。 |
| 26 | 備考 | remarks |  |  | 文字 | 120 |  | 改行を含む補足を保持する。成績管理には用いない。 |
| 27 | 削除の状態 | is_deleted |  | 〇 | 真偽 |  | 未削除 | 在籍区分とは別に、論理削除の状態を自動設定する。 |
| 28 | 削除日時 | deleted_at |  |  | 日時 |  |  | 論理削除時に自動設定し、未削除では空とする。 |
| 29 | 削除者 | deleted_by |  |  | 文字 | 64 |  | 論理削除の実行者を自動設定し、未削除では空とする。 |
| 30 | 削除理由 | delete_reason |  |  | 文字 | 60 |  | 論理削除時は必須。空白だけを認めず、未削除では空とする。 |
| 31 | 作成日時 | created_at |  | 〇 | 日時 |  |  | 最初の保存時点を自動設定し、後から変更しない。 |
| 32 | 作成者 | created_by |  | 〇 | 文字 | 64 |  | 認証済み登録者を自動設定し、登録後は変更しない。 |
| 33 | 更新日時 | updated_at |  | 〇 | 日時 |  |  | 実変更を保存した時点を自動設定する。 |
| 34 | 更新者 | updated_by |  | 〇 | 文字 | 64 |  | 実変更を行った認証済み利用者を設定する。 |
| 35 | 更新管理番号 | row_version |  | 〇 | 数字 |  | 1 | 新規は1、実変更ごとに1加算し、上限到達時は停止する。桁上限は採用DB定義に従う。 |
