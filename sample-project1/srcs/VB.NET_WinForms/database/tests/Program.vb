Imports System.Data
Imports System.IO
Imports System.Text.Json
Imports System.Text.RegularExpressions
Imports Microsoft.Data.SqlClient
Imports StudentManagement.WinForms.Domain
Module Program
 Private checks As Integer
 Private Sub Check(value As Boolean, id As String)
  If Not value Then Throw New Exception("FAILED: " & id)
  checks+=1 : Console.WriteLine("PASS " & id)
 End Sub
 Function Main() As Integer
  Return RunAsync().GetAwaiter().GetResult()
 End Function
 Private Async Function Scalar(c As SqlConnection,sql As String) As Task(Of Object)
  Using q As New SqlCommand(sql,c) With {.CommandTimeout=30}
   Return Await q.ExecuteScalarAsync()
  End Using
 End Function
 Private Async Function Execute(c As SqlConnection,sql As String) As Task
  Using q As New SqlCommand(sql,c) With {.CommandTimeout=30}
   Await q.ExecuteNonQueryAsync()
  End Using
 End Function
 Private Function SqlDirectory() As String
  Dim current As New DirectoryInfo(AppContext.BaseDirectory)
  While current IsNot Nothing
   If File.Exists(Path.Combine(current.FullName,"001_schema.sql")) Then Return current.FullName
   current=current.Parent
  End While
  Throw New FileNotFoundException("This project's generated schema and native resources are required.")
 End Function
 Private Function Draft(number As String,classId As Long) As StudentDraft
  Return New StudentDraft With {.StudentNo=number,.StudentName="試験 太郎",.StudentNameKana="シケン タロウ",.BirthDateInput=New BirthDateInput("HEISEI","20","05","15"),.GenderCode="0",.PostalCode="1000001",.PrefectureCode="13",.AddressLine1="試験町1",.PhoneNumber="0312345678",.AdmissionDate="2026-04-01",.EnrollmentStatusCode="01",.ClassId=classId}
 End Function
 Private Async Function RunAsync() As Task(Of Integer)
  Dim configured=Environment.GetEnvironmentVariable("STUDENT_TEST_DB_CONNECTION")
  If String.IsNullOrWhiteSpace(configured) Then
   Console.WriteLine(JsonSerializer.Serialize(New With {.profile="VB.NET_WinForms",.status="SKIP",.reason="STUDENT_TEST_DB_CONNECTION absent; no database opened",.checks=0})) : Return 0
  End If
  Dim nativeConfigured=Environment.GetEnvironmentVariable("STUDENT_TEST_NATIVE_DB_CONNECTION")
  If String.IsNullOrWhiteSpace(nativeConfigured) Then
   Console.WriteLine(JsonSerializer.Serialize(New With {.profile="VB.NET_WinForms",.status="SKIP",.reason="STUDENT_TEST_NATIVE_DB_CONNECTION absent; no database opened",.checks=0})) : Return 0
  End If
  Dim settings As New SqlConnectionStringBuilder(configured) With {.Encrypt=SqlConnectionEncryptOption.Mandatory,.TrustServerCertificate=False}
  If Not Regex.IsMatch(settings.InitialCatalog,"^contextbase_test_[A-Za-z0-9_]+$",RegexOptions.CultureInvariant) Then Throw New InvalidOperationException("Only dedicated contextbase_test_* fixtures are permitted.")
  Dim nativeSettings As New SqlConnectionStringBuilder(nativeConfigured) With {.Encrypt=SqlConnectionEncryptOption.Mandatory,.TrustServerCertificate=False}
  If Not String.Equals(settings.DataSource,nativeSettings.DataSource,StringComparison.OrdinalIgnoreCase) OrElse Not String.Equals(settings.InitialCatalog,nativeSettings.InitialCatalog,StringComparison.OrdinalIgnoreCase) Then Throw New InvalidOperationException("Both identities must use the same explicitly selected fixture server/database.")
  Using db As New SqlConnection(settings.ConnectionString)
   Await db.OpenAsync()
   Check(Convert.ToInt32(Await Scalar(db,"SELECT SERVERPROPERTY('ProductMajorVersion')"))=16,"SQL Server 2022")
   Check(Convert.ToInt32(Await Scalar(db,"SELECT COUNT(*) FROM sys.objects WHERE is_ms_shipped=0"))=0,"empty fixture objects; never overwrite")
   Dim directory=SqlDirectory()
   Dim clrSql=Await File.ReadAllTextAsync(Path.Combine(directory,"native/000_sqlclr.sql"))
   Dim approvedHash=Regex.Match(clrSql,"sys\.trusted_assemblies WHERE hash=0x([0-9A-Fa-f]{128})\)").Groups(1).Value
   If approvedHash.Length<>128 Then Throw New InvalidOperationException("The exact reviewed assembly hash is required.")
   Check(Convert.ToInt32(Await Scalar(db,"SELECT value_in_use FROM sys.configurations WHERE name='clr enabled'"))=1,"DBA pre-approved CLR")
   Check(Convert.ToInt32(Await Scalar(db,"SELECT COUNT(*) FROM sys.trusted_assemblies WHERE hash=0x" & approvedHash))=1,"DBA pre-registered exact assembly; no server changes")
   Dim nativePrincipal As String
   Using nativeDb As New SqlConnection(nativeSettings.ConnectionString)
    Await nativeDb.OpenAsync()
    Using identityCommand As New SqlCommand("SELECT USER_NAME(),COALESCE(IS_SRVROLEMEMBER('sysadmin'),0),COALESCE(IS_MEMBER('db_owner'),0)",nativeDb)
     Using identity=Await identityCommand.ExecuteReaderAsync()
      If Not Await identity.ReadAsync() Then Throw New InvalidOperationException("Application database identity is required.")
      nativePrincipal=identity.GetString(0)
      If nativePrincipal="dbo" OrElse nativePrincipal="guest" OrElse identity.GetInt32(1)<>0 OrElse identity.GetInt32(2)<>0 Then Throw New InvalidOperationException("A pre-created application user without dbo/db_owner/sysadmin is required.")
     End Using
    End Using
   End Using
   For Each filename In {"001_schema.sql","002_seed.sql","native/000_sqlclr.sql","native/010_student_api.sql","native/020_master_api.sql"}
    Dim batches As IEnumerable(Of String)=Regex.Split(Await File.ReadAllTextAsync(Path.Combine(directory,filename)),"(?m)^GO\s*\r?$")
    ' The first 000 batch can register server trust; omit it after the read-only precondition.
    If filename="native/000_sqlclr.sql" Then batches=batches.Skip(1)
    For Each batch In batches
     If Not String.IsNullOrWhiteSpace(batch) Then Await Execute(db,batch)
    Next
   Next
   Using grant As New SqlCommand("DECLARE @statement nvarchar(max)=N'ALTER ROLE student_admin ADD MEMBER '+QUOTENAME(@member);EXEC sys.sp_executesql @statement;",db)
    grant.Parameters.Add("@member",SqlDbType.NVarChar,128).Value=nativePrincipal
    Await grant.ExecuteNonQueryAsync()
   End Using
   Check(Convert.ToInt32(Await Scalar(db,"SELECT snapshot_isolation_state FROM sys.databases WHERE database_id=DB_ID()"))=1,"snapshot enabled")
   Check(Convert.ToInt32(Await Scalar(db,"SELECT COUNT(*) FROM sys.procedures WHERE schema_id=SCHEMA_ID(N'student_api') AND name IN (N'prepare_save',N'persist_student',N'delete_student',N'save_class',N'save_code')"))=5,"native entries deployed")
   Check(Convert.ToInt32(Await Scalar(db,"SELECT COUNT(*) FROM dbo.m_student"))=0,"empty dedicated fixture students")
   Check(Convert.ToInt32(Await Scalar(db,"SELECT COUNT(*) FROM dbo.m_class"))=0,"empty dedicated fixture classes")
   Check(Convert.ToInt32(Await Scalar(db,"SELECT COUNT(*) FROM dbo.m_code_category"))=5,"five code categories")
   Check(Convert.ToInt32(Await Scalar(db,"SELECT COUNT(*) FROM dbo.m_code"))=70,"70 code values")
   Dim user As New CurrentUser(nativePrincipal,Guid.NewGuid().ToString(),Role.Administrator)
   Dim service As New SqlServerStudentService(nativeSettings.ConnectionString,Function() user)
   Dim maintenance As New MasterMaintenanceService(nativeSettings.ConnectionString)
   Dim runId="V" & Guid.NewGuid().ToString("N").Substring(0,10)
   Dim classCode="T" & runId.Substring(1,7)
   Console.WriteLine("FIXTURE " & runId)
   Dim classResult=Await maintenance.SaveClassAsync(New ClassChange(Nothing,Nothing,2026,"01",classCode,"試験クラス","2026-04-01","2027-03-31",2,0,True,Nothing))
   Check(classResult.Outcome=Outcome.Saved,"native class create")
   Dim classId As Long
   Using classQuery As New SqlCommand("SELECT class_id FROM dbo.m_class WHERE school_year=2026 AND class_code=@code",db)
    classQuery.Parameters.Add("@code",SqlDbType.VarChar,9).Value=classCode
    classId=Convert.ToInt64(Await classQuery.ExecuteScalarAsync())
   End Using
   Dim initial=Draft(runId & "-1",classId)
   Dim saved=Await service.SaveAsync(New SaveRequest(initial))
   Check(saved.Outcome=Outcome.Saved AndAlso saved.StudentId.HasValue AndAlso saved.RowVersion.HasValue,"native create COMMIT")
   Dim id=saved.StudentId.Value
   Dim detail=Await service.GetAsync(id)
   Check(detail IsNot Nothing AndAlso detail.Draft.RelationshipCode Is Nothing,"paired optional emergency round trip")
   Check(Convert.ToInt32(Await Scalar(db,"SELECT COUNT(*) FROM dbo.m_student WHERE relationship_category IS NULL AND relationship_code IS NULL"))=1,"derived category NULL pair")
   Dim unchanged=Await service.SaveAsync(New SaveRequest(detail.Draft,id,detail.RowVersion))
   Check(unchanged.Outcome=Outcome.NoChange,"no change")
   detail.Draft.EmergencyContactName="試験 花子" : detail.Draft.RelationshipCode="01" : detail.Draft.EmergencyPhoneNumber="0312345678"
   Dim updated=Await service.SaveAsync(New SaveRequest(detail.Draft,id,detail.RowVersion))
   Check(updated.Outcome=Outcome.Saved,"set complete emergency")
   Check(Convert.ToInt32(Await Scalar(db,"SELECT COUNT(*) FROM dbo.m_student WHERE relationship_category='RELATIONSHIP' AND relationship_code='01'"))=1,"server category derivation")
   Dim conflict=Await service.SaveAsync(New SaveRequest(detail.Draft,id,detail.RowVersion))
   Check(conflict.Outcome=Outcome.Conflict,"stale version rejected")
   detail=Await service.GetAsync(id)
   detail.Draft.EmergencyContactName=Nothing : detail.Draft.RelationshipCode=Nothing : detail.Draft.EmergencyPhoneNumber=Nothing
   updated=Await service.SaveAsync(New SaveRequest(detail.Draft,id,detail.RowVersion))
   Check(updated.Outcome=Outcome.Saved,"clear complete emergency")
   Dim duplicateDraft=Draft(runId & "-2",classId)
   Dim waiting=Await service.SaveAsync(New SaveRequest(duplicateDraft))
   Check(waiting.Outcome=Outcome.ConfirmationRequired AndAlso waiting.ConfirmationToken IsNot Nothing,"confirmation persisted")
   Check(waiting.Candidates.Count=1 AndAlso GetType(StudentRow).GetProperty("Address") Is Nothing AndAlso GetType(StudentRow).GetProperty("PhoneNumber") Is Nothing AndAlso waiting.Candidates(0).EnrollmentStatusName Is Nothing,"duplicate candidates omit unrelated personal fields")
   Dim second=Await service.SaveAsync(New SaveRequest(duplicateDraft,ConfirmationToken:=waiting.ConfirmationToken,Reason:="別人であることを確認"))
   Check(second.Outcome=Outcome.Saved,"native confirm and create")
   Dim replay=Await service.SaveAsync(New SaveRequest(duplicateDraft,ConfirmationToken:=waiting.ConfirmationToken,Reason:="別人であることを確認"))
   Check(replay.Outcome<>Outcome.Saved,"confirmation replay denied")
   Dim lookup=Await service.LookupAsync(False)
   Check(lookup.Classes.All(Function(x) x.Occupied=0),"search lookup no occupancy")
   Dim search=Await service.SearchAsync(New SearchCriteria With {.EnrollmentStatusCodes={"01","02"}})
   Check(search.Status=SearchStatus.Success AndAlso search.Count.GetValueOrDefault(-1)=2,"search native saved rows")
   detail=Await service.GetAsync(id)
   Dim removed=Await service.DeleteAsync(id,detail.RowVersion,"評価用の論理削除")
   Check(removed.Outcome=Outcome.Saved,"native logical delete COMMIT")
   Check(Await service.GetAsync(id) Is Nothing,"deleted hidden")
   Check(Convert.ToInt32(Await Scalar(db,"SELECT COUNT(*) FROM dbo.m_student WHERE is_deleted=1"))=1,"physical row retained")
   Check(Convert.ToInt32(Await Scalar(db,"SELECT COUNT(*) FROM dbo.t_operation_log"))>=6,"student and master audit saved")
   Console.WriteLine(JsonSerializer.Serialize(New With {.profile="VB.NET_WinForms",.status="PASS",.checks=checks,.retainedFixture=True,.fixtureId=runId,.notRun={"Viewer/Staff identities","two-job conflicts","audit injected failure","commit unknown","DPI/IME/UI"}}))
  End Using
  Return 0
 End Function
End Module
