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
    public async Task<IActionResult> Index(CancellationToken ct)
    {await current.RequireAsync(Actor,true,ct);return View(await VmAsync(states.Add(new CodeState(Actor.SessionId,"DEPARTMENT")),ct));}
    [HttpPost("open")]
    public async Task<IActionResult> Open(CancellationToken ct)
    {
        var input=await HttpJson.ReadAsync<CodeOpenInput>(Request,ct);await current.RequireAsync(Actor,true,ct);Validation.Category(input.Category);
        var state=input.StateId is null?states.Add(new CodeState(Actor.SessionId,input.Category)):states.Get<CodeState>(input.StateId,Actor.SessionId);
        if(!await state.Gate.WaitAsync(0,ct))return Failure(Outcome.Of(29,"Busy"));
        try
        {
            if(input.StateId is not null)ScreenStateStore.Check(state,input.StateRevision??throw BusinessException.Error(8,"Conflict"));
            if(state.CommitState==CommitState.Unknown)throw new BusinessException(Outcome.Of(34,"ResultUnknown",CommitState.Unknown));
            var rows=await service.ReadAsync(Actor,input.Category,ct);
            if(input.New&&input.Category=="EMPLOYMENT_STATUS")throw BusinessException.Error(23);
            if(input.New&&rows.Count>=99)throw BusinessException.Error(24);
            state.Category=input.Category;state.Snapshot=null;state.IsNew=input.New;state.StopConfirmationValues=null;state.Outcome=null;
            if(!input.New&&input.Code is not null)state.Snapshot=rows.SingleOrDefault(x=>x.Code==input.Code)??throw BusinessException.Error(16,"NotFound");
            state.Revision++;state.CanSave=input.Category!="EMPLOYMENT_STATUS"&&(input.New||state.Snapshot is not null);
            var row=state.Snapshot;
            state.Draft=input.New?new(state.Id,state.Revision,state.Category,"","","1",true,null):row is null?null:new(state.Id,state.Revision,row.Category,row.Code,row.Name,row.SortOrder.ToString(System.Globalization.CultureInfo.InvariantCulture),row.Enabled,row.Revision);
            return Json(await VmAsync(state,ct));
        }
        catch(Exception ex){state.Outcome=SqlErrors.Map(ex,40);return new JsonResult(await VmAsync(state,ct),HttpJson.Options){StatusCode=HttpJson.Status(state.Outcome)};}
        finally{state.Gate.Release();}
    }
    [HttpPost("save")]
    public async Task<IActionResult> Save(CancellationToken ct)
    {
        var input=await HttpJson.ReadAsync<CodeSaveInput>(Request,ct);var state=states.Get<CodeState>(input.StateId,Actor.SessionId);
        if(!await state.Gate.WaitAsync(0,ct))return Failure(Outcome.Of(29,"Busy"));
        var accepted=false;
        try
        {
            ScreenStateStore.Check(state,input.StateRevision);accepted=true;
            if(state.CommitState==CommitState.Unknown)throw new BusinessException(Outcome.Of(34,"ResultUnknown",CommitState.Unknown));
            if(!state.CanSave||input.Category!=state.Category)throw BusinessException.Error(state.Category=="EMPLOYMENT_STATUS"?23:16);
            state.Draft=input;var normalized=Validation.CodeInput(input);
            var choice=Request.Headers["X-SP2-Confirm-Stop"].ToString();
            if(choice.Length>0&&choice!="Yes")return BadRequest(new{outcome=Outcome.Of(25)});
            var confirmed=choice=="Yes"&&state.StopConfirmationValues==normalized;
            if(state.Snapshot is not null&&state.Snapshot.Enabled&&!input.Enabled&&!confirmed)
            {state.StopConfirmationValues=normalized;state.Outcome=Outcome.Of(38,"Confirmation");state.Revision++;return Json(await VmAsync(state,ct));}
            state.StopConfirmationValues=null;state.Outcome=await service.SaveAsync(Actor,state.Snapshot,input,confirmed,ct);
            state.Revision++;
            try
            {
                var rows=await service.ReadAsync(Actor,state.Category,ct);state.Snapshot=rows.Single(x=>x.Code==input.Code);state.IsNew=false;
                var row=state.Snapshot;state.Draft=new(state.Id,state.Revision,row.Category,row.Code,row.Name,row.SortOrder.ToString(System.Globalization.CultureInfo.InvariantCulture),row.Enabled,row.Revision);
            }
            catch
            {
                state.CanSave=false;
                if(state.Outcome.Kind=="Success")state.Outcome=state.Outcome with{Message=Messages.Get(14)+" "+Messages.Get(40)};
                else state.Outcome=Outcome.Of(40);
            }
            return Json(await VmAsync(state,ct));
        }
        catch(Exception exception)
        {
            if(!accepted)return Failure(SqlErrors.Map(exception));
            state.Outcome=SqlErrors.Map(exception);if(state.Outcome.CommitState==CommitState.Unknown){state.CommitState=CommitState.Unknown;state.CanSave=false;}
            state.Revision++;return new JsonResult(await VmAsync(state,ct),HttpJson.Options){StatusCode=HttpJson.Status(state.Outcome)};
        }
        finally{state.Gate.Release();}
    }
    [HttpPost("cancel")]
    public async Task<IActionResult> Cancel(CancellationToken ct)
    {
        var input=await HttpJson.ReadAsync<CodeCancelInput>(Request,ct);var state=states.Get<CodeState>(input.StateId,Actor.SessionId);
        if(!await state.Gate.WaitAsync(0,ct))return Failure(Outcome.Of(29,"Busy"));
        try
        {
            ScreenStateStore.Check(state,input.StateRevision);
            if(state.CommitState==CommitState.Unknown&&(!input.ReloadOnly||input.ReturnToMenu||!input.ConfirmDiscard))throw new BusinessException(Outcome.Of(34,"ResultUnknown",CommitState.Unknown));
            if(!input.ConfirmDiscard)return Failure(Outcome.Of(15,"Confirmation"));
            if(input.ReturnToMenu){states.Remove(state.Id);return Json(new{redirect="/menu"});}
            // Existing cancel always reads the current row and current ADMIN, never restores an old cached snapshot.
            await current.RequireAsync(Actor,true,ct);var rows=await service.ReadAsync(Actor,state.Category,ct);
            var key=state.Snapshot?.Code??(state.CommitState==CommitState.Unknown?state.Draft?.Code:null);
            state.Snapshot=key is null?null:rows.SingleOrDefault(x=>x.Code==key);state.IsNew=false;
            state.CommitState=CommitState.NotStarted;state.Revision++;state.StopConfirmationValues=null;state.Outcome=key is not null&&state.Snapshot is null?Outcome.Of(16,"NotFound"):null;
            var row=state.Snapshot;state.Draft=row is null?null:new(state.Id,state.Revision,row.Category,row.Code,row.Name,row.SortOrder.ToString(System.Globalization.CultureInfo.InvariantCulture),row.Enabled,row.Revision);
            state.CanSave=row is not null&&state.Category!="EMPLOYMENT_STATUS";return Json(await VmAsync(state,ct));
        }
        catch(Exception ex){state.CanSave=false;state.Outcome=SqlErrors.Map(ex,40);return new JsonResult(await VmAsync(state,ct),HttpJson.Options){StatusCode=HttpJson.Status(state.Outcome)};}
        finally{state.Gate.Release();}
    }
    private async Task<CodeVm> VmAsync(CodeState state,CancellationToken ct)
    {
        IReadOnlyList<CodeRow> rows=[];
        try{rows=await service.ReadAsync(Actor,state.Category,ct);}catch when(state.Outcome is not null){}
        var draft=state.Draft is null?null:state.Draft with{StateRevision=state.Revision};
        return new(state.Id,state.Revision,state.Category,rows,state.Snapshot?.Code,draft,"部署・案件役割だけ保守できます。停止しても登録済みデータは保持されます。",state.Outcome,state.CanSave,false);
    }
    private static JsonResult Failure(Outcome o)=>new(new{outcome=o},HttpJson.Options){StatusCode=HttpJson.Status(o)};
}
