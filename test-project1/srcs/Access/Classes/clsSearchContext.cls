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
Public AppliedCriteria As Object
Public Page As Long
Public PageSize As Long
Public SortKey As String
Public Direction As String
Public LastUsedAt As Date
Public Sub Reset()
    ContextId = GuidText(): Owner = CurrentUserId(): AuthStamp = AuthorizationStamp(): Set AppliedCriteria = Nothing
    Page = 1: PageSize = 20: SortKey = "studentNo": Direction = "asc": LastUsedAt = UtcNow()
End Sub
Public Function Valid() As Boolean
    Valid = Owner = CurrentUserId() And AuthStamp = AuthorizationStamp() And UtcNow() < DateAdd("n", 30, LastUsedAt)
    If Valid Then LastUsedAt = UtcNow()
End Function
