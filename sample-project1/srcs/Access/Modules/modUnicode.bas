Attribute VB_Name = "modUnicode"
Option Explicit
Option Compare Binary

Private Declare PtrSafe Function NormalizeString Lib "Normaliz.dll" (ByVal normForm As Long, ByVal src As LongPtr, ByVal srcLen As Long, ByVal dst As LongPtr, ByVal dstLen As Long) As Long
Private Declare PtrSafe Function LCMapStringEx Lib "kernel32" (ByVal locale As LongPtr, ByVal flags As Long, ByVal src As LongPtr, ByVal srcLen As Long, ByVal dst As LongPtr, ByVal dstLen As Long, ByVal version As LongPtr, ByVal reserved As LongPtr, ByVal sortHandle As LongPtr) As Long

' COM-STU-005 / N-01..09 / T-02,T-25. UTF-16 storage and scalar limits are separate.
Public Function ScalarCount(ByVal s As String) As Long
    Dim i As Long, u As Long, v As Long
    i = 1
    Do While i <= Len(s)
        u = AscW(Mid$(s, i, 1)) And &HFFFF&
        If u >= &HD800& And u <= &HDBFF& Then
            If i = Len(s) Then Err.Raise vbObjectError + 102, , "Invalid surrogate"
            v = AscW(Mid$(s, i + 1, 1)) And &HFFFF&
            If v < &HDC00& Or v > &HDFFF& Then Err.Raise vbObjectError + 102, , "Invalid surrogate"
            i = i + 1
        ElseIf u >= &HDC00& And u <= &HDFFF& Then
            Err.Raise vbObjectError + 102, , "Invalid surrogate"
        End If
        ScalarCount = ScalarCount + 1
        i = i + 1
    Loop
End Function

Public Function IsWhite(ByVal n As Long) As Boolean
    IsWhite = (n >= 9 And n <= 13) Or n = 32 Or n = &H85 Or n = &HA0 Or n = &H1680 Or (n >= &H2000 And n <= &H200A) Or n = &H2028 Or n = &H2029 Or n = &H202F Or n = &H205F Or n = &H3000
End Function

Public Function TrimUnicode(ByVal s As String) As String
    Dim a As Long, b As Long
    a = 1: b = Len(s)
    Do While a <= b
        If Not IsWhite(AscW(Mid$(s, a, 1)) And &HFFFF&) Then Exit Do
        a = a + 1
    Loop
    Do While b >= a
        If Not IsWhite(AscW(Mid$(s, b, 1)) And &HFFFF&) Then Exit Do
        b = b - 1
    Loop
    If b >= a Then TrimUnicode = Mid$(s, a, b - a + 1)
End Function

Public Function NFKC(ByVal s As String) As String
    Dim n As Long, out As String
    If Len(s) = 0 Then Exit Function
    n = NormalizeString(5, StrPtr(s), Len(s), 0, 0)
    If n = 0 Then Err.Raise vbObjectError + 103, , "Unicode normalization failed"
    If n < 0 Then n = -n
    out = String$(n, vbNullChar)
    n = NormalizeString(5, StrPtr(s), Len(s), StrPtr(out), Len(out))
    If n < 0 Then
        out = String$(-n, vbNullChar)
        n = NormalizeString(5, StrPtr(s), Len(s), StrPtr(out), Len(out))
    End If
    If n <= 0 Then Err.Raise vbObjectError + 103, , "Unicode normalization failed"
    NFKC = Left$(out, n)
End Function

Public Function InvariantUpper(ByVal s As String) As String
    Dim invariant As String, n As Long, out As String
    If Len(s) = 0 Then Exit Function
    invariant = vbNullChar
    n = LCMapStringEx(StrPtr(invariant), &H200, StrPtr(s), Len(s), 0, 0, 0, 0, 0)
    If n = 0 Then Err.Raise vbObjectError + 104, , "Case conversion failed"
    out = String$(n, vbNullChar)
    n = LCMapStringEx(StrPtr(invariant), &H200, StrPtr(s), Len(s), StrPtr(out), Len(out), 0, 0, 0)
    If n = 0 Then Err.Raise vbObjectError + 104, , "Case conversion failed"
    InvariantUpper = Left$(out, n)
End Function

Public Function WithoutWhite(ByVal s As String) As String
    Dim i As Long
    For i = 1 To Len(s)
        If Not IsWhite(AscW(Mid$(s, i, 1)) And &HFFFF&) Then WithoutWhite = WithoutWhite & Mid$(s, i, 1)
    Next
End Function

Public Function TextValue(ByVal raw As Variant, ByVal maxRaw As Long, ByVal maxSaved As Long, ByVal kind As String) As Variant
    Dim s As String, i As Long, u As Long, out As String, lastSpace As Boolean
    s = Nz(raw, "")
    If ScalarCount(s) > maxRaw Then Err.Raise vbObjectError + 105, , "E-STU-002"
    For i = 1 To Len(s)
        u = AscW(Mid$(s, i, 1)) And &HFFFF&
        If u = 0 Or (u < 32 And Not ((kind = "memo") And (u = 10 Or u = 13))) Or (u >= 127 And u <= 159) Then Err.Raise vbObjectError + 105, , "E-STU-002"
    Next
    s = TrimUnicode(s)
    Select Case kind
    Case "code", "number": s = InvariantUpper(NFKC(s))
    Case "nameKey": s = WithoutWhite(InvariantUpper(NFKC(s)))
    Case "kana"
        s = NFKC(s)
        For i = 1 To Len(s)
            u = AscW(Mid$(s, i, 1)) And &HFFFF&
            If u >= &H3041 And u <= &H3096 Then u = u + &H60
            If u = &H309D Or u = &H309E Then u = u + &H60
            If IsWhite(u) Then
                If Not lastSpace Then out = out & " "
                lastSpace = True
            Else
                If Not (u >= &H30A1 And u <= &H30FA) And u <> &H30FC And u <> &H30FB And u <> &H30FD And u <> &H30FE Then Err.Raise vbObjectError + 106, , "E-STU-004"
                out = out & ChrW(u): lastSpace = False
            End If
        Next
        s = TrimUnicode(out)
    Case "phone", "postal"
        s = NFKC(s)
        s = Replace(s, "-", ""): s = Replace(s, ChrW(&H2010), "")
        s = Replace(s, ChrW(&H2011), ""): s = Replace(s, ChrW(&H2212), "")
        s = WithoutWhite(s)
        If kind = "phone" Then s = Replace(Replace(s, "(", ""), ")", "")
    Case "memo": s = Replace(Replace(s, vbCrLf, vbLf), vbCr, vbLf)
    Case "email"
        i = InStr(s, "@")
        If i > 0 Then s = Left$(s, i) & LCase$(Mid$(s, i + 1))
    End Select
    If ScalarCount(s) > maxSaved Then Err.Raise vbObjectError + 105, , "E-STU-002"
    If s = "" Then TextValue = Null Else TextValue = s
End Function

Public Function Match(ByVal value As String, ByVal pattern As String) As Boolean
    Dim rx As Object
    Set rx = CreateObject("VBScript.RegExp")
    rx.Pattern = pattern: rx.IgnoreCase = False: rx.Global = False
    Match = rx.Test(value)
End Function
