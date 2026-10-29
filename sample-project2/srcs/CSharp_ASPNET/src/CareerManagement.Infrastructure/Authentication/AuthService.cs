using System.Security.Cryptography;
using CareerManagement.Application;
using CareerManagement.Infrastructure.Sql;
using CareerManagement.Infrastructure.State;
using Microsoft.AspNetCore.Identity;
using Microsoft.Extensions.Options;

namespace CareerManagement.Infrastructure.Authentication;

public sealed class AuthService(Database database,Repository repository,BusinessClock clock,SessionRegistry sessions)
{
    public static PasswordHasher<AppUser> CreateHasher()=>new(Options.Create(new PasswordHasherOptions{CompatibilityMode=PasswordHasherCompatibilityMode.IdentityV3,IterationCount=100000}));
    private readonly PasswordHasher<AppUser> hasher=CreateHasher();
    private readonly AppUser dummy=new("DUMMY","DUMMY","", "",UserRole.STAFF,false,0,null);
    private string? dummyVerifier;
    public async Task<Actor?> AuthenticateAsync(LoginInput input,CancellationToken ct)
    {
        var id=Validation.LoginId(input.LoginId);Validation.Password(input.Password);
        try
        {
            await using var unit=await database.BeginAsync(true,ct);
            var now=clock.UtcNow; // F01-E01: after the global DB gate is acquired.
            var user=await repository.UserAsync(unit,id,true,ct);
            if(user is null)
            {
                dummyVerifier??=hasher.HashPassword(dummy,Convert.ToHexString(RandomNumberGenerator.GetBytes(32)));
                hasher.VerifyHashedPassword(dummy,dummyVerifier,input.Password);return null;
            }
            if(!user.Enabled||user.LockedUntil>now)return null;
            var failed=user.LockedUntil is not null?(byte)0:user.FailedCount;
            var verified=hasher.VerifyHashedPassword(user,user.PasswordVerifier,input.Password)!=PasswordVerificationResult.Failed;
            if(verified)
            {
                var current=await repository.UserAsync(unit,user.UserId,false,ct);
                if(current is null||!current.Enabled)return null;
                if(user.FailedCount!=0||user.LockedUntil is not null)await repository.UpdateAuthAsync(unit,user.UserId,0,null,ct);
            }
            else
            {
                failed=(byte)Math.Min(5,failed+1);
                await repository.UpdateAuthAsync(unit,user.UserId,failed,failed==5?now.AddMinutes(15):null,ct);
            }
            // SuccessRehashNeeded is success; password_verifier remains unchanged (F01-DB05).
            await unit.CommitAsync(ct);
            return verified?new(user.UserId,sessions.Create(user.UserId),user.DisplayName,user.Role):null;
        }
        catch(BusinessException){return null;}
        catch(System.Data.Common.DbException){return null;}
        catch(FormatException){return null;}
        catch(CryptographicException){return null;}
        catch(OperationCanceledException){return null;}
        catch(Exception ex)when(ex is not OutOfMemoryException){return null;}
    }
}
public sealed class CurrentUserService(Database database,Repository repository,SessionRegistry sessions)
{
    public async Task<Actor> RequireAsync(Actor actor,bool admin,CancellationToken ct)
    {
        await using var unit=await database.BeginAsync(false,ct);
        var result=await RequireInAsync(unit,actor,admin,ct);await unit.CommitAsync(ct);return result;
    }
    public async Task<Actor> RequireInAsync(DbUnit unit,Actor actor,bool admin,CancellationToken ct)
    {
        if(!sessions.IsValid(actor.SessionId,actor.UserId))throw BusinessException.Error(2,"Expired");
        var user=await repository.UserAsync(unit,actor.UserId,false,ct);
        if(user is null||!user.Enabled)throw BusinessException.Error(2,"Expired");
        if(admin&&user.Role!=UserRole.ADMIN)throw BusinessException.Error(3,"Forbidden");
        return new(user.UserId,actor.SessionId,user.DisplayName,user.Role);
    }
}
