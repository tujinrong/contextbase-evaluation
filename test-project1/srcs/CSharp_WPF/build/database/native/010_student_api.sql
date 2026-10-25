-- WPF-only native entrance. Apply after this project's 001_schema.sql and CLR deployment.
-- Every operation requires caller-owned READ COMMITTED transaction; no internal COMMIT.
SET XACT_ABORT ON;
GO
IF SCHEMA_ID('student_api') IS NULL EXEC('CREATE SCHEMA student_api AUTHORIZATION dbo');
GO
CREATE OR ALTER PROCEDURE student_api.process_save
 @raw nvarchar(max),@target_id bigint=NULL,@expected_version bigint=NULL,
 @session_id uniqueidentifier,@confirmation_token uniqueidentifier=NULL,@request_id uniqueidentifier,@write bit=0
AS
BEGIN
 SET NOCOUNT ON; SET XACT_ABORT ON; SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
 DECLARE @outcome varchar(32)='ValidationFailed',@code varchar(16)=NULL,@field varchar(64)='',@token uniqueidentifier=NULL,@candidate_count int=0,
 @saved_id bigint=@target_id,@saved_version bigint=@expected_version,@warning varchar(16)=NULL,@max_length int=NULL;
 DECLARE @actor nvarchar(128)=ORIGINAL_LOGIN(),@now datetimeoffset(7)=TODATETIMEOFFSET(SYSUTCDATETIME(),'+00:00'),@day date;
 SET @day=CONVERT(date,DATEADD(hour,9,@now));
 DECLARE @candidates TABLE(student_id bigint PRIMARY KEY,row_version bigint NOT NULL);
 IF @@TRANCOUNT=0 OR XACT_STATE()<>1 BEGIN SET @code='E-COM-003';GOTO Emit;END;
 IF @actor IS NULL OR LEN(@actor COLLATE Latin1_General_100_CS_AS_SC+N'#')-1>64 BEGIN SET @outcome='Forbidden';SET @code='E-COM-001';GOTO Emit;END;
 IF COALESCE(IS_MEMBER('student_staff'),0)<>1 AND COALESCE(IS_MEMBER('student_admin'),0)<>1 BEGIN SET @outcome='Forbidden';SET @code='E-COM-002';GOTO Emit;END;
 IF @session_id IS NULL OR @request_id IS NULL OR (@target_id IS NULL AND @expected_version IS NOT NULL) OR (@target_id IS NOT NULL AND (@target_id<=0 OR @expected_version IS NULL OR @expected_version<=0))
 BEGIN SET @code='E-COM-003';GOTO Emit;END;
 DECLARE @n xml=TRY_CONVERT(xml,student_api.normalize_raw(@raw,CONVERT(datetime,@day)));
 IF @n IS NULL BEGIN SET @code='E-COM-003';GOTO Emit;END;
 IF @n.value('(/normalized/@ok)[1]','varchar(5)')<>'true' BEGIN SET @code=@n.value('(/normalized/@code)[1]','varchar(16)');SET @field=@n.value('(/normalized/@field)[1]','varchar(64)');SET @max_length=TRY_CONVERT(int,NULLIF(@n.value('(/normalized/@max)[1]','varchar(12)'),''));GOTO Emit;END;
   DECLARE @student_no varchar(15)=CASE WHEN @n.exist('/normalized/values/student_no[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/values/student_no/text())[1]','varchar(15)') END;
  DECLARE @student_name nvarchar(16)=CASE WHEN @n.exist('/normalized/values/student_name[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/values/student_name/text())[1]','nvarchar(16)') END;
  DECLARE @student_name_kana nvarchar(36)=CASE WHEN @n.exist('/normalized/values/student_name_kana[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/values/student_name_kana/text())[1]','nvarchar(36)') END;
  DECLARE @name_key nvarchar(320)=CASE WHEN @n.exist('/normalized/values/name_key[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/values/name_key/text())[1]','nvarchar(320)') END;
  DECLARE @kana_key nvarchar(36)=CASE WHEN @n.exist('/normalized/values/kana_key[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/values/kana_key/text())[1]','nvarchar(36)') END;
  DECLARE @birth_date date=CASE WHEN @n.exist('/normalized/values/birth_date[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/values/birth_date/text())[1]','date') END;
  DECLARE @gender_code varchar(1)=CASE WHEN @n.exist('/normalized/values/gender_code[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/values/gender_code/text())[1]','varchar(1)') END;
  DECLARE @postal_code varchar(7)=CASE WHEN @n.exist('/normalized/values/postal_code[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/values/postal_code/text())[1]','varchar(7)') END;
  DECLARE @prefecture_code varchar(2)=CASE WHEN @n.exist('/normalized/values/prefecture_code[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/values/prefecture_code/text())[1]','varchar(2)') END;
  DECLARE @address_line1 nvarchar(90)=CASE WHEN @n.exist('/normalized/values/address_line1[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/values/address_line1/text())[1]','nvarchar(90)') END;
  DECLARE @address_line2 nvarchar(90)=CASE WHEN @n.exist('/normalized/values/address_line2[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/values/address_line2/text())[1]','nvarchar(90)') END;
  DECLARE @phone_number varchar(16)=CASE WHEN @n.exist('/normalized/values/phone_number[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/values/phone_number/text())[1]','varchar(16)') END;
  DECLARE @email_address varchar(60)=CASE WHEN @n.exist('/normalized/values/email_address[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/values/email_address/text())[1]','varchar(60)') END;
  DECLARE @admission_date date=CASE WHEN @n.exist('/normalized/values/admission_date[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/values/admission_date/text())[1]','date') END;
  DECLARE @enrollment_status_code varchar(2)=CASE WHEN @n.exist('/normalized/values/enrollment_status_code[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/values/enrollment_status_code/text())[1]','varchar(2)') END;
  DECLARE @enrollment_end_date date=CASE WHEN @n.exist('/normalized/values/enrollment_end_date[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/values/enrollment_end_date/text())[1]','date') END;
  DECLARE @class_id bigint=CASE WHEN @n.exist('/normalized/values/class_id[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/values/class_id/text())[1]','bigint') END;
  DECLARE @emergency_contact_name nvarchar(16)=CASE WHEN @n.exist('/normalized/values/emergency_contact_name[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/values/emergency_contact_name/text())[1]','nvarchar(16)') END;
  DECLARE @relationship_category varchar(24)=CASE WHEN @n.exist('/normalized/values/relationship_category[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/values/relationship_category/text())[1]','varchar(24)') END;
  DECLARE @relationship_code varchar(2)=CASE WHEN @n.exist('/normalized/values/relationship_code[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/values/relationship_code/text())[1]','varchar(2)') END;
  DECLARE @emergency_phone_number varchar(16)=CASE WHEN @n.exist('/normalized/values/emergency_phone_number[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/values/emergency_phone_number/text())[1]','varchar(16)') END;
  DECLARE @remarks nvarchar(240)=CASE WHEN @n.exist('/normalized/values/remarks[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/values/remarks/text())[1]','nvarchar(240)') END;
 DECLARE @reason nvarchar(120)=CASE WHEN @n.exist('/normalized/hints/reason[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/hints/reason/text())[1]','nvarchar(120)') END;
 DECLARE @school_year smallint=CASE WHEN @n.exist('/normalized/hints/school_year[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/hints/school_year/text())[1]','smallint') END;
 DECLARE @grade_code varchar(2)=CASE WHEN @n.exist('/normalized/hints/grade_code[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/hints/grade_code/text())[1]','varchar(2)') END;
 DECLARE @lock_result int;
 EXEC @lock_result=sys.sp_getapplock @Resource=N'test-project1:student-write',@LockMode='Exclusive',@LockOwner='Transaction',@LockTimeout=5000,@DbPrincipal='public';
 IF @lock_result<0 BEGIN SET @outcome='Conflict';SET @code='E-STU-105';GOTO Emit;END;
 SELECT * INTO #previous FROM dbo.m_student WITH(UPDLOCK) WHERE student_id=@target_id AND is_deleted=0;
 IF @target_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM #previous) BEGIN SET @outcome='NotFound';SET @code='E-STU-103';GOTO Emit;END;
 IF @target_id IS NOT NULL AND EXISTS(SELECT 1 FROM #previous WHERE row_version<>@expected_version) BEGIN SET @outcome='Conflict';SET @code='E-STU-105';GOTO Emit;END;
 IF @target_id IS NOT NULL AND EXISTS(SELECT 1 FROM #previous WHERE CONVERT(varbinary(max),student_no)<>CONVERT(varbinary(max),@student_no)) BEGIN SET @code='E-STU-104';SET @field='student_no';GOTO Emit;END;
 IF EXISTS(SELECT 1 FROM #previous WHERE enrollment_status_code IN('03','04') AND enrollment_status_code<>@enrollment_status_code)
 BEGIN
  IF COALESCE(IS_MEMBER('student_admin'),0)<>1 BEGIN SET @outcome='Forbidden';SET @code='E-COM-002';GOTO Emit;END;
  IF @reason IS NULL BEGIN SET @code='E-STU-106';SET @field='reason';GOTO Emit;END;
 END;
 DECLARE @codes TABLE(field varchar(64),category varchar(24),value varchar(10),old_value varchar(10));
 INSERT @codes VALUES('gender_code','GENDER',@gender_code,(SELECT gender_code FROM #previous)),('prefecture_code','PREFECTURE',@prefecture_code,(SELECT prefecture_code FROM #previous)),('enrollment_status_code','ENROLLMENT_STATUS',@enrollment_status_code,(SELECT enrollment_status_code FROM #previous)),('relationship_code','RELATIONSHIP',@relationship_code,(SELECT relationship_code FROM #previous));
 IF EXISTS(SELECT 1 FROM @codes v LEFT JOIN dbo.m_code c ON c.category_id=v.category AND c.code_value=v.value WHERE v.value IS NOT NULL AND c.code_value IS NULL)
 BEGIN SET @code='E-STU-009';SELECT TOP(1) @field=v.field FROM @codes v LEFT JOIN dbo.m_code c ON c.category_id=v.category AND c.code_value=v.value WHERE v.value IS NOT NULL AND c.code_value IS NULL;GOTO Emit;END;
 IF EXISTS(SELECT 1 FROM @codes v JOIN dbo.m_code c ON c.category_id=v.category AND c.code_value=v.value JOIN dbo.m_code_category k ON k.category_id=c.category_id WHERE v.value IS NOT NULL AND (v.old_value IS NULL OR v.old_value<>v.value) AND (c.is_active=0 OR k.is_active=0 OR c.valid_from>@day OR c.valid_to<@day))
 BEGIN SET @code='E-STU-011';GOTO Emit;END;
 DECLARE @old_class bigint=(SELECT class_id FROM #previous),@old_status varchar(2)=(SELECT enrollment_status_code FROM #previous),@old_admission date=(SELECT admission_date FROM #previous),@old_end date=(SELECT enrollment_end_date FROM #previous);
 DECLARE @new_seat bit=CASE WHEN @enrollment_status_code IN('01','02') AND @class_id IS NOT NULL THEN 1 ELSE 0 END,@same_seat bit=CASE WHEN @old_status IN('01','02') AND @old_class=@class_id THEN 1 ELSE 0 END;
 IF @class_id IS NOT NULL
 BEGIN
  IF NOT EXISTS(SELECT 1 FROM dbo.m_class WHERE class_id=@class_id) BEGIN SET @code='E-STU-010';SET @field='class_id';GOTO Emit;END;
  IF EXISTS(SELECT 1 FROM dbo.m_class WHERE class_id=@class_id AND ((@school_year IS NOT NULL AND school_year<>@school_year) OR (@grade_code IS NOT NULL AND grade_code<>@grade_code))) BEGIN SET @code='E-STU-014';SET @field='class_id';GOTO Emit;END;
  IF @new_seat=1 AND @same_seat=0 AND EXISTS(SELECT 1 FROM dbo.m_class WHERE class_id=@class_id AND (is_active=0 OR valid_from>@day OR valid_to<@day)) BEGIN SET @code='E-STU-013';SET @field='class_id';GOTO Emit;END;
  IF @same_seat=1 AND @new_seat=1 AND EXISTS(SELECT 1 FROM dbo.m_class WHERE class_id=@class_id AND (valid_from>@day OR valid_to<@day)) SET @warning='W-STU-106';
  IF @enrollment_status_code IN('03','04') AND (@target_id IS NULL OR @old_class IS NULL OR @old_class<>@class_id OR @old_status<>@enrollment_status_code OR @old_admission<>@admission_date OR @old_end IS NULL OR @old_end<>@enrollment_end_date) AND EXISTS(SELECT 1 FROM dbo.m_class WHERE class_id=@class_id AND (@admission_date>valid_to OR @enrollment_end_date<valid_from)) BEGIN SET @code='E-STU-108';SET @field='class_id';GOTO Emit;END;
  IF @new_seat=1 AND @same_seat=0 AND EXISTS(SELECT 1 FROM dbo.m_class c WHERE c.class_id=@class_id AND c.capacity IS NOT NULL AND (SELECT COUNT_BIG(*) FROM dbo.m_student s WHERE s.class_id=@class_id AND s.is_deleted=0 AND s.enrollment_status_code IN('01','02') AND (@target_id IS NULL OR s.student_id<>@target_id))+1>c.capacity) BEGIN SET @code='E-STU-102';SET @field='class_id';GOTO Emit;END;
 END;
 DECLARE @changed TABLE(name varchar(64) PRIMARY KEY);
   IF @target_id IS NULL OR EXISTS(SELECT CONVERT(varbinary(max),@student_no) EXCEPT SELECT CONVERT(varbinary(max),student_no) FROM #previous) INSERT @changed VALUES('student_no');
  IF @target_id IS NULL OR EXISTS(SELECT CONVERT(varbinary(max),@student_name) EXCEPT SELECT CONVERT(varbinary(max),student_name) FROM #previous) INSERT @changed VALUES('student_name');
  IF @target_id IS NULL OR EXISTS(SELECT CONVERT(varbinary(max),@student_name_kana) EXCEPT SELECT CONVERT(varbinary(max),student_name_kana) FROM #previous) INSERT @changed VALUES('student_name_kana');
  IF @target_id IS NULL OR EXISTS(SELECT CONVERT(varbinary(max),@name_key) EXCEPT SELECT CONVERT(varbinary(max),name_key) FROM #previous) INSERT @changed VALUES('name_key');
  IF @target_id IS NULL OR EXISTS(SELECT CONVERT(varbinary(max),@kana_key) EXCEPT SELECT CONVERT(varbinary(max),kana_key) FROM #previous) INSERT @changed VALUES('kana_key');
  IF @target_id IS NULL OR EXISTS(SELECT @birth_date EXCEPT SELECT birth_date FROM #previous) INSERT @changed VALUES('birth_date');
  IF @target_id IS NULL OR EXISTS(SELECT CONVERT(varbinary(max),@gender_code) EXCEPT SELECT CONVERT(varbinary(max),gender_code) FROM #previous) INSERT @changed VALUES('gender_code');
  IF @target_id IS NULL OR EXISTS(SELECT CONVERT(varbinary(max),@postal_code) EXCEPT SELECT CONVERT(varbinary(max),postal_code) FROM #previous) INSERT @changed VALUES('postal_code');
  IF @target_id IS NULL OR EXISTS(SELECT CONVERT(varbinary(max),@prefecture_code) EXCEPT SELECT CONVERT(varbinary(max),prefecture_code) FROM #previous) INSERT @changed VALUES('prefecture_code');
  IF @target_id IS NULL OR EXISTS(SELECT CONVERT(varbinary(max),@address_line1) EXCEPT SELECT CONVERT(varbinary(max),address_line1) FROM #previous) INSERT @changed VALUES('address_line1');
  IF @target_id IS NULL OR EXISTS(SELECT CONVERT(varbinary(max),@address_line2) EXCEPT SELECT CONVERT(varbinary(max),address_line2) FROM #previous) INSERT @changed VALUES('address_line2');
  IF @target_id IS NULL OR EXISTS(SELECT CONVERT(varbinary(max),@phone_number) EXCEPT SELECT CONVERT(varbinary(max),phone_number) FROM #previous) INSERT @changed VALUES('phone_number');
  IF @target_id IS NULL OR EXISTS(SELECT CONVERT(varbinary(max),@email_address) EXCEPT SELECT CONVERT(varbinary(max),email_address) FROM #previous) INSERT @changed VALUES('email_address');
  IF @target_id IS NULL OR EXISTS(SELECT @admission_date EXCEPT SELECT admission_date FROM #previous) INSERT @changed VALUES('admission_date');
  IF @target_id IS NULL OR EXISTS(SELECT CONVERT(varbinary(max),@enrollment_status_code) EXCEPT SELECT CONVERT(varbinary(max),enrollment_status_code) FROM #previous) INSERT @changed VALUES('enrollment_status_code');
  IF @target_id IS NULL OR EXISTS(SELECT @enrollment_end_date EXCEPT SELECT enrollment_end_date FROM #previous) INSERT @changed VALUES('enrollment_end_date');
  IF @target_id IS NULL OR EXISTS(SELECT @class_id EXCEPT SELECT class_id FROM #previous) INSERT @changed VALUES('class_id');
  IF @target_id IS NULL OR EXISTS(SELECT CONVERT(varbinary(max),@emergency_contact_name) EXCEPT SELECT CONVERT(varbinary(max),emergency_contact_name) FROM #previous) INSERT @changed VALUES('emergency_contact_name');
  IF @target_id IS NULL OR EXISTS(SELECT CONVERT(varbinary(max),@relationship_category) EXCEPT SELECT CONVERT(varbinary(max),relationship_category) FROM #previous) INSERT @changed VALUES('relationship_category');
  IF @target_id IS NULL OR EXISTS(SELECT CONVERT(varbinary(max),@relationship_code) EXCEPT SELECT CONVERT(varbinary(max),relationship_code) FROM #previous) INSERT @changed VALUES('relationship_code');
  IF @target_id IS NULL OR EXISTS(SELECT CONVERT(varbinary(max),@emergency_phone_number) EXCEPT SELECT CONVERT(varbinary(max),emergency_phone_number) FROM #previous) INSERT @changed VALUES('emergency_phone_number');
  IF @target_id IS NULL OR EXISTS(SELECT CONVERT(varbinary(max),@remarks) EXCEPT SELECT CONVERT(varbinary(max),remarks) FROM #previous) INSERT @changed VALUES('remarks');
 IF NOT EXISTS(SELECT 1 FROM @changed) BEGIN SET @outcome='NoChange';GOTO Emit;END;
 IF @expected_version=9223372036854775807 BEGIN SET @outcome='Conflict';SET @code='E-STU-105';GOTO Emit;END;
 IF EXISTS(SELECT 1 FROM dbo.m_student WHERE student_no=@student_no AND (@target_id IS NULL OR student_id<>@target_id)) BEGIN SET @code='E-STU-101';SET @field='student_no';GOTO Emit;END;
 INSERT @candidates SELECT student_id,row_version FROM dbo.m_student WHERE is_deleted=0 AND (@target_id IS NULL OR student_id<>@target_id) AND birth_date=@birth_date AND (name_key=@name_key OR kana_key=@kana_key);
 SELECT @candidate_count=COUNT(*) FROM @candidates;
 DECLARE @payload_hash binary(32)=HASHBYTES('SHA2_256',CONVERT(varbinary(max),CONVERT(nvarchar(max),@n.query('/normalized/values'))));
 DECLARE @candidate_text nvarchar(max)=COALESCE((SELECT STRING_AGG(CONVERT(nvarchar(max),CONCAT(student_id,':',row_version)),';') WITHIN GROUP(ORDER BY student_id) FROM @candidates),N'');
 DECLARE @candidate_hash binary(32)=HASHBYTES('SHA2_256',CONVERT(varbinary(max),@candidate_text)),@confirmed bit=0;
 IF @confirmation_token IS NOT NULL AND EXISTS(SELECT 1 FROM dbo.t_confirmation WITH(UPDLOCK) WHERE token=@confirmation_token AND principal=@actor COLLATE Latin1_General_100_BIN2 AND session_id=@session_id AND ((target_id IS NULL AND @target_id IS NULL) OR target_id=@target_id) AND ((expected_version IS NULL AND @expected_version IS NULL) OR expected_version=@expected_version) AND payload_hash=@payload_hash AND candidate_hash=@candidate_hash AND expires_at>@now AND consumed=0) SET @confirmed=1;
 IF @confirmed=1 AND @reason IS NULL BEGIN SET @code='E-STU-107';SET @field='reason';GOTO Emit;END;
 IF (@candidate_count>0 OR @confirmation_token IS NOT NULL) AND @confirmed=0
 BEGIN
  SET @token=NEWID();INSERT dbo.t_confirmation(token,principal,session_id,target_id,expected_version,payload_hash,candidate_hash,expires_at,consumed) VALUES(@token,@actor,@session_id,@target_id,@expected_version,@payload_hash,@candidate_hash,DATEADD(minute,10,@now),0);
  SET @outcome='ConfirmationRequired';SET @code=CASE WHEN @confirmation_token IS NULL THEN 'W-STU-101' ELSE 'W-STU-102' END;GOTO Emit;
 END;
 IF @write=0 BEGIN SET @outcome='Ready';GOTO Emit;END;
 DECLARE @written TABLE(student_id bigint,row_version bigint);
 IF @target_id IS NULL
 BEGIN
  INSERT dbo.m_student(student_no,student_name,student_name_kana,name_key,kana_key,birth_date,gender_code,postal_code,prefecture_code,address_line1,address_line2,phone_number,email_address,admission_date,enrollment_status_code,enrollment_end_date,class_id,emergency_contact_name,relationship_category,relationship_code,emergency_phone_number,remarks,gender_category,prefecture_category,enrollment_category,is_deleted,created_at,created_by,updated_at,updated_by,row_version)
  OUTPUT inserted.student_id,inserted.row_version INTO @written
  VALUES(@student_no,@student_name,@student_name_kana,@name_key,@kana_key,@birth_date,@gender_code,@postal_code,@prefecture_code,@address_line1,@address_line2,@phone_number,@email_address,@admission_date,@enrollment_status_code,@enrollment_end_date,@class_id,@emergency_contact_name,@relationship_category,@relationship_code,@emergency_phone_number,@remarks,'GENDER','PREFECTURE','ENROLLMENT_STATUS',0,@now,@actor,@now,@actor,1);
  INSERT @changed VALUES('gender_category'),('prefecture_category'),('enrollment_category'),('is_deleted'),('created_at'),('created_by'),('updated_at'),('updated_by'),('row_version');
 END
 ELSE
 BEGIN
  UPDATE dbo.m_student SET student_name=@student_name,student_name_kana=@student_name_kana,name_key=@name_key,kana_key=@kana_key,birth_date=@birth_date,gender_code=@gender_code,postal_code=@postal_code,prefecture_code=@prefecture_code,address_line1=@address_line1,address_line2=@address_line2,phone_number=@phone_number,email_address=@email_address,admission_date=@admission_date,enrollment_status_code=@enrollment_status_code,enrollment_end_date=@enrollment_end_date,class_id=@class_id,emergency_contact_name=@emergency_contact_name,relationship_category=@relationship_category,relationship_code=@relationship_code,emergency_phone_number=@emergency_phone_number,remarks=@remarks,updated_at=@now,updated_by=@actor,row_version=row_version+1 OUTPUT inserted.student_id,inserted.row_version INTO @written WHERE student_id=@target_id AND row_version=@expected_version AND is_deleted=0;
  IF @@ROWCOUNT<>1 THROW 51005,'E-STU-105',1;
  INSERT @changed VALUES('updated_at'),('updated_by'),('row_version');
 END;
 SELECT @saved_id=student_id,@saved_version=row_version FROM @written;
 DECLARE @changed_json nvarchar(max)=N'['+(SELECT STRING_AGG(CONVERT(nvarchar(max),N'"'+name+N'"'),N',') WITHIN GROUP(ORDER BY name) FROM @changed)+N']';
 INSERT dbo.t_operation_log(target_table,target_key,operation_type,before_version,after_version,changed_columns,executed_by,executed_at,correlation_id,operation_reason,duplicate_confirmed)
 VALUES('m_student',CONVERT(varchar(35),@saved_id),CASE WHEN @target_id IS NULL THEN 'CREATE' ELSE 'UPDATE' END,@expected_version,@saved_version,@changed_json,@actor,@now,@request_id,@reason,@confirmed);
 IF @confirmed=1 BEGIN UPDATE dbo.t_confirmation SET consumed=1 WHERE token=@confirmation_token AND consumed=0;IF @@ROWCOUNT<>1 THROW 51005,'E-STU-105',1;END;
 SET @outcome='Saved';SET @code='I-STU-001';
Emit:
 SELECT @outcome outcome,@code code,@field field,@saved_id student_id,@saved_version row_version,@token confirmation_token,@candidate_count candidate_count,@request_id request_id,@warning warning_code,@max_length max_length;
 SELECT s.student_no,s.student_name,s.birth_date,c.class_name FROM dbo.m_student s LEFT JOIN dbo.m_class c ON c.class_id=s.class_id WHERE s.student_id IN(SELECT TOP(20) student_id FROM @candidates ORDER BY student_id) ORDER BY s.student_id;
END;
GO
CREATE OR ALTER PROCEDURE student_api.prepare_save @raw nvarchar(max),@target_id bigint=NULL,@expected_version bigint=NULL,@session_id uniqueidentifier,@confirmation_token uniqueidentifier=NULL,@request_id uniqueidentifier
AS BEGIN SET NOCOUNT ON; EXEC student_api.process_save @raw,@target_id,@expected_version,@session_id,@confirmation_token,@request_id,0; END;
GO
CREATE OR ALTER PROCEDURE student_api.persist_student @raw nvarchar(max),@target_id bigint=NULL,@expected_version bigint=NULL,@session_id uniqueidentifier,@confirmation_token uniqueidentifier=NULL,@request_id uniqueidentifier
AS BEGIN SET NOCOUNT ON; EXEC student_api.process_save @raw,@target_id,@expected_version,@session_id,@confirmation_token,@request_id,1; END;
GO
CREATE OR ALTER PROCEDURE student_api.delete_student @target_id bigint,@expected_version bigint,@raw_reason nvarchar(max),@session_id uniqueidentifier,@request_id uniqueidentifier
AS
BEGIN
 SET NOCOUNT ON;SET XACT_ABORT ON;SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
 DECLARE @outcome varchar(32)='ValidationFailed',@code varchar(16)=NULL,@field varchar(64)='reason',@actor nvarchar(128)=ORIGINAL_LOGIN(),@now datetimeoffset(7)=TODATETIMEOFFSET(SYSUTCDATETIME(),'+00:00'),@saved_version bigint=@expected_version;
 IF @@TRANCOUNT=0 OR XACT_STATE()<>1 OR @session_id IS NULL OR @request_id IS NULL OR @target_id IS NULL OR @expected_version IS NULL OR @target_id<=0 OR @expected_version<=0 OR @expected_version=9223372036854775807 BEGIN SET @code='E-COM-003';GOTO Emit;END;
 IF @actor IS NULL OR LEN(@actor COLLATE Latin1_General_100_CS_AS_SC+N'#')-1>64 BEGIN SET @outcome='Forbidden';SET @code='E-COM-001';GOTO Emit;END;
 IF COALESCE(IS_MEMBER('student_admin'),0)<>1 BEGIN SET @outcome='Forbidden';SET @code='E-COM-002';GOTO Emit;END;
 DECLARE @n xml=TRY_CONVERT(xml,student_api.normalize_reason(@raw_reason));
 IF @n IS NULL OR @n.value('(/normalized/@ok)[1]','varchar(5)')<>'true' BEGIN SET @code=COALESCE(@n.value('(/normalized/@code)[1]','varchar(16)'),'E-COM-003');GOTO Emit;END;
 DECLARE @reason nvarchar(120)=@n.value('(/normalized/hints/reason/text())[1]','nvarchar(120)'),@lock_result int;
 EXEC @lock_result=sys.sp_getapplock @Resource=N'test-project1:student-write',@LockMode='Exclusive',@LockOwner='Transaction',@LockTimeout=5000,@DbPrincipal='public';
 IF @lock_result<0 BEGIN SET @outcome='Conflict';SET @code='E-STU-105';GOTO Emit;END;
 IF NOT EXISTS(SELECT 1 FROM dbo.m_student WITH(UPDLOCK) WHERE student_id=@target_id AND is_deleted=0) BEGIN SET @outcome='NotFound';SET @code='E-STU-103';GOTO Emit;END;
 IF EXISTS(SELECT 1 FROM dbo.m_student WHERE student_id=@target_id AND is_deleted=0 AND row_version<>@expected_version) BEGIN SET @outcome='Conflict';SET @code='E-STU-105';GOTO Emit;END;
 UPDATE dbo.m_student SET is_deleted=1,deleted_at=@now,deleted_by=@actor,delete_reason=@reason,updated_at=@now,updated_by=@actor,row_version=row_version+1 WHERE student_id=@target_id AND row_version=@expected_version AND is_deleted=0;
 IF @@ROWCOUNT<>1 THROW 51005,'E-STU-105',1;
 SET @saved_version=@expected_version+1;
 INSERT dbo.t_operation_log(target_table,target_key,operation_type,before_version,after_version,changed_columns,executed_by,executed_at,correlation_id,operation_reason,duplicate_confirmed)
 VALUES('m_student',CONVERT(varchar(35),@target_id),'DELETE',@expected_version,@saved_version,N'["is_deleted","deleted_at","deleted_by","delete_reason","updated_at","updated_by","row_version"]',@actor,@now,@request_id,@reason,0);
 SET @outcome='Saved';SET @code='I-STU-003';
Emit:
 SELECT @outcome outcome,@code code,@field field,@target_id student_id,@saved_version row_version,CAST(NULL AS uniqueidentifier) confirmation_token,0 candidate_count,@request_id request_id,CAST(NULL AS varchar(16)) warning_code,60 max_length;
END;
GO
-- Procedures and tables have dbo ownership; ownership chaining permits their fixed DML.
-- Calling identities retain their actual DB role; no EXECUTE AS OWNER impersonation.
DENY EXECUTE ON OBJECT::student_api.process_save TO student_staff,student_admin,student_viewer;
GRANT EXECUTE ON OBJECT::student_api.prepare_save TO student_staff,student_admin;
GRANT EXECUTE ON OBJECT::student_api.persist_student TO student_staff,student_admin;
GRANT EXECUTE ON OBJECT::student_api.delete_student TO student_admin;
DENY INSERT,UPDATE,DELETE ON dbo.m_student TO student_staff,student_admin,student_viewer;
DENY INSERT,UPDATE,DELETE ON dbo.m_class TO student_staff,student_admin,student_viewer;
DENY INSERT,UPDATE,DELETE ON dbo.m_code TO student_staff,student_admin,student_viewer;
DENY INSERT,UPDATE,DELETE ON dbo.m_code_category TO student_staff,student_admin,student_viewer;
DENY INSERT,UPDATE,DELETE ON dbo.t_operation_log TO student_staff,student_admin,student_viewer;
DENY INSERT,UPDATE,DELETE ON dbo.t_confirmation TO student_staff,student_admin,student_viewer;
GRANT SELECT ON dbo.m_student TO student_viewer,student_staff,student_admin;
GRANT SELECT ON dbo.m_class TO student_viewer,student_staff,student_admin;
GRANT SELECT ON dbo.m_code TO student_viewer,student_staff,student_admin;
GRANT SELECT ON dbo.m_code_category TO student_viewer,student_staff,student_admin;
GO
