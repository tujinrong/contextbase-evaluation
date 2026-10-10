# PostgreSQL物理仕様書

版5.0／2026-10-10。VB.NET・C#3方式・COBOLで共用する物理DB定義の正本。PostgreSQL 18は選定案。

共通管理列A＝`created_at timestamptz NOT NULL, created_by varchar(64) NOT NULL, updated_at timestamptz NOT NULL, updated_by varchar(64) NOT NULL, row_version bigint NOT NULL DEFAULT 1`。以下の`?`はNULL可、その他はNOT NULL。`ID`＝bigint GENERATED ALWAYS AS IDENTITY、`Vn`＝varchar(n)、`D`＝date、`T`＝timestamptz、`B`＝boolean、`I`＝integer、`L`＝bigint。Vnは業務文字数の上限。列名をsnake_case→PascalCaseに機械的変換した名前をEntityの標準プロパティ名とし、語中数字は保持する（address_line1→AddressLine1）。

| テーブル | 論理項目順の物理列・型 |
| --- | --- |
| m_student（30＋A=35） | student_id ID; student_no V20; student_name V100; student_name_kana V100; name_key V2000; kana_key V100; birth_date D; gender_category V30; gender_code V1; postal_code V7; prefecture_category V30; prefecture_code V2; address_line1 V200; address_line2 V200?; phone_number V16?; email_address V254?; admission_date D; enrollment_category V30; enrollment_status_code V2; enrollment_end_date D?; class_id L?; emergency_contact_name V100?; relationship_category V30; relationship_code V2?; emergency_phone_number V16?; remarks V1000?; is_deleted B DEFAULT false; deleted_at T?; deleted_by V64?; delete_reason V200?; A |
| m_class（12＋A=17） | class_id ID; school_year smallint; grade_category V30; grade_code V2; class_code V10; class_name V50; valid_from D; valid_to D; capacity I?; display_order I DEFAULT 0; is_active B DEFAULT true; remarks V500?; A |
| m_code_category（6＋A=11） | category_id V30; category_name V50; code_length smallint; allow_add B; is_active B DEFAULT true; remarks V500?; A |
| m_code（9＋A=14） | category_id V30; code_value V10; code_name V100; display_order I DEFAULT 0; is_active B DEFAULT true; valid_from D; valid_to D?; is_protected B; remarks V500?; A |
| t_operation_log（12） | log_id ID; target_table V30; target_key V200; operation_type V10; before_version L?; after_version L; changed_columns jsonb; executed_by V64; executed_at T; correlation_id uuid; operation_reason V200?; duplicate_confirmed B DEFAULT false |

Aは列5つを末尾に実際に展開する。t_operation_logにはAを重ねて追加しない。target_tableは許可5表のうち履歴自体を除く4値、target_keyはIDまたは分類＋値。changed_columnsは物理列名のJSON配列で、個人情報値を含めない。OperationTypeはCREATE/UPDATE/DELETE/DISABLE/ENABLE。

### キー・制約・索引

| 名前 | 定義 |
| --- | --- |
| pk_student / uq_student_no | student_id主キー、student_no全行一意（削除済みも対象） |
| pk_operation_log | t_operation_log.log_id主キー。IDENTITYだけでは一意制約の代替にしない |
| pk_class / uq_class_year_code | class_id主キー、school_year＋class_code一意 |
| pk_code_category / pk_code | category_id主キー、コードは(category_id,code_value)複合主キー |
| fk_student_class | class_id→m_class.class_id、ON DELETE RESTRICT |
| fk_student_gender/prefecture/enrollment/relationship | 分類列＋値列→m_code、RESTRICT。続柄値NULL可 |
| fk_class_grade / fk_code_category | (grade_category,grade_code)→m_code、m_code.category_id→m_code_category |
| ck_*_category | 学生4分類はGENDER/PREFECTURE/ENROLLMENT_STATUS/RELATIONSHIP、クラスはGRADEに固定 |
| ck_student_dates | birth_date≦admission_date、01/02は終了日NULLかつclass_id非NULL、03/04は終了日非NULLかつ入学日以上 |
| ck_student_contact | 連絡先の1つ以上、緊急3項目全部NULLまたは全部非NULL |
| ck_student_deleted | 未削除なら削除3項目全NULL、削除なら3項目全非NULL |
| ck_class_limits | 年度1900～9998、開始≦終了かつ年度内、capacity NULLまたは1～9999、display_order≧0 |
| ck_code_limits | code_length 1～10、値は数字、期間順、display_order≧0。分類固定桁は保守サービス／DB更新入口で検査 |
| ix_student_birth | birth_date、非削除行。氏名キー2000をB-tree複合キーへ無条件に入れない |
| ix_student_class_status | (class_id,enrollment_status_code) WHERE NOT is_deleted |
| ix_student_admission / ix_student_updated | admission_date / updated_at、非削除行 |
| ix_student_phone / ix_student_emergency_phone | 本人／緊急電話、非削除行 |
| ix_operation_target | (target_table,target_key,executed_at) |

各版は正数、更新時+1。現在日による検査は変動するためCHECKに埋めず保存入口で実行。メール・電話形式、必須空白、照合キー生成はサービスで検証しDB入口にも必要な検査を置く。学籍番号・クラスコードを大文字ASCIIにして保存、識別用列はバイナリー相当の決定的照合。全5表の業務上の意味・最大長は基本03に対応する。

## 日付制約

生年月日・入学日・終了日の固定下限1900-01-01とコード日付範囲をCHECKおよび保存入口で検証する。現在の業務日による動的上限は保存入口で確認し、固定年2026やCURRENT_DATEを不変制約へ埋め込まない。学生の日付列はdateのままとし元号文字列列を追加しない。下限は顧客確認対象。

[日付範囲の正本](../../共通/07_日付・和暦仕様.md)。物理実装は未作成、制約は設計定義であり実DBに適用済みではない。

履歴はafter_versionが正、before_versionは新規時NULL、既存変更時は正。changed_columnsは許可物理列名の配列、対象キーと操作種別を入口で検査する。履歴自身の変更を再度履歴へ追記しない。
