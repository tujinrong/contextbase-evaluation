using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using CareerManagement.Application;
using CareerManagement.Infrastructure.Authentication;
using Microsoft.AspNetCore.Identity;
using Microsoft.Data.SqlClient;

namespace CareerManagement.Infrastructure.Sql;

public sealed record SeedCareer(string EmployeeNo,string Start,string? End,string Company,string Project,string Description,string Duties,string? Achievements,string? Technologies,string Role,short Team,string? Phases);
public sealed record SeedDefinition(string DatasetId,string Version,string BasisDate,bool Fictional,string[][] Categories,string[][] Codes,string[][] Users,EmployeeRaw[] Employees,SeedCareer[] Careers);
public sealed record SeedManifest(string ProjectId,string MethodId,string DatasetId,string Version,string BasisDate,string Database,string Owner,string ContentSha256,DateTimeOffset AppliedUtc,Dictionary<string,int> Counts,string State);
public static class SafeInitializer
{
    public const string Owner="sample-project2/CSharp_ASPNET/SP2-DEMO-01";
    public static readonly JsonSerializerOptions Json=new(JsonSerializerDefaults.Web){WriteIndented=true};
    public static async Task CreateAsync(DatabaseOptions options,string schema,CancellationToken ct)
    {
        options.Validate();var b=new SqlConnectionStringBuilder(options.ConnectionString){InitialCatalog="master"};
        await using var connection=new SqlConnection(b.ConnectionString);await connection.OpenAsync(ct);
        await using(var exists=new SqlCommand("SELECT DB_ID(@name);",connection))
        {
            exists.Parameters.Add(P.N("@name",128,options.AllowedDatabase));
            if(await exists.ExecuteScalarAsync(ct)is not DBNull)throw new InvalidOperationException("Database already exists; creation/initialization refused.");
        }
        // Identifier is from the exact allowlist validated above, never from a UI field.
        var identifier="["+options.AllowedDatabase.Replace("]","]]",StringComparison.Ordinal)+"]";
        await using(var create=new SqlCommand("CREATE DATABASE "+identifier+" COLLATE Latin1_General_100_BIN2;",connection))await create.ExecuteNonQueryAsync(ct);
        await using(var compatibility=new SqlCommand("ALTER DATABASE "+identifier+" SET COMPATIBILITY_LEVEL=160;",connection))await compatibility.ExecuteNonQueryAsync(ct);
        await using var target=new SqlConnection(options.ConnectionString);await target.OpenAsync(ct);
        await using var tx=(SqlTransaction)await target.BeginTransactionAsync(ct);
        await using(var mark=new SqlCommand("EXEC sys.sp_addextendedproperty @name=N'SP2Owner',@value=@owner;",target,tx))
        {mark.Parameters.Add(P.N("@owner",200,Owner));await mark.ExecuteNonQueryAsync(ct);}
        await using(var ddl=new SqlCommand(schema,target,tx){CommandTimeout=60})await ddl.ExecuteNonQueryAsync(ct);
        await tx.CommitAsync(ct);
    }
    public static async Task RequireOwnerAsync(DbUnit db,CancellationToken ct)
    {
        await using var command=db.Command("SELECT CONVERT(nvarchar(200),value) FROM sys.extended_properties WHERE class=0 AND name=N'SP2Owner';");
        if((string?)await command.ExecuteScalarAsync(ct)!=Owner)throw new InvalidOperationException("DB ownership marker mismatch; no changes permitted.");
    }
    public static async Task<SeedManifest> SeedAsync(Database database,Repository repository,SeedDefinition definition,
        string adminPassword,string staffPassword,string? manifestPath,CancellationToken ct)
    {
        Validation.Password(adminPassword);Validation.Password(staffPassword);
        if(definition.DatasetId!="SP2-DEMO-01"||definition.Version!="1.1"||!definition.Fictional||definition.BasisDate!="2026-10-27"||definition.Categories.Length!=3||definition.Codes.Length!=9||definition.Users.Length!=2||definition.Employees.Length!=3||definition.Careers.Length!=3||!definition.Users.Select(x=>(x[0],x[1],x[3])).SequenceEqual(new[]{("SP2ADMIN","admin","ADMIN"),("SP2STAFF","staff","STAFF")}))throw new InvalidOperationException("Unexpected dataset definition.");
        var now=DateTimeOffset.UtcNow;var today=DateOnly.FromDateTime(TimeZoneInfo.ConvertTime(now,TimeZoneInfo.FindSystemTimeZoneById("Tokyo Standard Time")).DateTime);
        if(today<DateOnly.Parse(definition.BasisDate,System.Globalization.CultureInfo.InvariantCulture))throw new InvalidOperationException("Dataset is not valid before its basis date.");
        var contentHash=Convert.ToHexStringLower(SHA256.HashData(Encoding.UTF8.GetBytes(JsonSerializer.Serialize(definition,Json))));
        await using var unit=await database.BeginAsync(true,ct);await RequireOwnerAsync(unit,ct);
        await using var count=unit.Command("SELECT (SELECT COUNT(*) FROM dbo.m_app_user)+(SELECT COUNT(*) FROM dbo.m_code_category)+(SELECT COUNT(*) FROM dbo.m_code)+(SELECT COUNT(*) FROM dbo.m_employee)+(SELECT COUNT(*) FROM dbo.t_career);");
        var existing=(int)(await count.ExecuteScalarAsync(ct))!;
        if(existing!=0)
        {
            if(manifestPath is null||!File.Exists(manifestPath))throw new InvalidOperationException("Existing data without matching external seed manifest; no changes applied.");
            var prior=JsonSerializer.Deserialize<SeedManifest>(await File.ReadAllTextAsync(manifestPath,ct),Json)??throw new InvalidOperationException("Invalid seed manifest.");
            if(prior.Database!=database.Options.AllowedDatabase||prior.Owner!=Owner||prior.DatasetId!=definition.DatasetId||prior.Version!=definition.Version||prior.BasisDate!=definition.BasisDate||prior.ContentSha256!=contentHash||existing!=20)throw new InvalidOperationException("Existing dataset/owner/content differs; no changes applied.");
            await VerifyAsync(unit,repository,definition,adminPassword,staffPassword,today,ct);
            return prior with{State="SkippedExactMatch"};
        }
        foreach(var category in definition.Categories)
        {
            await using var cmd=unit.Command("INSERT dbo.m_code_category(category_id,category_name) VALUES(@category,@name);",P.V("@category",24,category[0]),P.N("@name",80,category[1]));await cmd.ExecuteNonQueryAsync(ct);
        }
        foreach(var code in definition.Codes)
            await repository.WriteCodeAsync(unit,new(code[0],code[1],code[2],short.Parse(code[1],System.Globalization.CultureInfo.InvariantCulture),true),null,"SP2ADMIN",now,ct);
        var hasher=AuthService.CreateHasher();
        foreach(var user in definition.Users)
        {
            var role=Enum.Parse<UserRole>(user[3]);var value=new AppUser(user[0],user[1],user[2],"",role,true,0,null);
            var verifier=hasher.HashPassword(value,role==UserRole.ADMIN?adminPassword:staffPassword);
            await using var cmd=unit.Command("INSERT dbo.m_app_user(user_id,login_id,display_name,password_verifier,role_id,is_enabled,failed_count,locked_until) VALUES(@id,@login,@name,@verifier,@role,1,0,NULL);",P.N("@id",40,user[0]),P.V("@login",20,user[1]),P.N("@name",80,user[2]),P.N("@verifier",2048,verifier),P.V("@role",5,user[3]));await cmd.ExecuteNonQueryAsync(ct);
        }
        var ids=new Dictionary<string,long>(StringComparer.Ordinal);
        foreach(var employee in definition.Employees)
            ids.Add(employee.EmployeeNo,await repository.InsertEmployeeAsync(unit,Validation.Employee(employee,today),"SP2ADMIN",now,ct));
        foreach(var career in definition.Careers)
        {
            var raw=new CareerRaw(null,Guid.NewGuid(),career.Start,career.End,career.Company,career.Project,career.Description,career.Duties,career.Achievements,career.Technologies,career.Phases,career.Role,career.Team.ToString(System.Globalization.CultureInfo.InvariantCulture));
            await repository.InsertCareerAsync(unit,ids[career.EmployeeNo],Validation.Career(raw,new(today.Year,today.Month,1),1).Values,ct);
        }
        await VerifyAsync(unit,repository,definition,adminPassword,staffPassword,today,ct);await unit.CommitAsync(ct);
        var manifest=new SeedManifest("sample-project2","CSharp_ASPNET",definition.DatasetId,definition.Version,definition.BasisDate,database.Options.AllowedDatabase,Owner,contentHash,now,new(){["m_code_category"]=3,["m_code"]=9,["m_app_user"]=2,["m_employee"]=3,["t_career"]=3},"Applied");
        if(manifestPath is not null){Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(manifestPath))!);await File.WriteAllTextAsync(manifestPath,JsonSerializer.Serialize(manifest,Json),ct);}
        return manifest;
    }
    private static async Task VerifyAsync(DbUnit unit,Repository repository,SeedDefinition definition,string adminPassword,string staffPassword,DateOnly today,CancellationToken ct)
    {
        await repository.ValidateCategoriesAsync(unit,ct);var codes=await repository.CodesAsync(unit,ct);
        if(codes.Count!=9||codes.Any(x=>x.Revision!=1||!x.Enabled||!definition.Codes.Any(y=>y[0]==x.Category&&y[1]==x.Code&&y[2]==x.Name&&short.Parse(y[1],System.Globalization.CultureInfo.InvariantCulture)==x.SortOrder)))throw new InvalidOperationException("Seed code values have changed; no changes applied.");
        foreach(var expected in definition.Users)
        {
            var user=await repository.UserAsync(unit,expected[0],false,ct);
            if(user is null||!user.Enabled||user.LoginId!=expected[1]||user.DisplayName!=expected[2]||user.Role.ToString()!=expected[3]||user.FailedCount!=0||user.LockedUntil is not null||AuthService.CreateHasher().VerifyHashedPassword(user,user.PasswordVerifier,user.Role==UserRole.ADMIN?adminPassword:staffPassword)==PasswordVerificationResult.Failed)throw new InvalidOperationException("Seed user values have changed; no changes applied.");
        }
        foreach(var expected in definition.Employees)
        {
            var id=await repository.EmployeeIdAsync(unit,expected.EmployeeNo,ct)??throw new InvalidOperationException("Seed employee missing.");
            var saved=await repository.EmployeeAsync(unit,id,ct)??throw new InvalidOperationException("Seed employee missing.");
            var expectedCareers=definition.Careers.Where(x=>x.EmployeeNo==expected.EmployeeNo).Select(x=>new CareerValues(DateOnly.Parse(x.Start+"-01",System.Globalization.CultureInfo.InvariantCulture),x.End is null?null:DateOnly.Parse(x.End+"-01",System.Globalization.CultureInfo.InvariantCulture),x.Company,x.Project,x.Description,x.Duties,x.Achievements,x.Technologies,x.Phases,x.Role,x.Team)).ToHashSet();
            if(saved.Employee!=Validation.Employee(expected,today)||saved.Revision!=1||saved.UpdatedBy!="SP2ADMIN"||!expectedCareers.SetEquals(saved.Careers.Select(x=>x.Values))||expectedCareers.Count!=saved.Careers.Count)throw new InvalidOperationException("Seed employee/career values have changed; no changes applied.");
        }
    }
}
