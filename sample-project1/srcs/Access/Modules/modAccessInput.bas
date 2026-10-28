Attribute VB_Name = "modAccessInput"
Option Explicit
Option Compare Binary

Private Declare PtrSafe Function OpenClipboard Lib "user32" (ByVal hwnd As LongPtr) As Long
Private Declare PtrSafe Function CloseClipboard Lib "user32" () As Long
Private Declare PtrSafe Function GetClipboardData Lib "user32" (ByVal format As Long) As LongPtr
Private Declare PtrSafe Function GlobalLock Lib "kernel32" (ByVal handle As LongPtr) As LongPtr
Private Declare PtrSafe Function GlobalUnlock Lib "kernel32" (ByVal handle As LongPtr) As Long
Private Declare PtrSafe Function lstrlenW Lib "kernel32" (ByVal value As LongPtr) As Long
Private Declare PtrSafe Sub CopyMemory Lib "kernel32" Alias "RtlMoveMemory" (ByVal target As LongPtr, ByVal source As LongPtr, ByVal bytes As LongPtr)

' The mask displays 3-4; the service still validates and stores seven digits.
' Validate the complete clipboard before assignment: the mask must not truncate it.
Public Function PostalPaste() As Boolean
    Dim handle As LongPtr, pointer As LongPtr, raw As String, normalized As Variant, length As Long
    Dim opened As Boolean, errorText As String
    On Error GoTo Failed
    If Screen.ActiveControl.Locked Or Not Screen.ActiveControl.Enabled Then Exit Function
    If OpenClipboard(0) = 0 Then Err.Raise vbObjectError + 188, , "E-STU-015|fieldKey=postal_code"
    opened = True: handle = GetClipboardData(13)
    If handle = 0 Then Err.Raise vbObjectError + 188, , "E-STU-015|fieldKey=postal_code"
    pointer = GlobalLock(handle)
    If pointer = 0 Then Err.Raise vbObjectError + 188, , "E-STU-015|fieldKey=postal_code"
    length = lstrlenW(pointer)
    If length > 10 Then Err.Raise vbObjectError + 188, , "E-STU-015|fieldKey=postal_code"
    raw = String$(length, vbNullChar)
    If length > 0 Then CopyMemory StrPtr(raw), pointer, CLngPtr(length) * 2
    GlobalUnlock handle: pointer = 0
    Call CloseClipboard
    opened = False
    normalized = TextValue(raw, 10, 7, "postal")
    If Not IsNull(normalized) Then
        If Not Match(CStr(normalized), "^[0-9]{7}$") Then Err.Raise vbObjectError + 188, , "E-STU-015|fieldKey=postal_code"
    End If
    Screen.ActiveControl.Value = normalized
    Screen.ActiveForm!lblMessage.Caption = ""
    DirtyEdit
    PostalPaste = True
    Exit Function
Failed:
    errorText = Err.Description
    On Error Resume Next
    If pointer <> 0 Then GlobalUnlock handle
    If opened Then CloseClipboard
    Screen.ActiveForm!lblMessage.Caption = MessageText("E-STU-015|fieldKey=postal_code")
End Function

Public Sub PostalKeyDown(ByRef KeyCode As Integer, ByVal Shift As Integer)
    If (KeyCode = vbKeyV And (Shift And 2) <> 0) Or (KeyCode = vbKeyInsert And (Shift And 1) <> 0) Then
        KeyCode = 0
        PostalPaste
    End If
End Sub

Public Sub PostalKeyPress(ByRef KeyAscii As Integer)
    Dim value As Long
    value = CLng(KeyAscii) And &HFFFF&
    If value >= &HFF10& And value <= &HFF19& Then KeyAscii = CInt(value - &HFF10& + 48)
    If value = &HFF0D& Or value = &H2010& Or value = &H2011& Or value = &H2212& Then KeyAscii = 45
End Sub

Public Sub PostalBeforeUpdate(ByRef Cancel As Integer)
    Dim normalized As Variant
    On Error GoTo Invalid
    normalized = TextValue(Screen.ActiveControl.Value, 10, 7, "postal")
    If Not IsNull(normalized) Then
        If Not Match(CStr(normalized), "^[0-9]{7}$") Then GoTo Invalid
    End If
    Exit Sub
Invalid:
    Cancel = True
    Screen.ActiveForm!lblMessage.Caption = MessageText("E-STU-015|fieldKey=postal_code")
End Sub
