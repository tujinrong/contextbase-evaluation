Imports System.Security.Principal
Imports System.Threading
Imports System.Threading.Tasks
Imports Microsoft.Data.SqlClient
Imports Core = StudentManagement.Core

Namespace Application
    ' COM-VB.NET_WinForms: trusted evaluation adapter; DB roles remain authoritative.
    Public Class StudentApplicationService
        Private ReadOnly _connection As String
        Private ReadOnly _service As Core.IStudentService
        Private _user As Core.CurrentUser
        Public Sub New(connection As String)
            _connection = New SqlConnectionStringBuilder(connection) With {.Encrypt = SqlConnectionEncryptOption.Mandatory, .TrustServerCertificate = False}.ConnectionString
            _user = New Core.CurrentUser(WindowsIdentity.GetCurrent().Name, Guid.NewGuid().ToString("D"), Core.Role.Viewer)
            _service = New Core.SqlServerStudentService(connection, Function() _user, webTokens:=False)
        End Sub
        Public ReadOnly Property User As Core.CurrentUser
            Get
                Return _user
            End Get
        End Property
        Public ReadOnly Property CanEdit As Boolean
            Get
                Return _user.Role <> Core.Role.Viewer
            End Get
        End Property
        Public ReadOnly Property CanDelete As Boolean
            Get
                Return _user.Role = Core.Role.Administrator
            End Get
        End Property
        Public Async Function AuthenticateAsync(ct As CancellationToken) As Task
            Using connection As New SqlConnection(_connection)
                Await connection.OpenAsync(ct)
                Using command As New SqlCommand("SELECT ORIGINAL_LOGIN(), IS_ROLEMEMBER(N'student_admin'), IS_ROLEMEMBER(N'student_staff'), IS_ROLEMEMBER(N'student_viewer')", connection)
                    Using reader = Await command.ExecuteReaderAsync(ct)
                        If Not Await reader.ReadAsync(ct) Then Throw New InvalidOperationException("認証主体を取得できませんでした。")
                        Dim admin = Not reader.IsDBNull(1) AndAlso reader.GetInt32(1) = 1
                        Dim staff = Not reader.IsDBNull(2) AndAlso reader.GetInt32(2) = 1
                        Dim viewer = Not reader.IsDBNull(3) AndAlso reader.GetInt32(3) = 1
                        If Not admin AndAlso Not staff AndAlso Not viewer Then Throw New InvalidOperationException("学生管理の参照権限がありません。")
                        _user = New Core.CurrentUser(reader.GetString(0), _user.SessionId, If(admin, Core.Role.Administrator, If(staff, Core.Role.Staff, Core.Role.Viewer)))
                    End Using
                End Using
            End Using
        End Function
        Public Async Function LookupAsync(ct As CancellationToken, Optional includeOccupancy As Boolean = True) As Task(Of Core.LookupSet)
            Await AuthenticateAsync(ct)
            Return Await _service.LookupAsync(includeOccupancy, ct)
        End Function
        Public Async Function SearchAsync(criteria As Core.SearchCriteria, ct As CancellationToken) As Task(Of Core.SearchResult)
            Await AuthenticateAsync(ct)
            Return Await _service.SearchAsync(criteria, ct)
        End Function
        Public Async Function GetAsync(id As Long, ct As CancellationToken) As Task(Of Core.StudentDetail)
            Await AuthenticateAsync(ct)
            Return Await _service.GetAsync(id, ct)
        End Function
        Public Async Function SaveAsync(command As Core.SaveRequest, ct As CancellationToken) As Task(Of Core.SaveResult)
            Await AuthenticateAsync(ct)
            Return Await _service.SaveAsync(command, ct)
        End Function
        Public Async Function DeleteAsync(id As Long, version As Long, reason As String, ct As CancellationToken) As Task(Of Core.SaveResult)
            Await AuthenticateAsync(ct)
            Return Await _service.DeleteAsync(id, version, reason, ct)
        End Function
    End Class
End Namespace
