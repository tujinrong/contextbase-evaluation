using System.Text;
using System.Text.Json;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using StudentManagement.Core;
using StudentManagement.Web.Controllers;
using StudentManagement.Web.Infrastructure;
using StudentManagement.Web.Models;

var results = new List<object>();
var failed = 0;
void Test(string name, Action action)
{
    try { action(); results.Add(new { name, status = "PASS" }); }
    catch (Exception ex) { failed++; results.Add(new { name, status = "FAIL", error = ex.ToString() }); }
}
void Equal<T>(T expected, T actual) { if (!EqualityComparer<T>.Default.Equals(expected, actual)) throw new InvalidOperationException($"Expected {expected}; actual {actual}."); }
void True(bool value) { if (!value) throw new InvalidOperationException("Expected true."); }
string Root()
{
    for (var directory = new DirectoryInfo(AppContext.BaseDirectory); directory is not null; directory = directory.Parent)
        if (File.Exists(Path.Combine(directory.FullName, "database/seed/approved-masters.json"))) return directory.FullName;
    throw new InvalidOperationException("Target root not found.");
}
var root = Root();
var store = InMemoryStudentRepository.CreateVerification(Path.Combine(root, "database/seed/approved-masters.json"));
var service = new StudentService(store, () => new DateTime(2026, 10, 27, 0, 0, 0, DateTimeKind.Utc));
var actor = service.ResolveActor("verification-admin");
var session = new TestSession("browser-a");
var snapshots = new EditorSnapshotStore();
var http = new DefaultHttpContext { Session = session };
http.Items["Actor"] = actor;
var controller = new StudentsController(service, new ConfirmationStore(), snapshots) { ControllerContext = new ControllerContext { HttpContext = http } };
EditorViewModel Editor(IActionResult result) => (EditorViewModel)((ViewResult)result).Model!;
SearchViewModel Search(IActionResult result) => (SearchViewModel)((ViewResult)result).Model!;

// IR-003: the source formatter changes labels precisely at the era boundaries.
foreach (var pair in new[] {
    ("1912-07-29", "明治45年07月29日"), ("1912-07-30", "大正元年07月30日"),
    ("1926-12-24", "大正15年12月24日"), ("1926-12-25", "昭和元年12月25日"),
    ("1989-01-07", "昭和64年01月07日"), ("1989-01-08", "平成元年01月08日"),
    ("2019-04-30", "平成31年04月30日"), ("2019-05-01", "令和元年05月01日") })
    Test("era:" + pair.Item1, () => Equal(pair.Item2, JapaneseDate.FormatBirthDate(pair.Item1)));

Test("search uses shared Japanese era formatter", () =>
{
    var model = Search(controller.Index(new SearchInput { Searched = true, StudentNo = "TRN001" }));
    Equal("平成10年04月01日", model.Rows.Single().BirthDate);
});

var initial = Editor(controller.Edit(1, "11111111111111111111111111111111"));
var token = initial.Input.SnapshotToken!;
var activeToken = token;
var originalPhone = initial.Input.PhoneNumber;
var originalVersion = initial.Input.ExpectedVersion;
Test("editor snapshot rejects another session and subject", () =>
{
    True(snapshots.Get(token, "browser-b", actor.UserId) is null);
    True(snapshots.Get(token, session.Id, "verification-reader") is null);
    True(snapshots.Get(token, session.Id, actor.UserId) is not null);
});
Test("snapshot values cannot mutate through returned objects", () =>
{
    var copy = snapshots.Get(token, session.Id, actor.UserId)!;
    copy.StudentName = "別内容";
    Equal(initial.Input.StudentName, snapshots.Get(token, session.Id, actor.UserId)!.StudentName);
});
Test("candidate redraw retains raw edits and original dirty baseline", () =>
{
    var posted = EditorSnapshotStore.Clone(initial.Input);
    posted.PhoneNumber = "0399999998";
    var candidate = Editor(controller.Candidates(posted));
    Equal("0399999998", candidate.Input.PhoneNumber);
    var baseline = JsonSerializer.Deserialize<Dictionary<string, string>>(candidate.BaselineJson)!;
    Equal(originalPhone, baseline["Input.PhoneNumber"]);
    Equal(originalVersion, candidate.Input.ExpectedVersion);
});
Test("failed save retains raw edits and original dirty baseline", () =>
{
    var posted = EditorSnapshotStore.Clone(initial.Input);
    posted.StudentName = "";
    posted.PostalCode = "０００-００００";
    var failedEditor = Editor(controller.Save(posted));
    Equal("０００-００００", failedEditor.Input.PostalCode);
    var baseline = JsonSerializer.Deserialize<Dictionary<string, string>>(failedEditor.BaselineJson)!;
    Equal(initial.Input.PostalCode, baseline["Input.PostalCode"]);
    True(!controller.ModelState.IsValid);
    controller.ModelState.Clear();
});
Test("reset restores original values and version after a concurrent update", () =>
{
    var current = service.Get(1, actor);
    var draft = StudentDraft.FromStudent(current);
    draft.PhoneNumber = "0399999999";
    service.Save(draft, 1, current.RowVersion, actor, "concurrent-update");
    var reset = Editor(controller.Reset(new StudentInput { SnapshotToken = token }));
    activeToken = reset.Input.SnapshotToken!;
    Equal(originalPhone, reset.Input.PhoneNumber);
    Equal(originalVersion, reset.Input.ExpectedVersion);
    Equal("0399999999", service.Get(1, actor).PhoneNumber);
    True(activeToken != token);
    True(snapshots.Get(token, session.Id, actor.UserId) is null);
});
Test("explicit reload replaces original snapshot with the latest row version", () =>
{
    var result = (ViewResult)controller.Reload(new StudentInput { SnapshotToken = activeToken });
    Equal("Edit", result.ViewName);
    var reloaded = Editor(result);
    Equal("0399999999", reloaded.Input.PhoneNumber);
    Equal(originalVersion + 1, reloaded.Input.ExpectedVersion);
    True(reloaded.Input.SnapshotToken != activeToken);
    True(snapshots.Get(activeToken, session.Id, actor.UserId) is null);
});
Test("expired editor state is rejected without replacing input", () => Equal(409, ((ObjectResult)controller.Reset(new StudentInput { SnapshotToken = "unknown" })).StatusCode));
Test("search contexts preserve applied criteria independently", () =>
{
    var first = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
    var second = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
    Search(controller.Index(new SearchInput { ContextId = first, Searched = true, StudentNo = "TRN001" }));
    Search(controller.Index(new SearchInput { ContextId = second, Searched = true, StudentNo = "TRN002" }));
    var restored = Search(controller.Index(new SearchInput { ContextId = first }));
    Equal("TRN001", restored.Input.StudentNo);
    Equal(1, restored.Rows.Single().Id);
    True(restored.RestoreScroll);
});
Test("confirmation wrong type or owner does not consume valid pending state", () =>
{
    var confirmation = new ConfirmationStore();
    var nonce = confirmation.Create("browser-a", actor.UserId, new TestPayload("draft"));
    True(confirmation.Consume<string>(nonce, "browser-a", actor.UserId) is null);
    True(confirmation.Consume<TestPayload>(nonce, "browser-b", actor.UserId) is null);
    Equal("draft", confirmation.Consume<TestPayload>(nonce, "browser-a", actor.UserId)!.Value);
    True(confirmation.Consume<TestPayload>(nonce, "browser-a", actor.UserId) is null);
});

