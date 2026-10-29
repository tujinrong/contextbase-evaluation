using System.Security.Claims;
using CareerManagement.Application;
using CareerManagement.Infrastructure.Authentication;
using CareerManagement.Infrastructure.Sql;
using CareerManagement.Infrastructure.State;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Filters;

namespace CareerManagement.Web.Filters;
public sealed class CurrentActorFilter(CurrentUserService current,SessionRegistry sessions,ScreenStateStore states):IAsyncActionFilter
{
    public async Task OnActionExecutionAsync(ActionExecutingContext context,ActionExecutionDelegate next)
    {
        var path=context.HttpContext.Request.Path;
        if(path=="/account/login"||path=="/account/exit"||path=="/account/logout"){await next();return;}
        var user=context.HttpContext.User;
        var id=user.FindFirstValue(ClaimTypes.NameIdentifier);var session=user.FindFirstValue("session_id");
        try
        {
            if(id is null||session is null||user.Identity?.IsAuthenticated!=true)throw BusinessException.Error(2,"Expired");
            var actor=await current.RequireAsync(new(id,session,"",UserRole.STAFF),path.StartsWithSegments("/codes"),context.HttpContext.RequestAborted);
            context.HttpContext.Items["Actor"]=actor;
            var result=await next();
            if(result.Result is Microsoft.AspNetCore.Mvc.Infrastructure.IStatusCodeActionResult status&&status.StatusCode==401)
            {sessions.Remove(session);states.RemoveSession(session);await context.HttpContext.SignOutAsync("SP2");return;}
            var request=context.HttpContext.Request;
            var explicitOperation=(HttpMethods.IsGet(request.Method)&&request.Headers["Sec-Fetch-Mode"]=="navigate")||
                (HttpMethods.IsPost(request.Method)&&request.Headers["X-SP2-User-Action"]=="true");
            if(result.Exception is null&&explicitOperation&&!context.HttpContext.Response.HasStarted&&context.HttpContext.Response.StatusCode<400&&sessions.Touch(session,id))
                await CookieActor.SignInAsync(context.HttpContext,actor);
        }
        catch(Exception exception)
        {
            if(exception is System.Text.Json.JsonException or BadHttpRequestException)
            {context.Result=new JsonResult(new{outcome=Outcome.Of(25)},HttpJson.Options){StatusCode=400};return;}
            var outcome=SqlErrors.Map(exception,40);
            if(outcome.Kind=="Forbidden"&&session is not null&&path.StartsWithSegments("/codes"))states.RemoveSessionOfType<CodeState>(session);
            if(outcome.Kind=="Expired")
            {
                if(session is not null){sessions.Remove(session);states.RemoveSession(session);}await context.HttpContext.SignOutAsync("SP2");
                if(HttpMethods.IsGet(context.HttpContext.Request.Method)){context.Result=new RedirectResult("/account/login?expired=1");return;}
            }
            context.Result=new JsonResult(new{outcome},HttpJson.Options){StatusCode=HttpJson.Status(outcome)};
        }
    }
}
public static class CookieActor
{
    public static Task SignInAsync(HttpContext context,Actor actor)
    {
        var identity=new ClaimsIdentity([new(ClaimTypes.NameIdentifier,actor.UserId),new("session_id",actor.SessionId),new(ClaimTypes.Role,actor.Role.ToString())],"SP2");
        return context.SignInAsync("SP2",new ClaimsPrincipal(identity),new AuthenticationProperties{IsPersistent=false,AllowRefresh=false,IssuedUtc=DateTimeOffset.UtcNow,ExpiresUtc=DateTimeOffset.UtcNow.AddMinutes(30)});
    }
}
