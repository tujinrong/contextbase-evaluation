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

// User-directed Web revision: these test Web adaptations rather than a third
// Access training candidate. CSRF middleware itself is exercised by HTTP tests.
Test("native date input maps to the unchanged domain era model", () =>
{
    var input = StudentInput.FromStudent(service.Get(1, actor));
    input.BirthDate = "2019-05-01";
    var draft = input.ToDraft();
    Equal("REIWA", draft.BirthEra); Equal("1", draft.BirthYear);
    Equal("05", draft.BirthMonth); Equal("01", draft.BirthDay);
});
Test("invalid native date stays field-addressable instead of using old era values", () =>
{
    var input = StudentInput.FromStudent(service.Get(1, actor)); input.BirthDate = "2026-02-30";
    try { input.ToDraft(); throw new InvalidOperationException("Expected invalid date."); }
    catch (BusinessException ex) { Equal("BirthDate", ex.Field); }
    input.BirthDate = "";
    try { input.ToDraft(); throw new InvalidOperationException("Expected required date."); }
    catch (BusinessException ex) { Equal("BirthDate", ex.Field); }
});
Test("native date dirty baseline excludes unrendered era controls", () =>
{
    var baseline = EditorSnapshotStore.RawValues(StudentInput.FromStudent(service.Get(1, actor)));
    Equal("1998-04-01", baseline["Input.BirthDate"]);
    True(!baseline.ContainsKey("Input.BirthEra")); True(!baseline.ContainsKey("Input.BirthYear"));
});
StudentInput OptionsInput()
{
    controller.ModelState.Clear();
    var model = Editor(controller.Edit(1, "ffffffffffffffffffffffffffffffff"));
    model.Input.SchoolYear = "2026"; model.Input.GradeCode = "01";
    return model.Input;
}
Test("JSON options return scoped candidates without rendering or saving the form", () =>
{
    var input = OptionsInput();
    var before = service.Get(1, actor);
    var json = JsonSerializer.SerializeToElement(((JsonResult)controller.EditorOptions(input)).Value);
    True(json.GetProperty("classes").EnumerateArray().Any(c => c.GetProperty("value").GetString() == "1"));
    True(!json.GetProperty("clearClass").GetBoolean());
    Equal(before.RowVersion, service.Get(1, actor).RowVersion);
});
Test("JSON options remove an incompatible old selection while keeping raw editor state", () =>
{
    var input = OptionsInput(); input.SchoolYear = "2099";
    var json = JsonSerializer.SerializeToElement(((JsonResult)controller.EditorOptions(input)).Value);
    True(json.GetProperty("clearClass").GetBoolean()); Equal(0, json.GetProperty("classes").GetArrayLength());
    Equal("1", input.ClassId); // Client receives a clear decision, no snapshot mutation.
});
Test("JSON options reject invalid IDs, stale versions, other sessions and Reader writes", () =>
{
    var input = OptionsInput(); input.ClassId = "not-an-id";
    Equal(422, ((ObjectResult)controller.EditorOptions(input)).StatusCode);
    input = OptionsInput(); input.ExpectedVersion++;
    Equal(409, ((ObjectResult)controller.EditorOptions(input)).StatusCode);
    input = OptionsInput(); http.Session = new TestSession("another-session");
    Equal(409, ((ObjectResult)controller.EditorOptions(input)).StatusCode);
    http.Session = session; http.Items["Actor"] = service.ResolveActor("verification-reader");
    Equal(403, ((StatusCodeResult)controller.EditorOptions(input)).StatusCode);
    http.Items["Actor"] = actor;
});
Test("JSON options reject unknown and duplicate posted fields", () =>
{
    var input = OptionsInput();
    http.Request.ContentType = "application/x-www-form-urlencoded";
    http.Request.Form = new FormCollection(new Dictionary<string, Microsoft.Extensions.Primitives.StringValues> { ["Input.UntrustedRole"] = "Admin" });
    Equal(400, ((ObjectResult)controller.EditorOptions(input)).StatusCode);
    http.Request.Form = new FormCollection(new Dictionary<string, Microsoft.Extensions.Primitives.StringValues> { ["Input.ClassId"] = new[] { "1", "2" } });
    Equal(400, ((ObjectResult)controller.EditorOptions(input)).StatusCode);
    http.Request.ContentType = null; http.Request.Form = new FormCollection(new());
});
Test("validation errors target their Web field and preserve the rejected raw value", () =>
{
    var input = OptionsInput(); input.StudentName = "";
    var rejected = Editor(controller.Save(input));
    True(controller.ModelState.ContainsKey("Input.StudentName"));
    Equal("", rejected.Input.StudentName);
    controller.ModelState.Clear();
});
Test("save return context remains bound to the originally opened editor", () =>
{
    var input = OptionsInput(); input.SearchContextId = "another-tab";
    try { controller.Save(input); throw new InvalidOperationException("Expected invalid editor return state."); }
    catch (BusinessException ex) { Equal("E-COM-003", ex.Code); }
});
Test("GET result paging slices without overlap and clamps page while retaining total and context", () =>
{
    for (var i = 1; i <= 21; i++)
    {
        var draft = StudentDraft.FromStudent(service.Get(1, actor));
        draft.StudentNo = $"WEBPG{i:000}"; draft.StudentName = $"頁確認{i:000}";
        draft.StudentNameKana = "ページカクニン"; draft.BirthEra = "HEISEI";
        draft.BirthYear = "12"; draft.BirthMonth = "1"; draft.BirthDay = i.ToString();
        Equal("Saved", service.Save(draft, null, null, actor, "page-fixture-" + i).Kind);
    }
    var context = "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee";
    var first = Search(controller.Index(new SearchInput { ContextId = context, Searched = true, StudentNo = "WEBPG", Page = 1, PageSize = 20 }));
    var second = Search(controller.Index(new SearchInput { ContextId = context, Searched = true, StudentNo = "WEBPG", Page = 2, PageSize = 20 }));
    Equal(21, first.TotalCount); Equal(2, first.PageCount); Equal(20, first.Rows.Count); Equal(1, second.Rows.Count);
    True(!first.Rows.Select(r => r.Id).Intersect(second.Rows.Select(r => r.Id)).Any());
    var clamped = Search(controller.Index(new SearchInput { ContextId = context, Searched = true, StudentNo = "WEBPG", Page = int.MaxValue, PageSize = 17 }));
    Equal(2, clamped.Input.Page); Equal(20, clamped.Input.PageSize);
    var restored = Search(controller.Index(new SearchInput { ContextId = context }));
    Equal(2, restored.Input.Page); Equal("WEBPG", restored.Input.StudentNo); Equal(1, restored.Rows.Count);
});
Test("over-limit result is a bounded-search warning rather than a fabricated exact count or empty match", () =>
{
    // An isolated in-memory fixture bypasses normal writes only to exercise the
    // existing 10,000-row safety branch; no SQL or accepted business data changes.
    var original = service.Get(1, actor);
    var fixture = store.Execute(false, s => new { Categories = s.Categories(), Codes = s.Codes(), Classes = s.Classes() });
    var rows = Enumerable.Range(1, 10001).Select(i => original with { StudentId = i, StudentNo = $"LIMIT{i:00000}" });
    var limitedStore = new InMemoryStudentRepository(fixture.Categories, fixture.Codes, fixture.Classes, rows,
        new Dictionary<string, string> { [actor.UserId] = actor.Role.ToString() });
    var limitedService = new StudentService(limitedStore, () => new DateTime(2026, 10, 27, 0, 0, 0, DateTimeKind.Utc));
    Equal("LimitExceeded", limitedService.Search(new SearchCriteria { StudentNo = "LIMIT" }, actor).Kind);
    var context = new DefaultHttpContext { Session = new TestSession("limit-browser") }; context.Items["Actor"] = actor;
    var limitedController = new StudentsController(limitedService, new ConfirmationStore(), new EditorSnapshotStore())
        { ControllerContext = new ControllerContext { HttpContext = context } };
    var model = Search(limitedController.Index(new SearchInput { Searched = true, StudentNo = "LIMIT", Page = 10 }));
    if (!model.LimitExceeded) throw new InvalidOperationException("Expected limit state; total=" + model.TotalCount + "; status=" + original.EnrollmentStatusCode + "; errors=" + string.Join(";", limitedController.ModelState.SelectMany(p => p.Value!.Errors).Select(e => e.ErrorMessage)));
    True(!string.IsNullOrEmpty(model.Warning));
    Equal(0, model.TotalCount); Equal(0, model.Rows.Count); Equal(1, model.PageCount); Equal(1, model.Input.Page);
});

var record = new
{
    schema = "access-rebuilder-web-adapter-tests/1.1", revision = "web-native-user-request", provider = "VerificationMemory",
    passed = results.Count - failed, failed, results,
    scope = "Web date adapter, field errors, immutable edit/confirmation state, scoped JSON dependent candidates and GET result paging. HTTP middleware/CSRF and SQL checks are separate.",
    sourceEvidence = new[] { "CSharp_ASPNET/Web/Controllers/StudentsController.cs", "CSharp_ASPNET/wwwroot/js/site.js", "Access-derived domain constraints" },
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
