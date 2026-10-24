using System.Globalization;
using System.Security.Principal;
using Microsoft.Data.SqlClient;
using Core = StudentManagement.Core;

namespace StudentManagement.Wpf.Services;

// Infrastructure adapter: trusted DB identity drives permissions; GUI flags do not authorize writes.
public sealed class StudentGateway : IStudentGateway
{
    private readonly string connectionString;
    private Core.CurrentUser current;
    private readonly Core.IStudentService service;
    private bool authenticated;
    private StudentGateway(string connection)
    {
        connectionString = new SqlConnectionStringBuilder(connection) { Encrypt=SqlConnectionEncryptOption.Mandatory,TrustServerCertificate=false }.ConnectionString;
        current = new(WindowsIdentity.GetCurrent().Name, Guid.NewGuid().ToString("D"), Core.Role.Viewer);
        service = new Core.SqlServerStudentService(connection, () => current);
    }
    public static StudentGateway Create() => new(Environment.GetEnvironmentVariable("STUDENT_DB_CONNECTION") ?? throw new InvalidOperationException("STUDENT_DB_CONNECTIONに証明書検証付きSQL Server接続文字列を設定してください。"));
    public bool CanEdit => authenticated && current.Role != Core.Role.Viewer;
    public bool CanDelete => authenticated && current.Role == Core.Role.Administrator;
    public string Principal => current.Principal;
    public string SessionId => current.SessionId;
    private async Task AuthenticateAsync(CancellationToken ct)
    {
        await using var connection = new SqlConnection(connectionString);
        await connection.OpenAsync(ct);
        await using var command = new SqlCommand("SELECT ORIGINAL_LOGIN(), IS_ROLEMEMBER(N'student_admin'), IS_ROLEMEMBER(N'student_staff'), IS_ROLEMEMBER(N'student_viewer')", connection);
        await using var reader = await command.ExecuteReaderAsync(ct);
        if (!await reader.ReadAsync(ct)) throw new InvalidOperationException("認証主体を取得できませんでした。");
        bool HasRole(int i) => !reader.IsDBNull(i) && reader.GetInt32(i) == 1;
        if (!HasRole(1) && !HasRole(2) && !HasRole(3)) throw new InvalidOperationException("学生管理の参照権限がありません。");
        current = current with { Principal = reader.GetString(0), Role = HasRole(1) ? Core.Role.Administrator : HasRole(2) ? Core.Role.Staff : Core.Role.Viewer };
        authenticated = true;
    }
    public async Task<LookupSet> LookupAsync(CancellationToken ct,bool includeOccupancy=true)
    {
        await AuthenticateAsync(ct);
        var data = await service.LookupAsync(includeOccupancy,ct);
        var today = DateOnly.FromDateTime(TimeZoneInfo.ConvertTimeBySystemTimeZoneId(DateTimeOffset.UtcNow, "Tokyo Standard Time").DateTime);
        return new(data.Codes.GroupBy(x => x.CategoryId).ToDictionary(g => g.Key, g => (IReadOnlyList<CodeOption>)g.OrderBy(x => x.DisplayOrder).ThenBy(x => x.CodeValue).Select(x => new CodeOption(x.CodeValue, x.CodeName, x.IsActive && x.ValidFrom <= today && (x.ValidTo is null || today <= x.ValidTo))).ToArray()),
            data.Classes.Select(x => new ClassOption(x.ClassId, x.SchoolYear, x.GradeCode, $"{x.SchoolYear} / {data.Codes.FirstOrDefault(c => c.CategoryId == "GRADE" && c.CodeValue == x.GradeCode)?.CodeName ?? "不整合"} / {x.ClassCode} / {x.ClassName}", x.IsActive && x.ValidFrom <= today && today <= x.ValidTo, x.Occupied, x.Capacity)).ToArray());
    }
    public async Task<SearchResult> SearchAsync(SearchDraft draft, int page, int pageSize, string sort, string direction, CancellationToken ct)
    {
        await AuthenticateAsync(ct);
        var result = await service.SearchAsync(new() { StudentNo = draft.StudentNo, StudentName = draft.Name, ClassId = draft.ClassId, EnrollmentStatusCodes = [.. draft.StatusCodes], Page = page, PageSize = pageSize, SortKey = sort, SortDirection = direction }, ct);
        var errors = string.Join(Environment.NewLine, result.Errors.Select(x => x.Code + " " + x.Message));
        var message = result.LimitExceeded ? "W-SRC-001 検索結果が10,000件を超えています。検索条件を追加してください。" : errors.Length > 0 ? errors : result.Count == 0 ? "I-SRC-001 該当する学生がありません。" : "検索が完了しました。";
        return new(result.LimitExceeded ? "LimitExceeded" : result.Errors.Count == 0 && result.Outcome is not (Core.Outcome.SystemError or Core.Outcome.Forbidden or Core.Outcome.Unknown) ? "Success" : result.Outcome.ToString(), result.LimitExceeded || result.Errors.Count > 0 ? null : result.Count, result.Items.Select(ToRow).ToArray(), message, result.SearchedAt);
    }
    private static StudentListItem ToRow(Core.StudentRow row) => new(row.StudentId, row.StudentNo, row.StudentName, row.StudentNameKana, row.BirthDateWareki, row.SchoolYear is null ? "－" : $"{row.SchoolYear} / {row.GradeName ?? "不整合"}", (row.ClassCode ?? "－") + " / " + (row.ClassName ?? "－"), row.EnrollmentStatusName ?? "不整合");
    public async Task<StudentRecord> GetAsync(long id, CancellationToken ct)
    {
        await AuthenticateAsync(ct);
        var data = await service.GetAsync(id, ct) ?? throw new InvalidOperationException("E-STU-103 対象の学生が見つからないか、既に削除されています。");
        var d = data.Draft; var birth = Core.JapaneseDateService.ToInput(data.BirthDate);
        var values = new Dictionary<string, string> { ["StudentNo"] = d.StudentNo, ["StudentName"] = d.StudentName, ["StudentNameKana"] = d.StudentNameKana, ["BirthEra"] = birth.Era, ["BirthYear"] = birth.Year, ["BirthMonth"] = birth.Month, ["BirthDay"] = birth.Day, ["GenderCode"] = d.GenderCode, ["PostalCode"] = d.PostalCode, ["PrefectureCode"] = d.PrefectureCode, ["AddressLine1"] = d.AddressLine1, ["AddressLine2"] = d.AddressLine2 ?? "", ["PhoneNumber"] = d.PhoneNumber ?? "", ["EmailAddress"] = d.EmailAddress ?? "", ["AdmissionDate"] = d.AdmissionDate, ["EnrollmentStatusCode"] = d.EnrollmentStatusCode, ["EnrollmentEndDate"] = d.EnrollmentEndDate ?? "", ["ClassId"] = d.ClassId?.ToString(CultureInfo.InvariantCulture) ?? "", ["EmergencyContactName"] = d.EmergencyContactName ?? "", ["RelationshipCode"] = d.RelationshipCode ?? "", ["EmergencyPhoneNumber"] = d.EmergencyPhoneNumber ?? "", ["Remarks"] = d.Remarks ?? "" };
        return new(data.StudentId, data.RowVersion, values, data.UpdatedAt.ToOffset(TimeSpan.FromHours(9)).ToString("yyyy/MM/dd HH:mm:ss", CultureInfo.InvariantCulture), data.UpdatedBy);
    }
    public async Task<SaveResult> SaveAsync(long? id, long? version, Dictionary<string, string> raw, string? confirmation, string reason, CancellationToken ct)
    {
        await AuthenticateAsync(ct);
        string V(string key) => raw.GetValueOrDefault(key) ?? "";
        long? classId = string.IsNullOrEmpty(V("ClassId")) ? null : long.TryParse(V("ClassId"), NumberStyles.None, CultureInfo.InvariantCulture, out var parsed) && parsed > 0 ? parsed : throw new InvalidOperationException("E-COM-003 クラス識別番号が正しくありません。");
        int? year = string.IsNullOrEmpty(V("SchoolYear")) ? null : int.TryParse(V("SchoolYear"), NumberStyles.None, CultureInfo.InvariantCulture, out var y) ? y : throw new InvalidOperationException("E-DATE-003 年度が正しくありません。");
        var draft = new Core.StudentDraft { StudentNo = V("StudentNo"), StudentName = V("StudentName"), StudentNameKana = V("StudentNameKana"), BirthDateInput = new(V("BirthEra"), V("BirthYear"), V("BirthMonth"), V("BirthDay")), GenderCode = V("GenderCode"), PostalCode = V("PostalCode"), PrefectureCode = V("PrefectureCode"), AddressLine1 = V("AddressLine1"), AddressLine2 = V("AddressLine2"), PhoneNumber = V("PhoneNumber"), EmailAddress = V("EmailAddress"), AdmissionDate = V("AdmissionDate"), EnrollmentStatusCode = V("EnrollmentStatusCode"), EnrollmentEndDate = V("EnrollmentEndDate"), ClassId = classId, EmergencyContactName = V("EmergencyContactName"), RelationshipCode = V("RelationshipCode"), EmergencyPhoneNumber = V("EmergencyPhoneNumber"), Remarks = V("Remarks") };
        return Map(await service.SaveAsync(new(draft, id, version, year, V("GradeCode"), confirmation, reason), ct));
    }
    public async Task<SaveResult> DeleteAsync(long id, long version, string reason, CancellationToken ct) { await AuthenticateAsync(ct); return Map(await service.DeleteAsync(id, version, reason, ct)); }
    private static SaveResult Map(Core.SaveResult result)
    {
        var message = result.Errors.Count > 0 ? string.Join(Environment.NewLine, result.Errors.Select(x => x.Code + " " + x.Message)) : result.Outcome switch { Core.Outcome.Saved => "保存しました。", Core.Outcome.NoChange => "I-STU-004 変更内容がありません。", Core.Outcome.ConfirmationRequired => "W-STU-101 別人確認と理由が必要です。", Core.Outcome.Unknown => "E-COM-004 保存結果が不明です。再保存の前に検索で確認してください。", _ => result.Outcome.ToString() };
        return new(result.Outcome.ToString(), message + (result.RequestId is null ? "" : " 受付番号：" + result.RequestId), result.ConfirmationToken, result.CandidateCount, result.Candidates?.Select(x => new DuplicateItem(x.StudentNo, x.StudentName, x.BirthDateWareki, x.ClassName ?? "－")).ToArray(), result.Errors.GroupBy(x => x.Field).ToDictionary(g => g.Key, g => g.Select(x => x.Message).ToArray()));
    }
}
