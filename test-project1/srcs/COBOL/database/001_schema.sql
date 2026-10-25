-- Source: ../../spec/COBOL/DB定義/SQLServer/テーブル; versions 8.1.
-- Apply to an EMPTY selected evaluation database only. No migration/drop is performed.
SET XACT_ABORT ON;
GO
ALTER DATABASE CURRENT SET ALLOW_SNAPSHOT_ISOLATION ON;
GO
CREATE TABLE dbo.m_student (
  student_id bigint IDENTITY(1,1) NOT NULL,
  student_no varchar(15) COLLATE Latin1_General_100_BIN2 NOT NULL,
  student_name nvarchar(16) COLLATE Latin1_General_100_CS_AS_SC NOT NULL,
  student_name_kana nvarchar(36) COLLATE Latin1_General_100_CS_AS_SC NOT NULL,
  name_key nvarchar(320) COLLATE Latin1_General_100_BIN2 NOT NULL,
  kana_key nvarchar(36) COLLATE Latin1_General_100_BIN2 NOT NULL,
  birth_date date NOT NULL,
  gender_category varchar(24) COLLATE Latin1_General_100_BIN2 NOT NULL,
  gender_code varchar(1) COLLATE Latin1_General_100_BIN2 NOT NULL,
  postal_code varchar(7) COLLATE Latin1_General_100_BIN2 NOT NULL,
  prefecture_category varchar(24) COLLATE Latin1_General_100_BIN2 NOT NULL,
  prefecture_code varchar(2) COLLATE Latin1_General_100_BIN2 NOT NULL,
  address_line1 nvarchar(90) COLLATE Latin1_General_100_CS_AS_SC NOT NULL,
  address_line2 nvarchar(90) COLLATE Latin1_General_100_CS_AS_SC NULL,
  phone_number varchar(16) COLLATE Latin1_General_100_BIN2 NULL,
  email_address varchar(60) COLLATE Latin1_General_100_BIN2 NULL,
  admission_date date NOT NULL,
  enrollment_category varchar(24) COLLATE Latin1_General_100_BIN2 NOT NULL,
  enrollment_status_code varchar(2) COLLATE Latin1_General_100_BIN2 NOT NULL,
  enrollment_end_date date NULL,
  class_id bigint NULL,
  emergency_contact_name nvarchar(16) COLLATE Latin1_General_100_CS_AS_SC NULL,
  relationship_category varchar(24) COLLATE Latin1_General_100_BIN2 NULL,
  relationship_code varchar(2) COLLATE Latin1_General_100_BIN2 NULL,
  emergency_phone_number varchar(16) COLLATE Latin1_General_100_BIN2 NULL,
  remarks nvarchar(240) COLLATE Latin1_General_100_CS_AS_SC NULL,
  is_deleted bit NOT NULL CONSTRAINT df_m_student_is_deleted DEFAULT (0),
  deleted_at datetimeoffset(7) NULL,
  deleted_by nvarchar(128) COLLATE Latin1_General_100_CS_AS_SC NULL,
  delete_reason nvarchar(120) COLLATE Latin1_General_100_CS_AS_SC NULL,
  created_at datetimeoffset(7) NOT NULL,
  created_by nvarchar(128) COLLATE Latin1_General_100_CS_AS_SC NOT NULL,
  updated_at datetimeoffset(7) NOT NULL,
  updated_by nvarchar(128) COLLATE Latin1_General_100_CS_AS_SC NOT NULL,
  row_version bigint NOT NULL CONSTRAINT df_m_student_row_version DEFAULT (1),
  CONSTRAINT pk_m_student PRIMARY KEY (student_id),
  CONSTRAINT ck_m_student_student_name_scalar CHECK (student_name IS NULL OR LEN(CONVERT(nvarchar(max),student_name) COLLATE Latin1_General_100_CS_AS_SC+N'#')-1<=8),
  CONSTRAINT ck_m_student_student_name_kana_scalar CHECK (student_name_kana IS NULL OR LEN(CONVERT(nvarchar(max),student_name_kana) COLLATE Latin1_General_100_CS_AS_SC+N'#')-1<=18),
  CONSTRAINT ck_m_student_name_key_scalar CHECK (name_key IS NULL OR LEN(CONVERT(nvarchar(max),name_key) COLLATE Latin1_General_100_CS_AS_SC+N'#')-1<=160),
  CONSTRAINT ck_m_student_kana_key_scalar CHECK (kana_key IS NULL OR LEN(CONVERT(nvarchar(max),kana_key) COLLATE Latin1_General_100_CS_AS_SC+N'#')-1<=18),
  CONSTRAINT ck_m_student_address_line1_scalar CHECK (address_line1 IS NULL OR LEN(CONVERT(nvarchar(max),address_line1) COLLATE Latin1_General_100_CS_AS_SC+N'#')-1<=45),
  CONSTRAINT ck_m_student_address_line2_scalar CHECK (address_line2 IS NULL OR LEN(CONVERT(nvarchar(max),address_line2) COLLATE Latin1_General_100_CS_AS_SC+N'#')-1<=45),
  CONSTRAINT ck_m_student_emergency_contact_name_scalar CHECK (emergency_contact_name IS NULL OR LEN(CONVERT(nvarchar(max),emergency_contact_name) COLLATE Latin1_General_100_CS_AS_SC+N'#')-1<=8),
  CONSTRAINT ck_m_student_remarks_scalar CHECK (remarks IS NULL OR LEN(CONVERT(nvarchar(max),remarks) COLLATE Latin1_General_100_CS_AS_SC+N'#')-1<=120),
  CONSTRAINT ck_m_student_deleted_at_utc CHECK (deleted_at IS NULL OR DATEPART(TZOFFSET,deleted_at)=0),
  CONSTRAINT ck_m_student_deleted_by_scalar CHECK (deleted_by IS NULL OR LEN(CONVERT(nvarchar(max),deleted_by) COLLATE Latin1_General_100_CS_AS_SC+N'#')-1<=64),
  CONSTRAINT ck_m_student_delete_reason_scalar CHECK (delete_reason IS NULL OR LEN(CONVERT(nvarchar(max),delete_reason) COLLATE Latin1_General_100_CS_AS_SC+N'#')-1<=60),
  CONSTRAINT ck_m_student_created_at_utc CHECK (created_at IS NULL OR DATEPART(TZOFFSET,created_at)=0),
  CONSTRAINT ck_m_student_created_by_scalar CHECK (created_by IS NULL OR LEN(CONVERT(nvarchar(max),created_by) COLLATE Latin1_General_100_CS_AS_SC+N'#')-1<=64),
  CONSTRAINT ck_m_student_updated_at_utc CHECK (updated_at IS NULL OR DATEPART(TZOFFSET,updated_at)=0),
  CONSTRAINT ck_m_student_updated_by_scalar CHECK (updated_by IS NULL OR LEN(CONVERT(nvarchar(max),updated_by) COLLATE Latin1_General_100_CS_AS_SC+N'#')-1<=64),
  CONSTRAINT ck_m_student_row_version CHECK (row_version>0)
);
GO
CREATE TABLE dbo.m_class (
  class_id bigint IDENTITY(1,1) NOT NULL,
  school_year smallint NOT NULL,
  grade_category varchar(24) COLLATE Latin1_General_100_BIN2 NOT NULL,
  grade_code varchar(2) COLLATE Latin1_General_100_BIN2 NOT NULL,
  class_code varchar(9) COLLATE Latin1_General_100_BIN2 NOT NULL,
  class_name nvarchar(36) COLLATE Latin1_General_100_CS_AS_SC NOT NULL,
  valid_from date NOT NULL,
  valid_to date NOT NULL,
  capacity int NULL,
  display_order int NOT NULL CONSTRAINT df_m_class_display_order DEFAULT (0),
  is_active bit NOT NULL CONSTRAINT df_m_class_is_active DEFAULT (1),
  remarks nvarchar(240) COLLATE Latin1_General_100_CS_AS_SC NULL,
  created_at datetimeoffset(7) NOT NULL,
  created_by nvarchar(128) COLLATE Latin1_General_100_CS_AS_SC NOT NULL,
  updated_at datetimeoffset(7) NOT NULL,
  updated_by nvarchar(128) COLLATE Latin1_General_100_CS_AS_SC NOT NULL,
  row_version bigint NOT NULL CONSTRAINT df_m_class_row_version DEFAULT (1),
  CONSTRAINT pk_m_class PRIMARY KEY (class_id),
  CONSTRAINT ck_m_class_class_name_scalar CHECK (class_name IS NULL OR LEN(CONVERT(nvarchar(max),class_name) COLLATE Latin1_General_100_CS_AS_SC+N'#')-1<=18),
  CONSTRAINT ck_m_class_remarks_scalar CHECK (remarks IS NULL OR LEN(CONVERT(nvarchar(max),remarks) COLLATE Latin1_General_100_CS_AS_SC+N'#')-1<=120),
  CONSTRAINT ck_m_class_created_at_utc CHECK (created_at IS NULL OR DATEPART(TZOFFSET,created_at)=0),
  CONSTRAINT ck_m_class_created_by_scalar CHECK (created_by IS NULL OR LEN(CONVERT(nvarchar(max),created_by) COLLATE Latin1_General_100_CS_AS_SC+N'#')-1<=64),
  CONSTRAINT ck_m_class_updated_at_utc CHECK (updated_at IS NULL OR DATEPART(TZOFFSET,updated_at)=0),
  CONSTRAINT ck_m_class_updated_by_scalar CHECK (updated_by IS NULL OR LEN(CONVERT(nvarchar(max),updated_by) COLLATE Latin1_General_100_CS_AS_SC+N'#')-1<=64),
  CONSTRAINT ck_m_class_row_version CHECK (row_version>0)
);
GO
CREATE TABLE dbo.m_code_category (
  category_id varchar(24) COLLATE Latin1_General_100_BIN2 NOT NULL,
  category_name nvarchar(24) COLLATE Latin1_General_100_CS_AS_SC NOT NULL,
  code_length smallint NOT NULL,
  allow_add bit NOT NULL,
  is_active bit NOT NULL CONSTRAINT df_m_code_category_is_active DEFAULT (1),
  remarks nvarchar(240) COLLATE Latin1_General_100_CS_AS_SC NULL,
  created_at datetimeoffset(7) NOT NULL,
  created_by nvarchar(128) COLLATE Latin1_General_100_CS_AS_SC NOT NULL,
  updated_at datetimeoffset(7) NOT NULL,
  updated_by nvarchar(128) COLLATE Latin1_General_100_CS_AS_SC NOT NULL,
  row_version bigint NOT NULL CONSTRAINT df_m_code_category_row_version DEFAULT (1),
  CONSTRAINT pk_m_code_category PRIMARY KEY (category_id),
  CONSTRAINT ck_m_code_category_category_name_scalar CHECK (category_name IS NULL OR LEN(CONVERT(nvarchar(max),category_name) COLLATE Latin1_General_100_CS_AS_SC+N'#')-1<=12),
  CONSTRAINT ck_m_code_category_remarks_scalar CHECK (remarks IS NULL OR LEN(CONVERT(nvarchar(max),remarks) COLLATE Latin1_General_100_CS_AS_SC+N'#')-1<=120),
  CONSTRAINT ck_m_code_category_created_at_utc CHECK (created_at IS NULL OR DATEPART(TZOFFSET,created_at)=0),
  CONSTRAINT ck_m_code_category_created_by_scalar CHECK (created_by IS NULL OR LEN(CONVERT(nvarchar(max),created_by) COLLATE Latin1_General_100_CS_AS_SC+N'#')-1<=64),
  CONSTRAINT ck_m_code_category_updated_at_utc CHECK (updated_at IS NULL OR DATEPART(TZOFFSET,updated_at)=0),
  CONSTRAINT ck_m_code_category_updated_by_scalar CHECK (updated_by IS NULL OR LEN(CONVERT(nvarchar(max),updated_by) COLLATE Latin1_General_100_CS_AS_SC+N'#')-1<=64),
  CONSTRAINT ck_m_code_category_row_version CHECK (row_version>0)
);
GO
CREATE TABLE dbo.m_code (
  category_id varchar(24) COLLATE Latin1_General_100_BIN2 NOT NULL,
  code_value varchar(10) COLLATE Latin1_General_100_BIN2 NOT NULL,
  code_name nvarchar(24) COLLATE Latin1_General_100_CS_AS_SC NOT NULL,
  display_order int NOT NULL CONSTRAINT df_m_code_display_order DEFAULT (0),
  is_active bit NOT NULL CONSTRAINT df_m_code_is_active DEFAULT (1),
  valid_from date NOT NULL,
  valid_to date NULL,
  is_protected bit NOT NULL,
  remarks nvarchar(240) COLLATE Latin1_General_100_CS_AS_SC NULL,
  created_at datetimeoffset(7) NOT NULL,
  created_by nvarchar(128) COLLATE Latin1_General_100_CS_AS_SC NOT NULL,
  updated_at datetimeoffset(7) NOT NULL,
  updated_by nvarchar(128) COLLATE Latin1_General_100_CS_AS_SC NOT NULL,
  row_version bigint NOT NULL CONSTRAINT df_m_code_row_version DEFAULT (1),
  CONSTRAINT pk_m_code PRIMARY KEY (category_id,code_value),
  CONSTRAINT ck_m_code_code_name_scalar CHECK (code_name IS NULL OR LEN(CONVERT(nvarchar(max),code_name) COLLATE Latin1_General_100_CS_AS_SC+N'#')-1<=12),
  CONSTRAINT ck_m_code_remarks_scalar CHECK (remarks IS NULL OR LEN(CONVERT(nvarchar(max),remarks) COLLATE Latin1_General_100_CS_AS_SC+N'#')-1<=120),
  CONSTRAINT ck_m_code_created_at_utc CHECK (created_at IS NULL OR DATEPART(TZOFFSET,created_at)=0),
  CONSTRAINT ck_m_code_created_by_scalar CHECK (created_by IS NULL OR LEN(CONVERT(nvarchar(max),created_by) COLLATE Latin1_General_100_CS_AS_SC+N'#')-1<=64),
  CONSTRAINT ck_m_code_updated_at_utc CHECK (updated_at IS NULL OR DATEPART(TZOFFSET,updated_at)=0),
  CONSTRAINT ck_m_code_updated_by_scalar CHECK (updated_by IS NULL OR LEN(CONVERT(nvarchar(max),updated_by) COLLATE Latin1_General_100_CS_AS_SC+N'#')-1<=64),
  CONSTRAINT ck_m_code_row_version CHECK (row_version>0)
);
GO
CREATE TABLE dbo.t_operation_log (
  log_id bigint IDENTITY(1,1) NOT NULL,
  target_table varchar(21) COLLATE Latin1_General_100_BIN2 NOT NULL,
  target_key varchar(35) COLLATE Latin1_General_100_BIN2 NOT NULL,
  operation_type varchar(11) COLLATE Latin1_General_100_BIN2 NOT NULL,
  before_version bigint NULL,
  after_version bigint NOT NULL,
  changed_columns nvarchar(max) COLLATE Latin1_General_100_CS_AS_SC NOT NULL,
  executed_by nvarchar(128) COLLATE Latin1_General_100_CS_AS_SC NOT NULL,
  executed_at datetimeoffset(7) NOT NULL,
  correlation_id uniqueidentifier NOT NULL,
  operation_reason nvarchar(120) COLLATE Latin1_General_100_CS_AS_SC NULL,
  duplicate_confirmed bit NOT NULL CONSTRAINT df_t_operation_log_duplicate_confirmed DEFAULT (0),
  CONSTRAINT pk_t_operation_log PRIMARY KEY (log_id),
  CONSTRAINT ck_t_operation_log_executed_by_scalar CHECK (executed_by IS NULL OR LEN(CONVERT(nvarchar(max),executed_by) COLLATE Latin1_General_100_CS_AS_SC+N'#')-1<=64),
  CONSTRAINT ck_t_operation_log_executed_at_utc CHECK (executed_at IS NULL OR DATEPART(TZOFFSET,executed_at)=0),
  CONSTRAINT ck_t_operation_log_operation_reason_scalar CHECK (operation_reason IS NULL OR LEN(CONVERT(nvarchar(max),operation_reason) COLLATE Latin1_General_100_CS_AS_SC+N'#')-1<=60)
);
GO
CREATE TABLE dbo.t_confirmation (
  token uniqueidentifier NOT NULL,
  principal nvarchar(128) COLLATE Latin1_General_100_CS_AS_SC NOT NULL,
  session_id uniqueidentifier NOT NULL,
  target_id bigint NULL,
  expected_version bigint NULL,
  payload_hash binary(32) NOT NULL,
  candidate_hash binary(32) NOT NULL,
  expires_at datetimeoffset(7) NOT NULL,
  consumed bit NOT NULL,
  CONSTRAINT pk_t_confirmation PRIMARY KEY (token),
  CONSTRAINT ck_t_confirmation_principal_scalar CHECK (principal IS NULL OR LEN(CONVERT(nvarchar(max),principal) COLLATE Latin1_General_100_CS_AS_SC+N'#')-1<=64),
  CONSTRAINT ck_t_confirmation_expires_at_utc CHECK (expires_at IS NULL OR DATEPART(TZOFFSET,expires_at)=0)
);
GO
CREATE TABLE dbo.t_runtime_state (
  state_id varchar(64) COLLATE Latin1_General_100_BIN2 NOT NULL,
  owner_id nvarchar(128) COLLATE Latin1_General_100_CS_AS_SC NOT NULL,
  login_session_id varchar(64) COLLATE Latin1_General_100_BIN2 NOT NULL,
  state_kind varchar(16) COLLATE Latin1_General_100_BIN2 NOT NULL,
  encrypted_payload varbinary(max) NOT NULL,
  expires_at datetimeoffset(7) NOT NULL,
  revision bigint NOT NULL,
  consumed bit NOT NULL,
  CONSTRAINT pk_t_runtime_state PRIMARY KEY (state_id),
  CONSTRAINT ck_t_runtime_state_owner_id_scalar CHECK (owner_id IS NULL OR LEN(CONVERT(nvarchar(max),owner_id) COLLATE Latin1_General_100_CS_AS_SC+N'#')-1<=64),
  CONSTRAINT ck_t_runtime_state_expires_at_utc CHECK (expires_at IS NULL OR DATEPART(TZOFFSET,expires_at)=0),
  CONSTRAINT ck_t_runtime_state_revision CHECK (revision>0)
);
GO

