using System.Text.Json;
using StudentManagement.Core;

// Regression expectations are derived from the binary exports listed here,
// never from existing ASP.NET implementation or spec-eval:
// modUnicode, modJapaneseDate, modStudentRules, clsStudentService,
// clsConfirmation, modSecurity, modMasterMaintenance, modStudentSearch.
var results=new List<object>();var failed=0;
var masters=args.FirstOrDefault()??"database/seed/approved-masters.json";
var now=new DateTime(2026,10,27,0,0,0,DateTimeKind.Utc);
(InMemoryStudentRepository Store,StudentService Service) Fresh()
{var store=InMemoryStudentRepository.CreateVerification(masters);return(store,new StudentService(store,()=>now));}
Actor Admin(StudentService service)=>service.ResolveActor("verification-admin");
StudentDraft Draft(string number="NEW0001")=>new(){StudentNo=number,StudentName="架空次郎",StudentNameKana="カクウジロウ",BirthEra="HEISEI",BirthYear="12",BirthMonth="6",BirthDay="3",GenderCode="1",PostalCode="000-0000",PrefectureCode="13",AddressLine1="架空住所3",PhoneNumber="03-1234-5680",AdmissionDate="2026-04-01",EnrollmentStatusCode="01",ClassId=1};
void Check(bool pass,string message="Expectation failed"){if(!pass)throw new Exception(message);}
void Code(string code,Action action)
{try{action();throw new Exception($"Expected {code}");}catch(BusinessException ex){Check(ex.Code==code,$"Expected {code}, got {ex.Code}");}}
void Test(string name,Action action)
{try{action();results.Add(new{name,status="PASS"});}catch(Exception ex){failed++;results.Add(new{name,status="FAIL",error=ex.Message});}}

