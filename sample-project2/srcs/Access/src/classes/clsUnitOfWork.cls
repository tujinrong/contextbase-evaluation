Option Compare Binary
Option Explicit
Public Db As DAO.Database
Private ws As DAO.Workspace
Private gate As LongPtr
Private active As Boolean
Public CommitStarted As Boolean
Public CommitReturned As Boolean
Public Sub OpenUnit(Optional ByVal transactional As Boolean = True)
    Dim abandoned As Boolean
    gate = AcquireGate(abandoned)
    ' ACE caches are process-local: refresh only after acquiring the common gate.
    ' Microsoft DAO DBEngine.Idle(dbRefreshCache), checked 2026-10-29.
    DBEngine.Idle dbRefreshCache
    Set ws = DBEngine.CreateWorkspace("SP2_" & Right$(NewRequestId(), 16), "Admin", "", dbUseJet)
    Set Db = ws.OpenDatabase(CurrentProject.FullName, False, False)
    If abandoned Then AssertIntegrity Db
    If transactional Then ws.BeginTrans: active = True
End Sub
Public Sub Commit()
    If Not active Then Err.Raise vbObjectError + 700, , "MSG-020"
    CommitStarted = True
    ws.CommitTrans dbForceOSFlush
    CommitReturned = True: active = False
End Sub
Public Function Cancel() As Boolean
    On Error GoTo Failed
    If active Then ws.Rollback: active = False
    Cancel = Not (CommitStarted And Not CommitReturned)
    Exit Function
Failed:
    Cancel = False
End Function
Public Sub CloseUnit()
    On Error Resume Next
    If active Then ws.Rollback
    active = False
    If Not Db Is Nothing Then Db.Close
    Set Db = Nothing
    If Not ws Is Nothing Then ws.Close
    Set ws = Nothing
    If gate <> 0 Then ReleaseGate gate
    gate = 0
End Sub
Private Sub Class_Terminate()
    CloseUnit
End Sub
