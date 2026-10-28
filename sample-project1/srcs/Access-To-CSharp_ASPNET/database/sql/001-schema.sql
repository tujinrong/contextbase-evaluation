-- Source ACCDB SHA-256: F5FF069C5D7AA45CFAE80584319FD11F0A0B8A6C52E141DA51D5263532D82CA4

-- Generated from DAO structure. Text uses explicit BIN2 comparison.

SET XACT_ABORT ON;

BEGIN TRANSACTION;

CREATE TABLE dbo.[m_class] (
  [class_id] int IDENTITY(1,1) NOT NULL,
  [school_year] int NOT NULL,
  [grade_category] nvarchar(48) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [grade_code] nvarchar(20) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [class_code] nvarchar(18) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [class_name] nvarchar(36) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [valid_from] nvarchar(10) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [valid_to] nvarchar(10) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [capacity] int NULL,
  [display_order] int NOT NULL DEFAULT (0),
  [is_active] bit NOT NULL DEFAULT (1),
  [remarks] nvarchar(240) COLLATE Latin1_General_100_BIN2 NULL,
  [created_at] datetime2(3) NOT NULL,
  [created_by] nvarchar(128) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [updated_at] datetime2(3) NOT NULL,
  [updated_by] nvarchar(128) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [row_version] int NOT NULL DEFAULT (1),
  CONSTRAINT [pk_m_class] PRIMARY KEY ([class_id])
);

ALTER TABLE dbo.[m_class] ADD CONSTRAINT [ck_m_class_1] CHECK ([grade_category] IS NULL OR DATALENGTH([grade_category])>0);

ALTER TABLE dbo.[m_class] ADD CONSTRAINT [ck_m_class_2] CHECK (DATALENGTH([grade_code])<=8);

ALTER TABLE dbo.[m_class] ADD CONSTRAINT [ck_m_class_3] CHECK ([grade_code] IS NULL OR DATALENGTH([grade_code])>0);

ALTER TABLE dbo.[m_class] ADD CONSTRAINT [ck_m_class_4] CHECK ([class_code] IS NULL OR DATALENGTH([class_code])>0);

ALTER TABLE dbo.[m_class] ADD CONSTRAINT [ck_m_class_5] CHECK ([class_name] IS NULL OR DATALENGTH([class_name])>0);

ALTER TABLE dbo.[m_class] ADD CONSTRAINT [ck_m_class_6] CHECK ([valid_from] IS NULL OR DATALENGTH([valid_from])>0);

ALTER TABLE dbo.[m_class] ADD CONSTRAINT [ck_m_class_7] CHECK ([valid_to] IS NULL OR DATALENGTH([valid_to])>0);

ALTER TABLE dbo.[m_class] ADD CONSTRAINT [ck_m_class_8] CHECK ([remarks] IS NULL OR DATALENGTH([remarks])>0);

ALTER TABLE dbo.[m_class] ADD CONSTRAINT [ck_m_class_9] CHECK ([created_by] IS NULL OR DATALENGTH([created_by])>0);

ALTER TABLE dbo.[m_class] ADD CONSTRAINT [ck_m_class_10] CHECK ([updated_by] IS NULL OR DATALENGTH([updated_by])>0);

ALTER TABLE dbo.[m_class] ADD CONSTRAINT [ck_m_class_11] CHECK ([row_version]>0);

ALTER TABLE dbo.[m_class] ADD CONSTRAINT [ck_m_class_record] CHECK ([school_year]>=1900 And [school_year]<=9998 And ([capacity] Is Null Or ([capacity]>=1 And [capacity]<=9999)) And [display_order]>=0 And [grade_category]=N'GRADE' And [valid_from]<=[valid_to] And [valid_from]>=CONVERT(nvarchar(20),[school_year]) + N'-04-01' And [valid_to]<=CONVERT(nvarchar(20),[school_year]+1) + N'-03-31');

CREATE INDEX [fk_class_grade] ON dbo.[m_class] ([grade_category], [grade_code]);

CREATE UNIQUE INDEX [uq_class_year_code] ON dbo.[m_class] ([school_year], [class_code]);

