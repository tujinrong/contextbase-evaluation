using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace StudentManagement.Web;

public sealed class AccountController(LocalLogin login) : Controller
{
    [AllowAnonymous, HttpGet("/login")]
    public IActionResult Login()
    {
        if (login.ReadSettings() is null) return NotFound();
        if (User.Identity?.IsAuthenticated == true) return Redirect("/students");
        return View(new LoginPageModel());
    }

    [AllowAnonymous, HttpPost("/login")]
    public async Task<IActionResult> Login([Bind("Username")] LoginPageModel input, [FromForm] string? password)
    {
        if (login.ReadSettings() is null) return NotFound();
        var form = await Request.ReadFormAsync();
        var duplicate = form["Username"].Count != 1 || form["password"].Count != 1;
        var principal = login.Authenticate(duplicate ? null : input.Username, duplicate ? null : password);
        if (principal is not null)
        {
            await HttpContext.SignInAsync(CookieAuthenticationDefaults.AuthenticationScheme, principal,
                new AuthenticationProperties { IsPersistent = false, AllowRefresh = true });
            return Redirect("/students");
        }
        ModelState.Clear();
        Response.StatusCode = StatusCodes.Status401Unauthorized;
        return View(new LoginPageModel { Username = input.Username is { Length: <= 64 } ? input.Username : "", Error = "ログインできません。利用者名・パスワードを確認し、試行を繰り返した場合は5分後に再試行してください。" });
    }

    [Authorize, HttpPost("/logout")]
    public async Task<IActionResult> Logout()
    {
        await HttpContext.SignOutAsync(CookieAuthenticationDefaults.AuthenticationScheme);
        return Redirect("/login");
    }
}
