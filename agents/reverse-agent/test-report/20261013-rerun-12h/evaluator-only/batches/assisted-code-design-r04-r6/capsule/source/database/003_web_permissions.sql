-- Trusted Web application database roles. Database-local rights only; no server login is created.
-- Viewer reads business data. Staff changes students and appends audit. Administrator adds master maintenance.
SET XACT_ABORT ON;
BEGIN TRANSACTION;
IF DB_NAME()<>'contextbase_test_project1_mvc' THROW 51205,N'Unexpected database for this project.',1;
IF DATABASE_PRINCIPAL_ID(N'student_viewer') IS NULL OR DATABASE_PRINCIPAL_ID(N'student_staff') IS NULL OR DATABASE_PRINCIPAL_ID(N'student_admin') IS NULL
 THROW 51214,N'Apply local 001_schema.sql before role grants.',1;
GRANT SELECT ON OBJECT::dbo.m_student TO student_viewer;
GRANT SELECT ON OBJECT::dbo.m_class TO student_viewer;
GRANT SELECT ON OBJECT::dbo.m_code_category TO student_viewer;
GRANT SELECT ON OBJECT::dbo.m_code TO student_viewer;
ALTER ROLE student_viewer ADD MEMBER student_staff;
ALTER ROLE student_staff ADD MEMBER student_admin;
GRANT INSERT,UPDATE ON OBJECT::dbo.m_student TO student_staff;
GRANT INSERT ON OBJECT::dbo.t_operation_log TO student_staff;
DENY DELETE ON OBJECT::dbo.m_student TO student_staff;
DENY UPDATE,DELETE ON OBJECT::dbo.t_operation_log TO student_staff;
GRANT INSERT,UPDATE ON OBJECT::dbo.m_class TO student_admin;
GRANT INSERT,UPDATE ON OBJECT::dbo.m_code TO student_admin;
DENY DELETE ON OBJECT::dbo.m_class TO student_admin;
DENY DELETE ON OBJECT::dbo.m_code TO student_admin;
DENY INSERT,UPDATE,DELETE ON OBJECT::dbo.m_code_category TO student_admin;
-- Current .NET Web contexts/confirmation tokens are server memory state; no t_confirmation/t_runtime_state DML is required.
-- MasterMaintenanceService independently checks IS_ROLEMEMBER('student_admin') on each connection.
COMMIT;
GO
