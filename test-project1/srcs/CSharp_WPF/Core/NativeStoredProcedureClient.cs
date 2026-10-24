using System.Data;
using System.Globalization;
using System.Text;
using System.Xml;
using Microsoft.Data.SqlClient;

namespace StudentManagement.Core;

// Caller owns the Connection, Transaction, commit/rollback, and Unknown handling.
// Saved is provisional; ConfirmationRequired must be committed before UI waiting.
public static class NativeStoredProcedureClient
{
    public const string PrepareProcedure = "student_api.prepare_save";
    public const string PersistProcedure = "student_api.persist_student";
    public const string DeleteProcedure = "student_api.delete_student";
    private sealed record Response(string State, SaveResult Result);
    public static Task<MaintenanceResult> SaveClassAsync(SqlConnection c,SqlTransaction tx,ClassChange change,
        Guid requestId,string? rawReason=null,CancellationToken ct=default)
        => SerializeMaster(c,tx,"student_api.save_class",()=>SerializeClass(change,rawReason),change.ClassId,change.ExpectedVersion,requestId,ct);
    public static Task<MaintenanceResult> SaveCodeAsync(SqlConnection c,SqlTransaction tx,CodeChange change,
        Guid requestId,string? rawReason=null,CancellationToken ct=default)
        => SerializeMaster(c,tx,"student_api.save_code",()=>SerializeCode(change,rawReason),null,change.ExpectedVersion,requestId,ct);
    private static Task<MaintenanceResult> SerializeMaster(SqlConnection c,SqlTransaction tx,string procedure,Func<string> serialize,
        long? id,long? version,Guid requestId,CancellationToken ct)
    {
        string raw;
        try {raw=serialize();}
        catch(Exception e) when(e is ArgumentException or XmlException) {
            return Task.FromResult(new MaintenanceResult(Outcome.ValidationFailed,null,NativeMessages.Resolve("E-STU-002",requestId:requestId)));
        }
        return Master(c,tx,procedure,raw,id,version,requestId,ct);
    }
    private static async Task<MaintenanceResult> Master(SqlConnection c,SqlTransaction tx,string procedure,string raw,
        long? id,long? version,Guid requestId,CancellationToken ct)
    {
        ValidateTransaction(c,tx);
        await using var command=Stored(c,tx,procedure);
        Parameter(command,"@raw",SqlDbType.NVarChar,raw,-1);
        if(procedure=="student_api.save_class")Parameter(command,"@target_id",SqlDbType.BigInt,id);
        Parameter(command,"@expected_version",SqlDbType.BigInt,version);Parameter(command,"@request_id",SqlDbType.UniqueIdentifier,requestId);
        try {
            await using var reader=await command.ExecuteReaderAsync(ct);
            if(!await reader.ReadAsync(ct))throw new InvalidOperationException("Native master procedure returned no status.");
            var state=reader.GetString(reader.GetOrdinal("outcome"));
            var outcome=Enum.TryParse<Outcome>(state,out var parsed)?parsed:Outcome.SystemError;
            var code=Text(reader,"code")??"E-COM-004";var field=Text(reader,"field")??"";
            var after=Long(reader,"row_version");var same=reader.GetBoolean(reader.GetOrdinal("same_name_warning"));
            var maximum=reader.IsDBNull(reader.GetOrdinal("max_length"))?(int?)null:reader.GetInt32(reader.GetOrdinal("max_length"));
            var message=outcome==Outcome.Saved&&!same?(procedure=="student_api.save_class"?"クラスを保存しました。":"コードを保存しました。"):NativeMessages.Resolve(code,field,maximum,requestId);
            return new(outcome,after,message,same);
        } catch(SqlException e) when(e.Number is 2601 or 2627 or 547 or 1205 or 1222 or 3960 or 51001 or 51005 or 229) {
            var code=e.Number is 2601 or 2627?"E-MST-002":e.Number==547?"E-STU-009":e.Number==229?"E-COM-002":"E-STU-105";
            return new(e.Number==229?Outcome.Forbidden:e.Number is 1205 or 1222 or 3960 or 51001 or 51005?Outcome.Conflict:Outcome.ValidationFailed,null,NativeMessages.Resolve(code,requestId:requestId));
        }
    }

