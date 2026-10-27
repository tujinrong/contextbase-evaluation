using Microsoft.AspNetCore.Diagnostics;
using Microsoft.AspNetCore.Mvc;
using StudentManagement.Web.Models;

namespace StudentManagement.Web.Controllers;

public sealed class SystemController(ILogger<SystemController> logger) : Controller
{
    [Route("System/Error")]
    public IActionResult Error()
    {
        var failure = HttpContext.Features.Get<IExceptionHandlerPathFeature>();
        if (failure is not null) logger.LogError(failure.Error, "Request failed at {Path}", failure.Path);
        Response.StatusCode = 503;
        return View("~/Views/Shared/Failure.cshtml", new FailureViewModel("処理を続けられません", "接続設定と利用可能なDB環境を確認してください。入力内容や秘密情報はこの画面には表示しません。"));
    }
}
