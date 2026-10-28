using System.Data;
using System.Text.Json;
using Microsoft.Data.SqlClient;
using StudentManagement.Core;

// Opt-in real SQL tests: only the explicitly authorized dedicated training DB.
// No seed-row changes, DELETE, DROP or reset. Mutating cases create distinct QA keys.
var connectionString=Environment.GetEnvironmentVariable("ACCESS_REBUILDER_SQL");
if(string.IsNullOrWhiteSpace(connectionString))
{Console.WriteLine(JsonSerializer.Serialize(new{status="NOT-RUN",reason="ACCESS_REBUILDER_SQL is not configured."}));return 2;}
var builder=new SqlConnectionStringBuilder(connectionString);
if(builder.InitialCatalog!="AccessRebuilderTraining_01a17be7"||builder.DataSource!=@".\SQLEXPRESS")
{Console.WriteLine(JsonSerializer.Serialize(new{status="REFUSED",reason="Only the user-selected dedicated local training database is allowed."}));return 2;}
var results=new List<object>();var failed=0;
var repository=new SqlStudentRepository(connectionString);
var now=new DateTime(2026,10,27,0,0,0,DateTimeKind.Utc);
StudentService Service()=>new(repository,()=>now);
var service=Service();var admin=service.ResolveActor("verification-admin");
var suffix=Guid.NewGuid().ToString("N")[..5].ToUpperInvariant();
var sequence=0;
string NextNo()=>"QA"+suffix+(++sequence).ToString("00");
StudentDraft Draft(int? classId=1)
{
    var number=NextNo();
    // Distinct synthetic name/kana per test run, not source/production personal data.
    const string kana="アイウエオカキクケコサシスセソタ";
    var tail=new string(suffix.Select(c=>kana[Convert.ToInt32(c.ToString(),16)]).ToArray());
    return new(){StudentNo=number,StudentName="架空"+suffix,StudentNameKana="カクウ"+tail+"ア",BirthEra="HEISEI",BirthYear="12",BirthMonth="6",BirthDay="3",GenderCode="1",PostalCode="000-0000",PrefectureCode="13",AddressLine1="架空SQL住所",PhoneNumber="0312345680",AdmissionDate="2026-04-01",EnrollmentStatusCode="01",ClassId=classId};
}
void Check(bool value,string message="Expectation failed"){if(!value)throw new Exception(message);}
void Code(string code,Action action)
{try{action();throw new Exception($"Expected {code}");}catch(BusinessException ex){Check(ex.Code==code,$"Expected {code}, got {ex.Code}");}}
void Test(string name,Action action)
{try{action();results.Add(new{name,status="PASS"});}catch(Exception ex){failed++;results.Add(new{name,status="FAIL",error=ex.Message});}}
T Scalar<T>(string sql,params (string Key,object? Value)[] parameters)
{
    using var connection=new SqlConnection(connectionString);connection.Open();using var command=new SqlCommand(sql,connection);
    foreach(var (key,value) in parameters)command.Parameters.AddWithValue(key,value??DBNull.Value);
    return (T)Convert.ChangeType(command.ExecuteScalar()!,typeof(T),System.Globalization.CultureInfo.InvariantCulture);
}
bool Guard()=>Scalar<bool>("SELECT lock_bit FROM dbo.t_write_guard WHERE guard_id=1");
int AuditCount()=>Scalar<int>("SELECT COUNT(*) FROM dbo.t_operation_log");
string[] LastColumns(string table,string key)=>JsonSerializer.Deserialize<string[]>(Scalar<string>("SELECT TOP(1) changed_columns FROM dbo.t_operation_log WHERE target_table=@table AND target_key=@key ORDER BY log_id DESC",("@table",table),("@key",key)))!;
SaveResult SaveOwned(StudentDraft draft,StudentService? chosen=null)
{
    chosen??=service;var form="sql-"+draft.StudentNo;var saved=chosen.Save(draft,null,null,admin,form);
    if(saved.Kind=="ConfirmationRequired")
    {draft.OperationReason="架空SQL検証データを別人として登録";saved=chosen.Save(draft,null,null,admin,form,saved.ConfirmationToken,true);}
    Check(saved.Kind=="Saved");return saved;
}
var owned=new List<int>();int? current=null;int? currentVersion=null;

