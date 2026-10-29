Option Compare Binary
Option Explicit
Private Type SYSTEMTIME
    y As Integer
    m As Integer
    dow As Integer
    d As Integer
    h As Integer
    n As Integer
    s As Integer
    ms As Integer
End Type
Public Declare PtrSafe Function GetTickCount64 Lib "kernel32" () As LongLong
Private Declare PtrSafe Sub GetSystemTime Lib "kernel32" (ByRef value As SYSTEMTIME)
Private counter As Long
Public Function UtcNow() As Date
    Dim t As SYSTEMTIME
    GetSystemTime t
    UtcNow = DateSerial(t.y, t.m, t.d) + TimeSerial(t.h, t.n, t.s)
End Function
Public Function BusinessDate() As Date
    Dim d As Date: d = DateAdd("h", 9, UtcNow())
    BusinessDate = DateSerial(Year(d), Month(d), Day(d))
End Function
Public Function NewRequestId() As String
    If counter = 2147483647 Then Err.Raise vbObjectError + 701, , "MSG-029"
    counter = counter + 1
    NewRequestId = CStr(GetTickCount64()) & "_" & CStr(counter) & "_" & RandomToken()
End Function
