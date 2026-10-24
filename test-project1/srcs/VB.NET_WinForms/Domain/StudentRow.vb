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
    Public NotInheritable Class StudentRow
        Public ReadOnly Property StudentId As Long
        Public ReadOnly Property StudentNo As String
        Public ReadOnly Property StudentName As String
        Public ReadOnly Property StudentNameKana As String
        Public ReadOnly Property BirthDate As DateOnly
        Public ReadOnly Property SchoolYear As Integer?
        Public ReadOnly Property GradeName As String
        Public ReadOnly Property ClassCode As String
        Public ReadOnly Property ClassName As String
        Public ReadOnly Property EnrollmentStatusName As String

        Public Sub New(StudentId As Long, StudentNo As String, StudentName As String, StudentNameKana As String, BirthDate As DateOnly, SchoolYear As Integer?, GradeName As String, ClassCode As String, ClassName As String, EnrollmentStatusName As String)
            Me.StudentId = StudentId
            Me.StudentNo = StudentNo
            Me.StudentName = StudentName
            Me.StudentNameKana = StudentNameKana
            Me.BirthDate = BirthDate
            Me.SchoolYear = SchoolYear
            Me.GradeName = GradeName
            Me.ClassCode = ClassCode
            Me.ClassName = ClassName
            Me.EnrollmentStatusName = EnrollmentStatusName
        End Sub

        Public ReadOnly Property BirthDateWareki As String
            Get
                Return ToWareki(BirthDate)
            End Get
        End Property
    End Class

End Namespace
