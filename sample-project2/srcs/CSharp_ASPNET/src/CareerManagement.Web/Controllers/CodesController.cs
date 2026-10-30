using CareerManagement.Application;
using CareerManagement.Infrastructure.Authentication;
using CareerManagement.Infrastructure.Sql;
using CareerManagement.Infrastructure.State;
using CareerManagement.Web.Filters;
using Microsoft.AspNetCore.Mvc;

namespace CareerManagement.Web.Controllers;
[Route("codes")]
public sealed class CodesController(ScreenStateStore states,CodeService service,CurrentUserService current):Controller
{
    private Actor Actor=>(Actor)HttpContext.Items["Actor"]!;
    [HttpGet]
    public async Task<IActionResult> Index(string? nav,CancellationToken ct)
    {
        await current.RequireAsync(Actor,true,ct);
        var state=nav is null?states.Add(new CodeState(Actor.SessionId,"DEPARTMENT")):states.Consume<CodeState>(nav,Actor.SessionId,"/codes");
        return View(await VmAsync(state,ct));
    }
    [HttpPost("open")]
    public async Task<IActionResult> Open(CancellationToken ct)
    {
        var i=await HttpJson.ReadAsync<CodeOpenInput>(Request,ct);Validation.Category(i.Category);
        var s=i.StateId is null?states.Add(new CodeState(Actor.SessionId,i.Category)):states.Get<CodeState>(i.StateId,Actor.SessionId);
        if(!await s.Gate.WaitAsync(0,ct))return Failure(Outcome.Of(29,"Busy"));
        var accepted=false;
        try
        {
            if(i.StateId is not null)
            {
                states.CheckUi(s,i.StateRevision??throw BusinessException.Error(8,"Conflict"),i.TabId,i.DocumentLease);accepted=true;
                if(i.RawUiEnvelope is null||i.RawUiEnvelope.StateId!=s.Id||i.RawUiEnvelope.StateRevision!=s.Revision)throw BusinessException.Error(25);
                ScreenStateStore.CaptureUi(s,i.RawUiEnvelope);
                if(states.ConfirmLeave(s,i.RawUiEnvelope,"CodeOpen",i.Category+":"+(i.New?"New":i.Code??"None"),i.ConfirmationId,i.Choice)!=true)
                    return Json(await VmAsync(s,ct));
            }
            var rows=await service.ReadAsync(Actor,i.Category,ct);
            if(i.New&&i.Category=="EMPLOYMENT_STATUS")throw BusinessException.Error(23);
            if(i.New&&rows.Count>=99)throw BusinessException.Error(24);
            var snapshot=!i.New&&i.Code is not null?rows.SingleOrDefault(x=>x.Code==i.Code)??throw BusinessException.Error(16,"NotFound"):null;
            s.Category=i.Category;s.Snapshot=snapshot;s.IsNew=i.New;s.StopConfirmationValues=null;s.StopConfirmationId=null;s.Outcome=null;s.Revision++;
            s.CanSave=i.Category!="EMPLOYMENT_STATUS"&&(i.New||snapshot is not null);
            s.Draft=i.New?new(s.Id,s.Revision,s.Category,"","","1",true,null):FromRow(s,snapshot);
            s.CleanDraft=s.Draft;s.ResumeAllowed=false;states.Touch(s);return Json(await VmAsync(s,ct));
        }
        catch(Exception e)
        {
            if(!accepted)return Failure(SqlErrors.Map(e,40));
            s.Outcome=SqlErrors.Map(e,40);return new JsonResult(await VmAsync(s,ct),HttpJson.Options){StatusCode=HttpJson.Status(s.Outcome)};
        }
        finally{s.Gate.Release();}
    }
    [HttpPost("save")]
    public async Task<IActionResult> Save(CancellationToken ct)
    {
        var i=await HttpJson.ReadAsync<CodeSaveInput>(Request,ct);var s=states.Get<CodeState>(i.StateId,Actor.SessionId);
        if(!await s.Gate.WaitAsync(0,ct))return Failure(Outcome.Of(29,"Busy"));
        var accepted=false;
        try
        {
            states.CheckUi(s,i.StateRevision,i.TabId,i.DocumentLease);accepted=true;
            if(!s.CanSave||i.Category!=s.Category)throw BusinessException.Error(s.Category=="EMPLOYMENT_STATUS"?23:16);
            s.Draft=i;var normalized=Validation.CodeInput(i);var choice=Request.Headers["X-SP2-Confirm-Stop"].ToString();
            if(choice.Length>0&&choice is not("Yes" or "No"))throw BusinessException.Error(25);
            var matched=Guid.TryParse(Request.Headers["X-SP2-Confirmation-Id"],out var id)&&id==s.StopConfirmationId&&s.StopConfirmationValues==normalized;
            if(choice.Length>0&&!matched)throw BusinessException.Error(8,"Conflict");
            if(choice=="No"){s.StopConfirmationId=null;s.StopConfirmationValues=null;s.Outcome=Outcome.Of(30,"Cancelled");s.Revision++;return Json(await VmAsync(s,ct));}
            var confirmed=choice=="Yes"&&matched;
            if(s.Snapshot is not null&&s.Snapshot.Enabled&&!i.Enabled&&!confirmed)
            {
                s.StopConfirmationValues=normalized;s.StopConfirmationId=Guid.NewGuid();s.Outcome=Outcome.Of(38,"Confirmation");s.Revision++;
                states.Touch(s);return Json(await VmAsync(s,ct));
            }
            s.StopConfirmationValues=null;s.StopConfirmationId=null;
            s.Outcome=await service.SaveAsync(Actor,s.Snapshot,i,confirmed,ct);s.Revision++;states.Touch(s);
            if(s.Outcome.Kind=="Success")s.CommitState=CommitState.Committed;
            try
            {
                var rows=await service.ReadAsync(Actor,s.Category,ct);s.Snapshot=rows.Single(x=>x.Code==i.Code);s.IsNew=false;
                s.Draft=FromRow(s,s.Snapshot);s.CleanDraft=s.Draft;
            }
            catch
            {
                s.CanSave=false;
                s.Outcome=s.Outcome.Kind=="Success"?s.Outcome with{Message=Messages.Get(14)+" "+Messages.Get(40)}:Outcome.Of(40);
            }
            return Json(await VmAsync(s,ct));
        }
        catch(Exception e)
        {
            if(!accepted)return Failure(SqlErrors.Map(e));
            s.Outcome=SqlErrors.Map(e);if(s.Outcome.CommitState==CommitState.Unknown){s.CommitState=CommitState.Unknown;s.CanSave=false;}
            s.Revision++;return new JsonResult(await VmAsync(s,ct),HttpJson.Options){StatusCode=HttpJson.Status(s.Outcome)};
        }
        finally{s.Gate.Release();}
    }
    [HttpPost("cancel")]
    public async Task<IActionResult> Cancel(CancellationToken ct)
    {
        var i=await HttpJson.ReadAsync<CodeCancelInput>(Request,ct);var s=states.Get<CodeState>(i.StateId,Actor.SessionId);
        if(!await s.Gate.WaitAsync(0,ct))return Failure(Outcome.Of(29,"Busy"));
        var accepted=false;
        try
        {
            states.CheckUi(s,i.StateRevision,i.RawUiEnvelope.TabId,i.RawUiEnvelope.DocumentLease,recovery:i.ReloadOnly);accepted=true;
            if(s.CommitState==CommitState.Unknown&&(!i.ReloadOnly||i.ReturnToMenu))throw new BusinessException(Outcome.Of(34,"ResultUnknown",CommitState.Unknown));
            if(i.RawUiEnvelope.StateId!=s.Id||i.RawUiEnvelope.StateRevision!=s.Revision)throw BusinessException.Error(25);
            ScreenStateStore.CaptureUi(s,i.RawUiEnvelope);
            if(states.ConfirmLeave(s,i.RawUiEnvelope,"CodeCancel",i.ReturnToMenu?"Menu":"Reload",i.ConfirmationId,i.Choice)!=true)return Json(await VmAsync(s,ct));
            if(i.ReturnToMenu)return Json(new{navigation=new{url=states.IssueTicket(s,states.Add(new NavigationState(Actor.SessionId)),"/menu"),commitState=s.CommitState,messageId=(string?)null}});
            await current.RequireAsync(Actor,true,ct);var rows=await service.ReadAsync(Actor,s.Category,ct);
            var key=s.Snapshot?.Code??(s.CommitState==CommitState.Unknown?s.Draft?.Code:null);
            var saved=key is null?null:rows.SingleOrDefault(x=>x.Code==key);
            s.Snapshot=saved;s.IsNew=false;s.CommitState=CommitState.NotStarted;s.Revision++;s.StopConfirmationValues=null;s.StopConfirmationId=null;
            s.Outcome=key is not null&&saved is null?Outcome.Of(16,"NotFound"):null;
            s.Draft=FromRow(s,saved);s.CleanDraft=s.Draft;s.CanSave=saved is not null&&s.Category!="EMPLOYMENT_STATUS";states.Touch(s);
            return Json(await VmAsync(s,ct));
        }
        catch(Exception e)
        {
            if(!accepted)return Failure(SqlErrors.Map(e,40));
            s.CanSave=false;s.Outcome=SqlErrors.Map(e,40);return new JsonResult(await VmAsync(s,ct),HttpJson.Options){StatusCode=HttpJson.Status(s.Outcome)};
        }
        finally{s.Gate.Release();}
    }
    private static CodeSaveInput? FromRow(CodeState s,CodeRow? r)=>r is null?null:new(s.Id,s.Revision,r.Category,r.Code,r.Name,r.SortOrder.ToString(System.Globalization.CultureInfo.InvariantCulture),r.Enabled,r.Revision,s.TabId,s.DocumentLease);
    private async Task<CodeVm> VmAsync(CodeState s,CancellationToken ct)
    {
        IReadOnlyList<CodeRow> rows=[];try{rows=await service.ReadAsync(Actor,s.Category,ct);}catch when(s.Outcome is not null){}
        var draft=s.Draft is null?null:s.Draft with{StateRevision=s.Revision,TabId=s.TabId,DocumentLease=s.DocumentLease};
        var confirm=s.StopConfirmationId is null?null:new ConfirmationVm(s.StopConfirmationId.Value,ConfirmationKind.StopCode,"MSG-038",[ConfirmationChoice.Yes,ConfirmationChoice.No],null,null);
        return new(s.Id,s.Revision,s.Category,rows,s.Snapshot?.Code,draft,"部署・案件役割だけ保守できます。停止しても登録済みデータは保持されます。",s.Outcome,s.CanSave,false,
            states.Info(s,"/codes"),ScreenStateStore.Question(s),confirm);
    }
    private static JsonResult Failure(Outcome o)=>new(new{outcome=o},HttpJson.Options){StatusCode=HttpJson.Status(o)};
}
