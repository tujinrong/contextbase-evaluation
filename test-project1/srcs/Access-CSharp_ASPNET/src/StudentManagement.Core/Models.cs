namespace StudentManagement.Core;

// Evidence: access-export/modules/modStudentRules.txt SavedFields/NormalizeDraft;
// access-export/modules/modStudentForms.txt FieldControls/FillEditor.
public sealed class StudentDraft
{
    public string? StudentNo { get; set; }
    public string? StudentName { get; set; }
    public string? StudentNameKana { get; set; }
    public string? BirthEra { get; set; }
    public string? BirthYear { get; set; }
    public string? BirthMonth { get; set; }
    public string? BirthDay { get; set; }
    public string? GenderCode { get; set; }
    public string? PostalCode { get; set; }
    public string? PrefectureCode { get; set; }
    public string? AddressLine1 { get; set; }
    public string? AddressLine2 { get; set; }
    public string? PhoneNumber { get; set; }
    public string? EmailAddress { get; set; }
    public string? AdmissionDate { get; set; }
    public string? EnrollmentStatusCode { get; set; } = "01";
    public string? EnrollmentEndDate { get; set; }
    public int? ClassId { get; set; }
    public string? SchoolYear { get; set; }
    public string? GradeCode { get; set; }
    public string? EmergencyContactName { get; set; }
    public string? RelationshipCode { get; set; }
    public string? EmergencyPhoneNumber { get; set; }
    public string? Remarks { get; set; }
    public string? OperationReason { get; set; }

    public static StudentDraft FromStudent(Student s)
    {
        var p = JapaneseDate.BirthParts(s.BirthDate);
        return new() { StudentNo=s.StudentNo, StudentName=s.StudentName, StudentNameKana=s.StudentNameKana,
            BirthEra=p.Era, BirthYear=p.Year, BirthMonth=p.Month, BirthDay=p.Day,
            GenderCode=s.GenderCode, PostalCode=s.PostalCode, PrefectureCode=s.PrefectureCode,
            AddressLine1=s.AddressLine1, AddressLine2=s.AddressLine2, PhoneNumber=s.PhoneNumber,
            EmailAddress=s.EmailAddress, AdmissionDate=s.AdmissionDate, EnrollmentStatusCode=s.EnrollmentStatusCode,
            EnrollmentEndDate=s.EnrollmentEndDate, ClassId=s.ClassId, EmergencyContactName=s.EmergencyContactName,
            RelationshipCode=s.RelationshipCode, EmergencyPhoneNumber=s.EmergencyPhoneNumber, Remarks=s.Remarks };
    }
}

public sealed record Student
{
    public int StudentId { get; init; }
    public string StudentNo { get; init; } = "";
    public string StudentName { get; init; } = "";
    public string StudentNameKana { get; init; } = "";
    public string NameKey { get; init; } = "";
    public string KanaKey { get; init; } = "";
    public string BirthDate { get; init; } = "";
    public string GenderCode { get; init; } = "";
    public string PostalCode { get; init; } = "";
    public string PrefectureCode { get; init; } = "";
    public string AddressLine1 { get; init; } = "";
    public string? AddressLine2 { get; init; }
    public string? PhoneNumber { get; init; }
    public string? EmailAddress { get; init; }
    public string AdmissionDate { get; init; } = "";
    public string EnrollmentStatusCode { get; init; } = "";
    public string? EnrollmentEndDate { get; init; }
    public int? ClassId { get; init; }
    public string? EmergencyContactName { get; init; }
    public string? RelationshipCode { get; init; }
    public string? EmergencyPhoneNumber { get; init; }
    public string? Remarks { get; init; }
    public bool IsDeleted { get; init; }
    public DateTime? DeletedAt { get; init; }
    public string? DeletedBy { get; init; }
    public string? DeleteReason { get; init; }
    public DateTime CreatedAt { get; init; }
    public string CreatedBy { get; init; } = "";
    public DateTime UpdatedAt { get; init; }
    public string UpdatedBy { get; init; } = "";
    public int RowVersion { get; init; } = 1;
}

