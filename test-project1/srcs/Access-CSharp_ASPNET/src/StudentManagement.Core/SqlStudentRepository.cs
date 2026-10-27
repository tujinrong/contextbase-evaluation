using System.Data;
using System.Globalization;
using Microsoft.Data.SqlClient;

namespace StudentManagement.Core;

/// <summary>SQL Server storage using the extracted schema. Guard + all checks/writes/audit share a transaction.</summary>
public sealed class SqlStudentRepository : IStudentRepository
{
    private readonly string connectionString;
    public SqlStudentRepository(string connectionString)
    {this.connectionString=string.IsNullOrWhiteSpace(connectionString)?throw new ArgumentException("A SQL Server connection must be configured.",nameof(connectionString)):connectionString;}
    public T Execute<T>(bool write,Func<IStudentSession,T> operation)
    {
        using var connection=new SqlConnection(connectionString);connection.Open();
        using var transaction=connection.BeginTransaction(write?IsolationLevel.Serializable:IsolationLevel.RepeatableRead);
        var committing=false;
        try
        {
            if(write)
            {
                using var guard=new SqlCommand("UPDATE dbo.t_write_guard SET lock_bit=~lock_bit WHERE guard_id=1",connection,transaction);
                if(guard.ExecuteNonQuery()!=1)throw new InvalidOperationException("The transaction guard row is missing.");
            }
            var session=new Session(connection,transaction);
            var result=operation(session);
            // Source CloseWork rolls back the guard when no business write occurred.
            if(write&&!session.HasWrites){transaction.Rollback();return result;}
            committing=true;transaction.Commit();return result;
        }
        catch(SqlException ex) when(!committing && ex.Number is 2601 or 2627)
        {TryRollback(transaction);throw new BusinessException("E-STU-101","The business key already exists.");}
        catch when(committing)
        {TryRollback(transaction);throw new CommitOutcomeUnknownException();}
        catch {TryRollback(transaction);throw;}
    }
    private static void TryRollback(SqlTransaction transaction){try{transaction.Rollback();}catch(InvalidOperationException){}catch(SqlException){}}
    private sealed class Session(SqlConnection connection,SqlTransaction transaction) : IStudentSession
    {
        private List<Student>? students;
        private List<ClassItem>? classes;
        private List<CodeItem>? codes;
        private List<CodeCategory>? categories;
        public bool HasWrites {get;private set;}
        private SqlCommand Command(string sql,Dictionary<string,object?>? values=null)
        {
            var command=new SqlCommand(sql,connection,transaction);
            if(values is not null)foreach(var (key,value) in values)
            {
                var type=key is "student_id" or "class_id" or "school_year" or "capacity" or "display_order" or "row_version" or "expected_version" or "before_version" or "after_version"?SqlDbType.Int:
                    key is "is_active" or "is_deleted" or "is_protected" or "duplicate_confirmed"?SqlDbType.Bit:key.EndsWith("_at",StringComparison.Ordinal)?SqlDbType.DateTime2:SqlDbType.NVarChar;
                var p=command.Parameters.Add("@"+key,type);
                if(type==SqlDbType.NVarChar)p.Size=key is "name_key" or "changed_columns"?-1:Math.Max(1,(value as string)?.Length??1);
                p.Value=value??DBNull.Value;
            }
            return command;
        }
        private List<T> Query<T>(string sql,Func<SqlDataReader,T> map)
        {using var command=Command(sql);using var reader=command.ExecuteReader();var list=new List<T>();while(reader.Read())list.Add(map(reader));return list;}
        private static string S(SqlDataReader r,string key)=>Convert.ToString(r[key],CultureInfo.InvariantCulture)??"";
        private static string? N(SqlDataReader r,string key)=>r[key] is DBNull?null:S(r,key);
        private static int I(SqlDataReader r,string key)=>Convert.ToInt32(r[key],CultureInfo.InvariantCulture);
        private static int? NI(SqlDataReader r,string key)=>r[key] is DBNull?null:I(r,key);
        private static bool B(SqlDataReader r,string key)=>Convert.ToBoolean(r[key],CultureInfo.InvariantCulture);
        private static DateTime D(SqlDataReader r,string key)=>DateTime.SpecifyKind(Convert.ToDateTime(r[key],CultureInfo.InvariantCulture),DateTimeKind.Utc);
        private static DateTime? ND(SqlDataReader r,string key)=>r[key] is DBNull?null:D(r,key);
        public string? FindRole(string userId)
        {
            using var command=Command("SELECT user_id,role_name FROM dbo.t_app_role WHERE user_id=@user_id",new(){{"user_id",userId}});
            using var reader=command.ExecuteReader();
            return reader.Read()&&S(reader,"user_id")==userId?S(reader,"role_name"):null;
        }
        public IReadOnlyList<Student> Students()=>students??=Query("SELECT * FROM dbo.m_student",r=>new Student {
            StudentId=I(r,"student_id"),StudentNo=S(r,"student_no"),StudentName=S(r,"student_name"),StudentNameKana=S(r,"student_name_kana"),NameKey=S(r,"name_key"),KanaKey=S(r,"kana_key"),BirthDate=S(r,"birth_date"),
            GenderCode=S(r,"gender_code"),PostalCode=S(r,"postal_code"),PrefectureCode=S(r,"prefecture_code"),AddressLine1=S(r,"address_line1"),AddressLine2=N(r,"address_line2"),PhoneNumber=N(r,"phone_number"),EmailAddress=N(r,"email_address"),
            AdmissionDate=S(r,"admission_date"),EnrollmentStatusCode=S(r,"enrollment_status_code"),EnrollmentEndDate=N(r,"enrollment_end_date"),ClassId=NI(r,"class_id"),EmergencyContactName=N(r,"emergency_contact_name"),
            RelationshipCode=N(r,"relationship_code"),EmergencyPhoneNumber=N(r,"emergency_phone_number"),Remarks=N(r,"remarks"),IsDeleted=B(r,"is_deleted"),DeletedAt=ND(r,"deleted_at"),DeletedBy=N(r,"deleted_by"),DeleteReason=N(r,"delete_reason"),
            CreatedAt=D(r,"created_at"),CreatedBy=S(r,"created_by"),UpdatedAt=D(r,"updated_at"),UpdatedBy=S(r,"updated_by"),RowVersion=I(r,"row_version")});
        public IReadOnlyList<ClassItem> Classes()=>classes??=Query("SELECT * FROM dbo.m_class",r=>new ClassItem {
            ClassId=I(r,"class_id"),SchoolYear=I(r,"school_year"),GradeCode=S(r,"grade_code"),ClassCode=S(r,"class_code"),ClassName=S(r,"class_name"),ValidFrom=S(r,"valid_from"),ValidTo=S(r,"valid_to"),Capacity=NI(r,"capacity"),
            DisplayOrder=I(r,"display_order"),IsActive=B(r,"is_active"),Remarks=N(r,"remarks"),CreatedAt=D(r,"created_at"),CreatedBy=S(r,"created_by"),UpdatedAt=D(r,"updated_at"),UpdatedBy=S(r,"updated_by"),RowVersion=I(r,"row_version")});
        public IReadOnlyList<CodeItem> Codes()=>codes??=Query("SELECT * FROM dbo.m_code",r=>new CodeItem {
            CategoryId=S(r,"category_id"),CodeValue=S(r,"code_value"),CodeName=S(r,"code_name"),DisplayOrder=I(r,"display_order"),IsActive=B(r,"is_active"),ValidFrom=S(r,"valid_from"),ValidTo=N(r,"valid_to"),IsProtected=B(r,"is_protected"),
            Remarks=N(r,"remarks"),CreatedAt=D(r,"created_at"),CreatedBy=S(r,"created_by"),UpdatedAt=D(r,"updated_at"),UpdatedBy=S(r,"updated_by"),RowVersion=I(r,"row_version")});
        public IReadOnlyList<CodeCategory> Categories()=>categories??=Query("SELECT * FROM dbo.m_code_category",r=>new CodeCategory(S(r,"category_id"),S(r,"category_name"),I(r,"code_length"),B(r,"allow_add"),B(r,"is_active")));
        private int Write(string table,string key,int id,int? expectedVersion,Dictionary<string,object?> values)
        {
            // Identifiers come from fixed internal mappings, never from HTTP/input SQL.
            if(id==0)
            {
                var columns=string.Join(",",values.Keys.Select(x=>$"[{x}]"));var parameters=string.Join(",",values.Keys.Select(x=>"@"+x));
                using var insert=Command($"INSERT INTO dbo.[{table}] ({columns}) OUTPUT INSERTED.[{key}] VALUES ({parameters})",values);
                var inserted=Convert.ToInt32(insert.ExecuteScalar(),CultureInfo.InvariantCulture);HasWrites=true;return inserted;
            }
            var assignment=string.Join(",",values.Keys.Select(x=>$"[{x}]=@{x}"));values.Add(key,id);values.Add("expected_version",expectedVersion);
            using var update=Command($"UPDATE dbo.[{table}] SET {assignment} WHERE [{key}]=@{key} AND row_version=@expected_version",values);
            if(update.ExecuteNonQuery()!=1)throw TextRules.Error("E-STU-105");HasWrites=true;return id;
        }
        public Student WriteStudent(Student s,int? expectedVersion)
        {
            var values=new Dictionary<string,object?> {
                ["student_no"]=s.StudentNo,["student_name"]=s.StudentName,["student_name_kana"]=s.StudentNameKana,["name_key"]=s.NameKey,["kana_key"]=s.KanaKey,["birth_date"]=s.BirthDate,
                ["gender_category"]="GENDER",["gender_code"]=s.GenderCode,["postal_code"]=s.PostalCode,["prefecture_category"]="PREFECTURE",["prefecture_code"]=s.PrefectureCode,
                ["address_line1"]=s.AddressLine1,["address_line2"]=s.AddressLine2,["phone_number"]=s.PhoneNumber,["email_address"]=s.EmailAddress,["admission_date"]=s.AdmissionDate,
                ["enrollment_category"]="ENROLLMENT_STATUS",["enrollment_status_code"]=s.EnrollmentStatusCode,["enrollment_end_date"]=s.EnrollmentEndDate,["class_id"]=s.ClassId,
                ["emergency_contact_name"]=s.EmergencyContactName,["relationship_category"]=s.RelationshipCode is null?null:"RELATIONSHIP",["relationship_code"]=s.RelationshipCode,
                ["emergency_phone_number"]=s.EmergencyPhoneNumber,["remarks"]=s.Remarks,["is_deleted"]=s.IsDeleted,["deleted_at"]=s.DeletedAt,["deleted_by"]=s.DeletedBy,["delete_reason"]=s.DeleteReason,
                ["created_at"]=s.CreatedAt,["created_by"]=s.CreatedBy,["updated_at"]=s.UpdatedAt,["updated_by"]=s.UpdatedBy,["row_version"]=s.RowVersion};
            var id=Write("m_student","student_id",s.StudentId,expectedVersion,values);var result=s with {StudentId=id};
            if(students is not null){students.RemoveAll(x=>x.StudentId==id);students.Add(result);}return result;
        }
        public ClassItem WriteClass(ClassItem c,int? expectedVersion)
        {
            var values=new Dictionary<string,object?> { ["school_year"]=c.SchoolYear,["grade_category"]="GRADE",["grade_code"]=c.GradeCode,["class_code"]=c.ClassCode,["class_name"]=c.ClassName,["valid_from"]=c.ValidFrom,["valid_to"]=c.ValidTo,
                ["capacity"]=c.Capacity,["display_order"]=c.DisplayOrder,["is_active"]=c.IsActive,["remarks"]=c.Remarks,["created_at"]=c.CreatedAt,["created_by"]=c.CreatedBy,["updated_at"]=c.UpdatedAt,["updated_by"]=c.UpdatedBy,["row_version"]=c.RowVersion};
            var id=Write("m_class","class_id",c.ClassId,expectedVersion,values);var result=c with {ClassId=id};if(classes is not null){classes.RemoveAll(x=>x.ClassId==id);classes.Add(result);}return result;
        }
        public CodeItem WriteCode(CodeItem c,int? expectedVersion)
        {
            var values=new Dictionary<string,object?> { ["code_name"]=c.CodeName,["display_order"]=c.DisplayOrder,["is_active"]=c.IsActive,["valid_from"]=c.ValidFrom,["valid_to"]=c.ValidTo,["is_protected"]=c.IsProtected,["remarks"]=c.Remarks,
                ["created_at"]=c.CreatedAt,["created_by"]=c.CreatedBy,["updated_at"]=c.UpdatedAt,["updated_by"]=c.UpdatedBy,["row_version"]=c.RowVersion};
            if(expectedVersion is null)
            {
                values.Add("category_id",c.CategoryId);values.Add("code_value",c.CodeValue);
                using var insert=Command($"INSERT INTO dbo.m_code ({string.Join(",",values.Keys.Select(x=>$"[{x}]"))}) VALUES ({string.Join(",",values.Keys.Select(x=>"@"+x))})",values);insert.ExecuteNonQuery();HasWrites=true;
            }
            else
            {
                var assignment=string.Join(",",values.Keys.Select(x=>$"[{x}]=@{x}"));values.Add("category_id",c.CategoryId);values.Add("code_value",c.CodeValue);values.Add("expected_version",expectedVersion);
                using var update=Command($"UPDATE dbo.m_code SET {assignment} WHERE category_id=@category_id AND code_value=@code_value AND row_version=@expected_version",values);
                if(update.ExecuteNonQuery()!=1)throw TextRules.Error("E-STU-105");
                HasWrites=true;
            }
            if(codes is not null){codes.RemoveAll(x=>x.CategoryId==c.CategoryId&&x.CodeValue==c.CodeValue);codes.Add(c);}return c;
        }
        public void AppendAudit(AuditEntry a)
        {
            var values=new Dictionary<string,object?> { ["target_table"]=a.TargetTable,["target_key"]=a.TargetKey,["operation_type"]=a.Operation,["before_version"]=a.BeforeVersion,["after_version"]=a.AfterVersion,
                ["changed_columns"]=a.ChangedColumns,["executed_by"]=a.ExecutedBy,["executed_at"]=a.ExecutedAt,["correlation_id"]=Guid.NewGuid().ToString(),["operation_reason"]=a.Reason,["duplicate_confirmed"]=a.DuplicateConfirmed};
            using var insert=Command($"INSERT INTO dbo.t_operation_log ({string.Join(",",values.Keys.Select(x=>$"[{x}]"))}) VALUES ({string.Join(",",values.Keys.Select(x=>"@"+x))})",values);insert.ExecuteNonQuery();HasWrites=true;
        }
    }
}

public sealed class CommitOutcomeUnknownException() : Exception("E-COM-004: commit outcome is unknown; reload before retrying.");
