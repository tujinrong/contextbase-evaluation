Attribute VB_Name = "modFailure"
Option Explicit
Option Compare Binary

' Keep the original error before rollback. The log stores numeric diagnostics, never SQL/field values.
Public Function FailureMessage(ByVal original As String, ByVal number As Long, ByVal operation As String) As String
    Dim correlation As String, daoError As DAO.Error, numbers As String, conflict As Boolean
    On Error Resume Next
    conflict = number = 3188 Or number = 3197 Or number = 3218 Or number = 3260
    For Each daoError In DBEngine.Errors
        numbers = numbers & CStr(daoError.Number) & ","
        If daoError.Number = 3188 Or daoError.Number = 3197 Or daoError.Number = 3218 Or daoError.Number = 3260 Then conflict = True
    Next
    If Left$(original, 2) = "E-" Or Left$(original, 2) = "W-" Then
        FailureMessage = original
    ElseIf conflict Then
        FailureMessage = "E-STU-105"
    Else
        correlation = GuidText()
        FailureMessage = "E-COM-004|correlationId=" & correlation
    End If
    If correlation <> "" Or conflict Then
        Dim fs As Object, stream As Object
        Set fs = CreateObject("Scripting.FileSystemObject")
        Set stream = fs.OpenTextFile(CurrentProject.Path & "\diagnostics.log", 8, True, -1)
        stream.WriteLine Format$(UtcNow(), "yyyy-mm-dd\Thh:nn:ss") & "Z" & vbTab & correlation & vbTab & operation & vbTab & CStr(number) & vbTab & numbers
        stream.Close
    End If
End Function
