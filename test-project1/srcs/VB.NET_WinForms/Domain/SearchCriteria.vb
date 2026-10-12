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
    Public NotInheritable Class SearchCriteria
        Public Property StudentNo As String
        Public Property StudentName As String
        Public Property StudentNameKana As String
        Public Property SchoolYear As Integer?
        Public Property GradeCode As String
        Public Property ClassId As Long?
        Public Property UnassignedOnly As Boolean
        Public Property EnrollmentStatusCodes As String() = New String() {"01", "02"}
        Public Property PrefectureCode As String
        Public Property PhoneNumber As String
        Public Property AdmissionFrom As String
        Public Property AdmissionTo As String
        Public Property Page As Integer = 1
        Public Property PageSize As Integer = 20
        Public Property SortKey As String = "studentNo"
        Public Property SortDirection As String = "asc"
    End Class

End Namespace
