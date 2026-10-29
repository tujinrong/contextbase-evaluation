Option Compare Binary
Option Explicit
Private Declare PtrSafe Function NormalizeString Lib "Normaliz" (ByVal form As Long, ByVal source As LongPtr, ByVal length As Long, ByVal target As LongPtr, ByVal capacity As Long) As Long
Private Declare PtrSafe Function LCMapStringEx Lib "kernel32" (ByVal locale As LongPtr, ByVal flags As Long, ByVal source As LongPtr, ByVal length As Long, ByVal target As LongPtr, ByVal capacity As Long, ByVal version As LongPtr, ByVal reserved As LongPtr, ByVal sortHandle As LongPtr) As Long
Public Sub Reject(ByVal message As String, Optional ByVal field As String = "")
    Err.Raise vbObjectError + 730, "SP2", message & IIf(Len(field) > 0, "|" & field, "")
End Sub
Public Function ScalarLength(ByVal s As String) As Long
    Dim i As Long, u As Long, v As Long, count As Long
    i = 1
    Do While i <= Len(s)
        u = AscW(Mid$(s, i, 1)) And &HFFFF&
        If u = 0 Or u < 32 And u <> 9 And u <> 10 And u <> 13 Or u = 127 Then Reject "MSG-005"
        If u >= &HD800& And u <= &HDBFF& Then
            If i = Len(s) Then Reject "MSG-005"
            v = AscW(Mid$(s, i + 1, 1)) And &HFFFF&
            If v < &HDC00& Or v > &HDFFF& Then Reject "MSG-005"
            i = i + 1
        ElseIf u >= &HDC00& And u <= &HDFFF& Then
            Reject "MSG-005"
        End If
        count = count + 1: i = i + 1
    Loop
    ScalarLength = count
End Function
Public Function SaveText(ByVal raw As Variant, Optional ByVal kana As Boolean = False) As Variant
    Dim s As String
    s = CStr(Nz(raw, ""))
    s = Replace(Replace(Replace(s, vbCrLf, vbLf), vbCr, vbLf), vbTab, " ")
    Do While Len(s) > 0
        If Left$(s, 1) <> " " And Left$(s, 1) <> ChrW(&H3000) And Left$(s, 1) <> vbLf Then Exit Do
        s = Mid$(s, 2)
    Loop
    Do While Len(s) > 0
        If Right$(s, 1) <> " " And Right$(s, 1) <> ChrW(&H3000) And Right$(s, 1) <> vbLf Then Exit Do
        s = Left$(s, Len(s) - 1)
    Loop
    If kana Then s = WideKana(s)
    If Len(s) = 0 Then SaveText = Null Else SaveText = s
End Function
Public Function WideKana(ByVal raw As String) As String
    Dim i As Long, first As Long, u As Long, value As String
    i = 1
    Do While i <= Len(raw)
        u = AscW(Mid$(raw, i, 1)) And &HFFFF&
        If u >= &HFF61& And u <= &HFF9F& Then
            first = i
            Do While i <= Len(raw)
                u = AscW(Mid$(raw, i, 1)) And &HFFFF&
                If u < &HFF61& Or u > &HFF9F& Then Exit Do
                i = i + 1
            Loop
            value = value & StrConv(Mid$(raw, first, i - first), vbWide, &H411)
        Else
            value = value & Mid$(raw, i, 1): i = i + 1
        End If
    Loop
    WideKana = value
End Function
Public Sub CheckKana(ByVal value As String)
    Dim i As Long, u As Long
    For i = 1 To Len(value)
        u = AscW(Mid$(value, i, 1)) And &HFFFF&
        If Not ((u >= &H30A1& And u <= &H30FA&) Or u = &H30FC& Or u = &H30FB& Or u = &H20& Or u = &H3000&) Then Reject "MSG-005", "氏名カナ"
    Next
End Sub
Public Sub CheckText(ByVal raw As Variant, ByVal maximum As Long, ByVal required As Boolean, ByVal field As String, Optional ByVal normalize As Boolean = True)
    Dim s As String, value As Variant, n As Long
    s = CStr(Nz(raw, ""))
    On Error GoTo Invalid
    n = ScalarLength(s)
    If n > maximum Then GoTo Invalid
    If normalize Then value = SaveText(s) Else value = s
    If required And (IsNull(value) Or Len(CStr(Nz(value, ""))) = 0) Then Reject "MSG-004", field
    If ScalarLength(CStr(Nz(value, ""))) > maximum Then GoTo Invalid
    Exit Sub
