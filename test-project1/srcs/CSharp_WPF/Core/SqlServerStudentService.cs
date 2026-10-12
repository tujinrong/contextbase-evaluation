using System.Data;
using System.Globalization;
using Microsoft.Data.SqlClient;

namespace StudentManagement.Core;

// COM-STU-003/008, DBDEF-SQLSERVER. Trusted application/evaluation service.
// Native production requires the separate EXEC-only DB entrance specified in its profile.
public sealed class SqlServerStudentService : IStudentService
{
    private readonly string _connectionString;
    private readonly Func<CurrentUser> _currentUser;
    private readonly TimeProvider _clock;
    private static readonly Dictionary<string, (SqlDbType Type, int Size)> Columns = new(StringComparer.Ordinal) {
        ["student_no"]=(SqlDbType.VarChar,15), ["student_name"]=(SqlDbType.NVarChar,16), ["student_name_kana"]=(SqlDbType.NVarChar,36),
        ["name_key"]=(SqlDbType.NVarChar,320), ["kana_key"]=(SqlDbType.NVarChar,36), ["birth_date"]=(SqlDbType.Date,0),
        ["gender_code"]=(SqlDbType.VarChar,1), ["postal_code"]=(SqlDbType.VarChar,7), ["prefecture_code"]=(SqlDbType.VarChar,2),
        ["address_line1"]=(SqlDbType.NVarChar,90), ["address_line2"]=(SqlDbType.NVarChar,90), ["phone_number"]=(SqlDbType.VarChar,16),
        ["email_address"]=(SqlDbType.VarChar,60), ["admission_date"]=(SqlDbType.Date,0), ["enrollment_status_code"]=(SqlDbType.VarChar,2),
        ["enrollment_end_date"]=(SqlDbType.Date,0), ["class_id"]=(SqlDbType.BigInt,0), ["emergency_contact_name"]=(SqlDbType.NVarChar,16),
        ["relationship_category"]=(SqlDbType.VarChar,24), ["relationship_code"]=(SqlDbType.VarChar,2), ["emergency_phone_number"]=(SqlDbType.VarChar,16), ["remarks"]=(SqlDbType.NVarChar,240)
    };
    public SqlServerStudentService(string connectionString, Func<CurrentUser> currentUser, TimeProvider? clock = null)
    {
        var builder = new SqlConnectionStringBuilder(connectionString) { Encrypt = SqlConnectionEncryptOption.Mandatory, TrustServerCertificate = false };
        _connectionString = builder.ConnectionString; _currentUser = currentUser; _clock = clock ?? TimeProvider.System;
    }
    private DateTimeOffset Now => _clock.GetUtcNow();
    private static DateOnly BusinessDay(DateTimeOffset now) => DateOnly.FromDateTime(now.ToOffset(TimeSpan.FromHours(9)).DateTime);
    private CurrentUser User()
    {
        var user = _currentUser();
        StudentNormalizer.Text(user.Principal, 64, 64, "Principal", true);
        if (!Guid.TryParse(user.SessionId, out _)) throw new UnauthorizedAccessException("認証セッションが不正です。");
        return user;
    }
    private async Task<SqlConnection> Open(CancellationToken ct)
    {
        var connection = new SqlConnection(_connectionString);
        try {
            await connection.OpenAsync(ct);
            await using var diagnostic = connection.CreateCommand();
            diagnostic.CommandText = "SELECT snapshot_isolation_state FROM sys.databases WHERE database_id=DB_ID()";
            if (Convert.ToInt32(await diagnostic.ExecuteScalarAsync(ct), CultureInfo.InvariantCulture) != 1)
                throw new InvalidOperationException("ALLOW_SNAPSHOT_ISOLATION ONが必要です。");
            return connection;
        } catch { await connection.DisposeAsync(); throw; }
    }
    internal static SqlCommand Command(SqlConnection connection, SqlTransaction? tx, string sql)
        => new(sql, connection, tx) { CommandTimeout = 30 };
    internal static void Param(SqlCommand command, string name, SqlDbType type, object? value, int size = 0)
    {
        if (value is DateOnly date) value = date.ToDateTime(TimeOnly.MinValue);
        var parameter = command.Parameters.Add(name, type);
        if (size != 0) parameter.Size = size;
        parameter.Value = value ?? DBNull.Value;
    }
    private static string? String(SqlDataReader reader, string column) => reader.IsDBNull(reader.GetOrdinal(column)) ? null : reader.GetString(reader.GetOrdinal(column));
    private static long Long(SqlDataReader reader, string column) => reader.GetInt64(reader.GetOrdinal(column));
    private static DateOnly Date(SqlDataReader reader, string column) => DateOnly.FromDateTime(reader.GetDateTime(reader.GetOrdinal(column)));
    private static StudentRow Row(SqlDataReader reader) => new(
        Long(reader,"student_id"), String(reader,"student_no")!, String(reader,"student_name")!, String(reader,"student_name_kana")!, Date(reader,"birth_date"),
        reader.IsDBNull(reader.GetOrdinal("school_year")) ? null : Convert.ToInt32(reader["school_year"]), String(reader,"grade_name"), String(reader,"class_code"), String(reader,"class_name"),
        String(reader,"status_name"), (String(reader,"prefecture_name") ?? "[不整合]") + String(reader,"address_line1"), String(reader,"phone_number"), Date(reader,"admission_date"),
        reader.GetFieldValue<DateTimeOffset>(reader.GetOrdinal("updated_at")), Long(reader,"row_version"));
    private const string RowSelect = """
        SELECT s.student_id,s.student_no,s.student_name,s.student_name_kana,s.birth_date,
               c.school_year,c.class_code,c.class_name,g.code_name grade_name,e.code_name status_name,
               p.code_name prefecture_name,s.address_line1,s.phone_number,s.admission_date,s.updated_at,s.row_version
          FROM dbo.m_student s
          LEFT JOIN dbo.m_class c ON c.class_id=s.class_id
          LEFT JOIN dbo.m_code g ON g.category_id=c.grade_category AND g.code_value=c.grade_code
          LEFT JOIN dbo.m_code e ON e.category_id=s.enrollment_category AND e.code_value=s.enrollment_status_code
          LEFT JOIN dbo.m_code p ON p.category_id=s.prefecture_category AND p.code_value=s.prefecture_code
        """;
    internal static async Task Gate(SqlConnection connection, SqlTransaction tx, CancellationToken ct)
    {
        await using var command = Command(connection,tx,"""
            SET XACT_ABORT ON;
            DECLARE @result int;
            EXEC @result=sys.sp_getapplock @Resource=N'test-project1:student-write',@LockMode='Exclusive',
                 @LockOwner='Transaction',@LockTimeout=5000,@DbPrincipal='public';
            IF @result<0 THROW 51001,N'保存用ロックを取得できませんでした。',1;
            """);
        await command.ExecuteNonQueryAsync(ct);
    }
    public async Task<SearchResult> SearchAsync(SearchCriteria criteria, CancellationToken ct = default)
    {
        _ = User(); var now = Now; var day = BusinessDay(now);
        try {
            if (criteria.Page < 1 || criteria.PageSize is not (20 or 50 or 100) || criteria.SortDirection is not ("asc" or "desc")) throw new ArgumentException("E-COM-003: ページ指定が不正です。");
            var order = criteria.SortKey switch { "studentNo" => "s.student_no", "name" => "s.name_key", "admissionDate" => "s.admission_date", "updatedAt" => "s.updated_at", _ => throw new ArgumentException("E-COM-003: 並び順が不正です。") };
            if (criteria.SchoolYear is < 1900 or > 9998 || criteria.ClassId is <= 0) throw new ArgumentException("E-DATE-003: 年度またはクラスが不正です。");
            if (criteria.UnassignedOnly && (criteria.SchoolYear is not null || criteria.GradeCode is not null || criteria.ClassId is not null)) throw new ArgumentException("E-SRC-001: 未所属と年度・学年・クラスは同時指定できません。");
            var statuses = criteria.EnrollmentStatusCodes;
            if (statuses.Length > 4 || statuses.Distinct(StringComparer.Ordinal).Count() != statuses.Length || statuses.Any(value => value is not ("01" or "02" or "03" or "04"))) throw new ArgumentException("E-STU-009: 在籍区分が不正です。");
            var no = string.IsNullOrEmpty(criteria.StudentNo) ? null : StudentNormalizer.Identifier(criteria.StudentNo,15,"StudentNo");
            var name = StudentNormalizer.Text(criteria.StudentName,8,8,"StudentName");
            name = name is null ? null : StudentNormalizer.NameKey(name);
            var kana = string.IsNullOrEmpty(criteria.StudentNameKana) ? null : StudentNormalizer.Kana(criteria.StudentNameKana,false).Replace(" ","");
            var phone = StudentNormalizer.Phone(criteria.PhoneNumber,"PhoneNumber");
            var grade = StudentNormalizer.Code(criteria.GradeCode,2,"GradeCode",false);
            var prefecture = StudentNormalizer.Code(criteria.PrefectureCode,2,"PrefectureCode",false);
            DateOnly? from = string.IsNullOrEmpty(criteria.AdmissionFrom) ? null : JapaneseDateService.ParseIso(criteria.AdmissionFrom,day);
            DateOnly? to = string.IsNullOrEmpty(criteria.AdmissionTo) ? null : JapaneseDateService.ParseIso(criteria.AdmissionTo,day);
            if (from > to) throw new ArgumentException("E-STU-006: 開始日は終了日以前にしてください。");
            await using var connection = await Open(ct);
            await using var tx = (SqlTransaction)await connection.BeginTransactionAsync(IsolationLevel.Snapshot,ct);
            if (grade is not null && !await CodeExists(connection,tx,"GRADE",grade,ct) || prefecture is not null && !await CodeExists(connection,tx,"PREFECTURE",prefecture,ct)) throw new ArgumentException("E-STU-009: 指定コードが存在しません。");
            if (criteria.SchoolYear is not null) {
                await using var yearCheck = Command(connection,tx,"SELECT COUNT_BIG(*) FROM dbo.m_class WHERE school_year=@year");
                Param(yearCheck,"@year",SqlDbType.SmallInt,criteria.SchoolYear);
                if ((long)(await yearCheck.ExecuteScalarAsync(ct))! == 0) throw new ArgumentException("E-STU-014: 年度候補が存在しません。");
            }
            if (criteria.ClassId is { } classId) {
                await using var classCheck = Command(connection,tx,"SELECT school_year,grade_code FROM dbo.m_class WHERE class_id=@id");
                Param(classCheck,"@id",SqlDbType.BigInt,classId);
                await using var reader = await classCheck.ExecuteReaderAsync(ct);
                if (!await reader.ReadAsync(ct) || criteria.SchoolYear is not null && Convert.ToInt32(reader[0]) != criteria.SchoolYear || grade is not null && reader.GetString(1) != grade) throw new ArgumentException("E-STU-014: 年度・学年・クラスが一致しません。");
            }
            var predicates = new List<string>{ "s.is_deleted=0" };
            var parameters = new List<(string Name, SqlDbType Type, object? Value, int Size)>();
            void Where(string sql, string key, SqlDbType type, object? value, int size = 0) { if (value is not null) { predicates.Add(sql); parameters.Add((key,type,value,size)); } }
            Where("s.student_no LIKE @no ESCAPE '!'","@no",SqlDbType.VarChar,no is null ? null : StudentNormalizer.EscapeLike(no)+"%",31);
            Where("s.name_key LIKE @name ESCAPE '!'","@name",SqlDbType.NVarChar,name is null ? null : "%"+StudentNormalizer.EscapeLike(name)+"%",642);
            Where("s.kana_key LIKE @kana ESCAPE '!'","@kana",SqlDbType.NVarChar,kana is null ? null : "%"+StudentNormalizer.EscapeLike(kana)+"%",74);
            Where("c.school_year=@year","@year",SqlDbType.SmallInt,criteria.SchoolYear);
            Where("c.grade_code=@grade","@grade",SqlDbType.VarChar,grade,2);
            Where("s.class_id=@class","@class",SqlDbType.BigInt,criteria.ClassId);
            if(criteria.UnassignedOnly) predicates.Add("s.class_id IS NULL");
            Where("s.prefecture_code=@prefecture","@prefecture",SqlDbType.VarChar,prefecture,2);
            Where("(s.phone_number=@phone OR s.emergency_phone_number=@phone)","@phone",SqlDbType.VarChar,phone,16);
            Where("s.admission_date>=@from","@from",SqlDbType.Date,from);
            Where("s.admission_date<=@to","@to",SqlDbType.Date,to);
            if(statuses.Length>0) {
                predicates.Add("s.enrollment_status_code IN ("+string.Join(',',statuses.Select((_,index)=>"@status"+index))+")");
                parameters.AddRange(statuses.Select((value,index)=>("@status"+index,SqlDbType.VarChar,(object?)value,2)));
            }
            var where = " WHERE "+string.Join(" AND ",predicates);
            await using var countCommand = Command(connection,tx,"SELECT COUNT_BIG(*) FROM (SELECT TOP (10001) s.student_id FROM dbo.m_student s LEFT JOIN dbo.m_class c ON c.class_id=s.class_id"+where+") limited");
            foreach(var p in parameters) Param(countCommand,p.Name,p.Type,p.Value,p.Size);
            var count = (int)(long)(await countCommand.ExecuteScalarAsync(ct))!;
            if(count>10000) { await tx.CommitAsync(ct); return new(Outcome.NoChange,count,[],now,true,[]); }
            var lastPage = Math.Max(1,(count+criteria.PageSize-1)/criteria.PageSize);
            var page = Math.Min(criteria.Page,lastPage);
            await using var pageCommand = Command(connection,tx,RowSelect+where+" ORDER BY "+order+" "+criteria.SortDirection+",s.student_id ASC OFFSET @offset ROWS FETCH NEXT @size ROWS ONLY");
            foreach(var p in parameters) Param(pageCommand,p.Name,p.Type,p.Value,p.Size);
            Param(pageCommand,"@offset",SqlDbType.Int,checked((page-1)*criteria.PageSize)); Param(pageCommand,"@size",SqlDbType.Int,criteria.PageSize);
            var rows = new List<StudentRow>();
            await using(var reader = await pageCommand.ExecuteReaderAsync(ct)) while(await reader.ReadAsync(ct)) rows.Add(Row(reader));
            await tx.CommitAsync(ct);
            return new(Outcome.NoChange,count,rows,now,false,[]);
        } catch(InputValidationException e) { return new(Outcome.ValidationFailed,0,[],now,false,e.Errors); }
        catch(ArgumentException e) { return new(Outcome.ValidationFailed,0,[],now,false,[StudentNormalizer.ArgumentError("Search",e)]); }
    }
    public async Task<StudentDetail?> GetAsync(long id, CancellationToken ct = default)
    {
        _ = User(); if (id <= 0) return null;
        await using var connection = await Open(ct);
        await using var command = Command(connection,null,"SELECT * FROM dbo.m_student WHERE student_id=@id AND is_deleted=0");
        Param(command,"@id",SqlDbType.BigInt,id);
        await using var reader = await command.ExecuteReaderAsync(ct);
        if(!await reader.ReadAsync(ct)) return null;
        var values = Columns.Keys.ToDictionary(key=>key,key=>reader.IsDBNull(reader.GetOrdinal(key))?null:reader[key]);
        return Detail(id,Long(reader,"row_version"),values,reader.GetFieldValue<DateTimeOffset>(reader.GetOrdinal("updated_at")),String(reader,"updated_by")!);
    }
    private static StudentDetail Detail(long id,long version,Dictionary<string,object?> values,DateTimeOffset updated,string actor)
    {
        string? S(string key)=>values[key]?.ToString();
        DateOnly D(string key)=>values[key] is DateOnly date?date:DateOnly.FromDateTime((DateTime)values[key]!);
        var draft = new StudentDraft {
            StudentNo=S("student_no")!,StudentName=S("student_name")!,StudentNameKana=S("student_name_kana")!,BirthDateInput=JapaneseDateService.ToInput(D("birth_date")),
            GenderCode=S("gender_code")!,PostalCode=S("postal_code")!,PrefectureCode=S("prefecture_code")!,AddressLine1=S("address_line1")!,AddressLine2=S("address_line2"),
            PhoneNumber=S("phone_number"),EmailAddress=S("email_address"),AdmissionDate=D("admission_date").ToString("yyyy-MM-dd",CultureInfo.InvariantCulture),
            EnrollmentStatusCode=S("enrollment_status_code")!,EnrollmentEndDate=values["enrollment_end_date"] is null?null:D("enrollment_end_date").ToString("yyyy-MM-dd",CultureInfo.InvariantCulture),
            ClassId=(long?)values["class_id"],EmergencyContactName=S("emergency_contact_name"),RelationshipCode=S("relationship_code"),EmergencyPhoneNumber=S("emergency_phone_number"),Remarks=S("remarks")
        };
        return new(id,version,draft,D("birth_date"),updated,actor);
    }
    public Task<LookupSet> LookupAsync(CancellationToken ct = default) => LookupAsync(true,ct);
    public async Task<LookupSet> LookupAsync(bool includeOccupancy,CancellationToken ct = default)
    {
        _ = User(); await using var connection = await Open(ct);
        await using var tx=(SqlTransaction)await connection.BeginTransactionAsync(IsolationLevel.Snapshot,ct);
        var occupied=includeOccupancy ? "(SELECT COUNT(*) FROM dbo.m_student s WHERE s.class_id=c.class_id AND s.is_deleted=0 AND s.enrollment_status_code IN ('01','02'))" : "CONVERT(int,0)";
        await using var command=Command(connection,tx,$"""
            SELECT c.category_id,c.code_value,c.code_name,c.display_order,
                   CONVERT(bit,CASE WHEN c.is_active=1 AND k.is_active=1 THEN 1 ELSE 0 END) is_active,c.valid_from,c.valid_to,c.is_protected
              FROM dbo.m_code c JOIN dbo.m_code_category k ON k.category_id=c.category_id ORDER BY c.category_id,c.display_order,c.code_value;
            SELECT c.*, {occupied} occupied
              FROM dbo.m_class c LEFT JOIN dbo.m_code g ON g.category_id=c.grade_category AND g.code_value=c.grade_code
             ORDER BY c.school_year DESC,g.display_order,c.display_order,c.class_code,c.class_id;
            """);
        var codes=new List<CodeEntry>(); var classes=new List<SchoolClass>();
        await using(var reader=await command.ExecuteReaderAsync(ct)) {
            while(await reader.ReadAsync(ct)) codes.Add(new(String(reader,"category_id")!,String(reader,"code_value")!,String(reader,"code_name")!,Convert.ToInt32(reader["display_order"]),reader.GetBoolean(reader.GetOrdinal("is_active")),Date(reader,"valid_from"),reader.IsDBNull(reader.GetOrdinal("valid_to"))?null:Date(reader,"valid_to"),reader.GetBoolean(reader.GetOrdinal("is_protected"))));
            await reader.NextResultAsync(ct);
            while(await reader.ReadAsync(ct)) classes.Add(new(Long(reader,"class_id"),Convert.ToInt32(reader["school_year"]),String(reader,"grade_code")!,String(reader,"class_code")!,String(reader,"class_name")!,Date(reader,"valid_from"),Date(reader,"valid_to"),reader.IsDBNull(reader.GetOrdinal("capacity"))?null:Convert.ToInt32(reader["capacity"]),Convert.ToInt32(reader["occupied"]),reader.GetBoolean(reader.GetOrdinal("is_active"))));
        }
        await tx.CommitAsync(ct); return new(codes,classes);
    }
    private static async Task<bool> CodeExists(SqlConnection connection,SqlTransaction tx,string category,string value,CancellationToken ct)
    {
        await using var command=Command(connection,tx,"SELECT COUNT_BIG(*) FROM dbo.m_code WHERE category_id=@category AND code_value=@value");
        Param(command,"@category",SqlDbType.VarChar,category,24); Param(command,"@value",SqlDbType.VarChar,value,10);
        return (long)(await command.ExecuteScalarAsync(ct))! == 1;
    }

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
            } else await Rollback(tx); // A known deadlock can already have ended this transaction.
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
