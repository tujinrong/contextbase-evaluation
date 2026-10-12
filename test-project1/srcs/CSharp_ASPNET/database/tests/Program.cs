using System.Data;
using System.Text.Json;
using System.Text.RegularExpressions;
using Microsoft.Data.SqlClient;
using StudentManagement.Core;

// Optional real SQL Server 2022 tests. Never selects, creates or drops a database.
// The caller must supply an EMPTY, dedicated contextbase_test_* database with
// encryption/certificate validation configured and schema creation permission.
var configured=Environment.GetEnvironmentVariable("STUDENT_TEST_DB_CONNECTION");
if(string.IsNullOrWhiteSpace(configured)) {Console.WriteLine("SKIP SQL Server integration: STUDENT_TEST_DB_CONNECTION is absent; no database opened.");return;}
var settings=new SqlConnectionStringBuilder(configured){Encrypt=SqlConnectionEncryptOption.Mandatory,TrustServerCertificate=false};
if(!Regex.IsMatch(settings.InitialCatalog,"^contextbase_test_[A-Za-z0-9_]+$",RegexOptions.CultureInvariant))throw new InvalidOperationException("Only an explicitly named contextbase_test_* fixture is permitted.");
await using var db=new SqlConnection(settings.ConnectionString);await db.OpenAsync();
async Task<object?> Scalar(string sql){await using var q=new SqlCommand(sql,db);return await q.ExecuteScalarAsync();}
async Task Execute(string sql){await using var q=new SqlCommand(sql,db){CommandTimeout=30};await q.ExecuteNonQueryAsync();}
if(Convert.ToInt32(await Scalar("SELECT SERVERPROPERTY('ProductMajorVersion')"))!=16)throw new InvalidOperationException("SQL Server 2022 (major 16) is required.");
if(Convert.ToInt32(await Scalar("SELECT COUNT(*) FROM sys.objects WHERE is_ms_shipped=0"))!=0)throw new InvalidOperationException("Fixture must be empty; existing objects are never overwritten.");
var sqlDirectory=FindSqlDirectory();
foreach(var filename in new[]{"001_schema.sql","002_seed.sql"})foreach(var batch in Regex.Split(await File.ReadAllTextAsync(Path.Combine(sqlDirectory,filename)),@"(?m)^GO\s*\r?$"))if(!string.IsNullOrWhiteSpace(batch))await Execute(batch);
int checks=0;
void Check(bool condition,string name){if(!condition)throw new Exception("FAILED: "+name);checks++;}
async Task Reject(string sql,string name){try{await Execute(sql);}catch(SqlException e)when(e.Number==547){checks++;return;}throw new Exception("FAILED constraint rejection: "+name);}
Check(Convert.ToInt32(await Scalar("SELECT COUNT(*) FROM dbo.m_code_category"))==5,"five categories");
Check(Convert.ToInt32(await Scalar("SELECT COUNT(*) FROM dbo.m_code"))==70,"70 codes");
Check(Convert.ToInt32(await Scalar("SELECT COUNT(*) FROM dbo.m_class"))==0,"no invented classes");
Check(Convert.ToInt32(await Scalar("SELECT COUNT(*) FROM dbo.m_student"))==0,"no invented students");
var user=new CurrentUser("integration-server",Guid.NewGuid().ToString(),Role.Administrator);
var service=new SqlServerStudentService(settings.ConnectionString,()=>user,webTokens:true);
StudentDraft Draft(string number)=>new(){StudentNo=number,StudentName="試験 太郎",StudentNameKana="シケン タロウ",BirthDateInput=new("HEISEI","20","05","15"),GenderCode="0",PostalCode="1000001",PrefectureCode="13",AddressLine1="試験町1",PhoneNumber="0312345678",AdmissionDate="2026-04-01",EnrollmentStatusCode="03",EnrollmentEndDate="2026-10-10"};
var draft=Draft("T-0001");var saved=await service.SaveAsync(new(draft));Check(saved.Outcome==Outcome.Saved,"R74-01 valid empty emergency create");
var id=saved.StudentId!.Value;
Check(Convert.ToInt32(await Scalar($"SELECT COUNT(*) FROM dbo.m_student WHERE student_id={id} AND emergency_contact_name IS NULL AND relationship_category IS NULL AND relationship_code IS NULL AND emergency_phone_number IS NULL"))==1,"R74-01 four null columns");
Check((string)(await Scalar("SELECT TOP(1) operation_type FROM dbo.t_operation_log ORDER BY log_id DESC"))! =="CREATE","R74-01 CREATE audit");
var relation=(string)(await Scalar("SELECT TOP(1) code_value FROM dbo.m_code WHERE category_id='RELATIONSHIP' ORDER BY code_value"))!;
for(var mask=0;mask<16;mask++){
 var name=(mask&1)==0?"NULL":"N'試験 花子'";var category=(mask&2)==0?"NULL":"'RELATIONSHIP'";var value=(mask&4)==0?"NULL":"'"+relation+"'";var phone=(mask&8)==0?"NULL":"'0312345678'";
 var update=$"UPDATE dbo.m_student SET emergency_contact_name={name},relationship_category={category},relationship_code={value},emergency_phone_number={phone} WHERE student_id={id}";
 if(mask is 0 or 15){await Execute(update);checks++;}else await Reject(update,"R74-04 mask "+mask);
}
var missing=(string)(await Scalar("SELECT TOP(1) RIGHT('0'+CONVERT(varchar(2),n),2) FROM (VALUES(90),(91),(92),(93),(94),(95),(96),(97),(98),(99)) v(n) WHERE NOT EXISTS(SELECT 1 FROM dbo.m_code c WHERE c.category_id='RELATIONSHIP' AND c.code_value=RIGHT('0'+CONVERT(varchar(2),v.n),2)) ORDER BY n"))!;
await Reject($"UPDATE dbo.m_student SET relationship_code='{missing}' WHERE student_id={id}","R74-06 nonexistent code");
await Reject($"UPDATE dbo.m_student SET relationship_category='GENDER',relationship_code='0' WHERE student_id={id}","R74-07 other category");
await Reject($"DELETE dbo.m_code WHERE category_id='RELATIONSHIP' AND code_value='{relation}'","R74-08 parent deletion");
await Reject($"UPDATE dbo.m_code SET code_value='{missing}' WHERE category_id='RELATIONSHIP' AND code_value='{relation}'","R74-08 parent key update");
var loaded=await service.GetAsync(id);Check(loaded!.Draft.RelationshipCode==relation,"R74-02 populated emergency reload");
loaded.Draft.EmergencyContactName=null;loaded.Draft.RelationshipCode=null;loaded.Draft.EmergencyPhoneNumber=null;
var cleared=await service.SaveAsync(new(loaded.Draft,id,loaded.RowVersion));Check(cleared.Outcome==Outcome.Saved&&cleared.RowVersion==2,"R74-03 clear increments version");
using(var changed=JsonDocument.Parse((string)(await Scalar("SELECT TOP(1) changed_columns FROM dbo.t_operation_log ORDER BY log_id DESC"))!))Check(changed.RootElement.EnumerateArray().Any(x=>x.GetString()=="relationship_category"),"R74-03 derived category audited");
var auditCount=Convert.ToInt32(await Scalar("SELECT COUNT(*) FROM dbo.t_operation_log"));
Check((await service.SaveAsync(new(loaded.Draft,id,2))).Outcome==Outcome.NoChange,"R74-12 no change");
Check(Convert.ToInt32(await Scalar("SELECT COUNT(*) FROM dbo.t_operation_log"))==auditCount,"no change has no audit");
await Execute("CREATE TRIGGER dbo.fixture_fail_audit ON dbo.t_operation_log AFTER INSERT AS THROW 51100,N'fixture audit failure',1;");
try{
 var failing=Draft("T-0001");failing.Remarks="監査取消試験";var failed=await service.SaveAsync(new(failing,id,2));Check(failed.Outcome==Outcome.SystemError,"R74-10 confirmed rollback outcome");
 Check(Convert.ToInt64(await Scalar($"SELECT row_version FROM dbo.m_student WHERE student_id={id}"))==2,"R74-10 version rollback");
 Check(await Scalar($"SELECT remarks FROM dbo.m_student WHERE student_id={id}") is DBNull,"R74-10 value rollback");
 Check(Convert.ToInt32(await Scalar("SELECT COUNT(*) FROM dbo.t_operation_log"))==auditCount,"R74-10 audit rollback");
}finally{await Execute("DROP TRIGGER dbo.fixture_fail_audit;");}
var duplicate=Draft("T-0002");var warning=await service.SaveAsync(new(duplicate));Check(warning.Outcome==Outcome.ConfirmationRequired,"duplicate confirmation");
duplicate.EmergencyContactName="試験 花子";duplicate.RelationshipCode=relation;duplicate.EmergencyPhoneNumber="0312345678";
var invalidated=await service.SaveAsync(new(duplicate,ConfirmationToken:warning.ConfirmationToken,Reason:"別人を確認"));Check(invalidated.Outcome==Outcome.ConfirmationRequired,"R74-12 changed payload invalidates confirmation");
var confirmed=await service.SaveAsync(new(duplicate,ConfirmationToken:invalidated.ConfirmationToken,Reason:"別人を確認"));Check(confirmed.Outcome==Outcome.Saved,"confirmed duplicate save");
var beforeDelete=await service.GetAsync(confirmed.StudentId!.Value);
var deletion=await service.DeleteAsync(beforeDelete!.StudentId,beforeDelete.RowVersion,"試験終了");Check(deletion.Outcome==Outcome.Saved,"R74-11 logical delete");
Check((string)(await Scalar($"SELECT relationship_category FROM dbo.m_student WHERE student_id={beforeDelete.StudentId}"))! =="RELATIONSHIP","R74-11 delete preserves category");
Console.WriteLine($"PASS {checks} real SQL Server 2022 integration assertions; dedicated fixture preserved. Trusted server adapter; no native EXEC-only boundary test.");

static string FindSqlDirectory(){var current=new DirectoryInfo(AppContext.BaseDirectory);while(current is not null){if(File.Exists(Path.Combine(current.FullName,"001_schema.sql")))return current.FullName;current=current.Parent;}throw new FileNotFoundException("Generated schema and seed must remain with this test project.");}
