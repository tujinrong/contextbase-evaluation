using System.Collections.Concurrent;
using System.Security.Cryptography;
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
    public string TabId {get;}=Guid.NewGuid().ToString("N");
    public int Revision {get;set;}=1;
    public SemaphoreSlim Gate {get;}=new(1,1);
    public CommitState CommitState {get;set;}
}
public sealed class SearchState(string session):ScreenState(session)
{
    public SearchCriteria Criteria {get;set;}=new(null,null,null,"01");
    public SearchCriteria? Applied {get;set;}
    public List<SearchRow> Rows {get;set;}=[];
    public long? Selection {get;set;}
    public bool Valid {get;set;}
    public ResultStatus Status {get;set;}=ResultStatus.Unsearched;
    public Outcome? Outcome {get;set;}
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
    public string? AttemptedEmployeeNo {get;set;}
}
public sealed class CodeState(string session,string category):ScreenState(session)
{
    public string Category {get;set;}=category;
    public CodeRow? Snapshot {get;set;}
    public CodeSaveInput? Draft {get;set;}
    public bool IsNew {get;set;}
    public bool StopConfirmed {get;set;}
    public CodeDraft? StopConfirmationValues {get;set;}
    public Outcome? Outcome {get;set;}
    public bool CanSave {get;set;}=true;
}
public sealed class ScreenStateStore
{
    private readonly ConcurrentDictionary<string,ScreenState> states=new(StringComparer.Ordinal);
    public T Add<T>(T state) where T:ScreenState {states[state.Id]=state;return state;}
    public T Get<T>(string id,string session) where T:ScreenState
    {
        if(!states.TryGetValue(id,out var value)||value is not T typed) throw BusinessException.Error(8,"Conflict");
        if(value.OwnerSessionId!=session) throw BusinessException.Error(3,"Forbidden");return typed;
    }
    public static void Check(ScreenState state,int revision)
    {
        if(state.Revision!=revision) throw BusinessException.Error(8,"Conflict");
        if(state.Revision==int.MaxValue) throw BusinessException.Error(8,"Conflict");
    }
    public void Remove(string id)=>states.TryRemove(id,out _);
    public void RemoveSession(string session)
    {
        foreach(var pair in states) if(pair.Value.OwnerSessionId==session) states.TryRemove(pair.Key,out _);
    }
    public void RemoveSessionOfType<T>(string session)where T:ScreenState
    {foreach(var pair in states)if(pair.Value.OwnerSessionId==session&&pair.Value is T)states.TryRemove(pair.Key,out _);}
}
public sealed class ExportOperation(string session,string state,Guid id):IDisposable
{
    public string Session {get;}=session;public string State {get;}=state; public Guid Id {get;}=id;
    public object Gate {get;}=new();public string Phase {get;set;}="Reading";
    public CancellationTokenSource Cancellation {get;}=new();
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
    public void Finish(ExportOperation op)
    {
        lock(gate) {if(active.TryGetValue(op.State,out var current)&&ReferenceEquals(current,op))active.Remove(op.State);}
        lock(op.Gate)op.Phase="Finished";op.Dispose();
    }
}
