using System.Globalization;
using System.IO;
using System.Text.Json;
using StudentManagement.Wpf.Services;

namespace Wpf.GuiEvidence;

// Test adapter only. No SQL client, environment connection string, or persistence.
internal sealed class FixtureGateway : IStudentGateway
{
    private readonly JsonDocument data;
    private readonly string role;
    public FixtureGateway(string path, string role = "admin")
    {
        data = JsonDocument.Parse(File.ReadAllText(path));
        if (data.RootElement.GetProperty("profile").GetString() != "CSharp_WPF" || data.RootElement.GetProperty("databaseConnected").GetBoolean()) throw new InvalidDataException("Expected isolated WPF fixture.");
        if (role is not ("admin" or "staff" or "viewer")) throw new ArgumentException("Fixture role must be admin/staff/viewer.");
        this.role = role;
    }
    public string SessionId => "fixture-session";
    public bool CanEdit => role != "viewer";
    public bool CanDelete => role == "admin";
    public string Principal => $"FIXTURE-{role}: 撮影用・DB未接続";
    private IEnumerable<JsonElement> Students => data.RootElement.GetProperty("students").EnumerateArray();
    private static Dictionary<string, string> Values(JsonElement student) => student.GetProperty("values").EnumerateObject().ToDictionary(p => p.Name, p => p.Value.GetString() ?? "");
    public Task<LookupSet> LookupAsync(CancellationToken ct, bool includeOccupancy = true)
    {
        ct.ThrowIfCancellationRequested();
        var codes = data.RootElement.GetProperty("codes").EnumerateArray().GroupBy(c => c.GetProperty("category").GetString()!).ToDictionary(g => g.Key, g => (IReadOnlyList<CodeOption>)g.Select(c => new CodeOption(c.GetProperty("value").GetString()!, c.GetProperty("name").GetString()!)).ToArray());
        var classes = data.RootElement.GetProperty("classes").EnumerateArray().Select(c => new ClassOption(c.GetProperty("id").GetInt64(), c.GetProperty("year").GetInt32(), c.GetProperty("grade").GetString()!, $"{c.GetProperty("year")} / {c.GetProperty("code").GetString()} / {c.GetProperty("name").GetString()}", true, includeOccupancy ? c.GetProperty("occupancy").GetInt32() : 0, c.GetProperty("capacity").GetInt32())).ToArray();
        return Task.FromResult(new LookupSet(codes, classes));
    }
    public Task<SearchResult> SearchAsync(SearchDraft draft, int page, int pageSize, string sort, string direction, CancellationToken ct)
    {
        ct.ThrowIfCancellationRequested();
        IEnumerable<JsonElement> selected = Students.Where(s => Matches(Values(s), draft));
        string Key(JsonElement s) { var v = Values(s); return sort switch { "name" => v["StudentName"], "admissionDate" => v["AdmissionDate"], "updatedAt" => s.GetProperty("updatedAt").GetString()!, _ => v["StudentNo"] }; }
        selected = direction == "desc" ? selected.OrderByDescending(Key, StringComparer.Ordinal).ThenBy(s => s.GetProperty("id").GetInt64()) : selected.OrderBy(Key, StringComparer.Ordinal).ThenBy(s => s.GetProperty("id").GetInt64());
        var items = selected.ToArray();
        var rows = items.Skip((page - 1) * pageSize).Take(pageSize).Select(ToRow).ToArray();
        return Task.FromResult(new SearchResult("Success", items.Length, rows, items.Length == 0 ? "I-SRC-001 該当なし（fixture・DB未接続）" : "検索完了（fixture・DB未接続）", DateTimeOffset.Parse(data.RootElement.GetProperty("searchedAt").GetString()!, CultureInfo.InvariantCulture)));
    }
    private static bool Matches(Dictionary<string, string> v, SearchDraft d) =>
        (string.IsNullOrEmpty(d.StudentNo) || StudentManagement.Core.StudentNormalizer.Identifier(v["StudentNo"],15,"StudentNo").StartsWith(StudentManagement.Core.StudentNormalizer.Identifier(d.StudentNo,15,"StudentNo"), StringComparison.Ordinal)) &&
        (string.IsNullOrEmpty(d.Name) || StudentManagement.Core.StudentNormalizer.NameKey(v["StudentName"]).Contains(StudentManagement.Core.StudentNormalizer.NameKey(d.Name), StringComparison.Ordinal)) &&
        (d.StatusCodes.Length == 0 || d.StatusCodes.Contains(v["EnrollmentStatusCode"])) &&
        (d.ClassId is null || v["ClassId"] == d.ClassId.Value.ToString(CultureInfo.InvariantCulture));
    private StudentListItem ToRow(JsonElement s)
    {
        var v = Values(s);
        var cls = data.RootElement.GetProperty("classes").EnumerateArray().Single(c => c.GetProperty("id").GetInt64().ToString(CultureInfo.InvariantCulture) == v["ClassId"]);
        var status = data.RootElement.GetProperty("codes").EnumerateArray().Single(c => c.GetProperty("category").GetString() == "ENROLLMENT_STATUS" && c.GetProperty("value").GetString() == v["EnrollmentStatusCode"]).GetProperty("name").GetString()!;
        return new(s.GetProperty("id").GetInt64(), v["StudentNo"], v["StudentName"], v["StudentNameKana"], StudentManagement.Core.JapaneseDateService.ToWareki(DateOnly.Parse(s.GetProperty("birthDate").GetString()!, CultureInfo.InvariantCulture)), v["SchoolYear"] + " / 1年", cls.GetProperty("name").GetString()!, status);
    }
    public Task<StudentRecord> GetAsync(long id, CancellationToken ct)
    {
        ct.ThrowIfCancellationRequested();
        var s = Students.Single(x => x.GetProperty("id").GetInt64() == id);
        return Task.FromResult(new StudentRecord(id, s.GetProperty("version").GetInt64(), Values(s), "2026/10/12 09:00:00", "FIXTURE-NOT-DB"));
    }
    public Task<SaveResult> SaveAsync(long? id, long? version, Dictionary<string, string> raw, string? confirmation, string reason, CancellationToken ct) => Task.FromResult(new SaveResult("SystemError", "撮影fixtureでは保存を実施しません。入力を保持しています。DB未接続。"));
    public Task<SaveResult> DeleteAsync(long id, long version, string reason, CancellationToken ct) => Task.FromResult(new SaveResult("SystemError", "撮影fixtureでは削除を実施しません。DB未接続。"));
}