Invalid:
    If Left$(Err.Description, 7) = "MSG-004" Then Reject "MSG-004", field
    Reject "MSG-005", field
End Sub
Public Function Digits(ByVal s As String, ByVal count As Long) As Boolean
    Dim i As Long, c As Long
    If Len(s) <> count Then Exit Function
    For i = 1 To count
        c = AscW(Mid$(s, i, 1))
        If c < 48 Or c > 57 Then Exit Function
    Next
    Digits = True
End Function
Public Function ValidCode(ByVal s As String) As Boolean
    ValidCode = Digits(s, 2) And s <> "00"
End Function
Public Function ReadInteger(ByVal raw As Variant, ByVal field As String) As Integer
    Dim s As String: s = CStr(Nz(raw, ""))
    If Len(s) = 0 Then Reject "MSG-004", field
    If Len(s) > 3 Then Reject "MSG-005", field
    If Not Digits(s, Len(s)) Then Reject "MSG-005", field
    If CLng(s) < 1 Or CLng(s) > 999 Then Reject "MSG-005", field
    ReadInteger = CInt(s)
End Function
Public Function ReadDate(ByVal raw As Variant, ByVal monthOnly As Boolean, ByVal optionalValue As Boolean, ByVal field As String, ByVal today As Date) As Variant
    Dim s As String, y As Long, m As Long, d As Long, value As Date
    s = CStr(Nz(raw, ""))
    If s = "" And optionalValue Then ReadDate = Null: Exit Function
    If s = "" Then Reject "MSG-004", field
    If Len(s) <> IIf(monthOnly, 7, 10) Then Reject "MSG-005", field
    If Mid$(s, 5, 1) <> "-" Or Not Digits(Left$(s, 4), 4) Or Not Digits(Mid$(s, 6, 2), 2) Then Reject "MSG-005", field
    If Not monthOnly Then
        If Mid$(s, 8, 1) <> "-" Or Not Digits(Right$(s, 2), 2) Then Reject "MSG-005", field
    End If
    y = CLng(Left$(s, 4)): m = CLng(Mid$(s, 6, 2)): d = 1
    If Not monthOnly Then d = CLng(Right$(s, 2))
    If y < 1900 Or m < 1 Or m > 12 Or d < 1 Or d > 31 Then Reject "MSG-005", field
    value = DateSerial(y, m, d)
    If Year(value) <> y Or Month(value) <> m Or Day(value) <> d Then Reject "MSG-005", field
    If monthOnly Then today = DateSerial(Year(today), Month(today), 1)
    If value > today Then Reject IIf(monthOnly, "MSG-007", "MSG-005"), field
    ReadDate = value
End Function
Public Function NameKey(ByVal raw As String) As String
    Dim s As String, output As String, n As Long, locale As String
    If Len(raw) = 0 Then Exit Function
    n = NormalizeString(5, StrPtr(raw), Len(raw), 0, 0)
    If n <= 0 Then Reject "MSG-005", "氏名・カナ"
    output = String$(n, vbNullChar)
    n = NormalizeString(5, StrPtr(raw), Len(raw), StrPtr(output), n)
    If n <= 0 Then Reject "MSG-005", "氏名・カナ"
    s = Left$(output, n)
    s = Replace(Replace(Replace(Replace(Replace(s, " ", ""), ChrW(&H3000), ""), vbTab, ""), vbLf, ""), vbCr, "")
    If s = "" Then Exit Function
    locale = vbNullChar
    n = LCMapStringEx(StrPtr(locale), &H200, StrPtr(s), Len(s), 0, 0, 0, 0, 0)
    If n <= 0 Then Reject "MSG-005", "氏名・カナ"
    output = String$(n, vbNullChar)
    n = LCMapStringEx(StrPtr(locale), &H200, StrPtr(s), Len(s), StrPtr(output), n, 0, 0, 0)
    If n <= 0 Then Reject "MSG-005", "氏名・カナ"
    NameKey = Left$(output, n)
End Function
Public Function Same(ByVal a As Variant, ByVal b As Variant) As Boolean
    If IsNull(a) Or IsNull(b) Then Same = IsNull(a) And IsNull(b) Else Same = (StrComp(CStr(a), CStr(b), vbBinaryCompare) = 0)
End Function