CREATE TABLE dbo.[m_code] (
  [category_id] nvarchar(48) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [code_value] nvarchar(20) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [code_name] nvarchar(24) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [display_order] int NOT NULL DEFAULT (0),
  [is_active] bit NOT NULL DEFAULT (1),
  [valid_from] nvarchar(10) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [valid_to] nvarchar(10) COLLATE Latin1_General_100_BIN2 NULL,
  [is_protected] bit NOT NULL,
  [remarks] nvarchar(240) COLLATE Latin1_General_100_BIN2 NULL,
  [created_at] datetime2(3) NOT NULL,
  [created_by] nvarchar(128) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [updated_at] datetime2(3) NOT NULL,
  [updated_by] nvarchar(128) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [row_version] int NOT NULL DEFAULT (1),
  CONSTRAINT [pk_m_code] PRIMARY KEY ([category_id], [code_value])
);

ALTER TABLE dbo.[m_code] ADD CONSTRAINT [ck_m_code_1] CHECK ([category_id] IS NULL OR DATALENGTH([category_id])>0);

ALTER TABLE dbo.[m_code] ADD CONSTRAINT [ck_m_code_2] CHECK ([code_value] IS NULL OR DATALENGTH([code_value])>0);

ALTER TABLE dbo.[m_code] ADD CONSTRAINT [ck_m_code_3] CHECK ([code_name] IS NULL OR DATALENGTH([code_name])>0);

ALTER TABLE dbo.[m_code] ADD CONSTRAINT [ck_m_code_4] CHECK ([valid_from] IS NULL OR DATALENGTH([valid_from])>0);

ALTER TABLE dbo.[m_code] ADD CONSTRAINT [ck_m_code_5] CHECK ([valid_to] IS NULL OR DATALENGTH([valid_to])>0);

ALTER TABLE dbo.[m_code] ADD CONSTRAINT [ck_m_code_6] CHECK ([remarks] IS NULL OR DATALENGTH([remarks])>0);

ALTER TABLE dbo.[m_code] ADD CONSTRAINT [ck_m_code_7] CHECK ([created_by] IS NULL OR DATALENGTH([created_by])>0);

ALTER TABLE dbo.[m_code] ADD CONSTRAINT [ck_m_code_8] CHECK ([updated_by] IS NULL OR DATALENGTH([updated_by])>0);

ALTER TABLE dbo.[m_code] ADD CONSTRAINT [ck_m_code_9] CHECK ([row_version]>0);

ALTER TABLE dbo.[m_code] ADD CONSTRAINT [ck_m_code_record] CHECK ([display_order]>=0 And ([valid_to] Is Null Or [valid_from]<=[valid_to]) And [code_value] Not Like N'%[^0-9]%');

CREATE INDEX [fk_code_category] ON dbo.[m_code] ([category_id]);

CREATE TABLE dbo.[m_code_category] (
  [category_id] nvarchar(48) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [category_name] nvarchar(24) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [code_length] int NOT NULL,
  [allow_add] bit NOT NULL,
  [is_active] bit NOT NULL DEFAULT (1),
  [remarks] nvarchar(240) COLLATE Latin1_General_100_BIN2 NULL,
  [created_at] datetime2(3) NOT NULL,
  [created_by] nvarchar(128) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [updated_at] datetime2(3) NOT NULL,
  [updated_by] nvarchar(128) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [row_version] int NOT NULL DEFAULT (1),
  CONSTRAINT [pk_m_code_category] PRIMARY KEY ([category_id])
);

ALTER TABLE dbo.[m_code_category] ADD CONSTRAINT [ck_m_code_category_1] CHECK ([category_id] IS NULL OR DATALENGTH([category_id])>0);

ALTER TABLE dbo.[m_code_category] ADD CONSTRAINT [ck_m_code_category_2] CHECK ([category_name] IS NULL OR DATALENGTH([category_name])>0);

ALTER TABLE dbo.[m_code_category] ADD CONSTRAINT [ck_m_code_category_3] CHECK ([remarks] IS NULL OR DATALENGTH([remarks])>0);

ALTER TABLE dbo.[m_code_category] ADD CONSTRAINT [ck_m_code_category_4] CHECK ([created_by] IS NULL OR DATALENGTH([created_by])>0);

