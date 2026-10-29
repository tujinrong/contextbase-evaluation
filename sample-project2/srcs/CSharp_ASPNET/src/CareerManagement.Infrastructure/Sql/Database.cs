using System.Data;
using CareerManagement.Application;
using Microsoft.Data.SqlClient;

namespace CareerManagement.Infrastructure.Sql;

public sealed class DatabaseOptions
{
    public required string ConnectionString {get;init;}
    public required string AllowedDatabase {get;init;}
    public bool Fixture {get;init;}
    public void Validate()
    {
        var b=new SqlConnectionStringBuilder(ConnectionString);
        if(!b.IntegratedSecurity||!b.Encrypt||b.InitialCatalog!=AllowedDatabase||(!Fixture&&b.TrustServerCertificate)) throw new InvalidOperationException("SQL connection policy violation.");
        if(AllowedDatabase!="SampleProject2_Career"&&!(Fixture&&System.Text.RegularExpressions.Regex.IsMatch(AllowedDatabase,"^SP2_WebFixture_[A-Za-z0-9_]{1,48}$",System.Text.RegularExpressions.RegexOptions.CultureInvariant))) throw new InvalidOperationException("Database allowlist violation.");
    }
}
// Fault seams are supplied only by formal test constructors. The web registration uses NoDbFaults.
public interface IDbFaults { void BeforeChildWrite(); void BeforeCommit(); void AfterCommit(); void BeforeRead(); void BeforeRollback(); }
public sealed class NoDbFaults:IDbFaults { public void BeforeChildWrite(){} public void BeforeCommit(){} public void AfterCommit(){} public void BeforeRead(){} public void BeforeRollback(){} }
public sealed class Database(DatabaseOptions options,IDbFaults faults)
{
    public DatabaseOptions Options=>options;
    public IDbFaults Faults=>faults;
    public async Task<DbUnit> BeginAsync(bool write,CancellationToken ct)
    {
        options.Validate();
        var connection=new SqlConnection(options.ConnectionString);
        try
        {
            await connection.OpenAsync(ct);
            var tx=(SqlTransaction)await connection.BeginTransactionAsync(IsolationLevel.Serializable,ct);
            var unit=new DbUnit(connection,tx,faults);
            try
            {
                await using var command=unit.Command("SET XACT_ABORT ON; SET LOCK_TIMEOUT 10000; DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource=N'SP2.Career.WriteGate',@LockMode=@mode,@LockOwner='Transaction',@LockTimeout=10000,@DbPrincipal='public'; SELECT @r;",P.V("@mode",32,write?"Exclusive":"Shared"));
                var code=Convert.ToInt32(await command.ExecuteScalarAsync(ct),System.Globalization.CultureInfo.InvariantCulture);
                if(code<0) throw BusinessException.Error(code==-1?27:code==-2?30:17,code==-1?"Busy":"RolledBack");
                return unit;
            }
            catch { await unit.DisposeAsync();throw; }
        }
        catch {await connection.DisposeAsync();throw;}
    }
}
public sealed class DbUnit(SqlConnection connection,SqlTransaction transaction,IDbFaults faults):IAsyncDisposable
{
    private bool commitSent;
    private bool done;
    public SqlConnection Connection=>connection;
    public SqlTransaction Transaction=>transaction;
    public SqlCommand Command(string sql,params SqlParameter[] parameters)
    {
        var command=new SqlCommand(sql,connection,transaction){CommandTimeout=30}; command.Parameters.AddRange(parameters);return command;
    }
    public async Task CommitAsync(CancellationToken ct)
    {
        faults.BeforeCommit();commitSent=true;
        try {await transaction.CommitAsync(ct); done=true;faults.AfterCommit();}
        catch {throw new BusinessException(Outcome.Of(34,"ResultUnknown",CommitState.Unknown));}
    }
    public async ValueTask DisposeAsync()
    {
        var uncertain=false;
        if(!done&&!commitSent)
        {
            try{faults.BeforeRollback();await transaction.RollbackAsync(CancellationToken.None);}
            catch {uncertain=true;}
        }
        try{await transaction.DisposeAsync();await connection.DisposeAsync();}
        catch{uncertain=true;}
        if(uncertain)throw new BusinessException(Outcome.Of(34,"ResultUnknown",CommitState.Unknown));
    }
}
public static class P
{
    public static SqlParameter N(string name,int size,string? value)=>new(name,SqlDbType.NVarChar,size){Value=(object?)value??DBNull.Value};
    public static SqlParameter V(string name,int size,string? value)=>new(name,SqlDbType.VarChar,size){Value=(object?)value??DBNull.Value};
    public static SqlParameter C(string name,int size,string? value)=>new(name,SqlDbType.Char,size){Value=(object?)value??DBNull.Value};
    public static SqlParameter I(string name,int value)=>new(name,SqlDbType.Int){Value=value};
    public static SqlParameter L(string name,long value)=>new(name,SqlDbType.BigInt){Value=value};
    public static SqlParameter S(string name,short value)=>new(name,SqlDbType.SmallInt){Value=value};
    public static SqlParameter B(string name,bool value)=>new(name,SqlDbType.Bit){Value=value};
    public static SqlParameter Tiny(string name,byte value)=>new(name,SqlDbType.TinyInt){Value=value};
    public static SqlParameter Date(string name,DateOnly? value)=>new(name,SqlDbType.Date){Value=value.HasValue?value.Value.ToDateTime(TimeOnly.MinValue):DBNull.Value};
    public static SqlParameter Utc(string name,DateTimeOffset? value)=>new(name,SqlDbType.DateTime2){Scale=7,Value=value.HasValue?value.Value.UtcDateTime:DBNull.Value};
}
public static class SqlErrors
{
    public static Outcome Map(Exception e,int fallback=17)
    {
        if(e is BusinessException b)return b.Outcome;
        if(e is OperationCanceledException)return Outcome.Of(30,"Cancelled");
        if(e is SqlException sql)
        {
            if(sql.Number is -2 or 1222)return Outcome.Of(27,"Busy",CommitState.RolledBack);
            if(sql.Number is 2601 or 2627)return Outcome.Of(sql.Message.Contains("employee",StringComparison.OrdinalIgnoreCase)?6:22);
            if(sql.Number==547)return Outcome.Of(16);
        }
        return Outcome.Of(fallback,fallback==20?"Corrupt":"RolledBack",CommitState.RolledBack);
    }
}
