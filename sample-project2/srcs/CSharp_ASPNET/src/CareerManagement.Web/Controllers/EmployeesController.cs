using System.Text.Json;
using CareerManagement.Application;
using CareerManagement.Infrastructure.Authentication;
using CareerManagement.Infrastructure.Reports;
using CareerManagement.Infrastructure.Sql;
using CareerManagement.Infrastructure.State;
using CareerManagement.Web.Filters;
using Microsoft.AspNetCore.Mvc;

namespace CareerManagement.Web.Controllers;
[Route("employees")]
public sealed class EmployeesController(ScreenStateStore states,EmployeeService service,CurrentUserService current,SessionRegistry sessions,
    BusinessClock clock,ReportService reports,ExportOperationRegistry exports,ILogger<EmployeesController> logger):Controller
{
    private Actor Actor=>(Actor)HttpContext.Items["Actor"]!;
    [HttpGet]
    public async Task<IActionResult> Index(string? state,CancellationToken ct)
    {
        var s=state is null?states.Add(new SearchState(Actor.SessionId)):states.Get<SearchState>(state,Actor.SessionId);
        return View(await SearchVmAsync(s,ct));
    }
    [HttpGet("edit")]
    public async Task<IActionResult> Edit(string state,CancellationToken ct)=>View(await EditVmAsync(states.Get<EditState>(state,Actor.SessionId),ct));
    [HttpPost("search")]
    public async Task<IActionResult> Search(CancellationToken ct)
    {
        var input=await HttpJson.ReadAsync<SearchInput>(Request,ct);var state=states.Get<SearchState>(input.StateId,Actor.SessionId);
        return await SearchCommand(state,input.StateRevision,async()=>
        {
            state.Valid=false;state.Rows.Clear();state.Selection=null;state.Applied=null;
            state.Criteria=new(input.EmployeeNo,input.Name,input.Department,input.EmploymentStatus);
            var criteria=Validation.Search(input);var data=await service.SearchAsync(Actor,criteria,ct);
            state.Criteria=criteria;state.Applied=criteria;state.Rows=data.Rows.ToList();state.Valid=true;state.Status=ResultStatus.Success;
            state.Outcome=data.Rows.Count==0?Outcome.Of(9,"Success"):null;
        },ct);
    }
    [HttpPost("invalidate")]
    public async Task<IActionResult> Invalidate(CancellationToken ct)
    {
        var input=await HttpJson.ReadAsync<StateCommand>(Request,ct);var state=states.Get<SearchState>(input.StateId,Actor.SessionId);
        return await SearchCommand(state,input.StateRevision,()=>{state.Valid=false;state.Rows.Clear();state.Selection=null;state.Status=ResultStatus.Unsearched;state.Outcome=null;return Task.CompletedTask;},ct);
    }
    [HttpPost("clear")]
    public async Task<IActionResult> Clear(CancellationToken ct)
    {
        var input=await HttpJson.ReadAsync<StateCommand>(Request,ct);var state=states.Get<SearchState>(input.StateId,Actor.SessionId);
        return await SearchCommand(state,input.StateRevision,()=>{state.Valid=false;state.Rows.Clear();state.Selection=null;state.Applied=null;state.Criteria=new(null,null,null,"01");state.Status=ResultStatus.Unsearched;state.Outcome=null;return Task.CompletedTask;},ct);
    }
    [HttpPost("open")]
    public async Task<IActionResult> Open(CancellationToken ct)
    {
        var input=await HttpJson.ReadAsync<OpenInput>(Request,ct);var state=states.Get<SearchState>(input.SearchStateId,Actor.SessionId);
        if(!await state.Gate.WaitAsync(0,ct))return Failure(Outcome.Of(29,"Busy"));
        try
        {
            ScreenStateStore.Check(state,input.StateRevision);EmployeeSnapshot? snapshot=null;
            if(input.Mode==OpenMode.Edit)
            {
                Selected(state,input.EmployeeId);snapshot=(await service.ReadAsync(Actor,input.EmployeeId!.Value,ct)).Snapshot;
                state.Selection=input.EmployeeId;
            }
            else if(input.EmployeeId is not null)throw BusinessException.Error(25);
            else {var rows=await service.SearchAsync(Actor,new(null,null,null,null),ct);if(rows.Rows.Count>=200)throw BusinessException.Error(18);}
            var edit=states.Add(new EditState(Actor.SessionId,state.Id,snapshot,snapshot?.Employee.Raw()??EmployeeRaw.Empty(clock.Begin().Date)));
            state.Revision++;return Json(new{redirect="/employees/edit?state="+edit.Id,edit=await EditVmAsync(edit,ct),searchRevision=state.Revision});
        }
        catch(BusinessException ex){return Failure(ex.Outcome);}
        finally{state.Gate.Release();}
    }
    [HttpPost("draft")]
    public async Task<IActionResult> Draft(CancellationToken ct)
    {
        var input=await HttpJson.ReadAsync<DraftInput>(Request,ct);var state=states.Get<EditState>(input.EditStateId,Actor.SessionId);
        return await EditCommand(state,input.StateRevision,()=>
        {
            if(input.Confirm is null)throw BusinessException.Error(25);
            var command=input;
            if(state.Confirmation is not null)
            {
                var question=state.Confirmation;
                if(input.Confirm.ConfirmationId!=question.ConfirmationId||input.Confirm.Kind!=question.Kind||!question.AllowedChoices.Contains(input.Confirm.Choice))throw BusinessException.Error(25);
                command=state.Deferred??throw BusinessException.Error(25);
                state.Confirmation=null;
                if(input.Confirm.Choice==ConfirmationChoice.Cancel){state.Deferred=null;return Task.CompletedTask;}
                if(question.Kind==ConfirmationKind.ApplyPending)
                {
                    if(input.Confirm.Choice==ConfirmationChoice.No){Question(state,ConfirmationKind.DiscardPending,33,command);return Task.CompletedTask;}
                    Apply(state,input.Fields??command.Fields);
                }
                else if(question.Kind==ConfirmationKind.DiscardPending)
                {
                    if(input.Confirm.Choice==ConfirmationChoice.No){state.Deferred=null;return Task.CompletedTask;}
                }
                else if(question.Kind==ConfirmationKind.RemoveRow)
                {
                    if(input.Confirm.Choice==ConfirmationChoice.Yes)Remove(state,command.TargetClientRowKey);
                    state.Deferred=null;return Task.CompletedTask;
                }
                state.Deferred=null;
            }
            else
            {
                if(input.Confirm.Kind!=ConfirmationKind.None||input.Confirm.Choice!=ConfirmationChoice.None||input.Confirm.ConfirmationId is not null)throw BusinessException.Error(25);
                var dirty=input.Fields is not null&&input.Fields!=state.Pending;
                if(input.Action is DraftAction.Add or DraftAction.Select or DraftAction.SwitchTab&&dirty)
                {Question(state,ConfirmationKind.ApplyPending,32,input);return Task.CompletedTask;}
            }
            switch(command.Action)
            {
                case DraftAction.Apply:Apply(state,input.Fields??command.Fields);break;
                case DraftAction.Add:
                    if(state.Careers.Count>=20)throw BusinessException.Error(18);
                    state.Pending=CareerRaw.Empty();state.Selected=state.Pending.ClientRowKey;state.ActiveTab=EditTab.Careers;break;
                case DraftAction.Select:
                    state.Pending=state.Careers.SingleOrDefault(x=>x.ClientRowKey==command.TargetClientRowKey)??throw BusinessException.Error(25);
                    state.Selected=state.Pending.ClientRowKey;state.ActiveTab=EditTab.Careers;break;
                case DraftAction.SwitchTab:
                    state.ActiveTab=command.TargetTab??throw BusinessException.Error(25);
                    if(state.Selected.HasValue)state.Pending=state.Careers.SingleOrDefault(x=>x.ClientRowKey==state.Selected);
                    break;
                case DraftAction.Remove:
                    if(command.TargetClientRowKey is null||!state.Careers.Any(x=>x.ClientRowKey==command.TargetClientRowKey))throw BusinessException.Error(25);
                    Question(state,ConfirmationKind.RemoveRow,31,command);break;
                default:throw BusinessException.Error(25);
            }
            return Task.CompletedTask;
        },ct);
    }
    private static void Question(EditState state,ConfirmationKind kind,int msg,DraftInput input)
    {
        state.Deferred=input;state.Confirmation=new(Guid.NewGuid(),kind,$"MSG-{msg:000}",kind==ConfirmationKind.ApplyPending?[ConfirmationChoice.Yes,ConfirmationChoice.No,ConfirmationChoice.Cancel]:[ConfirmationChoice.Yes,ConfirmationChoice.No],input.TargetClientRowKey,input.TargetTab);
        state.Outcome=Outcome.Of(msg,"Confirmation");
    }
    private void Apply(EditState state,CareerRaw? raw)
    {
        if(raw is null||state.Selected!=raw.ClientRowKey)throw BusinessException.Error(25);
        var normalized=Validation.Career(raw,clock.Begin().Month,Math.Max(1,state.Careers.FindIndex(x=>x.ClientRowKey==raw.ClientRowKey)+1));
        var at=state.Careers.FindIndex(x=>x.ClientRowKey==raw.ClientRowKey);
        if(at<0){if(raw.CareerId is not null||state.Careers.Count>=20)throw BusinessException.Error(18);state.Careers.Add(normalized.Raw());}
        else {if(state.Careers[at].CareerId!=raw.CareerId)throw BusinessException.Error(25);state.Careers[at]=normalized.Raw();}
        state.Pending=normalized.Raw();state.Selected=raw.ClientRowKey;
    }
    private static void Remove(EditState state,Guid? key)
    {
        var row=state.Careers.SingleOrDefault(x=>x.ClientRowKey==key)??throw BusinessException.Error(25);
        if(row.CareerId.HasValue)state.Removed.Add(row.CareerId.Value);state.Careers.Remove(row);
        if(state.Selected==key){state.Selected=null;state.Pending=null;}
    }
    [HttpPost("save")]
    public async Task<IActionResult> Save(CancellationToken ct)
    {
        var input=await HttpJson.ReadAsync<SaveInput>(Request,ct);var state=states.Get<EditState>(input.EditStateId,Actor.SessionId);
        if(!await state.Gate.WaitAsync(0,ct))return Failure(Outcome.Of(29,"Busy"));
        var accepted=false;
        try
        {
            ScreenStateStore.Check(state,input.StateRevision);accepted=true;CanSave(state);
            state.Employee=input.Employee;state.AttemptedEmployeeNo=input.Employee.EmployeeNo;
            if(!state.Removed.SetEquals(input.RemovedCareerIds))throw BusinessException.Error(25);
            if(state.Selected.HasValue)
            {
                var edited=input.Careers.Where(x=>x.ClientRowKey==state.Selected.Value).ToArray();
                if(edited.Length>1)throw BusinessException.Error(25);
                if(edited.Length==1)state.Pending=edited[0];
            }
            // Send the whole visible aggregate, including an unapplied pending row, in one request.
            var result=await service.SaveAsync(Actor,state.Snapshot,input.Employee,input.Careers,input.RemovedCareerIds,ct);
            state.Outcome=result.Outcome;state.Revision++;
            if(result.Outcome.Kind=="NoChange")return Json(await EditVmAsync(state,ct));
            state.Completed=true;state.CommitState=CommitState.Committed;
            var search=states.Get<SearchState>(state.SearchId,Actor.SessionId);
            await search.Gate.WaitAsync(ct);
            try
            {
                search.Valid=false;search.Rows.Clear();search.Selection=null;search.Revision++;
                try
                {
                    if(search.Applied is not null)
                    {
                        var data=await service.SearchAsync(Actor,search.Applied,ct);search.Rows=data.Rows.ToList();search.Valid=true;search.Status=ResultStatus.Success;
                        search.Selection=search.Rows.Any(x=>x.EmployeeId==result.EmployeeId)?result.EmployeeId:null;
                    }
                    search.Outcome=Outcome.Ok();
                }
                catch{search.Status=ResultStatus.Failed;search.Outcome=Outcome.Ok() with{Message=Messages.Get(14)+" "+Messages.Get(40)};}
            }
            finally{search.Gate.Release();}
            return Json(new{redirect="/employees?state="+search.Id,outcome=search.Outcome});
        }
        catch(Exception exception)
        {
            if(!accepted)return Failure(SqlErrors.Map(exception));
            state.Outcome=SqlErrors.Map(exception);if(state.Outcome.CommitState==CommitState.Unknown)state.CommitState=CommitState.Unknown;
            state.Revision++;return new JsonResult(await EditVmAsync(state,ct),HttpJson.Options){StatusCode=HttpJson.Status(state.Outcome)};
        }
        finally{state.Gate.Release();}
    }
    [HttpPost("cancel")]
    public async Task<IActionResult> Cancel(CancellationToken ct)
    {
        var input=await HttpJson.ReadAsync<CancelInput>(Request,ct);var state=states.Get<EditState>(input.EditStateId,Actor.SessionId);
        if(!await state.Gate.WaitAsync(0,ct))return Failure(Outcome.Of(29,"Busy"));
        try
        {
            ScreenStateStore.Check(state,input.StateRevision);
            if(state.CommitState==CommitState.Unknown&&(!input.ReloadOnly||!input.ConfirmDiscard||input.ReturnToMenu))return Failure(Outcome.Of(34,"ResultUnknown",CommitState.Unknown));
            if(!input.ConfirmDiscard)return Failure(Outcome.Of(15,"Confirmation"));
            if(input.ReloadOnly)
            {
                long? id=state.Snapshot?.EmployeeId;
                if(id is null&&state.AttemptedEmployeeNo is not null)id=(await service.SearchAsync(Actor,new(state.AttemptedEmployeeNo,null,null,null),ct)).Rows.SingleOrDefault()?.EmployeeId;
                if(id is not null)
                {
                    state.Snapshot=(await service.ReadAsync(Actor,id.Value,ct)).Snapshot;state.Employee=state.Snapshot.Employee.Raw();state.Careers=state.Snapshot.Careers.Select(x=>x.Raw()).ToList();
                }
                else {state.Snapshot=null;state.Careers=[];state.Outcome=Outcome.Of(19,"NotFound");}
                state.Removed.Clear();state.Pending=null;state.Selected=null;state.Completed=false;state.CommitState=CommitState.NotStarted;state.Revision++;
                return Json(await EditVmAsync(state,ct));
            }
            states.Remove(state.Id);return Json(new{redirect=input.ReturnToMenu?"/menu":"/employees?state="+state.SearchId});
        }
        catch(BusinessException b){return Failure(b.Outcome);}
        finally{state.Gate.Release();}
    }
    [HttpPost("export")]
    public async Task<IActionResult> Export(CancellationToken ct)
    {
        var input=await HttpJson.ReadAsync<ExportInput>(Request,ct);var state=states.Get<SearchState>(input.SearchStateId,Actor.SessionId);
        ExportOperation operation;
        if(!await state.Gate.WaitAsync(0,ct))return Failure(Outcome.Of(29,"Busy"));
        try {ScreenStateStore.Check(state,input.StateRevision);Selected(state,input.EmployeeId);state.Selection=input.EmployeeId;operation=exports.Start(Actor.SessionId,state.Id,input.OperationId);}
        finally{state.Gate.Release();}
        using var linked=CancellationTokenSource.CreateLinkedTokenSource(ct,operation.Cancellation.Token);
        try
        {
            var token=linked.Token;ReportSnapshot snapshot;
            try{snapshot=await service.ReportAsync(Actor,input.EmployeeId,token);}
            catch(BusinessException b)when(b.Outcome.MessageId=="MSG-034"){throw BusinessException.Error(28);}
            catch(Exception e)when(e is System.Data.Common.DbException or IOException){throw BusinessException.Error(28);}
            lock(operation.Gate){token.ThrowIfCancellationRequested();operation.Phase="Generating";}
            using var stream=await Task.Run(()=>reports.Create(snapshot,token),token);
            await current.RequireAsync(Actor,false,token); // only current user is re-read; snapshot data stays fixed.
            if(!sessions.Touch(Actor.SessionId,Actor.UserId))throw BusinessException.Error(2,"Expired");
            await CookieActor.SignInAsync(HttpContext,Actor); // cookie refresh must precede attachment headers/start.
            lock(operation.Gate)
            {
                operation.Phase="Ready";token.ThrowIfCancellationRequested();
                Response.ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
                var filename=$"職務経歴書_{snapshot.Employee.Employee.EmployeeNo}_{snapshot.Captured.Date:yyyyMMdd}.xlsx";
                Response.Headers.ContentDisposition="attachment; filename=career.xlsx; filename*=UTF-8''"+Uri.EscapeDataString(filename);
                Response.ContentLength=stream.Length;Response.Headers["X-SP2-Message"]="MSG-035";
                operation.Phase="Started"; // serialized with Cancel before StartAsync is sent.
            }
            await Response.StartAsync(token);await stream.CopyToAsync(Response.Body,token);return new EmptyResult();
        }
        catch(Exception exception)
        {
            var outcome=exception is OperationCanceledException?Outcome.Of(30,"Cancelled"):SqlErrors.Map(exception,13);
            if(!Response.HasStarted){Response.Headers.Remove("Content-Disposition");Response.ContentLength=null;return Failure(outcome);}
            logger.LogWarning("Export interrupted {OperationId} MSG-036",operation.Id);HttpContext.Abort();return new EmptyResult();
        }
        finally{exports.Finish(operation);}
    }
    [HttpPost("export/cancel")]
    public async Task<IActionResult> ExportCancel(CancellationToken ct)
    {var input=await HttpJson.ReadAsync<ExportCancelInput>(Request,ct);states.Get<SearchState>(input.SearchStateId,Actor.SessionId);return Json(exports.Cancel(Actor.SessionId,input.SearchStateId,input.OperationId));}
    private static void Selected(SearchState state,long? employee)
    {if(!state.Valid||employee is null||!state.Rows.Any(x=>x.EmployeeId==employee))throw BusinessException.Error(11);}
    private static void CanSave(EditState s)
    {if(s.CommitState==CommitState.Unknown)throw new BusinessException(Outcome.Of(34,"ResultUnknown",CommitState.Unknown));if(s.Completed)throw BusinessException.Error(8,"Conflict");}
    private async Task<IActionResult> SearchCommand(SearchState state,int revision,Func<Task> action,CancellationToken ct)
    {
        if(!await state.Gate.WaitAsync(0,ct))return Failure(Outcome.Of(29,"Busy"));
        try
        {
            ScreenStateStore.Check(state,revision);
            try{await action();}catch(Exception e){state.Valid=false;state.Rows.Clear();state.Selection=null;state.Outcome=SqlErrors.Map(e,40);state.Status=state.Outcome.MessageId=="MSG-010"?ResultStatus.LimitExceeded:ResultStatus.Failed;}
            state.Revision++;return new JsonResult(await SearchVmAsync(state,ct),HttpJson.Options){StatusCode=state.Outcome is null?200:HttpJson.Status(state.Outcome)};
        }
        finally{state.Gate.Release();}
    }
    private async Task<IActionResult> EditCommand(EditState state,int revision,Func<Task> action,CancellationToken ct)
    {
        if(!await state.Gate.WaitAsync(0,ct))return Failure(Outcome.Of(29,"Busy"));
        try
        {
            ScreenStateStore.Check(state,revision);CanSave(state);state.Outcome=null;
            try{await action();}catch(Exception e){state.Outcome=SqlErrors.Map(e);}
            state.Revision++;return new JsonResult(await EditVmAsync(state,ct),HttpJson.Options){StatusCode=state.Outcome is null?200:HttpJson.Status(state.Outcome)};
        }
        finally{state.Gate.Release();}
    }
    private async Task<SearchVm> SearchVmAsync(SearchState s,CancellationToken ct)=>new(s.Id,s.Revision,s.Criteria,s.Applied,s.Rows.ToArray(),s.Selection,s.Valid?s.Rows.Count:null,s.Status,s.Outcome,await service.CodesAsync(Actor,ct));
    private async Task<EditVm> EditVmAsync(EditState s,CancellationToken ct)=>new(s.Id,s.Revision,s.Employee,s.Careers.ToArray(),s.Pending,s.Selected,s.ActiveTab,s.Confirmation,s.Outcome,!s.Completed&&s.CommitState!=CommitState.Unknown,s.Careers.Count<20,false,await service.CodesAsync(Actor,ct),s.Removed.ToArray(),s.Snapshot is null);
    private static JsonResult Failure(Outcome outcome)=>new(new{outcome},HttpJson.Options){StatusCode=HttpJson.Status(outcome)};
}
