VERSION 1.0 CLASS
BEGIN
  MultiUse = -1
END
Attribute VB_Name = "clsUnitOfWork"
Option Explicit
Option Compare Binary
Public Workspace As DAO.Workspace
Public Database As DAO.Database
Private inTx As Boolean
Public CommitStarted As Boolean
Public Sub BeginWork()
    Dim backend As String
    CommitStarted = False
    backend = CurrentDb.Properties("StudentBackendPath")
    If backend = "SELF" Then backend = CurrentProject.FullName
    Set Workspace = DBEngine.CreateWorkspace("StudentTx-" & GuidText(), "Admin", "", dbUseJet)
    Set Database = Workspace.OpenDatabase(backend)
    If Not Database.Transactions Then Err.Raise vbObjectError + 121, , "Transactions required"
    Workspace.BeginTrans: inTx = True
    Database.Execute "UPDATE t_write_guard SET lock_bit=Not lock_bit WHERE guard_id=1", dbFailOnError
    If Database.RecordsAffected <> 1 Then Err.Raise vbObjectError + 122, , "Guard missing"
End Sub
Public Sub Commit()
    CommitStarted = True
    Workspace.CommitTrans dbForceOSFlush
    inTx = False
End Sub
Public Sub Rollback()
    If Not inTx Then Exit Sub
    If Workspace Is Nothing Then
        inTx = False
        Err.Raise vbObjectError + 122, , "Rollback workspace missing"
    End If
    Workspace.Rollback
    inTx = False
End Sub
Public Sub CloseWork()
    Dim cleanupError As Long, cleanupMessage As String
    On Error Resume Next
    Rollback
    If Err.Number <> 0 Then cleanupError = Err.Number: cleanupMessage = Err.Description: Err.Clear
    inTx = False
    If Not Database Is Nothing Then Database.Close
    If Err.Number <> 0 Then cleanupError = Err.Number: cleanupMessage = Err.Description: Err.Clear
    If Not Workspace Is Nothing Then Workspace.Close
    If Err.Number <> 0 Then cleanupError = Err.Number: cleanupMessage = Err.Description: Err.Clear
    Set Database = Nothing: Set Workspace = Nothing
    If cleanupError <> 0 Then cleanupMessage = FailureMessage(cleanupMessage, cleanupError, "CloseWork")
    Err.Clear
End Sub
Private Sub Class_Terminate()
    On Error Resume Next
    CloseWork
End Sub
