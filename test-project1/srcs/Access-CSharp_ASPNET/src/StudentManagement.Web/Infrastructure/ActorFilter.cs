using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Filters;
using StudentManagement.Core;
using StudentManagement.Web.Models;

namespace StudentManagement.Web.Infrastructure;

/// <summary>
/// Source evidence: modSecurity.CurrentUserId/CurrentRole/Authorize. A Web
/// request uses the host-authenticated subject, never the server process user.
/// Explicit synthetic identities are confined to the Verification environment.
/// </summary>
public sealed class ActorFilter(StudentService service, IWebHostEnvironment environment, IConfiguration configuration) : IActionFilter
{
    public void OnActionExecuting(ActionExecutingContext context)
    {
        if (context.RouteData.Values["controller"]?.ToString() == "System") return;
        var http = context.HttpContext;
        var verification = environment.IsEnvironment("Verification");
        var memory = string.Equals(configuration["Storage:Provider"], "VerificationMemory", StringComparison.Ordinal);
        var configuredUser = verification ? configuration["Verification:User"] : null;
        var userName = !string.IsNullOrWhiteSpace(configuredUser) ? configuredUser :
            http.User.Identity?.IsAuthenticated is true ? http.User.Identity.Name : null;
        if (string.IsNullOrWhiteSpace(userName))
        {
            Deny(context, 401, "認証が必要です", "Windows認証を有効にしたホストから接続してください。検証環境では検証用の主体を明示してください。");
            return;
        }
        try
        {
            Actor actor;
            if (verification && memory && !string.IsNullOrWhiteSpace(configuredUser))
            {
                if (!Enum.TryParse<Role>(configuration["Verification:Role"], false, out var role))
                {
                    Deny(context, 403, "検証用権限が未設定です", "Verification:RoleにReader、Staff、Adminのいずれかを明示してください。");
                    return;
                }
                actor = new(userName, role);
            }
            else actor = service.ResolveActor(userName);
            http.Items["Actor"] = actor;
            http.Items["ActorDisplay"] = actor.UserId + " ／ " + actor.Role;
            http.Items["VerificationMode"] = verification;
            http.Items["VerificationStorage"] = memory ? "メモリデータ（変更は永続化されません）" : "専用SQL Server検証DB";
        }
        catch (BusinessException ex) { Deny(context, 403, "操作権限がありません", SourceMessages.Describe(ex.Code, ex.Field)); }
    }

    public void OnActionExecuted(ActionExecutedContext context)
    {
        if (context.Exception is CommitOutcomeUnknownException)
        {
            context.Result = new ViewResult
            {
                ViewName = "~/Views/Shared/Failure.cshtml",
                ViewData = new Microsoft.AspNetCore.Mvc.ViewFeatures.ViewDataDictionary<FailureViewModel>(
                    new Microsoft.AspNetCore.Mvc.ModelBinding.EmptyModelMetadataProvider(), context.ModelState)
                { Model = new("保存結果を確認してください", "保存結果を確認できません。再送信せず、検索または最新再読込で保存結果を確認してください。確認できない場合は管理者に連絡してください。 (E-COM-004)") },
                StatusCode = 409
            };
            context.ExceptionHandled = true;
            return;
        }
        if (context.Exception is not BusinessException ex) return;
        var denied = ex.Code.Contains("AUTH", StringComparison.Ordinal) || ex.Code == "E-COM-002";
        context.Result = new ViewResult
        {
            ViewName = "~/Views/Shared/Failure.cshtml",
            ViewData = new Microsoft.AspNetCore.Mvc.ViewFeatures.ViewDataDictionary<FailureViewModel>(
                new Microsoft.AspNetCore.Mvc.ModelBinding.EmptyModelMetadataProvider(), context.ModelState)
            { Model = new(denied ? "操作権限がありません" : "処理できませんでした", SourceMessages.Describe(ex.Code, ex.Field)) },
            StatusCode = denied ? 403 : 409
        };
        context.ExceptionHandled = true;
    }

    private static void Deny(ActionExecutingContext context, int status, string title, string message)
    {
        context.Result = new ViewResult
        {
            ViewName = "~/Views/Shared/Failure.cshtml",
            ViewData = new Microsoft.AspNetCore.Mvc.ViewFeatures.ViewDataDictionary<FailureViewModel>(
                new Microsoft.AspNetCore.Mvc.ModelBinding.EmptyModelMetadataProvider(), context.ModelState) { Model = new(title, message) },
            StatusCode = status
        };
    }
}
