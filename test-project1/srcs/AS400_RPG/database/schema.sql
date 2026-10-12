-- Generated from test-project1 physical definitions; no actual database execution.

CREATE SCHEMA STUDAPP;

SET CURRENT SCHEMA STUDAPP;

CREATE TABLE m_code_category FOR SYSTEM NAME MCAT (
  category_id VARCHAR(24) CCSID1208 NOT NULL,
  category_name VARGRAPHIC(24) CCSID1200 NOT NULL,
  code_length SMALLINT NOT NULL,
  allow_add SMALLINT NOT NULL,
  is_active SMALLINT NOT NULL DEFAULT 1,
  remarks VARGRAPHIC(240) CCSID1200,
  created_at TIMESTAMP(6) NOT NULL,
  created_by VARGRAPHIC(128) CCSID1200 NOT NULL,
  updated_at TIMESTAMP(6) NOT NULL,
  updated_by VARGRAPHIC(128) CCSID1200 NOT NULL,
  row_version BIGINT NOT NULL DEFAULT 1,
  CONSTRAINT pk_m_code_category PRIMARY KEY (category_id),
  CONSTRAINT ck_m_code_category_1 CHECK (row_version > 0),
  CONSTRAINT ck_m_code_category_2 CHECK (code_length BETWEEN 1 AND 10),
  CHECK (allow_add IN (0,1)),
  CHECK (is_active IN (0,1))
);

CREATE TABLE m_code FOR SYSTEM NAME M_CODE (
  category_id VARCHAR(24) CCSID1208 NOT NULL,
  code_value VARCHAR(10) CCSID1208 NOT NULL,
  code_name VARGRAPHIC(24) CCSID1200 NOT NULL,
  display_order INTEGER NOT NULL DEFAULT 0,
  is_active SMALLINT NOT NULL DEFAULT 1,
  valid_from DATE NOT NULL,
  valid_to DATE,
  is_protected SMALLINT NOT NULL,
  remarks VARGRAPHIC(240) CCSID1200,
  created_at TIMESTAMP(6) NOT NULL,
  created_by VARGRAPHIC(128) CCSID1200 NOT NULL,
  updated_at TIMESTAMP(6) NOT NULL,
  updated_by VARGRAPHIC(128) CCSID1200 NOT NULL,
  row_version BIGINT NOT NULL DEFAULT 1,
  CONSTRAINT pk_m_code PRIMARY KEY (category_id,code_value),
  CONSTRAINT ck_m_code_1 CHECK (row_version > 0),
  CONSTRAINT ck_m_code_2 CHECK (display_order >= 0),
  CONSTRAINT ck_m_code_3 CHECK (valid_to IS NULL OR valid_from <= valid_to),
  CHECK (is_active IN (0,1)),
  CHECK (is_protected IN (0,1))
);

CREATE TABLE m_class FOR SYSTEM NAME M_CLASS (
  class_id BIGINT GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1) NOT NULL,
  school_year SMALLINT NOT NULL,
  grade_category VARCHAR(24) CCSID1208 NOT NULL,
  grade_code VARCHAR(2) CCSID1208 NOT NULL,
  class_code VARCHAR(9) CCSID1208 NOT NULL,
  class_name VARGRAPHIC(36) CCSID1200 NOT NULL,
  valid_from DATE NOT NULL,
  valid_to DATE NOT NULL,
  capacity INTEGER,
  display_order INTEGER NOT NULL DEFAULT 0,
  is_active SMALLINT NOT NULL DEFAULT 1,
  remarks VARGRAPHIC(240) CCSID1200,
  created_at TIMESTAMP(6) NOT NULL,
  created_by VARGRAPHIC(128) CCSID1200 NOT NULL,
  updated_at TIMESTAMP(6) NOT NULL,
  updated_by VARGRAPHIC(128) CCSID1200 NOT NULL,
  row_version BIGINT NOT NULL DEFAULT 1,
  CONSTRAINT pk_m_class PRIMARY KEY (class_id),
  CONSTRAINT ck_m_class_1 CHECK (row_version > 0),
  CONSTRAINT ck_m_class_2 CHECK (school_year BETWEEN 1900 AND 9998),
  CONSTRAINT ck_m_class_3 CHECK (valid_from <= valid_to),
  CONSTRAINT ck_m_class_4 CHECK (valid_from >= DATE(DIGITS(DECIMAL(school_year,4,0)) || '-04-01')),
  CONSTRAINT ck_m_class_5 CHECK (valid_to <= DATE(DIGITS(DECIMAL(school_year+1,4,0)) || '-03-31')),
  CONSTRAINT ck_m_class_6 CHECK (capacity IS NULL OR capacity BETWEEN 1 AND 9999),
  CONSTRAINT ck_m_class_7 CHECK (display_order >= 0),
  CONSTRAINT ck_m_class_8 CHECK (grade_category='GRADE'),
  CHECK (is_active IN (0,1))
);