ALTER TABLE dbo.[m_code_category] ADD CONSTRAINT [ck_m_code_category_5] CHECK ([updated_by] IS NULL OR DATALENGTH([updated_by])>0);

ALTER TABLE dbo.[m_code_category] ADD CONSTRAINT [ck_m_code_category_6] CHECK ([row_version]>0);

ALTER TABLE dbo.[m_code_category] ADD CONSTRAINT [ck_m_code_category_record] CHECK ([code_length]>=1 And [code_length]<=10);

CREATE TABLE dbo.[m_student] (
  [student_id] int IDENTITY(1,1) NOT NULL,
  [student_no] nvarchar(30) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [student_name] nvarchar(16) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [student_name_kana] nvarchar(36) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [name_key] nvarchar(max) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [kana_key] nvarchar(36) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [birth_date] nvarchar(10) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [gender_category] nvarchar(48) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [gender_code] nvarchar(20) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [postal_code] nvarchar(14) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [prefecture_category] nvarchar(48) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [prefecture_code] nvarchar(20) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [address_line1] nvarchar(90) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [address_line2] nvarchar(90) COLLATE Latin1_General_100_BIN2 NULL,
  [phone_number] nvarchar(32) COLLATE Latin1_General_100_BIN2 NULL,
  [email_address] nvarchar(120) COLLATE Latin1_General_100_BIN2 NULL,
  [admission_date] nvarchar(10) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [enrollment_category] nvarchar(48) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [enrollment_status_code] nvarchar(20) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [enrollment_end_date] nvarchar(10) COLLATE Latin1_General_100_BIN2 NULL,
  [class_id] int NULL,
  [emergency_contact_name] nvarchar(16) COLLATE Latin1_General_100_BIN2 NULL,
  [relationship_category] nvarchar(48) COLLATE Latin1_General_100_BIN2 NULL,
  [relationship_code] nvarchar(20) COLLATE Latin1_General_100_BIN2 NULL,
  [emergency_phone_number] nvarchar(32) COLLATE Latin1_General_100_BIN2 NULL,
  [remarks] nvarchar(240) COLLATE Latin1_General_100_BIN2 NULL,
  [is_deleted] bit NOT NULL DEFAULT (0),
  [deleted_at] datetime2(3) NULL,
  [deleted_by] nvarchar(128) COLLATE Latin1_General_100_BIN2 NULL,
  [delete_reason] nvarchar(120) COLLATE Latin1_General_100_BIN2 NULL,
  [created_at] datetime2(3) NOT NULL,
  [created_by] nvarchar(128) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [updated_at] datetime2(3) NOT NULL,
  [updated_by] nvarchar(128) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [row_version] int NOT NULL DEFAULT (1),
  CONSTRAINT [pk_m_student] PRIMARY KEY ([student_id])
);

ALTER TABLE dbo.[m_student] ADD CONSTRAINT [ck_m_student_1] CHECK ([student_no] IS NULL OR DATALENGTH([student_no])>0);

ALTER TABLE dbo.[m_student] ADD CONSTRAINT [ck_m_student_2] CHECK ([student_name] IS NULL OR DATALENGTH([student_name])>0);

ALTER TABLE dbo.[m_student] ADD CONSTRAINT [ck_m_student_3] CHECK ([student_name_kana] IS NULL OR DATALENGTH([student_name_kana])>0);

ALTER TABLE dbo.[m_student] ADD CONSTRAINT [ck_m_student_4] CHECK ([name_key] IS NULL OR DATALENGTH([name_key])>0);

ALTER TABLE dbo.[m_student] ADD CONSTRAINT [ck_m_student_5] CHECK ([kana_key] IS NULL OR DATALENGTH([kana_key])>0);

ALTER TABLE dbo.[m_student] ADD CONSTRAINT [ck_m_student_6] CHECK ([birth_date] IS NULL OR DATALENGTH([birth_date])>0);

ALTER TABLE dbo.[m_student] ADD CONSTRAINT [ck_m_student_7] CHECK ([gender_category] IS NULL OR DATALENGTH([gender_category])>0);

ALTER TABLE dbo.[m_student] ADD CONSTRAINT [ck_m_student_8] CHECK (DATALENGTH([gender_code])<=4);

