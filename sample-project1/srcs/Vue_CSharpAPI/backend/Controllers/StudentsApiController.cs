using Microsoft.AspNetCore.Antiforgery;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using StudentManagement.Core;
using StudentManagement.Web;
namespace StudentManagement.Api;
[Authorize,Route("api/students")]
public sealed class StudentsApiController(WebStudentCoordinator coordinator,IStudentService service,RequestIdentity identity,IAntiforgery antiforgery) : Controller
{
    [HttpGet("bootstrap")]
    public async Task<IActionResult> Bootstrap(CancellationToken ct) { identity.Read();var entry=coordinator.NewContext(identity.TabId);var token=antiforgery.GetAndStoreTokens(HttpContext).RequestToken;var lookup=await service.LookupAsync(false,ct);return Json(Merge(WebPresentation.Lookups(lookup),new { csrfToken=token,user=identity.CurrentUser.Principal,permissions=identity.Permissions,businessDate=WebPresentation.BusinessDate.ToString("yyyy-MM-dd"),schoolYear=WebPresentation.SchoolYear,formatVersion=entry.FormatVersion,contextId=entry.Id,contextRevision=entry.Revision.ToString(System.Globalization.CultureInfo.InvariantCulture) })); }
    [HttpPost("search")] public async Task<IActionResult> Search(CancellationToken ct)=>Json(await coordinator.Search(await StrictJson.Read<SearchRequest>(Request,ct),identity.TabId,ct));
    [HttpPost("page")] public async Task<IActionResult> Page(CancellationToken ct)=>Json(await coordinator.Page(await StrictJson.Read<PageRequest>(Request,ct),identity.TabId,ct));
    [HttpPost("context/clear")] public async Task<IActionResult> Clear(CancellationToken ct)=>Json(await coordinator.Clear(await StrictJson.Read<ContextRequest>(Request,ct),identity.TabId,ct));
    [HttpPost("resume")] public async Task<IActionResult> Resume(CancellationToken ct)=>Json(await coordinator.Resume(await StrictJson.Read<ContextRequest>(Request,ct),identity.TabId,ct));
    [HttpPost("options")] public async Task<IActionResult> Options(CancellationToken ct)=>Json(await coordinator.Options(await StrictJson.Read<OptionsRequest>(Request,ct),ct));
    [HttpGet("new")] public Task<IActionResult> New(string? returnContextId,CancellationToken ct)=>Load(null,returnContextId,ct);
    [HttpGet("{id:long}")] public Task<IActionResult> Get(long id,string? returnContextId,CancellationToken ct)=>Load(id,returnContextId,ct);
    private async Task<IActionResult> Load(long? id,string? contextId,CancellationToken ct) { var e=await coordinator.Edit(id,contextId,ct);return Json(Merge(WebPresentation.Lookups(e.Lookups,"register",e.Detail,null,null,e.Form.EnrollmentStatusCode,e.Form.AdmissionDate,e.Form.EnrollmentEndDate),new { studentId=id?.ToString(System.Globalization.CultureInfo.InvariantCulture),form=e.Form,updatedAt=e.Detail is null?null:WebPresentation.Time(e.Detail.UpdatedAt),updatedBy=e.Detail?.UpdatedBy,permissions=identity.Permissions })); }
    [HttpPost] public Task<IActionResult> Create(CancellationToken ct)=>Save(null,ct);
    [HttpPut("{id:long}")] public Task<IActionResult> Update(long id,CancellationToken ct)=>Save(id,ct);
    private async Task<IActionResult> Save(long? id,CancellationToken ct) { var result=await coordinator.Save(id,await StrictJson.Read<StudentSaveInput>(Request,ct),ct);return new JsonResult(WebPresentation.Save(result)){StatusCode=result.Outcome==Outcome.Saved&&id is null?201:WebPresentation.Status(result.Outcome)}; }
    [HttpPost("{id:long}/soft-delete")] public async Task<IActionResult> Delete(long id,CancellationToken ct) { var result=await coordinator.Delete(id,await StrictJson.Read<StudentDeleteInput>(Request,ct),ct);return new JsonResult(WebPresentation.Save(result)){StatusCode=WebPresentation.Status(result.Outcome)}; }
    private static object Merge(object a,object b) { var options=new System.Text.Json.JsonSerializerOptions(System.Text.Json.JsonSerializerDefaults.Web); var first=System.Text.Json.JsonSerializer.SerializeToElement(a,options).EnumerateObject().ToDictionary(p=>p.Name,p=>p.Value.Clone());foreach(var p in System.Text.Json.JsonSerializer.SerializeToElement(b,options).EnumerateObject())first[p.Name]=p.Value.Clone();return first; }
}
