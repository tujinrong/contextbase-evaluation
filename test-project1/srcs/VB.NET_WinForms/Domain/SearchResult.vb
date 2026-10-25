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
    Public Enum SearchStatus
        Success
        ValidationError
        LimitExceeded
        Failed
    End Enum
    Public NotInheritable Class SearchResult
        Public ReadOnly Property Status As SearchStatus
            Get
                If LimitExceeded Then Return SearchStatus.LimitExceeded
                If Outcome = Global.StudentManagement.WinForms.Domain.Outcome.ValidationFailed Then Return SearchStatus.ValidationError
                If Outcome = Global.StudentManagement.WinForms.Domain.Outcome.SystemError OrElse Outcome = Global.StudentManagement.WinForms.Domain.Outcome.Forbidden Then Return SearchStatus.Failed
                Return SearchStatus.Success
            End Get
        End Property
        Public ReadOnly Property Outcome As Outcome
        Public ReadOnly Property Count As Integer?
        Public ReadOnly Property Items As IReadOnlyList(Of StudentRow)
        Public ReadOnly Property SearchedAt As DateTimeOffset?
        Public ReadOnly Property LimitExceeded As Boolean
        Public ReadOnly Property Errors As IReadOnlyList(Of FieldError)

        Public Sub New(Outcome As Outcome, Count As Integer, Items As IReadOnlyList(Of StudentRow), SearchedAt As DateTimeOffset, LimitExceeded As Boolean, Errors As IReadOnlyList(Of FieldError))
            Me.Outcome = Outcome
            Me.Count = If(LimitExceeded OrElse Outcome = Global.StudentManagement.WinForms.Domain.Outcome.ValidationFailed OrElse Outcome = Global.StudentManagement.WinForms.Domain.Outcome.SystemError OrElse Outcome = Global.StudentManagement.WinForms.Domain.Outcome.Forbidden, CType(Nothing, Integer?), Count)
            Me.Items = If(Items, Array.Empty(Of StudentRow)())
            If LimitExceeded AndAlso Me.Items.Count <> 0 Then Throw New ArgumentException("上限超過では部分結果を返せません。")
            If Me.Count.HasValue AndAlso (Me.Count.Value < 0 OrElse Me.Count.Value > 10000 OrElse Me.Items.Count <> Me.Count.Value) Then Throw New ArgumentException("全一致件数と一覧件数が一致していません。")
            Me.SearchedAt = If(Outcome = Global.StudentManagement.WinForms.Domain.Outcome.ValidationFailed OrElse Outcome = Global.StudentManagement.WinForms.Domain.Outcome.SystemError OrElse Outcome = Global.StudentManagement.WinForms.Domain.Outcome.Forbidden, CType(Nothing, DateTimeOffset?), SearchedAt)
            Me.LimitExceeded = LimitExceeded
            Me.Errors = Errors
        End Sub
    End Class

End Namespace