ALTER TABLE dbo.[m_student] ADD CONSTRAINT [ck_m_student_9] CHECK ([gender_code] IS NULL OR DATALENGTH([gender_code])>0);

ALTER TABLE dbo.[m_student] ADD CONSTRAINT [ck_m_student_10] CHECK ([postal_code] IS NULL OR DATALENGTH([postal_code])>0);

ALTER TABLE dbo.[m_student] ADD CONSTRAINT [ck_m_student_11] CHECK ([prefecture_category] IS NULL OR DATALENGTH([prefecture_category])>0);

ALTER TABLE dbo.[m_student] ADD CONSTRAINT [ck_m_student_12] CHECK (DATALENGTH([prefecture_code])<=8);

ALTER TABLE dbo.[m_student] ADD CONSTRAINT [ck_m_student_13] CHECK ([prefecture_code] IS NULL OR DATALENGTH([prefecture_code])>0);

ALTER TABLE dbo.[m_student] ADD CONSTRAINT [ck_m_student_14] CHECK ([address_line1] IS NULL OR DATALENGTH([address_line1])>0);

ALTER TABLE dbo.[m_student] ADD CONSTRAINT [ck_m_student_15] CHECK ([address_line2] IS NULL OR DATALENGTH([address_line2])>0);

ALTER TABLE dbo.[m_student] ADD CONSTRAINT [ck_m_student_16] CHECK ([phone_number] IS NULL OR DATALENGTH([phone_number])>0);

ALTER TABLE dbo.[m_student] ADD CONSTRAINT [ck_m_student_17] CHECK ([email_address] IS NULL OR DATALENGTH([email_address])>0);

ALTER TABLE dbo.[m_student] ADD CONSTRAINT [ck_m_student_18] CHECK ([admission_date] IS NULL OR DATALENGTH([admission_date])>0);

ALTER TABLE dbo.[m_student] ADD CONSTRAINT [ck_m_student_19] CHECK ([enrollment_category] IS NULL OR DATALENGTH([enrollment_category])>0);

ALTER TABLE dbo.[m_student] ADD CONSTRAINT [ck_m_student_20] CHECK (DATALENGTH([enrollment_status_code])<=8);

ALTER TABLE dbo.[m_student] ADD CONSTRAINT [ck_m_student_21] CHECK ([enrollment_status_code] IS NULL OR DATALENGTH([enrollment_status_code])>0);

ALTER TABLE dbo.[m_student] ADD CONSTRAINT [ck_m_student_22] CHECK ([enrollment_end_date] IS NULL OR DATALENGTH([enrollment_end_date])>0);

ALTER TABLE dbo.[m_student] ADD CONSTRAINT [ck_m_student_23] CHECK ([emergency_contact_name] IS NULL OR DATALENGTH([emergency_contact_name])>0);

ALTER TABLE dbo.[m_student] ADD CONSTRAINT [ck_m_student_24] CHECK ([relationship_category] IS NULL OR DATALENGTH([relationship_category])>0);

ALTER TABLE dbo.[m_student] ADD CONSTRAINT [ck_m_student_25] CHECK (DATALENGTH([relationship_code])<=8);

ALTER TABLE dbo.[m_student] ADD CONSTRAINT [ck_m_student_26] CHECK ([relationship_code] IS NULL OR DATALENGTH([relationship_code])>0);

ALTER TABLE dbo.[m_student] ADD CONSTRAINT [ck_m_student_27] CHECK ([emergency_phone_number] IS NULL OR DATALENGTH([emergency_phone_number])>0);

ALTER TABLE dbo.[m_student] ADD CONSTRAINT [ck_m_student_28] CHECK ([remarks] IS NULL OR DATALENGTH([remarks])>0);

ALTER TABLE dbo.[m_student] ADD CONSTRAINT [ck_m_student_29] CHECK ([deleted_by] IS NULL OR DATALENGTH([deleted_by])>0);

ALTER TABLE dbo.[m_student] ADD CONSTRAINT [ck_m_student_30] CHECK ([delete_reason] IS NULL OR DATALENGTH([delete_reason])>0);

ALTER TABLE dbo.[m_student] ADD CONSTRAINT [ck_m_student_31] CHECK ([created_by] IS NULL OR DATALENGTH([created_by])>0);

