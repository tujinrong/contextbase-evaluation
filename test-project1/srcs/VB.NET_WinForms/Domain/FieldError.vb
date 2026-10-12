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
    Public NotInheritable Class FieldError
        Public ReadOnly Property Field As String
        Public ReadOnly Property Code As String
        Public ReadOnly Property Message As String

        Public Sub New(Field As String, Code As String, Message As String)
            Me.Field = Field
            Me.Code = Code
            Me.Message = Message
        End Sub
    End Class

End Namespace
