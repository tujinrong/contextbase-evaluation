Option Compare Binary
Option Explicit
' Own only short synchronous display batches. Never hold a scope through a
' dialog, export, DoEvents or deferred Timer job. Access resets Form.Painting
' on focus changes; Echo covers the whole native Open/Activate/Close batch.
Private scopes As Object
Private nextToken As Long
Private echoOwned As Boolean
Private layoutWrites As Long
Public Function UiBeginPaint() As Long
    Dim token As Long, outer As Boolean, number As Long, description As String
    On Error GoTo Failed
    If scopes Is Nothing Then Set scopes = CreateObject("Scripting.Dictionary")
    outer = (scopes.Count = 0)
    If outer Then echoOwned = True: Application.Echo False
    Do
        If nextToken >= 2147483646 Then nextToken = 0
        nextToken = nextToken + 1: token = nextToken
    Loop While scopes.Exists(CStr(token))
    scopes.Add CStr(token), True: UiBeginPaint = token
    Exit Function
Failed:
    number = Err.Number: description = Err.Description
    If outer And echoOwned Then
        On Error Resume Next
        Application.Echo True: echoOwned = False
        On Error GoTo 0
    End If
    Err.Raise number, "SP2.UiBeginPaint", description
End Function
Public Sub UiEndPaint(ByRef token As Long)
    Dim owned As Long
    owned = token
    If owned = 0 Or scopes Is Nothing Then token = 0: Exit Sub
    If Not scopes.Exists(CStr(owned)) Then token = 0: Exit Sub
    ' Keep the last ownership entry/token until Echo True succeeds. A caller's
    ' error cleanup can retry restoration without losing the only live handle.
    If scopes.Count = 1 And echoOwned Then
        Application.Echo True
        echoOwned = False
    End If
    scopes.Remove CStr(owned): token = 0
End Sub
Public Function UiPaintDepth() As Long
    If Not scopes Is Nothing Then UiPaintDepth = scopes.Count
End Function
Public Function UiPaintOwnsEcho() As Boolean
    UiPaintOwnsEcho = echoOwned
End Function
Public Sub UiRecoverPaint()
    ' Explicit recovery for an interrupted owned display batch; not normal flow.
    Application.Echo True
    echoOwned = False: Set scopes = Nothing
End Sub
Public Function UiSetIfChanged(ByVal target As Object, ByVal propertyName As String, ByVal desired As Variant) As Boolean
    Dim current As Variant, equal As Boolean
    current = CallByName(target, propertyName, VbGet)
    If IsNull(current) Or IsNull(desired) Then
        equal = IsNull(current) And IsNull(desired)
    ElseIf VarType(current) = vbString Or VarType(desired) = vbString Then
        equal = (StrComp(CStr(current), CStr(desired), vbBinaryCompare) = 0)
    Else
        equal = (current = desired)
    End If
    If equal Then Exit Function
    CallByName target, propertyName, VbLet, desired
    If layoutWrites >= 2147483646 Then layoutWrites = 0
    layoutWrites = layoutWrites + 1: UiSetIfChanged = True
End Function
Public Function UiLayoutWriteCount() As Long
    UiLayoutWriteCount = layoutWrites
End Function
