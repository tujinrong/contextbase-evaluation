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
    Public NotInheritable Class MaintenanceResult
        Public ReadOnly Property Outcome As Outcome
        Public ReadOnly Property RowVersion As Long?
        Public ReadOnly Property Message As String
        Public ReadOnly Property SameNameWarning As Boolean

        Public Sub New(Outcome As Outcome, RowVersion As Long?, Message As String, Optional SameNameWarning As Boolean = False)
            Me.Outcome = Outcome
            Me.RowVersion = RowVersion
            Me.Message = Message
            Me.SameNameWarning = SameNameWarning
        End Sub
    End Class

End Namespace
