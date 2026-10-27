using System.Data;
using System.Text.Json;
using Microsoft.Data.SqlClient;
using StudentManagement.Core;

var text=Environment.GetEnvironmentVariable("SHARED_STUDENT_DB_CONNECTION");
if(string.IsNullOrWhiteSpace(text)){Console.WriteLine("NOT-RUN: SHARED_STUDENT_DB_CONNECTION is required.");return 2;}
var settings=new SqlConnectionStringBuilder(text);
if(settings.DataSource!=@".\SQLEXPRESS"||settings.InitialCatalog!="AccessRebuilderTraining_01a17be7")throw new InvalidOperationException("Only the explicitly selected local shared training database is allowed.");
var checks=new List<object>();var failed=0;long? created=null;
var user=new CurrentUser("verification-admin",Guid.NewGuid().ToString(),Role.Administrator);
SqlServerStudentService Service(CurrentUser? actor=null)=>new(text,()=>actor??user,webTokens:true,databaseProfile:StudentDatabaseProfile.SharedAccess);
var service=Service();
async Task<T> Scalar<T>(string sql,params(string Name,object? Value)[] parameters){await using var c=new SqlConnection(text);await c.OpenAsync();await using var q=new SqlCommand(sql,c);foreach(var p in parameters)q.Parameters.AddWithValue(p.Name,p.Value??DBNull.Value);return (T)Convert.ChangeType((await q.ExecuteScalarAsync())!,typeof(T),System.Globalization.CultureInfo.InvariantCulture);}
void Assert(bool value,string message="Expectation failed"){if(!value)throw new Exception(message);}
async Task Test(string name,Func<Task> action){try{await action();checks.Add(new{name,status="PASS"});}catch(Exception ex){failed++;checks.Add(new{name,status="FAIL",error=ex.ToString()});}}
var number="SHR"+Guid.NewGuid().ToString("N")[..8].ToUpperInvariant();
await Test("existing canonical rows load with integer IDs and ISO dates",async()=>{var s=await service.SearchAsync(new(){StudentNoPrefix="TRN"});Assert(s.Items.Count==2);var d=await service.GetAsync(s.Items[0].StudentId);Assert(d is not null&&d.UpdatedAt.Offset==TimeSpan.Zero);Assert(d!.Draft.AdmissionDate=="2026-04-01");});
await Test("lookup reads class dates and all approved codes",async()=>{var lookups=await service.LookupAsync();Assert(lookups.Codes.Count==70&&lookups.Classes.Any(c=>c.ClassId==1));});
await Test("create stores canonical values and audit",async()=>{
 var draft=new StudentDraft{StudentNo=number,StudentName="共有確認",StudentNameKana="キョウユウカクニン",BirthDateInput=new("HEISEI","12","06","03"),GenderCode="0",PostalCode="001-0001",PrefectureCode="13",AddressLine1="架空の共有DB住所",PhoneNumber="0311113333",AdmissionDate="2026-04-01",EnrollmentStatusCode="01",ClassId=1};
 var result=await service.SaveAsync(new(draft,SchoolYear:2026,GradeCode:"01"));
 if(result.Outcome==Outcome.ConfirmationRequired)result=await service.SaveAsync(new(draft,SchoolYear:2026,GradeCode:"01",ConfirmationToken:result.ConfirmationToken,Reason:"架空の別人を確認"));
 Assert(result.Outcome==Outcome.Saved,string.Join(';',result.Errors.Select(e=>e.Code+":"+e.Message)));created=result.StudentId;
 Assert(await Scalar<string>("SELECT postal_code FROM dbo.m_student WHERE student_id=@id",("@id",created))=="0010001");
 Assert(await Scalar<int>("SELECT COUNT(*) FROM dbo.t_operation_log WHERE target_table=N'm_student' AND target_key=@id AND operation_type=N'CREATE'",("@id",created!.Value.ToString()))==1);
});
if(created is { } id){
 await Test("no-change leaves integer version audit and shared guard untouched",async()=>{var before=await service.GetAsync(id);var guard=await Scalar<bool>("SELECT lock_bit FROM dbo.t_write_guard WHERE guard_id=1");var audits=await Scalar<int>("SELECT COUNT(*) FROM dbo.t_operation_log WHERE target_key=@id",("@id",id.ToString()));var result=await service.SaveAsync(new(before!.Draft,id,before.RowVersion,2026,"01"));Assert(result.Outcome==Outcome.NoChange);Assert(await Scalar<bool>("SELECT lock_bit FROM dbo.t_write_guard WHERE guard_id=1")==guard);Assert(await Scalar<int>("SELECT COUNT(*) FROM dbo.t_operation_log WHERE target_key=@id",("@id",id.ToString()))==audits);});
 await Test("two services share optimistic version checks",async()=>{var a=await service.GetAsync(id);var b=await service.GetAsync(id);a!.Draft.Remarks="架空の競合A";b!.Draft.Remarks="架空の競合B";var results=await Task.WhenAll(service.SaveAsync(new(a.Draft,id,a.RowVersion,2026,"01")),Service().SaveAsync(new(b.Draft,id,b.RowVersion,2026,"01")));Assert(results.Count(r=>r.Outcome==Outcome.Saved)==1&&results.Count(r=>r.Outcome==Outcome.Conflict)==1);});
 await Test("canonical guard blocks this application too",async()=>{
  await using var c=new SqlConnection(text);await c.OpenAsync();await using var tx=(SqlTransaction)await c.BeginTransactionAsync();await using(var q=new SqlCommand("UPDATE dbo.t_write_guard SET lock_bit=lock_bit WHERE guard_id=1",c,tx))await q.ExecuteNonQueryAsync();
  var current=await service.GetAsync(id);current!.Draft.PhoneNumber="0312224444";var pending=service.SaveAsync(new(current.Draft,id,current.RowVersion,2026,"01"));await Task.Delay(200);var wasBlocked=!pending.IsCompleted;await tx.CommitAsync();var result=await pending;Assert(wasBlocked&&result.Outcome==Outcome.Saved);
 });
 await Test("viewer cannot modify shared data",async()=>{var current=await service.GetAsync(id);current!.Draft.PhoneNumber="0399999999";var result=await Service(new("verification-reader",Guid.NewGuid().ToString(),Role.Viewer)).SaveAsync(new(current.Draft,id,current.RowVersion,2026,"01"));Assert(result.Outcome==Outcome.Forbidden);Assert(await Scalar<string>("SELECT phone_number FROM dbo.m_student WHERE student_id=@id",("@id",id))=="0312224444");});
 await Test("logical delete uses existing schema and preserves unique number",async()=>{var current=await service.GetAsync(id);var result=await service.DeleteAsync(id,current!.RowVersion,"架空の共有DB検査終了");Assert(result.Outcome==Outcome.Saved);Assert((await service.SearchAsync(new(){StudentNoPrefix=number})).Count==0);Assert(await Scalar<bool>("SELECT is_deleted FROM dbo.m_student WHERE student_id=@id",("@id",id)));});
}
Console.WriteLine(JsonSerializer.Serialize(new{schema="csharp-shared-db-tests/1.0",status=failed==0?"PASS":"FAIL",passed=checks.Count-failed,failed,checks,createdStudentNo=number,scope="Actual selected shared DB. New synthetic key only; no schema/seed reset.",formalScore=(int?)null},new JsonSerializerOptions{WriteIndented=true}));
return failed==0?0:1;
