using System.Security.Cryptography;
using System.Text.Json;
using CareerManagement.Application;

var results = new List<object>();
var failed = 0;
void Check(string id, Action test)
{
    try { test(); results.Add(new { id, status = "PASS" }); }
    catch (Exception e) { failed++; results.Add(new { id, status = "FAIL", error = e.Message }); }
}
static void Equal<T>(T expected, T actual)
{
    if (!EqualityComparer<T>.Default.Equals(expected, actual)) throw new InvalidOperationException($"Expected {expected}; got {actual}");
}
static void Error(Action action, int number, string? item = null)
{
    try { action(); }
    catch (BusinessException e)
    {
        Equal($"MSG-{number:000}", e.Outcome.MessageId);
        if (item is not null) Equal(item, e.Outcome.FieldErrors.Single().ItemId);
        return;
    }
    throw new InvalidOperationException($"Expected MSG-{number:000}; operation was accepted");
}
var date = new DateOnly(2026, 10, 28);
SearchInput Search(string name) => new("fixture", 1, null, name, null, null);
EmployeeRaw Employee(string name) => new("000004", name, "ヤマダ タロウ", "01", "01", "2020-01-01", null, null, null, null);
CareerRaw Career() => new(1, Guid.NewGuid(), "2020-01", "2020-01", "架空会社", "架空案件", "概要", "担当", null, null, null, "01", "1");
Check("IR-V01-search-raw40", () => Equal(40, Validation.ScalarLength(Validation.Search(Search(new string('名', 40))).Name!)));
Check("IR-V02-search-raw41-rejected", () => Error(() => Validation.Search(Search(new string('名', 41))), 5, "F03-I02"));
Check("IR-V03-search-normalized-expansion-rejected", () => Error(() => Validation.Search(Search("\uFDFA\uFDFA\uFDFA")), 5, "F03-I02"));
Check("IR-V04-search-symbols-literal", () => Equal("%_*?[]", Validation.SearchKey(Validation.Search(Search("%_*?[]")).Name)));
Check("IR-V05-name40-supplementary", () => Equal(40, Validation.ScalarLength(Validation.Employee(Employee(string.Concat(Enumerable.Repeat("🐱", 40))), date).Name)));
Check("IR-V06-name41-rejected", () => Error(() => Validation.Employee(Employee(string.Concat(Enumerable.Repeat("🐱", 41))), date), 5, "F04-I02"));
Check("IR-V07-invalid-surrogate-rejected", () => Error(() => Validation.Employee(Employee("\uD800"), date), 5));
Check("IR-V08-kana-normalization", () => Equal("ヤマダ タロウ", Validation.Employee(Employee("架空氏名") with { Kana = "ﾔﾏﾀﾞ ﾀﾛｳ" }, date).Kana));
Check("IR-V09-kana-invalid-script", () => Error(() => Validation.Employee(Employee("架空氏名") with { Kana = "abc" }, date), 5, "F04-I03"));
Check("IR-V10-new-employee-date-empty", () => Equal("", EmployeeRaw.Empty(date).JoinDateRaw));
Check("IR-V11-new-career-team-empty", () => Equal("", CareerRaw.Empty().TeamSizeRaw));
var fieldCases = new (string Id, CareerRaw Raw, int Message, string Item)[]
{
    ("IR-F14-start", Career() with { StartMonthRaw = "bad" }, 5, "F04-I14"),
    ("IR-F15-end", Career() with { EndMonthRaw = "bad" }, 5, "F04-I15"),
    ("IR-F16-company", Career() with { CompanyName = "" }, 4, "F04-I16"),
    ("IR-F17-project", Career() with { ProjectName = "" }, 4, "F04-I17"),
    ("IR-F18-description", Career() with { Description = "" }, 4, "F04-I18"),
    ("IR-F19-duties", Career() with { Duties = "" }, 4, "F04-I19"),
    ("IR-F20-achievement", Career() with { Achievements = new string('文', 1001) }, 5, "F04-I20"),
    ("IR-F21-technologies", Career() with { Technologies = new string('文', 501) }, 5, "F04-I21"),
    ("IR-F22-phases", Career() with { Phases = new string('文', 201) }, 5, "F04-I22"),
    ("IR-F23-role", Career() with { RoleCode = "00" }, 5, "F04-I23"),
    ("IR-F24-team", Career() with { TeamSizeRaw = "0" }, 5, "F04-I24")
};
foreach (var item in fieldCases) Check(item.Id, () => Error(() => Validation.Career(item.Raw, new(2026, 10, 1), 1), item.Message, item.Item));
Check("IR-C01-same-month-allowed", () => Equal(new DateOnly(2020, 1, 1), Validation.Career(Career(), new(2026, 10, 1), 1).Values.EndMonth));
Check("IR-C02-eleven-value-duplicate", () => Error(() => Validation.Careers([Career(), Career() with { CareerId = 2 }], new(2026, 10, 1)), 26));
Check("IR-C03-one-value-difference", () => Equal(2, Validation.Careers([Career(), Career() with { CareerId = 2, Duties = "別担当" }], new(2026, 10, 1)).Length));
var one = Validation.Career(Career(), new(2026, 10, 1), 1);
var two = one with { CareerId = 2, ClientRowKey = Guid.NewGuid(), Values = one.Values with { Duties = "別担当" } };
var snapshot = new EmployeeSnapshot(1, 1, Validation.Employee(Employee("架空氏名"), date), [one, two], DateTimeOffset.UtcNow, "FIXTURE");
Check("IR-S01-keep-remove-partition", () => Validation.ChildSet(snapshot, [one], [2]));
Check("IR-S02-missing-loaded-id", () => Error(() => Validation.ChildSet(snapshot, [one], []), 25));
Check("IR-S03-retained-and-removed", () => Error(() => Validation.ChildSet(snapshot, [one, two], [2]), 25));
Check("IR-S04-duplicate-retained", () => Error(() => Validation.ChildSet(snapshot, [one, one], [2]), 25));
Check("IR-S05-unknown-retained", () => Error(() => Validation.ChildSet(snapshot, [one with { CareerId = 999 }, two], []), 25));
Check("IR-S06-existing-id-in-new-parent", () => Error(() => Validation.ChildSet(null, [one], []), 25));
CodeRow[] codes = [new("PROJECT_ROLE", "01", "停止役割", 1, false, 1)];
Check("IR-R01-stopped-existing-preserved", () => Validation.Reference(codes, "PROJECT_ROLE", "01", "01"));
Check("IR-R02-stopped-new-rejected", () => Error(() => Validation.Reference(codes, "PROJECT_ROLE", "01", null), 16));
Check("IR-R03-missing-reference-rejected", () => Error(() => Validation.Reference(codes, "PROJECT_ROLE", "02", null), 16));
Check("IR-R04-fixed-category-protected", () => Error(() => Validation.CodeInput(new("fixture", 1, "EMPLOYMENT_STATUS", "01", "変更", "1", true, 1)), 23));
var sourceRoot = Directory.GetCurrentDirectory();
var inputs = Directory.GetFiles(Path.Combine(sourceRoot, "src/CareerManagement.Application"), "*.cs").Order().Select(file => new
{
    path = Path.GetRelativePath(sourceRoot, file).Replace('\\', '/'), sha256 = Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(file)))
}).ToArray();
var testSources = Directory.GetFiles(Path.Combine(sourceRoot, "tests/IndependentReview")).Where(file => Path.GetExtension(file) is ".cs" or ".csproj").Order().Select(file => new { path = Path.GetRelativePath(sourceRoot, file).Replace('\\', '/'), sha256 = Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(file))) }).ToArray();
var runtimeArtifactSha256 = Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(System.Reflection.Assembly.GetExecutingAssembly().Location)));
var record = new { status = failed == 0 ? "PASS" : "FAIL", reviewer = "/root/req_desktop", finishedAtUtc = DateTimeOffset.UtcNow, checks = results.Count, failed, inputs, testSources, runtimeArtifactSha256, results,
    scope = "Independent executable Application validation/initial-state/item-ID/child-set/stopped-reference tests only; no SQL, native UI, runtime save/commit, workbook or acceptance claim.", formalScore = (int?)null };
var output = Path.Combine(sourceRoot, "build/test-results/independent-review/application.json");
Directory.CreateDirectory(Path.GetDirectoryName(output)!);
File.WriteAllText(output, JsonSerializer.Serialize(record, new JsonSerializerOptions { WriteIndented = true }));
Console.WriteLine(JsonSerializer.Serialize(new { record.status, record.checks, record.failed, output }));
foreach (var item in results.Select(x => JsonSerializer.Serialize(x)).Where(x => x.Contains("\"FAIL\"", StringComparison.Ordinal))) Console.WriteLine(item);
return failed == 0 ? 0 : 1;
