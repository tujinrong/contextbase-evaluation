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
    Public NotInheritable Class CodeEntry
        Public ReadOnly Property CategoryId As String
        Public ReadOnly Property CodeValue As String
        Public ReadOnly Property CodeName As String
        Public ReadOnly Property DisplayOrder As Integer
        Public ReadOnly Property IsActive As Boolean
        Public ReadOnly Property ValidFrom As DateOnly
        Public ReadOnly Property ValidTo As DateOnly?
        Public ReadOnly Property IsProtected As Boolean

        Public Sub New(CategoryId As String, CodeValue As String, CodeName As String, DisplayOrder As Integer, IsActive As Boolean, ValidFrom As DateOnly, ValidTo As DateOnly?, IsProtected As Boolean)
            Me.CategoryId = CategoryId
            Me.CodeValue = CodeValue
            Me.CodeName = CodeName
            Me.DisplayOrder = DisplayOrder
            Me.IsActive = IsActive
            Me.ValidFrom = ValidFrom
            Me.ValidTo = ValidTo
            Me.IsProtected = IsProtected
        End Sub
    End Class

End Namespace
