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
    Public NotInheritable Class StudentDetail
        Public ReadOnly Property StudentId As Long
        Public ReadOnly Property RowVersion As Long
        Public ReadOnly Property Draft As StudentDraft
        Public ReadOnly Property BirthDate As DateOnly
        Public ReadOnly Property UpdatedAt As DateTimeOffset
        Public ReadOnly Property UpdatedBy As String

        Public Sub New(StudentId As Long, RowVersion As Long, Draft As StudentDraft, BirthDate As DateOnly, UpdatedAt As DateTimeOffset, UpdatedBy As String)
            Me.StudentId = StudentId
            Me.RowVersion = RowVersion
            Me.Draft = Draft
            Me.BirthDate = BirthDate
            Me.UpdatedAt = UpdatedAt
            Me.UpdatedBy = UpdatedBy
        End Sub
    End Class

End Namespace
