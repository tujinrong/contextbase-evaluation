VERSION 1.0 CLASS
BEGIN
  MultiUse = -1
END
Attribute VB_Name = "clsSearchContext"
Option Explicit
Option Compare Binary
Public ContextId As String
Public Owner As String
Public AuthStamp As String
Public SessionId As String
Public FormId As String
Public AppliedCriteria As clsSearchCriteria
Public CriteriaFormatVersion As Long
Public Revision As Long
Public Page As Long
Public PageSize As Long
Public SortKey As String
Public Direction As String
Public LastUsedAt As Date
Private updating As Boolean
Public Sub Reset(Optional ByVal instanceId As String = "")
    If instanceId <> "" Then FormId = instanceId
    ContextId = GuidText(): Owner = CurrentUserId(): AuthStamp = AuthorizationStamp(): SessionId = AuthenticationSessionId()
    Set AppliedCriteria = Nothing: CriteriaFormatVersion = 2
    If Revision = 2147483647 Then Err.Raise vbObjectError + 150, , "W-SRC-002"
    Revision = Revision + 1: updating = False
    Page = 1: PageSize = 20: SortKey = "studentNo": Direction = "asc": LastUsedAt = UtcNow()
End Sub
Public Function RequestError(ByVal instanceId As String, ByVal stateId As String, ByVal expectedRevision As Variant) As String
    If Owner <> CurrentUserId() Or AuthStamp <> AuthorizationStamp() Or SessionId <> AuthenticationSessionId() Or FormId <> instanceId Or ContextId <> stateId Then
        RequestError = "E-COM-002": Exit Function
    End If
    If IsNull(expectedRevision) Then RequestError = "E-SRC-002": Exit Function
    If Not IsNumeric(expectedRevision) Then RequestError = "E-SRC-002": Exit Function
    If CDbl(expectedRevision) <> CDbl(Revision) Or updating Then RequestError = "E-SRC-002": Exit Function
    If CriteriaFormatVersion <> 2 Or UtcNow() >= DateAdd("n", 30, LastUsedAt) Then RequestError = "W-SRC-002"
End Function
Public Sub Acquire(ByVal instanceId As String, ByVal stateId As String, ByVal expectedRevision As Variant)
    Dim message As String
    message = RequestError(instanceId, stateId, expectedRevision)
    If message <> "" Then Err.Raise vbObjectError + 150, , message
    updating = True
End Sub
Public Sub Advance()
    If Not updating Then Err.Raise vbObjectError + 150, , "E-SRC-002"
    If Revision = 2147483647 Then Err.Raise vbObjectError + 150, , "W-SRC-002"
    Revision = Revision + 1: LastUsedAt = UtcNow()
End Sub
Public Sub ReleaseUpdate()
    updating = False
End Sub
