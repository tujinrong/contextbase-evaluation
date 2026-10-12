-- Read-only installation verification. Run with the deployment account; no data changes.
SET NOCOUNT ON;
IF DB_NAME()<>'contextbase_test_project1_vue' THROW 51205,N'Unexpected project database.',1;
IF ISNULL(CONVERT(int,SERVERPROPERTY('ProductMajorVersion')),0)<>17 OR ISNULL(CONVERT(nvarchar(128),SERVERPROPERTY('Edition')),N'') NOT LIKE N'%Express%'
 THROW 51200,N'Express major 17 is required for this requested deployment.',1;
IF (SELECT snapshot_isolation_state FROM sys.databases WHERE database_id=DB_ID())<>1 THROW 51215,N'SNAPSHOT isolation is not fully enabled.',1;
DECLARE @tables TABLE(name sysname,columns int);
INSERT @tables VALUES (N'm_student',35),
(N'm_class',17),
(N'm_code_category',11),
(N'm_code',14),
(N't_operation_log',12),
(N't_confirmation',9),
(N't_runtime_state',8);
IF (SELECT COUNT(*) FROM sys.tables WHERE is_ms_shipped=0)<>7
 OR EXISTS(SELECT 1 FROM @tables e LEFT JOIN sys.tables t ON t.name=e.name AND t.schema_id=SCHEMA_ID(N'dbo') WHERE t.object_id IS NULL OR (SELECT COUNT(*) FROM sys.columns c WHERE c.object_id=t.object_id)<>e.columns)
 THROW 51216,N'The seven local production tables or their physical column counts differ.',1;
IF EXISTS(SELECT 1 FROM sys.foreign_keys WHERE is_disabled=1 OR is_not_trusted=1)
 OR EXISTS(SELECT 1 FROM sys.check_constraints WHERE is_disabled=1 OR is_not_trusted=1)
 OR (SELECT COUNT(*) FROM sys.foreign_keys)<>7
 THROW 51217,N'Referential/check constraints are missing, disabled or untrusted.',1;
IF NOT EXISTS(SELECT 1 FROM sys.foreign_keys WHERE name=N'fk_student_relationship' AND parent_object_id=OBJECT_ID(N'dbo.m_student') AND referenced_object_id=OBJECT_ID(N'dbo.m_code') AND delete_referential_action=0 AND update_referential_action=0)
 OR (SELECT COUNT(*) FROM sys.columns WHERE object_id=OBJECT_ID(N'dbo.m_student') AND name IN(N'relationship_category',N'relationship_code') AND is_nullable=1)<>2
 OR NOT EXISTS(SELECT 1 FROM sys.check_constraints WHERE name=N'ck_student_contact' AND parent_object_id=OBJECT_ID(N'dbo.m_student'))
 THROW 51218,N'Nullable relationship columns / composite FK / all-or-none check differ.',1;
DECLARE @keys TABLE(category_id varchar(24),code_value varchar(10));
INSERT @keys VALUES ('GENDER','0'),
('GENDER','1'),
('GENDER','2'),
('GENDER','9'),
('ENROLLMENT_STATUS','01'),
('ENROLLMENT_STATUS','02'),
('ENROLLMENT_STATUS','03'),
('ENROLLMENT_STATUS','04'),
('PREFECTURE','01'),
('PREFECTURE','02'),
('PREFECTURE','03'),
('PREFECTURE','04'),
('PREFECTURE','05'),
('PREFECTURE','06'),
('PREFECTURE','07'),
('PREFECTURE','08'),
('PREFECTURE','09'),
('PREFECTURE','10'),
('PREFECTURE','11'),
('PREFECTURE','12'),
('PREFECTURE','13'),
('PREFECTURE','14'),
('PREFECTURE','15'),
('PREFECTURE','16'),
('PREFECTURE','17'),
('PREFECTURE','18'),
('PREFECTURE','19'),
('PREFECTURE','20'),
('PREFECTURE','21'),
('PREFECTURE','22'),
('PREFECTURE','23'),
('PREFECTURE','24'),
('PREFECTURE','25'),
('PREFECTURE','26'),
('PREFECTURE','27'),
('PREFECTURE','28'),
('PREFECTURE','29'),
('PREFECTURE','30'),
('PREFECTURE','31'),
('PREFECTURE','32'),
('PREFECTURE','33'),
('PREFECTURE','34'),
('PREFECTURE','35'),
('PREFECTURE','36'),
('PREFECTURE','37'),
('PREFECTURE','38'),
('PREFECTURE','39'),
('PREFECTURE','40'),
('PREFECTURE','41'),
('PREFECTURE','42'),
('PREFECTURE','43'),
('PREFECTURE','44'),
('PREFECTURE','45'),
('PREFECTURE','46'),
('PREFECTURE','47'),
('RELATIONSHIP','01'),
('RELATIONSHIP','02'),
('RELATIONSHIP','03'),
('RELATIONSHIP','04'),
('RELATIONSHIP','05'),
('RELATIONSHIP','06'),
('RELATIONSHIP','07'),
('RELATIONSHIP','99'),
('GRADE','00'),
('GRADE','01'),
('GRADE','02'),
('GRADE','03'),
('GRADE','04'),
('GRADE','05'),
('GRADE','06');
IF (SELECT COUNT(*) FROM dbo.m_code_category)<>5
 OR EXISTS(SELECT 1 FROM @keys e LEFT JOIN dbo.m_code c ON c.category_id=e.category_id AND c.code_value=e.code_value WHERE c.category_id IS NULL)
 THROW 51219,N'Five categories or an initial business-code key is missing.',1;
