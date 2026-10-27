// LEGACY one-time migration resource. Current generation uses build/ and .tmp/.
// One-time conversion of this WPF service to its own EXEC-only database boundary.
import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../../..');const base=path.join(root,'test-project1/srcs/CSharp_WPF');
const service=path.join(base,'Core/SqlServerStudentService.cs');let text=fs.readFileSync(service,'utf8');
if(!text.includes('private static byte[] HashPayload'))throw new Error('One-time native service migration already completed.');
text=text.slice(0,text.indexOf('    private static byte[] HashPayload'));
text=text.replace('using System.Collections.Concurrent;\n','').replaceAll('using System.Collections.Concurrent;\r\n','');
for(const using of ['using System.Security.Cryptography;','using System.Text;','using System.Text.Json;'])text=text.replace(using+'\r\n','').replace(using+'\n','');
text=text.replace('// COM-STU-003/008, DBDEF-SQLSERVER. Trusted application/evaluation service.\r\n// Native production requires the separate EXEC-only DB entrance specified in its profile.','// WPF read adapter and caller-owned transaction for the EXEC-only native database entry.');
text=text.replace('    private readonly bool _webTokens;\r\n','').replace('    private readonly bool _webTokens;\n','');
const confirmation=text.indexOf('    private sealed class Confirmation');const columns=text.indexOf('    private static readonly Dictionary');if(confirmation<0||columns<0)throw new Error('Migration source mismatch');text=text.slice(0,confirmation)+text.slice(columns);
text=text.replace('bool webTokens = false, TimeProvider? clock = null','TimeProvider? clock = null').replace('_webTokens = webTokens; ','').replace('string.IsNullOrEmpty(user.SessionId) || !_webTokens && !Guid.TryParse(user.SessionId, out _)','!Guid.TryParse(user.SessionId, out _)');
text+=String.raw`
    public Task<SaveResult> SaveAsync(SaveRequest request,CancellationToken ct=default)
        => ExecuteNative((c,tx,session,id)=>NativeStoredProcedureClient.SaveAsync(c,tx,request,session,id,ct),ct);
    public Task<SaveResult> DeleteAsync(long id,long version,string rawReason,CancellationToken ct=default)
        => ExecuteNative((c,tx,session,requestId)=>NativeStoredProcedureClient.DeleteAsync(c,tx,id,version,rawReason,session,requestId,ct),ct);
    private async Task<SaveResult> ExecuteNative(Func<SqlConnection,SqlTransaction,Guid,Guid,Task<SaveResult>> execute,CancellationToken ct)
    {
        var user=User();var requestId=Guid.NewGuid();
        await using var connection=await Open(ct);
        await using var tx=(SqlTransaction)await connection.BeginTransactionAsync(IsolationLevel.ReadCommitted,ct);
        bool procedureStarted=false,commitAttempted=false;
        try {
            // DB procedures resolve ORIGINAL_LOGIN/role and regenerate normalized values from Raw.
            procedureStarted=true;var result=await execute(connection,tx,Guid.Parse(user.SessionId),requestId);
            if(result.Outcome is Outcome.Saved or Outcome.ConfirmationRequired) {
                commitAttempted=true;await tx.CommitAsync(ct);
            } else await tx.RollbackAsync(CancellationToken.None);
            return result;
        } catch(Exception e) when(e is SqlException or InvalidOperationException or OperationCanceledException) {
            var rolledBack=await Rollback(tx);var unknown=procedureStarted&&(commitAttempted||!rolledBack);
            return new(unknown?Outcome.Unknown:Outcome.SystemError,null,null,
                [new("","E-COM-004",unknown?"保存結果を確認できません。再保存の前に検索で確認してください。":"処理に失敗しました。受付番号："+requestId)],RequestId:requestId.ToString());
        }
    }
    internal static async Task<bool> Rollback(SqlTransaction tx)
    {
        try { await tx.RollbackAsync(CancellationToken.None);return true; }
        catch(SqlException){return false;}catch(InvalidOperationException){return false;}
    }
}
`;
fs.writeFileSync(service,text);
const gateway=path.join(base,'Services/StudentGateway.cs');fs.writeFileSync(gateway,fs.readFileSync(gateway,'utf8').replace(', webTokens: false',''));
const integration=path.join(base,'database/tests/Program.cs');fs.writeFileSync(integration,fs.readFileSync(integration,'utf8').replace(',webTokens:true',''));
const maintenance=path.join(base,'Core/MasterMaintenanceService.cs');const original=fs.readFileSync(maintenance,'utf8');
fs.writeFileSync(maintenance,original.slice(0,original.indexOf('// BAS-STU-03'))+String.raw`
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
            if(result.Outcome==Outcome.Saved){commitAttempted=true;await tx.CommitAsync(ct);}else await tx.RollbackAsync(CancellationToken.None);
            return result;
        } catch(Exception e) when(e is SqlException or InvalidOperationException or OperationCanceledException) {
            var rolledBack=await Rollback(tx);var unknown=started&&(commitAttempted||!rolledBack);
            return new(unknown?Outcome.Unknown:Outcome.SystemError,null,unknown?"保守結果を確認できません。再実行前にマスタを照会してください。":"保守処理に失敗しました。");
        }
    }
}
`);
console.log('WPF save/delete/master adapters now use typed native procedures; caller commits before Saved.');
