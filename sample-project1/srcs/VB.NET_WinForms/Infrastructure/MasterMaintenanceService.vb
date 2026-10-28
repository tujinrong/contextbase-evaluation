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
    Public NotInheritable Class MasterMaintenanceService
        Public Sub New(connectionString As String)
            Me.connectionString = connectionString
        End Sub

        Private ReadOnly connectionString As String
        Public Function SaveClassAsync(raw As ClassChange, Optional ct As CancellationToken = Nothing) As Task(Of MaintenanceResult)
            Return Execute(Function(c, tx, id) NativeStoredProcedureClient.SaveClassAsync(c, tx, raw, id, ct:=ct), ct)
        End Function
        Public Function SaveCodeAsync(raw As CodeChange, Optional ct As CancellationToken = Nothing) As Task(Of MaintenanceResult)
            Return Execute(Function(c, tx, id) NativeStoredProcedureClient.SaveCodeAsync(c, tx, raw, id, ct:=ct), ct)
        End Function
        Private Async Function Execute(pExecute As Func(Of SqlConnection, SqlTransaction, Guid, Task(Of MaintenanceResult)), ct As CancellationToken) As Task(Of MaintenanceResult)
            Dim builder = New SqlConnectionStringBuilder(connectionString) With {
    .Encrypt = SqlConnectionEncryptOption.Mandatory,
    .TrustServerCertificate = False
}
            Using connection = New SqlConnection(builder.ConnectionString)
                Await connection.OpenAsync(ct)
                Using tx = CType(Await connection.BeginTransactionAsync(IsolationLevel.ReadCommitted, ct), SqlTransaction)
                    Dim started = False, commitAttempted = False
                    Try
                        started = True
                        Dim result = Await pExecute(connection, tx, Guid.NewGuid())
                        If result.Outcome = Outcome.Saved Then
                            commitAttempted = True
                            Await tx.CommitAsync(ct)
                        Else
                            SafeRollback(tx)
                        End If
                        Return result
                    Catch e As Exception When (TypeOf e Is SqlException) OrElse (TypeOf e Is InvalidOperationException) OrElse (TypeOf e Is OperationCanceledException)
                        Dim rolledBack = SafeRollback(tx)
                        Dim unknown = started AndAlso (commitAttempted OrElse Not rolledBack)
                        Return New Global.StudentManagement.WinForms.Domain.MaintenanceResult(If(unknown, Outcome.Unknown, Outcome.SystemError), Nothing, If(unknown, "保守結果を確認できません。再実行前にマスタを照会してください。", "保守処理に失敗しました。"))
                    End Try
                End Using
            End Using
        End Function
    End Class

End Namespace
