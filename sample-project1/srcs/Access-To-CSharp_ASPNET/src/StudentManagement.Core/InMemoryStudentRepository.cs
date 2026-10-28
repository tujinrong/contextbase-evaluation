using System.Text.Json;

namespace StudentManagement.Core;

/// <summary>Explicit test-only provider. Production never falls back to this store.</summary>
public sealed class InMemoryStudentRepository : IStudentRepository
{
    private readonly object gate=new();
    private State state;
    private sealed class State : IStudentSession
    {
        public List<Student> StudentRows=[];
        public List<ClassItem> ClassRows=[];
        public List<CodeItem> CodeRows=[];
        public List<CodeCategory> CategoryRows=[];
        public Dictionary<string,string> Roles=new(StringComparer.Ordinal);
        public List<AuditEntry> AuditRows=[];
        public State Clone()=>new(){StudentRows=[..StudentRows],ClassRows=[..ClassRows],CodeRows=[..CodeRows],CategoryRows=[..CategoryRows],Roles=new(Roles,StringComparer.Ordinal),AuditRows=[..AuditRows]};
        public string? FindRole(string userId)=>Roles.GetValueOrDefault(userId);
        public IReadOnlyList<Student> Students()=>StudentRows.ToArray();
        public IReadOnlyList<ClassItem> Classes()=>ClassRows.ToArray();
        public IReadOnlyList<CodeItem> Codes()=>CodeRows.ToArray();
        public IReadOnlyList<CodeCategory> Categories()=>CategoryRows.ToArray();
        public Student WriteStudent(Student value,int? expectedVersion)
        {
            var old=StudentRows.FirstOrDefault(x=>x.StudentId==value.StudentId);
            if(old is null){if(expectedVersion is not null)throw TextRules.Error("E-STU-105");value=value with{StudentId=StudentRows.Count==0?1:checked(StudentRows.Max(x=>x.StudentId)+1)};}
            else {if(old.RowVersion!=expectedVersion)throw TextRules.Error("E-STU-105");StudentRows.Remove(old);}
            if(StudentRows.Any(x=>x.StudentNo==value.StudentNo))throw TextRules.Error("E-STU-101");
            StudentRows.Add(value);return value;
        }
        public ClassItem WriteClass(ClassItem value,int? expectedVersion)
        {
            var old=ClassRows.FirstOrDefault(x=>x.ClassId==value.ClassId);
            if(old is null){if(expectedVersion is not null)throw TextRules.Error("E-STU-105");value=value with {ClassId=ClassRows.Count==0?1:checked(ClassRows.Max(x=>x.ClassId)+1)};}
            else{if(old.RowVersion!=expectedVersion)throw TextRules.Error("E-STU-105");ClassRows.Remove(old);}
            ClassRows.Add(value);return value;
        }
        public CodeItem WriteCode(CodeItem value,int? expectedVersion)
        {
            var old=CodeRows.FirstOrDefault(x=>x.CategoryId==value.CategoryId&&x.CodeValue==value.CodeValue);
            if(old is null){if(expectedVersion is not null)throw TextRules.Error("E-STU-105");}
            else{if(old.RowVersion!=expectedVersion)throw TextRules.Error("E-STU-105");CodeRows.Remove(old);}
            CodeRows.Add(value);return value;
        }
        public void AppendAudit(AuditEntry value)=>AuditRows.Add(value);
    }
    public InMemoryStudentRepository(IEnumerable<CodeCategory> categories,IEnumerable<CodeItem> codes,IEnumerable<ClassItem> classes,IEnumerable<Student> students,IReadOnlyDictionary<string,string> roles)
    {state=new(){CategoryRows=[..categories],CodeRows=[..codes],ClassRows=[..classes],StudentRows=[..students],Roles=new(roles,StringComparer.Ordinal)};}
    public T Execute<T>(bool write,Func<IStudentSession,T> operation)
    {
        lock(gate)
        {
            var work=state.Clone();var result=operation(work);
            if(write)state=work;
            return result;
        }
    }
    public IReadOnlyList<AuditEntry> AuditEntries {get{lock(gate)return state.AuditRows.ToArray();}}
    public static InMemoryStudentRepository CreateVerification(string approvedMastersPath)
    {
        using var json=JsonDocument.Parse(File.ReadAllText(approvedMastersPath));
        var options=new JsonSerializerOptions {PropertyNameCaseInsensitive=true};
        var categories=json.RootElement.GetProperty("categories").Deserialize<CodeCategory[]>(options)??throw new InvalidDataException("Missing approved categories.");
        var codes=json.RootElement.GetProperty("codes").Deserialize<CodeItem[]>(options)??throw new InvalidDataException("Missing approved codes.");
        var utc=new DateTime(2026,10,27,0,0,0,DateTimeKind.Utc);
        var c=new ClassItem {ClassId=1,SchoolYear=2026,GradeCode="01",ClassCode="TRN-A",ClassName="検証一組",ValidFrom="2026-04-01",ValidTo="2027-03-31",Capacity=30,DisplayOrder=10,IsActive=true,CreatedAt=utc,CreatedBy="verification-admin",UpdatedAt=utc,UpdatedBy="verification-admin"};
        Student Make(int id,string no,string name,string kana,string birth,string gender)
        {
            var s=StudentService.NormalizeDraft(new StudentDraft {StudentNo=no,StudentName=name,StudentNameKana=kana,BirthEra="HEISEI",BirthYear=birth[..4]=="1998"?"10":"11",BirthMonth=birth[5..7],BirthDay=birth[8..10],GenderCode=gender,
                PostalCode="0000000",PrefectureCode="13",AddressLine1=id==1?"架空住所1":"架空住所2",PhoneNumber=id==1?"0312345678":"0312345679",AdmissionDate="2026-04-01",EnrollmentStatusCode="01",ClassId=1},"2026-10-27");
            return s with {StudentId=id,CreatedAt=utc,CreatedBy="verification-admin",UpdatedAt=utc,UpdatedBy="verification-admin"};
        }
        return new(categories,codes,[c],[Make(1,"TRN001","検証太郎","ケンショウタロウ","1998-04-01","1"),Make(2,"TRN002","検証花子","ケンショウハナコ","1999-05-02","2")],
            new Dictionary<string,string>(StringComparer.Ordinal){{"verification-admin","Admin"},{"verification-staff","Staff"},{"verification-reader","Reader"}});
    }
}
