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
    Friend NotInheritable Class NormalizedStudent
        Public ReadOnly Property Values As Dictionary(Of String, Object)

        Public Sub New(Values As Dictionary(Of String, Object))
            Me.Values = Values
        End Sub

        Public Function Text(key As String) As String
            Return CStr(Values(key))
        End Function
        Public Function [Date](key As String) As DateOnly
            Return CType(Values(key), DateOnly)
        End Function
        Public ReadOnly Property ClassId As Long?
            Get
                Return CType(Values("class_id"), Long?)
            End Get
        End Property
    End Class

End Namespace
