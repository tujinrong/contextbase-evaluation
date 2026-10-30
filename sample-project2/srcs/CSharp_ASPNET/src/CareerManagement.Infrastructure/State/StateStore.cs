using System.Collections.Concurrent;
using System.Security.Cryptography;
using System.Text.Json;
using CareerManagement.Application;

namespace CareerManagement.Infrastructure.State;

public sealed class SessionRegistry(BusinessClock clock)
{
    private sealed class Entry(string user, DateTimeOffset now) { public string User {get;}=user; public DateTimeOffset Last {get;set;}=now; public object Gate {get;}=new(); }
    private readonly ConcurrentDictionary<string,Entry> entries=new(StringComparer.Ordinal);
    public string Create(string user)
    {
        var id=Convert.ToHexStringLower(RandomNumberGenerator.GetBytes(32)); entries[id]=new(user,clock.UtcNow);return id;
    }
    public bool IsValid(string session,string user)
    {
        if(!entries.TryGetValue(session,out var value)) return false;
        lock(value.Gate)
        {
            if(value.User!=user||clock.UtcNow>=value.Last.AddMinutes(30)) {entries.TryRemove(session,out _);return false;}return true;
        }
    }
    public bool Touch(string session,string user)
    {
        if(!entries.TryGetValue(session,out var value)) return false;
        lock(value.Gate)
        {
            if(value.User!=user||clock.UtcNow>=value.Last.AddMinutes(30)) {entries.TryRemove(session,out _);return false;}
            value.Last=clock.UtcNow;return true;
        }
    }
    public void Remove(string session)=>entries.TryRemove(session,out _);
}
public abstract class ScreenState(string session)
{
    public string Id {get;}=Convert.ToHexStringLower(RandomNumberGenerator.GetBytes(32));
    public string OwnerSessionId {get;}=session;
    public string TabId {get;set;}=Guid.NewGuid().ToString("N");
    public string DocumentId {get;private set;}=Guid.NewGuid().ToString("N");
    public string DocumentLease {get;private set;}=Convert.ToHexStringLower(RandomNumberGenerator.GetBytes(32));
    public bool LeaseActive {get;set;}=true;
    public DateTimeOffset LastActivityUtc {get;set;}=DateTimeOffset.UtcNow;
    public string? ResumeRef {get;set;}
    public string? SourceTabId {get;set;}
    public bool ResumeAllowed {get;set;}=true;
    public LeaveConfirmation? LeaveConfirmation {get;set;}
    public int Revision {get;set;}=1;
    public SemaphoreSlim Gate {get;}=new(1,1);
    public CommitState CommitState {get;set;}
    public void NewDocument(){DocumentId=Guid.NewGuid().ToString("N");DocumentLease=Convert.ToHexStringLower(RandomNumberGenerator.GetBytes(32));LeaseActive=true;}
}
public sealed class NavigationState(string session):ScreenState(session);
public sealed record SearchReturnSnapshot(SearchRaw Raw,SearchCriteria? Applied,ResultStatus Status,bool Valid,
    long? Selection,double ScrollTop,string Session,string SourceTabId,Outcome? Outcome,DateTimeOffset Expires);
