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
    Public NotInheritable Class LookupSet
        Public ReadOnly Property Codes As IReadOnlyList(Of CodeEntry)
        Public ReadOnly Property Classes As IReadOnlyList(Of SchoolClass)

        Public Sub New(Codes As IReadOnlyList(Of CodeEntry), Classes As IReadOnlyList(Of SchoolClass))
            Me.Codes = Codes
            Me.Classes = Classes
        End Sub
    End Class

End Namespace