ALTER TABLE dbo.[m_student] ADD CONSTRAINT [ck_m_student_32] CHECK ([updated_by] IS NULL OR DATALENGTH([updated_by])>0);

ALTER TABLE dbo.[m_student] ADD CONSTRAINT [ck_m_student_33] CHECK ([row_version]>0);

ALTER TABLE dbo.[m_student] ADD CONSTRAINT [ck_m_student_record] CHECK ([gender_category]=N'GENDER' And [prefecture_category]=N'PREFECTURE' And [enrollment_category]=N'ENROLLMENT_STATUS' And [birth_date]>=N'1900-01-01' And [birth_date]<=[admission_date] And (([enrollment_status_code] In (N'01',N'02') And [class_id] Is Not Null And [enrollment_end_date] Is Null) Or ([enrollment_status_code] In (N'03',N'04') And [enrollment_end_date] Is Not Null And [admission_date]<=[enrollment_end_date])) And ([phone_number] Is Not Null Or [email_address] Is Not Null Or [emergency_phone_number] Is Not Null) And (([emergency_contact_name] Is Null And [relationship_category] Is Null And [relationship_code] Is Null And [emergency_phone_number] Is Null) Or ([emergency_contact_name] Is Not Null And [relationship_category] Is Not Null And [relationship_category]=N'RELATIONSHIP' And [relationship_code] Is Not Null And [emergency_phone_number] Is Not Null)) And (([is_deleted]=0 And [deleted_at] Is Null And [deleted_by] Is Null And [delete_reason] Is Null) Or ([is_deleted]=1 And [deleted_at] Is Not Null And [deleted_by] Is Not Null And [delete_reason] Is Not Null)));

CREATE INDEX [fk_student_class] ON dbo.[m_student] ([class_id]);

CREATE INDEX [fk_student_enrollment] ON dbo.[m_student] ([enrollment_category], [enrollment_status_code]);

CREATE INDEX [fk_student_gender] ON dbo.[m_student] ([gender_category], [gender_code]);

CREATE INDEX [fk_student_prefecture] ON dbo.[m_student] ([prefecture_category], [prefecture_code]);

CREATE INDEX [fk_student_relationship] ON dbo.[m_student] ([relationship_category], [relationship_code]);

CREATE INDEX [ix_student_admission] ON dbo.[m_student] ([admission_date]);

CREATE INDEX [ix_student_birth] ON dbo.[m_student] ([birth_date]);

CREATE INDEX [ix_student_class_status] ON dbo.[m_student] ([is_deleted], [class_id], [enrollment_status_code]);

CREATE INDEX [ix_student_emergency_phone] ON dbo.[m_student] ([emergency_phone_number]);

CREATE INDEX [ix_student_phone] ON dbo.[m_student] ([phone_number]);

CREATE INDEX [ix_student_updated] ON dbo.[m_student] ([updated_at]);

CREATE UNIQUE INDEX [uq_student_no] ON dbo.[m_student] ([student_no]);

CREATE TABLE dbo.[t_app_role] (
  [user_id] nvarchar(128) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [role_name] nvarchar(10) COLLATE Latin1_General_100_BIN2 NOT NULL,
  CONSTRAINT [pk_app_role] PRIMARY KEY ([user_id])
);

ALTER TABLE dbo.[t_app_role] ADD CONSTRAINT [ck_t_app_role_1] CHECK ([user_id] IS NULL OR DATALENGTH([user_id])>0);

ALTER TABLE dbo.[t_app_role] ADD CONSTRAINT [ck_t_app_role_2] CHECK ([role_name] IS NULL OR DATALENGTH([role_name])>0);

ALTER TABLE dbo.[t_app_role] ADD CONSTRAINT [ck_t_app_role_record] CHECK ([role_name] In (N'Reader',N'Staff',N'Admin'));

CREATE TABLE dbo.[t_operation_log] (
  [log_id] int IDENTITY(1,1) NOT NULL,
  [target_table] nvarchar(42) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [target_key] nvarchar(70) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [operation_type] nvarchar(22) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [before_version] int NULL,
  [after_version] int NOT NULL,
  [changed_columns] nvarchar(max) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [executed_by] nvarchar(128) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [executed_at] datetime2(3) NOT NULL,
  [correlation_id] nvarchar(36) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [operation_reason] nvarchar(120) COLLATE Latin1_General_100_BIN2 NULL,
  [duplicate_confirmed] bit NOT NULL DEFAULT (0),
  CONSTRAINT [pk_t_operation_log] PRIMARY KEY ([log_id])
);

