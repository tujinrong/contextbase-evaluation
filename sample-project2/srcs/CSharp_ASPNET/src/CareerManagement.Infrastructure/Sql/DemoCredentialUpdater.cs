using System.Security.Cryptography;
using System.Text;
using CareerManagement.Application;
using CareerManagement.Infrastructure.Authentication;
using Microsoft.AspNetCore.Identity;

namespace CareerManagement.Infrastructure.Sql;

public sealed record DemoCredentialMigration(string ProjectId,string MethodId,string Database,string Owner,
    DateTimeOffset AppliedUtc,string State,int AccountsChanged,string[] UserIds,string[] LoginIds,
    Dictionary<string,string> BusinessBefore,Dictionary<string,string> BusinessAfter,
    string OtherUsersBefore,string OtherUsersAfter,string Lineage);

/// <summary>Explicit auth-only update for the two owned sample-project2 DEMO identities.</summary>
public static class DemoCredentialUpdater
{
    public const string Password="123";
    private static readonly (string Id,string OldLogin,string Login,UserRole Role)[] Targets=
        [("SP2ADMIN","demoadmin","admin",UserRole.ADMIN),("SP2STAFF","demostaff","staff",UserRole.STAFF)];

    public static async Task<DemoCredentialMigration> ApplyAsync(Database database,Repository repository,CancellationToken ct)
    {
        Validation.Password(Password);
        await using var unit=await database.BeginAsync(true,ct);
        await SafeInitializer.RequireOwnerAsync(unit,ct);
        var before=await BusinessHashesAsync(unit,ct);
        var othersBefore=await OtherUsersHashAsync(unit,ct);
        var users=new Dictionary<string,AppUser>(StringComparer.Ordinal);
        // Validate every identity and destination before touching either account.
        foreach(var target in Targets)
        {
            var user=await repository.UserAsync(unit,target.Id,false,ct)
                ??throw new InvalidOperationException("Expected DEMO identity is missing; no credential changes applied.");
            if(user.Role!=target.Role||!(user.LoginId.Equals(target.OldLogin,StringComparison.OrdinalIgnoreCase)||user.LoginId.Equals(target.Login,StringComparison.OrdinalIgnoreCase)))
                throw new InvalidOperationException("DEMO identity, login or role differs; no credential changes applied.");
            var collision=await repository.UserAsync(unit,target.Login,true,ct);
            if(collision is not null&&collision.UserId!=target.Id)
                throw new InvalidOperationException("Requested DEMO login is owned by another identity; no changes applied.");
            users.Add(target.Id,user);
        }
        var hasher=AuthService.CreateHasher();var changed=0;
        foreach(var target in Targets)
        {
            var user=users[target.Id];
            var verified=hasher.VerifyHashedPassword(user,user.PasswordVerifier,Password)!=PasswordVerificationResult.Failed;
            if(user.LoginId==target.Login&&user.Enabled&&user.FailedCount==0&&user.LockedUntil is null&&verified)continue;
            var verifier=verified?user.PasswordVerifier:hasher.HashPassword(user,Password);
            await using var command=unit.Command("UPDATE dbo.m_app_user SET login_id=@login,password_verifier=@verifier,is_enabled=1,failed_count=0,locked_until=NULL WHERE user_id=@id AND role_id=@role;",
                P.V("@login",20,target.Login),P.N("@verifier",2048,verifier),P.N("@id",40,target.Id),P.V("@role",5,target.Role.ToString()));
            if(await command.ExecuteNonQueryAsync(ct)!=1)throw new InvalidOperationException("DEMO identity changed during credential update.");
            changed++;
        }
        foreach(var target in Targets)
        {
            var user=await repository.UserAsync(unit,target.Id,false,ct);
            if(user is null||user.UserId!=target.Id||user.Role!=target.Role||user.DisplayName!=users[target.Id].DisplayName||user.LoginId!=target.Login||!user.Enabled||user.FailedCount!=0||user.LockedUntil is not null||hasher.VerifyHashedPassword(user,user.PasswordVerifier,Password)==PasswordVerificationResult.Failed)
                throw new InvalidOperationException("Credential update readback failed; transaction rolled back.");
        }
        var after=await BusinessHashesAsync(unit,ct);var othersAfter=await OtherUsersHashAsync(unit,ct);
        if(!before.OrderBy(x=>x.Key,StringComparer.Ordinal).SequenceEqual(after.OrderBy(x=>x.Key,StringComparer.Ordinal))||othersBefore!=othersAfter)
            throw new InvalidOperationException("Unrelated data changed during credential update; transaction rolled back.");
        await unit.CommitAsync(ct);
        return new("sample-project2","CSharp_ASPNET",database.Options.AllowedDatabase,SafeInitializer.Owner,
            DateTimeOffset.UtcNow,changed==0?"SkippedExactMatch":"AppliedAuthOnly",changed,
            Targets.Select(x=>x.Id).ToArray(),Targets.Select(x=>x.Login).ToArray(),before,after,othersBefore,othersAfter,
            "Existing seed version and business rows retained; this auth-only migration is not a full SP2-DEMO-01 v1.1 reseed.");
    }

    private static async Task<Dictionary<string,string>> BusinessHashesAsync(DbUnit unit,CancellationToken ct)
    {
        (string Table,string Order)[] tables=[("m_code_category","category_id"),("m_code","category_id,code"),("m_employee","employee_id"),("t_career","career_id")];
        var result=new Dictionary<string,string>(StringComparer.Ordinal);
        foreach(var item in tables)
        {
            await using var command=unit.Command($"SELECT * FROM dbo.{item.Table} ORDER BY {item.Order} FOR JSON PATH,INCLUDE_NULL_VALUES;");
            result[item.Table]=await HashRowsAsync(command,ct);
        }
        return result;
    }
    private static async Task<string> OtherUsersHashAsync(DbUnit unit,CancellationToken ct)
    {
        await using var command=unit.Command("SELECT * FROM dbo.m_app_user WHERE user_id NOT IN (N'SP2ADMIN',N'SP2STAFF') ORDER BY user_id FOR JSON PATH,INCLUDE_NULL_VALUES;");
        return await HashRowsAsync(command,ct);
    }
    private static async Task<string> HashRowsAsync(Microsoft.Data.SqlClient.SqlCommand command,CancellationToken ct)
    {
        // FOR JSON may stream several rows for long text. Hash the complete ordered content.
        var text=new StringBuilder();await using var reader=await command.ExecuteReaderAsync(ct);
        while(await reader.ReadAsync(ct))text.Append(reader.GetString(0));
        return Convert.ToHexStringLower(SHA256.HashData(Encoding.UTF8.GetBytes(text.ToString())));
    }
}
