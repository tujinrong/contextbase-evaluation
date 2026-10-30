using CareerManagement.Application;
using CareerManagement.Infrastructure.Authentication;
using CareerManagement.Infrastructure.State;
using CareerManagement.Infrastructure.Sql;
using CareerManagement.Web.Filters;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Mvc;

namespace CareerManagement.Web.Controllers;
[Route("ui")]
public sealed class UiController(ScreenStateStore states,SearchReturnCoordinator returns,CurrentUserService current,SessionRegistry sessions):Controller
{
    private Actor Actor=>(Actor)HttpContext.Items["Actor"]!;
    [HttpPost("attach")]
    public async Task<IActionResult> Attach(CancellationToken ct)
    {
        var i=await HttpJson.ReadAsync<AttachInput>(Request,ct);var s=states.Get<ScreenState>(i.StateId,Actor.SessionId);
        if(!await s.Gate.WaitAsync(0,ct))return Failure(Outcome.Of(29,"Busy"));
        try
        {
            states.Attach(s,i);
            if(s is EditState edit&&edit.Completed)return Failure(Outcome.Of(41,"UiExpired",CommitState.Committed) with{Message=Messages.Get(14)+" "+Messages.Get(41)});
            return Json(new{attached=true});
        }
        finally{s.Gate.Release();}
    }
    [HttpPost("navigate")]
    public async Task<IActionResult> Navigate(CancellationToken ct)=>await Move(await HttpJson.ReadAsync<NavigationInput>(Request,ct),ct);
    [HttpPost("/account/logout")]
    public async Task<IActionResult> Logout(CancellationToken ct)
    {
        var i=await HttpJson.ReadAsync<LogoutInput>(Request,ct);return await Move(new(UiDestination.Logout,i.RawUiEnvelope,i.ConfirmationId,i.Choice),ct);
    }
    private async Task<IActionResult> Move(NavigationInput i,CancellationToken ct)
    {
        var raw=i.RawUiEnvelope;var s=states.Get<ScreenState>(raw.StateId,Actor.SessionId);
        if(!await s.Gate.WaitAsync(0,ct))return Failure(Outcome.Of(29,"Busy"));
        try
        {
            states.CheckUi(s,raw.StateRevision,raw.TabId,raw.DocumentLease);ScreenStateStore.CaptureUi(s,raw);
            if(states.ConfirmLeave(s,raw,"Navigate",i.Destination.ToString(),i.ConfirmationId,i.Choice)!=true)
                return Json(new{ui=states.Info(s,Route(s)),discardConfirmation=ScreenStateStore.Question(s)});
            if(i.Destination==UiDestination.Logout)
            {
                sessions.Remove(Actor.SessionId);states.RemoveSession(Actor.SessionId);await HttpContext.SignOutAsync("SP2");
                return Navigation("/account/login");
            }
            if(i.Destination==UiDestination.Codes)await current.RequireAsync(Actor,true,ct);
            states.Touch(s);ScreenState target;string route;
            switch(i.Destination)
            {
                case UiDestination.Home:target=states.Add(new NavigationState(Actor.SessionId));route="/menu";break;
                case UiDestination.Employees:
                    var snapshot=s is EditState edit?edit.ReturnSnapshot:s is SearchState search?search.Capture():returns.Initial(Actor,s.TabId);
                    target=await returns.ReturnAsync(Actor,snapshot,null,null,ct);route="/employees";break;
                case UiDestination.Codes:target=states.Add(new CodeState(Actor.SessionId,"DEPARTMENT"));route="/codes";break;
                default:throw BusinessException.Error(25);
            }
            return Navigation(states.IssueTicket(s,target,route));
        }
        catch(Exception e){return Failure(SqlErrors.Map(e,40));}
        finally{s.Gate.Release();}
    }
    private static string Route(ScreenState s)=>s is SearchState?"/employees":s is CodeState?"/codes":s is EditState e?e.Snapshot is null?"/employees/new":$"/employees/{e.Snapshot.EmployeeId}/edit":"/menu";
    private JsonResult Navigation(string url)=>Json(new{navigation=new{url,commitState=CommitState.NotStarted,messageId=(string?)null}});
    private static JsonResult Failure(Outcome o)=>new(new{outcome=o},HttpJson.Options){StatusCode=HttpJson.Status(o)};
}
