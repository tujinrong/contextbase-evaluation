using System.Text.Json;
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
    public const string SearchSchema = "student-search-compact-1";
    private readonly string windowId = Guid.NewGuid().ToString("D");
    private readonly string stateId = Guid.NewGuid().ToString("D");
    private string contextOwner = "", contextSession = "";
    public long ContextRevision { get; private set; }
    private sealed record Context(string? SchemaVersion, string StateId, string WindowId, string Owner, string Session, long Revision, DateTimeOffset ExpiresAt, SearchDraft? Criteria, int Page, int PageSize, string SortKey, string SortDirection);
    private SearchDraft? applied;
    private DateTimeOffset lastUsed;
    private long requestSequence;
    private bool busy;
    private bool ready;
    private bool refreshingClasses;
    public bool IsIdle => !busy;
    public bool CanSelectClassCriteria => IsIdle;
    private string message = "未検索";
    private string countText = "未検索";
    private string searchedAt = "";
    private int page = 1;
    private int? total;
    private LookupSet lookup = new(new Dictionary<string, IReadOnlyList<CodeOption>>(), []);
    public SearchDraft Draft { get; private set; } = new();
    public ObservableCollection<StudentListItem> Items { get; } = [];
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
    private bool status01=true,status02=true,status03,status04;
    public bool Status01 { get => status01; set { if(Set(ref status01,value)) MarkDraftChanged(); } }
    public bool Status02 { get => status02; set { if(Set(ref status02,value)) MarkDraftChanged(); } }
    public bool Status03 { get => status03; set { if(Set(ref status03,value)) MarkDraftChanged(); } }
    public bool Status04 { get => status04; set { if(Set(ref status04,value)) MarkDraftChanged(); } }
    public bool CanEdit => gateway.CanEdit;
    public string Principal => gateway.Principal;
    public string NewVisibility => CanEdit ? "Visible" : "Collapsed";
    public string OpenLabel => CanEdit ? "編集" : "参照";
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
            RefreshClasses(); Changed(nameof(CanEdit)); Changed(nameof(Principal)); Changed(nameof(NewVisibility)); Changed(nameof(OpenLabel)); NewCommand.RaiseCanExecuteChanged();
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
        Draft.PropertyChanged += (_, e) => { MarkDraftChanged(); if (e.PropertyName == nameof(SearchDraft.ClassId)) Changed(nameof(SelectedClass)); };
    }
    public void RefreshClasses()
    {
        refreshingClasses = true;
        try {
            Classes.Clear(); Classes.Add(new(0, 0, "", "すべて", true, 0, null));
            foreach (var x in lookup.Classes.OrderByDescending(x => x.Year).ThenBy(x => x.Grade).ThenBy(x => x.Name)) Classes.Add(x);
        } finally { refreshingClasses = false; Changed(nameof(SelectedClass)); }
    }
    public string CaptureContext() => JsonSerializer.Serialize(new Context(SearchSchema,stateId,windowId,contextOwner,contextSession,ContextRevision,lastUsed.AddMinutes(30),applied,page,PageSize,SortKey,SortDirection));
    public bool RestoreContext(string serialized, long expectedRevision)
    {
        try {
            using var document = JsonDocument.Parse(serialized);
            var root = document.RootElement;
            if (root.GetProperty("StateId").GetString() != stateId || root.GetProperty("WindowId").GetString() != windowId || root.GetProperty("Owner").GetString() != gateway.Principal || root.GetProperty("Session").GetString() != gateway.SessionId || root.GetProperty("Revision").GetInt64() != ContextRevision || expectedRevision != ContextRevision)
                throw new InvalidOperationException("E-COM-003 検索状態の所有者・画面・版が一致しません。");
            if (lastUsed.AddMinutes(30) <= DateTimeOffset.UtcNow || root.GetProperty("ExpiresAt").GetDateTimeOffset() <= DateTimeOffset.UtcNow) { Clear(); Message = "W-SRC-002 検索条件の保持期限が切れました。"; return false; }
            if (!root.TryGetProperty("SchemaVersion",out var schema) || schema.GetString() != SearchSchema) { Clear(); Message = "旧形式の検索状態のため初期化しました。"; return false; }
            var context = JsonSerializer.Deserialize<Context>(serialized, new JsonSerializerOptions { UnmappedMemberHandling = System.Text.Json.Serialization.JsonUnmappedMemberHandling.Disallow })!;
            if (context.Page < 1 || context.PageSize is not (20 or 50 or 100) || context.SortKey is not ("studentNo" or "name" or "admissionDate" or "updatedAt") || context.SortDirection is not ("asc" or "desc")) throw new JsonException("Invalid context controls");
            applied = context.Criteria?.Clone(); page=context.Page; PageSize=context.PageSize; SortKey=context.SortKey; SortDirection=context.SortDirection;
            return applied is not null;
        } catch(JsonException ex) { throw new InvalidOperationException("E-COM-003 検索状態に未知・廃止項目があります。",ex); }
    }
    private SearchDraft Snapshot()
    {
        var d = Draft.Clone();
        d.StatusCodes = new[] { ("01", Status01), ("02", Status02), ("03", Status03), ("04", Status04) }.Where(x => x.Item2).Select(x => x.Item1).ToArray();
        if (d.ClassId == 0) d.ClassId = null;
        return d;
    }
    private async Task SearchNewAsync()
    {
        var draft = Snapshot();
        if (await ExecuteAsync(draft, 1)) { applied = draft.Clone(); lastUsed = DateTimeOffset.UtcNow; contextOwner=gateway.Principal; contextSession=gateway.SessionId; ContextRevision=checked(ContextRevision+1); Changed(nameof(HasSearched)); SortCommand.RaiseCanExecuteChanged(); }
    }
    private async Task<bool> ExecuteAsync(SearchDraft criteria, int targetPage)
    {
        var generation = requestSequence = checked(requestSequence+1);
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
        if (!RestoreContext(CaptureContext(),ContextRevision)) return;
        await ExecuteAsync(applied!, targetPage); lastUsed = DateTimeOffset.UtcNow; ContextRevision=checked(ContextRevision+1);
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
        ContextRevision=checked(ContextRevision+1); requestSequence=checked(requestSequence+1); Draft = new(); ObserveDraft(); applied = null; page = 1; total = null; Items.Clear();
        PageSize = 20; SortKey = "studentNo"; SortDirection = "asc"; Status01 = Status02 = true; Status03 = Status04 = false;
        CountText = "未検索"; SearchedAt = ""; Message = "未検索";
        foreach (var p in new[] { nameof(Draft), nameof(PageSize), nameof(SortKey), nameof(SortDirection), nameof(Status01), nameof(Status02), nameof(Status03), nameof(Status04), nameof(HasSearched) }) Changed(p);
        RefreshClasses();
        foreach (var c in new[] { FirstCommand, PreviousCommand, NextCommand, LastCommand, SortCommand }) c.RaiseCanExecuteChanged();
    }
    public void Dispose() { ++requestSequence; lifetime.Cancel(); lifetime.Dispose(); }
}