public sealed class SearchCriteria
{
    public string? StudentNo { get; set; }
    public string? Name { get; set; }
    public int? ClassId { get; set; }
    public bool Status01 { get; set; }
    public bool Status02 { get; set; }
    public bool Status03 { get; set; }
    public bool Status04 { get; set; }
}

public sealed record SearchRow(Student Student, string ClassDisplay, string GradeName, string EnrollmentName, int? SchoolYear);
public sealed record SearchResult(string Kind, string Message, int Total, IReadOnlyList<SearchRow> Rows, DateTime At);
public sealed record DuplicateCandidate(int StudentId, string StudentNo, string StudentName, string BirthDate, string ClassDisplay);
public sealed record SaveResult(string Kind, string Message, int? StudentId=null, int? RowVersion=null, string? Warning=null,
    string? ConfirmationToken=null, IReadOnlyList<DuplicateCandidate>? Candidates=null);

public sealed record ClassItem
{
    public int ClassId { get; init; }
    public int SchoolYear { get; init; }
    public string GradeCode { get; init; } = "";
    public string ClassCode { get; init; } = "";
    public string ClassName { get; init; } = "";
    public string ValidFrom { get; init; } = "";
    public string ValidTo { get; init; } = "";
    public int? Capacity { get; init; }
    public int DisplayOrder { get; init; }
    public bool IsActive { get; init; } = true;
    public string? Remarks { get; init; }
    public DateTime CreatedAt { get; init; }
    public string CreatedBy { get; init; } = "";
    public DateTime UpdatedAt { get; init; }
    public string UpdatedBy { get; init; } = "";
    public int RowVersion { get; init; } = 1;
}

public sealed class ClassDraft
{
    public string? SchoolYear { get; set; }
    public string? GradeCode { get; set; }
    public string? ClassCode { get; set; }
    public string? ClassName { get; set; }
    public string? ValidFrom { get; set; }
    public string? ValidTo { get; set; }
    public string? Capacity { get; set; }
    public string? DisplayOrder { get; set; } = "0";
    public bool IsActive { get; set; } = true;
    public string? Remarks { get; set; }
}

public sealed record CodeCategory(string CategoryId, string CategoryName, int CodeLength, bool AllowAdd, bool IsActive);
public sealed record CodeItem
{
    public string CategoryId { get; init; } = "";
    public string CodeValue { get; init; } = "";
    public string CodeName { get; init; } = "";
    public int DisplayOrder { get; init; }
    public bool IsActive { get; init; } = true;
    public string ValidFrom { get; init; } = "1900-01-01";
    public string? ValidTo { get; init; }
    public bool IsProtected { get; init; }
    public string? Remarks { get; init; }
    public DateTime CreatedAt { get; init; }
    public string CreatedBy { get; init; } = "";
    public DateTime UpdatedAt { get; init; }
    public string UpdatedBy { get; init; } = "";
    public int RowVersion { get; init; } = 1;
}

public sealed class CodeDraft
{
    public string? CodeName { get; set; }
    public string? DisplayOrder { get; set; } = "0";
    public bool IsActive { get; set; } = true;
    public string? ValidFrom { get; set; } = "1900-01-01";
    public string? ValidTo { get; set; }
    public string? Remarks { get; set; }
}

public sealed record AuditEntry(string TargetTable, string TargetKey, string Operation, int? BeforeVersion,
    int AfterVersion, string ChangedColumns, string ExecutedBy, DateTime ExecutedAt, string? Reason, bool DuplicateConfirmed);

/// <summary>Callbacks execute in one store transaction; implementations must roll back on failure.</summary>
public interface IStudentRepository
{
    T Execute<T>(bool write, Func<IStudentSession,T> operation);
}

public interface IStudentSession
{
    string? FindRole(string userId);
    IReadOnlyList<Student> Students();
    IReadOnlyList<ClassItem> Classes();
    IReadOnlyList<CodeItem> Codes();
    IReadOnlyList<CodeCategory> Categories();
    Student WriteStudent(Student value, int? expectedVersion);
    ClassItem WriteClass(ClassItem value, int? expectedVersion);
    CodeItem WriteCode(CodeItem value, int? expectedVersion);
    void AppendAudit(AuditEntry value);
}
