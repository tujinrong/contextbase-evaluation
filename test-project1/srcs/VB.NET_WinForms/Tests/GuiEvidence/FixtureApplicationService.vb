Imports System.Threading
Imports System.Threading.Tasks
Imports Core = StudentManagement.WinForms.Domain

Namespace Application
    ' Test-only substitution for the concrete adapter. Original UI/presenter sources are compiled unchanged.
    Public Class StudentApplicationService
        Private ReadOnly _service As Core.IStudentService
        Public ReadOnly Property User As Core.CurrentUser
        Public Sub New(service As Core.IStudentService, role As Core.Role)
            _service=service
            User=New Core.CurrentUser("FIXTURE-" & role.ToString() & ": 撮影用・DB未接続", "fixture-session",role)
        End Sub
        Public ReadOnly Property CanEdit As Boolean
            Get
                Return User.Role <> Core.Role.Viewer
            End Get
        End Property
        Public ReadOnly Property CanDelete As Boolean
            Get
                Return User.Role=Core.Role.Administrator
            End Get
        End Property
        Public Function AuthenticateAsync(ct As CancellationToken) As Task
            ct.ThrowIfCancellationRequested()
            Return Task.CompletedTask
        End Function
        Public Function LookupAsync(ct As CancellationToken,Optional includeOccupancy As Boolean=True) As Task(Of Core.LookupSet)
            Return _service.LookupAsync(includeOccupancy,ct)
        End Function
        Public Function SearchAsync(criteria As Core.SearchCriteria,sortKey As String,sortDirection As String,ct As CancellationToken) As Task(Of Core.SearchResult)
            Return _service.SearchAsync(criteria,sortKey,sortDirection,ct)
        End Function
        Public Function GetAsync(id As Long,ct As CancellationToken) As Task(Of Core.StudentDetail)
            Return _service.GetAsync(id,ct)
        End Function
        Public Function SaveAsync(command As Core.SaveRequest,ct As CancellationToken) As Task(Of Core.SaveResult)
            Return _service.SaveAsync(command,ct)
        End Function
        Public Function DeleteAsync(id As Long,version As Long,reason As String,ct As CancellationToken) As Task(Of Core.SaveResult)
            Return _service.DeleteAsync(id,version,reason,ct)
        End Function
    End Class
End Namespace
