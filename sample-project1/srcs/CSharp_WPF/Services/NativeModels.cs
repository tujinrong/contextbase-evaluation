namespace StudentManagement.Wpf.Services;

public sealed record CodeOption(string Value, string Name, bool Selectable = true)
{
    // Search has a NULL criterion for the explicit "all" option; registration keeps its raw string.
    public string? SearchValue => Value == "" ? null : Value;
    public override string ToString() => Name + (Selectable ? "" : "（停止・期間外）");
}
public sealed record ClassOption(long Id, int Year, string Grade, string Name, bool Selectable, int Occupancy, int? Capacity)
{
    public long? SearchId => Id == 0 ? null : Id;
    // Registration binds raw strings; an unselected ID stays empty instead of converting "" to Int64.
    public string Value => Id == 0 ? "" : Id.ToString(System.Globalization.CultureInfo.InvariantCulture);
    public override string ToString() => Name + (Selectable ? "" : "（停止・期間外）");
}
public sealed record LookupSet(IReadOnlyDictionary<string, IReadOnlyList<CodeOption>> Codes, IReadOnlyList<ClassOption> Classes);
public sealed record StudentListItem(long StudentId, string StudentNo, string StudentName, string StudentNameKana, string BirthDateWareki, string YearGrade, string ClassName, string EnrollmentName);
public sealed record SearchResult(string State, int? Total, IReadOnlyList<StudentListItem> Items, string Message, DateTimeOffset SearchedAt);
public sealed record DuplicateItem(string StudentNo, string StudentName, string BirthDateWareki, string ClassName);
public sealed record SaveResult(string State, string Message, string? Token = null, int CandidateCount = 0, IReadOnlyList<DuplicateItem>? Candidates = null, IReadOnlyDictionary<string, string[]>? Errors = null);
public sealed record StudentRecord(long StudentId, long Version, Dictionary<string, string> Values, string UpdatedAt, string UpdatedBy);

public sealed record YearOption(int? Value, string Name);
[System.Text.Json.Serialization.JsonUnmappedMemberHandling(System.Text.Json.Serialization.JsonUnmappedMemberHandling.Disallow)]
public sealed class SearchDraft : StudentManagement.Wpf.ViewModels.Bindable
{
    private string studentNo = "", name = "";
    private long? classId;
    public string StudentNo { get => studentNo; set => Set(ref studentNo, value); }
    public string Name { get => name; set => Set(ref name, value); }
    public long? ClassId { get => classId; set => Set(ref classId, value); }
    public string[] StatusCodes { get; set; } = ["01", "02"];
    public SearchDraft Clone() => new() { StudentNo = StudentNo, Name = Name, ClassId = ClassId, StatusCodes = [.. StatusCodes] };
}

public interface IStudentGateway
{
    bool CanEdit { get; }
    bool CanDelete { get; }
    string Principal { get; }
    string SessionId { get; }
    Task<LookupSet> LookupAsync(CancellationToken ct,bool includeOccupancy=true);
    Task<SearchResult> SearchAsync(SearchDraft draft, int page, int pageSize, string sort, string direction, CancellationToken ct);
    Task<StudentRecord> GetAsync(long id, CancellationToken ct);
    Task<SaveResult> SaveAsync(long? id, long? version, Dictionary<string, string> raw, string? confirmation, string reason, CancellationToken ct);
    Task<SaveResult> DeleteAsync(long id, long version, string reason, CancellationToken ct);
}
