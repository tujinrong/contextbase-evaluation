"""Generate fixed administrator-only class/code procedures using local DB definitions."""
from pathlib import Path
import os
import re
BASE=Path(__file__).resolve().parent
OUTPUT=Path(os.environ.get("STUDENT_NATIVE_OUTPUT",str(BASE.parents[1]/"build/database/native"))).resolve()
if not OUTPUT.is_relative_to(BASE.parents[1]):raise ValueError("Output must remain within this method")
OUTPUT.mkdir(parents=True,exist_ok=True)
schema=(BASE.parent/'001_schema.sql').read_text(encoding='utf-8')
output=['-- VB.NET WinForms-only master maintenance. Caller commits; all operations use the student gate.']
for kind,keys in [('class',['school_year','grade_code','class_code','class_name','valid_from','valid_to','capacity','display_order','is_active','remarks']),('code',['category_id','code_value','code_name','display_order','is_active','valid_from','valid_to','remarks'])]:
 table='m_'+kind
 body=schema.split('CREATE TABLE dbo.'+table+' (',1)[1].split('\n);',1)[0]
 types={k:re.search(r'^  '+k+r' (nvarchar\(\d+\)|varchar\(\d+\)|smallint|int|date|bit) ',body,re.M).group(1) for k in keys}
 decl='\n'.join(" DECLARE @"+k+" "+types[k]+"=CASE WHEN @n.exist('/normalized/values/"+k+"[@null=\"true\"]')=1 THEN NULL ELSE @n.value('(/normalized/values/"+k+"/text())[1]','"+types[k]+"') END;" for k in keys)
 compare='\n'.join(" IF @before IS NULL OR EXISTS(SELECT "+("CONVERT(varbinary(max),@"+k+")" if 'char' in types[k] else '@'+k)+" EXCEPT SELECT "+("CONVERT(varbinary(max),"+k+")" if 'char' in types[k] else k)+" FROM #old) INSERT @changed VALUES('"+k+"');" for k in keys)
 extra_params='@target_id bigint=NULL,' if kind=='class' else ''
 old="class_id=@target_id" if kind=='class' else "category_id=@category_id AND code_value=@code_value"
 input_check=" OR (@target_id IS NULL AND @expected_version IS NOT NULL) OR (@target_id IS NOT NULL AND (@target_id<=0 OR @expected_version IS NULL))" if kind=='class' else ''
 class_rules=r'''
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
 '''
 code_rules=r'''
 IF @before IS NULL AND @expected_version IS NOT NULL BEGIN SET @outcome='NotFound';SET @code='E-STU-009';GOTO Emit;END;
 IF @before IS NOT NULL AND @expected_version IS NULL BEGIN SET @code='E-MST-002';GOTO Emit;END;
 IF @before IS NOT NULL AND @before<>@expected_version BEGIN SET @outcome='Conflict';SET @code='E-STU-105';GOTO Emit;END;
 IF NOT EXISTS(SELECT 1 FROM dbo.m_code_category WHERE category_id=@category_id) BEGIN SET @code='E-MST-001';GOTO Emit;END;
 IF EXISTS(SELECT 1 FROM dbo.m_code_category WHERE category_id=@category_id AND code_length<>LEN(@code_value)) BEGIN SET @code='E-STU-009';SET @field='code_value';GOTO Emit;END;
 IF @before IS NULL AND EXISTS(SELECT 1 FROM dbo.m_code_category WHERE category_id=@category_id AND allow_add=0) BEGIN SET @code='E-MST-003';GOTO Emit;END;
 IF EXISTS(SELECT 1 FROM #old WHERE is_protected=1 AND (@is_active=0 OR @valid_from>valid_from OR (@valid_to IS NOT NULL AND (valid_to IS NULL OR @valid_to<valid_to)))) BEGIN SET @code='E-MST-003';GOTO Emit;END;
 '''
 fixedcols=['grade_category'] if kind=='class' else ['is_protected']
 fixedvals=["'GRADE'"] if kind=='class' else ['0']
 cols=keys+fixedcols+['created_at','created_by','updated_at','updated_by','row_version']
 vals=['@'+k for k in keys]+fixedvals+['@now','@actor','@now','@actor','1']
 written = 'OUTPUT inserted.class_id INTO @written ' if kind=='class' else ''
 setkey = "SELECT @target_key=CONVERT(varchar(35),id) FROM @written;" if kind=='class' else "SET @target_key=@category_id+':'+@code_value;"
 update=','.join(k+'=@'+k for k in keys if kind=='class' and k not in {'school_year','class_code'} or kind=='code' and k not in {'category_id','code_value'})
 create_changed=",".join("('"+k+"')" for k in fixedcols+['created_at','created_by','updated_at','updated_by','row_version'])
 text=r'''
CREATE OR ALTER PROCEDURE student_api.save___KIND__ @raw nvarchar(max),__EXTRA__ @expected_version bigint=NULL,@request_id uniqueidentifier
AS
BEGIN
 SET NOCOUNT ON;SET XACT_ABORT ON;SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
 DECLARE @outcome varchar(32)='ValidationFailed',@code varchar(16)=NULL,@field varchar(64)='',@before bigint=NULL,@after bigint=NULL,@same bit=0,@target_key varchar(35)=NULL,@max_length int=NULL;
 DECLARE @actor nvarchar(128)=ORIGINAL_LOGIN(),@now datetimeoffset(7)=TODATETIMEOFFSET(SYSUTCDATETIME(),'+00:00'),@day date;
 SET @day=CONVERT(date,DATEADD(hour,9,@now));
 IF @@TRANCOUNT=0 OR XACT_STATE()<>1 OR @request_id IS NULL OR @expected_version<=0 __INPUT__ BEGIN SET @code='E-COM-003';GOTO Emit;END;
 IF @actor IS NULL OR LEN(@actor COLLATE Latin1_General_100_CS_AS_SC+N'#')-1>64 BEGIN SET @outcome='Forbidden';SET @code='E-COM-001';GOTO Emit;END;
 IF COALESCE(IS_MEMBER('student_admin'),0)<>1 BEGIN SET @outcome='Forbidden';SET @code='E-COM-002';GOTO Emit;END;
 DECLARE @n xml=TRY_CONVERT(xml,student_api.normalize___KIND__(@raw));
 IF @n IS NULL BEGIN SET @code='E-COM-003';GOTO Emit;END;
 IF @n.value('(/normalized/@ok)[1]','varchar(5)')<>'true' BEGIN SET @code=@n.value('(/normalized/@code)[1]','varchar(16)');SET @field=@n.value('(/normalized/@field)[1]','varchar(64)');SET @max_length=TRY_CONVERT(int,NULLIF(@n.value('(/normalized/@max)[1]','varchar(12)'),''));GOTO Emit;END;
 __DECLARE__
 DECLARE @reason nvarchar(120)=CASE WHEN @n.exist('/normalized/hints/reason[@null="true"]')=1 THEN NULL ELSE @n.value('(/normalized/hints/reason/text())[1]','nvarchar(120)') END,@lock int;
 EXEC @lock=sys.sp_getapplock @Resource=N'test-project1:student-write',@LockMode='Exclusive',@LockOwner='Transaction',@LockTimeout=5000,@DbPrincipal='public';
 IF @lock<0 BEGIN SET @outcome='Conflict';SET @code='E-STU-105';GOTO Emit;END;
 SELECT * INTO #old FROM dbo.__TABLE__ WITH(UPDLOCK) WHERE __OLD__;
 SELECT @before=row_version FROM #old;
 __RULES__
 DECLARE @changed TABLE(name varchar(64) PRIMARY KEY);
 __COMPARE__
 IF NOT EXISTS(SELECT 1 FROM @changed) BEGIN SET @outcome='NoChange';SET @after=@before;SET @code='I-STU-004';GOTO Emit;END;
 IF @before=9223372036854775807 BEGIN SET @outcome='Conflict';SET @code='E-STU-105';GOTO Emit;END;
 DECLARE @old_active bit=(SELECT is_active FROM #old),@operation varchar(11);
 SET @operation=CASE WHEN @before IS NULL THEN 'CREATE' WHEN @old_active=1 AND @is_active=0 THEN 'DISABLE' WHEN @old_active=0 AND @is_active=1 THEN 'ENABLE' ELSE 'UPDATE' END;
 DECLARE @written TABLE(id bigint);
 IF @before IS NULL
 BEGIN
  INSERT dbo.__TABLE__(__COLS__) __WRITTEN__ VALUES(__VALS__);
  INSERT @changed VALUES __CREATE_CHANGED__;
 END
 ELSE
 BEGIN
  UPDATE dbo.__TABLE__ SET __UPDATE__,updated_at=@now,updated_by=@actor,row_version=row_version+1 WHERE __OLD__ AND row_version=@expected_version;
  IF @@ROWCOUNT<>1 THROW 51005,'E-STU-105',1;
  INSERT @changed VALUES('updated_at'),('updated_by'),('row_version');
  __UPDATEKEY__
 END;
 __SETKEY__
 SET @after=COALESCE(@before,0)+1;
 DECLARE @changed_json nvarchar(max)=N'['+(SELECT STRING_AGG(CONVERT(nvarchar(max),N'"'+name+N'"'),N',') WITHIN GROUP(ORDER BY name) FROM @changed)+N']';
 INSERT dbo.t_operation_log(target_table,target_key,operation_type,before_version,after_version,changed_columns,executed_by,executed_at,correlation_id,operation_reason,duplicate_confirmed) VALUES('__TABLE__',@target_key,@operation,@before,@after,@changed_json,@actor,@now,@request_id,@reason,0);
 SET @outcome='Saved';SET @code=CASE WHEN @same=1 THEN 'W-MST-001' ELSE 'I-STU-002' END;
Emit:
 SELECT @outcome outcome,@code code,@field field,@after row_version,@same same_name_warning,@target_key target_key,@request_id request_id,@max_length max_length;
END;
GO
GRANT EXECUTE ON OBJECT::student_api.save___KIND__ TO student_admin;
GO
'''
 replacements={'__KIND__':kind,'__EXTRA__':extra_params,'__INPUT__':input_check,'__DECLARE__':decl,'__TABLE__':table,'__OLD__':old,'__RULES__':class_rules if kind=='class' else code_rules,'__COMPARE__':compare,'__COLS__':','.join(cols),'__VALS__':','.join(vals),'__WRITTEN__':written,'__CREATE_CHANGED__':create_changed,'__UPDATE__':update,'__SETKEY__':setkey,'__UPDATEKEY__':"INSERT @written VALUES(@target_id);" if kind=='class' else ''}
 for a,b in replacements.items():text=text.replace(a,b)
 output.append(text)
(OUTPUT/'020_master_api.sql').write_text('\n'.join(output),encoding='utf-8')
print('Generated fixed administrator class/code API.')
