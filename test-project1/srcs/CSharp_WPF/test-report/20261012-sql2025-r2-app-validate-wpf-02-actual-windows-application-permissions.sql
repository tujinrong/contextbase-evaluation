IF COALESCE(IS_SRVROLEMEMBER('sysadmin'),1)<>0 THROW 51140,'Actual application session cannot be sysadmin.',1;SET NOCOUNT ON;
BEGIN TRY
 IF USER_NAME()<>N'DELL_DISKTOP1\tujin' THROW 51140,'Unexpected application database identity.',1;
 IF USER_NAME() IN ('dbo','guest') OR COALESCE(IS_MEMBER('db_owner'),1)<>0 THROW 51140,'Application user must not be owner or guest.',1;
 IF COALESCE(IS_MEMBER('student_admin'),0)<>1 THROW 51141,'Expected application role membership is absent.',1;
 IF COALESCE(HAS_PERMS_BY_NAME('dbo.m_student','OBJECT','SELECT'),0)<>1 OR COALESCE(HAS_PERMS_BY_NAME('dbo.m_class','OBJECT','SELECT'),0)<>1 THROW 51142,'Read permissions are incomplete.',1;
 IF COALESCE(HAS_PERMS_BY_NAME('dbo.m_student','OBJECT','INSERT'),0)<>0 OR COALESCE(HAS_PERMS_BY_NAME('dbo.m_student','OBJECT','UPDATE'),0)<>0 OR COALESCE(HAS_PERMS_BY_NAME('dbo.m_student','OBJECT','DELETE'),0)<>0 THROW 51143,'Direct student DML must be denied.',1;
 IF COALESCE(HAS_PERMS_BY_NAME('student_api.process_save','OBJECT','EXECUTE'),0)<>0 THROW 51144,'Private process_save must be inaccessible.',1;
 IF COALESCE(HAS_PERMS_BY_NAME('student_api.prepare_save','OBJECT','EXECUTE'),0)<>1 OR COALESCE(HAS_PERMS_BY_NAME('student_api.persist_student','OBJECT','EXECUTE'),0)<>1 THROW 51145,'Save entry permissions are incorrect.',1;
 IF COALESCE(HAS_PERMS_BY_NAME('student_api.delete_student','OBJECT','EXECUTE'),0)<>1 OR COALESCE(HAS_PERMS_BY_NAME('student_api.save_class','OBJECT','EXECUTE'),0)<>1 OR COALESCE(HAS_PERMS_BY_NAME('student_api.save_code','OBJECT','EXECUTE'),0)<>1 THROW 51146,'Administrator entry permissions are incorrect.',1;
 SELECT USER_NAME() application_user,IS_MEMBER('student_admin') role_member;
END TRY
BEGIN CATCH
 THROW;
END CATCH;