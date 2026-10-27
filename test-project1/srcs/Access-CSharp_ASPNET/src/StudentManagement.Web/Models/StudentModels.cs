using Microsoft.AspNetCore.Mvc.Rendering;
using StudentManagement.Core;

namespace StudentManagement.Web.Models;

// Field set follows the binary-exported modStudentForms.FieldControls and
// modStudentRules.NormalizeDraft. Raw strings reach domain normalization intact.
public sealed class StudentInput
{
    public int? Id { get; set; }
    public int? ExpectedVersion { get; set; }
    public string? SearchContextId { get; set; }
    public string? SnapshotToken { get; set; }
    public string? StudentNo { get; set; }
    public string? StudentName { get; set; }
    public string? StudentNameKana { get; set; }
    public string? BirthDate { get; set; }
    public string? BirthEra { get; set; }
    public string? BirthYear { get; set; }
    public string? BirthMonth { get; set; }
    public string? BirthDay { get; set; }
    public string? GenderCode { get; set; } = "0";
    public string? PostalCode { get; set; }
    public string? PrefectureCode { get; set; }
    public string? AddressLine1 { get; set; }
    public string? AddressLine2 { get; set; }
    public string? PhoneNumber { get; set; }
    public string? EmailAddress { get; set; }
    public string? AdmissionDate { get; set; }
    public string? EnrollmentStatusCode { get; set; } = "01";
    public string? EnrollmentEndDate { get; set; }
    public string? SchoolYear { get; set; }
    public string? GradeCode { get; set; }
    public string? ClassId { get; set; }
    public string? EmergencyContactName { get; set; }
    public string? RelationshipCode { get; set; }
    public string? EmergencyPhoneNumber { get; set; }
    public string? Remarks { get; set; }
    public string? OperationReason { get; set; }

    public StudentDraft ToDraft()
    {
        var birth = (Era: BirthEra, Year: BirthYear, Month: BirthMonth, Day: BirthDay);
        if (BirthDate is not null)
        {
            try { birth = JapaneseDate.BirthParts(JapaneseDate.StrictIso(BirthDate, true)!); }
            catch (BusinessException ex) { throw new BusinessException(ex.Code, ex.Message, nameof(BirthDate)); }
        }
        return new()
        {
        StudentNo = StudentNo, StudentName = StudentName, StudentNameKana = StudentNameKana,
        BirthEra = birth.Era, BirthYear = birth.Year, BirthMonth = birth.Month, BirthDay = birth.Day,
        GenderCode = GenderCode, PostalCode = PostalCode, PrefectureCode = PrefectureCode,
        AddressLine1 = AddressLine1, AddressLine2 = AddressLine2, PhoneNumber = PhoneNumber,
        EmailAddress = EmailAddress, AdmissionDate = AdmissionDate, EnrollmentStatusCode = EnrollmentStatusCode,
        EnrollmentEndDate = EnrollmentEndDate, ClassId = ParseOptionalId(ClassId), SchoolYear = SchoolYear,
        GradeCode = GradeCode, EmergencyContactName = EmergencyContactName, RelationshipCode = RelationshipCode,
        EmergencyPhoneNumber = EmergencyPhoneNumber, Remarks = Remarks, OperationReason = OperationReason
        };
    }

    public static StudentInput FromStudent(Student student)
    {
        var draft = StudentDraft.FromStudent(student);
        return new()
        {
            Id = student.StudentId, ExpectedVersion = student.RowVersion, StudentNo = draft.StudentNo,
            StudentName = draft.StudentName, StudentNameKana = draft.StudentNameKana, BirthEra = draft.BirthEra,
            BirthDate = student.BirthDate,
            BirthYear = draft.BirthYear, BirthMonth = draft.BirthMonth, BirthDay = draft.BirthDay,
            GenderCode = draft.GenderCode, PostalCode = draft.PostalCode, PrefectureCode = draft.PrefectureCode,
            AddressLine1 = draft.AddressLine1, AddressLine2 = draft.AddressLine2, PhoneNumber = draft.PhoneNumber,
            EmailAddress = draft.EmailAddress, AdmissionDate = draft.AdmissionDate, EnrollmentStatusCode = draft.EnrollmentStatusCode,
            EnrollmentEndDate = draft.EnrollmentEndDate, ClassId = draft.ClassId?.ToString(), SchoolYear = draft.SchoolYear,
            GradeCode = draft.GradeCode, EmergencyContactName = draft.EmergencyContactName, RelationshipCode = draft.RelationshipCode,
            EmergencyPhoneNumber = draft.EmergencyPhoneNumber, Remarks = draft.Remarks
        };
    }

    public static int? ParseOptionalId(string? value)
    {
        if (string.IsNullOrWhiteSpace(value)) return null;
        if (!int.TryParse(value, out var result) || result <= 0) throw new BusinessException("E-COM-003", "識別番号の形式が正しくありません。");
        return result;
    }
}

public sealed class SearchInput
{
    public string ContextId { get; set; } = "";
    public string? StudentNo { get; set; }
    public string? Name { get; set; }
    public string? ClassId { get; set; }
    public string[] Statuses { get; set; } = ["01", "02"];
    public string SortKey { get; set; } = "studentNo";
    public string SortDirection { get; set; } = "asc";
    public bool Searched { get; set; }
    public int Page { get; set; } = 1;
    public int PageSize { get; set; } = 20;
}

public sealed record StudentListItem(int Id, string StudentNo, string Name, string Kana, string BirthDate,
    string SchoolYearGrade, string ClassName, string EnrollmentName, int Version);

public sealed class SearchViewModel
{
    public SearchInput Input { get; set; } = new();
    public IReadOnlyList<SelectListItem> Classes { get; set; } = [];
    public IReadOnlyList<StudentListItem> Rows { get; set; } = [];
    public bool CanWrite { get; set; }
    public bool Searched { get; set; }
    public string? SearchedAt { get; set; }
    public string? Warning { get; set; }
    public bool RestoreScroll { get; set; }
    public int TotalCount { get; set; }
    public int PageCount { get; set; } = 1;
    public bool LimitExceeded { get; set; }
}

public sealed class EditorViewModel
{
    public StudentInput Input { get; set; } = new();
    public bool ReadOnly { get; set; }
    public bool CanDelete { get; set; }
    public IReadOnlyList<SelectListItem> Classes { get; set; } = [];
    public IReadOnlyList<SelectListItem> GenderCodes { get; set; } = [];
    public IReadOnlyList<SelectListItem> PrefectureCodes { get; set; } = [];
    public IReadOnlyList<SelectListItem> StatusCodes { get; set; } = [];
    public IReadOnlyList<SelectListItem> RelationshipCodes { get; set; } = [];
    public IReadOnlyList<SelectListItem> GradeCodes { get; set; } = [];
    public IReadOnlyList<SelectListItem> SchoolYears { get; set; } = [];
    public string? Capacity { get; set; }
    public string? Updated { get; set; }
    public string BaselineJson { get; set; } = "{}";
}

public sealed class ConfirmViewModel
{
    public string Token { get; set; } = "";
    public string Kind { get; set; } = "";
    public StudentInput Input { get; set; } = new();
    public IReadOnlyList<StudentListItem> Candidates { get; set; } = [];
    public string? Reason { get; set; }
}
