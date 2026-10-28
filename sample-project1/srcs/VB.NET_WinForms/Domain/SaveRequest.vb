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
    Public NotInheritable Class SaveRequest
        Public ReadOnly Property Draft As StudentDraft
        Public ReadOnly Property StudentId As Long?
        Public ReadOnly Property ExpectedVersion As Long?
        Public ReadOnly Property SchoolYear As Integer?
        Public ReadOnly Property GradeCode As String
        Public ReadOnly Property ConfirmationToken As String
        Public ReadOnly Property Reason As String

        Public Sub New(Draft As StudentDraft, Optional StudentId As Long? = Nothing, Optional ExpectedVersion As Long? = Nothing, Optional SchoolYear As Integer? = Nothing, Optional GradeCode As String = Nothing, Optional ConfirmationToken As String = Nothing, Optional Reason As String = Nothing)
            Me.Draft = Draft
            Me.StudentId = StudentId
            Me.ExpectedVersion = ExpectedVersion
            Me.SchoolYear = SchoolYear
            Me.GradeCode = GradeCode
            Me.ConfirmationToken = ConfirmationToken
            Me.Reason = Reason
        End Sub
    End Class

End Namespace
