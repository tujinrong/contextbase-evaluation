using System.Text.Json.Serialization;

namespace CareerManagement.Application;

public enum UserRole { ADMIN, STAFF }
public enum CommitState { NotStarted, RolledBack, Committed, Unknown }
public enum ResultStatus { Unsearched, Loading, Success, LimitExceeded, Failed }
public enum EditTab { Basic, Careers }
public enum DraftAction { Add, Apply, Remove, Select, SwitchTab }
public enum ConfirmationKind { None, ApplyPending, DiscardPending, RemoveRow }
public enum ConfirmationChoice { None, Yes, No, Cancel }
public enum OpenMode { New, Edit }
public sealed record AppUser(string UserId, string LoginId, string DisplayName, string PasswordVerifier,
    UserRole Role, bool Enabled, byte FailedCount, DateTimeOffset? LockedUntil);
public sealed record Actor(string UserId, string SessionId, string DisplayName, UserRole Role);
public sealed record BusinessInstant(DateTimeOffset Utc, DateOnly Date)
{
    public DateOnly Month => new(Date.Year, Date.Month, 1);
}
public sealed class BusinessClock(TimeProvider time)
{
    public DateTimeOffset UtcNow => time.GetUtcNow();
    public BusinessInstant Begin()
    {
        var now = UtcNow;
        var japan = TimeZoneInfo.ConvertTime(now, TimeZoneInfo.FindSystemTimeZoneById("Tokyo Standard Time"));
        return new(now, DateOnly.FromDateTime(japan.DateTime));
    }
}
public sealed record FieldError(string ItemId, int? CareerRowNumber, string MessageId, string Message);
public sealed record Outcome(string Kind, string MessageId, string Message, IReadOnlyList<FieldError> FieldErrors,
    string CorrelationId, bool CanRetry, CommitState CommitState)
{
    public static Outcome Of(int number, string kind = "Validation", CommitState commit = CommitState.NotStarted,
        IReadOnlyList<FieldError>? fields = null) => new(kind, $"MSG-{number:000}", Messages.Get(number), fields ?? [],
            Guid.NewGuid().ToString("N"), commit != CommitState.Unknown, commit);
    public static Outcome Ok() => Of(14, "Success", CommitState.Committed);
}
public sealed class BusinessException(Outcome outcome) : Exception(outcome.MessageId)
{
    public Outcome Outcome { get; } = outcome;
    public static BusinessException Error(int msg, string kind = "Validation") => new(Outcome.Of(msg, kind));
}

// F01 / F02. Password is never included in any view model.
public sealed record LoginInput(string LoginId, string Password);
public sealed record LoginVm(string LoginId, string? Message, IReadOnlyList<FieldError> FieldErrors);
public sealed record MenuVm(string DisplayName, UserRole CurrentRole, Outcome? Outcome);
public sealed record LogoutInput(bool ConfirmDiscard);
// F03. long is represented by a decimal JSON string at the HTTP boundary.
public sealed record SearchInput(string StateId, int StateRevision, string? EmployeeNo, string? Name,
    string? Department, string? EmploymentStatus);
public sealed record SearchCriteria(string? EmployeeNo, string? Name, string? Department, string? EmploymentStatus);
public sealed record StateCommand(string StateId, int StateRevision);
public sealed record OpenInput(string SearchStateId, int StateRevision, long? EmployeeId, OpenMode Mode);
public sealed record SearchRow(long EmployeeId, string EmployeeNo, string Name, string Kana, string DepartmentName,
    string EmploymentName, DateOnly JoinDate);
public sealed record CodeRow(string Category, string Code, string Name, short SortOrder, bool Enabled, int Revision);
public sealed record SearchVm(string StateId, int StateRevision, SearchCriteria Criteria, SearchCriteria? AppliedCriteria,
    IReadOnlyList<SearchRow> Rows, long? SelectedEmployeeId, int? TotalCount, ResultStatus ResultStatus,
    Outcome? Outcome, IReadOnlyList<CodeRow> Codes, string? SelectionText = null);
// F04-I01..I24. All raw user text is retained on validation failure.
public sealed record EmployeeRaw(string EmployeeNo, string Name, string Kana, string DepartmentCode,
    string EmploymentStatus, string JoinDateRaw, string? CareerSummary, string? Skills, string? Qualifications, string? SelfPr)
{
    public static EmployeeRaw Empty(DateOnly date) => new("", "", "", "", "01", "", null, null, null, null);
}
public sealed record CareerRaw(long? CareerId, Guid ClientRowKey, string StartMonthRaw, string? EndMonthRaw,
    string CompanyName, string ProjectName, string Description, string Duties, string? Achievements,
    string? Technologies, string? Phases, string RoleCode, string TeamSizeRaw)
{
    public static CareerRaw Empty() => new(null, Guid.NewGuid(), "", null, "", "", "", "", null, null, null, "", "");
}
public sealed record EmployeeDraft(string EmployeeNo, string Name, string Kana, string DepartmentCode,
    string EmploymentStatus, DateOnly JoinDate, string? CareerSummary, string? Skills, string? Qualifications, string? SelfPr);
