using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Rendering;
using StudentManagement.Core;
using StudentManagement.Web.Infrastructure;
using StudentManagement.Web.Models;

namespace StudentManagement.Web.Controllers;

// Web adapters for the binary-exported modMasterMaintenance administrative
// entry points. Source student forms do not expose these operations.
public sealed class MastersController(StudentService service) : Controller
{
    private Actor Actor => (Actor)HttpContext.Items["Actor"]!;

    [HttpGet]
    public IActionResult Index()
    {
        if (Actor.Role != Role.Admin) return StatusCode(403);
        return View(new MasterIndexViewModel(service.GetClasses(Actor), service.GetAllCodes(Actor), service.GetCategories(Actor)));
    }

    [HttpGet]
    public IActionResult Class(int? id)
    {
        if (Actor.Role != Role.Admin) return StatusCode(403);
        var model = new ClassEditorViewModel();
        if (id.HasValue)
        {
            var item = service.GetClasses(Actor).FirstOrDefault(c => c.ClassId == id) ?? throw new BusinessException("E-STU-010", "指定したクラスが存在しません。");
            model.Id = id; model.ExpectedVersion = item.RowVersion;
            model.Input = new ClassDraft { SchoolYear = item.SchoolYear.ToString(), GradeCode = item.GradeCode, ClassCode = item.ClassCode,
                ClassName = item.ClassName, ValidFrom = item.ValidFrom, ValidTo = item.ValidTo, Capacity = item.Capacity?.ToString(),
                DisplayOrder = item.DisplayOrder.ToString(), IsActive = item.IsActive, Remarks = item.Remarks };
        }
        else
        {
            var day = DateTime.ParseExact(service.BusinessDay, "yyyy-MM-dd", System.Globalization.CultureInfo.InvariantCulture);
            var year = day.Month < 4 ? day.Year - 1 : day.Year;
            model.Input.SchoolYear = year.ToString(); model.Input.ValidFrom = $"{year}-04-01"; model.Input.ValidTo = $"{year + 1}-03-31";
        }
        Fill(model); return View(model);
    }

    [HttpPost]
    public IActionResult Class(ClassEditorViewModel model)
    {
        if (Actor.Role != Role.Admin) return StatusCode(403);
        if (ModelState.IsValid)
        {
            try
            {
                var result = service.MaintainClass(model.Input, model.Id, model.ExpectedVersion, Actor);
                TempData["Message"] = "クラスマスタを保存しました。" + (result.Warning is null ? "" : SourceMessages.Describe(result.Warning));
                return RedirectToAction(nameof(Index));
            }
            catch (BusinessException ex) { ModelState.AddModelError("", SourceMessages.Describe(ex.Code, ex.Field)); }
        }
        Fill(model); return View(model);
    }

    [HttpGet]
    public IActionResult Code(string? categoryId, string? codeValue)
    {
        if (Actor.Role != Role.Admin) return StatusCode(403);
        var model = new CodeEditorViewModel { CategoryId = categoryId ?? "", CodeValue = codeValue ?? "" };
        if (!string.IsNullOrEmpty(codeValue))
        {
            var item = service.GetAllCodes(Actor).FirstOrDefault(c => c.CategoryId == categoryId && c.CodeValue == codeValue) ?? throw new BusinessException("E-MST-001", "指定したコードが存在しません。");
            model.ExpectedVersion = item.RowVersion; model.IsProtected = item.IsProtected;
            model.Input = new CodeDraft { CodeName = item.CodeName, DisplayOrder = item.DisplayOrder.ToString(), IsActive = item.IsActive,
                ValidFrom = item.ValidFrom, ValidTo = item.ValidTo, Remarks = item.Remarks };
        }
        Fill(model); return View(model);
    }

    [HttpPost]
    public IActionResult Code(CodeEditorViewModel model)
    {
        if (Actor.Role != Role.Admin) return StatusCode(403);
        if (ModelState.IsValid)
        {
            try
            {
                var result = service.MaintainCode(model.CategoryId, model.CodeValue, model.Input, model.ExpectedVersion, Actor);
                TempData["Message"] = result.Kind == "NoChange" ? SourceMessages.Describe("I-STU-004") : "コードマスタを保存しました。";
                return RedirectToAction(nameof(Index));
            }
            catch (BusinessException ex) { ModelState.AddModelError("", SourceMessages.Describe(ex.Code, ex.Field)); }
        }
        Fill(model); return View(model);
    }

    private void Fill(ClassEditorViewModel model) => model.GradeCodes = service.GetCodes("GRADE", Actor, model.Input.GradeCode)
        .Select(c => new SelectListItem(c.CodeName + (c.IsActive ? "" : " [停止]"), c.CodeValue)).ToArray();

    private void Fill(CodeEditorViewModel model) => model.Categories = service.GetCategories(Actor)
        .Where(c => model.ExpectedVersion.HasValue || c.AllowAdd)
        .Select(c => new SelectListItem(c.CategoryName + " (" + c.CategoryId + ")", c.CategoryId)).ToArray();
}
