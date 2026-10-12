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
    Public NotInheritable Class SchoolClass
        Public ReadOnly Property ClassId As Long
        Public ReadOnly Property SchoolYear As Integer
        Public ReadOnly Property GradeCode As String
        Public ReadOnly Property ClassCode As String
        Public ReadOnly Property ClassName As String
        Public ReadOnly Property ValidFrom As DateOnly
        Public ReadOnly Property ValidTo As DateOnly
        Public ReadOnly Property Capacity As Integer?
        Public ReadOnly Property Occupied As Integer
        Public ReadOnly Property IsActive As Boolean

        Public Sub New(ClassId As Long, SchoolYear As Integer, GradeCode As String, ClassCode As String, ClassName As String, ValidFrom As DateOnly, ValidTo As DateOnly, Capacity As Integer?, Occupied As Integer, IsActive As Boolean)
            Me.ClassId = ClassId
            Me.SchoolYear = SchoolYear
            Me.GradeCode = GradeCode
            Me.ClassCode = ClassCode
            Me.ClassName = ClassName
            Me.ValidFrom = ValidFrom
            Me.ValidTo = ValidTo
            Me.Capacity = Capacity
            Me.Occupied = Occupied
            Me.IsActive = IsActive
        End Sub
    End Class

End Namespace
