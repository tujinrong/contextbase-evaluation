-- Apply only after 001/002 in this independent database, as its deployer.
-- No login/user creation, server setting, business sample, or procedure is included.
IF DB_NAME()<>N'contextbase_test_project1_cobol' THROW 51101,N'Wrong COBOL database.',1;
GRANT SELECT ON OBJECT::dbo.m_student TO student_viewer;
GRANT SELECT ON OBJECT::dbo.m_class TO student_viewer;
GRANT SELECT ON OBJECT::dbo.m_code TO student_viewer;
GRANT SELECT ON OBJECT::dbo.m_code_category TO student_viewer;
-- Search/editor state is written even by viewers; ciphertext/owner checks are in the C boundary.
GRANT SELECT,INSERT,UPDATE,DELETE ON OBJECT::dbo.t_runtime_state TO student_viewer;
ALTER ROLE student_viewer ADD MEMBER student_staff;
GRANT INSERT,UPDATE ON OBJECT::dbo.m_student TO student_staff;
GRANT INSERT ON OBJECT::dbo.t_operation_log TO student_staff;
ALTER ROLE student_staff ADD MEMBER student_admin;
GRANT INSERT,UPDATE ON OBJECT::dbo.m_class TO student_admin;
GRANT INSERT,UPDATE ON OBJECT::dbo.m_code TO student_admin;
GRANT VIEW DEFINITION ON ROLE::student_admin TO student_admin;
-- t_confirmation is not used by this COBOL implementation (t_runtime_state is used).
-- No physical-delete permission for business rows or update/delete permission for audit rows.
