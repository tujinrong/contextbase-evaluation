using CareerManagement.Application;
using CareerManagement.Infrastructure.Authentication;

namespace CareerManagement.Infrastructure.Sql;
public sealed class CodeService(Database database,Repository repository,CurrentUserService current,BusinessClock clock)
{
    public async Task<IReadOnlyList<CodeRow>> ReadAsync(Actor actor,string category,CancellationToken ct)
    {
        Validation.Category(category);database.Faults.BeforeRead();
        await using var unit=await database.BeginAsync(false,ct);await current.RequireInAsync(unit,actor,true,ct);
        await repository.ValidateCategoriesAsync(unit,ct);var codes=await repository.CodesAsync(unit,ct);await unit.CommitAsync(ct);
        return codes.Where(x=>x.Category==category).OrderBy(x=>x.SortOrder).ThenBy(x=>x.Code,StringComparer.Ordinal).ToArray();
    }
    public async Task<Outcome> SaveAsync(Actor actor,CodeRow? snapshot,CodeSaveInput raw,bool stopConfirmed,CancellationToken ct)
    {
        var draft=Validation.CodeInput(raw);
        if(snapshot is not null&&(snapshot.Category!=draft.Category||snapshot.Code!=draft.Code||raw.ExpectedRevision!=snapshot.Revision))throw BusinessException.Error(8,"Conflict");
        if(snapshot is null&&raw.ExpectedRevision.HasValue)throw BusinessException.Error(8,"Conflict");
        if(snapshot is not null&&snapshot.Enabled&&!draft.Enabled&&!stopConfirmed)throw BusinessException.Error(38,"Confirmation");
        try
        {
            await using var unit=await database.BeginAsync(true,ct);await current.RequireInAsync(unit,actor,true,ct);
            await repository.ValidateCategoriesAsync(unit,ct);var codes=await repository.CodesAsync(unit,ct);
            var saved=codes.SingleOrDefault(x=>x.Category==draft.Category&&x.Code==draft.Code);
            if(snapshot is null)
            {
                if(saved is not null)throw BusinessException.Error(22);
                if(codes.Count(x=>x.Category==draft.Category)>=99)throw BusinessException.Error(24);
            }
            else
            {
                if(saved is null)throw BusinessException.Error(16,"NotFound");
                if(saved.Revision!=snapshot.Revision)throw BusinessException.Error(8,"Conflict");
                if(saved.Name==draft.Name&&saved.SortOrder==draft.SortOrder&&saved.Enabled==draft.Enabled)return Outcome.Of(21,"NoChange");
                if(saved.Revision==int.MaxValue)throw BusinessException.Error(39);
            }
            await repository.WriteCodeAsync(unit,draft,snapshot?.Revision,actor.UserId,clock.UtcNow,ct);
            await unit.CommitAsync(ct);return Outcome.Ok();
        }
        catch(Exception ex) when(ex is not BusinessException){throw new BusinessException(SqlErrors.Map(ex));}
    }
}
