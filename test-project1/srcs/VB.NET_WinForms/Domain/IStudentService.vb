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
    Public Interface IStudentService
        Function SearchAsync(criteria As SearchCriteria, Optional sortKey As String = "studentNo", Optional sortDirection As String = "asc", Optional ct As CancellationToken = Nothing) As Task(Of SearchResult)
        Function GetAsync(id As Long, Optional ct As CancellationToken = Nothing) As Task(Of StudentDetail)
        Function LookupAsync(Optional ct As CancellationToken = Nothing) As Task(Of LookupSet)
        Function LookupAsync(includeOccupancy As Boolean, Optional ct As CancellationToken = Nothing) As Task(Of LookupSet)
        Function SaveAsync(request As SaveRequest, Optional ct As CancellationToken = Nothing) As Task(Of SaveResult)
        Function DeleteAsync(id As Long, version As Long, reason As String, Optional ct As CancellationToken = Nothing) As Task(Of SaveResult)
    End Interface

End Namespace
