-- The previous owner marker is immutable for the existing training DB; accept its renamed profile too.
SET NOCOUNT ON;
IF NOT EXISTS(SELECT 1 FROM sys.extended_properties WHERE class=0 AND name=N'AccessRebuilderOwner' AND CONVERT(nvarchar(128),value) IN(N'test-project1/Access-To-CSharp_ASPNET',N'test-project1/Access-CSharp_ASPNET')) THROW 51100,'Wrong training database owner.',1;
IF (SELECT COUNT(*) FROM sys.tables WHERE is_ms_shipped=0)<>7 THROW 51101,'Wrong table count.',1;
IF (SELECT COUNT(*) FROM sys.columns WHERE object_id IN(SELECT object_id FROM sys.tables WHERE is_ms_shipped=0))<>93 THROW 51102,'Wrong column count.',1;
IF (SELECT COUNT(*) FROM sys.foreign_keys WHERE is_disabled=0 AND is_not_trusted=0)<>7 THROW 51103,'Wrong relation count.',1;
IF NOT EXISTS(SELECT 1 FROM sys.columns WHERE object_id=OBJECT_ID(N'dbo.m_student') AND name=N'row_version' AND TYPE_NAME(user_type_id)=N'int') THROW 51104,'Integer version changed type.',1;
IF (SELECT postal_code FROM dbo.m_student WHERE student_id=1)<>N'0000000' THROW 51105,'Leading zeros lost.',1;
IF (SELECT COUNT(*) FROM dbo.m_code_category)<>5 OR (SELECT COUNT(*) FROM dbo.m_code)<>70 THROW 51106,'Approved masters do not match.',1;
SELECT N'PASS' AS status, (SELECT COUNT(*) FROM sys.tables WHERE is_ms_shipped=0) AS tables, (SELECT COUNT(*) FROM sys.foreign_keys) AS relations, (SELECT COUNT(*) FROM dbo.m_code) AS approved_codes;
