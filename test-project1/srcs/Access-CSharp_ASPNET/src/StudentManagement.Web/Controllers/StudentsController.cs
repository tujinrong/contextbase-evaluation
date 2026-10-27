using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Rendering;
using StudentManagement.Core;
using StudentManagement.Web.Infrastructure;
using StudentManagement.Web.Models;
using System.Text.Json;

namespace StudentManagement.Web.Controllers;

public sealed class StudentsController(StudentService service, ConfirmationStore confirmations, EditorSnapshotStore snapshots) : Controller
{
    private sealed record PendingSave(StudentInput Input, string FormId, string CoreToken, IReadOnlyList<DuplicateCandidate> Candidates);
    private sealed record PendingDelete(StudentInput Input);
    private Actor Actor => (Actor)HttpContext.Items["Actor"]!;

    [HttpGet]
    public IActionResult Index([FromQuery] SearchInput input)
    {
        input.ContextId = Guid.TryParseExact(input.ContextId, "N", out var contextGuid) ? contextGuid.ToString("N") : Guid.NewGuid().ToString("N");
        var saved = HttpContext.Session.GetString("search:" + input.ContextId);
        if (!input.Searched && saved is not null) input = JsonSerializer.Deserialize<SearchInput>(saved)!;
        if (Request.Query.ContainsKey(nameof(SearchInput.Searched)) && input.Searched && !Request.Query.ContainsKey(nameof(SearchInput.Statuses))) input.Statuses = [];
        var model = new SearchViewModel { Input = input, CanWrite = Actor.Role != Role.Reader, Searched = input.Searched,
            RestoreScroll = input.Searched && !Request.Query.ContainsKey(nameof(SearchInput.Searched)) };
        model.Classes = ClassChoices(service.GetClasses(Actor), input.ClassId);
        if (!input.Searched) return View(model);
        try
        {
            var result = service.Search(new SearchCriteria
            {
                StudentNo = input.StudentNo, Name = input.Name, ClassId = StudentInput.ParseOptionalId(input.ClassId),
                Status01 = input.Statuses.Contains("01"), Status02 = input.Statuses.Contains("02"),
                Status03 = input.Statuses.Contains("03"), Status04 = input.Statuses.Contains("04")
            }, Actor, input.SortKey, input.SortDirection);
            model.Rows = result.Rows.Select(ToListItem).ToArray();
            model.SearchedAt = "検索日時 " + result.At.AddHours(9).ToString("yyyy/MM/dd HH:mm:ss") + " JST";
            if (result.Kind == "LimitExceeded") model.Warning = SourceMessages.Describe(result.Message);
            HttpContext.Session.SetString("search:" + input.ContextId, JsonSerializer.Serialize(input));
        }
        catch (BusinessException ex) { AddError(ex); }
        return View(model);
    }

    [HttpGet]
    public IActionResult New(string? contextId)
    {
        if (Actor.Role == Role.Reader) return StatusCode(403);
        var day = DateTime.ParseExact(service.BusinessDay, "yyyy-MM-dd", System.Globalization.CultureInfo.InvariantCulture);
        return View("Edit", Editor(new StudentInput { SchoolYear = (day.Month < 4 ? day.Year - 1 : day.Year).ToString(), SearchContextId = contextId }, true));
    }

    [HttpGet]
    public IActionResult Edit(int id, string? contextId)
    {
        var student = service.Get(id, Actor);
        var input = LoadedInput(student, contextId);
        var model = Editor(input, true);
        model.Updated = $"更新日時 {student.UpdatedAt.AddHours(9):yyyy/MM/dd HH:mm:ss} JST　{student.UpdatedBy}　版 {student.RowVersion}";
        return View("Edit", model);
    }

    [HttpPost]
    public IActionResult Candidates([Bind(Prefix = "Input")] StudentInput input)
    {
        if (Actor.Role == Role.Reader) return StatusCode(403);
        ValidateEditorIdentity(input);
        if (input.EnrollmentStatusCode is "01" or "02")
        {
            input.EnrollmentEndDate = null;
            ModelState.Remove("Input.EnrollmentEndDate");
        }
        return View("Edit", Editor(input));
    }

    [HttpPost]
    public IActionResult Save([Bind(Prefix = "Input")] StudentInput input)
    {
        if (Actor.Role == Role.Reader) return StatusCode(403);
        ValidateEditorIdentity(input);
        if (!ModelState.IsValid) return View("Edit", Editor(input));
        try
        {
            var formId = Guid.NewGuid().ToString("N");
            var result = service.Save(input.ToDraft(), input.Id, input.ExpectedVersion, Actor, formId);
            return SaveOutcome(input, formId, result);
        }
        catch (BusinessException ex) { AddError(ex); return View("Edit", Editor(input)); }
    }

