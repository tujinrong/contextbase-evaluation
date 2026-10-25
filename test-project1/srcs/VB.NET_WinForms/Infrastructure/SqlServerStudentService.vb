Option Strict On
Option Explicit On
Option Infer On
Option Compare Binary
Imports System
Imports System.Collections.Generic
Imports System.Linq
Imports System.Threading
Imports System.Threading.Tasks
Imports System.Globalization
Imports System.Text
Imports System.Data
Imports Microsoft.Data.SqlClient
Imports StudentManagement.WinForms.Domain.SqlServerStudentService
Imports System.Xml
Imports System.Text.RegularExpressions

Namespace Global.StudentManagement.WinForms.Domain
    Public NotInheritable Class SqlServerStudentService
        Implements IStudentService
        Private ReadOnly _connectionString As String
        Private ReadOnly _currentUser As Func(Of CurrentUser)
        Private ReadOnly _clock As TimeProvider
        Private Shared ReadOnly Columns As Dictionary(Of String, (SqlDbType, Integer)) = New Global.System.Collections.Generic.Dictionary(Of String, (Global.System.Data.SqlDbType, Integer))(StringComparer.Ordinal) From {
    {"student_no", (SqlDbType.VarChar, 15)},
    {"student_name", (SqlDbType.NVarChar, 16)},
    {"student_name_kana", (SqlDbType.NVarChar, 36)},
    {"name_key", (SqlDbType.NVarChar, 320)},
    {"kana_key", (SqlDbType.NVarChar, 36)},
    {"birth_date", (SqlDbType.Date, 0)},
    {"gender_code", (SqlDbType.VarChar, 1)},
    {"postal_code", (SqlDbType.VarChar, 7)},
    {"prefecture_code", (SqlDbType.VarChar, 2)},
    {"address_line1", (SqlDbType.NVarChar, 90)},
    {"address_line2", (SqlDbType.NVarChar, 90)},
    {"phone_number", (SqlDbType.VarChar, 16)},
    {"email_address", (SqlDbType.VarChar, 60)},
    {"admission_date", (SqlDbType.Date, 0)},
    {"enrollment_status_code", (SqlDbType.VarChar, 2)},
    {"enrollment_end_date", (SqlDbType.Date, 0)},
    {"class_id", (SqlDbType.BigInt, 0)},
    {"emergency_contact_name", (SqlDbType.NVarChar, 16)},
    {"relationship_category", (SqlDbType.VarChar, 24)},
    {"relationship_code", (SqlDbType.VarChar, 2)},
    {"emergency_phone_number", (SqlDbType.VarChar, 16)},
    {"remarks", (SqlDbType.NVarChar, 240)}
}
        Public Sub New(connectionString As String, currentUser As Func(Of CurrentUser), Optional clock As TimeProvider = Nothing)
            Dim builder = New SqlConnectionStringBuilder(connectionString) With {
    .Encrypt = SqlConnectionEncryptOption.Mandatory,
    .TrustServerCertificate = False
}
            _connectionString = builder.ConnectionString
            _currentUser = currentUser
            _clock = If(clock, TimeProvider.System)
        End Sub

        Private ReadOnly Property Now As DateTimeOffset
            Get
                Return _clock.GetUtcNow()
            End Get
        End Property

        Private Shared Function BusinessDay(now As DateTimeOffset) As DateOnly
            Return DateOnly.FromDateTime(now.ToOffset(TimeSpan.FromHours(9)).DateTime)
        End Function
        Private Function User() As CurrentUser
            Dim lUser = _currentUser()
            Text(lUser.Principal, 64, 64, "Principal", True)
            Dim ignoredSession As Guid
            If Not Guid.TryParse(lUser.SessionId, ignoredSession) Then Throw New UnauthorizedAccessException("認証セッションが不正です。")
            Return lUser
        End Function

        Private Async Function Open(ct As CancellationToken) As Task(Of SqlConnection)
            Dim connection = New SqlConnection(_connectionString)
            Try
                Await connection.OpenAsync(ct)
                Using diagnostic = connection.CreateCommand()
                    diagnostic.CommandText = "SELECT snapshot_isolation_state FROM sys.databases WHERE database_id=DB_ID()"
                    If Convert.ToInt32(Await diagnostic.ExecuteScalarAsync(ct), CultureInfo.InvariantCulture) <> 1 Then Throw New InvalidOperationException("ALLOW_SNAPSHOT_ISOLATION ONが必要です。")
                    Return connection
                End Using

            Catch
                connection.Dispose()
                Throw
            End Try
        End Function

        Friend Shared Function Command(connection As SqlConnection, tx As SqlTransaction, sql As String) As SqlCommand
            Return New Global.Microsoft.Data.SqlClient.SqlCommand(sql, connection, tx) With {
                .CommandTimeout = 30
            }
        End Function
        Friend Shared Sub Param(command As SqlCommand, name As String, type As SqlDbType, value As Object, Optional size As Integer = 0)
            Dim [date] As DateOnly = Nothing
            If TypeOf value Is DateOnly Then value = CType(value,DateOnly).ToDateTime(TimeOnly.MinValue)
            Dim parameter = command.Parameters.Add(name, type)
            If size <> 0 Then parameter.Size = size
            parameter.Value = If(value, DBNull.Value)
        End Sub

        Private Shared Function [String](reader As SqlDataReader, column As String) As String
            Return If(reader.IsDBNull(reader.GetOrdinal(column)), Nothing, reader.GetString(reader.GetOrdinal(column)))
        End Function
        Private Shared Function [Long](reader As SqlDataReader, column As String) As Long
            Return reader.GetInt64(reader.GetOrdinal(column))
        End Function
        Private Shared Function [Date](reader As SqlDataReader, column As String) As DateOnly
            Return DateOnly.FromDateTime(reader.GetDateTime(reader.GetOrdinal(column)))
        End Function
        Private Shared Function Row(reader As SqlDataReader) As StudentRow
            Return New Global.StudentManagement.WinForms.Domain.StudentRow([Long](reader, "student_id"), [String](reader, "student_no"), [String](reader, "student_name"), [String](reader, "student_name_kana"), [Date](reader, "birth_date"), If(reader.IsDBNull(reader.GetOrdinal("school_year")), CType(Nothing,Integer?), CType(Convert.ToInt32(reader("school_year")),Integer?)), [String](reader, "grade_name"), [String](reader, "class_code"), [String](reader, "class_name"), [String](reader, "status_name"))
        End Function
        Private Const RowSelect As String = "SELECT s.student_id,s.student_no,s.student_name,s.student_name_kana,s.birth_date," & vbLf & "       c.school_year,c.class_code,c.class_name,g.code_name grade_name,e.code_name status_name" & vbLf & "  FROM dbo.m_student s" & vbLf & "  LEFT JOIN dbo.m_class c ON c.class_id=s.class_id" & vbLf & "  LEFT JOIN dbo.m_code g ON g.category_id=c.grade_category AND g.code_value=c.grade_code" & vbLf & "  LEFT JOIN dbo.m_code e ON e.category_id=s.enrollment_category AND e.code_value=s.enrollment_status_code"
        Friend Shared Async Function Gate(connection As SqlConnection, tx As SqlTransaction, ct As CancellationToken) As Task
            Using command = SqlServerStudentService.Command(connection, tx, "SET XACT_ABORT ON;" & vbLf & "DECLARE @result int;" & vbLf & "EXEC @result=sys.sp_getapplock @Resource=N'test-project1:student-write',@LockMode='Exclusive'," & vbLf & "     @LockOwner='Transaction',@LockTimeout=5000,@DbPrincipal='public';" & vbLf & "IF @result<0 THROW 51001,N'保存用ロックを取得できませんでした。',1;")
                Await command.ExecuteNonQueryAsync(ct)
            End Using
        End Function

        Public Async Function SearchAsync(criteria As SearchCriteria, Optional sortKey As String = "studentNo", Optional sortDirection As String = "asc", Optional ct As CancellationToken = Nothing) As Task(Of SearchResult) Implements IStudentService.SearchAsync
            User()
            Dim now = Me.Now
            Dim day = BusinessDay(now)

            Dim classId As Long = Nothing
            Try
                If criteria Is Nothing OrElse Not (Equals(sortDirection, "asc") OrElse Equals(sortDirection, "desc")) Then Throw New ArgumentException("E-COM-003: 並び順が不正です。")
                Dim order = (If(Equals(sortKey, "studentNo"), "s.student_no", (If(Equals(sortKey, "name"), "s.name_key", (If(Equals(sortKey, "admissionDate"), "s.admission_date", (If(Equals(sortKey, "updatedAt"), "s.updated_at", ConversionSupport.__Throw(Of String)(New ArgumentException("E-COM-003: 並び順が不正です。"))))))))))
                If criteria.ClassId <= 0 Then Throw New ArgumentException("E-COM-003: クラスが不正です。")
                Dim statuses = criteria.EnrollmentStatusCodes
                If statuses Is Nothing Then Throw New ArgumentException("E-COM-003: 在籍区分が不正です。")
                If statuses.Length > 4 OrElse statuses.Distinct(StringComparer.Ordinal).Count() <> statuses.Length OrElse statuses.Any(Function(value) Not (Equals(value, "01") OrElse Equals(value, "02") OrElse Equals(value, "03") OrElse Equals(value, "04"))) Then Throw New ArgumentException("E-STU-009: 在籍区分が不正です。")
                Dim no = If(String.IsNullOrEmpty(criteria.StudentNo), Nothing, Identifier(criteria.StudentNo, 15, "StudentNo"))
                Dim name = Text(criteria.StudentName, 160, 160, "StudentName")
                name = If(Equals(name, Nothing), Nothing, NameKey(name))
                Using connection = Await Open(ct)
                    Using tx = CType(Await connection.BeginTransactionAsync(IsolationLevel.Snapshot, ct), SqlTransaction)
                        If criteria.ClassId.HasValue Then
                            Using classCheck = Command(connection, tx, "SELECT COUNT_BIG(*) FROM dbo.m_class WHERE class_id=@id")
                                Param(classCheck, "@id", SqlDbType.BigInt, criteria.ClassId.Value)
                                If CLng(Await classCheck.ExecuteScalarAsync(ct)) = 0 Then Throw New ArgumentException("E-STU-014: クラスが存在しません。")
                            End Using
                        End If
                        For Each status In statuses
                            Using statusCheck = Command(connection, tx, "SELECT COUNT_BIG(*) FROM dbo.m_code WHERE category_id='ENROLLMENT_STATUS' AND code_value=@code")
                                Param(statusCheck, "@code", SqlDbType.VarChar, status, 2)
                                If CLng(Await statusCheck.ExecuteScalarAsync(ct)) <> 1 Then Throw New ArgumentException("E-STU-009: 在籍区分が存在しません。")
                            End Using
                        Next
                        Dim predicates = New List(Of String) From {
    "s.is_deleted=0"
}
                        Dim parameters = New List(Of (String, SqlDbType, Object, Integer))()
                        Dim lWhere As Action(Of String, String, SqlDbType, Object, Integer) = Sub(sql, key, type, value, size)
                                                                                                  If Not value Is Nothing Then
                                                                                                      predicates.Add(sql)
                                                                                                      parameters.Add((key, type, value, size))
                                                                                                  End If
                                                                                              End Sub
                        lWhere("s.student_no LIKE @no ESCAPE '!'", "@no", SqlDbType.VarChar, If(Equals(no, Nothing), Nothing, EscapeLike(no) & "%"), 31)
                        lWhere("s.name_key LIKE @name ESCAPE '!'", "@name", SqlDbType.NVarChar, If(Equals(name, Nothing), Nothing, "%" & EscapeLike(name) & "%"), 642)
                        lWhere("s.class_id=@class", "@class", SqlDbType.BigInt, criteria.ClassId, 0)
                        If statuses.Length > 0 Then
                            predicates.Add("s.enrollment_status_code IN (" & String.Join(","c, statuses.[Select](Function(__, index) "@status" & index.ToString())) & ")")
                            parameters.AddRange(statuses.[Select](Function(value, index) ("@status" & index.ToString(), SqlDbType.VarChar, CObj(value), 2)))
                        End If

                        Dim where = " WHERE " & String.Join(" AND ", predicates)
                        Using countCommand = Command(connection, tx, "SELECT COUNT_BIG(*) FROM (SELECT TOP (10001) s.student_id FROM dbo.m_student s LEFT JOIN dbo.m_class c ON c.class_id=s.class_id" & where & ") limited")
                            For Each p In parameters
                                SqlServerStudentService.Param(countCommand, p.Item1, p.Item2, p.Item3, p.Item4)
                            Next
                            Dim count = CInt(CLng((Await countCommand.ExecuteScalarAsync(ct))))
                            If count > 10000 Then
                                Await tx.CommitAsync(ct)
                                Return New Global.StudentManagement.WinForms.Domain.SearchResult(Outcome.NoChange, count, New Global.StudentManagement.WinForms.Domain.StudentRow() {}, now, True, New Global.StudentManagement.WinForms.Domain.FieldError() {})
                            End If

                            Using listCommand = Command(connection, tx, RowSelect & where & " ORDER BY " & order & " " & sortDirection & ",s.student_id ASC")
                                For Each p In parameters
                                    SqlServerStudentService.Param(listCommand, p.Item1, p.Item2, p.Item3, p.Item4)
                                Next
                                Dim rows = New List(Of StudentRow)()
                                Using reader = Await listCommand.ExecuteReaderAsync(ct)
                                    While Await reader.ReadAsync(ct)
                                        rows.Add(Row(reader))
                                    End While
                                End Using
                                Await tx.CommitAsync(ct)
                                Return New Global.StudentManagement.WinForms.Domain.SearchResult(Outcome.NoChange, count, rows, now, False, New Global.StudentManagement.WinForms.Domain.FieldError() {})
                            End Using
                        End Using
                    End Using
                End Using
            Catch e As InputValidationException
                Return New Global.StudentManagement.WinForms.Domain.SearchResult(Outcome.ValidationFailed, 0, New Global.StudentManagement.WinForms.Domain.StudentRow() {}, now, False, e.Errors)
            Catch e As ArgumentException
                Return New Global.StudentManagement.WinForms.Domain.SearchResult(Outcome.ValidationFailed, 0, New Global.StudentManagement.WinForms.Domain.StudentRow() {}, now, False, New Global.StudentManagement.WinForms.Domain.FieldError() {ArgumentError("Search", e)})
            End Try
        End Function

        Public Async Function GetAsync(id As Long, Optional ct As CancellationToken = Nothing) As Task(Of StudentDetail) Implements IStudentService.GetAsync
            User()
            If id <= 0 Then Return Nothing
            Using connection = Await Open(ct)
                Using command = SqlServerStudentService.Command(connection, Nothing, "SELECT * FROM dbo.m_student WHERE student_id=@id AND is_deleted=0")
                    Param(command, "@id", SqlDbType.BigInt, id)
                    Using reader = Await command.ExecuteReaderAsync(ct)
                        If Not Await reader.ReadAsync(ct) Then Return Nothing
                        Dim values = Columns.Keys.ToDictionary(Function(key) key, Function(key) If(reader.IsDBNull(reader.GetOrdinal(key)), Nothing, reader(key)))
                        Return Detail(id, [Long](reader, "row_version"), values, reader.GetFieldValue(Of DateTimeOffset)(reader.GetOrdinal("updated_at")), [String](reader, "updated_by"))
                    End Using
                End Using
            End Using
        End Function

        Private Shared Function Detail(id As Long, version As Long, values As Dictionary(Of String, Object), updated As DateTimeOffset, actor As String) As StudentDetail
            Dim S As Func(Of String, String) = Function(key) values(key)?.ToString()
            Dim D As Func(Of String, DateOnly) = Function(key)
                                                     Return If(TypeOf values(key) Is DateOnly, CType(values(key),DateOnly), DateOnly.FromDateTime(CType(values(key),DateTime)))
                                                 End Function
            Dim draft = New StudentDraft With {
    .StudentNo = S("student_no"),
    .StudentName = S("student_name"),
    .StudentNameKana = S("student_name_kana"),
    .BirthDateInput = ToInput(D("birth_date")),
    .GenderCode = S("gender_code"),
    .PostalCode = S("postal_code"),
    .PrefectureCode = S("prefecture_code"),
    .AddressLine1 = S("address_line1"),
    .AddressLine2 = S("address_line2"),
    .PhoneNumber = S("phone_number"),
    .EmailAddress = S("email_address"),
    .AdmissionDate = D("admission_date").ToString("yyyy-MM-dd", CultureInfo.InvariantCulture),
    .EnrollmentStatusCode = S("enrollment_status_code"),
    .EnrollmentEndDate = If(values("enrollment_end_date") Is Nothing, Nothing, D("enrollment_end_date").ToString("yyyy-MM-dd", CultureInfo.InvariantCulture)),
    .ClassId = CType(values("class_id"),Long?),
    .EmergencyContactName = S("emergency_contact_name"),
    .RelationshipCode = S("relationship_code"),
    .EmergencyPhoneNumber = S("emergency_phone_number"),
    .Remarks = S("remarks")
}
            Return New Global.StudentManagement.WinForms.Domain.StudentDetail(id, version, draft, D("birth_date"), updated, actor)
        End Function

        Public Function LookupAsync(Optional ct As CancellationToken = Nothing) As Task(Of LookupSet) Implements IStudentService.LookupAsync
            Return LookupAsync(True, ct)
        End Function
        Public Async Function LookupAsync(includeOccupancy As Boolean, Optional ct As CancellationToken = Nothing) As Task(Of LookupSet) Implements IStudentService.LookupAsync
            User()
            Using connection = Await Open(ct)
                Using tx = CType(Await connection.BeginTransactionAsync(IsolationLevel.Snapshot, ct), SqlTransaction)
                    Dim occupied = If(includeOccupancy, "(SELECT COUNT(*) FROM dbo.m_student s WHERE s.class_id=c.class_id AND s.is_deleted=0 AND s.enrollment_status_code IN ('01','02'))", "CONVERT(int,0)")
                    Using command = SqlServerStudentService.Command(connection, tx, $"SELECT c.category_id,c.code_value,c.code_name,c.display_order,
       CONVERT(bit,CASE WHEN c.is_active=1 AND k.is_active=1 THEN 1 ELSE 0 END) is_active,c.valid_from,c.valid_to,c.is_protected
  FROM dbo.m_code c JOIN dbo.m_code_category k ON k.category_id=c.category_id ORDER BY c.category_id,c.display_order,c.code_value;
SELECT c.*, {occupied} occupied
  FROM dbo.m_class c LEFT JOIN dbo.m_code g ON g.category_id=c.grade_category AND g.code_value=c.grade_code
 ORDER BY c.school_year DESC,g.display_order,c.display_order,c.class_code,c.class_id;")
                        Dim codes = New List(Of CodeEntry)()
                        Dim classes = New List(Of SchoolClass)()
                        Using reader = Await command.ExecuteReaderAsync(ct)
                            While Await reader.ReadAsync(ct)
                                codes.Add(New Global.StudentManagement.WinForms.Domain.CodeEntry([String](reader, "category_id"), [String](reader, "code_value"), [String](reader, "code_name"), Convert.ToInt32(reader("display_order")), reader.GetBoolean(reader.GetOrdinal("is_active")), [Date](reader, "valid_from"), If(reader.IsDBNull(reader.GetOrdinal("valid_to")), CType(Nothing,DateOnly?), CType([Date](reader, "valid_to"),DateOnly?)), reader.GetBoolean(reader.GetOrdinal("is_protected"))))
                            End While
                            Await reader.NextResultAsync(ct)
                            While Await reader.ReadAsync(ct)
                                classes.Add(New Global.StudentManagement.WinForms.Domain.SchoolClass([Long](reader, "class_id"), Convert.ToInt32(reader("school_year")), [String](reader, "grade_code"), [String](reader, "class_code"), [String](reader, "class_name"), [Date](reader, "valid_from"), [Date](reader, "valid_to"), If(reader.IsDBNull(reader.GetOrdinal("capacity")), CType(Nothing,Integer?), CType(Convert.ToInt32(reader("capacity")),Integer?)), Convert.ToInt32(reader("occupied")), reader.GetBoolean(reader.GetOrdinal("is_active"))))
                            End While
                        End Using

                        Await tx.CommitAsync(ct)
                        Return New Global.StudentManagement.WinForms.Domain.LookupSet(codes, classes)
                    End Using
                End Using
            End Using
        End Function

        Private Shared Async Function CodeExists(connection As SqlConnection, tx As SqlTransaction, category As String, value As String, ct As CancellationToken) As Task(Of Boolean)
            Using command = SqlServerStudentService.Command(connection, tx, "SELECT COUNT_BIG(*) FROM dbo.m_code WHERE category_id=@category AND code_value=@value")
                Param(command, "@category", SqlDbType.VarChar, category, 24)
                Param(command, "@value", SqlDbType.VarChar, value, 10)
                Return CLng((Await command.ExecuteScalarAsync(ct))) = 1
            End Using
        End Function

        Public Function SaveAsync(request As SaveRequest, Optional ct As CancellationToken = Nothing) As Task(Of SaveResult) Implements IStudentService.SaveAsync
            Return ExecuteNative(Function(c, tx, session, id) NativeStoredProcedureClient.SaveAsync(c, tx, request, session, id, ct), ct)
        End Function
        Public Function DeleteAsync(id As Long, version As Long, rawReason As String, Optional ct As CancellationToken = Nothing) As Task(Of SaveResult) Implements IStudentService.DeleteAsync
            Return ExecuteNative(Function(c, tx, session, requestId) NativeStoredProcedureClient.DeleteAsync(c, tx, id, version, rawReason, session, requestId, ct), ct)
        End Function
        Private Async Function ExecuteNative(execute As Func(Of SqlConnection, SqlTransaction, Guid, Guid, Task(Of SaveResult)), ct As CancellationToken) As Task(Of SaveResult)
            Dim user = Me.User()
            Dim requestId = Guid.NewGuid()
            Using connection = Await Open(ct)
                Using tx = CType(Await connection.BeginTransactionAsync(IsolationLevel.ReadCommitted, ct), SqlTransaction)
                    Dim procedureStarted = False, commitAttempted = False
                    Try
                        ' DB procedures resolve ORIGINAL_LOGIN/role and regenerate normalized values from Raw.
                        procedureStarted = True
                        Dim result = Await execute(connection, tx, Guid.Parse(user.SessionId), requestId)
                        If result.Outcome = Outcome.Saved OrElse result.Outcome = Outcome.ConfirmationRequired Then
                            commitAttempted = True
                            Await tx.CommitAsync(ct)
                        Else
                            SafeRollback(tx)
                        End If
                        Return result
                    Catch e As Exception When (TypeOf e Is SqlException) OrElse (TypeOf e Is InvalidOperationException) OrElse (TypeOf e Is OperationCanceledException)
                        Dim rolledBack = SafeRollback(tx)
                        Dim unknown = procedureStarted AndAlso (commitAttempted OrElse Not rolledBack)
                        Return New Global.StudentManagement.WinForms.Domain.SaveResult(If(unknown, Outcome.Unknown, Outcome.SystemError), Nothing, Nothing, New Global.StudentManagement.WinForms.Domain.FieldError() {New Global.StudentManagement.WinForms.Domain.FieldError("", "E-COM-004", If(unknown, "保存結果を確認できません。再保存の前に検索で確認してください。", "処理に失敗しました。受付番号：" & requestId.ToString()))}, RequestId:=requestId.ToString())
                    End Try
                End Using
            End Using
        End Function

        Friend Shared Function SafeRollback(tx As SqlTransaction) As Boolean
            Try
                tx.Rollback()
                Return True
            Catch __unusedSqlException1__ As SqlException
                Return False
            Catch __unusedInvalidOperationException2__ As InvalidOperationException
                Return False
            End Try
        End Function

        Private Class ConversionSupport
            
            Shared Function __Assign(Of T)(ByRef target As T, value As T) As T
                target = value
                Return value
            End Function
            
            Shared Function __Throw(Of T)(ByVal e As Exception) As T
                Throw e
            End Function
        End Class
    End Class

End Namespace
