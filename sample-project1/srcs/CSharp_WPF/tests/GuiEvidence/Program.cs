using System.Text.Json;
using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Automation;
using System.Windows.Threading;
using System.Windows.Interop;
using System.Windows.Markup;
using System.Xml.Linq;
using StudentManagement.Wpf.Services;
using StudentManagement.Wpf.ViewModels;
using StudentManagement.Wpf.Views;

namespace Wpf.GuiEvidence;

internal static class Program
{
    [STAThread]
    private static int Main(string[] args)
    {
        var fixture = Path.Combine(AppContext.BaseDirectory, "fixture.json");
        if (args.SequenceEqual(new[] { "--self-test" })) return SelfTest(fixture);
        if (args.Length is not (2 or 4) || args[0] is not ("--screen" or "--verify-startup") || args[1] is not ("search" or "new" or "edit") || (args.Length == 4 && args[2] != "--role")) { Console.Error.WriteLine("Use --self-test or --screen search|new|edit [--role admin|staff|viewer] or --verify-startup search|new|edit"); return 2; }
        var app = new EvidenceApp(args[1], new PausableFixtureGateway(new FixtureGateway(fixture, args.Length == 4 ? args[3] : "admin")), args[0] == "--verify-startup");
        app.LoadProductionResources();
        return app.Run();
    }
    private static int SelfTest(string path)
    {
        var cases = new List<string>();
        void Check(bool ok, string id) { if (!ok) throw new Exception(id); cases.Add(id); }
        var gateway = new FixtureGateway(path);
        var app = new EvidenceApp("search",gateway,false); app.LoadProductionResources(); // Run/Show intentionally never invoked.
        Check(app.Resources.Count == 4 && app.Resources[typeof(System.Windows.Controls.TextBox)] is Style, "FIX-WPF-013 same loader reads original production App resources");
        var lookup = gateway.LookupAsync(default, false).GetAwaiter().GetResult();
        Check(lookup.Classes.All(c => c.Occupancy == 0), "FIX-WPF-001 search lookup omits occupancy");
        Check(gateway.LookupAsync(default).Result.Classes.Sum(c => c.Occupancy) == 2, "FIX-WPF-002 editor lookup fixture occupancy");
        using var search = new StudentSearchViewModel(gateway, new NavigationService(gateway));
        search.InitializeAsync().GetAwaiter().GetResult();
        Check(search.Classes[0].SearchId is null && search.Draft.ClassId is null, "FIX-WPF-015 all-class matches NULL criteria");
        search.SearchCommand.Execute(null);
        Check(search.Items.Count == 2 && search.CountText.StartsWith("2件"), "FIX-WPF-003 production search VM default status filter");
        search.Draft.StudentNo = "TEST-WPF-002"; search.SearchCommand.Execute(null);
        Check(search.Items.Count == 1 && search.Items[0].StudentName == "仮名 花子", "FIX-WPF-004 production search VM exact fixture");
        search.Draft.StudentNo = "TEST-NONE"; search.SearchCommand.Execute(null);
        Check(search.Items.Count == 0 && search.CountText == "0件 0–0", "FIX-WPF-005 production zero-results state");
        search.Clear(); Check(!search.HasSearched && search.Items.Count == 0, "FIX-WPF-006 production clear state");
        search.SearchCommand.Execute(null);
        var context=search.CaptureContext(); var revision=search.ContextRevision;
        Check(search.RestoreContext(context,revision),"COMPACT-WPF-001 current context restores");
        foreach(var field in new[]{"Owner","Session","StateId","WindowId"}) {
            var bad=System.Text.Json.Nodes.JsonNode.Parse(context)!.AsObject(); bad[field]="wrong"; var rejected=false;
            try { search.RestoreContext(bad.ToJsonString(),revision); } catch(InvalidOperationException ex) { rejected=ex.Message.Contains("E-COM-003"); }
            Check(rejected,"COMPACT-WPF-002 ownership boundary "+field);
        }
        var stale=false; try { search.RestoreContext(context,revision-1); } catch(InvalidOperationException) { stale=true; }
        Check(stale,"COMPACT-WPF-003 stale revision rejected");
        foreach(var field in new[]{"Kana","SchoolYear","GradeCode","UnassignedOnly","PrefectureCode","PhoneNumber","AdmissionFrom","AdmissionTo","Unexpected"}) {
            var bad=System.Text.Json.Nodes.JsonNode.Parse(context)!.AsObject(); bad["Criteria"]!.AsObject()[field]="obsolete"; var rejected=false;
            try { search.RestoreContext(bad.ToJsonString(),revision); } catch(InvalidOperationException ex) { rejected=ex.Message.Contains("E-COM-003"); }
            Check(rejected,"COMPACT-WPF-004 retired criteria "+field);
        }
        var state=System.Text.Json.Nodes.JsonNode.Parse(context)!.AsObject();state["SchemaVersion"]="student-search-old";
        Check(!search.RestoreContext(state.ToJsonString(),revision) && !search.HasSearched && search.Message.Contains("旧形式") && search.PageSize==20 && search.SortKey=="studentNo","COMPACT-WPF-005 legacy state fully resets");
        search.SearchCommand.Execute(null);state=System.Text.Json.Nodes.JsonNode.Parse(search.CaptureContext())!.AsObject();revision=search.ContextRevision;state.Remove("SchemaVersion");
        Check(!search.RestoreContext(state.ToJsonString(),revision) && search.Message.Contains("旧形式"),"COMPACT-WPF-006 missing schema resets");
        search.SearchCommand.Execute(null);state=System.Text.Json.Nodes.JsonNode.Parse(search.CaptureContext())!.AsObject();revision=search.ContextRevision;state["ExpiresAt"]=DateTimeOffset.UtcNow.AddMinutes(-1).ToString("O");
        Check(!search.RestoreContext(state.ToJsonString(),revision) && search.Message.Contains("W-SRC-002"),"COMPACT-WPF-007 expiry resets");
        search.Status01=search.Status02=search.Status03=search.Status04=false;search.SearchCommand.Execute(null);
        Check(search.Items.Count==3,"COMPACT-WPF-008 empty statuses means all");
        search.Draft.StudentNo="WPF-001";search.SearchCommand.Execute(null);
        Check(search.Items.Count==0,"COMPACT-WPF-009 student number prefix only");
        search.Clear();
        using var edit = new StudentEditViewModel(gateway, new DialogService(), 1);
        edit.InitializeAsync().GetAwaiter().GetResult();
        Check(edit.Model.StudentNo == "TEST-WPF-001" && edit.Model.StudentName == "仮名 太郎" && !edit.CanEditNumber, "FIX-WPF-007 production editor loads fixture immutable number");
        var before = edit.Model.StudentName; edit.SaveCommand.Execute(null);
        Check(edit.Message.Contains("DB未接続") && edit.Model.StudentName == before && edit.ResultNotice == "", "FIX-WPF-008 fixture refuses persistence without claiming saved");
        using var create = new StudentEditViewModel(gateway, new DialogService(), null);
        create.InitializeAsync().GetAwaiter().GetResult();
        Check(create.CanEditNumber && create.Model.StudentNo == "" && create.Model.GenderCode == "0", "FIX-WPF-009 production new defaults");
        Check(create.Classes[0].Value == "" && edit.Classes.Any(c => c.Value == edit.Model.ClassId), "FIX-WPF-014 registration selection keys match empty/raw string ID");
        using var viewer = new StudentEditViewModel(new FixtureGateway(path,"viewer"),new DialogService(),1);
        viewer.InitializeAsync().GetAwaiter().GetResult();
        Check(!viewer.CanEdit && !viewer.CanDelete && viewer.Title.Contains("参照"), "FIX-WPF-010 fixture viewer display flags only");
        var view = new StudentSearchView { DataContext = search }; var editor = new StudentEditView { DataContext = edit };
        Check(view.Content is not null && editor.Content is not null, "FIX-WPF-011 real production XAML constructs");
        var detail = gateway.GetAsync(1, default).Result; detail.Values["StudentName"] = "試験変更";
        Check(gateway.GetAsync(1, default).Result.Values["StudentName"] == "仮名 太郎", "FIX-WPF-012 fixture read returns detached values");
        Console.WriteLine(JsonSerializer.Serialize(new {profile="CSharp_WPF",passed=cases.Count,failed=0,cases,database="NOT_RUN",interactiveUI="NOT_RUN",screenshots="NOT_RUN",backend="fixture"}));
        return 0;
    }
    private sealed class PausableFixtureGateway(FixtureGateway inner) : IStudentGateway
    {
        private TaskCompletionSource<SearchResult>? pending;
        private SearchResult? result;
        public bool CanEdit => inner.CanEdit;
        public bool CanDelete => inner.CanDelete;
        public string Principal => inner.Principal;
        public string SessionId => inner.SessionId;
        public void HoldNextSearch() => pending = new();
        public void ReleaseSearch() { var held = pending; pending = null; held?.SetResult(result ?? throw new InvalidOperationException("No held search result")); }
        public Task<LookupSet> LookupAsync(CancellationToken ct, bool includeOccupancy = true) => inner.LookupAsync(ct, includeOccupancy);
        public Task<SearchResult> SearchAsync(SearchDraft draft, int page, int pageSize, string sort, string direction, CancellationToken ct)
        {
            var completed = inner.SearchAsync(draft, page, pageSize, sort, direction, ct);
            if (pending is null) return completed;
            result = completed.GetAwaiter().GetResult();
            return pending.Task;
        }
        public Task<StudentRecord> GetAsync(long id, CancellationToken ct) => inner.GetAsync(id, ct);
        public Task<SaveResult> SaveAsync(long? id, long? version, Dictionary<string, string> raw, string? confirmation, string reason, CancellationToken ct) => inner.SaveAsync(id, version, raw, confirmation, reason, ct);
        public Task<SaveResult> DeleteAsync(long id, long version, string reason, CancellationToken ct) => inner.DeleteAsync(id, version, reason, ct);
    }
    private sealed class EvidenceApp(string screen, IStudentGateway gateway, bool verifyStartup) : Application
    {
        public void LoadProductionResources()
        {
            // Read the unchanged production source, copied by MSBuild. App's generated
            // InitializeComponent expects its own assembly and cannot load into a subclass.
            XNamespace presentation = "http://schemas.microsoft.com/winfx/2006/xaml/presentation";
            var source = XDocument.Load(Path.Combine(AppContext.BaseDirectory,"Production.App.xml"));
            var original = source.Root!.Element(presentation + "Application.Resources") ?? throw new InvalidDataException("Production resources missing.");
            var dictionary = new XElement(presentation + "ResourceDictionary",new XAttribute("xmlns",presentation.NamespaceName),new XAttribute(XNamespace.Xmlns + "x","http://schemas.microsoft.com/winfx/2006/xaml"),original.Elements().Select(e => new XElement(e)));
            using var reader = dictionary.CreateReader();
            Resources = (ResourceDictionary)XamlReader.Load(reader);
        }
        private void VerifyWhenRendered(Window window)
        {
            if (!verifyStartup) return;
            window.ContentRendered += (_,_) =>
            {
                try
                {
                    if (!window.IsVisible || !window.IsLoaded || new WindowInteropHelper(window).Handle == IntPtr.Zero || Resources.Count != 4) throw new Exception("Actual Window/resources did not initialize.");
                    var populated = screen switch
                    {
                        "search" => window.DataContext is StudentSearchViewModel s && s.Items.Count == 2 && s.HasSearched,
                        "edit" => window.DataContext is StudentEditViewModel e && e.Model.StudentNo == "TEST-WPF-001",
                        _ => window.DataContext is StudentEditViewModel n && n.CanEditNumber && n.Model.StudentNo == ""
                    };
                    if (!populated) throw new Exception("Production Window did not bind fixture data/defaults.");
                    var searchChecks = new List<string>();
                    IEnumerable<DependencyObject> Descendants(DependencyObject parent) { for(int i=0;i<System.Windows.Media.VisualTreeHelper.GetChildrenCount(parent);i++) { var child=System.Windows.Media.VisualTreeHelper.GetChild(parent,i); yield return child; foreach(var nested in Descendants(child)) yield return nested; } }
                    if (screen == "search" && window.DataContext is StudentSearchViewModel search)
                    {
                        var grid=Descendants(window).OfType<DataGrid>().Single();
                        if(grid.Columns.Count != 7) throw new Exception("Compact grid must expose 7 columns.");
                        searchChecks.Add("compact-seven-columns");
                        var combos=Descendants(window).OfType<ComboBox>().Where(c=>AutomationProperties.GetName(c)=="クラス").ToArray();
                        if(combos.Length!=1 || search.Classes[0].SearchId is not null) throw new Exception("Class selector must retain all option.");
                        combos[0].SelectedItem=search.Classes.Single(c=>c.Id==101);
                        window.Dispatcher.Invoke(()=>{},DispatcherPriority.DataBind);
                        if(search.Draft.ClassId!=101) throw new Exception("Class selector must bind Int64 ID.");
                        searchChecks.Add("class-id-only-selection");
                        if(gateway is not PausableFixtureGateway held) throw new Exception("Pausable fixture required.");
                        held.HoldNextSearch();search.SearchCommand.Execute(null);
                        window.Dispatcher.Invoke(()=>{},DispatcherPriority.DataBind);
                        if(search.IsIdle || combos[0].IsEnabled) throw new Exception("Busy search must disable criteria.");
                        held.ReleaseSearch();
                        window.Dispatcher.Invoke(()=>{},DispatcherPriority.DataBind);
                        if(!search.IsIdle || !combos[0].IsEnabled) throw new Exception("Completed search must enable criteria.");
                        searchChecks.Add("busy-reentry-controls");
                        search.Clear();
                        if(search.Draft.ClassId is not null || search.Classes[0].SearchId is not null) throw new Exception("Clear must restore all classes.");
                        searchChecks.Add("clear-all-classes");
                    }
                    if(screen != "search") {
                        foreach(var width in new[]{1280,1366}) {
                            window.Width=width;window.Height=650;window.UpdateLayout();
                            var root=(ScrollViewer)window.Content;
                            if(root.ComputedHorizontalScrollBarVisibility==Visibility.Visible || root.ComputedVerticalScrollBarVisibility==Visibility.Visible) throw new Exception($"Compact editor unexpectedly scrolls at {width}x650: extent={root.ExtentWidth}x{root.ExtentHeight}, viewport={root.ViewportWidth}x{root.ViewportHeight}");
                            var evidence=Environment.GetEnvironmentVariable("STUDENT_UI_EVIDENCE_DIR");
                            if(!string.IsNullOrEmpty(evidence)) {
                                Directory.CreateDirectory(evidence);
                                var bitmap=new System.Windows.Media.Imaging.RenderTargetBitmap((int)window.ActualWidth,(int)window.ActualHeight,96,96,System.Windows.Media.PixelFormats.Pbgra32);bitmap.Render(window);
                                var encoder=new System.Windows.Media.Imaging.PngBitmapEncoder();encoder.Frames.Add(System.Windows.Media.Imaging.BitmapFrame.Create(bitmap));using var output=File.Create(Path.Combine(evidence,$"{screen}-{width}.png"));encoder.Save(output);
                            }
                            searchChecks.Add($"compact-editor-visible-{width}x650");
                        }
                        var editorModel=(StudentEditViewModel)window.DataContext;
                        var address=Descendants(window).OfType<TextBox>().Single(box=>AutomationProperties.GetName(box)=="住所1");
                        if(!editorModel.CanEdit && (!address.IsReadOnly || !address.IsEnabled || !address.Focus()))throw new Exception("Viewer must be able to focus and inspect the full readonly value.");
                        if(!editorModel.CanEdit)searchChecks.Add("viewer-readonly-full-value-focus");
                        var reference=Descendants(window).OfType<TextBlock>().Single(block=>AutomationProperties.GetName(block)=="所属人数・定員");
                        if(!reference.Text.Contains("参考"))throw new Exception("Occupancy must remain visible as reference data.");
                        searchChecks.Add("dedicated-occupancy-reference");
                        window.Width=760;window.Height=650;window.UpdateLayout();
                        var narrow=(ScrollViewer)window.Content;
                        if(narrow.ComputedHorizontalScrollBarVisibility==Visibility.Visible || narrow.ComputedVerticalScrollBarVisibility!=Visibility.Visible)throw new Exception("Narrow editor must reflow vertically without horizontal scrolling.");
                        var back=Descendants(window).OfType<Button>().Single(button=>ReferenceEquals(button.Command,editorModel.BackCommand));
                        back.BringIntoView();window.UpdateLayout();
                        var bounds=back.TransformToAncestor(narrow).TransformBounds(new Rect(back.RenderSize));
                        if(bounds.Top<0 || bounds.Bottom>narrow.ActualHeight)throw new Exception("Narrow editor back action must remain reachable.");
                        searchChecks.Add("narrow-editor-reflow-and-actions-reachable");
                    }
                    Console.WriteLine(JsonSerializer.Serialize(new {profile="CSharp_WPF",screen,passed=true,window=window.GetType().FullName,title=window.Title,visible=window.IsVisible,loaded=window.IsLoaded,hwnd=new WindowInteropHelper(window).Handle.ToInt64(),resourceCount=Resources.Count,searchChecks,backend="fixture",database="NOT_RUN",interactiveUI=(screen == "search" ? "STARTUP_AND_FIXTURE_FILTER_DEFAULTS" : "STARTUP_ONLY_NO_OPERATIONS"),screenshots="RenderTargetBitmap when STUDENT_UI_EVIDENCE_DIR is set"}));
                    window.Close();
                }
                catch(Exception ex) { Console.Error.WriteLine(ex.ToString()); Shutdown(1); }
            };
        }
        protected override void OnStartup(StartupEventArgs e)
        {
            base.OnStartup(e); // Application base only; production App/SQL startup is not used.
            if (screen == "search")
            {
                var vm = new StudentSearchViewModel(gateway, new NavigationService(gateway));
                var window = new StudentSearchView { DataContext = vm };
                MainWindow = window;
                window.Loaded += async (_,_) => { await vm.InitializeAsync(); vm.SearchCommand.Execute(null); };
                window.Closed += (_,_) => vm.Dispose(); VerifyWhenRendered(window); window.Show();
            }
            else
            {
                var vm = new StudentEditViewModel(gateway,new DialogService(),screen == "edit" ? 1 : null);
                var window = new StudentEditView { DataContext = vm }; MainWindow=window;
                vm.CloseRequested=window.Close; window.Loaded += async (_,_) => await vm.InitializeAsync();
                window.Closing += (_,e) => e.Cancel = !vm.CanClose(); window.Closed += (_,_) => vm.Dispose(); VerifyWhenRendered(window); window.Show();
            }
        }
    }
}
