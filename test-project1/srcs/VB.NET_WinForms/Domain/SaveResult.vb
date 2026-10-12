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
    Public NotInheritable Class SaveResult
        Public ReadOnly Property Outcome As Outcome
        Public ReadOnly Property StudentId As Long?
        Public ReadOnly Property RowVersion As Long?
        Public ReadOnly Property Errors As IReadOnlyList(Of FieldError)
        Public ReadOnly Property ConfirmationToken As String
        Public ReadOnly Property CandidateCount As Integer
        Public ReadOnly Property Candidates As IReadOnlyList(Of StudentRow)
        Public ReadOnly Property RequestId As String

        Public Sub New(Outcome As Outcome, StudentId As Long?, RowVersion As Long?, Errors As IReadOnlyList(Of FieldError), Optional ConfirmationToken As String = Nothing, Optional CandidateCount As Integer = 0, Optional Candidates As IReadOnlyList(Of StudentRow) = Nothing, Optional RequestId As String = Nothing)
            Me.Outcome = Outcome
            Me.StudentId = StudentId
            Me.RowVersion = RowVersion
            Me.Errors = Errors
            Me.ConfirmationToken = ConfirmationToken
            Me.CandidateCount = CandidateCount
            Me.Candidates = Candidates
            Me.RequestId = RequestId
        End Sub
    End Class

End Namespace
