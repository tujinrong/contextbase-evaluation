using StudentManagement.Wpf.Services;
using StudentManagement.Wpf.ViewModels;
using StudentManagement.Wpf.Views;


static class NativeSmoke
{
    static int checks;
    static void Check(bool condition, string label) { if (!condition) throw new Exception(label); checks++; }
    [STAThread]
    static void Main()
    {
        var app = new StudentManagement.Wpf.App(); app.InitializeComponent();
        var gateway = new FakeGateway();
        using var vm = new StudentSearchViewModel(gateway, new NavigationService(gateway));
        vm.InitializeAsync().GetAwaiter().GetResult();
        Check(vm.Classes[0].SearchId is null, "all-classes option uses nullable Int64");
        Check(vm.SearchCommand.CanExecute(null), "search enabled after lookup");
        var searchView = new StudentSearchView { DataContext = vm };
        searchView.Measure(new System.Windows.Size(1320, 900)); searchView.Arrange(new System.Windows.Rect(0, 0, 1320, 900));
        vm.SearchCommand.Execute(null);
        Check(vm.Items.Count == 1 && vm.HasSearched, "search binds one result");
        vm.Draft.Name = "変更";
        Check(vm.Items.Count == 1 && vm.Message.Contains("まだ反映"), "editing draft does not replace applied results");
        vm.Draft.ClassId = 9007199254740993;
        Check(vm.SelectedClass?.Id == 9007199254740993, "class criteria retains Int64 ID");
        Check(typeof(SearchDraft).GetProperties().All(p => p.Name is not ("Kana" or "SchoolYear" or "GradeCode" or "UnassignedOnly" or "PrefectureCode" or "PhoneNumber" or "AdmissionFrom" or "AdmissionTo")), "retired criteria absent from native typed boundary");
        vm.Clear(); Check(vm.Items.Count == 0 && !vm.HasSearched && vm.CountText == "未検索", "clear resets context");
        using var editor = new StudentEditViewModel(gateway, new DialogService(), null);
        var editView = new StudentEditView { DataContext = editor };
        editView.Measure(new System.Windows.Size(1200, 900)); editView.Arrange(new System.Windows.Rect(0, 0, 1200, 900));
        Check(editView.Content is not null, "WPF edit XAML constructs");
        Console.WriteLine($"WPF smoke: {checks} checks passed; no windows shown; no DB connection opened.");
    }
    sealed class FakeGateway : IStudentGateway
    {
        public string SessionId => "smoke-session";
        public bool CanEdit => true; public bool CanDelete => true; public string Principal => "test-principal";
        public Task<LookupSet> LookupAsync(CancellationToken ct,bool includeOccupancy=true) => Task.FromResult(new LookupSet(new Dictionary<string, IReadOnlyList<CodeOption>> { ["ENROLLMENT_STATUS"] = [new("01", "在学")], ["GRADE"] = [new("01", "1年")], ["PREFECTURE"] = [] }, [new(9007199254740993, 2026, "01", "1A", true, 0, 30)]));
        public Task<SearchResult> SearchAsync(SearchDraft draft, int page, int pageSize, string sort, string direction, CancellationToken ct) => Task.FromResult(new SearchResult("Success", 1, [new(9007199254740993, "S01", "学生", "ガクセイ", "平成20年1月1日", "2026 / 1年", "1A", "在学")], "検索完了", DateTimeOffset.UtcNow));
        public Task<StudentRecord> GetAsync(long id, CancellationToken ct) => throw new NotSupportedException();
        public Task<SaveResult> SaveAsync(long? id, long? version, Dictionary<string, string> raw, string? confirmation, string reason, CancellationToken ct) => throw new NotSupportedException();
        public Task<SaveResult> DeleteAsync(long id, long version, string reason, CancellationToken ct) => throw new NotSupportedException();
    }
}
