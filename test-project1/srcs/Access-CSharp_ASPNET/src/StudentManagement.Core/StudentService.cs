using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace StudentManagement.Core;

// Evidence: exported clsStudentService, modStudentRules, modStudentSearch,
// modMasterMaintenance, clsConfirmation, modSecurity. Source SHA in build/generation/inputs.json.
public sealed class StudentService(IStudentRepository repository, Func<DateTime>? utcClock=null)
{
    private readonly Func<DateTime> clock=utcClock??(()=>DateTime.UtcNow);
    private readonly object confirmationGate=new();
    private readonly Dictionary<string,Confirmation> confirmations=new(StringComparer.Ordinal);
    private sealed record Confirmation(string Owner,Role Role,string FormId,int? Target,int? Version,string Draft,string Candidates,DateTime Expires);
    private static readonly (string Property,string Column)[] savedFields = [
        (nameof(Student.StudentNo),"student_no"),(nameof(Student.StudentName),"student_name"),(nameof(Student.StudentNameKana),"student_name_kana"),
        (nameof(Student.BirthDate),"birth_date"),(nameof(Student.GenderCode),"gender_code"),(nameof(Student.PostalCode),"postal_code"),
        (nameof(Student.PrefectureCode),"prefecture_code"),(nameof(Student.AddressLine1),"address_line1"),(nameof(Student.AddressLine2),"address_line2"),
        (nameof(Student.PhoneNumber),"phone_number"),(nameof(Student.EmailAddress),"email_address"),(nameof(Student.AdmissionDate),"admission_date"),
        (nameof(Student.EnrollmentStatusCode),"enrollment_status_code"),(nameof(Student.EnrollmentEndDate),"enrollment_end_date"),(nameof(Student.ClassId),"class_id"),
        (nameof(Student.EmergencyContactName),"emergency_contact_name"),(nameof(Student.RelationshipCode),"relationship_code"),
        (nameof(Student.EmergencyPhoneNumber),"emergency_phone_number"),(nameof(Student.Remarks),"remarks")];
    public string BusinessDay => clock().AddHours(9).ToString("yyyy-MM-dd",CultureInfo.InvariantCulture);
    public Actor ResolveActor(string userName) => repository.Execute(false,s=>
    {
        if(TextRules.ScalarCount(userName)>64 || !Enum.TryParse<Role>(s.FindRole(userName),false,out var role)||!Enum.IsDefined(role))throw TextRules.Error("E-COM-001");
        return new Actor(userName,role);
    });
    private T Run<T>(bool write,Actor actor,Role required,Func<IStudentSession,T> action) => repository.Execute(write,s=>
    {
        var role=s.FindRole(actor.UserId);
        if(string.IsNullOrEmpty(actor.UserId)||TextRules.ScalarCount(actor.UserId)>64||role!=actor.Role.ToString()||!Enum.IsDefined(actor.Role))throw TextRules.Error("E-COM-001");
        if(actor.Role<required)throw TextRules.Error("E-COM-002");
        return action(s);
    });
    public Student Get(int id,Actor actor) => Run(false,actor,Role.Reader,s=>s.Students().FirstOrDefault(x=>x.StudentId==TextRules.PositiveId(id)&&!x.IsDeleted)??throw TextRules.Error("E-STU-103"));
    public IReadOnlyList<ClassItem> GetClasses(Actor actor) => Run(false,actor,Role.Reader,s=>s.Classes().OrderByDescending(x=>x.SchoolYear).ThenBy(x=>x.DisplayOrder).ThenBy(x=>x.ClassCode,StringComparer.Ordinal).ThenBy(x=>x.ClassId).ToArray());
    public IReadOnlyList<CodeItem> GetCodes(string category,Actor actor,string? currentValue=null) => Run(false,actor,Role.Reader,s=>s.Codes().Where(x=>x.CategoryId==category && (IsCodeActive(s,x,BusinessDay)||x.CodeValue==currentValue)).OrderBy(x=>x.DisplayOrder).ThenBy(x=>x.CodeValue,StringComparer.Ordinal).ToArray());
    public IReadOnlyList<CodeItem> GetAllCodes(Actor actor) => Run(false,actor,Role.Admin,s=>s.Codes().OrderBy(x=>x.CategoryId,StringComparer.Ordinal).ThenBy(x=>x.DisplayOrder).ThenBy(x=>x.CodeValue,StringComparer.Ordinal).ToArray());
    public IReadOnlyList<CodeCategory> GetCategories(Actor actor) => Run(false,actor,Role.Reader,s=>s.Categories());
    public int GetOccupancy(int classId,Actor actor) => Run(false,actor,Role.Reader,s=>Occupancy(s,TextRules.PositiveId(classId),0));
    public SearchResult Search(SearchCriteria raw,Actor actor,string sortKey="studentNo",string direction="asc") => Run(false,actor,Role.Reader,s=>
    {
        var no=TextRules.Text(raw.StudentNo,15,15,"number")??"";
        var name=TextRules.Text(raw.Name,8,160,"nameKey")??"";
        if(no!=""&&!TextRules.Match(no,"^[A-Z0-9][A-Z0-9-]{0,14}$"))throw TextRules.Error("E-STU-003");
        if(raw.ClassId is not null && !s.Classes().Any(x=>x.ClassId==TextRules.PositiveId(raw.ClassId.Value)))throw TextRules.Error("E-STU-010");
        if(direction is not ("asc" or "desc")||sortKey is not ("studentNo" or "name" or "admissionDate" or "updatedAt"))throw TextRules.Error("E-SRC-002");
        var statuses=new[]{raw.Status01?"01":null,raw.Status02?"02":null,raw.Status03?"03":null,raw.Status04?"04":null}.Where(x=>x is not null).ToArray();
        foreach(var status in statuses)CheckCode(s,"ENROLLMENT_STATUS",status,status,"1900-01-01");
        var rows=s.Students().Where(x=>!x.IsDeleted && (raw.ClassId is null||x.ClassId==raw.ClassId) &&
            (statuses.Length==0||statuses.Contains(x.EnrollmentStatusCode,StringComparer.Ordinal)) &&
            x.StudentNo.StartsWith(no,StringComparison.Ordinal)&&x.NameKey.Contains(name,StringComparison.Ordinal)).Take(10001).ToArray();
        if(rows.Length>10000)return new SearchResult("LimitExceeded","W-SRC-001",10001,[],clock());
        IOrderedEnumerable<Student> ordered;
        if(sortKey=="updatedAt")ordered=direction=="asc"?rows.OrderBy(x=>x.UpdatedAt):rows.OrderByDescending(x=>x.UpdatedAt);
        else
        {
            Func<Student,string> key=sortKey switch{"name"=>x=>x.NameKey,"admissionDate"=>x=>x.AdmissionDate,_=>x=>x.StudentNo};
            ordered=direction=="asc"?rows.OrderBy(key,StringComparer.Ordinal):rows.OrderByDescending(key,StringComparer.Ordinal);
        }
        var found=ordered.ThenBy(x=>x.StudentId).Select(x=>
        {
            var c=s.Classes().FirstOrDefault(c=>c.ClassId==x.ClassId);
            return new SearchRow(x,ClassDisplay(c,BusinessDay),CodeName(s,"GRADE",c?.GradeCode),CodeName(s,"ENROLLMENT_STATUS",x.EnrollmentStatusCode),c?.SchoolYear);
        }).ToArray();
        return new SearchResult("Found",found.Length==0?"I-SRC-001":"",found.Length,found,clock());
    });
    public SaveResult Save(StudentDraft raw,int? targetId,int? expectedVersion,Actor actor,string formId,string? confirmationToken=null,bool confirmed=false)
    {
        lock(confirmationGate)
        {
            foreach(var key in confirmations.Where(x=>x.Value.Expires<=clock()).Select(x=>x.Key).ToArray())confirmations.Remove(key);
            var result=Run(true,actor,Role.Staff,s=>
            {
                var utc=clock();var day=utc.AddHours(9).ToString("yyyy-MM-dd",CultureInfo.InvariantCulture);
                var d=NormalizeDraft(raw,day);var reason=TextRules.Text(raw.OperationReason,60,60,"memo");
                Student? old=null;
                if(targetId is not null)
                {
                    TextRules.PositiveId(targetId.Value);
                    if(expectedVersion is null)throw TextRules.Error("E-COM-003");
                    TextRules.PositiveId(expectedVersion.Value);
                    old=s.Students().FirstOrDefault(x=>x.StudentId==targetId&&!x.IsDeleted)??throw TextRules.Error("E-STU-103");
                    if(old.RowVersion!=expectedVersion)throw TextRules.Error("E-STU-105");
                    if(old.StudentNo!=d.StudentNo)throw TextRules.Error("E-STU-104");
                    if(old.EnrollmentStatusCode is "03" or "04" && old.EnrollmentStatusCode!=d.EnrollmentStatusCode)
                    {if(actor.Role!=Role.Admin)throw TextRules.Error("E-COM-002");if(reason is null)throw TextRules.Error("E-STU-106");}
                }
                else if(expectedVersion is not null)throw TextRules.Error("E-COM-003");
                if(s.Students().Any(x=>x.StudentId!=targetId&&x.StudentNo==d.StudentNo))throw TextRules.Error("E-STU-101");
                var warning=CheckMasters(s,d,old,raw,day);
                if(old is not null&&SameDraft(d,old))return new SaveResult("NoChange","I-STU-004",old.StudentId,old.RowVersion,warning);
                var duplicates=s.Students().Where(x=>!x.IsDeleted&&x.StudentId!=targetId&&x.BirthDate==d.BirthDate&&(x.NameKey==d.NameKey||x.KanaKey==d.KanaKey)).OrderBy(x=>x.StudentId).ToArray();
                var digest=string.Join(";",duplicates.Select(x=>$"{x.StudentId}:{x.RowVersion}"));
                var fingerprint=Fingerprint(d);
                if(duplicates.Length>0||!string.IsNullOrEmpty(confirmationToken))
                {
                    var valid=confirmed&&confirmationToken is not null&&confirmations.TryGetValue(confirmationToken,out var token)&&token.Owner==actor.UserId&&token.Role==actor.Role&&token.FormId==formId&&token.Target==targetId&&token.Version==expectedVersion&&token.Draft==fingerprint&&token.Candidates==digest&&utc<token.Expires;
                    if(!valid)
                    {
                        var newToken=Convert.ToHexString(RandomNumberGenerator.GetBytes(32));
                        confirmations[newToken]=new Confirmation(actor.UserId,actor.Role,formId,targetId,expectedVersion,fingerprint,digest,utc.AddMinutes(10));
                        var candidates=duplicates.Select(x=>new DuplicateCandidate(x.StudentId,x.StudentNo,x.StudentName,x.BirthDate,ClassDisplay(s.Classes().FirstOrDefault(c=>c.ClassId==x.ClassId),day))).ToArray();
                        return new SaveResult("ConfirmationRequired",confirmed?"W-STU-102":"W-STU-101",Warning:warning,ConfirmationToken:newToken,Candidates:candidates);
                    }
                    if(reason is null)throw TextRules.Error("E-STU-107");
                }
                var version=old is null?1:NextVersion(old.RowVersion);
                d=d with {StudentId=old?.StudentId??0,RowVersion=version,CreatedAt=old?.CreatedAt??utc,CreatedBy=old?.CreatedBy??actor.UserId,UpdatedAt=utc,UpdatedBy=actor.UserId};
                var saved=s.WriteStudent(d,old?.RowVersion);
                var changed=ChangedStudentColumns(d,old);
                s.AppendAudit(new AuditEntry("m_student",saved.StudentId.ToString(CultureInfo.InvariantCulture),old is null?"CREATE":"UPDATE",old?.RowVersion,version,JsonSerializer.Serialize(changed),actor.UserId,utc,reason,duplicates.Length>0));
                return new SaveResult("Saved",old is null?"I-STU-001":"I-STU-002",saved.StudentId,version,warning);
            });
            if(result.Kind=="Saved"&&confirmationToken is not null)confirmations.Remove(confirmationToken);
            return result;
        }
    }
    public SaveResult Delete(int targetId,int expectedVersion,string? reasonRaw,bool explicitConfirm,Actor actor) => Run(true,actor,Role.Admin,s=>
    {
        TextRules.PositiveId(targetId);TextRules.PositiveId(expectedVersion);
        var reason=TextRules.Text(reasonRaw,60,60,"memo");
        if(!explicitConfirm||reason is null)throw TextRules.Error("E-STU-020");
        var old=s.Students().FirstOrDefault(x=>x.StudentId==targetId&&!x.IsDeleted)??throw TextRules.Error("E-STU-103");
        if(old.RowVersion!=expectedVersion)throw TextRules.Error("E-STU-105");
        var version=NextVersion(old.RowVersion);var utc=clock();
        s.WriteStudent(old with {IsDeleted=true,DeletedAt=utc,DeletedBy=actor.UserId,DeleteReason=reason,UpdatedAt=utc,UpdatedBy=actor.UserId,RowVersion=version},expectedVersion);
        s.AppendAudit(new AuditEntry("m_student",targetId.ToString(CultureInfo.InvariantCulture),"DELETE",old.RowVersion,version,"[\"is_deleted\",\"deleted_at\",\"deleted_by\",\"delete_reason\",\"updated_at\",\"updated_by\",\"row_version\"]",actor.UserId,utc,reason,false));
        return new SaveResult("Saved","I-STU-003",targetId,version);
    });
    public SaveResult MaintainClass(ClassDraft raw,int? targetId,int? expectedVersion,Actor actor) => Run(true,actor,Role.Admin,s=>
    {
        var year=TextRules.Integer(raw.SchoolYear,true);if(year is <1900 or >9998)throw TextRules.Error("E-DATE-003");
        var grade=TextRules.Text(raw.GradeCode,2,2,"code");var code=TextRules.Text(raw.ClassCode,9,9,"number");var name=TextRules.Text(raw.ClassName,18,18,"text");
        var from=JapaneseDate.StrictIso(raw.ValidFrom,true)!;var to=JapaneseDate.StrictIso(raw.ValidTo,true)!;
        var capacity=string.IsNullOrEmpty(raw.Capacity)?(int?)null:TextRules.PositiveId(raw.Capacity);
        if(grade is null||code is null||name is null)throw TextRules.Error("E-STU-001");
        if(!TextRules.Match(code,"^[A-Z0-9][A-Z0-9-]{0,8}$"))throw TextRules.Error("E-MST-002");
        if(capacity>9999||string.CompareOrdinal(from,$"{year:0000}-04-01")<0||string.CompareOrdinal(to,$"{year+1:0000}-03-31")>0||string.CompareOrdinal(from,to)>0)throw TextRules.Error("E-MST-004");
        ClassItem? old=null;
        if(targetId is not null)
        {
            TextRules.PositiveId(targetId.Value);old=s.Classes().FirstOrDefault(x=>x.ClassId==targetId)??throw TextRules.Error("E-STU-010");
            if(expectedVersion is null||old.RowVersion!=expectedVersion)throw TextRules.Error("E-STU-105");
            var refs=s.Students().Count(x=>x.ClassId==targetId);var seats=Occupancy(s,targetId.Value,0);
            if(old.SchoolYear!=year||old.ClassCode!=code||(refs>0&&old.GradeCode!=grade))throw TextRules.Error("E-MST-003");
            if(seats>0&&(!raw.IsActive||string.CompareOrdinal(BusinessDay,from)<0||string.CompareOrdinal(BusinessDay,to)>0)||capacity<seats)throw TextRules.Error("E-MST-004");
        }
        else if(expectedVersion is not null)throw TextRules.Error("E-COM-003");
        CheckCode(s,"GRADE",grade,old?.GradeCode,BusinessDay);
        if(s.Classes().Any(x=>x.ClassId!=targetId&&x.SchoolYear==year&&x.ClassCode==code))throw TextRules.Error("E-MST-002");
        var warning=s.Classes().Any(x=>x.ClassId!=targetId&&x.SchoolYear==year&&x.GradeCode==grade&&x.ClassName==name)?"W-MST-001":null;
        var utc=clock();var d=new ClassItem {ClassId=old?.ClassId??0,SchoolYear=year,GradeCode=grade,ClassCode=code,ClassName=name,ValidFrom=from,ValidTo=to,Capacity=capacity,
            DisplayOrder=TextRules.Integer(raw.DisplayOrder),IsActive=raw.IsActive,Remarks=TextRules.Text(raw.Remarks,120,120,"memo"),CreatedAt=old?.CreatedAt??utc,CreatedBy=old?.CreatedBy??actor.UserId,
            UpdatedAt=utc,UpdatedBy=actor.UserId,RowVersion=old?.RowVersion??1};
        if(old is not null&&d with {UpdatedAt=old.UpdatedAt,UpdatedBy=old.UpdatedBy,RowVersion=old.RowVersion}==old)return new SaveResult("NoChange","I-STU-004",old.ClassId,old.RowVersion,warning);
        d=d with {RowVersion=old is null?1:NextVersion(old.RowVersion)};
        var saved=s.WriteClass(d,old?.RowVersion);
        s.AppendAudit(new AuditEntry("m_class",saved.ClassId.ToString(CultureInfo.InvariantCulture),MasterOperation(old?.IsActive,d.IsActive),old?.RowVersion,d.RowVersion,JsonSerializer.Serialize(ChangedClassColumns(d,old)),actor.UserId,utc,null,false));
        return new SaveResult("Saved","I-STU-002",saved.ClassId,d.RowVersion,warning);
    });
    public SaveResult MaintainCode(string category,string code,CodeDraft raw,int? expectedVersion,Actor actor) => Run(true,actor,Role.Admin,s=>
    {
        category=TextRules.Text(category,24,24,"code")??"";code=TextRules.Text(code,10,10,"code")??"";
        var cat=s.Categories().FirstOrDefault(x=>x.CategoryId==category)??throw TextRules.Error("E-MST-001");
        if(code.Length!=cat.CodeLength||!TextRules.Match(code,"^[0-9]+$"))throw TextRules.Error("E-STU-009");
        var name=TextRules.Text(raw.CodeName,12,12,"text");var from=JapaneseDate.StrictIso(raw.ValidFrom,true)!;var to=JapaneseDate.StrictIso(raw.ValidTo,false);
        if(name is null||string.CompareOrdinal(from,"1900-01-01")<0)throw TextRules.Error("E-STU-001");
        if(to is not null&&string.CompareOrdinal(to,from)<0)throw TextRules.Error("E-MST-004");
        var old=s.Codes().FirstOrDefault(x=>x.CategoryId==category&&x.CodeValue==code);
        if(old is null){if(expectedVersion is not null||!cat.AllowAdd)throw TextRules.Error("E-MST-003");}
        else
        {
            if(expectedVersion is null)throw TextRules.Error("E-MST-002");
            if(old.RowVersion!=TextRules.PositiveId(expectedVersion.Value))throw TextRules.Error("E-STU-105");
            if(old.IsProtected&&(!raw.IsActive||to is not null||string.CompareOrdinal(from,old.ValidFrom)>0))throw TextRules.Error("E-MST-003");
        }
        var utc=clock();var d=new CodeItem {CategoryId=category,CodeValue=code,CodeName=name,DisplayOrder=TextRules.Integer(raw.DisplayOrder),IsActive=raw.IsActive,ValidFrom=from,ValidTo=to,
            IsProtected=old?.IsProtected??false,Remarks=TextRules.Text(raw.Remarks,120,120,"memo"),CreatedAt=old?.CreatedAt??utc,CreatedBy=old?.CreatedBy??actor.UserId,
            UpdatedAt=utc,UpdatedBy=actor.UserId,RowVersion=old?.RowVersion??1};
        if(old is not null&&d with {UpdatedAt=old.UpdatedAt,UpdatedBy=old.UpdatedBy,RowVersion=old.RowVersion}==old)return new SaveResult("NoChange","I-STU-004",RowVersion:old.RowVersion);
        d=d with {RowVersion=old is null?1:NextVersion(old.RowVersion)};
        s.WriteCode(d,old?.RowVersion);
        s.AppendAudit(new AuditEntry("m_code",$"{category}:{code}",MasterOperation(old?.IsActive,d.IsActive),old?.RowVersion,d.RowVersion,JsonSerializer.Serialize(ChangedCodeColumns(d,old)),actor.UserId,utc,null,false));
        return new SaveResult("Saved","I-STU-002",RowVersion:d.RowVersion);
    });
    public static Student NormalizeDraft(StudentDraft raw,string today)
    {
        string? T(string? value,int r,int n,string kind,string field)=>TextRules.Text(value,r,n,kind,field);
        var d=new Student {StudentNo=T(raw.StudentNo,15,15,"number","student_no")!,StudentName=T(raw.StudentName,8,8,"text","student_name")!,StudentNameKana=T(raw.StudentNameKana,36,18,"kana","student_name_kana")!,
            BirthDate=JapaneseDate.ParseBirthDate(raw.BirthEra,raw.BirthYear,raw.BirthMonth,raw.BirthDay,today),GenderCode=T(raw.GenderCode,1,1,"code","gender_code")!,PostalCode=T(raw.PostalCode,10,7,"postal","postal_code")!,
            PrefectureCode=T(raw.PrefectureCode,2,2,"code","prefecture_code")!,AddressLine1=T(raw.AddressLine1,45,45,"text","address_line1")!,AddressLine2=T(raw.AddressLine2,45,45,"text","address_line2"),
            PhoneNumber=T(raw.PhoneNumber,20,16,"phone","phone_number"),EmailAddress=T(raw.EmailAddress,60,60,"email","email_address"),AdmissionDate=JapaneseDate.StrictIso(raw.AdmissionDate,true)!,
            EnrollmentStatusCode=T(raw.EnrollmentStatusCode,2,2,"code","enrollment_status_code")!,EnrollmentEndDate=JapaneseDate.StrictIso(raw.EnrollmentEndDate,false),ClassId=raw.ClassId,
            EmergencyContactName=T(raw.EmergencyContactName,8,8,"text","emergency_contact_name"),RelationshipCode=T(raw.RelationshipCode,2,2,"code","relationship_code"),
            EmergencyPhoneNumber=T(raw.EmergencyPhoneNumber,20,16,"phone","emergency_phone_number"),Remarks=T(raw.Remarks,120,120,"memo","remarks")};
        foreach(var property in new[]{nameof(Student.StudentNo),nameof(Student.StudentName),nameof(Student.StudentNameKana),nameof(Student.GenderCode),nameof(Student.PostalCode),nameof(Student.PrefectureCode),nameof(Student.AddressLine1),nameof(Student.EnrollmentStatusCode)})
            if(Value(d,property) is null)throw TextRules.Error("E-STU-001",savedFields.First(x=>x.Property==property).Column);
        if(!TextRules.Match(d.StudentNo,"^[A-Z0-9][A-Z0-9-]{0,14}$"))throw TextRules.Error("E-STU-003");
        if(!TextRules.Match(d.GenderCode,"^[0-9]$")||!TextRules.Match(d.PrefectureCode,"^[0-9]{2}$")||!TextRules.Match(d.EnrollmentStatusCode,"^0[1-4]$"))throw TextRules.Error("E-STU-009");
        if(!TextRules.Match(d.PostalCode,"^[0-9]{7}$"))throw TextRules.Error("E-STU-015");
        foreach(var pair in new[]{(d.PhoneNumber,"phone_number"),(d.EmergencyPhoneNumber,"emergency_phone_number")})if(pair.Item1 is not null&&!TextRules.Match(pair.Item1,"^(0[0-9]{9,10}|\\+[1-9][0-9]{6,14})$"))throw TextRules.Error("E-STU-016",pair.Item2);
        if(d.EmailAddress is not null&&!TextRules.Match(d.EmailAddress,"^[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+(\\.[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+)*@[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?(\\.[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$"))throw TextRules.Error("E-STU-017");
        if(d.PhoneNumber is null&&d.EmailAddress is null&&d.EmergencyPhoneNumber is null)throw TextRules.Error("E-STU-018");
        if((d.EmergencyContactName is null)!=(d.RelationshipCode is null)||(d.RelationshipCode is null)!=(d.EmergencyPhoneNumber is null))throw TextRules.Error("E-STU-019");
        if(d.RelationshipCode is not null&&!TextRules.Match(d.RelationshipCode,"^[0-9]{2}$"))throw TextRules.Error("E-STU-009");
        if(string.CompareOrdinal(d.BirthDate,d.AdmissionDate)>0||string.CompareOrdinal(d.AdmissionDate,"1900-01-01")<0||string.CompareOrdinal(d.AdmissionDate,today)>0)throw TextRules.Error("E-STU-007");
        if(d.ClassId is not null)TextRules.PositiveId(d.ClassId.Value);
        if(d.EnrollmentStatusCode is "01" or "02")
        {if(d.ClassId is null)throw TextRules.Error("E-STU-012");if(d.EnrollmentEndDate is not null)throw TextRules.Error("E-STU-008");}
        else if(d.EnrollmentEndDate is null||string.CompareOrdinal(d.EnrollmentEndDate,d.AdmissionDate)<0||string.CompareOrdinal(d.EnrollmentEndDate,today)>0)throw TextRules.Error("E-STU-008");
        return d with {NameKey=TextRules.Text(d.StudentName,8,160,"nameKey")!,KanaKey=TextRules.WithoutWhite(d.StudentNameKana)};
    }
    private static string? CheckMasters(IStudentSession s,Student d,Student? old,StudentDraft raw,string day)
    {
        CheckCode(s,"GENDER",d.GenderCode,old?.GenderCode,day);CheckCode(s,"PREFECTURE",d.PrefectureCode,old?.PrefectureCode,day);
        CheckCode(s,"ENROLLMENT_STATUS",d.EnrollmentStatusCode,old?.EnrollmentStatusCode,day);CheckCode(s,"RELATIONSHIP",d.RelationshipCode,old?.RelationshipCode,day);
        int? year=null;string? grade=null;
        if(!string.IsNullOrEmpty(raw.SchoolYear))
        {var y=TextRules.Nfkc(raw.SchoolYear);if(!TextRules.Match(y,"^[0-9]{4}$")||!int.TryParse(y,out var n)||n is <1900 or >9998)throw TextRules.Error("E-DATE-003");year=n;}
        if(!string.IsNullOrEmpty(raw.GradeCode)){grade=TextRules.Nfkc(raw.GradeCode);if(!TextRules.Match(grade,"^[0-9]{2}$"))throw TextRules.Error("E-STU-009");}
        if(d.ClassId is null)return null;
        var c=s.Classes().FirstOrDefault(x=>x.ClassId==d.ClassId)??throw TextRules.Error("E-STU-010");
        if(year is not null&&year!=c.SchoolYear||grade is not null&&grade!=c.GradeCode)throw TextRules.Error("E-STU-014");
        var oldSeat=Seat(old);var newSeat=Seat(d);
        if(newSeat is not null)
        {
            if(oldSeat!=newSeat)
            {if(!IsClassActive(c,day))throw TextRules.Error("E-STU-013");if(c.Capacity is not null&&Occupancy(s,newSeat.Value,d.StudentId)+1>c.Capacity)throw TextRules.Error("E-STU-102");}
            else if(!IsClassActive(c,day))return "W-STU-106";
        }
        else if(old is null||old.ClassId!=d.ClassId||old.AdmissionDate!=d.AdmissionDate||old.EnrollmentEndDate!=d.EnrollmentEndDate||old.EnrollmentStatusCode!=d.EnrollmentStatusCode)
            if(string.CompareOrdinal(c.ValidFrom,d.EnrollmentEndDate)>0||string.CompareOrdinal(c.ValidTo,d.AdmissionDate)<0)throw TextRules.Error("E-STU-108");
        return null;
    }
    private static int? Seat(Student? s)=>s?.EnrollmentStatusCode is "01" or "02"?s.ClassId:null;
    private static int Occupancy(IStudentSession s,int classId,int excludeId)=>s.Students().Count(x=>!x.IsDeleted&&x.StudentId!=excludeId&&Seat(x)==classId);
    private static bool IsClassActive(ClassItem c,string day)=>c.IsActive&&string.CompareOrdinal(c.ValidFrom,day)<=0&&string.CompareOrdinal(c.ValidTo,day)>=0;
    private static bool IsCodeActive(IStudentSession s,CodeItem c,string day)=>c.IsActive&&s.Categories().Any(x=>x.CategoryId==c.CategoryId&&x.IsActive)&&string.CompareOrdinal(c.ValidFrom,day)<=0&&(c.ValidTo is null||string.CompareOrdinal(c.ValidTo,day)>=0);
    private static void CheckCode(IStudentSession s,string category,string? value,string? oldValue,string day)
    {if(value is null)return;var c=s.Codes().FirstOrDefault(x=>x.CategoryId==category&&x.CodeValue==value)??throw TextRules.Error("E-STU-009",category);if(!IsCodeActive(s,c,day)&&value!=oldValue)throw TextRules.Error("E-STU-011",category);}
    private static string ClassDisplay(ClassItem? c,string day)=>c is null?"－":$"{c.ClassCode} {c.ClassName}"+(IsClassActive(c,day)?"":" [停止・期間外]");
    private static string CodeName(IStudentSession s,string category,string? value)=>value is null?"－":s.Codes().FirstOrDefault(x=>x.CategoryId==category&&x.CodeValue==value)?.CodeName??$"[未定義: {value}]";
    private static int NextVersion(int n)=>n==int.MaxValue?throw TextRules.Error("E-COM-004"):n+1;
    private static object? Value(Student s,string property)=>typeof(Student).GetProperty(property)!.GetValue(s);
    private static bool SameDraft(Student a,Student b)=>savedFields.All(p=>Equals(Value(a,p.Property),Value(b,p.Property)))&&a.NameKey==b.NameKey&&a.KanaKey==b.KanaKey;
    private static string Fingerprint(Student s)=>Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(JsonSerializer.Serialize(savedFields.Select(p=>Value(s,p.Property))))));
    private static string MasterOperation(bool? old,bool active)=>old is null?"CREATE":old.Value&&!active?"DISABLE":!old.Value&&active?"ENABLE":"UPDATE";
    private static string[] ChangedStudentColumns(Student d,Student? old)
    {
        var columns=savedFields.Where(p=>old is null||!Equals(Value(d,p.Property),Value(old,p.Property))).Select(p=>p.Column).ToList();
        if(old is null||d.NameKey!=old.NameKey)columns.Add("name_key");
        if(old is null||d.KanaKey!=old.KanaKey)columns.Add("kana_key");
        if(old is null)columns.AddRange(["gender_category","prefecture_category","enrollment_category","relationship_category","is_deleted","created_at","created_by"]);
        else if((old.RelationshipCode is null)!=(d.RelationshipCode is null))columns.Add("relationship_category");
        columns.AddRange(["row_version","updated_at","updated_by"]);
        return columns.ToArray();
    }
    private static string[] ChangedClassColumns(ClassItem d,ClassItem? old)
    {
        var fields=new(string Column,object? Current,object? Original)[]{("school_year",d.SchoolYear,old?.SchoolYear),("grade_category","GRADE",old is null?null:"GRADE"),("grade_code",d.GradeCode,old?.GradeCode),
            ("class_code",d.ClassCode,old?.ClassCode),("class_name",d.ClassName,old?.ClassName),("valid_from",d.ValidFrom,old?.ValidFrom),("valid_to",d.ValidTo,old?.ValidTo),
            ("capacity",d.Capacity,old?.Capacity),("display_order",d.DisplayOrder,old?.DisplayOrder),("is_active",d.IsActive,old?.IsActive),("remarks",d.Remarks,old?.Remarks)};
        return fields.Where(x=>old is null||!Equals(x.Current,x.Original)).Select(x=>x.Column).Concat(["row_version","updated_at","updated_by"]).ToArray();
    }
    private static string[] ChangedCodeColumns(CodeItem d,CodeItem? old)
    {
        var fields=new(string Column,object? Current,object? Original)[]{("code_name",d.CodeName,old?.CodeName),("display_order",d.DisplayOrder,old?.DisplayOrder),("is_active",d.IsActive,old?.IsActive),
            ("valid_from",d.ValidFrom,old?.ValidFrom),("valid_to",d.ValidTo,old?.ValidTo),("remarks",d.Remarks,old?.Remarks)};
        return fields.Where(x=>old is null||!Equals(x.Current,x.Original)).Select(x=>x.Column).Concat(["row_version","updated_at","updated_by"]).ToArray();
    }
}
