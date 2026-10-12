using System.Data;
using System.Globalization;
using System.Text.Json;
using Microsoft.Data.SqlClient;
using static StudentManagement.Core.SqlServerStudentService;

namespace StudentManagement.Core;

public sealed record ClassChange(long? ClassId,long? ExpectedVersion,int SchoolYear,string GradeCode,string ClassCode,string ClassName,string ValidFrom,string ValidTo,int? Capacity,int DisplayOrder,bool IsActive,string? Remarks);
public sealed record CodeChange(string CategoryId,string CodeValue,long? ExpectedVersion,string CodeName,int DisplayOrder,bool IsActive,string ValidFrom,string? ValidTo,string? Remarks);
public sealed record MaintenanceResult(Outcome Outcome,long? RowVersion,string Message,bool SameNameWarning=false);


// Native administrator operations use only EXEC; caller handles the transaction outcome.
public sealed class MasterMaintenanceService(string connectionString)
{
    public Task<MaintenanceResult> SaveClassAsync(ClassChange raw,CancellationToken ct=default)
        => Execute((c,tx,id)=>NativeStoredProcedureClient.SaveClassAsync(c,tx,raw,id,ct:ct),ct);
    public Task<MaintenanceResult> SaveCodeAsync(CodeChange raw,CancellationToken ct=default)
        => Execute((c,tx,id)=>NativeStoredProcedureClient.SaveCodeAsync(c,tx,raw,id,ct:ct),ct);
    private async Task<MaintenanceResult> Execute(Func<SqlConnection,SqlTransaction,Guid,Task<MaintenanceResult>> execute,CancellationToken ct)
    {
        var builder=new SqlConnectionStringBuilder(connectionString){Encrypt=SqlConnectionEncryptOption.Mandatory,TrustServerCertificate=false};
        await using var connection=new SqlConnection(builder.ConnectionString);await connection.OpenAsync(ct);
        await using var tx=(SqlTransaction)await connection.BeginTransactionAsync(IsolationLevel.ReadCommitted,ct);
        bool started=false,commitAttempted=false;
        try {
            started=true;var result=await execute(connection,tx,Guid.NewGuid());
            if(result.Outcome==Outcome.Saved){commitAttempted=true;await tx.CommitAsync(ct);}else await Rollback(tx);
            return result;
        } catch(Exception e) when(e is SqlException or InvalidOperationException or OperationCanceledException) {
            var rolledBack=await Rollback(tx);var unknown=started&&(commitAttempted||!rolledBack);
            return new(unknown?Outcome.Unknown:Outcome.SystemError,null,unknown?"保守結果を確認できません。再実行前にマスタを照会してください。":"保守処理に失敗しました。");
        }
    }
}
