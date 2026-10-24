"""Generate only ABI/COPY and the fixed SQL catalog from the same schema."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def put(name,text):
 p=ROOT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8',newline='\n')
fields=[('action',16),('studentId',19),('expectedVersion',19),('studentNo',15),('studentName',8),('studentNameKana',36),('birthEra',6),('birthYear',4),('birthMonth',2),('birthDay',2),('genderCode',1),('postalCode',10),('prefectureCode',2),('addressLine1',45),('addressLine2',45),('phoneNumber',20),('emailAddress',60),('admissionDate',10),('enrollmentStatusCode',2),('enrollmentEndDate',10),('classId',19),('emergencyContactName',8),('relationshipCode',2),('emergencyPhoneNumber',20),('remarks',120),('schoolYear',4),('gradeCode',2),('reason',60),('contextId',64),('contextRevision',19),('editorId',64),('confirmationToken',64),('tabId',64),('csrfToken',64),('confirmed',1),('deleteReason',60),('page',5),('pageSize',3),('sortKey',13),('sortDirection',4),('unassignedOnly',1),('status01',1),('status02',1),('status03',1),('status04',1),('admissionFrom',10),('admissionTo',10),('categoryId',24),('codeValue',10),('codeName',12),('validFrom',10),('validTo',10),('isActive',1),('displayOrder',10),('classCode',9),('className',18),('capacity',4),('initialDefaults',1),('flashId',64),('openStudentId',19),('pageTarget',5),('name',8),('statusCode',2),('navigation',4)]
put('bridge/fields.h','/* generated; do not edit */\nstatic const char *field_names[]={'+','.join(json.dumps(x[0]) for x in fields)+'};\nstatic const int field_limits[]={'+','.join(str(x[1]) for x in fields)+'};\n#define FIELD_COUNT '+str(len(fields))+'\n')
put('copy/ST-FIELDS.cpy','\n'.join(f'78 F-{name.upper()} VALUE {i}.' for i,(name,_) in enumerate(fields,1))+'\n')
put('bridge/student_abi.h',r'''#ifndef STUDENT_ABI_H
#define STUDENT_ABI_H
#include <stdint.h>
#include <stddef.h>
typedef struct {int32_t type_id;int16_t null_flag;char pad1[2];int32_t byte_length;char pad2[4];void *data_pointer;} ST_PARAM;
typedef struct {char command_id[12];int32_t parameter_count;ST_PARAM parameters[40];} ST_DB_REQUEST;
typedef struct {char sqlstate[5];char pad1[3];int32_t native_error_code;char pad2[4];int64_t affected_rows;void *cursor_handle;int32_t error_class;char pad3[4];} ST_DB_RESULT;
typedef struct {int32_t length;int16_t null_flag;char pad[2];char data[1024];} ST_VALUE;
_Static_assert(sizeof(void*)==8,"64bit Linux ABI required");
_Static_assert(sizeof(ST_PARAM)==24 && offsetof(ST_PARAM,data_pointer)==16,"parameter ABI");
_Static_assert(sizeof(ST_DB_REQUEST)==976,"request ABI");
_Static_assert(sizeof(ST_DB_RESULT)==40 && offsetof(ST_DB_RESULT,cursor_handle)==24,"result ABI");
_Static_assert(sizeof(ST_VALUE)==1032,"value ABI");
int32_t STDBOP(void*,const ST_DB_REQUEST*,ST_DB_RESULT*);
#endif
''')
put('copy/ST-DB-REQUEST.cpy',r'''01 ST-DB-REQUEST.
  05 DB-COMMAND PIC X(12).
  05 DB-PARAMETER-COUNT PIC S9(9) COMP-5.
  05 DB-PARAMETER OCCURS 40 TIMES.
    10 DB-TYPE PIC S9(9) COMP-5.
    10 DB-NULL PIC S9(4) COMP-5.
    10 FILLER PIC X(2).
    10 DB-LENGTH PIC S9(9) COMP-5.
    10 FILLER PIC X(4).
    10 DB-DATA USAGE POINTER.
''')
put('copy/ST-DB-RESULT.cpy',r'''01 ST-DB-RESULT.
  05 DB-SQLSTATE PIC X(5).
  05 FILLER PIC X(3).
  05 DB-NATIVE PIC S9(9) COMP-5.
  05 FILLER PIC X(4).
  05 DB-AFFECTED PIC S9(18) COMP-5.
  05 DB-CURSOR USAGE POINTER.
  05 DB-ERROR PIC S9(9) COMP-5.
  05 FILLER PIC X(4).
''')
put('copy/ST-REQUEST.cpy','01 ST-RAW.\n  05 R-VALUE OCCURS 64 TIMES.\n    10 R-LENGTH PIC S9(9) COMP-5.\n    10 R-NULL PIC S9(4) COMP-5.\n    10 FILLER PIC X(2).\n    10 R-DATA PIC X(1024).\n')
put('copy/ST-STUDENT.cpy','01 ST-NORMAL.\n  05 N-VALUE OCCURS 28 TIMES.\n    10 N-LENGTH PIC S9(9) COMP-5.\n    10 N-NULL PIC S9(4) COMP-5.\n    10 FILLER PIC X(2).\n    10 N-DATA PIC X(1024).\n')
put('copy/ST-SEARCH.cpy','01 ST-SEARCH-STATE.\n  05 SEARCH-SCHEMA PIC X(16).\n  05 SEARCH-EXECUTED PIC S9(9) COMP-5.\n  05 SEARCH-TAB PIC X(64).\n  05 SEARCH-RAW PIC X(66048).\n')
put('copy/ST-RESULT.cpy','01 ST-ROWS.\n  05 ST-ROW OCCURS 100 TIMES.\n    10 ROW-VALUE OCCURS 13 TIMES.\n      15 ROW-LENGTH PIC S9(9) COMP-5.\n      15 ROW-NULL PIC S9(4) COMP-5.\n      15 FILLER PIC X(2).\n      15 ROW-DATA PIC X(1024).\n')
put('copy/ST-DATE-INPUT.cpy','01 ST-DATE-INPUT.\n  05 DATE-ERA PIC X(24).\n  05 DATE-YEAR PIC X(16).\n  05 DATE-MONTH PIC X(8).\n  05 DATE-DAY PIC X(8).\n  05 DATE-ISO PIC X(10).\n')
sql={}
def add(command,text):sql[command]=text
add('CLOCK',"SELECT CONVERT(char(10),SWITCHOFFSET(SYSDATETIMEOFFSET(),'+09:00'),23),CONVERT(varchar(27),CAST(SWITCHOFFSET(SYSDATETIMEOFFSET(),'+00:00') AS datetime2(7)),126)+'Z',CONVERT(varchar(36),NEWID()),snapshot_isolation_state FROM sys.databases WHERE database_id=DB_ID()")
add('AUTH-ADMIN',"SELECT CASE WHEN IS_ROLEMEMBER('student_admin')=1 THEN 1 ELSE 0 END,ORIGINAL_LOGIN()")
add('INIT-CHECK',"SELECT (SELECT COUNT_BIG(*) FROM dbo.m_code_category WHERE category_id IN ('GENDER','ENROLLMENT_STATUS','PREFECTURE','RELATIONSHIP','GRADE')),(SELECT COUNT_BIG(*) FROM dbo.m_code WHERE category_id='GENDER' AND code_value='0' OR category_id='GRADE' AND code_value='00' OR category_id='ENROLLMENT_STATUS' AND code_value IN ('01','02','03','04'))")
add('ST-LOAD',"SELECT student_no,student_name,student_name_kana,CONVERT(char(10),birth_date,23),gender_code,postal_code,prefecture_code,address_line1,address_line2,phone_number,email_address,CONVERT(char(10),admission_date,23),enrollment_status_code,CONVERT(char(10),enrollment_end_date,23),CONVERT(varchar(19),class_id),emergency_contact_name,relationship_code,emergency_phone_number,remarks,name_key,kana_key,CONVERT(varchar(19),row_version),CONVERT(varchar(19),SWITCHOFFSET(updated_at,'+09:00'),120),updated_by,relationship_category FROM dbo.m_student WHERE student_id=? AND is_deleted=0")
add('ST-UQ','SELECT COUNT_BIG(*) FROM dbo.m_student WHERE student_no=? AND (? IS NULL OR student_id<>?)')
add('ST-CODE','SELECT c.is_active,k.is_active,CONVERT(char(10),c.valid_from,23),CONVERT(char(10),c.valid_to,23) FROM dbo.m_code c JOIN dbo.m_code_category k ON c.category_id=k.category_id WHERE c.category_id=? AND c.code_value=?')
add('ST-CLASS','SELECT school_year,grade_code,CONVERT(char(10),valid_from,23),CONVERT(char(10),valid_to,23),is_active,capacity FROM dbo.m_class WHERE class_id=?')
add('ST-CAP',"SELECT COUNT_BIG(*) FROM dbo.m_student WHERE class_id=? AND is_deleted=0 AND enrollment_status_code IN ('01','02') AND (? IS NULL OR student_id<>?)")
add('ST-YEAR','SELECT COUNT_BIG(*) FROM dbo.m_class WHERE school_year=?')
add('CODE-LIST',"SELECT c.category_id,c.code_value,c.code_name,c.is_active,k.is_active,CONVERT(char(10),c.valid_from,23),CONVERT(char(10),c.valid_to,23) FROM dbo.m_code c JOIN dbo.m_code_category k ON k.category_id=c.category_id ORDER BY c.category_id,c.display_order,c.code_value")
add('CLASS-LIST',"SELECT c.class_id,c.school_year,c.grade_code,c.class_code,c.class_name,CONVERT(char(10),c.valid_from,23),CONVERT(char(10),c.valid_to,23),c.is_active,c.capacity,g.code_name FROM dbo.m_class c LEFT JOIN dbo.m_code g ON g.category_id=c.grade_category AND g.code_value=c.grade_code ORDER BY school_year DESC,g.display_order,c.display_order,class_code,class_id")
add('CLASS-EDIT',sql['CLASS-LIST'].replace(' FROM dbo.m_class c',",(SELECT COUNT_BIG(*) FROM dbo.m_student s WHERE s.class_id=c.class_id AND s.is_deleted=0 AND s.enrollment_status_code IN ('01','02')) FROM dbo.m_class c"))
joins=" FROM dbo.m_student s LEFT JOIN dbo.m_class c ON c.class_id=s.class_id LEFT JOIN dbo.m_code g ON g.category_id=c.grade_category AND g.code_value=c.grade_code LEFT JOIN dbo.m_code e ON e.category_id=s.enrollment_category AND e.code_value=s.enrollment_status_code LEFT JOIN dbo.m_code p ON p.category_id=s.prefecture_category AND p.code_value=s.prefecture_code"
row="SELECT CONVERT(varchar(19),s.student_id),s.student_no,s.student_name,s.student_name_kana,CONVERT(char(10),s.birth_date,23),c.school_year,COALESCE(g.code_name,N'不整合'),c.class_code,c.class_name,COALESCE(e.code_name,N'不整合')"
add('ST-DUP',"DECLARE @id bigint=?,@birth date=?,@name nvarchar(320)=?,@kana nvarchar(36)=?; SELECT s.student_id,s.row_version,s.student_no,s.student_name,CONVERT(char(10),s.birth_date,23),c.class_name FROM dbo.m_student s LEFT JOIN dbo.m_class c ON c.class_id=s.class_id WHERE s.is_deleted=0 AND (@id IS NULL OR s.student_id<>@id) AND s.birth_date=@birth AND (s.name_key=@name OR s.kana_key=@kana) ORDER BY s.student_id")
params=[('no','varchar(31)'),('name','nvarchar(642)'),('class','bigint'),('s1','varchar(2)'),('s2','varchar(2)'),('s3','varchar(2)'),('s4','varchar(2)')]
decl='DECLARE '+','.join('@'+n+' '+typ+'=?' for n,typ in params)+'; '
where=" WHERE s.is_deleted=0 AND (@no IS NULL OR s.student_no LIKE @no ESCAPE '!') AND (@name IS NULL OR s.name_key LIKE @name ESCAPE '!') AND (@class IS NULL OR s.class_id=@class) AND ((@s1 IS NULL AND @s2 IS NULL AND @s3 IS NULL AND @s4 IS NULL) OR s.enrollment_status_code IN (@s1,@s2,@s3,@s4))"
add('ST-COUNT',decl+'SELECT COUNT_BIG(*) FROM (SELECT TOP (10001) s.student_id FROM dbo.m_student s LEFT JOIN dbo.m_class c ON c.class_id=s.class_id'+where+') limited')
for i,(key,col) in enumerate([('studentNo','s.student_no'),('name','s.name_key'),('admissionDate','s.admission_date'),('updatedAt','s.updated_at')],1):
 for direction,code in [('ASC','A'),('DESC','D')]:add(f'ST-LIST-{i}{code}',decl+'DECLARE @offset int=?,@size int=?; '+row+joins+where+f' ORDER BY {col} {direction},s.student_id ASC OFFSET @offset ROWS FETCH NEXT @size ROWS ONLY')
columns=[('student_no','varchar(15)'),('student_name','nvarchar(16)'),('student_name_kana','nvarchar(36)'),('birth_date','date'),('gender_code','varchar(1)'),('postal_code','varchar(7)'),('prefecture_code','varchar(2)'),('address_line1','nvarchar(90)'),('address_line2','nvarchar(90)'),('phone_number','varchar(16)'),('email_address','varchar(60)'),('admission_date','date'),('enrollment_status_code','varchar(2)'),('enrollment_end_date','date'),('class_id','bigint'),('emergency_contact_name','nvarchar(16)'),('relationship_code','varchar(2)'),('emergency_phone_number','varchar(16)'),('remarks','nvarchar(240)'),('name_key','nvarchar(320)'),('kana_key','nvarchar(36)'),('relationship_category','varchar(24)')]
base='DECLARE '+','.join('@'+n+' '+t+'=?' for n,t in columns)+',@actor nvarchar(128)=?,@now datetimeoffset(7)=?; DECLARE @changed TABLE(id bigint); '
add('ST-INSERT',base+'INSERT INTO dbo.m_student ('+','.join(n for n,t in columns)+',gender_category,prefecture_category,enrollment_category,is_deleted,created_at,created_by,updated_at,updated_by,row_version) OUTPUT INSERTED.student_id INTO @changed VALUES ('+','.join('@'+n for n,t in columns)+",'GENDER','PREFECTURE','ENROLLMENT_STATUS',0,@now,@actor,@now,@actor,1); SELECT id FROM @changed")
add('ST-UPDATE',base+'DECLARE @id bigint=?,@version bigint=?; UPDATE dbo.m_student SET '+','.join(n+'=@'+n for n,t in columns if n!='student_no')+',updated_at=@now,updated_by=@actor,row_version=row_version+1 OUTPUT INSERTED.student_id INTO @changed WHERE student_id=@id AND row_version=@version AND is_deleted=0; SELECT id FROM @changed')
add('ST-DELETE',"DECLARE @actor nvarchar(128)=?,@now datetimeoffset(7)=?,@reason nvarchar(120)=?,@id bigint=?,@version bigint=?; DECLARE @changed TABLE(id bigint); UPDATE dbo.m_student SET is_deleted=1,deleted_at=@now,deleted_by=@actor,delete_reason=@reason,updated_at=@now,updated_by=@actor,row_version=row_version+1 OUTPUT INSERTED.student_id INTO @changed WHERE student_id=@id AND row_version=@version AND is_deleted=0; SELECT id FROM @changed")
add('LOG-INSERT',"INSERT INTO dbo.t_operation_log(target_table,target_key,operation_type,before_version,after_version,changed_columns,executed_by,executed_at,correlation_id,operation_reason,duplicate_confirmed) VALUES ('m_student',?,?,?,?,?,?,?,CONVERT(uniqueidentifier,?),?,?)")
# Only fixed statements enter the bridge; user values are always parameter data.
for command,text in sql.items():put('sql/'+command+'.sql',text+';\n')
put('bridge/sql_catalog.h','/* generated from sql/*.sql */\nstatic const struct {const char *id;const char *sql;} catalog[]={\n'+',\n'.join('{'+json.dumps(k)+','+json.dumps(v,ensure_ascii=False)+'}' for k,v in sql.items())+'\n};\n')
put('tools/abi-schema.json',json.dumps({'profile':'linux-x86_64-little-endian','pointer':8,'ST_PARAM':24,'ST_DB_REQUEST':976,'ST_DB_RESULT':40,'ST_VALUE':1032,'fields':fields},ensure_ascii=False,indent=2)+'\n')
print(f'Generated ABI/COPY, {len(fields)} fields, {len(sql)} fixed SQL statements.')
