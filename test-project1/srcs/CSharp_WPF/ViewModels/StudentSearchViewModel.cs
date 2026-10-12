using System.Collections.ObjectModel;
using StudentManagement.Wpf.Commands;
using StudentManagement.Wpf.Services;

namespace StudentManagement.Wpf.ViewModels;

// SCR-STU-001 EV-SRC-001..006. AppliedCriteria is separate from editable Draft.
public sealed class StudentSearchViewModel : Bindable, IDisposable
{
    private readonly IStudentGateway gateway;
    private readonly NavigationService navigation;
    private readonly CancellationTokenSource lifetime = new();
    private SearchDraft? applied;
    private DateTimeOffset lastUsed;
    private int requestSequence;
    private bool busy;
    private bool ready;
    private bool refreshingClasses;
    public bool IsIdle => !busy;
    public bool CanSelectClassCriteria => IsIdle && !Draft.UnassignedOnly;
    private string message = "未検索";
    private string countText = "未検索";
    private string searchedAt = "";
    private int page = 1;
    private int? total;
    private LookupSet lookup = new(new Dictionary<string, IReadOnlyList<CodeOption>>(), []);
    public SearchDraft Draft { get; private set; } = new();
    public ObservableCollection<StudentListItem> Items { get; } = [];
    public ObservableCollection<YearOption> Years { get; } = [];
    public ObservableCollection<CodeOption> Grades { get; } = [];
    public ObservableCollection<CodeOption> Prefectures { get; } = [];
    public ObservableCollection<ClassOption> Classes { get; } = [];
    public ClassOption? SelectedClass
    {
        get => Classes.FirstOrDefault(x => x.SearchId == Draft.ClassId);
        set { if (!refreshingClasses) Draft.ClassId = value?.SearchId; }
    }
    public int[] PageSizes { get; } = [20, 50, 100];
    public CodeOption[] SortKeys { get; } = [new("studentNo", "学籍番号"), new("name", "氏名"), new("admissionDate", "入学日"), new("updatedAt", "更新日時")];
    public CodeOption[] Directions { get; } = [new("asc", "昇順"), new("desc", "降順")];
    public int PageSize { get; set; } = 20;
    public string SortKey { get; set; } = "studentNo";
    public string SortDirection { get; set; } = "asc";
    public bool Status01 { get; set; } = true;
    public bool Status02 { get; set; } = true;
    public bool Status03 { get; set; }
    public bool Status04 { get; set; }
    public bool CanEdit => gateway.CanEdit;
    public string Principal => gateway.Principal;
    public string Message { get => message; private set => Set(ref message, value); }
    public string CountText { get => countText; private set => Set(ref countText, value); }
    public string SearchedAt { get => searchedAt; private set => Set(ref searchedAt, value); }
    public bool HasSearched => applied is not null;
    public AsyncCommand SearchCommand { get; }
    public AsyncCommand ClearCommand { get; }
    public AsyncCommand NewCommand { get; }
    public AsyncCommand OpenCommand { get; }
    public AsyncCommand FirstCommand { get; }
    public AsyncCommand PreviousCommand { get; }
    public AsyncCommand NextCommand { get; }
    public AsyncCommand LastCommand { get; }
    public AsyncCommand SortCommand { get; }
    public StudentSearchViewModel(IStudentGateway gateway, NavigationService navigation)
    {
        this.gateway = gateway; this.navigation = navigation;
        ObserveDraft();
        void Error(Exception ex) { Items.Clear(); Message = ex is InvalidOperationException ? ex.Message : "E-COM-004 検索に失敗しました。"; }
        SearchCommand = new(_ => RunAsync(SearchNewAsync), () => ready && IsIdle, Error);
        ClearCommand = new(_ => { Clear(); return Task.CompletedTask; }, () => IsIdle, Error);
        NewCommand = new(_ => RunAsync(() => EditAsync(null)), () => CanEdit && ready && IsIdle, Error);
        OpenCommand = new(p => RunAsync(() => EditAsync(p is StudentListItem row ? row.StudentId : null)), () => ready && IsIdle, Error);
        FirstCommand = new(_ => RunAsync(() => MoveAsync(1)), () => IsIdle && total > 0 && page > 1, Error);
        PreviousCommand = new(_ => RunAsync(() => MoveAsync(page - 1)), () => IsIdle && total > 0 && page > 1, Error);
        NextCommand = new(_ => RunAsync(() => MoveAsync(page + 1)), () => IsIdle && total > 0 && page < MaxPage, Error);
        LastCommand = new(_ => RunAsync(() => MoveAsync(MaxPage)), () => IsIdle && total > 0 && page < MaxPage, Error);
        SortCommand = new(_ => RunAsync(() => MoveAsync(1)), () => IsIdle && HasSearched, Error);
    }
    private int MaxPage => total is > 0 ? (total.Value + PageSize - 1) / PageSize : 1;
    private void RefreshCommands()
    {
        foreach (var c in new[] { SearchCommand, ClearCommand, NewCommand, OpenCommand, FirstCommand, PreviousCommand, NextCommand, LastCommand, SortCommand }) c.RaiseCanExecuteChanged();
    }
    private async Task RunAsync(Func<Task> operation)
    {
        if (busy) return;
        busy = true; Changed(nameof(IsIdle)); Changed(nameof(CanSelectClassCriteria)); RefreshCommands();
        try { await operation(); }
        finally { busy = false; Changed(nameof(IsIdle)); Changed(nameof(CanSelectClassCriteria)); RefreshCommands(); }
    }
    public async Task InitializeAsync()
    {
        try
        {
            lookup = await gateway.LookupAsync(lifetime.Token,includeOccupancy:false);
            Years.Clear(); Years.Add(new(null, "すべて"));
            foreach (var year in lookup.Classes.Select(x => x.Year).Distinct().OrderDescending()) Years.Add(new(year, year.ToString()));
            Grades.Clear(); Grades.Add(new("", "すべて")); foreach (var x in lookup.Codes.GetValueOrDefault("GRADE") ?? []) Grades.Add(x);
            Prefectures.Clear(); Prefectures.Add(new("", "すべて")); foreach (var x in lookup.Codes.GetValueOrDefault("PREFECTURE") ?? []) Prefectures.Add(x);
            RefreshClasses(); Changed(nameof(CanEdit)); Changed(nameof(Principal)); NewCommand.RaiseCanExecuteChanged();
            ready = (lookup.Codes.GetValueOrDefault("ENROLLMENT_STATUS") ?? []).Any(x => x.Value == "01");
            if (!ready) Message = "E-COM-004 必須コードが不足しています。";
            RefreshCommands();
        }
        catch (Exception ex) { Message = ex is InvalidOperationException ? ex.Message : "E-COM-004 起動時のDB参照に失敗しました。"; }
    }
    public void MarkDraftChanged()
    {
        if (applied is not null) Message = "条件を変更しました。検索結果にはまだ反映されていません。";
    }
    private void ObserveDraft()
    {
        Draft.PropertyChanged += (_, e) => { MarkDraftChanged(); if (e.PropertyName == nameof(SearchDraft.ClassId)) Changed(nameof(SelectedClass)); if (e.PropertyName == nameof(SearchDraft.UnassignedOnly)) Changed(nameof(CanSelectClassCriteria)); };
    }
    public void RefreshClasses()
    {
        if (Draft.UnassignedOnly) { Draft.SchoolYear = null; Draft.GradeCode = null; Draft.ClassId = null; Changed(nameof(Draft)); }
        var classCleared = false;
        refreshingClasses = true;
        try
        {
            Classes.Clear();
            Classes.Add(new(0, 0, "", "すべて", true, 0, null));
            foreach (var x in lookup.Classes.Where(x => (Draft.SchoolYear is null || x.Year == Draft.SchoolYear) && (string.IsNullOrEmpty(Draft.GradeCode) || x.Grade == Draft.GradeCode))) Classes.Add(x);
            if (Draft.ClassId is > 0 && Classes.All(x => x.Id != Draft.ClassId)) { classCleared = true; Draft.ClassId = null; Message = "W-STU-107 選択条件が変わったためクラスの選択を解除しました。"; Changed(nameof(Draft)); }
        }
        finally { refreshingClasses = false; Changed(nameof(SelectedClass)); Changed(nameof(CanSelectClassCriteria)); }
        if (!classCleared && applied is not null) Message = "条件を変更しました。検索結果にはまだ反映されていません。";
    }
    public void SelectClass()
    {
        var selected = lookup.Classes.FirstOrDefault(x => x.Id == Draft.ClassId);
        if (selected is not null) { Draft.SchoolYear = selected.Year; Draft.GradeCode = selected.Grade; Changed(nameof(Draft)); }
    }
    private SearchDraft Snapshot()
    {
        var d = Draft.Clone();
        d.StatusCodes = new[] { ("01", Status01), ("02", Status02), ("03", Status03), ("04", Status04) }.Where(x => x.Item2).Select(x => x.Item1).ToArray();
        if (d.ClassId == 0) d.ClassId = null;
        if (d.SchoolYear == 0) d.SchoolYear = null;
        return d;
    }
    private async Task SearchNewAsync()
    {
        var draft = Snapshot();
        if (await ExecuteAsync(draft, 1)) { applied = draft.Clone(); lastUsed = DateTimeOffset.UtcNow; Changed(nameof(HasSearched)); SortCommand.RaiseCanExecuteChanged(); }
    }
    private async Task<bool> ExecuteAsync(SearchDraft criteria, int targetPage)
    {
        var generation = ++requestSequence;
        Items.Clear(); CountText = "検索中";
        var result = await gateway.SearchAsync(criteria, targetPage, PageSize, SortKey, SortDirection, lifetime.Token);
        if (lifetime.IsCancellationRequested || generation != requestSequence) return false;
        total = result.Total; page = targetPage;
        if (total is > 0 && page > MaxPage) return await ExecuteAsync(criteria, MaxPage);
        foreach (var item in result.Items) Items.Add(item);
        Message = result.Message;
        CountText = total is null ? "上限超過または検索失敗" : total == 0 ? "0件 0–0" : $"{total}件 {(page - 1) * PageSize + 1}–{Math.Min(page * PageSize, total.Value)} / {page}ページ";
        SearchedAt = result.SearchedAt.ToOffset(TimeSpan.FromHours(9)).ToString("yyyy/MM/dd HH:mm:ss");
        foreach (var command in new[] { FirstCommand, PreviousCommand, NextCommand, LastCommand }) command.RaiseCanExecuteChanged();
        return result.State == "Success";
    }
    private async Task MoveAsync(int targetPage)
    {
        if (applied is null) return;
        if (DateTimeOffset.UtcNow - lastUsed > TimeSpan.FromMinutes(30)) { Clear(); Message = "W-SRC-002 検索条件の保持期限が切れました。"; return; }
        await ExecuteAsync(applied, targetPage); lastUsed = DateTimeOffset.UtcNow;
    }
    private async Task EditAsync(long? id)
    {
        if (id is null && !CanEdit) return;
        var notice = await navigation.OpenEditorAsync(id);
        if (applied is not null) await MoveAsync(page);
        if (!string.IsNullOrEmpty(notice)) Message = notice;
    }
    public void Clear()
    {
        ++requestSequence; Draft = new(); ObserveDraft(); applied = null; page = 1; total = null; Items.Clear();
        PageSize = 20; SortKey = "studentNo"; SortDirection = "asc"; Status01 = Status02 = true; Status03 = Status04 = false;
        CountText = "未検索"; SearchedAt = ""; Message = "未検索";
        foreach (var p in new[] { nameof(Draft), nameof(PageSize), nameof(SortKey), nameof(SortDirection), nameof(Status01), nameof(Status02), nameof(Status03), nameof(Status04), nameof(HasSearched) }) Changed(p);
        RefreshClasses();
        foreach (var c in new[] { FirstCommand, PreviousCommand, NextCommand, LastCommand, SortCommand }) c.RaiseCanExecuteChanged();
    }
    public void Dispose() { ++requestSequence; lifetime.Cancel(); lifetime.Dispose(); }
}
