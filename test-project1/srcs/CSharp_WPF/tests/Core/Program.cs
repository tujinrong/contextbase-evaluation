using StudentManagement.Core;

var passed=0;
void Same<T>(T expected,T actual,string id) { if(!Equals(expected,actual)) throw new Exception($"{id}: expected {expected}, got {actual}"); passed++; }
void Reject(Action action,string id) { try { action(); } catch(ArgumentException) { passed++; return; } catch(InputValidationException) { passed++; return; } throw new Exception(id+": invalid input accepted"); }
var day=new DateOnly(2026,10,10);
DateOnly Parse(string era,string year,string month,string date)=>JapaneseDateService.Parse(new(era,year,month,date),day);
Same("平成20年05月15日",JapaneseDateService.ToWareki(new(2008,5,15)),"DATE-T01");
Same(new DateOnly(1900,1,1),Parse("MEIJI","33","01","01"),"DATE-T02");
Reject(()=>Parse("MEIJI","32","12","31"),"DATE-T02 below");
var boundaries=new[]{("TAISHO","1","07","29","30"),("SHOWA","1","12","24","25"),("HEISEI","1","01","07","08"),("REIWA","1","05","00","01")};
foreach(var (era,year,month,bad,good) in boundaries) {
    Reject(()=>Parse(era,year,month,bad),"DATE boundary "+era);
    Same(era,JapaneseDateService.ToInput(Parse(era,year,month,good)).Era,"DATE reverse "+era);
}
Reject(()=>Parse("TAISHO","15","12","25"),"DATE-T04");
Reject(()=>Parse("SHOWA","64","01","08"),"DATE-T06");
Reject(()=>Parse("HEISEI","31","05","01"),"DATE-T08");
Reject(()=>Parse("REIWA","元","04","30"),"DATE-T09");
foreach(var year in new[]{"0","-1","99999","1e2","1.5",""}) Reject(()=>Parse("REIWA",year,"05","01"),"DATE-T10 "+year);
Reject(()=>Parse("UNKNOWN","1","01","01"),"DATE-T10 unknown");
Same(new DateOnly(2000,2,29),Parse("HEISEI","12","02","29"),"DATE-T11");
Reject(()=>Parse("HEISEI","13","02","29"),"DATE-T11 nonleap");
Same(day,Parse("REIWA","8","10","10"),"DATE-T12 today");
Reject(()=>Parse("REIWA","8","10","11"),"DATE-T12 future");
foreach(var date in new[]{"2026-04-31","2026-13-01","26-04-01","1899-12-31","2026-10-11"}) Reject(()=>JapaneseDateService.ParseIso(date,day),"DATE-T13/14 "+date);
Same(2025,JapaneseDateService.SchoolYear(new(2026,3,31)),"DATE-T26 fiscal before");
Same(2026,JapaneseDateService.SchoolYear(new(2026,4,1)),"DATE-T26 fiscal after");
Same(8,StudentNormalizer.ScalarCount(string.Concat(Enumerable.Repeat("𠮷",8))),"T-25 scalars");
Reject(()=>StudentNormalizer.ScalarCount("\ud800"),"T-25 invalid high surrogate");
Reject(()=>StudentNormalizer.ScalarCount("\udc00"),"T-25 invalid low surrogate");
Reject(()=>StudentNormalizer.Text("         ",8,8,"StudentName"),"LEN raw before trim");
Reject(()=>StudentNormalizer.Text("123456789",8,8,"StudentName"),"LEN9");
Same("𠮷𠮷𠮷𠮷𠮷𠮷𠮷𠮷",StudentNormalizer.Text("𠮷𠮷𠮷𠮷𠮷𠮷𠮷𠮷",8,8,"StudentName"),"LEN supplementary8");
Same("見本 太郎",StudentNormalizer.Text("見本 太郎",8,8,"StudentName"),"N02 internal space");
Same("AB-01",StudentNormalizer.Identifier("ＡＢ-01",15,"StudentNo"),"N06");
Reject(()=>StudentNormalizer.Identifier("-A",15,"StudentNo"),"N06 initial");
Same("AB",StudentNormalizer.NameKey("Ａ  ｂ"),"N03");
Same("ミホン ガ",StudentNormalizer.Kana("みほん  ｶﾞ"),"N04");
Reject(()=>StudentNormalizer.Kana("ﾐ"+new string('ｱ',36)),"N04 raw37");
Reject(()=>StudentNormalizer.Kana(new string('ア',19)),"N04 saved19");
Reject(()=>StudentNormalizer.Kana("abc"),"N04 latin");
Same("1000001",StudentNormalizer.Postal("１００－０００１"),"N08");
Same("0312345678",StudentNormalizer.Phone("(03)1234-5678","PhoneNumber"),"N09 domestic");
Same("+81312345678",StudentNormalizer.Phone("+81 3 1234 5678","PhoneNumber"),"N09 international");
Reject(()=>StudentNormalizer.Phone("+012345678","PhoneNumber"),"N09 intl zero");
Reject(()=>StudentNormalizer.Phone("03/1234/5678","PhoneNumber"),"N09 invalid separator");
Same("User@example.com",StudentNormalizer.Email(" User@EXAMPLE.COM "),"N10 case");
foreach(var email in new[]{".x@example.com","x..y@example.com","x@example","x@-example.com","x@example-.com","x@例.jp"}) Reject(()=>StudentNormalizer.Email(email),"N10 "+email);
Same("!%!_!!![",StudentNormalizer.EscapeLike("%_!["),"N12 SQL literal metacharacters");
Reject(()=>StudentNormalizer.Code("1",2,"GradeCode"),"N07 no padding");
Reject(()=>StudentNormalizer.Text("a\tb",120,120,"Remarks",multiline:true),"N01 tab");
Same("a\nb",StudentNormalizer.Text("a\r\nb",120,120,"Remarks",multiline:true),"N01 LF");
// Combined-field rules belong to the pure normalizer; native saves validate in the DB entrance.
StudentDraft Draft()=>new() { StudentNo="S2026-0001",StudentName="見本 太郎",StudentNameKana="ミホン タロウ",BirthDateInput=new("HEISEI","20","05","15"),GenderCode="0",PostalCode="1000001",PrefectureCode="13",AddressLine1="見本町1",PhoneNumber="0312345678",AdmissionDate="2026-04-01",EnrollmentStatusCode="03",EnrollmentEndDate="2026-10-10" };
IReadOnlyList<FieldError> Invalid(Action<StudentDraft> edit) {
    var input=Draft();edit(input);
    try { StudentNormalizer.Normalize(input,day); }
    catch(InputValidationException error) {Same(true,error.Errors.Count>0,"combined normalizer refuses invalid input");return error.Errors;}
    throw new Exception("Combined invalid input was accepted by the normalizer.");
}
var supplementary=Invalid(d=> {d.StudentName=string.Concat(Enumerable.Repeat("𠮷",8));d.PostalCode="bad";});
Same(false,supplementary.Any(e=>e.Field=="StudentName"),"8 supplementary name survives whole draft validation");
Same(true,supplementary.Any(e=>e.Field=="PostalCode"&&e.Code=="E-STU-015"),"field-mapped postal error");
var malformed=Invalid(d=>d.StudentName="\ud800");Same(true,malformed.Any(e=>e.Field=="StudentName"&&e.Code=="E-STU-002"),"malformed Unicode has catalogued Japanese field error");
var ordered=Invalid(d=>d.AdmissionDate="2000-04-01");Same(true,ordered.Any(e=>e.Field=="AdmissionDate"&&e.Code=="E-STU-007"),"birth before admission");
var contact=Invalid(d=>d.PhoneNumber=null);Same(true,contact.Any(e=>e.Code=="E-STU-018"),"one contact required");
var emergency=Invalid(d=>d.EmergencyContactName="見本 花子");Same(true,emergency.Any(e=>e.Code=="E-STU-019"),"all three emergency fields required");
var active=Invalid(d=>d.EnrollmentStatusCode="01");Same(true,active.Any(e=>e.Field=="ClassId"&&e.Code=="E-STU-012"),"active requires class");Same(true,active.Any(e=>e.Field=="EnrollmentEndDate"&&e.Code=="E-STU-008"),"active excludes end date");
// These identity guards run before Open(); authorization by DB roles is an integration concern.
async Task Guard<TException>(Func<Task> action,string id) where TException:Exception {
    try {await action();}catch(TException){passed++;return;}
    throw new Exception(id+": invalid identity accepted");
}
var invalidSession=new SqlServerStudentService("Server=unconnected.invalid;Database=never_opened;Integrated Security=True",()=>new("test-principal","not-a-guid",Role.Viewer));
await Guard<UnauthorizedAccessException>(()=>invalidSession.SaveAsync(new(Draft())),"malformed session rejected before Open");
var emptyPrincipal=new SqlServerStudentService("Server=unconnected.invalid;Database=never_opened;Integrated Security=True",()=>new("",Guid.NewGuid().ToString(),Role.Staff));
await Guard<InputValidationException>(()=>emptyPrincipal.DeleteAsync(1,1,"理由"),"empty principal rejected before Open");
// R74-01/02/03/09: independent normalization tests; these are not DB round trips.
var emptyEmergency=StudentNormalizer.Normalize(Draft(),day);
foreach(var column in new[]{"emergency_contact_name","relationship_category","relationship_code","emergency_phone_number"}) Same<object?>(null,emptyEmergency.Values[column],"R74-01 empty "+column);
var completeDraft=Draft();completeDraft.EmergencyContactName="見本 花子";completeDraft.RelationshipCode="01";completeDraft.EmergencyPhoneNumber="0312345678";
var complete=StudentNormalizer.Normalize(completeDraft,day);
Same("RELATIONSHIP",complete.Text("relationship_category"),"R74-02 derived category");
Same("01",complete.Text("relationship_code"),"R74-02 value");
completeDraft.EmergencyContactName=null;completeDraft.RelationshipCode=null;completeDraft.EmergencyPhoneNumber=null;
var cleared=StudentNormalizer.Normalize(completeDraft,day);
foreach(var column in new[]{"emergency_contact_name","relationship_category","relationship_code","emergency_phone_number"}) Same<object?>(null,cleared.Values[column],"R74-03 cleared "+column);
var noContact=Draft();noContact.PhoneNumber=null;Reject(()=>StudentNormalizer.Normalize(noContact,day),"R74-09 contact still mandatory");
Same("UPDATE",AuditOperation.ForMaster(false,false),"R74-14 stopped name change");
Same("UPDATE",AuditOperation.ForMaster(true,true),"R74-14 active name change");
Same("DISABLE",AuditOperation.ForMaster(true,false),"R74-14 disable transition");
Same("ENABLE",AuditOperation.ForMaster(false,true),"R74-14 enable transition");
Same("CREATE",AuditOperation.ForMaster(null,false),"R74-14 new stopped code");
Same("CREATE",AuditOperation.ForMaster(null,true),"R74-14 new active code");
Console.WriteLine($"PASS {passed} independent boundary assertions; no DB or UI tests executed.");
