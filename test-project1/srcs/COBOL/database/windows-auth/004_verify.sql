-- Read-only verification; execute in contextbase_test_project1_cobol as deployer.
SELECT N'DATABASE' AS check_id,CONVERT(bit,CASE WHEN DB_NAME()=N'contextbase_test_project1_cobol' THEN 1 ELSE 0 END) AS passed,CONVERT(nvarchar(256),DB_NAME()) AS observed
UNION ALL SELECT N'ENGINE_17',CONVERT(bit,CASE WHEN CONVERT(int,SERVERPROPERTY('ProductMajorVersion'))=17 THEN 1 ELSE 0 END),CONVERT(nvarchar(256),SERVERPROPERTY('ProductVersion'))
UNION ALL SELECT N'EXPRESS',CONVERT(bit,CASE WHEN CONVERT(int,SERVERPROPERTY('EngineEdition'))=4 THEN 1 ELSE 0 END),CONVERT(nvarchar(256),SERVERPROPERTY('Edition'))
UNION ALL SELECT N'WINDOWS_ONLY',CONVERT(bit,CASE WHEN CONVERT(int,SERVERPROPERTY('IsIntegratedSecurityOnly'))=1 THEN 1 ELSE 0 END),CONVERT(nvarchar(256),SERVERPROPERTY('IsIntegratedSecurityOnly'))
UNION ALL SELECT N'SNAPSHOT_ENABLED',CONVERT(bit,CASE WHEN snapshot_isolation_state=1 THEN 1 ELSE 0 END),CONVERT(nvarchar(256),snapshot_isolation_state) FROM sys.databases WHERE database_id=DB_ID()
UNION ALL SELECT N'SEVEN_EXPECTED_TABLES',CONVERT(bit,CASE WHEN COUNT(*)=7 AND SUM(CASE WHEN name IN ('m_student','m_class','m_code_category','m_code','t_operation_log','t_confirmation','t_runtime_state') THEN 1 ELSE 0 END)=7 THEN 1 ELSE 0 END),CONVERT(nvarchar(256),COUNT(*)) FROM sys.tables WHERE is_ms_shipped=0
UNION ALL SELECT N'BUSINESS_COLUMNS_89',CONVERT(bit,CASE WHEN COUNT(*)=89 THEN 1 ELSE 0 END),CONVERT(nvarchar(256),COUNT(*)) FROM sys.columns WHERE object_id IN (OBJECT_ID('dbo.m_student'),OBJECT_ID('dbo.m_class'),OBJECT_ID('dbo.m_code_category'),OBJECT_ID('dbo.m_code'),OBJECT_ID('dbo.t_operation_log'))
UNION ALL SELECT N'SEVEN_TRUSTED_FK',CONVERT(bit,CASE WHEN COUNT(*)=7 AND SUM(CONVERT(int,is_disabled)+CONVERT(int,is_not_trusted))=0 THEN 1 ELSE 0 END),CONVERT(nvarchar(256),COUNT(*)) FROM sys.foreign_keys
UNION ALL SELECT N'TRUSTED_CHECKS',CONVERT(bit,CASE WHEN SUM(CONVERT(int,is_disabled)+CONVERT(int,is_not_trusted))=0 THEN 1 ELSE 0 END),CONVERT(nvarchar(256),COUNT(*)) FROM sys.check_constraints
UNION ALL SELECT N'CATEGORY_COUNT_5',CONVERT(bit,CASE WHEN COUNT(*)=5 THEN 1 ELSE 0 END),CONVERT(nvarchar(256),COUNT(*)) FROM dbo.m_code_category
UNION ALL SELECT N'CODE_COUNT_70',CONVERT(bit,CASE WHEN COUNT(*)=70 THEN 1 ELSE 0 END),CONVERT(nvarchar(256),COUNT(*)) FROM dbo.m_code
UNION ALL SELECT N'PROTECTED_CODE_COUNT_53',CONVERT(bit,CASE WHEN COUNT(*)=53 THEN 1 ELSE 0 END),CONVERT(nvarchar(256),COUNT(*)) FROM dbo.m_code WHERE is_protected=1
UNION ALL SELECT N'REQUIRED_ROLES',CONVERT(bit,CASE WHEN COUNT(*)=3 THEN 1 ELSE 0 END),CONVERT(nvarchar(256),COUNT(*)) FROM sys.database_principals WHERE type='R' AND name IN ('student_viewer','student_staff','student_admin')
UNION ALL SELECT N'NO_STORED_PROCEDURES_REQUIRED',CONVERT(bit,CASE WHEN COUNT(*)=0 THEN 1 ELSE 0 END),CONVERT(nvarchar(256),COUNT(*)) FROM sys.procedures WHERE is_ms_shipped=0;

-- Initial-only baseline; later application tests may create dedicated fixture data.
SELECT N'INITIAL_CLASS_ROWS' AS observation,COUNT_BIG(*) AS row_count FROM dbo.m_class
UNION ALL SELECT N'INITIAL_STUDENT_ROWS',COUNT_BIG(*) FROM dbo.m_student
UNION ALL SELECT N'INITIAL_AUDIT_ROWS',COUNT_BIG(*) FROM dbo.t_operation_log;
SELECT ORIGINAL_LOGIN() AS original_login,SUSER_SNAME() AS execution_login,USER_NAME() AS database_user,
       IS_ROLEMEMBER('student_admin') AS is_student_admin,CONNECTIONPROPERTY('auth_scheme') AS auth_scheme;
