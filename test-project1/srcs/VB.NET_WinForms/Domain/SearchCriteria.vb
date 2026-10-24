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
    <System.Text.Json.Serialization.JsonUnmappedMemberHandling(System.Text.Json.Serialization.JsonUnmappedMemberHandling.Disallow)>
    Public NotInheritable Class SearchCriteria
        Public Property StudentNo As String
        Public Property StudentName As String
        Public Property ClassId As Long?
        Public Property EnrollmentStatusCodes As String() = New String() {"01", "02"}
        Public Property Page As Integer = 1
        Public Property PageSize As Integer = 20
        Public Property SortKey As String = "studentNo"
        Public Property SortDirection As String = "asc"
    End Class

End Namespace
