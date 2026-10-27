using System.Collections.Concurrent;
using System.Data;
using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Runtime.CompilerServices;
using Microsoft.Data.SqlClient;

namespace StudentManagement.Core;

// COM-STU-003/008, DBDEF-SQLSERVER. Trusted application/evaluation service.
// Native production requires the separate EXEC-only DB entrance specified in its profile.
public sealed class SqlServerStudentService : IStudentService
{
    private readonly string _connectionString;
    private readonly Func<CurrentUser> _currentUser;
    private readonly bool _webTokens;
    private readonly TimeProvider _clock;
    private readonly bool _sharedAccess;
    private long MaximumVersion => _sharedAccess ? int.MaxValue : long.MaxValue;
    private sealed class Confirmation(CurrentUser owner, long? id, long? version, byte[] payload, byte[] candidates, DateTimeOffset expires)
    {
        public CurrentUser Owner { get; } = owner;
        public long? Id { get; } = id;
        public long? Version { get; } = version;
        public byte[] Payload { get; } = payload;
        public byte[] Candidates { get; } = candidates;
        public DateTimeOffset Expires { get; } = expires;
        public int Busy;
    }
    private static readonly ConcurrentDictionary<string, Confirmation> WebConfirmations = new(StringComparer.Ordinal);
    private static readonly Dictionary<string, (SqlDbType Type, int Size)> Columns = new(StringComparer.Ordinal) {
        ["student_no"]=(SqlDbType.VarChar,15), ["student_name"]=(SqlDbType.NVarChar,16), ["student_name_kana"]=(SqlDbType.NVarChar,36),
        ["name_key"]=(SqlDbType.NVarChar,320), ["kana_key"]=(SqlDbType.NVarChar,36), ["birth_date"]=(SqlDbType.Date,0),
        ["gender_code"]=(SqlDbType.VarChar,1), ["postal_code"]=(SqlDbType.VarChar,7), ["prefecture_code"]=(SqlDbType.VarChar,2),
        ["address_line1"]=(SqlDbType.NVarChar,90), ["address_line2"]=(SqlDbType.NVarChar,90), ["phone_number"]=(SqlDbType.VarChar,16),
        ["email_address"]=(SqlDbType.VarChar,60), ["admission_date"]=(SqlDbType.Date,0), ["enrollment_status_code"]=(SqlDbType.VarChar,2),
        ["enrollment_end_date"]=(SqlDbType.Date,0), ["class_id"]=(SqlDbType.BigInt,0), ["emergency_contact_name"]=(SqlDbType.NVarChar,16),
        ["relationship_category"]=(SqlDbType.VarChar,24), ["relationship_code"]=(SqlDbType.VarChar,2), ["emergency_phone_number"]=(SqlDbType.VarChar,16), ["remarks"]=(SqlDbType.NVarChar,240)
    };
    public SqlServerStudentService(string connectionString, Func<CurrentUser> currentUser, bool webTokens = false, TimeProvider? clock = null, StudentDatabaseProfile databaseProfile = StudentDatabaseProfile.Native)
    {
        if (!Enum.IsDefined(databaseProfile)) throw new ArgumentOutOfRangeException(nameof(databaseProfile));
        _sharedAccess = databaseProfile == StudentDatabaseProfile.SharedAccess;
        if (_sharedAccess && !webTokens) throw new ArgumentException("SharedAccess requires Web-owned confirmation tokens; native DB token tables are not used.", nameof(webTokens));
        _connectionString = SharedAccessSchema.ConnectionString(connectionString,databaseProfile); _currentUser = currentUser; _webTokens = webTokens; _clock = clock ?? TimeProvider.System;
    }
    private DateTimeOffset Now => _clock.GetUtcNow();
    private static DateOnly BusinessDay(DateTimeOffset now) => DateOnly.FromDateTime(now.ToOffset(TimeSpan.FromHours(9)).DateTime);
    private CurrentUser User()
    {
        var user = _currentUser();
        StudentNormalizer.Text(user.Principal, 64, 64, "Principal", true);
        if (string.IsNullOrEmpty(user.SessionId) || !_webTokens && !Guid.TryParse(user.SessionId, out _)) throw new UnauthorizedAccessException("認証セッションが不正です。");
        return user;
    }
    private async Task<SqlConnection> Open(CancellationToken ct)
    {
        var connection = new SqlConnection(_connectionString);
        SharedAccessSchema.Register(connection,_sharedAccess);
        try {
            await connection.OpenAsync(ct);
            if (_sharedAccess) return connection;
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
        SharedAccessSchema.ConvertParameter(command.Connection,type,value,size,out type,out value,out size);
        if (value is DateOnly date) value = date.ToDateTime(TimeOnly.MinValue);
        var parameter = command.Parameters.Add(name, type);
        if (size != 0) parameter.Size = size;
        parameter.Value = value ?? DBNull.Value;
    }
    private static string? String(SqlDataReader reader, string column) => reader.IsDBNull(reader.GetOrdinal(column)) ? null : reader.GetString(reader.GetOrdinal(column));
    private static long Long(SqlDataReader reader, string column) => Convert.ToInt64(reader[column],CultureInfo.InvariantCulture);
    private static DateOnly Date(SqlDataReader reader, string column) => SharedAccessSchema.ReadDate(reader[column]);
    private static StudentRow Row(SqlDataReader reader) => new(
        Long(reader,"student_id"), String(reader,"student_no")!, String(reader,"student_name")!, String(reader,"student_name_kana")!, Date(reader,"birth_date"),
        reader.IsDBNull(reader.GetOrdinal("school_year")) ? null : Convert.ToInt32(reader["school_year"]), String(reader,"grade_name"), String(reader,"class_code"), String(reader,"class_name"),
        String(reader,"status_name"), (String(reader,"prefecture_name") ?? "[不整合]") + String(reader,"address_line1"), String(reader,"phone_number"), Date(reader,"admission_date"),
        SharedAccessSchema.ReadTimestamp(reader["updated_at"]), Long(reader,"row_version"));
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
        if (SharedAccessSchema.IsShared(connection)) {
            await using var guard=Command(connection,tx,"SET XACT_ABORT ON; UPDATE dbo.t_write_guard WITH (UPDLOCK,HOLDLOCK) SET lock_bit=~lock_bit WHERE guard_id=1;");
            if(await guard.ExecuteNonQueryAsync(ct)!=1) throw new InvalidOperationException("Shared DB write guard is missing.");
            return;
        }
        await using var command = Command(connection,tx,"""
            SET XACT_ABORT ON;
            DECLARE @result int;
            EXEC @result=sys.sp_getapplock @Resource=N'test-project1:student-write',@LockMode='Exclusive',
                 @LockOwner='Transaction',@LockTimeout=5000,@DbPrincipal='public';
            IF @result<0 THROW 51001,N'保存用ロックを取得できませんでした。',1;
            """);
        await command.ExecuteNonQueryAsync(ct);
    }
    // OP-PAGE deliberately omits registration-only personal information and sort-only columns.
    private const string ListSelect = """
        SELECT s.student_id,s.student_no,s.student_name,s.student_name_kana,s.birth_date,
               c.school_year,c.class_code,c.class_name,g.code_name grade_name,e.code_name status_name
          FROM dbo.m_student s
          LEFT JOIN dbo.m_class c ON c.class_id=s.class_id
          LEFT JOIN dbo.m_code g ON g.category_id=c.grade_category AND g.code_value=c.grade_code
          LEFT JOIN dbo.m_code e ON e.category_id=s.enrollment_category AND e.code_value=s.enrollment_status_code
        """;
    private static StudentListItem ListItem(SqlDataReader reader) => new(
        Long(reader,"student_id"), String(reader,"student_no")!, String(reader,"student_name")!, String(reader,"student_name_kana")!, Date(reader,"birth_date"),
        reader.IsDBNull(reader.GetOrdinal("school_year")) ? null : Convert.ToInt32(reader["school_year"]), String(reader,"grade_name"), String(reader,"class_code"), String(reader,"class_name"), String(reader,"status_name"));
    public async Task<SearchResult> SearchAsync(SearchCriteria criteria, CancellationToken ct = default)
    {
        _ = User(); var now = Now;
        try {
            if (criteria.Page < 1 || criteria.PageSize is not (20 or 50 or 100) || criteria.SortDirection is not ("asc" or "desc")) throw new ArgumentException("E-COM-003: ページ指定が不正です。");
            var order = criteria.SortKey switch { "studentNo" => "s.student_no", "name" => "s.name_key", "admissionDate" => "s.admission_date", "updatedAt" => "s.updated_at", _ => throw new ArgumentException("E-COM-003: 並び順が不正です。") };
            if (criteria.ClassId is <= 0 || (_sharedAccess && criteria.ClassId>int.MaxValue)) throw new ArgumentException("E-STU-010: クラスIDが不正です。");
            var statuses = criteria.StatusCodes;
            if (statuses is null || statuses.Length > 4 || statuses.Distinct(StringComparer.Ordinal).Count() != statuses.Length || statuses.Any(value => value is not ("01" or "02" or "03" or "04"))) throw new ArgumentException("E-STU-009: 在籍区分が不正です。");
            var no = criteria.StudentNoPrefix;
            var name = criteria.NameKey;
            if (no is not null && StudentNormalizer.Identifier(no,15,"StudentNo") != no || name is not null && (StudentNormalizer.ScalarCount(name)>160 || StudentNormalizer.NameKey(name)!=name))
                throw new ArgumentException("E-SRC-002: 正規化済み検索条件が不正です。");
            await using var connection = await Open(ct);
            await using var tx = (SqlTransaction)await connection.BeginTransactionAsync(_sharedAccess ? IsolationLevel.Serializable : IsolationLevel.Snapshot,ct);
            foreach (var status in statuses)
                if (!await CodeExists(connection,tx,"ENROLLMENT_STATUS",status,ct)) throw new ArgumentException("E-STU-009: 指定した在籍区分が存在しません。");
            if (criteria.ClassId is { } classId) {
                await using var classCheck = Command(connection,tx,"SELECT COUNT_BIG(*) FROM dbo.m_class WHERE class_id=@id");
                Param(classCheck,"@id",SqlDbType.BigInt,classId);
                if ((long)(await classCheck.ExecuteScalarAsync(ct))! != 1) throw new ArgumentException("E-STU-014: 指定クラスが存在しません。");
            }
            var predicates = new List<string>{ "s.is_deleted=0" };
            var parameters = new List<(string Name, SqlDbType Type, object? Value, int Size)>();
            void Where(string sql, string key, SqlDbType type, object? value, int size = 0) { if (value is not null) { predicates.Add(sql); parameters.Add((key,type,value,size)); } }
            Where("s.student_no LIKE @no ESCAPE '!'","@no",SqlDbType.VarChar,no is null ? null : StudentNormalizer.EscapeLike(no)+"%",31);
            Where("s.name_key LIKE @name ESCAPE '!'","@name",SqlDbType.NVarChar,name is null ? null : "%"+StudentNormalizer.EscapeLike(name)+"%",642);
            Where("s.class_id=@class","@class",SqlDbType.BigInt,criteria.ClassId);
            if(statuses.Length>0) {
                predicates.Add("s.enrollment_status_code IN ("+string.Join(',',statuses.Select((_,index)=>"@status"+index))+")");
                parameters.AddRange(statuses.Select((value,index)=>("@status"+index,SqlDbType.VarChar,(object?)value,2)));
            }
            var where = " WHERE "+string.Join(" AND ",predicates);
            await using var countCommand = Command(connection,tx,"SELECT COUNT_BIG(*) FROM (SELECT TOP (10001) s.student_id FROM dbo.m_student s"+where+") limited");
            foreach(var p in parameters) Param(countCommand,p.Name,p.Type,p.Value,p.Size);
            var count = (int)(long)(await countCommand.ExecuteScalarAsync(ct))!;
            if(count>10000) { await tx.CommitAsync(ct); return new(Outcome.NoChange,count,[],now,true,[]); }
            var lastPage = Math.Max(1,(count+criteria.PageSize-1)/criteria.PageSize);
            var page = Math.Min(criteria.Page,lastPage);
            await using var pageCommand = Command(connection,tx,ListSelect+where+" ORDER BY "+order+" "+criteria.SortDirection+",s.student_id ASC OFFSET @offset ROWS FETCH NEXT @size ROWS ONLY");
            foreach(var p in parameters) Param(pageCommand,p.Name,p.Type,p.Value,p.Size);
            Param(pageCommand,"@offset",SqlDbType.Int,checked((page-1)*criteria.PageSize)); Param(pageCommand,"@size",SqlDbType.Int,criteria.PageSize);
            var rows = new List<StudentListItem>();
            await using(var reader = await pageCommand.ExecuteReaderAsync(ct)) while(await reader.ReadAsync(ct)) rows.Add(ListItem(reader));
            await tx.CommitAsync(ct);
            return new(Outcome.NoChange,count,rows,now,false,[]);
        } catch(InputValidationException e) { return new(Outcome.ValidationFailed,0,[],now,false,e.Errors); }
        catch(ArgumentException e) { return new(Outcome.ValidationFailed,0,[],now,false,[StudentNormalizer.ArgumentError("Search",e)]); }
    }
    public async Task<StudentDetail?> GetAsync(long id, CancellationToken ct = default)
    {
        _ = User(); if (id <= 0 || (_sharedAccess && id>int.MaxValue)) return null;
        await using var connection = await Open(ct);
        await using var command = Command(connection,null,"SELECT * FROM dbo.m_student WHERE student_id=@id AND is_deleted=0");
        Param(command,"@id",SqlDbType.BigInt,id);
        await using var reader = await command.ExecuteReaderAsync(ct);
        if(!await reader.ReadAsync(ct)) return null;
        var values = Columns.Keys.ToDictionary(key=>key,key=>SharedAccessSchema.ReadValue(reader,key));
        return Detail(id,Long(reader,"row_version"),values,SharedAccessSchema.ReadTimestamp(reader["updated_at"]),String(reader,"updated_by")!);
    }
    private static StudentDetail Detail(long id,long version,Dictionary<string,object?> values,DateTimeOffset updated,string actor)
    {
        string? S(string key)=>values[key]?.ToString();
        DateOnly D(string key)=>SharedAccessSchema.ReadDate(values[key]!);
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
        await using var tx=(SqlTransaction)await connection.BeginTransactionAsync(_sharedAccess ? IsolationLevel.Serializable : IsolationLevel.Snapshot,ct);
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
            while(await reader.ReadAsync(ct)) classes.Add(new(Long(reader,"class_id"),Convert.ToInt32(reader["school_year"]),String(reader,"grade_code")!,String(reader,"class_code")!,String(reader,"class_name")!,Date(reader,"valid_from"),Date(reader,"valid_to"),reader.IsDBNull(reader.GetOrdinal("capacity"))?null:Convert.ToInt32(reader["capacity"]),Convert.ToInt32(reader["occupied"]),reader.GetBoolean(reader.GetOrdinal("is_active")),Convert.ToInt32(reader["display_order"])));
        }
        await tx.CommitAsync(ct); return new(codes,classes);
    }
    private static async Task<bool> CodeExists(SqlConnection connection,SqlTransaction tx,string category,string value,CancellationToken ct)
    {
        await using var command=Command(connection,tx,"SELECT COUNT_BIG(*) FROM dbo.m_code WHERE category_id=@category AND code_value=@value");
        Param(command,"@category",SqlDbType.VarChar,category,24); Param(command,"@value",SqlDbType.VarChar,value,10);
        return (long)(await command.ExecuteScalarAsync(ct))! == 1;
    }
    private static byte[] HashPayload(NormalizedStudent student) => SHA256.HashData(Encoding.UTF8.GetBytes(JsonSerializer.Serialize(Columns.Keys.Where(key=>key is not ("name_key" or "kana_key" or "relationship_category")).Select(key=>new KeyValuePair<string,object?>(key,student.Values[key])))));
    private static byte[] HashCandidates(IEnumerable<StudentRow> candidates) => SHA256.HashData(Encoding.UTF8.GetBytes(JsonSerializer.Serialize(candidates.Select(row=>new[]{row.StudentId,row.RowVersion}))));
    private static SaveResult Result(Outcome outcome,string code,string message,string requestId) => new(outcome,null,null,[new("",code,message)],RequestId:requestId);
    public async Task<SaveResult> SaveAsync(SaveRequest request,CancellationToken ct = default)
    {
        var requestId=Guid.NewGuid().ToString(); var user=User(); var now=Now; var day=BusinessDay(now);
        if(user.Role==Role.Viewer) return Result(Outcome.Forbidden,"E-COM-002","保存権限がありません。",requestId);
        NormalizedStudent student; string? reason;
        try {
            student=StudentNormalizer.Normalize(request.Draft,day);
            if(_sharedAccess && student.ClassId>int.MaxValue) throw new ArgumentException("E-STU-010: 共有DBのクラスID範囲を超えています。");
            reason=StudentNormalizer.Text(request.Reason,60,60,"Reason",multiline:true);
            if(request.StudentId is <=0 || request.ExpectedVersion is <=0 || (_sharedAccess && (request.StudentId>int.MaxValue || request.ExpectedVersion>int.MaxValue)) || (request.StudentId is null)!=(request.ExpectedVersion is null)) throw new ArgumentException("E-COM-003: 学生ID/版が不正です。");
            if(request.SchoolYear is <1900 or >9998) throw new ArgumentException("E-DATE-003: 年度が不正です。");
            request=request with { GradeCode=StudentNormalizer.Code(request.GradeCode,2,"GradeCode",false) };
        } catch(InputValidationException e) { return new(Outcome.ValidationFailed,null,null,e.Errors,RequestId:requestId); }
        catch(ArgumentException e) { return new(Outcome.ValidationFailed,null,null,[StudentNormalizer.ArgumentError("Save",e)],RequestId:requestId); }
        var writeStarted=false; var commitAttempted=false; var completed=false; var unknown=false; Confirmation? claimed=null;
        await using var connection=await Open(ct);
        await using var tx=(SqlTransaction)await connection.BeginTransactionAsync(IsolationLevel.ReadCommitted,ct);
        try {
            await Gate(connection,tx,ct);
            Dictionary<string,object?>? previous=null; long? previousVersion=null;
            if(request.StudentId is { } existing) {
                await using var load=Command(connection,tx,"SELECT * FROM dbo.m_student WHERE student_id=@id AND is_deleted=0");
                Param(load,"@id",SqlDbType.BigInt,existing);
                await using var reader=await load.ExecuteReaderAsync(ct);
                if(!await reader.ReadAsync(ct)) return Result(Outcome.NotFound,"E-STU-103","対象学生が存在しません。",requestId);
                previousVersion=Long(reader,"row_version");
                if(previousVersion!=request.ExpectedVersion) return Result(Outcome.Conflict,"E-STU-105","他の利用者が変更しています。再読込してください。",requestId);
                previous=Columns.Keys.ToDictionary(key=>key,key=>SharedAccessSchema.ReadValue(reader,key));
                if((string)previous["student_no"]! != student.Text("student_no")) return Result(Outcome.ValidationFailed,"E-STU-104","学籍番号は変更できません。",requestId);
                if((string)previous["enrollment_status_code"]! is "03" or "04" && !Equals(previous["enrollment_status_code"],student.Values["enrollment_status_code"])) {
                    if(user.Role!=Role.Administrator) return Result(Outcome.Forbidden,"E-COM-002","終了区分の訂正は管理者権限が必要です。",requestId);
                    if(reason is null) return Result(Outcome.ValidationFailed,"E-STU-106","終了区分の訂正理由を入力してください。",requestId);
                }
            }
            await CheckRules(connection,tx,student,previous,request,day,ct);
            var changed=student.Values.Where(pair=>previous is null || !EqualValue(pair.Value,previous[pair.Key])).Select(pair=>pair.Key).ToArray();
            if(changed.Length==0) { await tx.RollbackAsync(ct); return new(Outcome.NoChange,request.StudentId,previousVersion,[],RequestId:requestId); }
            if(previousVersion==MaximumVersion) return Result(Outcome.Conflict,"E-STU-105","更新管理番号が上限に到達しました。",requestId);
            await using(var number=Command(connection,tx,"SELECT COUNT_BIG(*) FROM dbo.m_student WHERE student_no=@no AND (@id IS NULL OR student_id<>@id)")) {
                Param(number,"@no",SqlDbType.VarChar,student.Text("student_no"),15); Param(number,"@id",SqlDbType.BigInt,request.StudentId);
                if((long)(await number.ExecuteScalarAsync(ct))!>0) return Result(Outcome.ValidationFailed,"E-STU-101","学籍番号は使用済みです。",requestId);
            }
            var candidates=new List<StudentRow>();
            await using(var duplicate=Command(connection,tx,RowSelect+" WHERE s.is_deleted=0 AND (@id IS NULL OR s.student_id<>@id) AND s.birth_date=@birth AND (s.name_key=@name OR s.kana_key=@kana) ORDER BY s.student_id")) {
                Param(duplicate,"@id",SqlDbType.BigInt,request.StudentId); Param(duplicate,"@birth",SqlDbType.Date,student.Date("birth_date"));
                Param(duplicate,"@name",SqlDbType.NVarChar,student.Text("name_key"),320); Param(duplicate,"@kana",SqlDbType.NVarChar,student.Text("kana_key"),36);
                await using var reader=await duplicate.ExecuteReaderAsync(ct); while(await reader.ReadAsync(ct)) candidates.Add(Row(reader));
            }
            var payload=HashPayload(student); var candidateHash=HashCandidates(candidates);
            var confirmationValid=false;
            if(request.ConfirmationToken is { } supplied) {
                if(_webTokens) {
                    if(WebConfirmations.TryGetValue(supplied,out var value) && value.Owner.Principal==user.Principal && value.Owner.SessionId==user.SessionId && value.Id==request.StudentId && value.Version==request.ExpectedVersion && value.Expires>now && CryptographicOperations.FixedTimeEquals(value.Payload,payload) && CryptographicOperations.FixedTimeEquals(value.Candidates,candidateHash) && Interlocked.CompareExchange(ref value.Busy,1,0)==0) { claimed=value; confirmationValid=true; }
                } else if(Guid.TryParse(supplied,out var token)) {
                    await using var check=Command(connection,tx,"SELECT payload_hash,candidate_hash FROM dbo.t_confirmation WITH (UPDLOCK) WHERE token=@token AND principal=@actor AND session_id=@session AND ((target_id IS NULL AND @id IS NULL) OR target_id=@id) AND ((expected_version IS NULL AND @version IS NULL) OR expected_version=@version) AND expires_at>@now AND consumed=0");
                    Param(check,"@token",SqlDbType.UniqueIdentifier,token); Param(check,"@actor",SqlDbType.NVarChar,user.Principal,128); Param(check,"@session",SqlDbType.UniqueIdentifier,Guid.Parse(user.SessionId)); Param(check,"@id",SqlDbType.BigInt,request.StudentId); Param(check,"@version",SqlDbType.BigInt,request.ExpectedVersion); Param(check,"@now",SqlDbType.DateTimeOffset,now);
                    await using var reader=await check.ExecuteReaderAsync(ct);
                    confirmationValid=await reader.ReadAsync(ct) && CryptographicOperations.FixedTimeEquals((byte[])reader[0],payload) && CryptographicOperations.FixedTimeEquals((byte[])reader[1],candidateHash);
                }
            }
            if(confirmationValid && reason is null) return Result(Outcome.ValidationFailed,"E-STU-107","重複登録を続ける理由を入力してください。",requestId);
            if((candidates.Count>0 || request.ConfirmationToken is not null) && !confirmationValid) {
                await tx.RollbackAsync(ct);
                var token=await IssueConfirmation(connection,user,request,payload,candidateHash,now,ct);
                return new(Outcome.ConfirmationRequired,request.StudentId,previousVersion,[],token,candidates.Count,candidates.Take(20).ToArray(),requestId);
            }
            long id; var version=(previousVersion??0)+1;
            var insert=request.StudentId is null;
            var writeColumns=student.Values.Keys.Where(key=>insert || key!="student_no").ToArray();
            var sql=insert
                ? "DECLARE @changed TABLE(student_id bigint); INSERT INTO dbo.m_student ("+string.Join(',',writeColumns)+",gender_category,prefecture_category,enrollment_category,is_deleted,created_at,created_by,updated_at,updated_by,row_version) OUTPUT INSERTED.student_id INTO @changed VALUES ("+string.Join(',',writeColumns.Select(key=>"@"+key))+",'GENDER','PREFECTURE','ENROLLMENT_STATUS',0,@now,@actor,@now,@actor,1); SELECT student_id FROM @changed;"
                : "DECLARE @changed TABLE(student_id bigint); UPDATE dbo.m_student SET "+string.Join(',',writeColumns.Select(key=>key+"=@"+key))+",updated_at=@now,updated_by=@actor,row_version=row_version+1 OUTPUT INSERTED.student_id INTO @changed WHERE student_id=@id AND row_version=@version AND is_deleted=0; SELECT student_id FROM @changed;";
            await using(var save=Command(connection,tx,sql)) {
                foreach(var key in writeColumns) Param(save,"@"+key,Columns[key].Type,student.Values[key],Columns[key].Size);
                Param(save,"@now",SqlDbType.DateTimeOffset,now); Param(save,"@actor",SqlDbType.NVarChar,user.Principal,128);
                if(!insert) { Param(save,"@id",SqlDbType.BigInt,request.StudentId); Param(save,"@version",SqlDbType.BigInt,request.ExpectedVersion); }
                writeStarted=true; var saved=await save.ExecuteScalarAsync(ct);
                if(saved is null || saved is DBNull) throw new DBConcurrencyException();
                id=Convert.ToInt64(saved,CultureInfo.InvariantCulture);
            }
            var auditChanged=insert ? writeColumns.Concat(new[]{"gender_category","prefecture_category","enrollment_category","is_deleted","created_at","created_by","updated_at","updated_by","row_version"}).ToArray() : changed.Concat(new[]{"updated_at","updated_by","row_version"}).ToArray();
            await Audit(connection,tx,id,insert?"CREATE":"UPDATE",previousVersion,version,auditChanged,user.Principal,now,reason,candidates.Count>0,Guid.Parse(requestId),ct);
            if(confirmationValid && !_webTokens) {
                await using var consume=Command(connection,tx,"UPDATE dbo.t_confirmation SET consumed=1 WHERE token=@token AND consumed=0");
                Param(consume,"@token",SqlDbType.UniqueIdentifier,Guid.Parse(request.ConfirmationToken!));
                if(await consume.ExecuteNonQueryAsync(ct)!=1) throw new DBConcurrencyException();
            }
            commitAttempted=true; await tx.CommitAsync(ct); completed=true;
            if(request.ConfirmationToken is { } consumed) WebConfirmations.TryRemove(consumed,out _);
            return new(Outcome.Saved,id,version,[],RequestId:requestId);
        } catch(InputValidationException e) { await Rollback(tx); return new(Outcome.ValidationFailed,null,null,e.Errors,RequestId:requestId); }
        catch(SqlException e) when(e.Number is 2601 or 2627) { await Rollback(tx); return Result(Outcome.ValidationFailed,"E-STU-101","学籍番号は使用済みです。",requestId); }
        catch(DBConcurrencyException) { await Rollback(tx); return Result(Outcome.Conflict,"E-STU-105","他の利用者が変更しています。",requestId); }
        catch(Exception e) when(e is SqlException or InvalidOperationException or OperationCanceledException) {
            var rolledBack=await Rollback(tx); unknown=writeStarted&&(commitAttempted||!rolledBack);
            if(unknown && request.ConfirmationToken is { } invalid) WebConfirmations.TryRemove(invalid,out _);
            return Result(unknown?Outcome.Unknown:Outcome.SystemError,"E-COM-004",unknown?"保存結果を確認できません。再保存の前に検索で確認してください。":"処理に失敗しました。受付番号："+requestId,requestId);
        } finally { if(claimed is not null && !completed && !unknown) Interlocked.Exchange(ref claimed.Busy,0); }
    }
    private static bool EqualValue(object? a,object? b) {
        if(a is DateOnly date && b is DateTime time) return date==DateOnly.FromDateTime(time);
        return Equals(a,b);
    }
    internal static async Task<bool> Rollback(SqlTransaction tx) { try { await tx.RollbackAsync(CancellationToken.None); return true; } catch(SqlException) { return false; } catch(InvalidOperationException) { return false; } }
    private async Task<string> IssueConfirmation(SqlConnection connection,CurrentUser user,SaveRequest request,byte[] payload,byte[] candidates,DateTimeOffset now,CancellationToken ct)
    {
        if(_webTokens) {
            foreach(var expired in WebConfirmations.Where(pair=>pair.Value.Expires<=now)) WebConfirmations.TryRemove(expired.Key,out _);
            var token=Convert.ToHexString(RandomNumberGenerator.GetBytes(32)).ToLowerInvariant();
            WebConfirmations[token]=new(user,request.StudentId,request.ExpectedVersion,payload,candidates,now.AddMinutes(10)); return token;
        }
        var id=Guid.NewGuid();
        await using var tx=(SqlTransaction)await connection.BeginTransactionAsync(IsolationLevel.ReadCommitted,ct);
        await using var command=Command(connection,tx,"INSERT INTO dbo.t_confirmation (token,principal,session_id,target_id,expected_version,payload_hash,candidate_hash,expires_at,consumed) VALUES (@token,@actor,@session,@id,@version,@payload,@candidates,@expires,0)");
        Param(command,"@token",SqlDbType.UniqueIdentifier,id); Param(command,"@actor",SqlDbType.NVarChar,user.Principal,128); Param(command,"@session",SqlDbType.UniqueIdentifier,Guid.Parse(user.SessionId));
        Param(command,"@id",SqlDbType.BigInt,request.StudentId); Param(command,"@version",SqlDbType.BigInt,request.ExpectedVersion); Param(command,"@payload",SqlDbType.Binary,payload,32); Param(command,"@candidates",SqlDbType.Binary,candidates,32); Param(command,"@expires",SqlDbType.DateTimeOffset,now.AddMinutes(10));
        await command.ExecuteNonQueryAsync(ct); await tx.CommitAsync(ct); return id.ToString();
    }
    private static async Task CheckRules(SqlConnection connection,SqlTransaction tx,NormalizedStudent student,Dictionary<string,object?>? previous,SaveRequest request,DateOnly day,CancellationToken ct)
    {
        var errors=new List<FieldError>();
        foreach(var (column,category) in new[]{("gender_code","GENDER"),("prefecture_code","PREFECTURE"),("enrollment_status_code","ENROLLMENT_STATUS"),("relationship_code","RELATIONSHIP")}) {
            if(student.Values[column] is not string value) continue;
            await using var check=Command(connection,tx,"SELECT c.is_active,k.is_active,c.valid_from,c.valid_to FROM dbo.m_code c JOIN dbo.m_code_category k ON k.category_id=c.category_id WHERE c.category_id=@category AND c.code_value=@value");
            Param(check,"@category",SqlDbType.VarChar,category,24); Param(check,"@value",SqlDbType.VarChar,value,10);
            await using var reader=await check.ExecuteReaderAsync(ct);
            if(!await reader.ReadAsync(ct)) errors.Add(new(StudentNormalizer.PropertyNames[column],"E-STU-009","コードが存在しません。"));
            else if(previous is null || !Equals(previous[column],value)) {
                if(!reader.GetBoolean(0) || !reader.GetBoolean(1) || SharedAccessSchema.ReadDate(reader.GetValue(2))>day || !reader.IsDBNull(3)&&SharedAccessSchema.ReadDate(reader.GetValue(3))<day) errors.Add(new(StudentNormalizer.PropertyNames[column],"E-STU-011","コードは現在使用できません。"));
            }
        }
        var oldClass=(long?)previous?.GetValueOrDefault("class_id");
        var oldStatus=(string?)previous?.GetValueOrDefault("enrollment_status_code");
        var status=student.Text("enrollment_status_code");
        var oldSeat=oldClass is not null && oldStatus is "01" or "02";
        var newSeat=student.ClassId is not null && status is "01" or "02";
        if(student.ClassId is { } classId) {
            await using var command=Command(connection,tx,"SELECT school_year,grade_code,valid_from,valid_to,is_active,capacity FROM dbo.m_class WHERE class_id=@id");
            Param(command,"@id",SqlDbType.BigInt,classId);
            int? capacity=null;
            await using(var reader=await command.ExecuteReaderAsync(ct)) {
                if(!await reader.ReadAsync(ct)) errors.Add(new("ClassId","E-STU-010","指定クラスが存在しません。"));
                else {
                    var start=SharedAccessSchema.ReadDate(reader.GetValue(2)); var end=SharedAccessSchema.ReadDate(reader.GetValue(3));
                    capacity=reader.IsDBNull(5)?null:reader.GetInt32(5);
                    if(request.SchoolYear is not null&&Convert.ToInt32(reader[0])!=request.SchoolYear || request.GradeCode is not null&&reader.GetString(1)!=request.GradeCode) errors.Add(new("ClassId","E-STU-014","年度・学年・クラスが一致しません。"));
                    var changedPeriod=previous is null || oldClass!=classId || oldStatus!=status || !EqualValue(student.Values["admission_date"],previous["admission_date"]) || !EqualValue(student.Values["enrollment_end_date"],previous["enrollment_end_date"]);
                    if(newSeat&&(!oldSeat||oldClass!=classId)&&(!reader.GetBoolean(4)||day<start||day>end)) errors.Add(new("ClassId","E-STU-013","このクラスには新たに所属できません。"));
                    if(status is "03" or "04"&&changedPeriod&&(student.Date("admission_date")>end||(DateOnly?)student.Values["enrollment_end_date"]<start)) errors.Add(new("ClassId","E-STU-108","在籍期間とクラス期間が重なりません。"));
                }
            }
            if(newSeat&&(!oldSeat||oldClass!=classId)&&capacity is not null) {
                await using var count=Command(connection,tx,"SELECT COUNT_BIG(*) FROM dbo.m_student WHERE class_id=@class AND is_deleted=0 AND enrollment_status_code IN ('01','02') AND (@id IS NULL OR student_id<>@id)");
                Param(count,"@class",SqlDbType.BigInt,classId); Param(count,"@id",SqlDbType.BigInt,request.StudentId);
                if((long)(await count.ExecuteScalarAsync(ct))!+1>capacity) errors.Add(new("ClassId","E-STU-102","クラス定員を超えています。"));
            }
        }
        if(errors.Count>0) throw new InputValidationException(errors);
    }
    private static async Task Audit(SqlConnection connection,SqlTransaction tx,long id,string operation,long? before,long after,string[] changed,string actor,DateTimeOffset now,string? reason,bool confirmed,Guid requestId,CancellationToken ct)
    {
        await using var command=Command(connection,tx,"INSERT INTO dbo.t_operation_log (target_table,target_key,operation_type,before_version,after_version,changed_columns,executed_by,executed_at,correlation_id,operation_reason,duplicate_confirmed) VALUES ('m_student',@id,@op,@before,@after,@changed,@actor,@now,@request,@reason,@confirmed)");
        Param(command,"@id",SqlDbType.VarChar,id.ToString(CultureInfo.InvariantCulture),35); Param(command,"@op",SqlDbType.VarChar,operation,11); Param(command,"@before",SqlDbType.BigInt,before); Param(command,"@after",SqlDbType.BigInt,after);
        Param(command,"@changed",SqlDbType.NVarChar,JsonSerializer.Serialize(changed),-1); Param(command,"@actor",SqlDbType.NVarChar,actor,128); Param(command,"@now",SqlDbType.DateTimeOffset,now); Param(command,"@request",SqlDbType.UniqueIdentifier,requestId); Param(command,"@reason",SqlDbType.NVarChar,reason,120); Param(command,"@confirmed",SqlDbType.Bit,confirmed);
        await command.ExecuteNonQueryAsync(ct);
    }
    public async Task<SaveResult> DeleteAsync(long id,long version,string reason,CancellationToken ct = default)
    {
        var requestId=Guid.NewGuid().ToString(); var user=User(); var now=Now;
        if(user.Role!=Role.Administrator) return Result(Outcome.Forbidden,"E-COM-002","削除権限がありません。",requestId);
        try { reason=StudentNormalizer.Text(reason,60,60,"DeleteReason",true,true)!; }
        catch(InputValidationException e) { return new(Outcome.ValidationFailed,null,null,e.Errors,RequestId:requestId); }
        if(id<=0||(_sharedAccess&&id>int.MaxValue)||version<=0||version>=MaximumVersion) return Result(Outcome.ValidationFailed,"E-COM-003","学生ID/版が不正です。",requestId);
        await using var connection=await Open(ct);
        await using var tx=(SqlTransaction)await connection.BeginTransactionAsync(IsolationLevel.ReadCommitted,ct);
        var writeStarted=false; var commitAttempted=false;
        try {
            await Gate(connection,tx,ct);
            await using(var load=Command(connection,tx,"SELECT row_version FROM dbo.m_student WHERE student_id=@id AND is_deleted=0")) {
                Param(load,"@id",SqlDbType.BigInt,id); var saved=await load.ExecuteScalarAsync(ct);
                if(saved is null) return Result(Outcome.NotFound,"E-STU-103","対象学生が存在しません。",requestId);
                if(Convert.ToInt64(saved,CultureInfo.InvariantCulture)!=version) return Result(Outcome.Conflict,"E-STU-105","他の利用者が変更しています。",requestId);
            }
            await using(var command=Command(connection,tx,"UPDATE dbo.m_student SET is_deleted=1,deleted_at=@now,deleted_by=@actor,delete_reason=@reason,updated_at=@now,updated_by=@actor,row_version=row_version+1 WHERE student_id=@id AND row_version=@version AND is_deleted=0")) {
                Param(command,"@id",SqlDbType.BigInt,id); Param(command,"@version",SqlDbType.BigInt,version); Param(command,"@now",SqlDbType.DateTimeOffset,now); Param(command,"@actor",SqlDbType.NVarChar,user.Principal,128); Param(command,"@reason",SqlDbType.NVarChar,reason,120);
                writeStarted=true; if(await command.ExecuteNonQueryAsync(ct)!=1) throw new DBConcurrencyException();
            }
            await Audit(connection,tx,id,"DELETE",version,version+1,["is_deleted","deleted_at","deleted_by","delete_reason","updated_at","updated_by","row_version"],user.Principal,now,reason,false,Guid.Parse(requestId),ct);
            commitAttempted=true; await tx.CommitAsync(ct); return new(Outcome.Saved,id,version+1,[],RequestId:requestId);
        } catch(DBConcurrencyException) { await Rollback(tx); return Result(Outcome.Conflict,"E-STU-105","他の利用者が変更しています。",requestId); }
        catch(Exception e) when(e is SqlException or InvalidOperationException or OperationCanceledException) { var rolledBack=await Rollback(tx); var unknown=writeStarted&&(commitAttempted||!rolledBack); return Result(unknown?Outcome.Unknown:Outcome.SystemError,"E-COM-004",unknown?"削除結果を確認できません。検索で確認してください。":"削除処理に失敗しました。受付番号："+requestId,requestId); }
    }
}

