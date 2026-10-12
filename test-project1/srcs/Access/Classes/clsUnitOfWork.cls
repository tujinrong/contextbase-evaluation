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
    backend = CurrentDb.Properties("StudentBackendPath")
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
    If inTx Then Workspace.Rollback: inTx = False
End Sub
Public Sub CloseWork()
    Rollback
    If Not Database Is Nothing Then Database.Close
    If Not Workspace Is Nothing Then Workspace.Close
    Set Database = Nothing: Set Workspace = Nothing
End Sub
Private Sub Class_Terminate()
    On Error Resume Next
    CloseWork
End Sub