DECLARE @expected TABLE(role_name sysname,object_name sysname,permission_name nvarchar(128),state char(1));
INSERT @expected VALUES (N'student_viewer',N'm_student',N'SELECT','G'),
(N'student_viewer',N'm_class',N'SELECT','G'),
(N'student_viewer',N'm_code_category',N'SELECT','G'),
(N'student_viewer',N'm_code',N'SELECT','G'),
(N'student_staff',N'm_student',N'INSERT','G'),
(N'student_staff',N'm_student',N'UPDATE','G'),
(N'student_staff',N't_operation_log',N'INSERT','G'),
(N'student_staff',N'm_student',N'DELETE','D'),
(N'student_staff',N't_operation_log',N'UPDATE','D'),
(N'student_staff',N't_operation_log',N'DELETE','D'),
(N'student_admin',N'm_class',N'INSERT','G'),
(N'student_admin',N'm_class',N'UPDATE','G'),
(N'student_admin',N'm_code',N'INSERT','G'),
(N'student_admin',N'm_code',N'UPDATE','G'),
(N'student_admin',N'm_class',N'DELETE','D'),
(N'student_admin',N'm_code',N'DELETE','D'),
(N'student_admin',N'm_code_category',N'INSERT','D'),
(N'student_admin',N'm_code_category',N'UPDATE','D'),
(N'student_admin',N'm_code_category',N'DELETE','D');
IF EXISTS(SELECT role_name,object_name,permission_name,state FROM @expected
 EXCEPT SELECT r.name,OBJECT_NAME(p.major_id),p.permission_name,p.state FROM sys.database_permissions p JOIN sys.database_principals r ON r.principal_id=p.grantee_principal_id WHERE r.name IN(N'student_viewer',N'student_staff',N'student_admin') AND p.class=1 AND p.minor_id=0)
 OR EXISTS(SELECT r.name,OBJECT_NAME(p.major_id),p.permission_name,p.state FROM sys.database_permissions p JOIN sys.database_principals r ON r.principal_id=p.grantee_principal_id WHERE r.name IN(N'student_viewer',N'student_staff',N'student_admin')
 EXCEPT SELECT role_name,object_name,permission_name,state FROM @expected)
 THROW 51220,N'Database role grants/denies differ from this Web adapter permission plan.',1;
IF NOT EXISTS(SELECT 1 FROM sys.database_role_members WHERE role_principal_id=DATABASE_PRINCIPAL_ID(N'student_viewer') AND member_principal_id=DATABASE_PRINCIPAL_ID(N'student_staff'))
 OR NOT EXISTS(SELECT 1 FROM sys.database_role_members WHERE role_principal_id=DATABASE_PRINCIPAL_ID(N'student_staff') AND member_principal_id=DATABASE_PRINCIPAL_ID(N'student_admin'))
 THROW 51221,N'Database role inheritance differs.',1;
SELECT N'PASS deployment metadata / seed keys / database-local rights' AS Result,
 DB_NAME() AS DatabaseName,SERVERPROPERTY('ProductVersion') AS ProductVersion,
 SERVERPROPERTY('Edition') AS Edition,ORIGINAL_LOGIN() AS VerificationLogin,USER_NAME() AS VerificationDatabaseUser,
 (SELECT COUNT(*) FROM dbo.m_code_category) AS CodeCategories,(SELECT COUNT(*) FROM dbo.m_code) AS Codes,
 (SELECT COUNT(*) FROM dbo.m_class) AS Classes,(SELECT COUNT(*) FROM dbo.m_student) AS Students;
-- This verifies the declared role grants, not effective Windows group/server privileges.
-- Production principal effective permissions must be tested through its actual Windows login.
GO
