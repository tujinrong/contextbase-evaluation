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
    Public NotInheritable Class SearchResult
        Public ReadOnly Property Outcome As Outcome
        Public ReadOnly Property Count As Integer
        Public ReadOnly Property Items As IReadOnlyList(Of StudentRow)
        Public ReadOnly Property SearchedAt As DateTimeOffset
        Public ReadOnly Property LimitExceeded As Boolean
        Public ReadOnly Property Errors As IReadOnlyList(Of FieldError)

        Public Sub New(Outcome As Outcome, Count As Integer, Items As IReadOnlyList(Of StudentRow), SearchedAt As DateTimeOffset, LimitExceeded As Boolean, Errors As IReadOnlyList(Of FieldError))
            Me.Outcome = Outcome
            Me.Count = Count
            Me.Items = Items
            Me.SearchedAt = SearchedAt
            Me.LimitExceeded = LimitExceeded
            Me.Errors = Errors
        End Sub
    End Class

End Namespace
