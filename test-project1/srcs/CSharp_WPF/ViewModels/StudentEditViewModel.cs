using System.Text.Json;
using StudentManagement.Wpf.Commands;
using StudentManagement.Wpf.Services;

namespace StudentManagement.Wpf.ViewModels;

public sealed class EditModel : Bindable
{
    private Dictionary<string, string> values = [];
    public string this[string field] { get => values.GetValueOrDefault(field) ?? ""; set { if (this[field] != value) { values[field] = value; Changed("Item[]"); Changed(field); } } }
    public string StudentNo { get => this["StudentNo"]; set => this["StudentNo"] = value; }
    public string StudentName { get => this["StudentName"]; set => this["StudentName"] = value; }
    public string StudentNameKana { get => this["StudentNameKana"]; set => this["StudentNameKana"] = value; }
    public string BirthEra { get => this["BirthEra"]; set => this["BirthEra"] = value; }
    public string BirthYear { get => this["BirthYear"]; set => this["BirthYear"] = value; }
    public string BirthMonth { get => this["BirthMonth"]; set => this["BirthMonth"] = value; }
    public string BirthDay { get => this["BirthDay"]; set => this["BirthDay"] = value; }
    public string GenderCode { get => this["GenderCode"]; set => this["GenderCode"] = value; }
    public string PostalCode { get => this["PostalCode"]; set => this["PostalCode"] = value; }
    public string PrefectureCode { get => this["PrefectureCode"]; set => this["PrefectureCode"] = value; }
    public string AddressLine1 { get => this["AddressLine1"]; set => this["AddressLine1"] = value; }
    public string AddressLine2 { get => this["AddressLine2"]; set => this["AddressLine2"] = value; }
    public string PhoneNumber { get => this["PhoneNumber"]; set => this["PhoneNumber"] = value; }
    public string EmailAddress { get => this["EmailAddress"]; set => this["EmailAddress"] = value; }
    public string AdmissionDate { get => this["AdmissionDate"]; set => this["AdmissionDate"] = value; }
    public string EnrollmentStatusCode { get => this["EnrollmentStatusCode"]; set => this["EnrollmentStatusCode"] = value; }
    public string EnrollmentEndDate { get => this["EnrollmentEndDate"]; set => this["EnrollmentEndDate"] = value; }
    public string SchoolYear { get => this["SchoolYear"]; set => this["SchoolYear"] = value; }
    public string GradeCode { get => this["GradeCode"]; set => this["GradeCode"] = value; }
    public string ClassId { get => this["ClassId"]; set => this["ClassId"] = value; }
    public string EmergencyContactName { get => this["EmergencyContactName"]; set => this["EmergencyContactName"] = value; }
    public string RelationshipCode { get => this["RelationshipCode"]; set => this["RelationshipCode"] = value; }
    public string EmergencyPhoneNumber { get => this["EmergencyPhoneNumber"]; set => this["EmergencyPhoneNumber"] = value; }
    public string Remarks { get => this["Remarks"]; set => this["Remarks"] = value; }
    public string OperationReason { get => this["OperationReason"]; set => this["OperationReason"] = value; }
    public Dictionary<string, string> Snapshot() => new(values);
    public void Load(Dictionary<string, string> data) { values = new(data); ClearErrors(); Changed("Item[]"); foreach (var p in GetType().GetProperties().Where(x => x.PropertyType == typeof(string))) Changed(p.Name); }
}

