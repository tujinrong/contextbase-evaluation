SET NOCOUNT ON;
IF CONVERT(int,SERVERPROPERTY('ProductMajorVersion'))<>17 THROW 51120,'SQL Server 2025 (17.x) is required.',1;
IF CONVERT(nvarchar(128),SERVERPROPERTY('Edition')) NOT LIKE N'%Express%' THROW 51121,'The explicitly requested Express edition is required.',1;
IF CONVERT(nvarchar(128),SERVERPROPERTY('MachineName'))<>N'DELL_DISKTOP1' THROW 51122,'Only the local machine is permitted.',1;
IF CONVERT(varchar(20),CONNECTIONPROPERTY('auth_scheme')) NOT IN ('NTLM','KERBEROS') THROW 51123,'Windows integrated authentication is required.',1;
SELECT SERVERPROPERTY('ProductVersion') product_version,SERVERPROPERTY('Edition') edition,ORIGINAL_LOGIN() deployment_login;IF CONVERT(int,(SELECT value_in_use FROM sys.configurations WHERE name='clr enabled'))<>1 THROW 51124,'DBA must explicitly enable CLR before deployment.',1;
IF CONVERT(int,(SELECT value_in_use FROM sys.configurations WHERE name='clr strict security'))<>1 THROW 51125,'CLR strict security must remain enabled.',1;
IF NOT EXISTS(SELECT 1 FROM sys.trusted_assemblies WHERE hash=0xA5889EAA82A078761A59AD48F79472437671FB8AFAECFA2706948AC9DD95915A727F0717500CF01BA0DB4CF5F4EC32C5B5609F4F5D49D739616AE1D73E6D5468) THROW 51126,'DBA must independently register this exact reviewed assembly hash.',1;