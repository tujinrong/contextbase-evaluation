using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Filters;
namespace StudentManagement.Web;
// JSON failure contracts also apply when MVC's antiforgery filter rejects the request.
public sealed class AntiforgeryResultFilter : IAsyncAlwaysRunResultFilter
{
    public Task OnResultExecutionAsync(ResultExecutingContext context,ResultExecutionDelegate next) {
        if(context.Result is AntiforgeryValidationFailedResult&&context.HttpContext.Request.Path.StartsWithSegments("/api"))context.Result=new JsonResult(WebPresentation.Error("badRequest","CSRF情報を確認できません。画面を開き直してください。")){StatusCode=400};return next();
    }
}