ALTER TABLE dbo.m_student ADD CONSTRAINT uq_student_no UNIQUE(student_no);
ALTER TABLE dbo.m_class ADD CONSTRAINT uq_class_year_code UNIQUE(school_year,class_code);
ALTER TABLE dbo.m_code ADD CONSTRAINT fk_code_category FOREIGN KEY(category_id) REFERENCES dbo.m_code_category(category_id);
ALTER TABLE dbo.m_class ADD CONSTRAINT fk_class_grade FOREIGN KEY(grade_category,grade_code) REFERENCES dbo.m_code(category_id,code_value);
ALTER TABLE dbo.m_student ADD CONSTRAINT fk_student_class FOREIGN KEY(class_id) REFERENCES dbo.m_class(class_id);
ALTER TABLE dbo.m_student ADD CONSTRAINT fk_student_gender FOREIGN KEY(gender_category,gender_code) REFERENCES dbo.m_code(category_id,code_value);
ALTER TABLE dbo.m_student ADD CONSTRAINT fk_student_prefecture FOREIGN KEY(prefecture_category,prefecture_code) REFERENCES dbo.m_code(category_id,code_value);
ALTER TABLE dbo.m_student ADD CONSTRAINT fk_student_enrollment FOREIGN KEY(enrollment_category,enrollment_status_code) REFERENCES dbo.m_code(category_id,code_value);
ALTER TABLE dbo.m_student ADD CONSTRAINT fk_student_relationship FOREIGN KEY(relationship_category,relationship_code) REFERENCES dbo.m_code(category_id,code_value);
ALTER TABLE dbo.m_student ADD CONSTRAINT ck_student_category CHECK(gender_category='GENDER' AND prefecture_category='PREFECTURE' AND enrollment_category='ENROLLMENT_STATUS');
ALTER TABLE dbo.m_class ADD CONSTRAINT ck_class_category CHECK(grade_category='GRADE');
ALTER TABLE dbo.m_student ADD CONSTRAINT ck_student_dates CHECK(birth_date>='19000101' AND birth_date<=admission_date AND admission_date>='19000101' AND ((enrollment_status_code IN ('01','02') AND enrollment_end_date IS NULL AND class_id IS NOT NULL) OR (enrollment_status_code IN ('03','04') AND enrollment_end_date IS NOT NULL AND enrollment_end_date>=admission_date)));
ALTER TABLE dbo.m_student ADD CONSTRAINT ck_student_contact CHECK((phone_number IS NOT NULL OR email_address IS NOT NULL OR emergency_phone_number IS NOT NULL) AND ((emergency_contact_name IS NULL AND relationship_category IS NULL AND relationship_code IS NULL AND emergency_phone_number IS NULL) OR (emergency_contact_name IS NOT NULL AND relationship_category IS NOT NULL AND relationship_code IS NOT NULL AND emergency_phone_number IS NOT NULL AND relationship_category='RELATIONSHIP')));
ALTER TABLE dbo.m_student ADD CONSTRAINT ck_student_deleted CHECK((is_deleted=0 AND deleted_at IS NULL AND deleted_by IS NULL AND delete_reason IS NULL) OR (is_deleted=1 AND deleted_at IS NOT NULL AND deleted_by IS NOT NULL AND delete_reason IS NOT NULL));
ALTER TABLE dbo.m_class ADD CONSTRAINT ck_class_limits CHECK(school_year BETWEEN 1900 AND 9998 AND valid_from<=valid_to AND valid_from>=DATEFROMPARTS(school_year,4,1) AND valid_to<=DATEFROMPARTS(school_year+1,3,31) AND (capacity IS NULL OR capacity BETWEEN 1 AND 9999) AND display_order>=0);
ALTER TABLE dbo.m_code_category ADD CONSTRAINT ck_category_length CHECK(code_length BETWEEN 1 AND 10);
ALTER TABLE dbo.m_code ADD CONSTRAINT ck_code_limits CHECK(code_value<>'' AND code_value NOT LIKE '%[^0-9]%' COLLATE Latin1_General_100_BIN2 AND valid_from>='19000101' AND (valid_to IS NULL OR valid_to>=valid_from) AND display_order>=0);
ALTER TABLE dbo.t_operation_log ADD CONSTRAINT ck_audit_json CHECK(ISJSON(changed_columns)=1 AND LEFT(LTRIM(changed_columns),1)='[');
ALTER TABLE dbo.t_operation_log ADD CONSTRAINT ck_audit_operation CHECK(operation_type IN ('CREATE','UPDATE','DELETE','DISABLE','ENABLE'));
CREATE INDEX ix_student_birth ON dbo.m_student(birth_date) WHERE is_deleted=0;
CREATE INDEX ix_student_class_status ON dbo.m_student(class_id,enrollment_status_code) WHERE is_deleted=0;
CREATE INDEX ix_student_admission ON dbo.m_student(admission_date) WHERE is_deleted=0;
CREATE INDEX ix_student_updated ON dbo.m_student(updated_at) WHERE is_deleted=0;
CREATE INDEX ix_student_phone ON dbo.m_student(phone_number) WHERE is_deleted=0;
CREATE INDEX ix_student_emergency_phone ON dbo.m_student(emergency_phone_number) WHERE is_deleted=0;
CREATE INDEX ix_operation_target ON dbo.t_operation_log(target_table,target_key,executed_at);
CREATE ROLE student_viewer;
CREATE ROLE student_staff;
CREATE ROLE student_admin;
-- No login/user/password or rights escalation is performed automatically.
-- CGI uses a trusted application-service identity; operator reviews effective least privileges.
GO