CREATE TABLE m_student FOR SYSTEM NAME M_STUDENT (
  student_id BIGINT GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1) NOT NULL,
  student_no VARCHAR(15) CCSID1208 NOT NULL,
  student_name VARGRAPHIC(16) CCSID1200 NOT NULL,
  student_name_kana VARGRAPHIC(36) CCSID1200 NOT NULL,
  name_key VARGRAPHIC(320) CCSID1200 NOT NULL,
  kana_key VARGRAPHIC(36) CCSID1200 NOT NULL,
  birth_date DATE NOT NULL,
  gender_category VARCHAR(24) CCSID1208 NOT NULL,
  gender_code VARCHAR(1) CCSID1208 NOT NULL,
  postal_code VARCHAR(7) CCSID1208 NOT NULL,
  prefecture_category VARCHAR(24) CCSID1208 NOT NULL,
  prefecture_code VARCHAR(2) CCSID1208 NOT NULL,
  address_line1 VARGRAPHIC(90) CCSID1200 NOT NULL,
  address_line2 VARGRAPHIC(90) CCSID1200,
  phone_number VARCHAR(16) CCSID1208,
  email_address VARCHAR(60) CCSID1208,
  admission_date DATE NOT NULL,
  enrollment_category VARCHAR(24) CCSID1208 NOT NULL,
  enrollment_status_code VARCHAR(2) CCSID1208 NOT NULL,
  enrollment_end_date DATE,
  class_id BIGINT,
  emergency_contact_name VARGRAPHIC(16) CCSID1200,
  relationship_category VARCHAR(24) CCSID1208 NOT NULL,
  relationship_code VARCHAR(2) CCSID1208,
  emergency_phone_number VARCHAR(16) CCSID1208,
  remarks VARGRAPHIC(240) CCSID1200,
  is_deleted SMALLINT NOT NULL DEFAULT 0,
  deleted_at TIMESTAMP(6),
  deleted_by VARGRAPHIC(128) CCSID1200,
  delete_reason VARGRAPHIC(120) CCSID1200,
  created_at TIMESTAMP(6) NOT NULL,
  created_by VARGRAPHIC(128) CCSID1200 NOT NULL,
  updated_at TIMESTAMP(6) NOT NULL,
  updated_by VARGRAPHIC(128) CCSID1200 NOT NULL,
  row_version BIGINT NOT NULL DEFAULT 1,
  CONSTRAINT pk_m_student PRIMARY KEY (student_id),
  CONSTRAINT ck_m_student_1 CHECK (row_version > 0),
  CONSTRAINT ck_m_student_2 CHECK (birth_date >= DATE('1900-01-01')),
  CONSTRAINT ck_m_student_3 CHECK (birth_date <= admission_date),
  CONSTRAINT ck_m_student_4 CHECK ((enrollment_status_code IN ('01','02') AND class_id IS NOT NULL AND enrollment_end_date IS NULL) OR (enrollment_status_code IN ('03','04') AND enrollment_end_date IS NOT NULL AND enrollment_end_date >= admission_date)),
  CONSTRAINT ck_m_student_5 CHECK (phone_number IS NOT NULL OR email_address IS NOT NULL OR emergency_phone_number IS NOT NULL),
  CONSTRAINT ck_m_student_6 CHECK ((emergency_contact_name IS NULL AND relationship_code IS NULL AND emergency_phone_number IS NULL) OR (emergency_contact_name IS NOT NULL AND relationship_code IS NOT NULL AND emergency_phone_number IS NOT NULL)),
  CONSTRAINT ck_m_student_7 CHECK ((is_deleted=0 AND deleted_at IS NULL AND deleted_by IS NULL AND delete_reason IS NULL) OR (is_deleted=1 AND deleted_at IS NOT NULL AND deleted_by IS NOT NULL AND delete_reason IS NOT NULL)),
  CONSTRAINT ck_m_student_8 CHECK (gender_category='GENDER'),
  CONSTRAINT ck_m_student_9 CHECK (prefecture_category='PREFECTURE'),
  CONSTRAINT ck_m_student_10 CHECK (enrollment_category='ENROLLMENT_STATUS'),
  CONSTRAINT ck_m_student_11 CHECK (relationship_category='RELATIONSHIP'),
  CHECK (is_deleted IN (0,1))
);