    public static async Task<SaveResult> SaveAsync(SqlConnection c, SqlTransaction tx, SaveRequest request,
        Guid sessionId, Guid requestId, CancellationToken ct = default)
    {
        ValidateTransaction(c, tx);
        Guid? token = null;
        if (request.ConfirmationToken is { } text) {
            if (!Guid.TryParse(text, out var parsed)) return Failure(Outcome.ValidationFailed,"E-COM-003","ConfirmationToken",requestId);
            token = parsed;
        }
        string raw;
        try { raw = SerializeRaw(request); }
        catch (ArgumentException) { return Failure(Outcome.ValidationFailed,"E-STU-002","Save",requestId); }
        catch (XmlException) { return Failure(Outcome.ValidationFailed,"E-STU-002","Save",requestId); }
        try {
            var prepared = await SaveProcedure(c,tx,PrepareProcedure,raw,request,sessionId,token,requestId,ct);
            if (prepared.State != "Ready") return prepared.Result;
            // Persist repeats normalization/role/gate/latest rules and full confirmation comparison.
            return (await SaveProcedure(c,tx,PersistProcedure,raw,request,sessionId,token,requestId,ct)).Result;
        } catch (SqlException e) when (KnownFailure(e,requestId) is not null) { return KnownFailure(e,requestId)!; }
    }
    public static async Task<SaveResult> DeleteAsync(SqlConnection c, SqlTransaction tx, long id, long version,
        string rawReason, Guid sessionId, Guid requestId, CancellationToken ct = default)
    {
        ValidateTransaction(c,tx);
        await using var command = Stored(c,tx,DeleteProcedure);
        Parameter(command,"@target_id",SqlDbType.BigInt,id);
        Parameter(command,"@expected_version",SqlDbType.BigInt,version);
        Parameter(command,"@raw_reason",SqlDbType.NVarChar,rawReason,-1);
        Parameter(command,"@session_id",SqlDbType.UniqueIdentifier,sessionId);
        Parameter(command,"@request_id",SqlDbType.UniqueIdentifier,requestId);
        try { return (await Read(command,requestId,ct)).Result; }
        catch (SqlException e) when (KnownFailure(e,requestId) is not null) { return KnownFailure(e,requestId)!; }
    }
    private static void ValidateTransaction(SqlConnection c, SqlTransaction tx)
    {
        if (c.State != ConnectionState.Open || !ReferenceEquals(tx.Connection,c))
            throw new InvalidOperationException("Native procedure requires caller's open connection/transaction.");
        if (tx.IsolationLevel != IsolationLevel.ReadCommitted)
            throw new InvalidOperationException("Native caller transaction must be READ COMMITTED.");
    }
    private static SqlCommand Stored(SqlConnection c,SqlTransaction tx,string name)
        => new(name,c,tx) { CommandType=CommandType.StoredProcedure,CommandTimeout=30 };
    private static void Parameter(SqlCommand cmd,string name,SqlDbType type,object? value,int size=0)
    {
        var p=cmd.Parameters.Add(name,type); if(size!=0)p.Size=size; p.Value=value??DBNull.Value;
    }
    private static async Task<Response> SaveProcedure(SqlConnection c,SqlTransaction tx,string name,string raw,
        SaveRequest request,Guid sessionId,Guid? token,Guid requestId,CancellationToken ct)
    {
        await using var command=Stored(c,tx,name);
        Parameter(command,"@raw",SqlDbType.NVarChar,raw,-1);
        Parameter(command,"@target_id",SqlDbType.BigInt,request.StudentId);
        Parameter(command,"@expected_version",SqlDbType.BigInt,request.ExpectedVersion);
        Parameter(command,"@session_id",SqlDbType.UniqueIdentifier,sessionId);
        Parameter(command,"@confirmation_token",SqlDbType.UniqueIdentifier,token);
        Parameter(command,"@request_id",SqlDbType.UniqueIdentifier,requestId);
        return await Read(command,requestId,ct);
    }
    private static string? Text(SqlDataReader reader,string key)
        => reader.IsDBNull(reader.GetOrdinal(key))?null:reader.GetString(reader.GetOrdinal(key));
    private static long? Long(SqlDataReader reader,string key)
        => reader.IsDBNull(reader.GetOrdinal(key))?null:reader.GetInt64(reader.GetOrdinal(key));
    private static async Task<Response> Read(SqlCommand command,Guid requestId,CancellationToken ct)
    {
        await using var reader=await command.ExecuteReaderAsync(ct);
        if (!await reader.ReadAsync(ct)) throw new InvalidOperationException("Native procedure returned no status.");
        var state=reader.GetString(reader.GetOrdinal("outcome"));
        var outcome=state=="Ready"?Outcome.NoChange:Enum.TryParse<Outcome>(state,out var parsed)?parsed:Outcome.SystemError;
        var id=Long(reader,"student_id");var version=Long(reader,"row_version");
        var token=reader.IsDBNull(reader.GetOrdinal("confirmation_token"))?null:reader.GetGuid(reader.GetOrdinal("confirmation_token")).ToString();
        var count=reader.GetInt32(reader.GetOrdinal("candidate_count"));var code=Text(reader,"code");var field=Text(reader,"field")??"";
        if(StudentNormalizer.PropertyNames.TryGetValue(field,out var property))field=property;
        else field=field switch {"reason"=>"Reason","school_year"=>"SchoolYear","grade_code"=>"GradeCode",_=>field};
        var maximum=reader.IsDBNull(reader.GetOrdinal("max_length"))?(int?)null:reader.GetInt32(reader.GetOrdinal("max_length"));
        var errors=code?.StartsWith("E-",StringComparison.Ordinal)==true?new[]{new FieldError(field,code,NativeMessages.Resolve(code,field,maximum,requestId))}:[];
        var candidates=new List<StudentRow>();
        if(await reader.NextResultAsync(ct))while(await reader.ReadAsync(ct)) {
            candidates.Add(ReadDuplicateCandidate(reader));
        }
        return new(state,new(outcome,id,version,errors,token,count,candidates,requestId.ToString()));
    }
    // Duplicate UI is limited to number, name, wareki birth date and class.
    // Candidate IDs/versions remain inside the server confirmation hash.
    public static StudentRow ReadDuplicateCandidate(IDataRecord row)
    {
        var classOrdinal=row.GetOrdinal("class_name");
        return new(0,row.GetString(row.GetOrdinal("student_no")),row.GetString(row.GetOrdinal("student_name")),"",
            DateOnly.FromDateTime(row.GetDateTime(row.GetOrdinal("birth_date"))),null,null,null,
            row.IsDBNull(classOrdinal)?null:row.GetString(classOrdinal),null);
    }
    private static SaveResult? KnownFailure(SqlException error,Guid requestId) => error.Number switch {
        2601 or 2627 => Failure(Outcome.ValidationFailed,"E-STU-101","StudentNo",requestId),
        547 => Failure(Outcome.ValidationFailed,"E-STU-009","Save",requestId),
        1205 or 1222 or 3960 or 51001 or 51005 => Failure(Outcome.Conflict,"E-STU-105","Save",requestId),
        229 => Failure(Outcome.Forbidden,"E-COM-002","Save",requestId),
        _ => null
    };
    private static SaveResult Failure(Outcome outcome,string code,string field,Guid requestId)
        => new(outcome,null,null,[new(field,code,NativeMessages.Resolve(code,field,requestId:requestId))],RequestId:requestId.ToString());