    [HttpPost]
    public IActionResult ConfirmSave(string token, string? reason)
    {
        if (Actor.Role == Role.Reader) return StatusCode(403);
        var pending = confirmations.Consume<PendingSave>(token, SessionId(), Actor.UserId);
        if (pending is null) return ExpiredConfirmation();
        if (!IsEditorIdentityValid(pending.Input)) return ExpiredEditor();
        pending.Input.OperationReason = reason;
        try
        {
            var result = service.Save(pending.Input.ToDraft(), pending.Input.Id, pending.Input.ExpectedVersion,
                Actor, pending.FormId, pending.CoreToken, true);
            return SaveOutcome(pending.Input, pending.FormId, result);
        }
        catch (BusinessException ex) { AddError(ex); return View("Edit", Editor(pending.Input)); }
    }

    [HttpGet]
    public IActionResult Delete(int id, string? contextId, string? snapshotToken)
    {
        if (Actor.Role != Role.Admin) return StatusCode(403);
        var input = snapshots.Get(snapshotToken, SessionId(), Actor.UserId);
        if (snapshotToken is not null && (input is null || input.Id != id)) return ExpiredEditor();
        if (input is null)
        {
            input = LoadedInput(service.Get(id, Actor), contextId);
            input.SnapshotToken = snapshots.Capture(input, SessionId(), Actor.UserId);
        }
        var token = confirmations.Create(SessionId(), Actor.UserId, new PendingDelete(input));
        return View("Confirm", new ConfirmViewModel { Token = token, Kind = "DELETE", Input = input });
    }

    [HttpPost]
    public IActionResult ConfirmDelete(string token, string? reason)
    {
        if (Actor.Role != Role.Admin) return StatusCode(403);
        var pending = confirmations.Consume<PendingDelete>(token, SessionId(), Actor.UserId);
        if (pending is null) return ExpiredConfirmation();
        if (!IsEditorIdentityValid(pending.Input)) return ExpiredEditor();
        try
        {
            var result = service.Delete(pending.Input.Id!.Value, pending.Input.ExpectedVersion!.Value, reason, true, Actor);
            snapshots.Remove(pending.Input.SnapshotToken, SessionId(), Actor.UserId);
            TempData["Message"] = SourceMessages.Describe(result.Message);
            return RedirectToAction(nameof(Index), new { contextId = pending.Input.SearchContextId });
        }
        catch (BusinessException ex) { AddError(ex); return View("Edit", Editor(pending.Input)); }
    }

    [HttpPost]
    public IActionResult CancelConfirmation(string token)
    {
        var save = confirmations.Consume<PendingSave>(token, SessionId(), Actor.UserId);
        if (save is not null) return View("Edit", Editor(save.Input));
        var deletion = confirmations.Consume<PendingDelete>(token, SessionId(), Actor.UserId);
        if (deletion is not null) return View("Edit", Editor(deletion.Input));
        return ExpiredConfirmation();
    }

    private IActionResult SaveOutcome(StudentInput input, string formId, SaveResult result)
    {
        if (result.Kind == "ConfirmationRequired")
        {
            var candidates = result.Candidates ?? [];
            var token = confirmations.Create(SessionId(), Actor.UserId, new PendingSave(input, formId, result.ConfirmationToken!, candidates));
            return View("Confirm", new ConfirmViewModel
            {
                Kind = "DUPLICATE", Token = token, Input = input, Reason = input.OperationReason,
                Candidates = candidates.Select(c => new StudentListItem(c.StudentId, c.StudentNo, c.StudentName, "", JapaneseDate.FormatBirthDate(c.BirthDate), "", c.ClassDisplay, "", 0)).ToArray()
            });
        }
        TempData["Message"] = SourceMessages.Describe(result.Message, studentNo: input.StudentNo) + (result.Warning is null ? "" : " " + SourceMessages.Describe(result.Warning));
        snapshots.Remove(input.SnapshotToken, SessionId(), Actor.UserId);
        return RedirectToAction(nameof(Index), new { contextId = input.SearchContextId });
    }

    private EditorViewModel Editor(StudentInput input, bool captureOriginal = false)
    {
        if (captureOriginal) input.SnapshotToken = snapshots.Capture(input, SessionId(), Actor.UserId);
        var original = snapshots.Get(input.SnapshotToken, SessionId(), Actor.UserId) ?? throw new BusinessException("E-COM-003", "編集状態の期限が切れました。");
        var allClasses = service.GetClasses(Actor);
        var originalClassId = StudentInput.ParseOptionalId(original.ClassId);
        var day = service.BusinessDay;
        var choices = allClasses.Where(c => c.ClassId == originalClassId ||
            (c.IsActive && string.CompareOrdinal(c.ValidFrom, day) <= 0 && string.CompareOrdinal(c.ValidTo, day) >= 0 &&
             (string.IsNullOrWhiteSpace(input.SchoolYear) || c.SchoolYear.ToString() == input.SchoolYear) &&
             (string.IsNullOrWhiteSpace(input.GradeCode) || c.GradeCode == input.GradeCode))).ToArray();
        var selectedClass = allClasses.FirstOrDefault(c => c.ClassId.ToString() == input.ClassId);
        return new()
        {
            Input = input, ReadOnly = Actor.Role == Role.Reader, CanDelete = Actor.Role == Role.Admin && input.Id.HasValue,
            BaselineJson = JsonSerializer.Serialize(EditorSnapshotStore.RawValues(original)),
            Classes = ClassChoices(choices, input.ClassId),
            GenderCodes = Codes("GENDER", input.GenderCode), PrefectureCodes = Codes("PREFECTURE", input.PrefectureCode),
            StatusCodes = Codes("ENROLLMENT_STATUS", input.EnrollmentStatusCode), RelationshipCodes = Codes("RELATIONSHIP", input.RelationshipCode),
            GradeCodes = Codes("GRADE", input.GradeCode),
            SchoolYears = allClasses.Select(c => c.SchoolYear).Distinct().OrderDescending().Select(y => new SelectListItem(y.ToString(), y.ToString(), y.ToString() == input.SchoolYear)).ToArray(),
            Capacity = selectedClass is null ? "未選択" : $"{service.GetOccupancy(selectedClass.ClassId, Actor)} 人 ／ {selectedClass.Capacity?.ToString() ?? "上限なし"}"
        };
    }

