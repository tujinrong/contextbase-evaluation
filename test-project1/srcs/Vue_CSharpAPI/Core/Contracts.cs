namespace StudentManagement.Core;

// COM-STU-001/003/008/009. Internal IDs stay Int64; Web adapters emit decimal strings.
public enum Role { Viewer, Staff, Administrator }
public enum Outcome { Saved, NoChange, ValidationFailed, Forbidden, NotFound, Conflict, ConfirmationRequired, SystemError, Unknown }
public sealed record CurrentUser(string Principal, string SessionId, Role Role);
public sealed record FieldError(string Field, string Code, string Message);
public sealed record BirthDateInput(string Era = "", string Year = "", string Month = "", string Day = "");
public sealed class StudentDraft
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
    public long? ClassId { get; set; }
    public string? EmergencyContactName { get; set; }
    public string? RelationshipCode { get; set; }
    public string? EmergencyPhoneNumber { get; set; }
    public string? Remarks { get; set; }
}
public sealed class SearchCriteria
{
    public string? StudentNoPrefix { get; set; }
    public string? NameKey { get; set; }
    public long? ClassId { get; set; }
    public string[] StatusCodes { get; set; } = ["01", "02"];
    public int Page { get; set; } = 1;
    public int PageSize { get; set; } = 20;
    public string SortKey { get; set; } = "studentNo";
    public string SortDirection { get; set; } = "asc";
    public static SearchCriteria Create(string? rawNo,string? rawName,long? classId,string[] statuses,int pageSize=20,string sortKey="studentNo",string direction="asc")
    {
        var number=StudentNormalizer.Text(rawNo,15,15,"SRC-001");
        var name=StudentNormalizer.Text(rawName,8,8,"SRC-002");
        if(classId is <=0)throw new InputValidationException([new("SRC-006","E-SRC-002","クラスIDを確認してください。")]);
        if(statuses is null||statuses.Length>4||statuses.Distinct(StringComparer.Ordinal).Count()!=statuses.Length||statuses.Any(s=>s is not ("01" or "02" or "03" or "04")))
            throw new InputValidationException([new("SRC-008","E-SRC-002","在籍区分を確認してください。")]);
        if(pageSize is not (20 or 50 or 100)||sortKey is not ("studentNo" or "name" or "admissionDate" or "updatedAt")||direction is not ("asc" or "desc"))
            throw new InputValidationException([new("PageSize","E-COM-003","表示件数・並び順を確認してください。")]);
        return new(){StudentNoPrefix=number is null?null:StudentNormalizer.Identifier(number,15,"SRC-001"),NameKey=name is null?null:StudentNormalizer.NameKey(name),ClassId=classId,StatusCodes=[..statuses],PageSize=pageSize,SortKey=sortKey,SortDirection=direction};
    }
}
public sealed record StudentListItem(long StudentId,string StudentNo,string StudentName,string StudentNameKana,
    DateOnly BirthDate,int? SchoolYear,string? GradeName,string? ClassCode,string? ClassName,string? EnrollmentStatusName)
{ public string BirthDateWareki=>JapaneseDateService.ToWareki(BirthDate); }
public sealed record StudentRow(long StudentId, string StudentNo, string StudentName, string StudentNameKana,
    DateOnly BirthDate, int? SchoolYear, string? GradeName, string? ClassCode, string? ClassName,
    string? EnrollmentStatusName, string Address, string? PhoneNumber, DateOnly AdmissionDate,
    DateTimeOffset UpdatedAt, long RowVersion)
{
    public string BirthDateWareki => JapaneseDateService.ToWareki(BirthDate);
}
public sealed record SearchResult(Outcome Outcome, int Count, IReadOnlyList<StudentListItem> Items,
    DateTimeOffset SearchedAt, bool LimitExceeded, IReadOnlyList<FieldError> Errors);
public sealed record StudentDetail(long StudentId, long RowVersion, StudentDraft Draft,
    DateOnly BirthDate, DateTimeOffset UpdatedAt, string UpdatedBy);
public sealed record CodeEntry(string CategoryId, string CodeValue, string CodeName, int DisplayOrder,
    bool IsActive, DateOnly ValidFrom, DateOnly? ValidTo, bool IsProtected);
public sealed record SchoolClass(long ClassId, int SchoolYear, string GradeCode, string ClassCode,
    string ClassName, DateOnly ValidFrom, DateOnly ValidTo, int? Capacity, int Occupied, bool IsActive);
public sealed record LookupSet(IReadOnlyList<CodeEntry> Codes, IReadOnlyList<SchoolClass> Classes);
public sealed record SaveRequest(StudentDraft Draft, long? StudentId = null, long? ExpectedVersion = null,
    int? SchoolYear = null, string? GradeCode = null, string? ConfirmationToken = null, string? Reason = null);
public sealed record SaveResult(Outcome Outcome, long? StudentId, long? RowVersion,
    IReadOnlyList<FieldError> Errors, string? ConfirmationToken = null,
    int CandidateCount = 0, IReadOnlyList<StudentRow>? Candidates = null, string? RequestId = null);
public interface IStudentService
{
    Task<SearchResult> SearchAsync(SearchCriteria criteria, CancellationToken ct = default);
    Task<StudentDetail?> GetAsync(long id, CancellationToken ct = default);
    Task<LookupSet> LookupAsync(CancellationToken ct = default);
    Task<LookupSet> LookupAsync(bool includeOccupancy,CancellationToken ct = default) => LookupAsync(ct);
    Task<SaveResult> SaveAsync(SaveRequest request, CancellationToken ct = default);
    Task<SaveResult> DeleteAsync(long id, long version, string reason, CancellationToken ct = default);
}