public sealed record LeaveConfirmation(Guid Id,int Revision,string Action,string Target,string Digest);
public sealed class SearchState(string session):ScreenState(session)
{
    public SearchRaw Raw {get;set;}=SearchRaw.Initial;
    public SearchCriteria? Applied {get;set;}
    public List<SearchRow> Rows {get;set;}=[];
    public long? Selection {get;set;}
    public bool Valid {get;set;}
    public ResultStatus Status {get;set;}=ResultStatus.Unsearched;
    public Outcome? Outcome {get;set;}
    public double ScrollTop {get;set;}
    public long ClientSequence {get;set;}
    public SearchReturnSnapshot Capture()=>new(Raw,Applied,Status,Valid,Selection,ScrollTop,OwnerSessionId,TabId,Outcome,LastActivityUtc.AddMinutes(30));
}
public sealed class EditState(string session,string searchId,EmployeeSnapshot? snapshot,EmployeeRaw raw):ScreenState(session)
{
    public string SearchId {get;}=searchId;
    public EmployeeSnapshot? Snapshot {get;set;}=snapshot;
    public EmployeeRaw Employee {get;set;}=raw;
    public List<CareerRaw> Careers {get;set;}=snapshot?.Careers.Select(x=>x.Raw()).ToList()??[];
    public HashSet<long> Removed {get;}=[];
    public CareerRaw? Pending {get;set;}
    public Guid? Selected {get;set;}
    public EditTab ActiveTab {get;set;}
    public ConfirmationVm? Confirmation {get;set;}
    public DraftInput? Deferred {get;set;}
    public Outcome? Outcome {get;set;}
    public bool Completed {get;set;}
    public bool OperationsBlocked {get;set;}
    public string? AttemptedEmployeeNo {get;set;}
    public SearchReturnSnapshot? ReturnSnapshot {get;set;}
    public EmployeeRaw CleanEmployee {get;set;}=raw;
    public CareerRaw[] CleanCareers {get;set;}=snapshot?.Careers.Select(x=>x.Raw()).ToArray()??[];
    public bool Dirty=>Employee!=CleanEmployee||!Careers.SequenceEqual(CleanCareers)||Removed.Count>0||
        Pending is not null&&(!Careers.Contains(Pending)||Selected!=Pending.ClientRowKey);
}
public sealed class CodeState(string session,string category):ScreenState(session)
{
    public string Category {get;set;}=category;
    public CodeRow? Snapshot {get;set;}
    public CodeSaveInput? Draft {get;set;}
    public bool IsNew {get;set;}
    public bool StopConfirmed {get;set;}
    public CodeDraft? StopConfirmationValues {get;set;}
    public Guid? StopConfirmationId {get;set;}
    public Outcome? Outcome {get;set;}
    public bool CanSave {get;set;}=true;
    public CodeSaveInput? CleanDraft {get;set;}
    public bool Dirty=>!Equals(Values(Draft),Values(CleanDraft));
    private static object? Values(CodeSaveInput? v)=>v is null?null:(v.Category,v.Code,v.Name,v.SortOrderRaw,v.Enabled);
}
public sealed class ScreenStateStore(BusinessClock? clock=null)
{
    private readonly ConcurrentDictionary<string,ScreenState> states=new(StringComparer.Ordinal);
    private readonly Dictionary<string,ResumeEntry> resumes=new(StringComparer.Ordinal);
    private readonly Dictionary<string,Ticket> tickets=new(StringComparer.Ordinal);
    private readonly Dictionary<string,(string Ticket,string Signature)> openOperations=new(StringComparer.Ordinal);
    private readonly object transientGate=new();
    private DateTimeOffset Now=>clock?.UtcNow??DateTimeOffset.UtcNow;
    private sealed record ResumeEntry(SearchReturnSnapshot Snapshot,DateTimeOffset Expires);
    private sealed record Ticket(string Session,string Tab,string SourceId,string SourceLease,string TargetId,string Route,
        DateTimeOffset Expires,CommitState Commit,string? MessageId){public bool Consumed {get;set;}}
    public T Add<T>(T state) where T:ScreenState
    {state.LastActivityUtc=Now;lock(transientGate)Sweep();states[state.Id]=state;return state;}
    public T Get<T>(string id,string session) where T:ScreenState
    {
        if(!states.TryGetValue(id,out var value)||value is not T typed) throw BusinessException.Error(41,"UiExpired");
        if(value.OwnerSessionId!=session) throw BusinessException.Error(3,"Forbidden");return typed;
    }
    public static void Check(ScreenState state,int revision)
    {
        if(state.Revision!=revision) throw BusinessException.Error(8,"Conflict");
        if(state.Revision==int.MaxValue) throw BusinessException.Error(8,"Conflict");
    }
    public void CheckUi(ScreenState state,int revision,string tab,string lease,bool recovery=false,bool background=false)
    {
        if(state.TabId!=tab)throw BusinessException.Error(3,"Forbidden");
        if(state.CommitState==CommitState.Unknown&&!recovery)throw new BusinessException(Outcome.Of(34,"ResultUnknown",CommitState.Unknown));
        if(state.DocumentLease!=lease||(!recovery&&(!state.LeaseActive||Now>=state.LastActivityUtc.AddMinutes(30))))
        {
            var expired=Outcome.Of(41,"UiExpired",state.CommitState);
            if(state.CommitState==CommitState.Committed)expired=expired with{Message=Messages.Get(14)+" "+Messages.Get(41)};
            throw new BusinessException(expired);
        }
        Check(state,revision);
        _=background;
    }
    public void Touch(ScreenState state)=>state.LastActivityUtc=Now;
    public UiStateInfo Info(ScreenState s,string route)=>new(s.Id,s.Revision,s.TabId,s.DocumentId,s.DocumentLease,s.ResumeRef,s.SourceTabId,route,
        s.LeaseActive&&Now<s.LastActivityUtc.AddMinutes(30)&&s.CommitState!=CommitState.Unknown&&!(s is EditState edit&&(edit.Completed||edit.OperationsBlocked)));
    public void Attach(ScreenState s,AttachInput input)
    {
        CheckUi(s,s.Revision,input.TabId,input.DocumentLease,background:true);
        if(s.DocumentId!=input.DocumentId)throw BusinessException.Error(41,"UiExpired");
    }
    public static void CaptureRaw(SearchState state,SearchRaw raw,long sequence,double scroll)
    {
        Validation.TechnicalRaw(raw);
        if(sequence<state.ClientSequence||!double.IsFinite(scroll)||scroll<0)throw BusinessException.Error(8,"Conflict");
        if(state.Raw!=raw)
        {
            state.Raw=raw;state.Valid=false;state.Rows=[];state.Selection=null;state.Status=ResultStatus.Unapplied;state.Outcome=null;
        }
        state.ClientSequence=sequence;state.ScrollTop=scroll;state.ResumeAllowed=false;
    }
    public string Checkpoint(SearchState s)
    {
        var id=Convert.ToHexStringLower(RandomNumberGenerator.GetBytes(32));
        lock(transientGate){Sweep();resumes[id]=new(s.Capture(),Now.AddMinutes(30));}
        s.ResumeRef=id;s.SourceTabId=s.TabId;return id;
    }
    public SearchReturnSnapshot CopyReturnReference(ScreenState target,SearchReturnSnapshot snapshot)
    {
        var copy=snapshot with{Session=target.OwnerSessionId,SourceTabId=target.TabId,Expires=target.LastActivityUtc.AddMinutes(30)};
        var id=Convert.ToHexStringLower(RandomNumberGenerator.GetBytes(32));
        lock(transientGate){Sweep();resumes[id]=new(copy,copy.Expires);}
        target.ResumeRef=id;target.SourceTabId=target.TabId;return copy;
    }
    public SearchReturnSnapshot ReadResume(string reference,string sourceTab,string session)
    {
        lock(transientGate)
        {
            if(!resumes.TryGetValue(reference,out var entry)||Now>=entry.Expires)throw BusinessException.Error(41,"UiExpired");
            if(entry.Snapshot.Session!=session||entry.Snapshot.SourceTabId!=sourceTab)throw BusinessException.Error(3,"Forbidden");
            return entry.Snapshot;
        }
    }
    public static void Restore(SearchState s,SearchReturnSnapshot snapshot)
    {
        s.Raw=snapshot.Raw;s.Applied=snapshot.Applied;s.Status=snapshot.Status;s.Valid=false;s.Rows=[];s.Selection=null;
        s.ScrollTop=snapshot.ScrollTop;s.Outcome=snapshot.Outcome;s.ResumeAllowed=false;
    }
    public static void CaptureUi(ScreenState state,RawUiEnvelope raw)
    {
        void Texts(object? value)
        {
            if(value is null)return;
            foreach(var p in value.GetType().GetProperties())if(p.PropertyType==typeof(string)&&p.GetValue(value) is string text)Validation.TechnicalRaw(text);
        }
        Texts(raw.Employee);Texts(raw.Pending);Texts(raw.Code);
        if(state is EditState edit)
        {
            if(raw.Employee is null)throw new ArgumentException("Employee raw required.");
            if(raw.SelectedClientRowKey!=edit.Selected||edit.Pending is not null&&raw.Pending is null)throw BusinessException.Error(25);
            if(raw.Pending is not null&&raw.Pending.ClientRowKey!=edit.Selected)throw BusinessException.Error(25);
            edit.Employee=raw.Employee;edit.Pending=raw.Pending;
            if(raw.ActiveTab is not null)edit.ActiveTab=raw.ActiveTab.Value;
        }
        else if(state is CodeState code)
        {
            if(code.Draft is not null&&raw.Code is null)throw BusinessException.Error(25);
            if(raw.Code is not null&&(raw.Code.Category!=code.Category||code.Snapshot is not null&&raw.Code.Code!=code.Snapshot.Code))throw BusinessException.Error(25);
            code.Draft=raw.Code;
        }
    }
    public static bool IsDirty(ScreenState state)=>state is EditState e?e.Dirty:state is CodeState c&&c.Dirty;
    private static string Digest(RawUiEnvelope raw)=>Convert.ToHexStringLower(SHA256.HashData(JsonSerializer.SerializeToUtf8Bytes(new{
        raw.Employee,raw.Pending,raw.ActiveTab,raw.SelectedClientRowKey,
        Code=raw.Code is null?null:new{raw.Code.Category,raw.Code.Code,raw.Code.Name,raw.Code.SortOrderRaw,raw.Code.Enabled}})));
    // null asks, false continues editing, true authorizes this exact one-time action.
    public bool? ConfirmLeave(ScreenState state,RawUiEnvelope raw,string action,string target,Guid? id,DiscardChoice? choice)
    {
        var digest=Digest(raw);
        if(id is not null)
        {
            var q=state.LeaveConfirmation;
            if(q is null||q.Id!=id||q.Revision!=state.Revision||q.Action!=action||q.Target!=target||q.Digest!=digest||choice is null)
                throw BusinessException.Error(8,"Conflict");
            state.LeaveConfirmation=null;return choice==DiscardChoice.Discard;
        }
        if(choice is not null)throw BusinessException.Error(25);
        if(!IsDirty(state)&&state.CommitState!=CommitState.Unknown)return true;
        state.Revision++;state.LeaveConfirmation=new(Guid.NewGuid(),state.Revision,action,target,digest);return null;
    }
    public static DiscardQuestion? Question(ScreenState s)=>s.LeaveConfirmation is null?null:new(s.LeaveConfirmation.Id,"MSG-015",Messages.Get(15));
    public string IssueTicket(ScreenState source,ScreenState target,string route,string? message=null,Guid? openOperation=null,string? openSignature=null)
    {
        if(source.CommitState==CommitState.Unknown)throw new BusinessException(Outcome.Of(34,"ResultUnknown",CommitState.Unknown));
        var id=Convert.ToHexStringLower(RandomNumberGenerator.GetBytes(32));target.TabId=source.TabId;
        lock(transientGate)
        {
            Sweep();tickets[id]=new(source.OwnerSessionId,source.TabId,source.Id,source.DocumentLease,target.Id,route,Now.AddSeconds(60),source.CommitState,message);
            if(openOperation is not null)openOperations[source.Id+":"+openOperation.Value.ToString("N")]=(id,openSignature??"");
        }
        return route+"?nav="+id;
    }
    public string? ExistingOpen(ScreenState source,Guid operation,string signature)
    {
        lock(transientGate)
        {
            if(!openOperations.TryGetValue(source.Id+":"+operation.ToString("N"),out var entry)||!tickets.TryGetValue(entry.Ticket,out var t))return null;
            if(entry.Signature!=signature)throw BusinessException.Error(8,"Conflict");
            if(t.Consumed||Now>=t.Expires)throw BusinessException.Error(41,"UiExpired");return t.Route+"?nav="+entry.Ticket;
        }
    }
    public T Consume<T>(string id,string session,string route)where T:ScreenState
    {
        lock(transientGate)
        {
            if(!tickets.TryGetValue(id,out var ticket))throw BusinessException.Error(41,"UiExpired");
            if(ticket.Session!=session)throw BusinessException.Error(3,"Forbidden");
            if(ticket.Route!=route||ticket.Consumed||Now>=ticket.Expires)
            {
                var o=Outcome.Of(41,"UiExpired",ticket.Commit);
                if(ticket.Commit==CommitState.Committed)o=o with{Message=Messages.Get(14)+" "+Messages.Get(41)};
                throw new BusinessException(o);
            }
            var state=Get<T>(ticket.TargetId,session);
            if(states.TryGetValue(ticket.SourceId,out var source)&&source.DocumentLease==ticket.SourceLease)source.LeaseActive=false;
            ticket.Consumed=true;state.TabId=ticket.Tab;state.NewDocument();state.LastActivityUtc=Now;return state;
        }
    }
    private void Sweep()
    {
        foreach(var pair in states)
        {
            var state=pair.Value;
            if(Now<state.LastActivityUtc.AddMinutes(30)||!state.Gate.Wait(0))continue;
            try{if(Now>=state.LastActivityUtc.AddMinutes(30))states.TryRemove(pair.Key,out _);}
            finally{state.Gate.Release();}
        }
        foreach(var key in resumes.Where(p=>Now>=p.Value.Expires).Select(p=>p.Key).ToArray())resumes.Remove(key);
        foreach(var key in tickets.Where(p=>Now>=p.Value.Expires.AddMinutes(30)).Select(p=>p.Key).ToArray())tickets.Remove(key);
        foreach(var key in openOperations.Where(p=>!tickets.ContainsKey(p.Value.Ticket)).Select(p=>p.Key).ToArray())openOperations.Remove(key);
    }
    public void Remove(string id)=>states.TryRemove(id,out _);
    public void RemoveSession(string session)
    {
        foreach(var pair in states) if(pair.Value.OwnerSessionId==session) states.TryRemove(pair.Key,out _);
        lock(transientGate)
        {
            foreach(var key in resumes.Where(p=>p.Value.Snapshot.Session==session).Select(p=>p.Key).ToArray())resumes.Remove(key);
            foreach(var key in tickets.Where(p=>p.Value.Session==session).Select(p=>p.Key).ToArray())tickets.Remove(key);
            Sweep();
        }
    }
    public void RemoveSessionOfType<T>(string session)where T:ScreenState
    {foreach(var pair in states)if(pair.Value.OwnerSessionId==session&&pair.Value is T)states.TryRemove(pair.Key,out _);}
}
public sealed class ExportOperation(string session,string state,Guid id):IDisposable
{
    public string Session {get;}=session;public string State {get;}=state; public Guid Id {get;}=id;
    public object Gate {get;}=new();public string Phase {get;set;}="Reading";
    public CancellationTokenSource Cancellation {get;}=new();
    public TaskCompletionSource Finished {get;}=new(TaskCreationOptions.RunContinuationsAsynchronously);
    public void Dispose()=>Cancellation.Dispose();
}
public sealed class ExportOperationRegistry
{
    private readonly object gate=new();
    private readonly Dictionary<string,ExportOperation> active=new(StringComparer.Ordinal);
    public ExportOperation Start(string session,string state,Guid id)
    {
        if(id==Guid.Empty) throw BusinessException.Error(25);
        lock(gate)
        {
            if(active.ContainsKey(state)) throw BusinessException.Error(29,"Busy");
            var operation=new ExportOperation(session,state,id);active.Add(state,operation);return operation;
        }
    }
    public CancelResult Cancel(string session,string state,Guid id)
    {
        ExportOperation? op;
        lock(gate) active.TryGetValue(state,out op);
        if(op is null) return new("AlreadyFinished","MSG-036",Messages.Get(36));
        if(op.Session!=session||op.Id!=id) throw BusinessException.Error(3,"Forbidden");
        lock(op.Gate)
        {
            if(op.Phase=="Finished")return new("AlreadyFinished","MSG-036",Messages.Get(36));
            op.Cancellation.Cancel();var before=op.Phase is "Reading" or "Generating" or "Ready";
            return new(before?"CancelledBeforeStart":"AfterStart",before?"MSG-030":"MSG-036",Messages.Get(before?30:36));
        }
    }
    public async Task<CancelResult> CancelAsync(string session,string state,Guid id,CancellationToken ct)
    {
        ExportOperation? operation;lock(gate)active.TryGetValue(state,out operation);
        var result=Cancel(session,state,id);
        if(operation is not null)await operation.Finished.Task.WaitAsync(TimeSpan.FromSeconds(30),ct);
        return result;
    }
    public void Finish(ExportOperation op)
    {
        lock(gate) {if(active.TryGetValue(op.State,out var current)&&ReferenceEquals(current,op))active.Remove(op.State);}
        lock(op.Gate)op.Phase="Finished";op.Dispose();op.Finished.TrySetResult();
    }
}
