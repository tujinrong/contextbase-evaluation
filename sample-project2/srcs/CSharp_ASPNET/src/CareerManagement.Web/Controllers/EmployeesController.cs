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
    BusinessClock clock,ReportService reports,ExportOperationRegistry exports,SearchReturnCoordinator returns,ILogger<EmployeesController> logger):Controller
{
    private Actor Actor=>(Actor)HttpContext.Items["Actor"]!;
    [HttpGet]
    public async Task<IActionResult> Index(string? nav,CancellationToken ct)
    {
        SearchState s;
        try{s=nav is null?states.Add(new SearchState(Actor.SessionId)):states.Consume<SearchState>(nav,Actor.SessionId,"/employees");}
        catch(BusinessException e)when(e.Outcome.MessageId=="MSG-041")
        {s=states.Add(new SearchState(Actor.SessionId){Outcome=e.Outcome});Response.StatusCode=410;}
        return View(await SearchVmAsync(s,ct));
    }
    [HttpGet("new")]
    public Task<IActionResult> New(string? nav,CancellationToken ct)=>DisplayEdit(null,nav,ct);
    [HttpGet("{employeeId:long:min(1)}/edit")]
    public Task<IActionResult> Edit(long employeeId,string? nav,CancellationToken ct)=>DisplayEdit(employeeId,nav,ct);
    private async Task<IActionResult> DisplayEdit(long? employeeId,string? nav,CancellationToken ct)
    {
        var route=employeeId is null?"/employees/new":$"/employees/{employeeId}/edit";
        EditState s;
        if(nav is not null)s=states.Consume<EditState>(nav,Actor.SessionId,route);
        else
        {
            EmployeeSnapshot? snapshot=employeeId is null?null:(await service.ReadAsync(Actor,employeeId.Value,ct)).Snapshot;
            if(employeeId is null)await service.RequireNewCapacityAsync(Actor,ct);
            s=states.Add(new EditState(Actor.SessionId,"",snapshot,snapshot?.Employee.Raw()??EmployeeRaw.Empty(clock.Begin().Date)));
            s.ReturnSnapshot=returns.Initial(Actor,s.TabId);
        }
        return View("Edit",await EditVmAsync(s,ct));
    }
    [HttpPost("search")]
    public async Task<IActionResult> Search(CancellationToken ct)
    {
        var input=await HttpJson.ReadAsync<SearchInput>(Request,ct);var state=states.Get<SearchState>(input.StateId,Actor.SessionId);
        return await SearchCommand(state,input.StateRevision,input.TabId,input.DocumentLease,async()=>
        {
            ScreenStateStore.CaptureRaw(state,input.Raw,input.ClientSequence,state.ScrollTop);
            state.Valid=false;state.Rows.Clear();state.Selection=null;
            var criteria=Validation.Search(input);var data=await service.SearchAsync(Actor,criteria,ct);
            state.Applied=criteria;state.Rows=data.Rows.ToList();state.Valid=true;state.Status=ResultStatus.Success;state.ScrollTop=0;
            state.Outcome=data.Rows.Count==0?Outcome.Of(9,"Success"):null;
        },ct);
    }
    [HttpPost("invalidate")]
    public async Task<IActionResult> Invalidate(CancellationToken ct)
    {
        var input=await HttpJson.ReadAsync<InvalidateInput>(Request,ct);var state=states.Get<SearchState>(input.StateId,Actor.SessionId);
        return await SearchCommand(state,input.StateRevision,input.TabId,input.DocumentLease,()=>
        {
            ScreenStateStore.CaptureRaw(state,input.Raw,input.ClientSequence,input.ScrollTop);
            state.Valid=false;state.Rows.Clear();state.Selection=null;state.Status=ResultStatus.Unapplied;state.Outcome=null;return Task.CompletedTask;
        },ct);
    }
    [HttpPost("checkpoint")]
    public async Task<IActionResult> Checkpoint(CancellationToken ct)
    {
        var i=await HttpJson.ReadAsync<InvalidateInput>(Request,ct);var s=states.Get<SearchState>(i.StateId,Actor.SessionId);
        return await SearchCommand(s,i.StateRevision,i.TabId,i.DocumentLease,()=>{ScreenStateStore.CaptureRaw(s,i.Raw,i.ClientSequence,i.ScrollTop);return Task.CompletedTask;},ct);
    }
    [HttpPost("select")]
    public async Task<IActionResult> Select(CancellationToken ct)
    {
        var i=await HttpJson.ReadAsync<SelectionInput>(Request,ct);var s=states.Get<SearchState>(i.StateId,Actor.SessionId);
        return await SearchCommand(s,i.StateRevision,i.TabId,i.DocumentLease,()=>{Selected(s,i.EmployeeId);s.Selection=i.EmployeeId;return Task.CompletedTask;},ct);
    }
    [HttpPost("resume")]
    public async Task<IActionResult> Resume(CancellationToken ct)
    {
        var i=await HttpJson.ReadAsync<SearchResumeInput>(Request,ct);var s=states.Get<ScreenState>(i.CurrentStateId,Actor.SessionId);
        if(!await s.Gate.WaitAsync(0,ct))return Failure(Outcome.Of(29,"Busy"));
        try
        {
            states.CheckUi(s,s.Revision,i.CurrentTabId,i.DocumentLease,background:true);
            if(!s.ResumeAllowed)throw BusinessException.Error(41,"UiExpired");
            var snapshot=states.ReadResume(i.ResumeRef,i.SourceTabId,Actor.SessionId);
            if(s is SearchState search)
            {await returns.RestoreAsync(Actor,search,snapshot,null,null,ct);search.Revision++;return Json(await SearchVmAsync(search,ct));}
            if(s is EditState edit)
            {
                if(edit.Dirty)throw BusinessException.Error(41,"UiExpired");
                edit.ReturnSnapshot=states.CopyReturnReference(edit,snapshot);edit.ResumeAllowed=false;edit.Revision++;
                return Json(await EditVmAsync(edit,ct));
            }
            throw BusinessException.Error(25);
        }
        catch(BusinessException e)
        {
            if(e.Outcome.MessageId!="MSG-041")return Failure(e.Outcome);
            if(s is SearchState search){search.Outcome=e.Outcome;search.ResumeAllowed=false;states.Checkpoint(search);return Json(await SearchVmAsync(search,ct));}
            if(s is EditState edit){edit.Outcome=e.Outcome;edit.ResumeAllowed=false;return Json(await EditVmAsync(edit,ct));}
            return Failure(e.Outcome);
        }
        finally{s.Gate.Release();}
    }
    [HttpPost("clear")]
    public async Task<IActionResult> Clear(CancellationToken ct)
    {
        var input=await HttpJson.ReadAsync<StateCommand>(Request,ct);var state=states.Get<SearchState>(input.StateId,Actor.SessionId);
        return await SearchCommand(state,input.StateRevision,input.TabId,input.DocumentLease,()=>{state.Valid=false;state.Rows.Clear();state.Selection=null;state.Applied=null;state.Raw=SearchRaw.Initial;state.ScrollTop=0;state.Status=ResultStatus.Unsearched;state.Outcome=null;return Task.CompletedTask;},ct);
    }
    [HttpPost("open")]
    public async Task<IActionResult> Open(CancellationToken ct)
    {
        var input=await HttpJson.ReadAsync<OpenInput>(Request,ct);var state=states.Get<SearchState>(input.SearchStateId,Actor.SessionId);
        if(!await state.Gate.WaitAsync(0,ct))return Failure(Outcome.Of(29,"Busy"));
        var accepted=false;
        try
        {
            states.CheckUi(state,state.Revision,input.TabId,input.DocumentLease);
            if(input.OpenOperationId==Guid.Empty)throw BusinessException.Error(25);
            var signature=JsonSerializer.Serialize(input,HttpJson.Options);
            var existing=states.ExistingOpen(state,input.OpenOperationId,signature);if(existing is not null)return Navigation(existing);
            ScreenStateStore.Check(state,input.StateRevision);accepted=true;
            ScreenStateStore.CaptureRaw(state,input.Raw,input.ClientSequence,input.ScrollTop);EmployeeSnapshot? snapshot=null;
            if(input.Mode==OpenMode.Edit)
            {
                Selected(state,input.EmployeeId);snapshot=(await service.ReadAsync(Actor,input.EmployeeId!.Value,ct)).Snapshot;
                state.Selection=input.EmployeeId;
            }
            else if(input.EmployeeId is not null)throw BusinessException.Error(25);
            else await service.RequireNewCapacityAsync(Actor,ct);
            var edit=states.Add(new EditState(Actor.SessionId,state.Id,snapshot,snapshot?.Employee.Raw()??EmployeeRaw.Empty(clock.Begin().Date)));
            states.Touch(state);states.Checkpoint(state);edit.ReturnSnapshot=state.Capture();edit.ResumeRef=state.ResumeRef;edit.SourceTabId=state.SourceTabId;
            state.Revision++;var route=snapshot is null?"/employees/new":$"/employees/{snapshot.EmployeeId}/edit";
            return Navigation(states.IssueTicket(state,edit,route,openOperation:input.OpenOperationId,openSignature:signature));
        }
        catch(Exception ex)
        {
            if(!accepted)return Failure(SqlErrors.Map(ex,40));
            state.Revision++;states.Checkpoint(state);state.Outcome=SqlErrors.Map(ex,40);return new JsonResult(await SearchVmAsync(state,ct),HttpJson.Options){StatusCode=HttpJson.Status(state.Outcome)};
        }
        finally{state.Gate.Release();}
    }
    [HttpPost("draft")]
    public async Task<IActionResult> Draft(CancellationToken ct)
    {
        var input=await HttpJson.ReadAsync<DraftInput>(Request,ct);var state=states.Get<EditState>(input.EditStateId,Actor.SessionId);
        return await EditCommand(state,input.StateRevision,input.TabId,input.DocumentLease,()=>
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
                var dirty=input.Fields is not null&&(input.Fields!=state.Pending||!state.Careers.Any(x=>x.ClientRowKey==input.Fields.ClientRowKey));
                if((input.Action is DraftAction.Add or DraftAction.Select or DraftAction.SwitchTab)&&dirty)
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
                    if(state.Pending is null)state.Selected=null;
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
        CareerRaw[]? attemptedCareers=null;
        try
        {
            states.CheckUi(state,input.StateRevision,input.TabId,input.DocumentLease);accepted=true;CanSave(state);
            state.Employee=input.Employee;state.AttemptedEmployeeNo=input.Employee.EmployeeNo;
            if(!state.Removed.SetEquals(input.RemovedCareerIds))throw BusinessException.Error(25);
            var careers=input.Careers.ToList();
            if(input.Pending is not null)
            {
                if(state.Selected!=input.Pending.ClientRowKey||state.Pending is null||state.Pending.CareerId!=input.Pending.CareerId)throw BusinessException.Error(25);
                var at=careers.FindIndex(x=>x.ClientRowKey==input.Pending.ClientRowKey);
                if(at<0)careers.Add(input.Pending);else careers[at]=input.Pending;
                state.Pending=input.Pending;
            }
            else if(state.Pending is not null)throw BusinessException.Error(25);
            var ownedKeys=state.Careers.Select(x=>x.ClientRowKey).ToHashSet();if(state.Pending is not null)ownedKeys.Add(state.Pending.ClientRowKey);
            if(careers.Any(x=>!ownedKeys.Contains(x.ClientRowKey)))throw BusinessException.Error(25);
            attemptedCareers=careers.ToArray();
            var result=await service.SaveAsync(Actor,state.Snapshot,input.Employee,careers.ToArray(),input.RemovedCareerIds,ct);
            state.Outcome=result.Outcome;state.Revision++;
            states.Touch(state);
            if(result.Outcome.Kind=="NoChange")
            {state.Careers=careers;state.CleanEmployee=state.Employee;state.CleanCareers=careers.ToArray();return Json(await EditVmAsync(state,ct));}
            state.Completed=true;state.CommitState=CommitState.Committed;
            var search=await returns.ReturnAsync(Actor,state.ReturnSnapshot,result.EmployeeId,result.Outcome,ct);
            return Navigation(states.IssueTicket(state,search,"/employees",result.Outcome.MessageId),CommitState.Committed,result.Outcome.MessageId);
        }
        catch(Exception exception)
        {
            if(!accepted)return Failure(SqlErrors.Map(exception));
            state.Outcome=SqlErrors.Map(exception);if(state.Outcome.CommitState==CommitState.Unknown)state.CommitState=CommitState.Unknown;
            var error=state.Outcome.FieldErrors.FirstOrDefault();
            if(error is not null)
            {
                var careerField=int.TryParse(error.ItemId.AsSpan(5),out var item)&&item is >=14 and <=24;
                state.ActiveTab=careerField?EditTab.Careers:EditTab.Basic;
                if(careerField&&attemptedCareers is not null&&error.CareerRowNumber is >0&&error.CareerRowNumber<=attemptedCareers.Length)
                {state.Careers=attemptedCareers.ToList();state.Pending=attemptedCareers[error.CareerRowNumber.Value-1];state.Selected=state.Pending.ClientRowKey;}
            }
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
            states.CheckUi(state,input.StateRevision,input.RawUiEnvelope.TabId,input.RawUiEnvelope.DocumentLease,recovery:input.ReloadOnly);
            if(state.CommitState==CommitState.Unknown&&(!input.ReloadOnly||input.ReturnToMenu))return Failure(Outcome.Of(34,"ResultUnknown",CommitState.Unknown));
            if(input.RawUiEnvelope.StateId!=state.Id||input.RawUiEnvelope.StateRevision!=state.Revision)throw BusinessException.Error(8,"Conflict");
            ScreenStateStore.CaptureUi(state,input.RawUiEnvelope);
            var decision=states.ConfirmLeave(state,input.RawUiEnvelope,"Cancel",input.ReloadOnly?"Reload":input.ReturnToMenu?"Menu":"Search",input.ConfirmationId,input.Choice);
            if(decision!=true)return Json(await EditVmAsync(state,ct));
            if(input.ReloadOnly)
            {
                long? id=state.Snapshot?.EmployeeId;
                if(id is null&&state.AttemptedEmployeeNo is not null)id=(await service.SearchAsync(Actor,new(state.AttemptedEmployeeNo,null,null,null),ct)).Rows.SingleOrDefault()?.EmployeeId;
                var snapshot=id is null?null:(await service.ReadAsync(Actor,id.Value,ct)).Snapshot;
                var fresh=states.Add(new EditState(Actor.SessionId,"",snapshot,snapshot?.Employee.Raw()??EmployeeRaw.Empty(clock.Begin().Date)));
                fresh.ReturnSnapshot=state.ReturnSnapshot;fresh.ResumeRef=state.ResumeRef;fresh.SourceTabId=state.SourceTabId;state.LeaseActive=false;
                return Json(await EditVmAsync(fresh,ct));
            }
            states.Touch(state);
            if(input.ReturnToMenu)return Navigation(states.IssueTicket(state,states.Add(new NavigationState(Actor.SessionId)),"/menu"));
            var search=await returns.ReturnAsync(Actor,state.ReturnSnapshot,null,null,ct);
            return Navigation(states.IssueTicket(state,search,"/employees"));
        }
        catch(Exception e)
        {
            state.Outcome=SqlErrors.Map(e,40);
            if(input.ReloadOnly)state.OperationsBlocked=true;
            if(input.ReloadOnly)return new JsonResult(await EditVmAsync(state,ct),HttpJson.Options){StatusCode=HttpJson.Status(state.Outcome)};
            return Failure(state.Outcome);
        }
        finally{state.Gate.Release();}
    }
    [HttpPost("export")]
    public async Task<IActionResult> Export(CancellationToken ct)
    {
        var input=await HttpJson.ReadAsync<ExportInput>(Request,ct);var state=states.Get<SearchState>(input.SearchStateId,Actor.SessionId);
        ExportOperation operation;
        if(!await state.Gate.WaitAsync(0,ct))return Failure(Outcome.Of(29,"Busy"));
        try
        {
            states.CheckUi(state,input.StateRevision,input.TabId,input.DocumentLease);
            ScreenStateStore.CaptureRaw(state,input.Raw,input.ClientSequence,input.ScrollTop);Selected(state,input.EmployeeId);
            if(state.Selection!=input.EmployeeId)throw BusinessException.Error(11);
            operation=exports.Start(Actor.SessionId,state.Id,input.OperationId);state.Revision++;states.Touch(state);states.Checkpoint(state);
        }
        catch(Exception e){state.Outcome=SqlErrors.Map(e,40);state.Revision++;states.Checkpoint(state);return new JsonResult(await SearchVmAsync(state,ct),HttpJson.Options){StatusCode=HttpJson.Status(state.Outcome)};}
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
                Response.Headers["X-SP2-State-Revision"]=state.Revision.ToString(System.Globalization.CultureInfo.InvariantCulture);
                Response.Headers["X-SP2-Resume-Ref"]=state.ResumeRef;Response.Headers["X-SP2-Source-Tab"]=state.SourceTabId;
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
    private async Task<IActionResult> SearchCommand(SearchState state,int revision,string tab,string lease,Func<Task> action,CancellationToken ct)
    {
        if(!await state.Gate.WaitAsync(0,ct))return Failure(Outcome.Of(29,"Busy"));
        try
        {
            states.CheckUi(state,revision,tab,lease);
            try{await action();}catch(Exception e){state.Valid=false;state.Rows.Clear();state.Selection=null;state.Outcome=SqlErrors.Map(e,40);state.Status=state.Outcome.MessageId=="MSG-010"?ResultStatus.LimitExceeded:ResultStatus.Failed;}
            state.Revision++;if(state.Outcome is null||HttpJson.Status(state.Outcome)<400)states.Touch(state);states.Checkpoint(state);
            return new JsonResult(await SearchVmAsync(state,ct),HttpJson.Options){StatusCode=state.Outcome is null?200:HttpJson.Status(state.Outcome)};
        }
        finally{state.Gate.Release();}
    }
    private async Task<IActionResult> EditCommand(EditState state,int revision,string tab,string lease,Func<Task> action,CancellationToken ct)
    {
        if(!await state.Gate.WaitAsync(0,ct))return Failure(Outcome.Of(29,"Busy"));
        try
        {
            states.CheckUi(state,revision,tab,lease);CanSave(state);state.Outcome=null;
            try{await action();}catch(Exception e){state.Outcome=SqlErrors.Map(e);}
            state.Revision++;if(state.Outcome is null||HttpJson.Status(state.Outcome)<400)states.Touch(state);
            return new JsonResult(await EditVmAsync(state,ct),HttpJson.Options){StatusCode=state.Outcome is null?200:HttpJson.Status(state.Outcome)};
        }
        finally{state.Gate.Release();}
    }
    private async Task<SearchVm> SearchVmAsync(SearchState s,CancellationToken ct)
    {
        if(s.ResumeRef is null)states.Checkpoint(s);
        var selected=s.Rows.SingleOrDefault(x=>x.EmployeeId==s.Selection);
        return new(s.Id,s.Revision,s.Raw,s.Applied,s.Rows.ToArray(),s.Selection,s.Valid&&s.Status==ResultStatus.Success?s.Rows.Count:null,s.Status,s.Outcome,
            await service.CodesAsync(Actor,ct),s.ScrollTop,s.ClientSequence,states.Info(s,"/employees"),selected is null?null:$"選択中：{selected.EmployeeNo} {selected.Name}");
    }
    private async Task<EditVm> EditVmAsync(EditState s,CancellationToken ct)=>new(s.Id,s.Revision,s.Employee,s.Careers.ToArray(),s.Pending,s.Selected,s.ActiveTab,s.Confirmation,s.Outcome,
        !s.Completed&&!s.OperationsBlocked&&s.CommitState!=CommitState.Unknown,s.Careers.Count<20,false,await service.CodesAsync(Actor,ct),s.Removed.ToArray(),s.Snapshot is null,
        states.Info(s,s.Snapshot is null?"/employees/new":$"/employees/{s.Snapshot.EmployeeId}/edit"),ScreenStateStore.Question(s));
    private JsonResult Navigation(string url,CommitState commit=CommitState.NotStarted,string? message=null)=>Json(new{navigation=new{url,commitState=commit,messageId=message}});
    private static JsonResult Failure(Outcome outcome)=>new(new{outcome},HttpJson.Options){StatusCode=HttpJson.Status(outcome)};
}