    private IReadOnlyList<SelectListItem> Codes(string category, string? current) => service.GetCodes(category, Actor, current)
        .Select(c => new SelectListItem(c.CodeName + (c.IsActive ? "" : " [停止]"), c.CodeValue, c.CodeValue == current)).ToArray();

    private static IReadOnlyList<SelectListItem> ClassChoices(IEnumerable<ClassItem> classes, string? selected) => classes
        .Select(c => new SelectListItem($"{c.SchoolYear} {c.ClassCode} {c.ClassName}" + (c.IsActive ? "" : " [停止]"), c.ClassId.ToString(), c.ClassId.ToString() == selected)).ToArray();

    private static StudentListItem ToListItem(SearchRow row) => new(row.Student.StudentId, row.Student.StudentNo,
        row.Student.StudentName, row.Student.StudentNameKana, JapaneseDate.FormatBirthDate(row.Student.BirthDate),
        $"{row.SchoolYear?.ToString() ?? "－"}／{row.GradeName}", row.ClassDisplay, row.EnrollmentName, row.Student.RowVersion);

    private string SessionId()
    {
        HttpContext.Session.SetString("confirmation-session", "active");
        return HttpContext.Session.Id;
    }

    [HttpPost]
    public IActionResult Reset([Bind(Prefix = "Input")] StudentInput input)
    {
        if (Actor.Role == Role.Reader) return StatusCode(403);
        var original = snapshots.Get(input.SnapshotToken, SessionId(), Actor.UserId);
        if (original is null) return ExpiredEditor();
        InvalidateEditor(input.SnapshotToken);
        ModelState.Clear();
        return View("Edit", Editor(original, true));
    }

    [HttpPost]
    public IActionResult Reload([Bind(Prefix = "Input")] StudentInput input)
    {
        if (Actor.Role == Role.Reader) return StatusCode(403);
        var original = snapshots.Get(input.SnapshotToken, SessionId(), Actor.UserId);
        if (original is null) return ExpiredEditor();
        InvalidateEditor(input.SnapshotToken);
        ModelState.Clear();
        if (!original.Id.HasValue) return New(original.SearchContextId);
        return Edit(original.Id.Value, original.SearchContextId);
    }

    private StudentInput LoadedInput(Student student, string? contextId)
    {
        var input = StudentInput.FromStudent(student);
        input.SearchContextId = contextId;
        var classroom = service.GetClasses(Actor).FirstOrDefault(c => c.ClassId == student.ClassId);
        input.SchoolYear = classroom?.SchoolYear.ToString();
        input.GradeCode = classroom?.GradeCode;
        return input;
    }

    private void ValidateEditorIdentity(StudentInput input)
    {
        if (!IsEditorIdentityValid(input))
            throw new BusinessException("E-COM-003", "編集状態が無効です。画面を開き直してください。");
    }

    private bool IsEditorIdentityValid(StudentInput input)
    {
        var original = snapshots.Get(input.SnapshotToken, SessionId(), Actor.UserId);
        return original is not null && input.Id == original.Id && input.ExpectedVersion == original.ExpectedVersion;
    }

    private void InvalidateEditor(string? snapshotToken)
    {
        confirmations.CancelWhere<PendingSave>(SessionId(), Actor.UserId, pending => pending.Input.SnapshotToken == snapshotToken);
        confirmations.CancelWhere<PendingDelete>(SessionId(), Actor.UserId, pending => pending.Input.SnapshotToken == snapshotToken);
        snapshots.Remove(snapshotToken, SessionId(), Actor.UserId);
    }

    private IActionResult ExpiredEditor() => StatusCode(409, "編集状態の有効期限が切れました。画面を開き直してください。保存前の内容は自動更新していません。");

    [HttpGet]
    public IActionResult Clear(string contextId)
    {
        if (Guid.TryParseExact(contextId, "N", out _)) HttpContext.Session.Remove("search:" + contextId);
        return RedirectToAction(nameof(Index), new { contextId });
    }

    private void AddError(BusinessException ex) => ModelState.AddModelError("", SourceMessages.Describe(ex.Code, ex.Field));
    private IActionResult ExpiredConfirmation() => StatusCode(409, "確認の有効期限が切れたか、既に処理済みです。入力画面からやり直してください。");
}
