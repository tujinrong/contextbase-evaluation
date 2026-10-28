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
    Public NotInheritable Class InputValidationException
        Inherits Exception
        Public Sub New(errors As IReadOnlyList(Of FieldError))
            MyBase.New("ValidationFailed")
            Me.Errors = errors
        End Sub

        Public ReadOnly Property Errors As IReadOnlyList(Of FieldError)
    End Class

End Namespace
