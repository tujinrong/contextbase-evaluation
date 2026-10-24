using StudentManagement.Core;

var passed=0;
void Same<T>(T expected,T actual,string id) { if(!Equals(expected,actual)) throw new Exception($"{id}: expected {expected}, got {actual}"); passed++; }
void Check(bool value,string id)=>Same(true,value,id);
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
// All these saves fail before Open(): verify combined-field rules without a database.
var service=new SqlServerStudentService("Server=unconnected.invalid;Database=never_opened;Integrated Security=True",()=>new("test-staff",Guid.Empty.ToString(),Role.Staff));
var four=SearchCriteria.Create("ａｂ-１","㍿",9007199254740993,["01","02"]);
Check(four.StudentNoPrefix=="AB-1"&&four.NameKey=="株式会社"&&four.ClassId==9007199254740993,"compact criteria normalize raw before storage");
Check(SearchCriteria.Create(null,null,null,[]).StatusCodes.Length==0,"all-off search statuses mean all");
foreach(var badSize in new[]{0,19,21})try{SearchCriteria.Create(null,null,null,[],badSize);throw new Exception("bad size accepted");}catch(InputValidationException){Check(true,"invalid page size rejected");}
foreach(var statuses in new[]{new[]{"01","01"},new[]{"99"},new[]{"01","02","03","04","01"}})try{SearchCriteria.Create(null,null,null,statuses);throw new Exception("bad statuses accepted");}catch(InputValidationException){Check(true,"duplicate undefined excess statuses rejected");}
try{SearchCriteria.Create(null,"あいうえおかきくけ",null,[]);throw new Exception("overlong search name accepted");}catch(InputValidationException){Check(true,"raw name guard precedes name key");}
StudentDraft Draft()=>new() { StudentNo="S2026-0001",StudentName="見本 太郎",StudentNameKana="ミホン タロウ",BirthDateInput=new("HEISEI","20","05","15"),GenderCode="0",PostalCode="1000001",PrefectureCode="13",AddressLine1="見本町1",PhoneNumber="0312345678",AdmissionDate="2026-04-01",EnrollmentStatusCode="03",EnrollmentEndDate="2026-10-10" };
async Task<SaveResult> Invalid(Action<StudentDraft> edit) { var input=Draft();edit(input);var result=await service.SaveAsync(new(input));Same(Outcome.ValidationFailed,result.Outcome,"combined validation before DB");return result; }
var supplementary=await Invalid(d=> {d.StudentName=string.Concat(Enumerable.Repeat("𠮷",8));d.PostalCode="bad";});
Same(false,supplementary.Errors.Any(e=>e.Field=="StudentName"),"8 supplementary name survives whole draft validation");
Same(true,supplementary.Errors.Any(e=>e.Field=="PostalCode"&&e.Code=="E-STU-015"),"field-mapped postal error");
var malformed=await Invalid(d=>d.StudentName="\ud800");Same(true,malformed.Errors.Any(e=>e.Field=="StudentName"&&e.Code=="E-STU-002"),"malformed Unicode has catalogued Japanese field error");
var ordered=await Invalid(d=>d.AdmissionDate="2000-04-01");Same(true,ordered.Errors.Any(e=>e.Field=="AdmissionDate"&&e.Code=="E-STU-007"),"birth before admission");
var contact=await Invalid(d=>d.PhoneNumber=null);Same(true,contact.Errors.Any(e=>e.Code=="E-STU-018"),"one contact required");
var emergency=await Invalid(d=>d.EmergencyContactName="見本 花子");Same(true,emergency.Errors.Any(e=>e.Code=="E-STU-019"),"all three emergency fields required");
var active=await Invalid(d=>d.EnrollmentStatusCode="01");Same(true,active.Errors.Any(e=>e.Field=="ClassId"&&e.Code=="E-STU-012"),"active requires class");Same(true,active.Errors.Any(e=>e.Field=="EnrollmentEndDate"&&e.Code=="E-STU-008"),"active excludes end date");
var viewer=new SqlServerStudentService("Server=unconnected.invalid;Database=never_opened;Integrated Security=True",()=>new("test-viewer",Guid.Empty.ToString(),Role.Viewer));
Same(Outcome.Forbidden,(await viewer.SaveAsync(new(Draft()))).Outcome,"Viewer save denied before DB");
Same(Outcome.Forbidden,(await service.DeleteAsync(1,1,"理由")).Outcome,"Staff delete denied before DB");
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