ALTER TABLE dbo.[t_operation_log] ADD CONSTRAINT [ck_t_operation_log_1] CHECK ([target_table] IS NULL OR DATALENGTH([target_table])>0);

ALTER TABLE dbo.[t_operation_log] ADD CONSTRAINT [ck_t_operation_log_2] CHECK ([target_key] IS NULL OR DATALENGTH([target_key])>0);

ALTER TABLE dbo.[t_operation_log] ADD CONSTRAINT [ck_t_operation_log_3] CHECK ([operation_type] IS NULL OR DATALENGTH([operation_type])>0);

ALTER TABLE dbo.[t_operation_log] ADD CONSTRAINT [ck_t_operation_log_4] CHECK ([changed_columns] IS NULL OR DATALENGTH([changed_columns])>0);

ALTER TABLE dbo.[t_operation_log] ADD CONSTRAINT [ck_t_operation_log_5] CHECK ([executed_by] IS NULL OR DATALENGTH([executed_by])>0);

ALTER TABLE dbo.[t_operation_log] ADD CONSTRAINT [ck_t_operation_log_6] CHECK ([correlation_id] IS NULL OR DATALENGTH([correlation_id])>0);

ALTER TABLE dbo.[t_operation_log] ADD CONSTRAINT [ck_t_operation_log_7] CHECK ([operation_reason] IS NULL OR DATALENGTH([operation_reason])>0);

ALTER TABLE dbo.[t_operation_log] ADD CONSTRAINT [ck_t_operation_log_record] CHECK ([after_version]>0 And ([before_version] Is Null Or [before_version]>0) And [operation_type] In (N'CREATE',N'UPDATE',N'DELETE',N'DISABLE',N'ENABLE'));

CREATE INDEX [correlation_id] ON dbo.[t_operation_log] ([correlation_id]);

CREATE INDEX [ix_operation_target] ON dbo.[t_operation_log] ([target_table], [target_key], [executed_at]);

CREATE TABLE dbo.[t_write_guard] (
  [guard_id] int NOT NULL,
  [lock_bit] bit NOT NULL,
  CONSTRAINT [pk_t_write_guard] PRIMARY KEY ([guard_id])
);

ALTER TABLE dbo.[t_write_guard] ADD CONSTRAINT [ck_t_write_guard_record] CHECK ([guard_id]=1);

ALTER TABLE dbo.[m_class] ADD CONSTRAINT [fk_class_grade] FOREIGN KEY ([grade_category], [grade_code]) REFERENCES dbo.[m_code] ([category_id], [code_value]);

ALTER TABLE dbo.[m_code] ADD CONSTRAINT [fk_code_category] FOREIGN KEY ([category_id]) REFERENCES dbo.[m_code_category] ([category_id]);

ALTER TABLE dbo.[m_student] ADD CONSTRAINT [fk_student_class] FOREIGN KEY ([class_id]) REFERENCES dbo.[m_class] ([class_id]);

ALTER TABLE dbo.[m_student] ADD CONSTRAINT [fk_student_enrollment] FOREIGN KEY ([enrollment_category], [enrollment_status_code]) REFERENCES dbo.[m_code] ([category_id], [code_value]);

ALTER TABLE dbo.[m_student] ADD CONSTRAINT [fk_student_gender] FOREIGN KEY ([gender_category], [gender_code]) REFERENCES dbo.[m_code] ([category_id], [code_value]);

ALTER TABLE dbo.[m_student] ADD CONSTRAINT [fk_student_prefecture] FOREIGN KEY ([prefecture_category], [prefecture_code]) REFERENCES dbo.[m_code] ([category_id], [code_value]);

ALTER TABLE dbo.[m_student] ADD CONSTRAINT [fk_student_relationship] FOREIGN KEY ([relationship_category], [relationship_code]) REFERENCES dbo.[m_code] ([category_id], [code_value]);

COMMIT TRANSACTION;