// The shared DB keeps Access's ISO text dates, INT identities/versions and UTC
// datetime2 audit values. Convert only at the persistence boundary; public Web
// contracts remain Int64/DateOnly/DateTimeOffset and business limits stay intact.
internal static class SharedAccessSchema
{
    private sealed record Profile(bool Shared);
    private static readonly ConditionalWeakTable<SqlConnection,Profile> Profiles = new();
    internal static void Register(SqlConnection connection,bool shared) => Profiles.Add(connection,new(shared));
    internal static bool IsShared(SqlConnection? connection) => connection is not null && Profiles.TryGetValue(connection,out var profile) && profile.Shared;
    internal static string ConnectionString(string value,StudentDatabaseProfile profile)
    {
        var builder=new SqlConnectionStringBuilder(value){Encrypt=SqlConnectionEncryptOption.Mandatory};
        if(profile!=StudentDatabaseProfile.SharedAccess) builder.TrustServerCertificate=false;
        else if(builder.TrustServerCertificate && !new[]{@".\SQLEXPRESS",@"localhost\SQLEXPRESS",@"127.0.0.1\SQLEXPRESS"}.Contains(builder.DataSource,StringComparer.OrdinalIgnoreCase))
            throw new ArgumentException("SharedAccess certificate bypass is restricted to the explicit local SQLEXPRESS instance.");
        return builder.ConnectionString;
    }
    internal static void ConvertParameter(SqlConnection? connection,SqlDbType requested,object? source,int requestedSize,out SqlDbType type,out object? value,out int size)
    {
        type=requested;value=source;size=requestedSize;
        if(!IsShared(connection))return;
        switch(requested)
        {
            case SqlDbType.BigInt:
                type=SqlDbType.Int;
                if(source is not null && source is not DBNull)value=checked(Convert.ToInt32(source,CultureInfo.InvariantCulture));
                break;
            case SqlDbType.Date:
                type=SqlDbType.NVarChar;size=10;
                if(source is not null && source is not DBNull)value=ReadDate(source).ToString("yyyy-MM-dd",CultureInfo.InvariantCulture);
                break;
            case SqlDbType.DateTimeOffset:
                type=SqlDbType.DateTime2;
                if(source is DateTimeOffset instant)value=instant.UtcDateTime;
                break;
            case SqlDbType.UniqueIdentifier:
                type=SqlDbType.NVarChar;size=36;
                if(source is Guid id)value=id.ToString("D");
                break;
            case SqlDbType.VarChar: type=SqlDbType.NVarChar;break;
        }
    }
    internal static DateOnly ReadDate(object value) => value switch
    {
        DateOnly day=>day,
        DateTime timestamp=>DateOnly.FromDateTime(timestamp),
        string text=>DateOnly.ParseExact(text,"yyyy-MM-dd",CultureInfo.InvariantCulture),
        _=>throw new InvalidOperationException("Unexpected SQL date representation.")
    };
    internal static DateTimeOffset ReadTimestamp(object value) => value switch
    {
        DateTimeOffset instant=>instant.ToUniversalTime(),
        DateTime timestamp=>new DateTimeOffset(DateTime.SpecifyKind(timestamp,DateTimeKind.Utc)),
        _=>throw new InvalidOperationException("Unexpected SQL audit timestamp representation.")
    };
    internal static object? ReadValue(SqlDataReader reader,string column)
    {
        var value=reader[column];
        if(value is DBNull)return null;
        if(column is "birth_date" or "admission_date" or "enrollment_end_date" or "valid_from" or "valid_to")return ReadDate(value);
        if(column is "student_id" or "class_id" or "row_version")return Convert.ToInt64(value,CultureInfo.InvariantCulture);
        return value;
    }
}
