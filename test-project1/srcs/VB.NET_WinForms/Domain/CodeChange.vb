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
    Public NotInheritable Class CodeChange
        Public ReadOnly Property CategoryId As String
        Public ReadOnly Property CodeValue As String
        Public ReadOnly Property ExpectedVersion As Long?
        Public ReadOnly Property CodeName As String
        Public ReadOnly Property DisplayOrder As Integer
        Public ReadOnly Property IsActive As Boolean
        Public ReadOnly Property ValidFrom As String
        Public ReadOnly Property ValidTo As String
        Public ReadOnly Property Remarks As String

        Public Sub New(CategoryId As String, CodeValue As String, ExpectedVersion As Long?, CodeName As String, DisplayOrder As Integer, IsActive As Boolean, ValidFrom As String, ValidTo As String, Remarks As String)
            Me.CategoryId = CategoryId
            Me.CodeValue = CodeValue
            Me.ExpectedVersion = ExpectedVersion
            Me.CodeName = CodeName
            Me.DisplayOrder = DisplayOrder
            Me.IsActive = IsActive
            Me.ValidFrom = ValidFrom
            Me.ValidTo = ValidTo
            Me.Remarks = Remarks
        End Sub
    End Class

End Namespace
