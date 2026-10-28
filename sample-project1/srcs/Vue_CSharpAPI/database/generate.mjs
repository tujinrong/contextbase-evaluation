// Regenerate this method's SQL sources from its current, independent specification.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
const output=path.dirname(fileURLToPath(import.meta.url));
const project=path.resolve(output,'..');
const specRoot=path.resolve(project,'../../spec',path.basename(project));
const inputs=[];
function readInput(target) {
  const data=fs.readFileSync(target);const text=data.toString('utf8');
  const meta=JSON.parse(text.match(/<!-- spec-meta: (.*?) -->/)[1]);
  inputs.push({file:path.relative(specRoot,target).split(path.sep).join('/'),documentId:meta.documentId,version:meta.version,sha256:crypto.createHash('sha256').update(data).digest('hex')});
  return text;
}
const spec=path.join(specRoot,'DB定義/SQLServer/テーブル');
const tables=fs.readdirSync(spec).filter(name=>name.endsWith('.md')).map(name=>{
  const text=readInput(path.join(spec,name));
  const meta=JSON.parse(text.match(/<!-- spec-meta: (.*?) -->/)[1]);
  const rows=text.split('## 項目詳細')[1].split(/\r?\n/).filter(line=>/^\| \d+ \|/.test(line)).map(line=>line.split('|').slice(1,-1).map(cell=>cell.trim()));
  return {name:meta.table.physicalName,pk:meta.table.primaryKey,rows};
});
const tableInputHash=crypto.createHash('sha256').update(JSON.stringify(inputs)).digest('hex');
const sql=[`-- Generated from the current method SQLServer table definitions; input SHA256 ${tableInputHash}.`,"-- Apply to an EMPTY selected evaluation database only. No migration/drop is performed.","SET XACT_ABORT ON;", "GO", "ALTER DATABASE CURRENT SET ALLOW_SNAPSHOT_ISOLATION ON;", "GO"];
for(const table of tables) {
  sql.push(`CREATE TABLE dbo.${table.name} (`);
  const fields=table.rows.map(row=>{
    const name=row[2],type=row[5];
    if(!/^[a-z][a-z0-9_]*$/.test(name)||!/^((n?varchar|binary|varbinary)\((\d+|max)\)|datetimeoffset\(7\)|bigint|smallint|int|bit|date|uniqueidentifier)$/.test(type)) throw new Error(`Invalid input identifier/type: ${name} ${type}`);
    const collate=/^(n?varchar)/.test(type)?` COLLATE ${name.endsWith('_key')||type.startsWith('varchar')?'Latin1_General_100_BIN2':'Latin1_General_100_CS_AS_SC'}`:'';
    const identity=row[7]==='自動採番'?' IDENTITY(1,1)':'';
    const initial=/^[01]$/.test(row[7])?` CONSTRAINT df_${table.name}_${name} DEFAULT (${row[7]})`:'';
    return `  ${name} ${type}${collate}${identity} ${row[4]==='〇'?'NOT NULL':'NULL'}${initial}`;
  });
  fields.push(`  CONSTRAINT pk_${table.name} PRIMARY KEY (${table.pk.join(',')})`);
  for(const row of table.rows) {
    const name=row[2];
    if(/^nvarchar\(\d+\)$/.test(row[5])&&/^\d+$/.test(row[6])) fields.push(`  CONSTRAINT ck_${table.name}_${name}_scalar CHECK (${name} IS NULL OR LEN(CONVERT(nvarchar(max),${name}) COLLATE Latin1_General_100_CS_AS_SC+N'#')-1<=${row[6]})`);
    if(row[5]==='datetimeoffset(7)') fields.push(`  CONSTRAINT ck_${table.name}_${name}_utc CHECK (${name} IS NULL OR DATEPART(TZOFFSET,${name})=0)`);
    if(name==='row_version'||name==='revision') fields.push(`  CONSTRAINT ck_${table.name}_${name} CHECK (${name}>0)`);
  }
  sql.push(fields.join(',\n'),');','GO');
}
sql.push(`
ALTER TABLE dbo.m_student ADD CONSTRAINT uq_student_no UNIQUE(student_no);
ALTER TABLE dbo.m_class ADD CONSTRAINT uq_class_year_code UNIQUE(school_year,class_code);
ALTER TABLE dbo.m_code ADD CONSTRAINT fk_code_category FOREIGN KEY(category_id) REFERENCES dbo.m_code_category(category_id);
ALTER TABLE dbo.m_class ADD CONSTRAINT fk_class_grade FOREIGN KEY(grade_category,grade_code) REFERENCES dbo.m_code(category_id,code_value);
ALTER TABLE dbo.m_student ADD CONSTRAINT fk_student_class FOREIGN KEY(class_id) REFERENCES dbo.m_class(class_id);
ALTER TABLE dbo.m_student ADD CONSTRAINT fk_student_gender FOREIGN KEY(gender_category,gender_code) REFERENCES dbo.m_code(category_id,code_value);
ALTER TABLE dbo.m_student ADD CONSTRAINT fk_student_prefecture FOREIGN KEY(prefecture_category,prefecture_code) REFERENCES dbo.m_code(category_id,code_value);
ALTER TABLE dbo.m_student ADD CONSTRAINT fk_student_enrollment FOREIGN KEY(enrollment_category,enrollment_status_code) REFERENCES dbo.m_code(category_id,code_value);
ALTER TABLE dbo.m_student ADD CONSTRAINT fk_student_relationship FOREIGN KEY(relationship_category,relationship_code) REFERENCES dbo.m_code(category_id,code_value);
ALTER TABLE dbo.m_student ADD CONSTRAINT ck_student_category CHECK(gender_category='GENDER' AND prefecture_category='PREFECTURE' AND enrollment_category='ENROLLMENT_STATUS');
ALTER TABLE dbo.m_class ADD CONSTRAINT ck_class_category CHECK(grade_category='GRADE');
ALTER TABLE dbo.m_student ADD CONSTRAINT ck_student_dates CHECK(birth_date>='19000101' AND birth_date<=admission_date AND admission_date>='19000101' AND ((enrollment_status_code IN ('01','02') AND enrollment_end_date IS NULL AND class_id IS NOT NULL) OR (enrollment_status_code IN ('03','04') AND enrollment_end_date IS NOT NULL AND enrollment_end_date>=admission_date)));
ALTER TABLE dbo.m_student ADD CONSTRAINT ck_student_contact CHECK((phone_number IS NOT NULL OR email_address IS NOT NULL OR emergency_phone_number IS NOT NULL) AND ((emergency_contact_name IS NULL AND relationship_category IS NULL AND relationship_code IS NULL AND emergency_phone_number IS NULL) OR (emergency_contact_name IS NOT NULL AND relationship_category IS NOT NULL AND relationship_code IS NOT NULL AND emergency_phone_number IS NOT NULL AND relationship_category='RELATIONSHIP')));
ALTER TABLE dbo.m_student ADD CONSTRAINT ck_student_deleted CHECK((is_deleted=0 AND deleted_at IS NULL AND deleted_by IS NULL AND delete_reason IS NULL) OR (is_deleted=1 AND deleted_at IS NOT NULL AND deleted_by IS NOT NULL AND delete_reason IS NOT NULL));
ALTER TABLE dbo.m_class ADD CONSTRAINT ck_class_limits CHECK(school_year BETWEEN 1900 AND 9998 AND valid_from<=valid_to AND valid_from>=DATEFROMPARTS(school_year,4,1) AND valid_to<=DATEFROMPARTS(school_year+1,3,31) AND (capacity IS NULL OR capacity BETWEEN 1 AND 9999) AND display_order>=0);
ALTER TABLE dbo.m_code_category ADD CONSTRAINT ck_category_length CHECK(code_length BETWEEN 1 AND 10);
ALTER TABLE dbo.m_code ADD CONSTRAINT ck_code_limits CHECK(code_value<>'' AND code_value NOT LIKE '%[^0-9]%' COLLATE Latin1_General_100_BIN2 AND valid_from>='19000101' AND (valid_to IS NULL OR valid_to>=valid_from) AND display_order>=0);
ALTER TABLE dbo.t_operation_log ADD CONSTRAINT ck_audit_json CHECK(ISJSON(changed_columns)=1 AND LEFT(LTRIM(changed_columns),1)='[');
ALTER TABLE dbo.t_operation_log ADD CONSTRAINT ck_audit_operation CHECK(operation_type IN ('CREATE','UPDATE','DELETE','DISABLE','ENABLE'));
CREATE INDEX ix_student_birth ON dbo.m_student(birth_date) WHERE is_deleted=0;
CREATE INDEX ix_student_class_status ON dbo.m_student(class_id,enrollment_status_code) WHERE is_deleted=0;
CREATE INDEX ix_student_admission ON dbo.m_student(admission_date) WHERE is_deleted=0;
CREATE INDEX ix_student_updated ON dbo.m_student(updated_at) WHERE is_deleted=0;
CREATE INDEX ix_student_phone ON dbo.m_student(phone_number) WHERE is_deleted=0;
CREATE INDEX ix_student_emergency_phone ON dbo.m_student(emergency_phone_number) WHERE is_deleted=0;
CREATE INDEX ix_operation_target ON dbo.t_operation_log(target_table,target_key,executed_at);
CREATE ROLE student_viewer;
CREATE ROLE student_staff;
CREATE ROLE student_admin;
-- No login/user/password or rights escalation is performed automatically.
-- Native production EXEC-only grants require the reviewed student_api entrance implementation.
GO
`);
fs.writeFileSync(path.join(output,'001_schema.sql'),sql.join('\n'));
const mappings={'性別':'GENDER','在籍区分':'ENROLLMENT_STATUS','都道府県':'PREFECTURE','緊急連絡先続柄':'RELATIONSHIP','学年':'GRADE'};
const text=readInput(path.join(specRoot,'共通/10_業務コード定義.md'));
const codes=text.split('## 項目一覧')[1].split('## 分類一覧')[0].split(/\r?\n/).filter(line=>/^\| (性別-|在籍区分-|都道府県-|緊急連絡先続柄-|学年-)/.test(line)).map(line=>line.split('|').slice(1,-1).map(cell=>cell.trim()));
if(codes.length!==70) throw new Error(`Expected 70 business codes, got ${codes.length}`);
const quote=value=>"N'"+value.replaceAll("'","''")+"'";
const categories=Object.entries(mappings).map(([name,id])=>`('${id}',${quote(name)},${id==='GENDER'?1:2},${id==='GRADE'||id==='RELATIONSHIP'?1:0})`).join(',\n');
const values=codes.map(row=>`('${mappings[row[1]]}','${row[2]}',${quote(row[3])},${Number(row[4])},${row[5]==='対象'?1:0})`).join(',\n');
fs.writeFileSync(path.join(output,'002_seed.sql'),`-- COM-STU-010: five categories / 70 codes, no invented class/student data.
SET XACT_ABORT ON;
BEGIN TRANSACTION;
DECLARE @lock int;
EXEC @lock=sys.sp_getapplock @Resource=N'test-project1:student-write',@LockMode='Exclusive',@LockOwner='Transaction',@LockTimeout=5000,@DbPrincipal='public';
IF @lock<0 BEGIN ROLLBACK; THROW 51001,N'保存用ロック取得失敗',1; END;
DECLARE @now datetimeoffset(7)=TODATETIMEOFFSET(SYSUTCDATETIME(),'+00:00'),@actor nvarchar(128)=ORIGINAL_LOGIN();
DECLARE @categories TABLE(category_id varchar(24),category_name nvarchar(24),code_length smallint,allow_add bit);
INSERT @categories VALUES ${categories};
DECLARE @codes TABLE(category_id varchar(24),code_value varchar(10),code_name nvarchar(24),display_order int,is_protected bit);
INSERT @codes VALUES ${values};
IF EXISTS(SELECT 1 FROM @categories i JOIN dbo.m_code_category c ON c.category_id=i.category_id WHERE c.category_name<>i.category_name OR c.code_length<>i.code_length OR c.allow_add<>i.allow_add OR c.is_active<>1)
 OR EXISTS(SELECT 1 FROM @codes i JOIN dbo.m_code c ON c.category_id=i.category_id AND c.code_value=i.code_value WHERE c.code_name<>i.code_name OR c.display_order<>i.display_order OR c.is_protected<>i.is_protected OR c.is_active<>1 OR c.valid_from<>'19000101' OR c.valid_to IS NOT NULL)
 BEGIN ROLLBACK; THROW 51002,N'初期コードに差分があります。既存値を上書きせず確認してください。',1; END;
INSERT dbo.m_code_category(category_id,category_name,code_length,allow_add,is_active,remarks,created_at,created_by,updated_at,updated_by,row_version)
 SELECT i.category_id,i.category_name,i.code_length,i.allow_add,1,NULL,@now,@actor,@now,@actor,1 FROM @categories i WHERE NOT EXISTS(SELECT 1 FROM dbo.m_code_category c WHERE c.category_id=i.category_id);
INSERT dbo.m_code(category_id,code_value,code_name,display_order,is_active,valid_from,valid_to,is_protected,remarks,created_at,created_by,updated_at,updated_by,row_version)
 SELECT i.category_id,i.code_value,i.code_name,i.display_order,1,'19000101',NULL,i.is_protected,NULL,@now,@actor,@now,@actor,1 FROM @codes i WHERE NOT EXISTS(SELECT 1 FROM dbo.m_code c WHERE c.category_id=i.category_id AND c.code_value=i.code_value);
COMMIT;
GO
`);
const record={profileId:path.basename(project),specRoot:path.relative(path.resolve(project,'../../..'),specRoot).split(path.sep).join('/'),tables:tables.length,businessColumns:tables.filter(table=>table.name!=='t_confirmation'&&table.name!=='t_runtime_state').reduce((count,table)=>count+table.rows.length,0),categories:5,codes:codes.length,executedDatabase:false,inputs,outputs:['001_schema.sql','002_seed.sql'].map(file=>({file:'database/'+file,sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(output,file))).digest('hex')}))};
const generation=path.join(project,'build/generation');fs.mkdirSync(generation,{recursive:true});
fs.writeFileSync(path.join(generation,'database-inputs.json'),JSON.stringify(record,null,2)+'\n');
console.log(JSON.stringify(record));
