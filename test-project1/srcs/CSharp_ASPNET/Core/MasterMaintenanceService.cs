using System.Data;
using System.Globalization;
using System.Text.Json;
using Microsoft.Data.SqlClient;
using static StudentManagement.Core.SqlServerStudentService;

namespace StudentManagement.Core;

public sealed record ClassChange(long? ClassId,long? ExpectedVersion,int SchoolYear,string GradeCode,string ClassCode,string ClassName,string ValidFrom,string ValidTo,int? Capacity,int DisplayOrder,bool IsActive,string? Remarks);
public sealed record CodeChange(string CategoryId,string CodeValue,long? ExpectedVersion,string CodeName,int DisplayOrder,bool IsActive,string ValidFrom,string? ValidTo,string? Remarks);
public sealed record MaintenanceResult(Outcome Outcome,long? RowVersion,string Message,bool SameNameWarning=false);

// BAS-STU-03 class maintenance and COM-STU-010 protected-code maintenance.
// CLI evaluates roles from the authenticated DB connection on every request.
public sealed class MasterMaintenanceService(string connectionString, StudentDatabaseProfile databaseProfile = StudentDatabaseProfile.Native)
{
    private bool Shared => databaseProfile == StudentDatabaseProfile.SharedAccess;
    private long MaximumVersion => Shared ? int.MaxValue : long.MaxValue;
    private async Task<(SqlConnection Connection,string Actor)> Open(CancellationToken ct)
    {
        if(!Enum.IsDefined(databaseProfile))throw new ArgumentOutOfRangeException(nameof(databaseProfile));
        var connection=new SqlConnection(SharedAccessSchema.ConnectionString(connectionString,databaseProfile));
        SharedAccessSchema.Register(connection,Shared);
        try {
            await connection.OpenAsync(ct);
            var authorization=Shared
                ? "SELECT ORIGINAL_LOGIN(),CASE WHEN IS_SRVROLEMEMBER(N'sysadmin')=1 OR IS_ROLEMEMBER(N'db_owner')=1 OR EXISTS(SELECT 1 FROM dbo.t_app_role WHERE user_id=ORIGINAL_LOGIN() AND role_name=N'Admin') THEN 1 ELSE 0 END"
                : "SELECT ORIGINAL_LOGIN(),IS_ROLEMEMBER(N'student_admin')";
            await using var command=Command(connection,null,authorization);
            await using var reader=await command.ExecuteReaderAsync(ct);
            if(!await reader.ReadAsync(ct)||reader.IsDBNull(1)||reader.GetInt32(1)!=1) throw new UnauthorizedAccessException("E-COM-002: 管理者権限が必要です。");
            var actor=StudentNormalizer.Text(reader.GetString(0),64,64,"Principal",true)!;
            return (connection,actor);
        } catch { await connection.DisposeAsync(); throw; }
    }
    public async Task<MaintenanceResult> SaveClassAsync(ClassChange raw,CancellationToken ct=default)
    {
        if((Shared && (raw.ClassId>int.MaxValue || raw.ExpectedVersion>int.MaxValue)) || raw.SchoolYear is <1900 or >9998 || raw.Capacity is <1 or >9999 || raw.DisplayOrder<0 || raw.ClassId is <=0 || raw.ExpectedVersion is <=0 || (raw.ClassId is null)!=(raw.ExpectedVersion is null)) throw new ArgumentException("E-MST-004: 年度・定員・版を確認してください。");
        var code=StudentNormalizer.Identifier(raw.ClassCode,9,"ClassCode"); var name=StudentNormalizer.Text(raw.ClassName,18,18,"ClassName",true)!;
        var grade=StudentNormalizer.Code(raw.GradeCode,2,"GradeCode")!;
        var remarks=StudentNormalizer.Text(raw.Remarks,120,120,"Remarks",multiline:true);
        var from=JapaneseDateService.ParseIso(raw.ValidFrom,DateOnly.MaxValue,false); var to=JapaneseDateService.ParseIso(raw.ValidTo,DateOnly.MaxValue,false);
        if(from>to||from<new DateOnly(raw.SchoolYear,4,1)||to>new DateOnly(raw.SchoolYear+1,3,31)) throw new ArgumentException("E-MST-004: 利用期間は年度内にしてください。");
        var (connection,actor)=await Open(ct); await using var disposal=connection;
        await using var tx=(SqlTransaction)await connection.BeginTransactionAsync(IsolationLevel.ReadCommitted,ct);
        var now=DateTimeOffset.UtcNow; var day=DateOnly.FromDateTime(now.ToOffset(TimeSpan.FromHours(9)).DateTime);
        try {
            await Gate(connection,tx,ct);
            Dictionary<string,object?>? previous=null;
            if(raw.ClassId is { } id) {
                await using(var load=Command(connection,tx,"SELECT * FROM dbo.m_class WHERE class_id=@id")) {
                    Param(load,"@id",SqlDbType.BigInt,id);
                    await using var reader=await load.ExecuteReaderAsync(ct);
                    if(!await reader.ReadAsync(ct)) return new(Outcome.NotFound,null,"対象クラスが存在しません。");
                    if(Convert.ToInt64(reader["row_version"],CultureInfo.InvariantCulture)!=raw.ExpectedVersion) return new(Outcome.Conflict,null,"他の操作でクラスが変更されています。");
                    previous=Enumerable.Range(0,reader.FieldCount).ToDictionary(reader.GetName,index=>SharedAccessSchema.ReadValue(reader,reader.GetName(index)));
                }
                if(Convert.ToInt32(previous["school_year"])!=raw.SchoolYear||(string)previous["class_code"]! !=code) throw new ArgumentException("E-MST-003: 年度・クラスコードは変更できません。");
                await using var references=Command(connection,tx,"SELECT COUNT_BIG(*),COALESCE(SUM(CONVERT(bigint,CASE WHEN is_deleted=0 AND enrollment_status_code IN ('01','02') THEN 1 ELSE 0 END)),0) FROM dbo.m_student WHERE class_id=@id");
                Param(references,"@id",SqlDbType.BigInt,id); await using var counts=await references.ExecuteReaderAsync(ct); await counts.ReadAsync(ct);
                if(counts.GetInt64(0)>0&&(string)previous["grade_code"]! !=grade) throw new ArgumentException("E-MST-003: 参照学生のあるクラスの学年は変更できません。");
                var occupied=counts.GetInt64(1);
                if(occupied>0&&(!raw.IsActive||day<from||day>to)||raw.Capacity is { } capacity&&occupied>capacity) throw new ArgumentException("E-MST-004: 定員・利用期間が現在の所属状況と整合しません。");
            }
            await using(var lookup=Command(connection,tx,"SELECT c.is_active,k.is_active,c.valid_from,c.valid_to FROM dbo.m_code c JOIN dbo.m_code_category k ON k.category_id=c.category_id WHERE c.category_id='GRADE' AND c.code_value=@grade")) {
                Param(lookup,"@grade",SqlDbType.VarChar,grade,2); await using var reader=await lookup.ExecuteReaderAsync(ct);
                if(!await reader.ReadAsync(ct)) throw new ArgumentException("E-STU-009: 学年が存在しません。");
                if(previous is null||(string)previous["grade_code"]! !=grade)
                    if(!reader.GetBoolean(0)||!reader.GetBoolean(1)||SharedAccessSchema.ReadDate(reader.GetValue(2))>day||!reader.IsDBNull(3)&&SharedAccessSchema.ReadDate(reader.GetValue(3))<day) throw new ArgumentException("E-STU-011: 学年は現在選択できません。");
            }
            var values=new Dictionary<string,object?>{{"school_year",raw.SchoolYear},{"grade_code",grade},{"class_code",code},{"class_name",name},{"valid_from",from},{"valid_to",to},{"capacity",raw.Capacity},{"display_order",raw.DisplayOrder},{"is_active",raw.IsActive},{"remarks",remarks}};
            var changed=values.Where(pair=>previous is null||!Same(pair.Value,previous[pair.Key])).Select(pair=>pair.Key).ToArray();
            if(changed.Length==0) { await tx.RollbackAsync(ct); return new(Outcome.NoChange,raw.ExpectedVersion,"変更内容がありません。"); }
            if(raw.ExpectedVersion==MaximumVersion) throw new ArgumentException("更新管理番号が上限に到達しました。");
            var sameName=false;
            await using(var check=Command(connection,tx,"SELECT COUNT_BIG(*) FROM dbo.m_class WHERE school_year=@year AND grade_code=@grade AND class_name=@name AND (@id IS NULL OR class_id<>@id)")) {
                Param(check,"@year",SqlDbType.SmallInt,raw.SchoolYear); Param(check,"@grade",SqlDbType.VarChar,grade,2); Param(check,"@name",SqlDbType.NVarChar,name,36); Param(check,"@id",SqlDbType.BigInt,raw.ClassId); sameName=(long)(await check.ExecuteScalarAsync(ct))!>0;
            }
            var types=new Dictionary<string,(SqlDbType,int)>{{"school_year",(SqlDbType.SmallInt,0)},{"grade_code",(SqlDbType.VarChar,2)},{"class_code",(SqlDbType.VarChar,9)},{"class_name",(SqlDbType.NVarChar,36)},{"valid_from",(SqlDbType.Date,0)},{"valid_to",(SqlDbType.Date,0)},{"capacity",(SqlDbType.Int,0)},{"display_order",(SqlDbType.Int,0)},{"is_active",(SqlDbType.Bit,0)},{"remarks",(SqlDbType.NVarChar,240)}};
            var result=await Save(connection,tx,"m_class","class_id",raw.ClassId,raw.ExpectedVersion,values,types,actor,now,ct);
            await Log(connection,tx,"m_class",result.Id.ToString(CultureInfo.InvariantCulture),AuditOperation.ForMaster(previous is null?null:(bool)previous["is_active"]!,raw.IsActive),raw.ExpectedVersion,result.Version,changed,actor,now,ct);
            await tx.CommitAsync(ct); return new(Outcome.Saved,result.Version,"クラスを保存しました。",sameName);
        } catch { await Rollback(tx); throw; }
    }
    public async Task<MaintenanceResult> SaveCodeAsync(CodeChange raw,CancellationToken ct=default)
    {
        if((Shared && raw.ExpectedVersion>int.MaxValue) || raw.CategoryId is not ("GENDER" or "ENROLLMENT_STATUS" or "PREFECTURE" or "RELATIONSHIP" or "GRADE")||raw.ExpectedVersion is <=0||raw.DisplayOrder<0) throw new ArgumentException("E-MST-003: 分類・版・表示順を確認してください。");
        var name=StudentNormalizer.Text(raw.CodeName,12,12,"CodeName",true)!;
        var remarks=StudentNormalizer.Text(raw.Remarks,120,120,"Remarks",multiline:true);
        var from=JapaneseDateService.ParseIso(raw.ValidFrom,DateOnly.MaxValue,false);
        DateOnly? to=string.IsNullOrEmpty(raw.ValidTo)?null:JapaneseDateService.ParseIso(raw.ValidTo,DateOnly.MaxValue,false);
        if(to<from) throw new ArgumentException("E-MST-004: 有効期間が逆転しています。");
        var (connection,actor)=await Open(ct); await using var disposal=connection;
        await using var tx=(SqlTransaction)await connection.BeginTransactionAsync(IsolationLevel.ReadCommitted,ct); var now=DateTimeOffset.UtcNow;
        try {
            await Gate(connection,tx,ct);
            int width; bool allow;
            await using(var category=Command(connection,tx,"SELECT code_length,allow_add FROM dbo.m_code_category WHERE category_id=@category")) {
                Param(category,"@category",SqlDbType.VarChar,raw.CategoryId,24); await using var reader=await category.ExecuteReaderAsync(ct);
                if(!await reader.ReadAsync(ct)) throw new ArgumentException("E-MST-001: 分類初期値がありません。"); width=Convert.ToInt32(reader.GetValue(0),CultureInfo.InvariantCulture);allow=reader.GetBoolean(1);
            }
            var value=StudentNormalizer.Code(raw.CodeValue,width,"CodeValue")!;
            Dictionary<string,object?>? previous=null;
            await using(var load=Command(connection,tx,"SELECT * FROM dbo.m_code WHERE category_id=@category AND code_value=@value")) {
                Param(load,"@category",SqlDbType.VarChar,raw.CategoryId,24); Param(load,"@value",SqlDbType.VarChar,value,10); await using var reader=await load.ExecuteReaderAsync(ct);
                if(await reader.ReadAsync(ct)) previous=Enumerable.Range(0,reader.FieldCount).ToDictionary(reader.GetName,index=>SharedAccessSchema.ReadValue(reader,reader.GetName(index)));
            }
            if(previous is null&&raw.ExpectedVersion is not null) return new(Outcome.NotFound,null,"対象コードが存在しません。");
            if(previous is not null&&Convert.ToInt64(previous["row_version"],CultureInfo.InvariantCulture) !=raw.ExpectedVersion) return new(Outcome.Conflict,null,"コードは既に存在するか、他の操作で変更されています。");
            if(previous is null&&!allow) throw new ArgumentException("E-MST-003: この分類への通常追加はできません。");
            if(previous is not null&&(bool)previous["is_protected"]!) {
                var oldFrom=SharedAccessSchema.ReadDate(previous["valid_from"]!); var oldTo=previous["valid_to"] is { } end ? SharedAccessSchema.ReadDate(end):(DateOnly?)null;
                if(!raw.IsActive||from>oldFrom||to is not null&&(oldTo is null||to<oldTo)) throw new ArgumentException("E-MST-003: 保護値の停止・期間短縮はできません。");
            }
            var values=new Dictionary<string,object?>{{"code_name",name},{"display_order",raw.DisplayOrder},{"is_active",raw.IsActive},{"valid_from",from},{"valid_to",to},{"remarks",remarks}};
            var changed=values.Where(pair=>previous is null||!Same(pair.Value,previous[pair.Key])).Select(pair=>pair.Key).ToArray();
            if(changed.Length==0) { await tx.RollbackAsync(ct); return new(Outcome.NoChange,raw.ExpectedVersion,"変更内容がありません。"); }
            if(raw.ExpectedVersion==MaximumVersion) throw new ArgumentException("更新管理番号が上限に到達しました。");
            var sql=previous is null?"INSERT dbo.m_code(category_id,code_value,code_name,display_order,is_active,valid_from,valid_to,is_protected,remarks,created_at,created_by,updated_at,updated_by,row_version) VALUES(@category,@value,@name,@order,@active,@from,@to,0,@remarks,@now,@actor,@now,@actor,1)":"UPDATE dbo.m_code SET code_name=@name,display_order=@order,is_active=@active,valid_from=@from,valid_to=@to,remarks=@remarks,updated_at=@now,updated_by=@actor,row_version=row_version+1 WHERE category_id=@category AND code_value=@value AND row_version=@version";
            await using(var save=Command(connection,tx,sql)) {
                Param(save,"@category",SqlDbType.VarChar,raw.CategoryId,24); Param(save,"@value",SqlDbType.VarChar,value,10); Param(save,"@name",SqlDbType.NVarChar,name,24); Param(save,"@order",SqlDbType.Int,raw.DisplayOrder); Param(save,"@active",SqlDbType.Bit,raw.IsActive); Param(save,"@from",SqlDbType.Date,from); Param(save,"@to",SqlDbType.Date,to); Param(save,"@remarks",SqlDbType.NVarChar,remarks,240); Param(save,"@now",SqlDbType.DateTimeOffset,now); Param(save,"@actor",SqlDbType.NVarChar,actor,128); if(previous is not null) Param(save,"@version",SqlDbType.BigInt,raw.ExpectedVersion);
                if(await save.ExecuteNonQueryAsync(ct)!=1) throw new DBConcurrencyException();
            }
            var version=(raw.ExpectedVersion??0)+1;
            await Log(connection,tx,"m_code",raw.CategoryId+":"+value,AuditOperation.ForMaster(previous is null?null:(bool)previous["is_active"]!,raw.IsActive),raw.ExpectedVersion,version,changed,actor,now,ct);
            await tx.CommitAsync(ct); return new(Outcome.Saved,version,"コードを保存しました。");
        } catch { await Rollback(tx); throw; }
    }
    private static bool Same(object? a,object? b)=>a is DateOnly date&&b is DateTime timestamp?date==DateOnly.FromDateTime(timestamp):a is int number&&b is short small?number==small:Equals(a,b);
    private static async Task<(long Id,long Version)> Save(SqlConnection connection,SqlTransaction tx,string table,string key,long? id,long? before,Dictionary<string,object?> values,Dictionary<string,(SqlDbType,int)> types,string actor,DateTimeOffset now,CancellationToken ct)
    {
        var columns=values.Keys.ToArray();
        var sql=id is null?"DECLARE @saved TABLE(id bigint);INSERT dbo."+table+"("+string.Join(',',columns)+",grade_category,created_at,created_by,updated_at,updated_by,row_version) OUTPUT INSERTED."+key+" INTO @saved VALUES("+string.Join(',',columns.Select(column=>"@"+column))+",'GRADE',@now,@actor,@now,@actor,1);SELECT id FROM @saved;":"DECLARE @saved TABLE(id bigint);UPDATE dbo."+table+" SET "+string.Join(',',columns.Select(column=>column+"=@"+column))+",updated_at=@now,updated_by=@actor,row_version=row_version+1 OUTPUT INSERTED."+key+" INTO @saved WHERE "+key+"=@id AND row_version=@version; SELECT id FROM @saved;";
        await using var command=Command(connection,tx,sql); foreach(var column in columns) Param(command,"@"+column,types[column].Item1,values[column],types[column].Item2); Param(command,"@now",SqlDbType.DateTimeOffset,now); Param(command,"@actor",SqlDbType.NVarChar,actor,128);
        if(id is not null) { Param(command,"@id",SqlDbType.BigInt,id);Param(command,"@version",SqlDbType.BigInt,before); }
        var saved=await command.ExecuteScalarAsync(ct); if(saved is null) throw new DBConcurrencyException(); return (Convert.ToInt64(saved,CultureInfo.InvariantCulture),(before??0)+1);
    }
    private static async Task Log(SqlConnection connection,SqlTransaction tx,string table,string key,string operation,long? before,long after,string[] changed,string actor,DateTimeOffset now,CancellationToken ct)
    {
        await using var command=Command(connection,tx,"INSERT dbo.t_operation_log(target_table,target_key,operation_type,before_version,after_version,changed_columns,executed_by,executed_at,correlation_id,operation_reason,duplicate_confirmed) VALUES(@table,@key,@op,@before,@after,@changed,@actor,@now,@request,NULL,0)");
        Param(command,"@table",SqlDbType.VarChar,table,21);Param(command,"@key",SqlDbType.VarChar,key,35);Param(command,"@op",SqlDbType.VarChar,operation,11);Param(command,"@before",SqlDbType.BigInt,before);Param(command,"@after",SqlDbType.BigInt,after);Param(command,"@changed",SqlDbType.NVarChar,JsonSerializer.Serialize(changed),-1);Param(command,"@actor",SqlDbType.NVarChar,actor,128);Param(command,"@now",SqlDbType.DateTimeOffset,now);Param(command,"@request",SqlDbType.UniqueIdentifier,Guid.NewGuid());await command.ExecuteNonQueryAsync(ct);
    }
}
