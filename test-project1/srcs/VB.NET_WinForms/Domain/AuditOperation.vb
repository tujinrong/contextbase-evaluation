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
    Friend Module AuditOperation
        Friend Function ForMaster(previousActive As Boolean?, currentActive As Boolean) As String
            Return If(previousActive Is Nothing, "CREATE", If(previousActive = currentActive, "UPDATE", If(currentActive, "ENABLE", "DISABLE")))
        End Function
    End Module

End Namespace
