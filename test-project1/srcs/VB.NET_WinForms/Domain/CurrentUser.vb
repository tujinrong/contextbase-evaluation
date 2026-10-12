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
    Public NotInheritable Class CurrentUser
        Public ReadOnly Property Principal As String
        Public ReadOnly Property SessionId As String
        Public ReadOnly Property Role As Role

        Public Sub New(Principal As String, SessionId As String, Role As Role)
            Me.Principal = Principal
            Me.SessionId = SessionId
            Me.Role = Role
        End Sub
    End Class

End Namespace
