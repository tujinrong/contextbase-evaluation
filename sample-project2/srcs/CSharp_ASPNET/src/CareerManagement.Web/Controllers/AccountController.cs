using CareerManagement.Application;
using CareerManagement.Infrastructure.Authentication;
using CareerManagement.Infrastructure.State;
using CareerManagement.Web.Filters;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Mvc;

namespace CareerManagement.Web.Controllers;
[Route("account")]
public sealed class AccountController(AuthService auth,SessionRegistry sessions,ScreenStateStore states):Controller
{
    [HttpGet("login")]
    public IActionResult Login()=>View(new LoginVm("",Request.Query.ContainsKey("expired")?Messages.Get(2):null,[]));
    [HttpPost("login")]
    public async Task<IActionResult> Login(CancellationToken ct)
    {
        var form=await Request.ReadFormAsync(ct);
        if(form.Keys.Any(k=>k is not("LoginId" or "Password" or "__RequestVerificationToken"))||form.Any(x=>x.Value.Count!=1)||!form.ContainsKey("LoginId")||!form.ContainsKey("Password"))return BadRequest();
        var input=new LoginInput(form["LoginId"].ToString(),form["Password"].ToString());
        try
        {
            var actor=await auth.AuthenticateAsync(input,ct);
            if(actor is null)return View(new LoginVm(input.LoginId,Messages.Get(1),[]));
            await ClearAsync();await CookieActor.SignInAsync(HttpContext,actor);Response.StatusCode=303;Response.Headers.Location="/menu";return new EmptyResult();
        }
        catch(BusinessException b){return View(new LoginVm(input.LoginId,b.Outcome.Message,b.Outcome.FieldErrors));}
    }
    [HttpPost("exit")]
    public async Task<IActionResult> Exit(){await ClearAsync();return View("Exited");}
    private async Task ClearAsync()
    {
        var session=User.FindFirst("session_id")?.Value;if(session is not null){sessions.Remove(session);states.RemoveSession(session);}
        await HttpContext.SignOutAsync("SP2");
    }
}
[Route("menu")]
public sealed class MenuController(ScreenStateStore states):Controller
{
    [HttpGet]
    public IActionResult Index(string? nav)
    {
        var actor=(Actor)HttpContext.Items["Actor"]!;
        var state=nav is null?states.Add(new NavigationState(actor.SessionId)):states.Consume<NavigationState>(nav,actor.SessionId,"/menu");
        return View(new MenuVm(actor.DisplayName,actor.Role,Request.Query.ContainsKey("denied")?Outcome.Of(3,"Forbidden"):null,states.Info(state,"/menu")));
    }
}