// SCR-STU-002 EV-REG-001..007. Raw strings survive all validation failures.
public sealed class StudentEditViewModel : Bindable, IDisposable
{
    private readonly IStudentGateway gateway;
    private readonly DialogService dialogs;
    private readonly CancellationTokenSource lifetime = new();
    private readonly long? id;
    private long? version;
    private Dictionary<string, string> original = [];
    private string message = "";
    private bool busy;
    public bool IsBusy { get => busy; private set { Set(ref busy, value); Changed(nameof(CanEdit)); Changed(nameof(CanEditNumber)); Changed(nameof(CanDelete)); foreach (var command in new[] { SaveCommand, DeleteCommand, ResetCommand, ReloadCommand, BackCommand }) command?.RaiseCanExecuteChanged(); } }
    public EditModel Model { get; } = new();
    public LookupSet Lookup { get; private set; } = new(new Dictionary<string, IReadOnlyList<CodeOption>>(), []);
    public IReadOnlyList<CodeOption> Genders => Options("GENDER");
    public IReadOnlyList<CodeOption> Prefectures => Options("PREFECTURE");
    public IReadOnlyList<CodeOption> Statuses => Options("ENROLLMENT_STATUS");
    public IReadOnlyList<CodeOption> Relationships => new[] { new CodeOption("", "未選択") }.Concat(Options("RELATIONSHIP")).ToArray();
    public IReadOnlyList<CodeOption> Grades => new[] { new CodeOption("", "すべて") }.Concat(Options("GRADE")).ToArray();
    public IReadOnlyList<ClassOption> Classes => new[] { new ClassOption(0, 0, "", "未選択", true, 0, null) }.Concat(Lookup.Classes.Where(x => (string.IsNullOrEmpty(Model["SchoolYear"]) || x.Year.ToString() == Model["SchoolYear"]) && (string.IsNullOrEmpty(Model["GradeCode"]) || x.Grade == Model["GradeCode"]))).ToArray();
    public CodeOption[] Eras { get; } = [new("", "未選択"), new("REIWA", "令和"), new("HEISEI", "平成"), new("SHOWA", "昭和"), new("TAISHO", "大正"), new("MEIJI", "明治")];
    public bool CanEdit => gateway.CanEdit && !IsBusy;
    public bool CanDelete => gateway.CanDelete && id is not null && !IsBusy;
    public bool CanEditNumber => CanEdit && id is null;
    public bool IsDirty => JsonSerializer.Serialize(Model.Snapshot().OrderBy(x => x.Key)) != JsonSerializer.Serialize(original.OrderBy(x => x.Key));
    public string StudentIdDisplay => id?.ToString(System.Globalization.CultureInfo.InvariantCulture) ?? "自動採番";
    public string Title => id is null ? "学生登録：新規" : CanEdit ? "学生登録：編集" : "学生登録：参照";
    public string Message { get => message; private set => Set(ref message, value); }
    public string UpdatedInfo { get; private set; } = "";
    public string ResultNotice { get; private set; } = "";
    public Action? CloseRequested { get; set; }
    public AsyncCommand SaveCommand { get; }
    public AsyncCommand DeleteCommand { get; }
    public AsyncCommand ResetCommand { get; }
    public AsyncCommand ReloadCommand { get; }
    public AsyncCommand BackCommand { get; }
    public StudentEditViewModel(IStudentGateway gateway, DialogService dialogs, long? id)
    {
        this.gateway = gateway; this.dialogs = dialogs; this.id = id;
        void Error(Exception ex) { Message = ex is InvalidOperationException ? ex.Message : "E-COM-004 処理に失敗しました。入力を保持しています。"; }
        SaveCommand = new(_ => RunAsync(SaveAsync), () => CanEdit && !IsBusy, Error);
        DeleteCommand = new(_ => RunAsync(DeleteAsync), () => CanDelete && !IsBusy, Error);
        ResetCommand = new(_ => { if (dialogs.Discard("入力内容を取り消しますか。")) Model.Load(original); return Task.CompletedTask; }, () => !IsBusy, Error);
        ReloadCommand = new(async _ => { if (dialogs.Discard("最新情報を再読み込みしますか。入力中の変更は破棄されます。")) await RunAsync(LoadAsync); }, () => id is not null && !IsBusy, Error);
        BackCommand = new(_ => { CloseRequested?.Invoke(); return Task.CompletedTask; }, () => !IsBusy, Error);
        Model.PropertyChanged += (_, _) => { Changed(nameof(IsDirty)); Changed(nameof(Classes)); };
    }
    private IReadOnlyList<CodeOption> Options(string category) => Lookup.Codes.GetValueOrDefault(category) ?? [];
    private async Task RunAsync(Func<Task> operation) { if (IsBusy) return; IsBusy = true; try { await operation(); } finally { IsBusy = false; } }
    public async Task InitializeAsync()
    {
        try { Lookup = await gateway.LookupAsync(lifetime.Token); await LoadAsync(); foreach (var p in new[] { nameof(Genders), nameof(Prefectures), nameof(Statuses), nameof(Relationships), nameof(Grades), nameof(Classes) }) Changed(p); }
        catch (Exception ex) { Message = ex is InvalidOperationException ? ex.Message : "E-COM-004 学生を読み込めませんでした。"; }
    }
    private async Task LoadAsync()
    {
        if (id is not null)
        {
            var data = await gateway.GetAsync(id.Value, lifetime.Token);
            version = data.Version; original = new(data.Values); UpdatedInfo = data.UpdatedAt + " / " + data.UpdatedBy;
            var cls = Lookup.Classes.FirstOrDefault(x => x.Id.ToString() == original.GetValueOrDefault("ClassId"));
            if (cls is not null) { original["SchoolYear"] = cls.Year.ToString(); original["GradeCode"] = cls.Grade; }
        }
        else
        {
            var today = DateTimeOffset.UtcNow.ToOffset(TimeSpan.FromHours(9));
            original = new() { ["GenderCode"] = "0", ["EnrollmentStatusCode"] = "01", ["SchoolYear"] = (today.Month < 4 ? today.Year - 1 : today.Year).ToString() };
        }
        Model.Load(original); Message = Lookup.Classes.Count == 0 ? "W-STU-108 登録可能なクラスがありません。" : ""; Changed(nameof(UpdatedInfo));
    }
    public void SelectClass()
    {
        var cls = Lookup.Classes.FirstOrDefault(x => x.Id.ToString() == Model["ClassId"]);
        if (cls is not null) { Model["SchoolYear"] = cls.Year.ToString(); Model["GradeCode"] = cls.Grade; Message = $"所属人数 {cls.Occupancy} / 定員 {(cls.Capacity?.ToString() ?? "制限なし")}（参考値）"; }
        if (Model["ClassId"] == "0") Model["ClassId"] = "";
    }
    private async Task SaveAsync()
    {
        Model.ClearErrors();
        var snapshot = Model.Snapshot();
        var result = await gateway.SaveAsync(id, version, snapshot, null, Model["OperationReason"], lifetime.Token);
        if (result.State == "ConfirmationRequired")
        {
            var reason = dialogs.ConfirmDuplicate(result);
            if (reason is null) { Message = "確認を取り消しました。入力を保持しています。"; return; }
            Model["OperationReason"] = reason;
            result = await gateway.SaveAsync(id, version, Model.Snapshot(), result.Token, reason, lifetime.Token);
        }
        Message = result.Message;
        foreach (var error in result.Errors ?? new Dictionary<string, string[]>())
        {
            if (error.Key == "BirthDateInput") foreach (var p in new[] { "BirthEra", "BirthYear", "BirthMonth", "BirthDay" }) Model.SetError(p, error.Value);
            else Model.SetError(error.Key, error.Value);
        }
        if (result.State == "Saved") { original = Model.Snapshot(); ResultNotice = result.Message; IsBusy = false; CloseRequested?.Invoke(); }
    }
    private async Task DeleteAsync()
    {
        if (id is null || version is null) return;
        var reason = dialogs.DeleteReason(); if (reason is null) return;
        var result = await gateway.DeleteAsync(id.Value, version.Value, reason, lifetime.Token);
        Message = result.Message;
        if (result.State == "Saved") { original = Model.Snapshot(); ResultNotice = result.Message; IsBusy = false; CloseRequested?.Invoke(); }
    }
    public bool CanClose() => !IsBusy && (!IsDirty || dialogs.Discard("保存していない変更を破棄しますか。"));
    public void Dispose() { lifetime.Cancel(); lifetime.Dispose(); }
}
