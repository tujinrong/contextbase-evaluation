using Microsoft.AspNetCore.Mvc.Rendering;
using StudentManagement.Core;

namespace StudentManagement.Web.Models;

public sealed record MasterIndexViewModel(IReadOnlyList<ClassItem> Classes, IReadOnlyList<CodeItem> Codes,
    IReadOnlyList<CodeCategory> Categories);

public sealed class ClassEditorViewModel
{
    public int? Id { get; set; }
    public int? ExpectedVersion { get; set; }
    public ClassDraft Input { get; set; } = new();
    public IReadOnlyList<SelectListItem> GradeCodes { get; set; } = [];
}

public sealed class CodeEditorViewModel
{
    public string CategoryId { get; set; } = "";
    public string CodeValue { get; set; } = "";
    public int? ExpectedVersion { get; set; }
    public bool IsProtected { get; set; }
    public CodeDraft Input { get; set; } = new();
    public IReadOnlyList<SelectListItem> Categories { get; set; } = [];
}