Test("scalar supplementary pairs count once",()=>Check(TextRules.ScalarCount("𠮷野")==2));
Test("unpaired surrogate rejected",()=>Code("E-STU-002",()=>TextRules.ScalarCount("\ud800")));
Test("raw length checked before compatibility normalization",()=>Code("E-STU-002",()=>TextRules.Text("ＡＢＣ",2,4,"number")));
Test("kana halfwidth and hiragana normalize",()=>Check(TextRules.Text(" ﾔﾏﾀﾞ　たろう ",36,18,"kana")=="ヤマダ タロウ"));
Test("kana latin characters rejected",()=>Code("E-STU-004",()=>TextRules.Text("TARO",36,18,"kana")));
Test("postal leading zero retained",()=>Check(TextRules.Text("０００－００００",10,7,"postal")=="0000000"));
Test("email lowercases domain only",()=>Check(TextRules.Text("Foo.Bar@EXAMPLE.COM",60,60,"email")=="Foo.Bar@example.com"));
Test("memo line endings normalize",()=>Check(TextRules.Text("a\r\nb\rc",120,120,"memo")=="a\nb\nc"));
Test("tab is forbidden even when whitespace",()=>Code("E-STU-002",()=>TextRules.Text("a\tb",8,8,"text")));
Test("whitespace-only optional becomes null",()=>Check(TextRules.Text("　 ",8,8,"text") is null));
Test("Reiwa first day accepted",()=>Check(JapaneseDate.ParseBirthDate("REIWA","元","5","1","2026-10-27")=="2019-05-01"));
Test("Reiwa before era boundary rejected",()=>Code("E-DATE-001",()=>JapaneseDate.ParseBirthDate("REIWA","1","4","30","2026-10-27")));
Test("Heisei after era boundary rejected",()=>Code("E-DATE-001",()=>JapaneseDate.ParseBirthDate("HEISEI","31","5","1","2026-10-27")));
Test("strict date rejects invalid leap day",()=>Code("E-STU-005",()=>JapaneseDate.StrictIso("2025-02-29",true)));
Test("strict date accepts fullwidth digits",()=>Check(JapaneseDate.StrictIso("２０２４-０２-２９",true)=="2024-02-29"));
Test("normalize validates contact requirement",()=>{var d=Draft();d.PhoneNumber=null;Code("E-STU-018",()=>StudentService.NormalizeDraft(d,"2026-10-27"));});
Test("normalize checks emergency triplet",()=>{var d=Draft();d.EmergencyContactName="架空母";Code("E-STU-019",()=>StudentService.NormalizeDraft(d,"2026-10-27"));});
Test("future admission rejected",()=>{var d=Draft();d.AdmissionDate="2026-10-28";Code("E-STU-007",()=>StudentService.NormalizeDraft(d,"2026-10-27"));});
Test("active status requires class",()=>{var d=Draft();d.ClassId=null;Code("E-STU-012",()=>StudentService.NormalizeDraft(d,"2026-10-27"));});
Test("ended status requires end date",()=>{var d=Draft();d.EnrollmentStatusCode="03";Code("E-STU-008",()=>StudentService.NormalizeDraft(d,"2026-10-27"));});
Test("reader cannot save and no row written",()=>{var(store,s)=Fresh();Code("E-COM-002",()=>s.Save(Draft(),null,null,s.ResolveActor("verification-reader"),"form"));Check(s.Search(new(),Admin(s)).Total==2);Check(store.AuditEntries.Count==0);});
Test("unknown role fails closed",()=>{var(_,s)=Fresh();Code("E-COM-001",()=>s.ResolveActor("unknown"));});
Test("role supplied by caller is revalidated",()=>{var(_,s)=Fresh();Code("E-COM-001",()=>s.Search(new(),new Actor("verification-reader",Role.Admin)));});
Test("create writes audit and re-searchable normalized values",()=>{var(store,s)=Fresh();var a=Admin(s);var r=s.Save(Draft("ｎｅｗ０００１"),null,null,a,"form");Check(r.Kind=="Saved");var found=s.Search(new(){StudentNo="NEW0001"},a);Check(found.Total==1&&found.Rows[0].Student.PostalCode=="0000000");Check(store.AuditEntries.Count==1&&store.AuditEntries[0].Operation=="CREATE");});
Test("no-change update does not advance version or audit",()=>{var(store,s)=Fresh();var a=Admin(s);var old=s.Get(1,a);var r=s.Save(StudentDraft.FromStudent(old),1,old.RowVersion,a,"form");Check(r.Kind=="NoChange"&&s.Get(1,a).RowVersion==old.RowVersion&&store.AuditEntries.Count==0);});
Test("stale version rejected without mutation",()=>{var(store,s)=Fresh();var a=Admin(s);var old=s.Get(1,a);var d=StudentDraft.FromStudent(old);d.AddressLine1="架空変更";Code("E-STU-105",()=>s.Save(d,1,99,a,"form"));Check(s.Get(1,a).AddressLine1==old.AddressLine1&&store.AuditEntries.Count==0);});
Test("business number immutable on update",()=>{var(_,s)=Fresh();var a=Admin(s);var d=StudentDraft.FromStudent(s.Get(1,a));d.StudentNo="CHANGED";Code("E-STU-104",()=>s.Save(d,1,1,a,"form"));});
Test("logical delete hides row and retains unique number",()=>{var(_,s)=Fresh();var a=Admin(s);s.Delete(1,1,"架空削除理由",true,a);Check(s.Search(new(){StudentNo="TRN001"},a).Total==0);var d=Draft("TRN001");Code("E-STU-101",()=>s.Save(d,null,null,a,"form"));});
Test("delete requires admin and explicit reason confirmation",()=>{var(_,s)=Fresh();var a=Admin(s);Code("E-COM-002",()=>s.Delete(1,1,"理由",true,s.ResolveActor("verification-staff")));Code("E-STU-020",()=>s.Delete(1,1,"理由",false,a));Code("E-STU-020",()=>s.Delete(1,1,null,true,a));});
Test("duplicate confirmation binds normalized draft and candidates",()=>{var(_,s)=Fresh();var a=Admin(s);var d=StudentDraft.FromStudent(s.Get(1,a));d.StudentNo="DUP0001";var first=s.Save(d,null,null,a,"form");Check(first.Kind=="ConfirmationRequired"&&first.Candidates?.Count==1);d.AddressLine1="変更住所";d.OperationReason="別人です";var invalid=s.Save(d,null,null,a,"form",first.ConfirmationToken,true);Check(invalid.Kind=="ConfirmationRequired"&&invalid.Message=="W-STU-102");var valid=s.Save(d,null,null,a,"form",invalid.ConfirmationToken,true);Check(valid.Kind=="Saved");});
Test("duplicate confirmation requires reason",()=>{var(_,s)=Fresh();var a=Admin(s);var d=StudentDraft.FromStudent(s.Get(1,a));d.StudentNo="DUP0002";var first=s.Save(d,null,null,a,"form");Code("E-STU-107",()=>s.Save(d,null,null,a,"form",first.ConfirmationToken,true));});
Test("duplicate token cannot cross form or actor",()=>{var(_,s)=Fresh();var a=Admin(s);var d=StudentDraft.FromStudent(s.Get(1,a));d.StudentNo="DUP0003";d.OperationReason="別人です";var first=s.Save(d,null,null,a,"first");var other=s.Save(d,null,null,s.ResolveActor("verification-staff"),"second",first.ConfirmationToken,true);Check(other.Kind=="ConfirmationRequired");});
Test("capacity rejects new seat atomically",()=>{var(store,s)=Fresh();store.Execute(true,x=>{var c=x.Classes()[0];x.WriteClass(c with{Capacity=2,RowVersion=2},1);return 0;});Code("E-STU-102",()=>s.Save(Draft(),null,null,Admin(s),"form"));Check(s.Search(new(),Admin(s)).Total==2);});
Test("class capacity cannot be lowered below occupancy",()=>{var(_,s)=Fresh();Code("E-MST-004",()=>s.MaintainClass(new(){SchoolYear="2026",GradeCode="01",ClassCode="TRN-A",ClassName="検証一組",ValidFrom="2026-04-01",ValidTo="2027-03-31",Capacity="1",DisplayOrder="10",IsActive=true},1,1,Admin(s)));});
Test("protected code cannot be disabled",()=>{var(_,s)=Fresh();var old=s.GetAllCodes(Admin(s)).Single(x=>x.CategoryId=="ENROLLMENT_STATUS"&&x.CodeValue=="01");Code("E-MST-003",()=>s.MaintainCode(old.CategoryId,old.CodeValue,new(){CodeName=old.CodeName,DisplayOrder=old.DisplayOrder.ToString(),ValidFrom=old.ValidFrom,IsActive=false},old.RowVersion,Admin(s)));});
Test("binary name search and deterministic tie ordering",()=>{var(_,s)=Fresh();var a=Admin(s);Check(s.Search(new(){Name="検証"},a,"name","asc").Total==2);Code("E-SRC-002",()=>s.Search(new(),a,"untrusted","asc"));});
Test("phone-only audit contains only actual changed values",()=>{var(store,s)=Fresh();var a=Admin(s);var d=StudentDraft.FromStudent(s.Get(1,a));d.PhoneNumber="0311112222";s.Save(d,1,1,a,"form");var cols=JsonSerializer.Deserialize<string[]>(store.AuditEntries.Single().ChangedColumns)!;Check(cols.SequenceEqual(new[]{"phone_number","row_version","updated_at","updated_by"}));});
Test("create audit includes derived fixed and creation columns",()=>{var(store,s)=Fresh();s.Save(Draft(),null,null,Admin(s),"form");var cols=JsonSerializer.Deserialize<string[]>(store.AuditEntries.Single().ChangedColumns)!;Check(new[]{"name_key","kana_key","gender_category","prefecture_category","enrollment_category","relationship_category","is_deleted","created_at","created_by","row_version","updated_at","updated_by"}.All(cols.Contains));Check(cols.Length==cols.Distinct().Count());});
Test("relationship category audit tracks null to assigned transition",()=>{var(store,s)=Fresh();var a=Admin(s);var d=StudentDraft.FromStudent(s.Get(1,a));d.EmergencyContactName="架空母";d.RelationshipCode="01";d.EmergencyPhoneNumber="09012345678";s.Save(d,1,1,a,"form");var cols=JsonSerializer.Deserialize<string[]>(store.AuditEntries.Single().ChangedColumns)!;Check(cols.Contains("relationship_category")&&!cols.Contains("name_key")&&!cols.Contains("kana_key"));});
Test("class name-only audit omits unchanged master fields",()=>{var(store,s)=Fresh();s.MaintainClass(new(){SchoolYear="2026",GradeCode="01",ClassCode="TRN-A",ClassName="検証二組",ValidFrom="2026-04-01",ValidTo="2027-03-31",Capacity="30",DisplayOrder="10",IsActive=true},1,1,Admin(s));var cols=JsonSerializer.Deserialize<string[]>(store.AuditEntries.Single().ChangedColumns)!;Check(cols.SequenceEqual(new[]{"class_name","row_version","updated_at","updated_by"}));});
Test("code name-only audit omits unchanged master fields",()=>{var(store,s)=Fresh();var a=Admin(s);var c=s.GetAllCodes(a).Single(x=>x.CategoryId=="GENDER"&&x.CodeValue=="1");s.MaintainCode(c.CategoryId,c.CodeValue,new(){CodeName="検証名称",DisplayOrder=c.DisplayOrder.ToString(),IsActive=c.IsActive,ValidFrom=c.ValidFrom,ValidTo=c.ValidTo,Remarks=c.Remarks},c.RowVersion,a);var cols=JsonSerializer.Deserialize<string[]>(store.AuditEntries.Single().ChangedColumns)!;Check(cols.SequenceEqual(new[]{"code_name","row_version","updated_at","updated_by"}));});
Test("unchanged class at maximum version remains NoChange",()=>{var(store,s)=Fresh();store.Execute(true,x=>{var c=x.Classes()[0];x.WriteClass(c with{RowVersion=int.MaxValue},c.RowVersion);return 0;});var r=s.MaintainClass(new(){SchoolYear="2026",GradeCode="01",ClassCode="TRN-A",ClassName="検証一組",ValidFrom="2026-04-01",ValidTo="2027-03-31",Capacity="30",DisplayOrder="10",IsActive=true},1,int.MaxValue,Admin(s));Check(r.Kind=="NoChange"&&store.AuditEntries.Count==0);});
Test("unchanged code at maximum version remains NoChange",()=>{var(store,s)=Fresh();store.Execute(true,x=>{var c=x.Codes().Single(x=>x.CategoryId=="GENDER"&&x.CodeValue=="1");x.WriteCode(c with{RowVersion=int.MaxValue},c.RowVersion);return 0;});var a=Admin(s);var c=s.GetAllCodes(a).Single(x=>x.CategoryId=="GENDER"&&x.CodeValue=="1");var r=s.MaintainCode(c.CategoryId,c.CodeValue,new(){CodeName=c.CodeName,DisplayOrder=c.DisplayOrder.ToString(),IsActive=c.IsActive,ValidFrom=c.ValidFrom,ValidTo=c.ValidTo,Remarks=c.Remarks},int.MaxValue,a);Check(r.Kind=="NoChange"&&store.AuditEntries.Count==0);});
Test("capacity preserves source raw ASCII PositiveId rule",()=>{var(_,s)=Fresh();Code("E-COM-003",()=>s.MaintainClass(new(){SchoolYear="2026",GradeCode="01",ClassCode="TRN-A",ClassName="検証一組",ValidFrom="2026-04-01",ValidTo="2027-03-31",Capacity="３０",DisplayOrder="10",IsActive=true},1,1,Admin(s)));});
Test("era display retains first year and padded month day",()=>{Check(JapaneseDate.FormatBirthDate("2019-05-01")=="令和元年05月01日");Check(JapaneseDate.FormatBirthDate("1989-01-07")=="昭和64年01月07日");Check(JapaneseDate.FormatBirthDate("1989-01-08")=="平成元年01月08日");});

Console.WriteLine(JsonSerializer.Serialize(new{status=failed==0?"PASS":"FAIL",passed=results.Count-failed,failed,total=results.Count,source="binary-export-derived cases; in-memory provider only",results},new JsonSerializerOptions{WriteIndented=true}));
return failed==0?0:1;
