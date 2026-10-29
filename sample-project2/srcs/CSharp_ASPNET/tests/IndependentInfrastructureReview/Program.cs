using System.Security.Claims;
using System.Security.Cryptography;
using System.Text.Json;
using CareerManagement.Application;
using CareerManagement.Infrastructure.Authentication;
using CareerManagement.Infrastructure.Reports;
using CareerManagement.Infrastructure.Sql;
using CareerManagement.Infrastructure.State;
using CareerManagement.Web.Filters;
using ClosedXML.Excel;
using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Abstractions;
using Microsoft.AspNetCore.Mvc.Filters;
using Microsoft.AspNetCore.Routing;
using Microsoft.Data.SqlClient;
using Microsoft.Extensions.DependencyInjection;

var results = new List<object>();
var failed = 0;
var startedAtUtc = DateTimeOffset.UtcNow;
var reportOutputs = new List<object>();
void SaveReport(string filename, byte[] content)
{
    var path = Path.Combine(Directory.GetCurrentDirectory(), ".tmp/independent-review", filename); Directory.CreateDirectory(Path.GetDirectoryName(path)!); File.WriteAllBytes(path, content);
    reportOutputs.Add(new { path = Path.GetRelativePath(Directory.GetCurrentDirectory(), path).Replace('\\', '/'), sha256 = Convert.ToHexStringLower(SHA256.HashData(content)) });
}
void Check(string id, Action test)
{
    try { test(); results.Add(new { id, status = "PASS" }); }
    catch (Exception e) { failed++; results.Add(new { id, status = "FAIL", error = e.Message }); }
}
async Task CheckAsync(string id, Func<Task> test)
{
    try { await test(); results.Add(new { id, status = "PASS" }); }
    catch (Exception e) { failed++; results.Add(new { id, status = "FAIL", error = e.Message }); }
}
static void Require(bool value, string message) { if (!value) throw new InvalidOperationException(message); }
static async Task Unknown(Func<Task> action)
{
    try { await action(); }
    catch (BusinessException e) { Require(e.Outcome.MessageId == "MSG-034" && e.Outcome.CommitState == CommitState.Unknown && !e.Outcome.CanRetry, "Unknown must be MSG034 / Unknown / CanRetry=false"); return; }
    throw new InvalidOperationException("Expected an unconfirmed outcome");
}
Check("IR-X01-leading-apostrophe-public-API-roundtrip", () =>
{
    string[] values = ["'ABC", "''ABC", "'=1+1", "'", "=SUM(A1:A2)", "+1", "@SUM", "-1", "000001", "_x0041_", "元LF\n🐱e\u0301"];
    using var book = new XLWorkbook(); var sheet = book.AddWorksheet("fixture");
    for (var i = 0; i < values.Length; i++) ReportText.SetExact(sheet.Cell(i + 1, 1), values[i]);
    using var stream = new MemoryStream(); book.SaveAs(stream); stream.Position = 0; using var read = new XLWorkbook(stream);
    for (var i = 0; i < values.Length; i++) Require(read.Worksheet(1).Cell(i + 1, 1).GetText() == values[i] && !read.Worksheet(1).Cell(i + 1, 1).HasFormula, "Literal text was changed");
});
Check("IR-X02-text-split-restores-original", () =>
{
    var text = "'ABC\n" + string.Concat(Enumerable.Repeat("🐱e\u0301", 60)) + "\n_x0041_";
    var slices = ReportText.Split(text, 200, new FixtureWidth());
    Require(string.Concat(slices.Select(x => x.Text + x.FollowingSeparator)) == text, "Split lost original LF/scalars");
});
Check("IR-X03-native-GDI-font-measurement", () => Require(new GdiTextWidthMeasurer().Width("独立検査ABC") > 0, "Actual Windows GDI measurement failed"));
var instant = new BusinessInstant(new DateTimeOffset(2026, 10, 31, 14, 59, 59, TimeSpan.Zero), new(2026, 10, 31));
string LongText(int length) => "'=1+1\n" + new string('文', length - 6);
var employee = new EmployeeDraft("000001", "'" + new string('名', 38) + "🐱", "カクウシャイン", "01", "01", new(2020, 1, 1), LongText(1000), LongText(1000), LongText(1000), LongText(1000));
var careers = Enumerable.Range(1, 20).Select(i => new CareerDraft(i, Guid.NewGuid(), new(new(2026, 10, 1), null, new string('会', 100), "架空案件" + i.ToString("D2") + new string('案', 94), LongText(1000), LongText(1000), LongText(1000), LongText(500), LongText(200), "01", 999))).ToArray();
CodeRow[] codes = [new("DEPARTMENT", "01", "開発", 1, true, 1), new("DEPARTMENT", "02", "基盤", 2, true, 1), new("DEPARTMENT", "03", "管理", 3, true, 1), new("EMPLOYMENT_STATUS", "01", "在職", 1, true, 1), new("EMPLOYMENT_STATUS", "02", "休職", 2, true, 1), new("EMPLOYMENT_STATUS", "03", "退職", 3, true, 1), new("PROJECT_ROLE", "01", "メンバー", 1, true, 1), new("PROJECT_ROLE", "02", "リーダー", 2, true, 1), new("PROJECT_ROLE", "03", "PM", 3, true, 1)];
var snapshot = new ReportSnapshot(instant, new(1, 1, employee, careers, instant.Utc, "SP2ADMIN"), codes);
MemoryStream? report = null;
Check("IR-X04-report20-maximum-fields-create-and-self-verify", () =>
{
    EmployeeService.ValidateStored(snapshot.Employee, codes, instant);
    report = new ReportService(new GdiTextWidthMeasurer()).Create(snapshot, CancellationToken.None);
    SaveReport("maximum-report.xlsx", report.ToArray());
});
if (report is not null)
{
    using (report)
    using (var read = new XLWorkbook(report))
    {
        Check("IR-X05-exact-two-sheets-and-literal-values", () =>
        {
            Require(read.Worksheets.Select(x => x.Name).SequenceEqual(new[] { "職務経歴書", "案件経歴" }), "Unexpected sheet set");
            Require(read.Worksheets.SelectMany(x => x.CellsUsed()).All(x => !x.HasFormula), "Formula exists");
            Require(read.Worksheet(1).Cell("A3").GetText().Contains("2026年10月31日", StringComparison.Ordinal), "Capture basis changed");
            Require(read.Worksheet(2).CellsUsed().Count(x => x.GetText().StartsWith("案件連番・案件名", StringComparison.Ordinal)) >= 20, "Not all twenty careers are represented");
        });
        Check("IR-X06-report-heading-11pt-bold", () => Require(read.Worksheet(1).CellsUsed().Any(x => x.GetText() == "職務要約" && x.Style.Font.FontSize == 11 && x.Style.Font.Bold), "Required 11pt bold heading is missing"));
        Check("IR-X07-header-footer-seven-mm", () => Require(read.Worksheets.All(x => Math.Abs(x.PageSetup.Margins.Header - 7 / 25.4) < 0.0001 && Math.Abs(x.PageSetup.Margins.Footer - 7 / 25.4) < 0.0001), "Header/footer margin must each be 7mm"));
        foreach (var item in IndependentReportChecks.Cases(read, report.ToArray(), 20)) Check("IR-PRINT-maximum-" + item.Id, item.Test);
    }
}
foreach (var fixture in new[] { (File: "normal-seed-career.xlsx", Careers: 2), (File: "normal-literal-career.xlsx", Careers: 1) })
{
    var path = Path.Combine(Directory.GetCurrentDirectory(), ".tmp/report-format-review", fixture.File); var content = File.ReadAllBytes(path);
    reportOutputs.Add(new { path = Path.GetRelativePath(Directory.GetCurrentDirectory(), path).Replace('\\', '/'), sha256 = Convert.ToHexStringLower(SHA256.HashData(content)) });
    using var stream = new MemoryStream(content); using var book = new XLWorkbook(stream);
    foreach (var item in IndependentReportChecks.Cases(book, content, fixture.Careers)) Check("IR-PRINT-" + fixture.File + "-" + item.Id, item.Test);
}
Check("IR-T01-expired-session-cannot-revive", () =>
{
    var time = new ManualTime(); var sessions = new SessionRegistry(new(time)); var id = sessions.Create("fixture");
    time.Advance(TimeSpan.FromMinutes(30)); Require(!sessions.Touch(id, "fixture") && !sessions.IsValid(id, "fixture"), "Expired input revived authentication");
});
Check("IR-T02-read-does-not-extend-idle", () =>
{
    var time = new ManualTime(); var sessions = new SessionRegistry(new(time)); var id = sessions.Create("fixture");
    time.Advance(TimeSpan.FromMinutes(29)); Require(sessions.IsValid(id, "fixture"), "Too early expiry"); time.Advance(TimeSpan.FromMinutes(1)); Require(!sessions.IsValid(id, "fixture"), "Read extended idle expiry");
});
Check("IR-O01-finished-export-cancel-interleaving", () =>
{
    var registry = new ExportOperationRegistry(); var operation = registry.Start("session", "state", Guid.NewGuid());
    Exception? observed = null; CancelResult? cancelled = null;
    var thread = new Thread(() => { try { cancelled = registry.Cancel("session", "state", operation.Id); } catch (Exception e) { observed = e; } });
    lock (operation.Gate)
    {
        thread.Start(); Require(SpinWait.SpinUntil(() => (thread.ThreadState & System.Threading.ThreadState.WaitSleepJoin) != 0, 5000), "Cancel did not reach operation gate");
        registry.Finish(operation);
    }
    Require(thread.Join(5000), "Cancel worker did not finish");
    Require(observed is null, "Concurrent Cancel/Finish threw " + observed?.GetType().Name);
    Require(cancelled?.Phase == "AlreadyFinished" && cancelled.MessageId == "MSG-036", "Finished operation should report AlreadyFinished/MSG036");
});
object? sqlScope = null;
if (args.Contains("--sql", StringComparer.Ordinal))
{
    var dbName = "SP2_WebFixture_IR_" + Guid.NewGuid().ToString("N");
    var options = new DatabaseOptions { AllowedDatabase = dbName, Fixture = true, ConnectionString = $"Server=.\\SQLEXPRESS;Database={dbName};Integrated Security=True;Encrypt=True;TrustServerCertificate=True" };
    var created = false; var owner = "independent-review/" + Guid.NewGuid().ToString("N");
    var root = Directory.GetCurrentDirectory();
    try
    {
        await SafeInitializer.CreateAsync(options, await File.ReadAllTextAsync(Path.Combine(root, "database/schema.sql")), CancellationToken.None); created = true;
        await using (var connection = new SqlConnection(options.ConnectionString))
        {
            await connection.OpenAsync();
            await using var mark = new SqlCommand("EXEC sys.sp_addextendedproperty @name=N'IndependentReviewOwner',@value=@owner; SELECT CONVERT(nvarchar(100),SERVERPROPERTY('ProductVersion'));", connection);
            mark.Parameters.Add(P.N("@owner", 100, owner)); var version = (string?)await mark.ExecuteScalarAsync();
            sqlScope = new { database = dbName, serverVersion = version, compatibility = 160, sqlServer2022Executed = false, resource = "new owned temporary fixture; no existing DB initialized or reset" };
        }
        var clean = new Database(options, new NoDbFaults());
        async Task<int> CountAsync()
        {
            await using var connection = new SqlConnection(options.ConnectionString); await connection.OpenAsync();
            await using var command = new SqlCommand("SELECT COUNT(*) FROM dbo.m_code_category;", connection); return (int)(await command.ExecuteScalarAsync())!;
        }
        static async Task Insert(DbUnit unit) { await using var cmd = unit.Command("INSERT dbo.m_code_category(category_id,category_name) VALUES('PROJECT_ROLE',N'案件役割');"); await cmd.ExecuteNonQueryAsync(); }
        await CheckAsync("IR-D01-confirmed-rollback-restores-row", async () => { var unit = await clean.BeginAsync(true, CancellationToken.None); await Insert(unit); await unit.DisposeAsync(); Require(await CountAsync() == 0, "Confirmed rollback left a row"); });
        await CheckAsync("IR-D02-rollback-failure-is-unknown", async () => { var unit = await new Database(options, new FixtureFaults { RollbackFailure = true }).BeginAsync(true, CancellationToken.None); await Insert(unit); await Unknown(async () => await unit.DisposeAsync()); Require(await CountAsync() == 0, "Fixture connection disposal did not clean its uncommitted row"); });
        await CheckAsync("IR-D03-postcommit-response-loss-is-unknown", async () =>
        {
            await using (var unit = await new Database(options, new FixtureFaults { AfterCommitFailure = true }).BeginAsync(true, CancellationToken.None)) { await Insert(unit); await Unknown(() => unit.CommitAsync(CancellationToken.None)); }
            Require(await CountAsync() == 1, "Postcommit fault did not preserve actual committed data");
            await using var cleanup = await clean.BeginAsync(true, CancellationToken.None); await using var command = cleanup.Command("DELETE dbo.m_code_category WHERE category_id='PROJECT_ROLE';"); await command.ExecuteNonQueryAsync(); await cleanup.CommitAsync(CancellationToken.None);
        });
        await using (var unit = await clean.BeginAsync(true, CancellationToken.None))
        {
            var verifier = AuthService.CreateHasher().HashPassword(new("IR", "IR", "fixture", "", UserRole.STAFF, true, 0, null), Convert.ToHexString(RandomNumberGenerator.GetBytes(24)));
            await using var cmd = unit.Command("INSERT dbo.m_app_user(user_id,login_id,display_name,password_verifier,role_id,is_enabled,failed_count,locked_until) VALUES(N'IRUSER','IRUSER',N'fixture',@verifier,'STAFF',1,0,NULL);", P.N("@verifier", 2048, verifier)); await cmd.ExecuteNonQueryAsync(); await unit.CommitAsync(CancellationToken.None);
        }
        await CheckAsync("IR-H01-background-GET-does-not-extend-idle", async () =>
        {
            var time = new ManualTime(); var sessions = new SessionRegistry(new(time)); var session = sessions.Create("IRUSER"); time.Advance(TimeSpan.FromMinutes(29));
            var current = new CurrentUserService(clean, new Repository(), sessions); var filter = new CurrentActorFilter(current, sessions, new());
            var services = new ServiceCollection(); services.AddLogging(); services.AddAuthentication("SP2").AddCookie("SP2"); using var provider = services.BuildServiceProvider();
            var http = new DefaultHttpContext { RequestServices = provider }; http.Request.Method = "GET"; http.Request.Path = "/employees/edit"; http.Request.Headers["Sec-Fetch-Mode"] = "cors";
            http.User = new ClaimsPrincipal(new ClaimsIdentity([new(ClaimTypes.NameIdentifier, "IRUSER"), new("session_id", session)], "SP2"));
            var action = new ActionContext(http, new RouteData(), new ActionDescriptor()); var context = new ActionExecutingContext(action, [], new Dictionary<string, object?>(), new object());
            await filter.OnActionExecutionAsync(context, () => Task.FromResult(new ActionExecutedContext(action, [], new object()) { Result = new EmptyResult() }));
            time.Advance(TimeSpan.FromMinutes(2)); Require(!sessions.IsValid(session, "IRUSER"), "Background GET refreshed the idle deadline");
        });
        var businessClock = new BusinessClock(TimeProvider.System); var businessSessions = new SessionRegistry(businessClock);
        var businessRepository = new Repository(); var currentActor = new CurrentUserService(clean, businessRepository, businessSessions);
        var businessService = new EmployeeService(clean, businessRepository, currentActor, businessClock);
        var staleAdmin = new Actor("IRUSER", businessSessions.Create("IRUSER"), "fixture", UserRole.ADMIN);
        long repairId = 0;
        await CheckAsync("IR-D04-edit-repairs-invalid-values-report-stays-strict", async () =>
        {
            await using (var unit = await clean.BeginAsync(true, CancellationToken.None))
            {
                await using (var categories = unit.Command("INSERT dbo.m_code_category(category_id,category_name) VALUES('DEPARTMENT',N'部署'),('EMPLOYMENT_STATUS',N'在籍区分'),('PROJECT_ROLE',N'案件役割');")) await categories.ExecuteNonQueryAsync();
                foreach (var code in codes)
                {
                    await using var insert = unit.Command("INSERT dbo.m_code(category_id,code,code_name,sort_order,is_enabled,updated_at,updated_by,revision) VALUES(@category,@code,@name,@sort,1,SYSUTCDATETIME(),N'IRUSER',1);",
                        P.V("@category", 24, code.Category), P.C("@code", 2, code.Code), P.N("@name", 80, code.Name), P.S("@sort", code.SortOrder));
                    await insert.ExecuteNonQueryAsync();
                }
                await unit.CommitAsync(CancellationToken.None);
            }
            var raw = new EmployeeRaw("000001", "訂正前", "テスト", "01", "01", "2020-01-01", null, null, null, null);
            var child = new CareerRaw(null, Guid.NewGuid(), "2020-01", null, "架空会社", "架空案件", "概要", "業務", null, null, null, "01", "1");
            var saved = await businessService.SaveAsync(staleAdmin, null, raw, [child], [], CancellationToken.None); repairId = saved.EmployeeId;
            await using (var unit = await clean.BeginAsync(true, CancellationToken.None))
            {
                await using var corrupt = unit.Command("UPDATE dbo.m_employee SET employee_name=N' ' WHERE employee_id=@id; UPDATE dbo.t_career SET start_month='20990101' WHERE employee_id=@id;", P.L("@id", repairId));
                Require(await corrupt.ExecuteNonQueryAsync() == 2, "Correctable fixture update missed a row"); await unit.CommitAsync(CancellationToken.None);
            }
            var editable = (await businessService.ReadAsync(staleAdmin, repairId, CancellationToken.None)).Snapshot;
            Require(editable.Employee.Name == " " && editable.Careers.Single().Values.StartMonth == new DateOnly(2099, 1, 1), "Edit read hid or rejected correctable raw values");
            try { await businessService.ReportAsync(staleAdmin, repairId, CancellationToken.None); throw new InvalidOperationException("Invalid values were reportable"); }
            catch (BusinessException e) { Require(e.Outcome.MessageId == "MSG-020", "Report integrity rejection changed"); }
            var corrected = editable.Careers.Select(x => x.Raw() with { StartMonthRaw = "2020-01" }).ToArray();
            var repair = await businessService.SaveAsync(staleAdmin, editable, editable.Employee.Raw() with { Name = "訂正済み" }, corrected, [], CancellationToken.None);
            Require(repair.Revision == editable.Revision + 1 && repair.Outcome.MessageId == "MSG-014", "Repair did not atomically advance the parent once");
            var after = (await businessService.ReadAsync(staleAdmin, repairId, CancellationToken.None)).Snapshot;
            Require(after.Employee.Name == "訂正済み" && after.Careers.Single().Values.StartMonth == new DateOnly(2020, 1, 1), "Corrected aggregate differs");
            Require((await businessService.ReportAsync(staleAdmin, repairId, CancellationToken.None)).Employee.Revision == after.Revision, "Repaired aggregate is not reportable");
            try { await businessService.SaveAsync(staleAdmin, editable, after.Employee.Raw(), after.Careers.Select(x => x.Raw()).ToArray(), [], CancellationToken.None); throw new InvalidOperationException("Stale no-change save succeeded"); }
            catch (BusinessException e) { Require(e.Outcome.MessageId == "MSG-008", "Version must precede no-change comparison"); }
            try { await businessService.SaveAsync(staleAdmin, after, after.Employee.Raw(), [], [], CancellationToken.None); throw new InvalidOperationException("Omitted child became an implicit deletion"); }
            catch (BusinessException e) { Require(e.Outcome.MessageId == "MSG-025", "Loaded child partition must be complete"); }
            Require((await businessService.ReadAsync(staleAdmin, repairId, CancellationToken.None)).Snapshot.Revision == after.Revision, "Rejected saves changed parent revision");
        });
        await CheckAsync("IR-H02-lost-admin-discards-only-code-drafts", async () =>
        {
            var states = new ScreenStateStore(); var ownCode = states.Add(new CodeState(staleAdmin.SessionId, "DEPARTMENT"));
            var ownSearch = states.Add(new SearchState(staleAdmin.SessionId)); var otherCode = states.Add(new CodeState("other-session", "PROJECT_ROLE"));
            var filter = new CurrentActorFilter(currentActor, businessSessions, states); var http = new DefaultHttpContext();
            http.Request.Method = "POST"; http.Request.Path = "/codes/save"; http.Request.Headers["X-SP2-User-Action"] = "true";
            http.User = new ClaimsPrincipal(new ClaimsIdentity([new(ClaimTypes.NameIdentifier, "IRUSER"), new("session_id", staleAdmin.SessionId), new(ClaimTypes.Role, "ADMIN")], "SP2"));
            var action = new ActionContext(http, new RouteData(), new ActionDescriptor()); var context = new ActionExecutingContext(action, [], new Dictionary<string, object?>(), new object());
            var invoked = false;
            await filter.OnActionExecutionAsync(context, () => { invoked = true; return Task.FromResult(new ActionExecutedContext(action, [], new object()) { Result = new EmptyResult() }); });
            Require(!invoked && context.Result is JsonResult { StatusCode: 403 }, "Current STAFF reached code action after losing ADMIN");
            var body = JsonSerializer.SerializeToElement(((JsonResult)context.Result!).Value, HttpJson.Options);
            Require(body.GetProperty("outcome").GetProperty("messageId").GetString() == "MSG-003", "Lost ADMIN must return MSG003");
            try { states.Get<CodeState>(ownCode.Id, staleAdmin.SessionId); throw new InvalidOperationException("Forbidden code draft remained"); }
            catch (BusinessException e) { Require(e.Outcome.MessageId == "MSG-008", "Code draft removal returned an unexpected result"); }
            Require(ReferenceEquals(states.Get<SearchState>(ownSearch.Id, staleAdmin.SessionId), ownSearch) && ReferenceEquals(states.Get<CodeState>(otherCode.Id, "other-session"), otherCode), "Forbidden code operation removed unrelated state");
            Require(businessSessions.IsValid(staleAdmin.SessionId, "IRUSER"), "Permission downgrade expired a still-authorized STAFF session");
        });
        await CheckAsync("IR-D05-current-role-and-enabled-status-rechecked", async () =>
        {
            Require(repairId > 0, "Repair fixture is unavailable");
            try { await new CodeService(clean, businessRepository, currentActor, businessClock).ReadAsync(staleAdmin, "DEPARTMENT", CancellationToken.None); throw new InvalidOperationException("Stale ADMIN bypassed current STAFF permission"); }
            catch (BusinessException e) { Require(e.Outcome.MessageId == "MSG-003", "Current STAFF code access must be forbidden"); }
            Require((await businessService.ReportAsync(staleAdmin, repairId, CancellationToken.None)).Employee.EmployeeId == repairId, "ADMIN to STAFF removed an allowed report permission");
            await using (var unit = await clean.BeginAsync(true, CancellationToken.None))
            {
                await using var disable = unit.Command("UPDATE dbo.m_app_user SET is_enabled=0 WHERE user_id=N'IRUSER';"); Require(await disable.ExecuteNonQueryAsync() == 1, "Disable fixture missed its user"); await unit.CommitAsync(CancellationToken.None);
            }
            try { await businessService.ReportAsync(staleAdmin, repairId, CancellationToken.None); throw new InvalidOperationException("Disabled user retained report access"); }
            catch (BusinessException e) { Require(e.Outcome.MessageId == "MSG-002", "Disabled current user must expire authorization"); }
        });
    }
    catch (Exception e) { failed++; results.Add(new { id = "IR-SQL-SETUP", status = "FAIL", error = e.Message }); }
    finally
    {
        if (created)
        {
            try
            {
                await using (var check = new SqlConnection(options.ConnectionString)) { await check.OpenAsync(); await using var cmd = new SqlCommand("SELECT CONVERT(nvarchar(100),value) FROM sys.extended_properties WHERE class=0 AND name=N'IndependentReviewOwner';", check); Require((string?)await cmd.ExecuteScalarAsync() == owner, "Cleanup ownership proof failed"); }
                Require(dbName.StartsWith("SP2_WebFixture_IR_", StringComparison.Ordinal) && dbName.Length == 50, "Unsafe fixture identifier");
                var master = new SqlConnectionStringBuilder(options.ConnectionString) { InitialCatalog = "master" }; await using var connection = new SqlConnection(master.ConnectionString); await connection.OpenAsync();
                await using var drop = new SqlCommand($"ALTER DATABASE [{dbName}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE; DROP DATABASE [{dbName}];", connection); await drop.ExecuteNonQueryAsync();
            }
            catch (Exception e) { failed++; results.Add(new { id = "IR-SQL-CLEANUP", status = "FAIL", error = e.Message }); }
        }
    }
}
var sourceRoot = Directory.GetCurrentDirectory();
object Proof(string file) => new { path = Path.GetRelativePath(sourceRoot, file).Replace('\\', '/'), sha256 = Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(file))) };
var sources = Directory.GetFiles(Path.Combine(sourceRoot, "src"), "*.cs", SearchOption.AllDirectories).Where(file => !Path.GetRelativePath(sourceRoot, file).Replace('\\', '/').Split('/').Any(x => x is "bin" or "obj")).Order().Select(Proof).ToArray();
var testSources = Directory.GetFiles(Path.Combine(sourceRoot, "tests/IndependentInfrastructureReview")).Where(file => Path.GetExtension(file) is ".cs" or ".csproj").Order().Select(Proof).ToArray();
var runtimeArtifacts = new[] { typeof(EmployeeService).Assembly.Location, typeof(Validation).Assembly.Location, System.Reflection.Assembly.GetExecutingAssembly().Location }.Distinct().Select(Proof).ToArray();
var printContractInputs = new[] { "基本設計書/05_経歴書出力.md", "詳細仕様書/05_経歴書出力.md" }.Select(x => Proof(Path.GetFullPath(Path.Combine(sourceRoot, "../../spec/CSharp_ASPNET", x)))).ToArray();
var record = new { status = failed == 0 ? "PASS" : "FAIL", reviewer = "/root/req_desktop", startedAtUtc, finishedAtUtc = DateTimeOffset.UtcNow, checks = results.Count, failed, sqlScope, sources, testSources, runtimeArtifacts, printContractInputs, reportOutputs, results, scope = "Independent native GDI/ClosedXML full-text and normal/20-career output; OOXML font/full-width chapter/project heading/navy-line/gray-outline/geometry contracts; session/operation concurrency, owned SQL transaction faults, actual aggregate repair/current-role enforcement, and MVC filter HTTP-context tests. Actual Excel printing/native browser/user acceptance not performed.", formalScore = (int?)null };
var output = Path.Combine(sourceRoot, "build/test-results/independent-review/infrastructure.json"); Directory.CreateDirectory(Path.GetDirectoryName(output)!); await File.WriteAllTextAsync(output, JsonSerializer.Serialize(record, new JsonSerializerOptions { WriteIndented = true }));
Console.WriteLine(JsonSerializer.Serialize(new { record.status, record.checks, record.failed, record.sqlScope, output }));
foreach (var item in results.Select(x => JsonSerializer.Serialize(x)).Where(x => x.Contains("\"FAIL\"", StringComparison.Ordinal))) Console.WriteLine(item);
return failed == 0 ? 0 : 1;

sealed class FixtureWidth : ITextWidthMeasurer { public double Width(string text) => Validation.ScalarLength(text) * 10; }
sealed class ManualTime : TimeProvider { private DateTimeOffset now = DateTimeOffset.UtcNow; public override DateTimeOffset GetUtcNow() => now; public void Advance(TimeSpan value) => now += value; }
sealed class FixtureFaults : IDbFaults
{
    public bool RollbackFailure { get; init; } public bool AfterCommitFailure { get; init; }
    public void BeforeChildWrite() { } public void BeforeCommit() { } public void BeforeRead() { }
    public void AfterCommit() { if (AfterCommitFailure) throw new IOException("Independent fault after actual COMMIT"); }
    public void BeforeRollback() { if (RollbackFailure) throw new IOException("Independent fault before rollback acknowledgement"); }
}
