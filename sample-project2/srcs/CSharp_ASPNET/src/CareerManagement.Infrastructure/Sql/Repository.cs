using CareerManagement.Application;
using Microsoft.Data.SqlClient;

namespace CareerManagement.Infrastructure.Sql;

public sealed class Repository
{
    private const string UserColumns="user_id,login_id,display_name,password_verifier,role_id,is_enabled,failed_count,locked_until";
    public async Task<AppUser?> UserAsync(DbUnit db,string key,bool byLogin,CancellationToken ct)
    {
        await using var cmd=db.Command(byLogin?"SELECT "+UserColumns+" FROM dbo.m_app_user WHERE login_id=@key;":"SELECT "+UserColumns+" FROM dbo.m_app_user WHERE user_id=@key;",byLogin?P.V("@key",20,key):P.N("@key",40,key));
        await using var r=await cmd.ExecuteReaderAsync(ct);
        if(!await r.ReadAsync(ct))return null;
        if(!Enum.TryParse<UserRole>(r.GetString(4),false,out var role)||!Enum.IsDefined(role))throw BusinessException.Error(20,"Corrupt");
        var result=new AppUser(r.GetString(0),r.GetString(1),r.GetString(2),r.GetString(3),role,r.GetBoolean(5),r.GetByte(6),r.IsDBNull(7)?null:Utc(r.GetDateTime(7)));
        if(await r.ReadAsync(ct)||result.FailedCount>5||(result.FailedCount==5)!=(result.LockedUntil is not null)||Validation.ScalarLength(result.PasswordVerifier)>1024)throw BusinessException.Error(20,"Corrupt");
        return result;
    }
    public async Task UpdateAuthAsync(DbUnit db,string id,byte count,DateTimeOffset? until,CancellationToken ct)
    {
        await using var cmd=db.Command("UPDATE dbo.m_app_user SET failed_count=@count,locked_until=@until WHERE user_id=@id;",P.N("@id",40,id),P.Tiny("@count",count),P.Utc("@until",until));
        One(await cmd.ExecuteNonQueryAsync(ct));
    }
    public async Task<List<CodeRow>> CodesAsync(DbUnit db,CancellationToken ct)
    {
        await using var cmd=db.Command("SELECT category_id,code,code_name,sort_order,is_enabled,revision FROM dbo.m_code ORDER BY category_id,sort_order,code;");
        await using var r=await cmd.ExecuteReaderAsync(ct);var result=new List<CodeRow>();
        while(await r.ReadAsync(ct)) result.Add(new(r.GetString(0),r.GetString(1),r.GetString(2),r.GetInt16(3),r.GetBoolean(4),r.GetInt32(5)));
        Validation.FixedCodes(result);return result;
    }
    public async Task ValidateCategoriesAsync(DbUnit db,CancellationToken ct)
    {
        await using var cmd=db.Command("SELECT category_id,category_name FROM dbo.m_code_category ORDER BY category_id;");
        await using var r=await cmd.ExecuteReaderAsync(ct);var rows=new List<(string,string)>();
        while(await r.ReadAsync(ct))rows.Add((r.GetString(0),r.GetString(1)));
        if(!rows.SequenceEqual(new[]{("DEPARTMENT","部署"),("EMPLOYMENT_STATUS","在籍区分"),("PROJECT_ROLE","案件役割")}))throw BusinessException.Error(20,"Corrupt");
    }
    public async Task<List<SearchRow>> SearchAsync(DbUnit db,SearchCriteria criteria,CancellationToken ct)
    {
        const string sql="""
SELECT e.employee_id,e.employee_no,e.employee_name,e.employee_kana,e.department_category,e.employment_category,e.join_date,d.code_name,s.code_name
FROM dbo.m_employee e LEFT JOIN dbo.m_code d ON d.category_id=e.department_category AND d.code=e.department_code
LEFT JOIN dbo.m_code s ON s.category_id=e.employment_category AND s.code=e.employment_status
WHERE (@no IS NULL OR e.employee_no=@no) AND (@dep IS NULL OR e.department_code=@dep) AND (@status IS NULL OR e.employment_status=@status)
ORDER BY e.employee_no;
""";
        await using var cmd=db.Command(sql,P.C("@no",6,criteria.EmployeeNo),P.C("@dep",2,criteria.Department),P.C("@status",2,criteria.EmploymentStatus));
        await using var r=await cmd.ExecuteReaderAsync(ct);var rows=new List<SearchRow>();var key=Validation.SearchKey(criteria.Name);
        while(await r.ReadAsync(ct))
        {
            if(r.GetString(4)!="DEPARTMENT"||r.GetString(5)!="EMPLOYMENT_STATUS"||r.IsDBNull(7)||r.IsDBNull(8)||r.GetInt64(0)<=0)throw BusinessException.Error(20,"Corrupt");
            var name=r.GetString(2);var kana=r.GetString(3);
            if(key.Length!=0&&!Validation.SearchKey(name).Contains(key,StringComparison.Ordinal)&&!Validation.SearchKey(kana).Contains(key,StringComparison.Ordinal))continue;
            rows.Add(new(r.GetInt64(0),r.GetString(1),name,kana,r.GetString(7),r.GetString(8),DateOnly.FromDateTime(r.GetDateTime(6))));
            if(rows.Count>200)throw BusinessException.Error(10);
        }
        return rows;
    }
    public async Task<EmployeeSnapshot?> EmployeeAsync(DbUnit db,long id,CancellationToken ct)
    {
        const string sql="""
SELECT employee_id,employee_no,employee_name,employee_kana,department_category,department_code,employment_category,employment_status,
join_date,career_summary,skills,qualifications,self_pr,updated_at,updated_by,revision FROM dbo.m_employee WHERE employee_id=@id;
SELECT career_id,employee_id,start_month,end_month,company_name,project_name,description,duties,achievements,technologies,role_category,role_code,team_size,phases
FROM dbo.t_career WHERE employee_id=@id ORDER BY start_month DESC,career_id DESC;
""";
        await using var cmd=db.Command(sql,P.L("@id",id));await using var r=await cmd.ExecuteReaderAsync(ct);
        if(!await r.ReadAsync(ct))return null;
        if(r.GetString(4)!="DEPARTMENT"||r.GetString(6)!="EMPLOYMENT_STATUS"||r.GetInt32(15)<1)throw BusinessException.Error(20,"Corrupt");
        var employee=new EmployeeDraft(r.GetString(1),r.GetString(2),r.GetString(3),r.GetString(5),r.GetString(7),DateOnly.FromDateTime(r.GetDateTime(8)),N(r,9),N(r,10),N(r,11),N(r,12));
        var revision=r.GetInt32(15);var utc=Utc(r.GetDateTime(13));var actor=r.GetString(14);
        if(await r.ReadAsync(ct))throw BusinessException.Error(20,"Corrupt");
        await r.NextResultAsync(ct);var careers=new List<CareerDraft>();
        while(await r.ReadAsync(ct))
        {
            if(r.GetInt64(1)!=id||r.GetString(10)!="PROJECT_ROLE"||r.GetInt64(0)<=0)throw BusinessException.Error(20,"Corrupt");
            careers.Add(new(r.GetInt64(0),Guid.NewGuid(),new(DateOnly.FromDateTime(r.GetDateTime(2)),r.IsDBNull(3)?null:DateOnly.FromDateTime(r.GetDateTime(3)),r.GetString(4),r.GetString(5),r.GetString(6),r.GetString(7),N(r,8),N(r,9),N(r,13),r.GetString(11),r.GetInt16(12))));
        }
        if(careers.Count>20||careers.Select(x=>x.CareerId).Distinct().Count()!=careers.Count)throw BusinessException.Error(20,"Corrupt");
        return new(id,revision,employee,careers,utc,actor);
    }
    public async Task<long?> EmployeeIdAsync(DbUnit db,string number,CancellationToken ct)
    { await using var cmd=db.Command("SELECT employee_id FROM dbo.m_employee WHERE employee_no=@no;",P.C("@no",6,number));var value=await cmd.ExecuteScalarAsync(ct);return value is null?null:Convert.ToInt64(value,System.Globalization.CultureInfo.InvariantCulture); }
    public async Task<int> EmployeeCountAsync(DbUnit db,CancellationToken ct)
    { await using var cmd=db.Command("SELECT COUNT(*) FROM dbo.m_employee;");return (int)(await cmd.ExecuteScalarAsync(ct))!; }
    public async Task<long> InsertEmployeeAsync(DbUnit db,EmployeeDraft v,string actor,DateTimeOffset now,CancellationToken ct)
    {
        const string sql="""
INSERT dbo.m_employee(employee_no,employee_name,employee_kana,department_category,department_code,employment_category,employment_status,join_date,career_summary,skills,qualifications,self_pr,updated_at,updated_by,revision)
OUTPUT INSERTED.employee_id VALUES(@no,@name,@kana,'DEPARTMENT',@dep,'EMPLOYMENT_STATUS',@status,@join,@summary,@skills,@qual,@pr,@utc,@actor,1);
""";
        await using var cmd=db.Command(sql,EmployeeParameters(v,actor,now));return (long)(await cmd.ExecuteScalarAsync(ct))!;
    }
    public async Task UpdateEmployeeAsync(DbUnit db,long id,int revision,EmployeeDraft v,string actor,DateTimeOffset now,CancellationToken ct)
    {
        const string sql="""
UPDATE dbo.m_employee SET employee_name=@name,employee_kana=@kana,department_code=@dep,employment_status=@status,join_date=@join,career_summary=@summary,skills=@skills,qualifications=@qual,self_pr=@pr,updated_at=@utc,updated_by=@actor,revision=revision+1
WHERE employee_id=@id AND revision=@expected AND revision<2147483647;
""";
        await using var cmd=db.Command(sql,[..EmployeeParameters(v,actor,now),P.L("@id",id),P.I("@expected",revision)]);One(await cmd.ExecuteNonQueryAsync(ct));
    }
    public async Task DeleteCareerAsync(DbUnit db,long parent,long id,CancellationToken ct)
    {await using var cmd=db.Command("DELETE dbo.t_career WHERE employee_id=@parent AND career_id=@id;",P.L("@parent",parent),P.L("@id",id));One(await cmd.ExecuteNonQueryAsync(ct));}
    public async Task<long> InsertCareerAsync(DbUnit db,long parent,CareerValues v,CancellationToken ct)
    {
        const string sql="""
INSERT dbo.t_career(employee_id,start_month,end_month,company_name,project_name,description,duties,achievements,technologies,role_category,role_code,team_size,phases)
OUTPUT INSERTED.career_id VALUES(@parent,@start,@end,@company,@project,@description,@duties,@achievements,@tech,'PROJECT_ROLE',@role,@team,@phases);
""";
        await using var cmd=db.Command(sql,[P.L("@parent",parent),..CareerParameters(v)]);return (long)(await cmd.ExecuteScalarAsync(ct))!;
    }
    public async Task UpdateCareerAsync(DbUnit db,long parent,long id,CareerValues v,CancellationToken ct)
    {
        const string sql="""
UPDATE dbo.t_career SET start_month=@start,end_month=@end,company_name=@company,project_name=@project,description=@description,duties=@duties,achievements=@achievements,technologies=@tech,role_code=@role,team_size=@team,phases=@phases WHERE employee_id=@parent AND career_id=@id;
""";
        await using var cmd=db.Command(sql,[P.L("@parent",parent),P.L("@id",id),..CareerParameters(v)]);One(await cmd.ExecuteNonQueryAsync(ct));
    }
    public async Task WriteCodeAsync(DbUnit db,CodeDraft v,int? expected,string actor,DateTimeOffset now,CancellationToken ct)
    {
        var sql=expected.HasValue?"UPDATE dbo.m_code SET code_name=@name,sort_order=@sort,is_enabled=@enabled,updated_at=@utc,updated_by=@actor,revision=revision+1 WHERE category_id=@category AND code=@code AND revision=@expected AND revision<2147483647;":
            "INSERT dbo.m_code(category_id,code,code_name,sort_order,is_enabled,updated_at,updated_by,revision) VALUES(@category,@code,@name,@sort,@enabled,@utc,@actor,1);";
        await using var cmd=db.Command(sql,P.V("@category",24,v.Category),P.C("@code",2,v.Code),P.N("@name",80,v.Name),P.S("@sort",v.SortOrder),P.B("@enabled",v.Enabled),P.Utc("@utc",now),P.N("@actor",40,actor),P.I("@expected",expected??1));One(await cmd.ExecuteNonQueryAsync(ct));
    }
    private static SqlParameter[] EmployeeParameters(EmployeeDraft v,string actor,DateTimeOffset now)=>[P.C("@no",6,v.EmployeeNo),P.N("@name",80,v.Name),P.N("@kana",160,v.Kana),P.C("@dep",2,v.DepartmentCode),P.C("@status",2,v.EmploymentStatus),P.Date("@join",v.JoinDate),P.N("@summary",2000,v.CareerSummary),P.N("@skills",2000,v.Skills),P.N("@qual",2000,v.Qualifications),P.N("@pr",2000,v.SelfPr),P.Utc("@utc",now),P.N("@actor",40,actor)];
    private static SqlParameter[] CareerParameters(CareerValues v)=>[P.Date("@start",v.StartMonth),P.Date("@end",v.EndMonth),P.N("@company",200,v.CompanyName),P.N("@project",200,v.ProjectName),P.N("@description",2000,v.Description),P.N("@duties",2000,v.Duties),P.N("@achievements",2000,v.Achievements),P.N("@tech",1000,v.Technologies),P.N("@phases",400,v.Phases),P.C("@role",2,v.RoleCode),P.S("@team",v.TeamSize)];
    private static string? N(SqlDataReader r,int i)=>r.IsDBNull(i)?null:r.GetString(i);
    private static DateTimeOffset Utc(DateTime value)=>new(DateTime.SpecifyKind(value,DateTimeKind.Utc));
    private static void One(int count){if(count!=1)throw BusinessException.Error(20,"Corrupt");}
}