Test("dedicated schema and role mapping",()=>{Check(Scalar<int>("SELECT COUNT(*) FROM sys.tables WHERE is_ms_shipped=0")==7);Check(admin.Role==Role.Admin&&service.ResolveActor("verification-reader").Role==Role.Reader);});
Test("NoChange rolls back guard and leaves audit untouched",()=>{var before=Guard();var audits=AuditCount();var old=service.Get(1,admin);var r=service.Save(StudentDraft.FromStudent(old),1,old.RowVersion,admin,"noop");Check(r.Kind=="NoChange"&&Guard()==before&&AuditCount()==audits);});
Test("confirmation-required rolls back guard and creates no row",()=>{var before=Guard();var audits=AuditCount();var draft=StudentDraft.FromStudent(service.Get(1,admin));draft.StudentNo=NextNo();var r=service.Save(draft,null,null,admin,"pending");Check(r.Kind=="ConfirmationRequired"&&Guard()==before&&AuditCount()==audits&&service.Search(new(){StudentNo=draft.StudentNo},admin).Total==0);});
Test("Reader save denied with transaction rollback",()=>{var before=Guard();var audits=AuditCount();Code("E-COM-002",()=>service.Save(Draft(),null,null,service.ResolveActor("verification-reader"),"reader"));Check(Guard()==before&&AuditCount()==audits);});
Test("SQL create persists normalized values and complete audit",()=>{var d=Draft();var r=SaveOwned(d);current=r.StudentId;currentVersion=r.RowVersion;owned.Add(current!.Value);var s=service.Get(current.Value,admin);Check(s.PostalCode=="0000000"&&s.StudentNo==d.StudentNo&&s.RowVersion==1);var columns=LastColumns("m_student",current.ToString()!);Check(new[]{"name_key","kana_key","gender_category","prefecture_category","enrollment_category","relationship_category","is_deleted","created_at","created_by"}.All(columns.Contains));});
Test("SQL phone-only update has exact changed-column audit",()=>{Check(current is not null);var old=service.Get(current!.Value,admin);var d=StudentDraft.FromStudent(old);d.PhoneNumber="0311112222";var r=service.Save(d,old.StudentId,old.RowVersion,admin,"edit");currentVersion=r.RowVersion;Check(r.Kind=="Saved"&&LastColumns("m_student",old.StudentId.ToString()).SequenceEqual(new[]{"phone_number","row_version","updated_at","updated_by"}));});
Test("SQL stale version preserves row audit and guard",()=>{Check(current is not null);var before=Guard();var audits=AuditCount();var old=service.Get(current!.Value,admin);var d=StudentDraft.FromStudent(old);d.AddressLine1="競合で保存しない";Code("E-STU-105",()=>service.Save(d,old.StudentId,1,admin,"stale"));Check(service.Get(old.StudentId,admin).AddressLine1==old.AddressLine1&&Guard()==before&&AuditCount()==audits);});
Test("SQL confirmed duplicate writes only after valid bound token",()=>{var before=Guard();var original=service.Get(1,admin);var d=StudentDraft.FromStudent(original);d.StudentNo=NextNo();d.OperationReason="架空検証の重複確認";var first=service.Save(d,null,null,admin,"duplicate");Check(first.Kind=="ConfirmationRequired"&&Guard()==before);var saved=service.Save(d,null,null,admin,"duplicate",first.ConfirmationToken,true);Check(saved.Kind=="Saved");owned.Add(saved.StudentId!.Value);Check(Scalar<bool>("SELECT TOP(1) duplicate_confirmed FROM dbo.t_operation_log WHERE target_table=N'm_student' AND target_key=@key ORDER BY log_id DESC",("@key",saved.StudentId.Value.ToString())));});
Test("SQL optimistic race allows one update and one conflict",()=>{var d=Draft();d.StudentName="競合"+suffix;d.StudentNameKana=d.StudentNameKana+"イ";var created=SaveOwned(d);owned.Add(created.StudentId!.Value);var old=service.Get(created.StudentId.Value,admin);var left=StudentDraft.FromStudent(old);left.AddressLine1="競合左";var right=StudentDraft.FromStudent(old);right.AddressLine1="競合右";var saved=0;var conflicts=0;var errors=new List<Exception>();Parallel.Invoke(()=>Attempt(Service(),left),()=>Attempt(Service(),right));Check(saved==1&&conflicts==1&&errors.Count==0,$"Saved={saved},conflicts={conflicts},errors={string.Join(';',errors.Select(x=>x.Message))}");void Attempt(StudentService s,StudentDraft value){try{Check(s.Save(value,old.StudentId,old.RowVersion,admin,"race").Kind=="Saved");Interlocked.Increment(ref saved);}catch(BusinessException ex)when(ex.Code=="E-STU-105"){Interlocked.Increment(ref conflicts);}catch(Exception ex){lock(errors)errors.Add(ex);}}});
Test("SQL class name-only audit is exact",()=>{var code="Q"+suffix;var draft=new ClassDraft{SchoolYear="2026",GradeCode="01",ClassCode=code,ClassName="架空検証組",ValidFrom="2026-04-01",ValidTo="2027-03-31",Capacity="10",DisplayOrder="990",IsActive=true};var created=service.MaintainClass(draft,null,null,admin);draft.ClassName="架空変更組";var updated=service.MaintainClass(draft,created.StudentId,created.RowVersion,admin);Check(updated.Kind=="Saved"&&LastColumns("m_class",created.StudentId.ToString()!).SequenceEqual(new[]{"class_name","row_version","updated_at","updated_by"}));});
Test("SQL logical delete hides owned row and retains unique business key",()=>{Check(current is not null);var old=service.Get(current!.Value,admin);service.Delete(old.StudentId,old.RowVersion,"架空SQL検証終了",true,admin);Check(service.Search(new(){StudentNo=old.StudentNo},admin).Total==0);var d=Draft();d.StudentNo=old.StudentNo;Code("E-STU-101",()=>service.Save(d,null,null,admin,"reused"));});

// Cleanup only this runner's newly created students through the normal logical-delete path.
foreach(var id in owned.Distinct())
{
    try{var row=service.Get(id,admin);service.Delete(id,row.RowVersion,"架空SQL検証終了",true,admin);}
    catch(BusinessException ex)when(ex.Code=="E-STU-103"){}
    catch(Exception ex){failed++;results.Add(new{name="owned fixture logical cleanup",status="FAIL",error=ex.Message});}
}
Console.WriteLine(JsonSerializer.Serialize(new{status=failed==0?"PASS":"FAIL",passed=results.Count-failed,failed,total=results.Count,provider="SQL Server",database=builder.InitialCatalog,source="binary-derived domain semantics; dedicated fictional test data",results},new JsonSerializerOptions{WriteIndented=true}));
return failed==0?0:1;