CREATE TABLE t_operation_log FOR SYSTEM NAME T_OPLOG (
  log_id BIGINT GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1) NOT NULL,
  target_table VARCHAR(21) CCSID1208 NOT NULL,
  target_key VARCHAR(35) CCSID1208 NOT NULL,
  operation_type VARCHAR(11) CCSID1208 NOT NULL,
  before_version BIGINT,
  after_version BIGINT NOT NULL,
  changed_columns CLOB(16K) CCSID1208 NOT NULL,
  executed_by VARGRAPHIC(128) CCSID1200 NOT NULL,
  executed_at TIMESTAMP(6) NOT NULL,
  correlation_id CHAR(36) NOT NULL,
  operation_reason VARGRAPHIC(120) CCSID1200,
  duplicate_confirmed SMALLINT NOT NULL DEFAULT 0,
  CONSTRAINT pk_t_operation_log PRIMARY KEY (log_id),
  CONSTRAINT ck_t_operation_log_1 CHECK (after_version > 0),
  CONSTRAINT ck_t_operation_log_2 CHECK (before_version IS NULL OR before_version > 0),
  CONSTRAINT ck_t_operation_log_3 CHECK (operation_type IN ('CREATE','UPDATE','DELETE','DISABLE','ENABLE')),
  CHECK (duplicate_confirmed IN (0,1))
);

CREATE TABLE t_write_guard FOR SYSTEM NAME STGUARD (
  guard_id SMALLINT NOT NULL,
  lock_bit SMALLINT NOT NULL,
  CONSTRAINT pk_t_write_guard PRIMARY KEY (guard_id),
  CONSTRAINT ck_t_write_guard_1 CHECK (guard_id=1),
  CONSTRAINT ck_t_write_guard_2 CHECK (lock_bit IN (0,1))
);

CREATE UNIQUE INDEX uq_student_no ON m_student(student_no);

CREATE UNIQUE INDEX uq_class_year_code ON m_class(school_year,class_code);

ALTER TABLE m_code ADD CONSTRAINT fk_code_category FOREIGN KEY (category_id) REFERENCES m_code_category(category_id);

ALTER TABLE m_class ADD CONSTRAINT fk_class_grade FOREIGN KEY (grade_category,grade_code) REFERENCES m_code(category_id,code_value);

ALTER TABLE m_student ADD CONSTRAINT fk_student_class FOREIGN KEY (class_id) REFERENCES m_class(class_id);

ALTER TABLE m_student ADD CONSTRAINT fk_student_gender FOREIGN KEY (gender_category,gender_code) REFERENCES m_code(category_id,code_value);

ALTER TABLE m_student ADD CONSTRAINT fk_student_prefecture FOREIGN KEY (prefecture_category,prefecture_code) REFERENCES m_code(category_id,code_value);

ALTER TABLE m_student ADD CONSTRAINT fk_student_enrollment FOREIGN KEY (enrollment_category,enrollment_status_code) REFERENCES m_code(category_id,code_value);

ALTER TABLE m_student ADD CONSTRAINT fk_student_relationship FOREIGN KEY (relationship_category,relationship_code) REFERENCES m_code(category_id,code_value);

CREATE INDEX ix_student_birth ON m_student(birth_date);

CREATE INDEX ix_student_class_status ON m_student(is_deleted,class_id,enrollment_status_code);

CREATE INDEX ix_student_admission ON m_student(admission_date);

CREATE INDEX ix_student_updated ON m_student(updated_at);

CREATE INDEX ix_student_phone ON m_student(phone_number);

CREATE INDEX ix_student_emergency_phone ON m_student(emergency_phone_number);

CREATE INDEX ix_operation_target ON t_operation_log(target_table,target_key,executed_at);

INSERT INTO t_write_guard(guard_id,lock_bit) VALUES(1,0);
