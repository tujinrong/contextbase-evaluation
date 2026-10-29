Option Compare Binary
Option Explicit
Public UserId As String
Public DisplayName As String
Public RoleId As String
Public LastActivityTick As LongLong
Public IsAuthenticated As Boolean
Public Sub Clear()
    UserId = "": DisplayName = "": RoleId = "": LastActivityTick = 0: IsAuthenticated = False
End Sub
