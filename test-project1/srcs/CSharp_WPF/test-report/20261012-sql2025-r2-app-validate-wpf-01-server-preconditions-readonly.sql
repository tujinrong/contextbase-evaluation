SET NOCOUNT ON;
IF CONVERT(int,SERVERPROPERTY('ProductMajorVersion'))<>17 THROW 51120,'SQL Server 2025 (17.x) is required.',1;
IF CONVERT(nvarchar(128),SERVERPROPERTY('Edition')) NOT LIKE N'%Express%' THROW 51121,'The explicitly requested Express edition is required.',1;
IF CONVERT(nvarchar(128),SERVERPROPERTY('MachineName'))<>N'DELL_DISKTOP1' THROW 51122,'Only the local machine is permitted.',1;
IF CONVERT(varchar(20),CONNECTIONPROPERTY('auth_scheme')) NOT IN ('NTLM','KERBEROS') THROW 51123,'Windows integrated authentication is required.',1;
SELECT SERVERPROPERTY('ProductVersion') product_version,SERVERPROPERTY('Edition') edition,ORIGINAL_LOGIN() deployment_login;IF NOT EXISTS(SELECT 1 FROM sys.server_principals WHERE name=N'DELL_DISKTOP1\tujin' AND type='U') THROW 51127,'A pre-created individual Windows application login is required.',1;IF ORIGINAL_LOGIN()<>N'DELL_DISKTOP1\tujin' THROW 51128,'Run ValidateApp under the actual intended Windows token.',1;
IF COALESCE(IS_SRVROLEMEMBER('sysadmin'),1)<>0 THROW 51128,'The actual Windows session must not be sysadmin.',1;