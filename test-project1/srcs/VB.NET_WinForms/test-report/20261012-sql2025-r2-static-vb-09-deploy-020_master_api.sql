-- VB.NET WinForms-only master maintenance. Caller commits; all operations use the student gate.

CREATE OR ALTER PROCEDURE student_api.save_class @raw nvarchar(max),@target_id bigint=NULL, @expected_version bigint=NULL,@request_id uniqueidentifier
AS
BEGIN
 SET NOCOUNT ON;SET XACT_ABORT ON;SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
 DECLARE @outcome varchar(32)='ValidationFailed',@code varchar(16)=NULL,@field varchar(64)='',@before bigint=NULL,@after bigint=NULL,@same bit=0,@target_key varchar(35)=NULL,@max_length int=NULL;
 DECLARE @actor nvarchar(128)=ORIGINAL_LOGIN(),@now datetimeoffset(7)=TODATETIMEOFFSET(SYSUTCDATETIME(),'+00:00'),@day date;
 SET @day=CONVERT(date,DATEADD(hour,9,@now));
 IF @@TRANCOUNT=0 OR XACT_STATE()<>1 OR @request_id IS NULL OR @expected_version<=0  OR (@target_id IS NULL AND @expected_version IS NOT NULL) OR (@target_id IS NOT NULL AND (@target_id<=0 OR @expected_version IS NULL)) BEGIN SET @code='E-COM-003';GOTO Emit;END;
 IF @actor IS NULL OR LEN(@actor COLLATE Latin1_General_100_CS_AS_SC+N'#')-1>64 BEGIN SET @outcome='Forbidden';SET @code='E-COM-001';GOTO Emit;END;
 IF COALESCE(IS_MEMBER('student_admin'),0)<>1 BEGIN SET @outcome='Forbidden';SET @code='E-COM-002';GOTO Emit;END;
 DECLARE @n xml=TRY_CONVERT(xml,student_api.normalize_class(@raw));
 IF @n IS NULL BEGIN SET @code='E-COM-003';GOTO Emit;END;
 IF @n.value('(/normalized/@ok)[1]','varchar(5)')<>'true' BEGIN SET @code=@n.value('(/normalized/@code)[1]','varchar(16)');SET @field=@n.value('(/normalized/@field)[1]','varchar(64)');SET @max_length=TRY_CONVERT(int,NULLIF(@n.value('(/normalized/@max)[1]','varchar(12)'),''));GOTO Emit;END;
  DECLARE @school_year smallint=CASE WHEN @n.exist('/normalized/values/school_year[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/values/school_year/text())[1]','smallint') END;
 DECLARE @grade_code varchar(2)=CASE WHEN @n.exist('/normalized/values/grade_code[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/values/grade_code/text())[1]','varchar(2)') END;
 DECLARE @class_code varchar(9)=CASE WHEN @n.exist('/normalized/values/class_code[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/values/class_code/text())[1]','varchar(9)') END;
 DECLARE @class_name nvarchar(36)=CASE WHEN @n.exist('/normalized/values/class_name[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/values/class_name/text())[1]','nvarchar(36)') END;
 DECLARE @valid_from date=CASE WHEN @n.exist('/normalized/values/valid_from[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/values/valid_from/text())[1]','date') END;
 DECLARE @valid_to date=CASE WHEN @n.exist('/normalized/values/valid_to[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/values/valid_to/text())[1]','date') END;
 DECLARE @capacity int=CASE WHEN @n.exist('/normalized/values/capacity[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/values/capacity/text())[1]','int') END;
 DECLARE @display_order int=CASE WHEN @n.exist('/normalized/values/display_order[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/values/display_order/text())[1]','int') END;
 DECLARE @is_active bit=CASE WHEN @n.exist('/normalized/values/is_active[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/values/is_active/text())[1]','bit') END;
 DECLARE @remarks nvarchar(240)=CASE WHEN @n.exist('/normalized/values/remarks[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/values/remarks/text())[1]','nvarchar(240)') END;
 DECLARE @reason nvarchar(120)=CASE WHEN @n.exist('/normalized/hints/reason[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/hints/reason/text())[1]','nvarchar(120)') END,@lock int;
 EXEC @lock=sys.sp_getapplock @Resource=N'test-project1:student-write',@LockMode='Exclusive',@LockOwner='Transaction',@LockTimeout=5000,@DbPrincipal='public';
 IF @lock<0 BEGIN SET @outcome='Conflict';SET @code='E-STU-105';GOTO Emit;END;
 SELECT * INTO #old FROM dbo.m_class WITH(UPDLOCK) WHERE class_id=@target_id;
 SELECT @before=row_version FROM #old;
 
 IF @target_id IS NOT NULL AND @before IS NULL BEGIN SET @outcome='NotFound';SET @code='E-STU-010';GOTO Emit;END;
 IF @before IS NOT NULL AND (@expected_version IS NULL OR @before<>@expected_version) BEGIN SET @outcome='Conflict';SET @code='E-STU-105';GOTO Emit;END;
 IF EXISTS(SELECT 1 FROM #old WHERE school_year<>@school_year OR CONVERT(varbinary(max),class_code)<>CONVERT(varbinary(max),@class_code)) BEGIN SET @code='E-MST-003';GOTO Emit;END;
 DECLARE @refs bigint=(SELECT COUNT_BIG(*) FROM dbo.m_student WHERE class_id=@target_id),@occupied bigint=(SELECT COUNT_BIG(*) FROM dbo.m_student WHERE class_id=@target_id AND is_deleted=0 AND enrollment_status_code IN('01','02'));
 IF @refs>0 AND EXISTS(SELECT 1 FROM #old WHERE grade_code<>@grade_code) BEGIN SET @code='E-MST-003';GOTO Emit;END;
 IF (@occupied>0 AND (@is_active=0 OR @valid_from>@day OR @valid_to<@day)) OR (@capacity IS NOT NULL AND @capacity<@occupied) BEGIN SET @code='E-MST-004';GOTO Emit;END;
 IF NOT EXISTS(SELECT 1 FROM dbo.m_code WHERE category_id='GRADE' AND code_value=@grade_code) BEGIN SET @code='E-STU-009';SET @field='grade_code';GOTO Emit;END;
 IF NOT EXISTS(SELECT 1 FROM #old WHERE grade_code=@grade_code) AND EXISTS(SELECT 1 FROM dbo.m_code c JOIN dbo.m_code_category k ON c.category_id=k.category_id WHERE c.category_id='GRADE' AND c.code_value=@grade_code AND (c.is_active=0 OR k.is_active=0 OR c.valid_from>@day OR c.valid_to<@day)) BEGIN SET @code='E-STU-011';SET @field='grade_code';GOTO Emit;END;
 IF EXISTS(SELECT 1 FROM dbo.m_class WHERE school_year=@school_year AND class_code=@class_code AND (@target_id IS NULL OR class_id<>@target_id)) BEGIN SET @code='E-MST-002';GOTO Emit;END;
 IF EXISTS(SELECT 1 FROM dbo.m_class WHERE school_year=@school_year AND grade_code=@grade_code AND class_name=@class_name AND (@target_id IS NULL OR class_id<>@target_id)) SET @same=1;
 
 DECLARE @changed TABLE(name varchar(64) PRIMARY KEY);
  IF @before IS NULL OR EXISTS(SELECT @school_year EXCEPT SELECT school_year FROM #old) INSERT @changed VALUES('school_year');
 IF @before IS NULL OR EXISTS(SELECT CONVERT(varbinary(max),@grade_code) EXCEPT SELECT CONVERT(varbinary(max),grade_code) FROM #old) INSERT @changed VALUES('grade_code');
 IF @before IS NULL OR EXISTS(SELECT CONVERT(varbinary(max),@class_code) EXCEPT SELECT CONVERT(varbinary(max),class_code) FROM #old) INSERT @changed VALUES('class_code');
 IF @before IS NULL OR EXISTS(SELECT CONVERT(varbinary(max),@class_name) EXCEPT SELECT CONVERT(varbinary(max),class_name) FROM #old) INSERT @changed VALUES('class_name');
 IF @before IS NULL OR EXISTS(SELECT @valid_from EXCEPT SELECT valid_from FROM #old) INSERT @changed VALUES('valid_from');
 IF @before IS NULL OR EXISTS(SELECT @valid_to EXCEPT SELECT valid_to FROM #old) INSERT @changed VALUES('valid_to');
 IF @before IS NULL OR EXISTS(SELECT @capacity EXCEPT SELECT capacity FROM #old) INSERT @changed VALUES('capacity');
 IF @before IS NULL OR EXISTS(SELECT @display_order EXCEPT SELECT display_order FROM #old) INSERT @changed VALUES('display_order');
 IF @before IS NULL OR EXISTS(SELECT @is_active EXCEPT SELECT is_active FROM #old) INSERT @changed VALUES('is_active');
 IF @before IS NULL OR EXISTS(SELECT CONVERT(varbinary(max),@remarks) EXCEPT SELECT CONVERT(varbinary(max),remarks) FROM #old) INSERT @changed VALUES('remarks');
 IF NOT EXISTS(SELECT 1 FROM @changed) BEGIN SET @outcome='NoChange';SET @after=@before;SET @code='I-STU-004';GOTO Emit;END;
 IF @before=9223372036854775807 BEGIN SET @outcome='Conflict';SET @code='E-STU-105';GOTO Emit;END;
 DECLARE @old_active bit=(SELECT is_active FROM #old),@operation varchar(11);
 SET @operation=CASE WHEN @before IS NULL THEN 'CREATE' WHEN @old_active=1 AND @is_active=0 THEN 'DISABLE' WHEN @old_active=0 AND @is_active=1 THEN 'ENABLE' ELSE 'UPDATE' END;
 DECLARE @written TABLE(id bigint);
 IF @before IS NULL
 BEGIN
  INSERT dbo.m_class(school_year,grade_code,class_code,class_name,valid_from,valid_to,capacity,display_order,is_active,remarks,grade_category,created_at,created_by,updated_at,updated_by,row_version) OUTPUT inserted.class_id INTO @written  VALUES(@school_year,@grade_code,@class_code,@class_name,@valid_from,@valid_to,@capacity,@display_order,@is_active,@remarks,'GRADE',@now,@actor,@now,@actor,1);
  INSERT @changed VALUES ('grade_category'),('created_at'),('created_by'),('updated_at'),('updated_by'),('row_version');
 END
 ELSE
 BEGIN
  UPDATE dbo.m_class SET grade_code=@grade_code,class_name=@class_name,valid_from=@valid_from,valid_to=@valid_to,capacity=@capacity,display_order=@display_order,is_active=@is_active,remarks=@remarks,updated_at=@now,updated_by=@actor,row_version=row_version+1 WHERE class_id=@target_id AND row_version=@expected_version;
  IF @@ROWCOUNT<>1 THROW 51005,'E-STU-105',1;
  INSERT @changed VALUES('updated_at'),('updated_by'),('row_version');
  INSERT @written VALUES(@target_id);
 END;
 SELECT @target_key=CONVERT(varchar(35),id) FROM @written;
 SET @after=COALESCE(@before,0)+1;
 DECLARE @changed_json nvarchar(max)=N'['+(SELECT STRING_AGG(CONVERT(nvarchar(max),N'"'+name+N'"'),N',') WITHIN GROUP(ORDER BY name) FROM @changed)+N']';
 INSERT dbo.t_operation_log(target_table,target_key,operation_type,before_version,after_version,changed_columns,executed_by,executed_at,correlation_id,operation_reason,duplicate_confirmed) VALUES('m_class',@target_key,@operation,@before,@after,@changed_json,@actor,@now,@request_id,@reason,0);
 SET @outcome='Saved';SET @code=CASE WHEN @same=1 THEN 'W-MST-001' ELSE 'I-STU-002' END;
Emit:
 SELECT @outcome outcome,@code code,@field field,@after row_version,@same same_name_warning,@target_key target_key,@request_id request_id,@max_length max_length;
END;
GO
GRANT EXECUTE ON OBJECT::student_api.save_class TO student_admin;
GO


CREATE OR ALTER PROCEDURE student_api.save_code @raw nvarchar(max), @expected_version bigint=NULL,@request_id uniqueidentifier
AS
BEGIN
 SET NOCOUNT ON;SET XACT_ABORT ON;SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
 DECLARE @outcome varchar(32)='ValidationFailed',@code varchar(16)=NULL,@field varchar(64)='',@before bigint=NULL,@after bigint=NULL,@same bit=0,@target_key varchar(35)=NULL,@max_length int=NULL;
 DECLARE @actor nvarchar(128)=ORIGINAL_LOGIN(),@now datetimeoffset(7)=TODATETIMEOFFSET(SYSUTCDATETIME(),'+00:00'),@day date;
 SET @day=CONVERT(date,DATEADD(hour,9,@now));
 IF @@TRANCOUNT=0 OR XACT_STATE()<>1 OR @request_id IS NULL OR @expected_version<=0  BEGIN SET @code='E-COM-003';GOTO Emit;END;
 IF @actor IS NULL OR LEN(@actor COLLATE Latin1_General_100_CS_AS_SC+N'#')-1>64 BEGIN SET @outcome='Forbidden';SET @code='E-COM-001';GOTO Emit;END;
 IF COALESCE(IS_MEMBER('student_admin'),0)<>1 BEGIN SET @outcome='Forbidden';SET @code='E-COM-002';GOTO Emit;END;
 DECLARE @n xml=TRY_CONVERT(xml,student_api.normalize_code(@raw));
 IF @n IS NULL BEGIN SET @code='E-COM-003';GOTO Emit;END;
 IF @n.value('(/normalized/@ok)[1]','varchar(5)')<>'true' BEGIN SET @code=@n.value('(/normalized/@code)[1]','varchar(16)');SET @field=@n.value('(/normalized/@field)[1]','varchar(64)');SET @max_length=TRY_CONVERT(int,NULLIF(@n.value('(/normalized/@max)[1]','varchar(12)'),''));GOTO Emit;END;
  DECLARE @category_id varchar(24)=CASE WHEN @n.exist('/normalized/values/category_id[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/values/category_id/text())[1]','varchar(24)') END;
 DECLARE @code_value varchar(10)=CASE WHEN @n.exist('/normalized/values/code_value[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/values/code_value/text())[1]','varchar(10)') END;
 DECLARE @code_name nvarchar(24)=CASE WHEN @n.exist('/normalized/values/code_name[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/values/code_name/text())[1]','nvarchar(24)') END;
 DECLARE @display_order int=CASE WHEN @n.exist('/normalized/values/display_order[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/values/display_order/text())[1]','int') END;
 DECLARE @is_active bit=CASE WHEN @n.exist('/normalized/values/is_active[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/values/is_active/text())[1]','bit') END;
 DECLARE @valid_from date=CASE WHEN @n.exist('/normalized/values/valid_from[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/values/valid_from/text())[1]','date') END;
 DECLARE @valid_to date=CASE WHEN @n.exist('/normalized/values/valid_to[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/values/valid_to/text())[1]','date') END;
 DECLARE @remarks nvarchar(240)=CASE WHEN @n.exist('/normalized/values/remarks[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/values/remarks/text())[1]','nvarchar(240)') END;
 DECLARE @reason nvarchar(120)=CASE WHEN @n.exist('/normalized/hints/reason[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/hints/reason/text())[1]','nvarchar(120)') END,@lock int;
 EXEC @lock=sys.sp_getapplock @Resource=N'test-project1:student-write',@LockMode='Exclusive',@LockOwner='Transaction',@LockTimeout=5000,@DbPrincipal='public';
 IF @lock<0 BEGIN SET @outcome='Conflict';SET @code='E-STU-105';GOTO Emit;END;
 SELECT * INTO #old FROM dbo.m_code WITH(UPDLOCK) WHERE category_id=@category_id AND code_value=@code_value;
 SELECT @before=row_version FROM #old;
 
 IF @before IS NULL AND @expected_version IS NOT NULL BEGIN SET @outcome='NotFound';SET @code='E-STU-009';GOTO Emit;END;
 IF @before IS NOT NULL AND @expected_version IS NULL BEGIN SET @code='E-MST-002';GOTO Emit;END;
 IF @before IS NOT NULL AND @before<>@expected_version BEGIN SET @outcome='Conflict';SET @code='E-STU-105';GOTO Emit;END;
 IF NOT EXISTS(SELECT 1 FROM dbo.m_code_category WHERE category_id=@category_id) BEGIN SET @code='E-MST-001';GOTO Emit;END;
 IF EXISTS(SELECT 1 FROM dbo.m_code_category WHERE category_id=@category_id AND code_length<>LEN(@code_value)) BEGIN SET @code='E-STU-009';SET @field='code_value';GOTO Emit;END;
 IF @before IS NULL AND EXISTS(SELECT 1 FROM dbo.m_code_category WHERE category_id=@category_id AND allow_add=0) BEGIN SET @code='E-MST-003';GOTO Emit;END;
 IF EXISTS(SELECT 1 FROM #old WHERE is_protected=1 AND (@is_active=0 OR @valid_from>valid_from OR (@valid_to IS NOT NULL AND (valid_to IS NULL OR @valid_to<valid_to)))) BEGIN SET @code='E-MST-003';GOTO Emit;END;
 
 DECLARE @changed TABLE(name varchar(64) PRIMARY KEY);
  IF @before IS NULL OR EXISTS(SELECT CONVERT(varbinary(max),@category_id) EXCEPT SELECT CONVERT(varbinary(max),category_id) FROM #old) INSERT @changed VALUES('category_id');
 IF @before IS NULL OR EXISTS(SELECT CONVERT(varbinary(max),@code_value) EXCEPT SELECT CONVERT(varbinary(max),code_value) FROM #old) INSERT @changed VALUES('code_value');
 IF @before IS NULL OR EXISTS(SELECT CONVERT(varbinary(max),@code_name) EXCEPT SELECT CONVERT(varbinary(max),code_name) FROM #old) INSERT @changed VALUES('code_name');
 IF @before IS NULL OR EXISTS(SELECT @display_order EXCEPT SELECT display_order FROM #old) INSERT @changed VALUES('display_order');
 IF @before IS NULL OR EXISTS(SELECT @is_active EXCEPT SELECT is_active FROM #old) INSERT @changed VALUES('is_active');
 IF @before IS NULL OR EXISTS(SELECT @valid_from EXCEPT SELECT valid_from FROM #old) INSERT @changed VALUES('valid_from');
 IF @before IS NULL OR EXISTS(SELECT @valid_to EXCEPT SELECT valid_to FROM #old) INSERT @changed VALUES('valid_to');
 IF @before IS NULL OR EXISTS(SELECT CONVERT(varbinary(max),@remarks) EXCEPT SELECT CONVERT(varbinary(max),remarks) FROM #old) INSERT @changed VALUES('remarks');
 IF NOT EXISTS(SELECT 1 FROM @changed) BEGIN SET @outcome='NoChange';SET @after=@before;SET @code='I-STU-004';GOTO Emit;END;
 IF @before=9223372036854775807 BEGIN SET @outcome='Conflict';SET @code='E-STU-105';GOTO Emit;END;
 DECLARE @old_active bit=(SELECT is_active FROM #old),@operation varchar(11);
 SET @operation=CASE WHEN @before IS NULL THEN 'CREATE' WHEN @old_active=1 AND @is_active=0 THEN 'DISABLE' WHEN @old_active=0 AND @is_active=1 THEN 'ENABLE' ELSE 'UPDATE' END;
 DECLARE @written TABLE(id bigint);
 IF @before IS NULL
 BEGIN
  INSERT dbo.m_code(category_id,code_value,code_name,display_order,is_active,valid_from,valid_to,remarks,is_protected,created_at,created_by,updated_at,updated_by,row_version)  VALUES(@category_id,@code_value,@code_name,@display_order,@is_active,@valid_from,@valid_to,@remarks,0,@now,@actor,@now,@actor,1);
  INSERT @changed VALUES ('is_protected'),('created_at'),('created_by'),('updated_at'),('updated_by'),('row_version');
 END
 ELSE
 BEGIN
  UPDATE dbo.m_code SET code_name=@code_name,display_order=@display_order,is_active=@is_active,valid_from=@valid_from,valid_to=@valid_to,remarks=@remarks,updated_at=@now,updated_by=@actor,row_version=row_version+1 WHERE category_id=@category_id AND code_value=@code_value AND row_version=@expected_version;
  IF @@ROWCOUNT<>1 THROW 51005,'E-STU-105',1;
  INSERT @changed VALUES('updated_at'),('updated_by'),('row_version');
  
 END;
 SET @target_key=@category_id+':'+@code_value;
 SET @after=COALESCE(@before,0)+1;
 DECLARE @changed_json nvarchar(max)=N'['+(SELECT STRING_AGG(CONVERT(nvarchar(max),N'"'+name+N'"'),N',') WITHIN GROUP(ORDER BY name) FROM @changed)+N']';
 INSERT dbo.t_operation_log(target_table,target_key,operation_type,before_version,after_version,changed_columns,executed_by,executed_at,correlation_id,operation_reason,duplicate_confirmed) VALUES('m_code',@target_key,@operation,@before,@after,@changed_json,@actor,@now,@request_id,@reason,0);
 SET @outcome='Saved';SET @code=CASE WHEN @same=1 THEN 'W-MST-001' ELSE 'I-STU-002' END;
Emit:
 SELECT @outcome outcome,@code code,@field field,@after row_version,@same same_name_warning,@target_key target_key,@request_id request_id,@max_length max_length;
END;
GO
GRANT EXECUTE ON OBJECT::student_api.save_code TO student_admin;
GO