    // Raw strings are deliberately unnormalized. Character entities preserve CR before raw scalar checks.
    public static string SerializeRaw(SaveRequest request)
    {
        var d=request.Draft;var birth=d.BirthDateInput;var buffer=new StringBuilder();
        using(var xml=XmlWriter.Create(buffer,new XmlWriterSettings { OmitXmlDeclaration=true,NewLineHandling=NewLineHandling.Entitize,CheckCharacters=true })) {
            xml.WriteStartElement("raw");
            void Field(string key,object? value) {
                xml.WriteStartElement(key);
                if(value is null)xml.WriteAttributeString("null","true");else xml.WriteString(Convert.ToString(value,CultureInfo.InvariantCulture)??"");
                xml.WriteEndElement();
            }
            Field("student_no",d.StudentNo);Field("student_name",d.StudentName);Field("student_name_kana",d.StudentNameKana);
            Field("birth_era",birth.Era);Field("birth_year",birth.Year);Field("birth_month",birth.Month);Field("birth_day",birth.Day);
            Field("gender_code",d.GenderCode);Field("postal_code",d.PostalCode);Field("prefecture_code",d.PrefectureCode);
            Field("address_line1",d.AddressLine1);Field("address_line2",d.AddressLine2);Field("phone_number",d.PhoneNumber);Field("email_address",d.EmailAddress);
            Field("admission_date",d.AdmissionDate);Field("enrollment_status_code",d.EnrollmentStatusCode);Field("enrollment_end_date",d.EnrollmentEndDate);
            Field("class_id",d.ClassId);Field("emergency_contact_name",d.EmergencyContactName);Field("relationship_code",d.RelationshipCode);
            Field("emergency_phone_number",d.EmergencyPhoneNumber);Field("remarks",d.Remarks);
            Field("school_year",request.SchoolYear);Field("grade_code",request.GradeCode);Field("reason",request.Reason);
            xml.WriteEndElement();
        }
        return buffer.ToString();
    }
    public static string SerializeClass(ClassChange c,string? reason=null)
        => SerializeFields(new Dictionary<string,object?> {["school_year"]=c.SchoolYear,["grade_code"]=c.GradeCode,["class_code"]=c.ClassCode,["class_name"]=c.ClassName,["valid_from"]=c.ValidFrom,["valid_to"]=c.ValidTo,["capacity"]=c.Capacity,["display_order"]=c.DisplayOrder,["is_active"]=c.IsActive,["remarks"]=c.Remarks,["reason"]=reason});
    public static string SerializeCode(CodeChange c,string? reason=null)
        => SerializeFields(new Dictionary<string,object?> {["category_id"]=c.CategoryId,["code_value"]=c.CodeValue,["code_name"]=c.CodeName,["display_order"]=c.DisplayOrder,["is_active"]=c.IsActive,["valid_from"]=c.ValidFrom,["valid_to"]=c.ValidTo,["remarks"]=c.Remarks,["reason"]=reason});
    private static string SerializeFields(Dictionary<string,object?> values)
    {
        var buffer=new StringBuilder();
        using(var xml=XmlWriter.Create(buffer,new XmlWriterSettings {OmitXmlDeclaration=true,NewLineHandling=NewLineHandling.Entitize,CheckCharacters=true})) {
            xml.WriteStartElement("raw");
            foreach(var pair in values) {xml.WriteStartElement(pair.Key);if(pair.Value is null)xml.WriteAttributeString("null","true");else xml.WriteString(pair.Value is bool b?(b?"true":"false"):Convert.ToString(pair.Value,CultureInfo.InvariantCulture)??"");xml.WriteEndElement();}
            xml.WriteEndElement();
        }
        return buffer.ToString();
    }
}
