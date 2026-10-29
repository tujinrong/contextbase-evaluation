Option Compare Binary
Option Explicit
Private Type WINMSG
    hwnd As LongPtr
    message As Long
    padding As Long
    wParam As LongPtr
    lParam As LongPtr
    time As Long
    x As Long
    y As Long
    reserved As Long
End Type
Private Declare PtrSafe Function CreateFileW Lib "kernel32" (ByVal name As LongPtr, ByVal access As Long, ByVal sharing As Long, ByVal security As LongPtr, ByVal disposition As Long, ByVal flags As Long, ByVal template As LongPtr) As LongPtr
Private Declare PtrSafe Function GetFinalPathNameByHandleW Lib "kernel32" (ByVal h As LongPtr, ByVal buffer As LongPtr, ByVal capacity As Long, ByVal flags As Long) As Long
Private Declare PtrSafe Function CreateMutexW Lib "kernel32" (ByVal security As LongPtr, ByVal owned As Long, ByVal name As LongPtr) As LongPtr
Private Declare PtrSafe Function ReleaseMutex Lib "kernel32" (ByVal h As LongPtr) As Long
Private Declare PtrSafe Function CloseHandle Lib "kernel32" (ByVal h As LongPtr) As Long
Private Declare PtrSafe Function MsgWaitForMultipleObjectsEx Lib "user32" (ByVal count As Long, ByRef h As LongPtr, ByVal milliseconds As Long, ByVal wakeMask As Long, ByVal flags As Long) As Long
Private Declare PtrSafe Function PeekMessageW Lib "user32" (ByRef m As WINMSG, ByVal hwnd As LongPtr, ByVal first As Long, ByVal last As Long, ByVal flags As Long) As Long
Private Declare PtrSafe Function TranslateMessage Lib "user32" (ByRef m As WINMSG) As Long
Private Declare PtrSafe Function DispatchMessageW Lib "user32" (ByRef m As WINMSG) As LongPtr
Private gateDepth As Long
Private waiting As Boolean
Public Function GateIsOwned() As Boolean
    GateIsOwned = (gateDepth > 0)
End Function
Public Function AcquireGate(ByRef abandoned As Boolean) As LongPtr
    Dim h As LongPtr, file As LongPtr, full As String, name As String, n As Long, deadline As LongLong, remaining As Long, outcome As Long, m As WINMSG, ownsWaiting As Boolean
    On Error GoTo Failed
    If gateDepth <> 0 Or waiting Then Err.Raise vbObjectError + 720, , "MSG-029"
    waiting = True: ownsWaiting = True
    full = CurrentProject.FullName
    file = CreateFileW(StrPtr(full), &H80, 7, 0, 3, 0, 0)
    If file = -1 Or file = 0 Then Err.Raise vbObjectError + 721, , "MSG-020"
    full = String$(32768, vbNullChar)
    n = GetFinalPathNameByHandleW(file, StrPtr(full), Len(full), 0)
    CloseHandle file: file = 0
    If n <= 0 Or n >= Len(full) Then Err.Raise vbObjectError + 721, , "MSG-020"
    full = UCase$(Left$(full, n))
    name = "Global\SP2Access_" & Sha256(full)
    h = CreateMutexW(0, 0, StrPtr(name))
    If h = 0 Then Err.Raise vbObjectError + 721, , "MSG-027"
    deadline = GetTickCount64() + 10000
    Do
        remaining = CLng(deadline - GetTickCount64())
        If remaining <= 0 Then Err.Raise vbObjectError + 722, , "MSG-027"
        outcome = MsgWaitForMultipleObjectsEx(1, h, remaining, &H4FF, &H4)
        Select Case outcome
            Case 0, 128
                abandoned = (outcome = 128): gateDepth = 1: waiting = False: AcquireGate = h: Exit Function
            Case 1
                Do While PeekMessageW(m, 0, 0, 0, 1) <> 0
                    TranslateMessage m: DispatchMessageW m
                Loop
            Case 258
                Err.Raise vbObjectError + 722, , "MSG-027"
            Case Else
                Err.Raise vbObjectError + 721, , "MSG-027"
        End Select
    Loop
Failed:
    n = Err.Number: name = Err.Description
    If file <> 0 And file <> -1 Then CloseHandle file
    If h <> 0 Then CloseHandle h
    If ownsWaiting Then waiting = False
    Err.Raise n, , name
End Function
Public Sub ReleaseGate(ByVal h As LongPtr)
    If h = 0 Or gateDepth <> 1 Then Exit Sub
    ReleaseMutex h: CloseHandle h: gateDepth = 0
End Sub
