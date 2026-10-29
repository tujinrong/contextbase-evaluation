-- Execute as DB owner in the explicitly selected new database, substituting a pre-created Windows DB user.
-- This script never creates server logins or grants server/admin roles. No startup execution.
IF NOT EXISTS(SELECT 1 FROM sys.database_principals WHERE name=N'SP2_Career_App') CREATE ROLE SP2_Career_App AUTHORIZATION dbo;
GRANT SELECT ON dbo.m_app_user TO SP2_Career_App;
GRANT UPDATE(failed_count,locked_until) ON dbo.m_app_user TO SP2_Career_App;
GRANT SELECT,INSERT,UPDATE ON dbo.m_employee TO SP2_Career_App;
GRANT SELECT,INSERT,UPDATE,DELETE ON dbo.t_career TO SP2_Career_App;
GRANT SELECT ON dbo.m_code_category TO SP2_Career_App;
GRANT SELECT,INSERT,UPDATE ON dbo.m_code TO SP2_Career_App;
DENY DELETE ON dbo.m_app_user TO SP2_Career_App;
DENY DELETE ON dbo.m_employee TO SP2_Career_App;
DENY DELETE ON dbo.m_code_category TO SP2_Career_App;
DENY DELETE ON dbo.m_code TO SP2_Career_App;
DENY ALTER,TAKE OWNERSHIP ON SCHEMA::dbo TO SP2_Career_App;
-- Owner completes: ALTER ROLE SP2_Career_App ADD MEMBER [the explicitly approved application Windows user];
-- Do not add db_owner/db_ddladmin/db_datawriter. App login must not be sysadmin.
