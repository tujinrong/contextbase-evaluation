using System.Globalization;
using System.Xml;
using StudentManagement.Core;
using StudentManagement.Native;

var checks=0;
void Check(bool condition,string name) {checks++;Console.WriteLine($"{checks}\t{(condition?"PASS":"FAIL")}\t{name}");if(!condition)throw new Exception(name);}
var business=new DateTime(2026,10,12);
SaveRequest Request(Action<StudentDraft> edit=null) {
    var d=new StudentDraft {StudentNo="ｓ２０２６-０１",StudentName="山田 太郎",StudentNameKana="やまだ　たろう",BirthDateInput=new("HEISEI","１５","０４","０２"),
        GenderCode="０",PostalCode="１００－００００",PrefectureCode="１３",AddressLine1="東京都見本町１",PhoneNumber="０３－１２３４－５６７８",
        EmailAddress="Student@EXAMPLE.INVALID",AdmissionDate="２０２６-０４-０１",EnrollmentStatusCode="０１",ClassId=1};
    edit?.Invoke(d);return new(d,SchoolYear:2026,GradeCode:"００");
}
XmlDocument Normalize(SaveRequest r) {var xml=new XmlDocument();xml.LoadXml(NativeNormalizer.NormalizeText(NativeStoredProcedureClient.SerializeRaw(r),business));return xml;}
string Value(XmlDocument doc,string key) => doc.SelectSingleNode("/normalized/values/"+key)?.InnerText;
string Code(XmlDocument doc) => doc.DocumentElement.GetAttribute("code");
bool Good(XmlDocument doc) => doc.DocumentElement.GetAttribute("ok")=="true";
var request=Request();var raw=NativeStoredProcedureClient.SerializeRaw(request);var n=Normalize(request);
Check(raw.Contains("ｓ２０２６-０１") && raw.Contains("やまだ"),"wire retains unnormalized original values");
Check(Good(n),"baseline raw normalization");
Check(Value(n,"student_no")==StudentNormalizer.Identifier(request.Draft.StudentNo,15,"StudentNo"),"NFKC identifier server/client boundary");
Check(Value(n,"student_name")==request.Draft.StudentName,"display name preserves width/text");
Check(Value(n,"student_name_kana")==StudentNormalizer.Kana(request.Draft.StudentNameKana),"hiragana/fullwidth space -> kana");
Check(Value(n,"name_key")==StudentNormalizer.NameKey(request.Draft.StudentName),"name key normalization");
Check(Value(n,"kana_key")=="ヤマダタロウ","kana key ignores spaces");
Check(Value(n,"postal_code")==StudentNormalizer.Postal(request.Draft.PostalCode),"postal normalization");
Check(Value(n,"phone_number")==StudentNormalizer.Phone(request.Draft.PhoneNumber,"PhoneNumber"),"phone normalization");
Check(Value(n,"email_address")==StudentNormalizer.Email(request.Draft.EmailAddress),"email domain lower case / local preserve");
Check(Value(n,"birth_date")==JapaneseDateService.Parse(request.Draft.BirthDateInput,new(2026,10,12)).ToString("yyyy-MM-dd",CultureInfo.InvariantCulture),"raw four-part era normalization");
Check(Value(n,"admission_date")=="2026-04-01","fullwidth ISO normalization");
Check(n.SelectSingleNode("/normalized/values/relationship_category/@null")?.Value=="true","no emergency -> both relationship fields NULL");
Check(Code(Normalize(Request(d=>d.StudentName=new string('名',9))))=="E-STU-002","name raw maximum");
Check(Good(Normalize(Request(d=>d.StudentName=string.Concat(Enumerable.Repeat("𠮷",8))))),"eight supplementary scalars accepted");
Check(Code(Normalize(Request(d=>d.StudentName=string.Concat(Enumerable.Repeat("𠮷",9)))))=="E-STU-002","nine supplementary scalars rejected");
Check(Good(Normalize(Request(d=>d.StudentNameKana=string.Concat(Enumerable.Repeat("ｶﾞ",18))))),"raw 36 / saved 18 kana boundary");
Check(Code(Normalize(Request(d=>d.StudentNameKana=string.Concat(Enumerable.Repeat("ｶﾞ",18))+"ｶ")))=="E-STU-002","raw kana 37 rejected");
Check(Code(Normalize(Request(d=>d.StudentNameKana=new string('カ',19))))=="E-STU-002","saved kana 19 rejected");
Check(Code(Normalize(Request(d=>d.StudentNameKana="A")))=="E-STU-004","non-kana rejected");
Check(Code(Normalize(Request(d=>d.StudentNo="-BAD")))=="E-STU-003","identifier leading hyphen rejected");
Check(Code(Normalize(Request(d=>d.PostalCode="123")))=="E-STU-015","postal format");
Check(Code(Normalize(Request(d=>d.PhoneNumber="+１２３４５６７")))=="","international phone accepted");
Check(Code(Normalize(Request(d=>d.PhoneNumber="123")))=="E-STU-016","phone format");
Check(Code(Normalize(Request(d=>d.EmailAddress="bad..mail@example.invalid")))=="E-STU-017","mail local dot format");
Check(Code(Normalize(Request(d=>d.EmailAddress="a@-bad.invalid")))=="E-STU-017","mail domain labels");
Check(Code(Normalize(Request(d=>d.GenderCode="9x")))=="E-STU-002","raw code maximum before normalization");
Check(Code(Normalize(Request(d=>d.GenderCode="X")))=="E-STU-009","code digits");
Check(Code(Normalize(Request(d=>d.BirthDateInput=new("HEISEI","元","01","07"))))=="E-DATE-001","Heisei boundary excludes January 7");
Check(Value(Normalize(Request(d=>d.BirthDateInput=new("SHOWA","64","01","07"))),"birth_date")=="1989-01-07","Showa final day");
Check(Value(Normalize(Request(d=>d.BirthDateInput=new("HEISEI","元","01","08"))),"birth_date")=="1989-01-08","Heisei first day");
Check(Code(Normalize(Request(d=>d.BirthDateInput=new("REIWA","元","04","30"))))=="E-DATE-001","Reiwa excludes April 30");
Check(Value(Normalize(Request(d=>d.BirthDateInput=new("REIWA","元","05","01"))),"birth_date")=="2019-05-01","Reiwa first day");
Check(Code(Normalize(Request(d=>d.BirthDateInput=new("HEISEI","15","02","29"))))=="E-STU-005","impossible date no rollover");
Check(Code(Normalize(Request(d=>d.AdmissionDate="2026-02-30")))=="E-STU-005","ISO impossible date");
Check(Code(Normalize(Request(d=>d.AdmissionDate="2026-10-13")))=="E-DATE-002","future admission");
Check(Code(Normalize(Request(d=>d.AdmissionDate="2000-01-01")))=="E-STU-007","birth <= admission");
Check(Code(Normalize(Request(d=>d.ClassId=null)))=="E-STU-012","01/02 class required");
Check(Code(Normalize(Request(d=>d.ClassId=0)))=="E-COM-003","positive ID");
Check(Code(Normalize(Request(d=>d.EnrollmentEndDate="2026-04-02")))=="E-STU-008","01/02 end must be NULL");
Check(Code(Normalize(Request(d=>{d.EnrollmentStatusCode="03";d.ClassId=null;})))=="E-STU-008","03/04 end required");
Check(Good(Normalize(Request(d=>{d.EnrollmentStatusCode="03";d.ClassId=null;d.EnrollmentEndDate="2026-04-02";}))),"ended no class allowed");
Check(Code(Normalize(Request(d=>{d.PhoneNumber=null;d.EmailAddress=null;})))=="E-STU-018","at least one contact");
Check(Code(Normalize(Request(d=>d.EmergencyContactName="保護者")))=="E-STU-019","partial emergency rejected");
var emergency=Normalize(Request(d=>{d.EmergencyContactName="保護者";d.RelationshipCode="０１";d.EmergencyPhoneNumber="090-1234-5678";}));
Check(Good(emergency) && Value(emergency,"relationship_category")=="RELATIONSHIP","full emergency derives fixed category server-side");
Check(Code(Normalize(Request(d=>d.Remarks=new string('備',121))))=="E-STU-002","memo maximum");
Check(Code(Normalize(Request(d=>d.AddressLine1=new string('住',46))))=="E-STU-002","address maximum");
var cr=Request(d=>d.Remarks="a\r\nb\rc");var crRaw=NativeStoredProcedureClient.SerializeRaw(cr);
Check(crRaw.Contains("&#xD;"),"wire entitizes CR preserving pre-normalization length");
Check(Value(Normalize(cr),"remarks")=="a\nb\nc","memo line endings normalize");
Check(Code(Normalize(Request(d=>d.Remarks=new string('a',119)+"\r\n")))=="E-STU-002","CRLF counted before memo normalization");
Check(NativeNormalizer.Scalars("𠮷")==1,"scalar counter pair");
try {NativeNormalizer.Scalars("\ud800");Check(false,"unpaired surrogate");}catch(Exception){Check(true,"unpaired surrogate rejected");}
var extra=raw.Replace("</raw>","<name_key>forged</name_key></raw>");
Check(NativeNormalizer.NormalizeText(extra,business).Contains("E-COM-003"),"generated key cannot be provided");
Check(NativeNormalizer.NormalizeText(raw.Replace("<class_id>1</class_id>","<class_id>9223372036854775808</class_id>"),business).Contains("E-COM-003"),"malicious bigint overflow wire");
Check(NativeNormalizer.NormalizeText(raw.Replace("</raw>","<class_id>2</class_id></raw>"),business).Contains("E-COM-003"),"duplicate wire fields rejected");
Check(NativeNormalizer.NormalizeText("<!DOCTYPE raw [<!ENTITY x SYSTEM 'file:///never'>]><raw>&x;</raw>",business).Contains("E-COM-003"),"DTD/external entity prohibited");
Check(NativeNormalizer.ReasonText(new string('理',61)).Contains("E-STU-020"),"delete reason server maximum");
Check(NativeNormalizer.ReasonText("理由").Contains("ok=\"true\""),"delete reason normalized");
Check(NativeNormalizer.ReasonText("").Contains("E-STU-020"),"delete reason mandatory");
var classRaw=new ClassChange(null,null,2026,"００","ｃ-１","見本クラス","２０２６-０４-０１","2027-03-31",30,0,true,null);
XmlDocument Master(bool cls,string xml) {var d=new XmlDocument();d.LoadXml(NativeNormalizer.MasterText(xml,cls));return d;}
XmlDocument Class(ClassChange change,string reason=null)=>Master(true,NativeStoredProcedureClient.SerializeClass(change,reason));
XmlDocument CodeMaster(CodeChange change,string reason=null)=>Master(false,NativeStoredProcedureClient.SerializeCode(change,reason));
var cls=Class(classRaw);
Check(Good(cls) && Value(cls,"class_code")=="C-1" && Value(cls,"grade_code")=="00","class raw normalization");
Check(Good(Class(classRaw with {Capacity=null})),"class nullable unlimited capacity");
Check(Code(Class(classRaw with {Capacity=0}))=="E-MST-004","class capacity lower limit");
Check(Code(Class(classRaw with {Capacity=10000}))=="E-MST-004","class capacity upper limit");
Check(Code(Class(classRaw with {SchoolYear=1899}))=="E-DATE-003","class year lower limit");
Check(Code(Class(classRaw with {SchoolYear=9999}))=="E-DATE-003","class year upper limit");
Check(Code(Class(classRaw with {DisplayOrder=-1}))=="E-MST-004","class nonnegative display order");
Check(Code(Class(classRaw with {ClassName=new string('名',19)}))=="E-STU-002","class name raw scalar limit");
Check(Code(Class(classRaw with {ClassCode="-C"}))=="E-STU-003","class code fixed format");
Check(Code(Class(classRaw with {ValidFrom="2026-03-31"}))=="E-MST-004","class from inside year");
Check(Code(Class(classRaw with {ValidTo="2027-04-01"}))=="E-MST-004","class to inside year");
Check(Code(Class(classRaw with {ValidTo=null}))=="E-MST-004","class valid-to mandatory");
Check(Code(Class(classRaw,new string('理',61)))=="E-STU-002","master audit reason maximum");
var codeRaw=new CodeChange("RELATIONSHIP","９８",null,"追加続柄",0,true,"1900-01-01",null,null);
Check(Good(CodeMaster(codeRaw)) && Value(CodeMaster(codeRaw),"code_value")=="98","code raw NFKC digits");
Check(Code(CodeMaster(codeRaw with {CategoryId="UNKNOWN"}))=="E-MST-003","fixed code category");
Check(Code(CodeMaster(codeRaw with {CodeValue="X"}))=="E-STU-009","master code digits only");
Check(Code(CodeMaster(codeRaw with {CodeName=new string('名',13)}))=="E-STU-002","code name scalar maximum");
Check(Code(CodeMaster(codeRaw with {ValidFrom="1800-01-01"}))=="E-DATE-002","master date historical lower limit");
Check(Code(CodeMaster(codeRaw with {ValidTo="1899-12-31"}))=="E-DATE-002","master date lower limit on end");
Check(Code(CodeMaster(codeRaw with {ValidFrom="2000-01-02",ValidTo="2000-01-01"}))=="E-MST-004","master period ordering");
Check(Good(CodeMaster(codeRaw with {ValidFrom="2999-01-01"})),"master future validity permitted");
Check(NativeMessages.Resolve("E-STU-002","StudentName",8).Contains("氏名は8文字") && !NativeMessages.Resolve("E-STU-002","StudentName",8).Contains("{"),"Japanese field/max message");
Check(NativeMessages.Resolve("E-STU-020").Contains("削除理由"),"Japanese deletion reason message");
Check(NativeMessages.Resolve("E-COM-004",requestId:Guid.Empty).Contains(Guid.Empty.ToString()),"Japanese request/correlation message");
Check(NativeMessages.Resolve("E-STU-003","class_code").Contains("クラスコード") && NativeMessages.Resolve("E-STU-003","class_code").Contains("9文字"),"master code label and nine-character contract");
Check(Normalize(Request(d=>d.StudentNameKana=new string('カ',37))).DocumentElement.GetAttribute("max")=="36","raw kana failure carries 36 maximum");
Check(Normalize(Request(d=>d.StudentNameKana=new string('カ',19))).DocumentElement.GetAttribute("max")=="18","saved kana failure carries 18 maximum");
using(var disconnected=new Microsoft.Data.SqlClient.SqlConnection()) {
    var malformedClass=await NativeStoredProcedureClient.SaveClassAsync(disconnected,null,classRaw with {ClassName="\uD800"},Guid.NewGuid());
    Check(malformedClass.Outcome==Outcome.ValidationFailed && !malformedClass.Message.StartsWith("E-"),"malformed master class XML gives Japanese validation without opening DB");
    var malformedCode=await NativeStoredProcedureClient.SaveCodeAsync(disconnected,null,codeRaw with {CodeName="\uD800"},Guid.NewGuid());
    Check(malformedCode.Outcome==Outcome.ValidationFailed && !malformedCode.Message.StartsWith("E-"),"malformed master code XML gives Japanese validation without opening DB");
}
XmlDocument HintYear(string value) {
    var x=raw.Replace("<school_year>2026</school_year>",value is null?"<school_year null=\"true\" />":"<school_year>"+value+"</school_year>");
    var doc=new XmlDocument();doc.LoadXml(NativeNormalizer.NormalizeText(x,business));return doc;
}
Check(Code(HintYear("02026"))=="E-DATE-003","student year rejects leading-zero five-character raw");
Check(Code(HintYear("0000000000000002026"))=="E-DATE-003","student year raw is not generic nineteen-digit ID");
Check(Code(HintYear("226"))=="E-DATE-003","student year requires four ASCII digits");
Check(Code(HintYear("2e03"))=="E-DATE-003","student year rejects exponent notation");
Check(Code(HintYear("1899"))=="E-DATE-003" && Code(HintYear("9999"))=="E-DATE-003","student year range both ends");
Check(Good(HintYear("1900")) && Good(HintYear("9998")),"student year inclusive endpoints");
Check(Good(HintYear("２０２６")),"student year four fullwidth digits NFKC accepted");
Check(Code(HintYear("2026 "))=="E-DATE-003","student year raw maximum checked before trim");
Check(Good(HintYear(null)),"student year optional NULL preserved");
Check(Code(Master(true,NativeStoredProcedureClient.SerializeClass(classRaw).Replace("<school_year>2026</school_year>","<school_year>02026</school_year>")))=="E-DATE-003","master year rejects leading-zero raw");
var candidatesTable=new System.Data.DataTable();
candidatesTable.Columns.Add("student_no",typeof(string));candidatesTable.Columns.Add("student_name",typeof(string));candidatesTable.Columns.Add("birth_date",typeof(DateTime));candidatesTable.Columns.Add("class_name",typeof(string));
candidatesTable.Rows.Add("S2026-01","山田 太郎",new DateTime(2003,4,2),"１年Ａ組");
candidatesTable.Rows.Add("S2026-02","見本 花子",new DateTime(2019,5,1),DBNull.Value);
using(var fourFields=candidatesTable.CreateDataReader()) {
    Check(fourFields.Read(),"four-column duplicate fixture read");
    var candidate=NativeStoredProcedureClient.ReadDuplicateCandidate(fourFields);
    Check(candidate.StudentNo=="S2026-01" && candidate.StudentName=="山田 太郎" && candidate.BirthDateWareki.Contains("平成15年") && candidate.ClassName=="１年Ａ組","duplicate mapper requires only four permitted fields and displays wareki");
    Check(candidate.StudentId==0 && candidate.StudentNameKana=="" && candidate.SchoolYear is null && candidate.GradeName is null && candidate.ClassCode is null && candidate.EnrollmentStatusName is null && typeof(StudentRow).GetProperty("Address") is null && typeof(StudentRow).GetProperty("PhoneNumber") is null && typeof(StudentRow).GetProperty("UpdatedAt") is null,"duplicate mapper has no address/contact/status/history/technical data");
    Check(fourFields.Read() && NativeStoredProcedureClient.ReadDuplicateCandidate(fourFields).ClassName is null,"duplicate mapper preserves no-class NULL");
}
Console.WriteLine($"PASS: {checks} native normalization/wire boundary assertions");
