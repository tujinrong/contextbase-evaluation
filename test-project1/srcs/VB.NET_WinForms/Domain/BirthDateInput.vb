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
    Public NotInheritable Class BirthDateInput
        Public ReadOnly Property Era As String
        Public ReadOnly Property Year As String
        Public ReadOnly Property Month As String
        Public ReadOnly Property Day As String

        Public Sub New(Optional Era As String = "", Optional Year As String = "", Optional Month As String = "", Optional Day As String = "")
            Me.Era = Era
            Me.Year = Year
            Me.Month = Month
            Me.Day = Day
        End Sub
    End Class

End Namespace
