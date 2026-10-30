using CareerManagement.Application;
using CareerManagement.Infrastructure.Authentication;

namespace CareerManagement.Infrastructure.Sql;

public sealed class EmployeeService(Database database,Repository repository,CurrentUserService current,BusinessClock clock)
{
    public async Task RequireNewCapacityAsync(Actor actor,CancellationToken ct)
    {
        await using var unit=await database.BeginAsync(false,ct);await current.RequireInAsync(unit,actor,false,ct);
        if(await repository.EmployeeCountAsync(unit,ct)>=200)throw BusinessException.Error(18);
        await unit.CommitAsync(ct);
    }
    public async Task<(IReadOnlyList<SearchRow> Rows,IReadOnlyList<CodeRow> Codes)> SearchAsync(Actor actor,SearchCriteria criteria,CancellationToken ct)
    {
        database.Faults.BeforeRead();
        await using var unit=await database.BeginAsync(false,ct);await current.RequireInAsync(unit,actor,false,ct);
        await repository.ValidateCategoriesAsync(unit,ct);var codes=await repository.CodesAsync(unit,ct);
        if(criteria.Department is not null&&!codes.Any(x=>x.Category=="DEPARTMENT"&&x.Code==criteria.Department))throw BusinessException.Error(16);
        var rows=await repository.SearchAsync(unit,criteria,ct);await unit.CommitAsync(ct);return(rows,codes);
    }
    public async Task<IReadOnlyList<CodeRow>> CodesAsync(Actor actor,CancellationToken ct)
    {
        await using var unit=await database.BeginAsync(false,ct);await current.RequireInAsync(unit,actor,false,ct);
        await repository.ValidateCategoriesAsync(unit,ct);var rows=await repository.CodesAsync(unit,ct);await unit.CommitAsync(ct);return rows;
    }
    public async Task<(EmployeeSnapshot Snapshot,IReadOnlyList<CodeRow> Codes)> ReadAsync(Actor actor,long id,CancellationToken ct)
    {
        database.Faults.BeforeRead();var instant=clock.Begin();
        await using var unit=await database.BeginAsync(false,ct);await current.RequireInAsync(unit,actor,false,ct);
        await repository.ValidateCategoriesAsync(unit,ct);var codes=await repository.CodesAsync(unit,ct);
        var saved=await repository.EmployeeAsync(unit,id,ct)??throw BusinessException.Error(19,"NotFound");
        ValidateStructure(saved,codes);await unit.CommitAsync(ct);return(saved,codes);
    }
    public async Task<ReportSnapshot> ReportAsync(Actor actor,long id,CancellationToken ct)
    {
        database.Faults.BeforeRead();
        await using var unit=await database.BeginAsync(false,ct);await current.RequireInAsync(unit,actor,false,ct);
        var instant=clock.Begin(); // Fixed only after the consistent read gate is established.
        await repository.ValidateCategoriesAsync(unit,ct);var codes=await repository.CodesAsync(unit,ct);
        var saved=await repository.EmployeeAsync(unit,id,ct)??throw BusinessException.Error(19,"NotFound");
        ValidateStored(saved,codes,instant);if(saved.Careers.Count==0)throw BusinessException.Error(12);
        await unit.CommitAsync(ct);return new(instant,saved,codes.ToArray());
    }
    public async Task<SaveResult> SaveAsync(Actor actor,EmployeeSnapshot? snapshot,EmployeeRaw raw,CareerRaw[] rawCareers,long[] removed,CancellationToken ct)
    {
        var instant=clock.Begin();var draft=Validation.Employee(raw,instant.Date);var careers=Validation.Careers(rawCareers,instant.Month);
        Validation.ChildSet(snapshot,careers,removed);
        try
        {
            await using var unit=await database.BeginAsync(true,ct);await current.RequireInAsync(unit,actor,false,ct);
            EmployeeSnapshot? saved=null;long id;int revision;
            if(snapshot is not null)
            {
                saved=await repository.EmployeeAsync(unit,snapshot.EmployeeId,ct)??throw BusinessException.Error(19,"NotFound");
                // Version is checked before no-change and before restoring any stale input.
                if(saved.Revision!=snapshot.Revision)throw BusinessException.Error(8,"Conflict");
                if(draft.EmployeeNo!=snapshot.Employee.EmployeeNo)throw Validation.Field(5,"F04-I01","社員番号（編集不可）");
                if(!saved.Careers.Select(x=>x.CareerId).ToHashSet().SetEquals(snapshot.Careers.Select(x=>x.CareerId)))throw BusinessException.Error(20,"Corrupt");
                id=saved.EmployeeId;revision=saved.Revision;
            }
            else
            {
                if(await repository.EmployeeIdAsync(unit,draft.EmployeeNo,ct)is not null)throw BusinessException.Error(6);
                if(await repository.EmployeeCountAsync(unit,ct)>=200)throw BusinessException.Error(18);
                id=0;revision=1;
            }
            var codes=await repository.CodesAsync(unit,ct);await repository.ValidateCategoriesAsync(unit,ct);
            if(saved is not null)ValidateStructure(saved,codes);
            Validation.Reference(codes,"DEPARTMENT",draft.DepartmentCode,saved?.Employee.DepartmentCode);
            Validation.Reference(codes,"EMPLOYMENT_STATUS",draft.EmploymentStatus,saved?.Employee.EmploymentStatus);
            foreach(var career in careers)
            {
                var original=saved?.Careers.SingleOrDefault(x=>x.CareerId==career.CareerId&&career.CareerId.HasValue);
                Validation.Reference(codes,"PROJECT_ROLE",career.Values.RoleCode,original?.Values.RoleCode);
            }
            if(saved is not null&&saved.Employee==draft&&removed.Length==0&&careers.Count()==saved.Careers.Count&&careers.All(x=>x.CareerId.HasValue&&saved.Careers.Any(y=>y.CareerId==x.CareerId&&y.Values==x.Values)))
                return new(id,draft.EmployeeNo,revision,Outcome.Of(21,"NoChange"));
            if(saved?.Revision==int.MaxValue)throw BusinessException.Error(39);
            var now=clock.UtcNow;
            if(saved is null)id=await repository.InsertEmployeeAsync(unit,draft,actor.UserId,now,ct);
            else {await repository.UpdateEmployeeAsync(unit,id,revision,draft,actor.UserId,now,ct);revision++;}
            foreach(var childId in removed.Order()) {database.Faults.BeforeChildWrite();await repository.DeleteCareerAsync(unit,id,childId,ct);}
            foreach(var child in careers.OrderBy(x=>x.CareerId??long.MaxValue))
            {
                if(child.CareerId.HasValue)
                {
                    var old=saved!.Careers.Single(x=>x.CareerId==child.CareerId);
                    if(child.Values!=old.Values) {database.Faults.BeforeChildWrite();await repository.UpdateCareerAsync(unit,id,child.CareerId.Value,child.Values,ct);}
                }
                else {database.Faults.BeforeChildWrite();await repository.InsertCareerAsync(unit,id,child.Values,ct);}
            }
            await unit.CommitAsync(ct);return new(id,draft.EmployeeNo,revision,Outcome.Ok());
        }
        catch(Exception ex) when(ex is not BusinessException)
        {throw new BusinessException(SqlErrors.Map(ex));}
    }
    public static void ValidateStored(EmployeeSnapshot snapshot,IReadOnlyList<CodeRow> codes,BusinessInstant instant)
    {
        try
        {
            if(snapshot.EmployeeId<=0||snapshot.Revision<1||Validation.Employee(snapshot.Employee.Raw(),instant.Date)!=snapshot.Employee)throw BusinessException.Error(20);
            var seen=new HashSet<CareerValues>();
            if(snapshot.Careers.Count>20)throw BusinessException.Error(20);
            foreach(var career in snapshot.Careers)
            {
                if(career.CareerId is not >0||career.Values.StartMonth.Day!=1||career.Values.EndMonth?.Day is not (null or 1)||!seen.Add(career.Values)||Validation.Career(career.Raw(),instant.Month,1).Values!=career.Values)throw BusinessException.Error(20);
                if(codes.Count(x=>x.Category=="PROJECT_ROLE"&&x.Code==career.Values.RoleCode)!=1)throw BusinessException.Error(20);
            }
            if(codes.Count(x=>x.Category=="DEPARTMENT"&&x.Code==snapshot.Employee.DepartmentCode)!=1||codes.Count(x=>x.Category=="EMPLOYMENT_STATUS"&&x.Code==snapshot.Employee.EmploymentStatus)!=1)throw BusinessException.Error(20);
        }
        catch(BusinessException){throw BusinessException.Error(20,"Corrupt");}
    }
    public static void ValidateStructure(EmployeeSnapshot snapshot,IReadOnlyList<CodeRow> codes)
    {
        // F04 permits correction of existing missing/invalid business values, while refusing structural corruption.
        if(snapshot.EmployeeId<=0||snapshot.Revision<1||snapshot.Careers.Count>20||snapshot.Careers.Any(x=>x.CareerId is not >0)||snapshot.Careers.Select(x=>x.CareerId).Distinct().Count()!=snapshot.Careers.Count)throw BusinessException.Error(20,"Corrupt");
        if(codes.Count(x=>x.Category=="DEPARTMENT"&&x.Code==snapshot.Employee.DepartmentCode)!=1||codes.Count(x=>x.Category=="EMPLOYMENT_STATUS"&&x.Code==snapshot.Employee.EmploymentStatus)!=1||snapshot.Careers.Any(c=>codes.Count(x=>x.Category=="PROJECT_ROLE"&&x.Code==c.Values.RoleCode)!=1))throw BusinessException.Error(20,"Corrupt");
    }
}
