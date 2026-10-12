-- Generated exclusively from Access/spec. Apply DAO properties/relations through Build-Access.ps1.

CREATE TABLE m_code_category (
  category_id TEXT(48) NOT NULL,
  category_name TEXT(24) NOT NULL,
  code_length LONG NOT NULL,
  allow_add YESNO NOT NULL,
  is_active YESNO NOT NULL DEFAULT True,
  remarks TEXT(240),
  created_at DATETIME NOT NULL,
  created_by TEXT(128) NOT NULL,
  updated_at DATETIME NOT NULL,
  updated_by TEXT(128) NOT NULL,
  row_version LONG NOT NULL DEFAULT 1,
  CONSTRAINT pk_m_code_category PRIMARY KEY (category_id)
);

CREATE TABLE m_code (
  category_id TEXT(48) NOT NULL,
  code_value TEXT(20) NOT NULL,
  code_name TEXT(24) NOT NULL,
  display_order LONG NOT NULL DEFAULT 0,
  is_active YESNO NOT NULL DEFAULT True,
  valid_from TEXT(10) NOT NULL,
  valid_to TEXT(10),
  is_protected YESNO NOT NULL,
  remarks TEXT(240),
  created_at DATETIME NOT NULL,
  created_by TEXT(128) NOT NULL,
  updated_at DATETIME NOT NULL,
  updated_by TEXT(128) NOT NULL,
  row_version LONG NOT NULL DEFAULT 1,
  CONSTRAINT pk_m_code PRIMARY KEY (category_id,code_value)
);

CREATE TABLE m_class (
  class_id COUNTER NOT NULL,
  school_year LONG NOT NULL,
  grade_category TEXT(48) NOT NULL,
  grade_code TEXT(4) NOT NULL,
  class_code TEXT(18) NOT NULL,
  class_name TEXT(36) NOT NULL,
  valid_from TEXT(10) NOT NULL,
  valid_to TEXT(10) NOT NULL,
  capacity LONG,
  display_order LONG NOT NULL DEFAULT 0,
  is_active YESNO NOT NULL DEFAULT True,
  remarks TEXT(240),
  created_at DATETIME NOT NULL,
  created_by TEXT(128) NOT NULL,
  updated_at DATETIME NOT NULL,
  updated_by TEXT(128) NOT NULL,
  row_version LONG NOT NULL DEFAULT 1,
  CONSTRAINT pk_m_class PRIMARY KEY (class_id)
);

CREATE TABLE m_student (
  student_id COUNTER NOT NULL,
  student_no TEXT(30) NOT NULL,
  student_name TEXT(16) NOT NULL,
  student_name_kana TEXT(36) NOT NULL,
  name_key LONGTEXT NOT NULL,
  kana_key TEXT(36) NOT NULL,
  birth_date TEXT(10) NOT NULL,
  gender_category TEXT(48) NOT NULL,
  gender_code TEXT(2) NOT NULL,
  postal_code TEXT(14) NOT NULL,
  prefecture_category TEXT(48) NOT NULL,
  prefecture_code TEXT(4) NOT NULL,
  address_line1 TEXT(90) NOT NULL,
  address_line2 TEXT(90),
  phone_number TEXT(32),
  email_address TEXT(120),
  admission_date TEXT(10) NOT NULL,
  enrollment_category TEXT(48) NOT NULL,
  enrollment_status_code TEXT(4) NOT NULL,
  enrollment_end_date TEXT(10),
  class_id LONG,
  emergency_contact_name TEXT(16),
  relationship_category TEXT(48),
  relationship_code TEXT(4),
  emergency_phone_number TEXT(32),
  remarks TEXT(240),
  is_deleted YESNO NOT NULL DEFAULT False,
  deleted_at DATETIME,
  deleted_by TEXT(128),
  delete_reason TEXT(120),
  created_at DATETIME NOT NULL,
  created_by TEXT(128) NOT NULL,
  updated_at DATETIME NOT NULL,
  updated_by TEXT(128) NOT NULL,
  row_version LONG NOT NULL DEFAULT 1,
  CONSTRAINT pk_m_student PRIMARY KEY (student_id)
);

CREATE TABLE t_operation_log (
  log_id COUNTER NOT NULL,
  target_table TEXT(42) NOT NULL,
  target_key TEXT(70) NOT NULL,
  operation_type TEXT(22) NOT NULL,
  before_version LONG,
  after_version LONG NOT NULL,
  changed_columns LONGTEXT NOT NULL,
  executed_by TEXT(128) NOT NULL,
  executed_at DATETIME NOT NULL,
  correlation_id TEXT(36) NOT NULL,
  operation_reason TEXT(120),
  duplicate_confirmed YESNO NOT NULL DEFAULT False,
  CONSTRAINT pk_t_operation_log PRIMARY KEY (log_id)
);

CREATE TABLE t_write_guard (
  guard_id LONG NOT NULL,
  lock_bit YESNO NOT NULL,
  CONSTRAINT pk_t_write_guard PRIMARY KEY (guard_id)
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

INSERT INTO t_write_guard(guard_id,lock_bit) VALUES(1,False);
