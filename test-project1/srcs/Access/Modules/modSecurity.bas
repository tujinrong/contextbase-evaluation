Attribute VB_Name = "modSecurity"
Option Explicit
Option Compare Binary
Private Declare PtrSafe Function GetUserNameW Lib "advapi32" (ByVal buffer As LongPtr, ByRef size As Long) As Long

' Evaluation adapter: trusted process identity + administrator-deployed role configuration.
' ACE direct editing remains outside the role boundary specified by COM-Access.
Public Function CurrentUserId() As String
    Dim n As Long, s As String
    n = 257: s = String$(n, vbNullChar)
    If GetUserNameW(StrPtr(s), n) = 0 Then Err.Raise vbObjectError + 116, , "E-COM-001"
    CurrentUserId = Left$(s, n - 1)
    If ScalarCount(CurrentUserId) > 64 Then Err.Raise vbObjectError + 116, , "E-COM-001"
End Function
Public Function CurrentRole() As String
    Dim fs As Object, text As Object, line As String, p As Long
    Set fs = CreateObject("Scripting.FileSystemObject")
    Set text = fs.OpenTextFile(CurrentProject.Path & "\roles.conf", 1, False, -1)
    Do Until text.AtEndOfStream
        line = text.ReadLine: p = InStr(line, "=")
        If p > 1 Then
            If StrComp(Left$(line, p - 1), CurrentUserId(), vbBinaryCompare) = 0 Then CurrentRole = Mid$(line, p + 1)
        End If
    Loop
    text.Close
    If CurrentRole <> "Reader" And CurrentRole <> "Staff" And CurrentRole <> "Admin" Then Err.Raise vbObjectError + 116, , "E-COM-001"
End Function
Public Sub Authorize(ByVal operation As String)
    Dim role As String
    role = CurrentRole()
    If operation = "Read" Then Exit Sub
    If operation = "Save" And (role = "Staff" Or role = "Admin") Then Exit Sub
    If (operation = "Delete" Or operation = "Master" Or operation = "CorrectEnded") And role = "Admin" Then Exit Sub
    Err.Raise vbObjectError + 117, , "E-COM-002"
End Sub
Public Function AuthorizationStamp() As String
    Dim fs As Object, file As Object
    Set fs = CreateObject("Scripting.FileSystemObject")
    Set file = fs.GetFile(CurrentProject.Path & "\roles.conf")
    AuthorizationStamp = CurrentUserId() & "|" & CurrentRole() & "|" & CStr(file.DateLastModified) & "|" & CStr(file.Size)
End Function