public sealed record CareerValues(DateOnly StartMonth, DateOnly? EndMonth, string CompanyName, string ProjectName,
    string Description, string Duties, string? Achievements, string? Technologies, string? Phases, string RoleCode, short TeamSize);
public sealed record CareerDraft(long? CareerId, Guid ClientRowKey, CareerValues Values);
public sealed record EmployeeSnapshot(long EmployeeId, int Revision, EmployeeDraft Employee,
    IReadOnlyList<CareerDraft> Careers, DateTimeOffset UpdatedAt, string UpdatedBy);
public sealed record SaveInput(string EditStateId, int StateRevision, EmployeeRaw Employee,
    CareerRaw[] Careers, long[] RemovedCareerIds);
public sealed record CancelInput(string EditStateId, int StateRevision, bool ConfirmDiscard, bool ReloadOnly, bool ReturnToMenu);
public sealed record ConfirmationInput(ConfirmationKind Kind, ConfirmationChoice Choice, Guid? ConfirmationId);
public sealed record DraftInput(string EditStateId, int StateRevision, DraftAction Action, CareerRaw? Fields,
    Guid? TargetClientRowKey, EditTab? TargetTab, ConfirmationInput Confirm);
public sealed record ConfirmationVm(Guid ConfirmationId, ConfirmationKind Kind, string MessageId,
    IReadOnlyList<ConfirmationChoice> AllowedChoices, Guid? TargetClientRowKey, EditTab? TargetTab);
public sealed record EditVm(string EditStateId, int StateRevision, EmployeeRaw Employee, IReadOnlyList<CareerRaw> Careers,
    CareerRaw? Pending, Guid? SelectedClientRowKey, EditTab ActiveTab, ConfirmationVm? Confirmation,
    Outcome? Outcome, bool CanSave, bool CanAdd, bool IsBusy, IReadOnlyList<CodeRow> Codes, IReadOnlyList<long> RemovedCareerIds, bool IsNew);
public sealed record SaveResult(long EmployeeId, string EmployeeNo, int Revision, Outcome Outcome);
// F06. ExpectedRevision must also match the server-owned snapshot.
public sealed record CodeOpenInput(string Category, string? Code, bool New, string? StateId, int? StateRevision);
public sealed record CodeSaveInput(string StateId, int StateRevision, string Category, string Code, string Name,
    string SortOrderRaw, bool Enabled, int? ExpectedRevision);
public sealed record CodeCancelInput(string StateId, int StateRevision, bool ConfirmDiscard, bool ReloadOnly, bool ReturnToMenu);
public sealed record CodeVm(string StateId, int StateRevision, string Category, IReadOnlyList<CodeRow> Rows,
    string? SelectedCode, CodeSaveInput? Draft, string Note, Outcome? Outcome, bool CanSave, bool IsBusy);
public sealed record CodeDraft(string Category, string Code, string Name, short SortOrder, bool Enabled);
// F05 snapshot contains only the selected saved aggregate and current names.
public sealed record ExportInput(string SearchStateId, int StateRevision, long EmployeeId, Guid OperationId);
public sealed record ExportCancelInput(string SearchStateId, Guid OperationId);
public sealed record CancelResult(string Phase, string MessageId, string Message);
public sealed record ReportSnapshot(BusinessInstant Captured, EmployeeSnapshot Employee,
    IReadOnlyList<CodeRow> Codes);

public static class Mapping
{
    public static EmployeeRaw Raw(this EmployeeDraft v) => new(v.EmployeeNo,v.Name,v.Kana,v.DepartmentCode,v.EmploymentStatus,
        v.JoinDate.ToString("yyyy-MM-dd"),v.CareerSummary,v.Skills,v.Qualifications,v.SelfPr);
    public static CareerRaw Raw(this CareerDraft v) => new(v.CareerId,v.ClientRowKey,v.Values.StartMonth.ToString("yyyy-MM"),
        v.Values.EndMonth?.ToString("yyyy-MM"),v.Values.CompanyName,v.Values.ProjectName,v.Values.Description,v.Values.Duties,
        v.Values.Achievements,v.Values.Technologies,v.Values.Phases,v.Values.RoleCode,v.Values.TeamSize.ToString(System.Globalization.CultureInfo.InvariantCulture));
}