ConfirmViewModel DuplicateConfirmation(string no)
{
    controller.ModelState.Clear();
    var blank = Editor(controller.New("cccccccccccccccccccccccccccccccc"));
    var input = StudentInput.FromStudent(service.Get(1, actor));
    input.Id = null; input.ExpectedVersion = null; input.StudentNo = no;
    input.SchoolYear = "2026"; input.GradeCode = "01";
    input.SnapshotToken = blank.Input.SnapshotToken; input.SearchContextId = blank.Input.SearchContextId;
    return (ConfirmViewModel)((ViewResult)controller.Save(input)).Model!;
}
Test("reset invalidates an earlier duplicate confirmation without affecting another editor", () =>
{
    var other = Editor(controller.Edit(2, "dddddddddddddddddddddddddddddddd"));
    var confirmation = DuplicateConfirmation("DUPRESET2");
    var reset = Editor(controller.Reset(new StudentInput { SnapshotToken = confirmation.Input.SnapshotToken }));
    True(reset.Input.SnapshotToken != confirmation.Input.SnapshotToken);
    Equal(409, ((ObjectResult)controller.ConfirmSave(confirmation.Token, "別人であることを確認")).StatusCode);
    True(snapshots.Get(other.Input.SnapshotToken, session.Id, actor.UserId) is not null);
    Equal(0, service.Search(new SearchCriteria { StudentNo = "DUPRESET2" }, actor).Rows.Count);
});
Test("reload invalidates an earlier duplicate confirmation", () =>
{
    var confirmation = DuplicateConfirmation("DUPRELOAD2");
    Editor(controller.Reload(new StudentInput { SnapshotToken = confirmation.Input.SnapshotToken }));
    Equal(409, ((ObjectResult)controller.ConfirmSave(confirmation.Token, "別人であることを確認")).StatusCode);
    Equal(0, service.Search(new SearchCriteria { StudentNo = "DUPRELOAD2" }, actor).Rows.Count);
});

var record = new
{
    schema = "access-rebuilder-web-adapter-tests/1.0", iteration = 2, provider = "VerificationMemory",
    passed = results.Count - failed, failed, results,
    scope = "Era boundaries, MVC adapter composition, immutable reset/reload state, raw redraw state, search context and confirmation ownership. Browser/SQL checks are separate.",
    sourceEvidence = new[] { "modJapaneseDate.BirthParts/FormatBirthDate", "modStudentForms.ResetEdit/ShowDraft/ReadEditSnapshot/EditHasChanges", "clsSearchContext", "clsConfirmation" },
    formalScore = (int?)null
};
var report = args.Length >= 2 && args[0] == "--output" ? Path.GetFullPath(args[1]) : Path.Combine(root, "build/test-results/web-adapter.json");
Directory.CreateDirectory(Path.GetDirectoryName(report)!);
File.WriteAllText(report, JsonSerializer.Serialize(record, new JsonSerializerOptions { WriteIndented = true }) + Environment.NewLine, new UTF8Encoding(false));
Console.WriteLine(JsonSerializer.Serialize(new { passed = results.Count - failed, failed, report }));
Environment.ExitCode = failed == 0 ? 0 : 1;

sealed record TestPayload(string Value);
sealed class TestSession(string id) : ISession
{
    private readonly Dictionary<string, byte[]> values = new();
    public bool IsAvailable => true;
    public string Id => id;
    public IEnumerable<string> Keys => values.Keys;
    public void Clear() => values.Clear();
    public Task CommitAsync(CancellationToken cancellationToken = default) => Task.CompletedTask;
    public Task LoadAsync(CancellationToken cancellationToken = default) => Task.CompletedTask;
    public void Remove(string key) => values.Remove(key);
    public void Set(string key, byte[] value) => values[key] = value.ToArray();
    public bool TryGetValue(string key, out byte[] value) { var found = values.TryGetValue(key, out var bytes); value = bytes?.ToArray() ?? []; return found; }
}
