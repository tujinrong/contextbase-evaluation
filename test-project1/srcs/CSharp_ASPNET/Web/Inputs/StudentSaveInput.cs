using System.Globalization;
using System.Text.Json.Serialization;
using StudentManagement.Core;
namespace StudentManagement.Web;
// REG-002..024, COM-Vue_CSharpAPI. The transport contains only explicitly permitted values.
[JsonUnmappedMemberHandling(JsonUnmappedMemberHandling.Disallow)]
public sealed class StudentSaveInput
{
    public string StudentNo { get; set; } = "";
    public string StudentName { get; set; } = "";
    public string StudentNameKana { get; set; } = "";
    public BirthDateInput BirthDateInput { get; set; } = new();
    public string GenderCode { get; set; } = "0";
    public string PostalCode { get; set; } = "";
    public string PrefectureCode { get; set; } = "";
    public string AddressLine1 { get; set; } = "";
    public string? AddressLine2 { get; set; }
    public string? PhoneNumber { get; set; }
    public string? EmailAddress { get; set; }
    public string AdmissionDate { get; set; } = "";
    public string EnrollmentStatusCode { get; set; } = "01";
    public string? EnrollmentEndDate { get; set; }
    public string? ClassId { get; set; }
    public string? EmergencyContactName { get; set; }
    public string? RelationshipCode { get; set; }
    public string? EmergencyPhoneNumber { get; set; }
    public string? Remarks { get; set; }
    public int? SchoolYear { get; set; }
    public string? GradeCode { get; set; }
    public string? ExpectedVersion { get; set; }
    public string? DuplicateToken { get; set; }
    public string? OperationReason { get; set; }
    public string? ReturnContextId { get; set; }
    public SaveRequest ToRequest(long? id) => new(new StudentDraft {
        StudentNo=StudentNo, StudentName=StudentName, StudentNameKana=StudentNameKana,
        BirthDateInput=BirthDateInput ?? new(), GenderCode=GenderCode, PostalCode=PostalCode,
        PrefectureCode=PrefectureCode, AddressLine1=AddressLine1, AddressLine2=AddressLine2,
        PhoneNumber=PhoneNumber, EmailAddress=EmailAddress, AdmissionDate=AdmissionDate,
        EnrollmentStatusCode=EnrollmentStatusCode, EnrollmentEndDate=EnrollmentEndDate,
        ClassId=IdParser.Optional(ClassId,"REG-018"), EmergencyContactName=EmergencyContactName,
        RelationshipCode=RelationshipCode, EmergencyPhoneNumber=EmergencyPhoneNumber, Remarks=Remarks
    },id,id.HasValue ? IdParser.Required(ExpectedVersion,"REG-INT-013") : EnsureNewVersion(),SchoolYear,GradeCode,DuplicateToken,OperationReason);
    private long? EnsureNewVersion() { if (!string.IsNullOrEmpty(ExpectedVersion)) throw new WebFault(400,"要求が不正です。"); return null; }
    public static StudentSaveInput From(StudentDetail? detail, string? contextId, LookupSet lookups)
    {
        var d=detail?.Draft ?? new StudentDraft(); var cls=lookups.Classes.FirstOrDefault(c=>c.ClassId==d.ClassId);
        return new() { StudentNo=d.StudentNo,StudentName=d.StudentName,StudentNameKana=d.StudentNameKana,
            BirthDateInput=detail is null ? new() : JapaneseDateService.ToInput(detail.BirthDate),GenderCode=d.GenderCode,
            PostalCode=d.PostalCode,PrefectureCode=d.PrefectureCode,AddressLine1=d.AddressLine1,AddressLine2=d.AddressLine2,
            PhoneNumber=d.PhoneNumber,EmailAddress=d.EmailAddress,AdmissionDate=d.AdmissionDate,
            EnrollmentStatusCode=d.EnrollmentStatusCode,EnrollmentEndDate=d.EnrollmentEndDate,ClassId=d.ClassId?.ToString(CultureInfo.InvariantCulture),
            EmergencyContactName=d.EmergencyContactName,RelationshipCode=d.RelationshipCode,EmergencyPhoneNumber=d.EmergencyPhoneNumber,
            Remarks=d.Remarks,SchoolYear=cls?.SchoolYear ?? (detail is null ? WebPresentation.SchoolYear : null),GradeCode=cls?.GradeCode,
            ExpectedVersion=detail?.RowVersion.ToString(CultureInfo.InvariantCulture),ReturnContextId=contextId };
    }
}
public static class IdParser
{
    public static long Required(string? raw,string field) => Optional(raw,field) ?? throw new WebFault(422,"識別番号・版を正しく指定してください。",field);
    public static long? Optional(string? raw,string field) { if(string.IsNullOrEmpty(raw)) return null; if(raw.Length>19 || raw.Any(c=>c<'0'||c>'9') || !long.TryParse(raw,NumberStyles.None,CultureInfo.InvariantCulture,out var n)||n<=0) throw new WebFault(422,"識別番号・版を正の64bit整数で指定してください。",field); return n; }
}
