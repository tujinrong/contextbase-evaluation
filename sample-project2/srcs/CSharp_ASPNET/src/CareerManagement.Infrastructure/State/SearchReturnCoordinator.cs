using CareerManagement.Application;
using CareerManagement.Infrastructure.Sql;

namespace CareerManagement.Infrastructure.State;

// Only immutable search values cross documents; mutable employee drafts never do.
public sealed class SearchReturnCoordinator(ScreenStateStore states,EmployeeService employees,BusinessClock clock)
{
    public SearchReturnSnapshot Initial(Actor actor,string tab)=>new(SearchRaw.Initial,null,ResultStatus.Unsearched,false,null,0,
        actor.SessionId,tab,null,clock.UtcNow.AddMinutes(30));
    public async Task<SearchState> ReturnAsync(Actor actor,SearchReturnSnapshot? snapshot,long? saved,Outcome? completed,CancellationToken ct)
    {
        var state=states.Add(new SearchState(actor.SessionId));
        await RestoreAsync(actor,state,snapshot,saved,completed,ct);return state;
    }
    public async Task RestoreAsync(Actor actor,SearchState state,SearchReturnSnapshot? snapshot,long? saved,Outcome? completed,CancellationToken ct)
    {
        if(snapshot is null||snapshot.Session!=actor.SessionId||clock.UtcNow>=snapshot.Expires)
        {
            state.Raw=SearchRaw.Initial;state.Status=ResultStatus.Unsearched;state.Outcome=Outcome.Of(41,"UiExpired");
            if(completed?.CommitState==CommitState.Committed)state.Outcome=completed with{Message=Messages.Get(14)+" "+Messages.Get(41)};
            states.Checkpoint(state);return;
        }
        ScreenStateStore.Restore(state,snapshot);
        if(snapshot.Status==ResultStatus.Success&&snapshot.Valid&&snapshot.Applied is not null)
        {
            try
            {
                var result=await employees.SearchAsync(actor,snapshot.Applied,ct);
                state.Rows=result.Rows.ToList();state.Status=ResultStatus.Success;state.Valid=true;
                var selection=saved??snapshot.Selection;
                state.Selection=state.Rows.Any(x=>x.EmployeeId==selection)?selection:null;
                state.Outcome=completed??(state.Rows.Count==0?Outcome.Of(9,"Success"):null);
            }
            catch(Exception e)
            {
                state.Rows=[];state.Valid=false;state.Selection=null;var failure=SqlErrors.Map(e,40);
                if(failure.Kind is "Expired" or "Forbidden")throw;
                state.Status=failure.MessageId=="MSG-010"?ResultStatus.LimitExceeded:ResultStatus.Failed;
                state.Outcome=completed?.CommitState==CommitState.Committed?completed with{Message=Messages.Get(14)+" "+failure.Message}:failure;
            }
        }
        else if(completed is not null)state.Outcome=completed;
        states.Checkpoint(state);
    }
}
