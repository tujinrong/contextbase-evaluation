Option Compare Binary
Option Explicit
Private Declare PtrSafe Function BCryptOpenAlgorithmProvider Lib "bcrypt" (ByRef h As LongPtr, ByVal alg As LongPtr, ByVal implementation As LongPtr, ByVal flags As Long) As Long
Private Declare PtrSafe Function BCryptCloseAlgorithmProvider Lib "bcrypt" (ByVal h As LongPtr, ByVal flags As Long) As Long
Private Declare PtrSafe Function BCryptGenRandom Lib "bcrypt" (ByVal h As LongPtr, ByRef buffer As Byte, ByVal length As Long, ByVal flags As Long) As Long
Private Declare PtrSafe Function BCryptDeriveKeyPBKDF2 Lib "bcrypt" (ByVal h As LongPtr, ByRef password As Byte, ByVal passwordLength As Long, ByRef salt As Byte, ByVal saltLength As Long, ByVal iterations As LongLong, ByRef output As Byte, ByVal outputLength As Long, ByVal flags As Long) As Long
Private Declare PtrSafe Function BCryptHash Lib "bcrypt" (ByVal h As LongPtr, ByVal secret As LongPtr, ByVal secretLength As Long, ByRef inputBytes As Byte, ByVal inputLength As Long, ByRef output As Byte, ByVal outputLength As Long) As Long
Private Declare PtrSafe Function WideCharToMultiByte Lib "kernel32" (ByVal cp As Long, ByVal flags As Long, ByVal value As LongPtr, ByVal chars As Long, ByVal bytes As LongPtr, ByVal capacity As Long, ByVal defaultChar As LongPtr, ByVal usedDefault As LongPtr) As Long
Public Function Utf8(ByVal value As String) As Byte()
    Dim b() As Byte, n As Long
    If Len(value) = 0 Then Err.Raise vbObjectError + 710, , "MSG-005"
    n = WideCharToMultiByte(65001, &H80, StrPtr(value), Len(value), 0, 0, 0, 0)
    If n <= 0 Then Err.Raise vbObjectError + 710, , "MSG-005"
    ReDim b(0 To n - 1)
    If WideCharToMultiByte(65001, &H80, StrPtr(value), Len(value), VarPtr(b(0)), n, 0, 0) <> n Then Err.Raise vbObjectError + 710, , "MSG-005"
    Utf8 = b
End Function
Private Function HexBytes(ByRef b() As Byte) As String
    Dim i As Long, s As String
    For i = LBound(b) To UBound(b): s = s & LCase$(Right$("0" & Hex$(b(i)), 2)): Next
    HexBytes = s
End Function
Private Function FromHex(ByVal s As String) As Byte()
    Dim b(0 To 31) As Byte, i As Long, c As String
    If Len(s) <> 64 Then Err.Raise vbObjectError + 711, , "MSG-001"
    For i = 1 To 64
        c = Mid$(s, i, 1)
        If InStr(1, "0123456789abcdef", c, vbBinaryCompare) = 0 Then Err.Raise vbObjectError + 711, , "MSG-001"
    Next
    For i = 0 To 31: b(i) = CByte("&H" & Mid$(s, i * 2 + 1, 2)): Next
    FromHex = b
End Function
Private Function Derive(ByVal password As String, ByRef salt() As Byte) As Byte()
    Dim h As LongPtr, b() As Byte, output(0 To 31) As Byte, algorithm As String, number As Long
    On Error GoTo Failed
    algorithm = "SHA256": b = Utf8(password)
    If BCryptOpenAlgorithmProvider(h, StrPtr(algorithm), 0, &H8) <> 0 Then Err.Raise vbObjectError + 712
    If BCryptDeriveKeyPBKDF2(h, b(0), UBound(b) + 1, salt(0), 32, CLngLng(600000), output(0), 32, 0) <> 0 Then Err.Raise vbObjectError + 712
    BCryptCloseAlgorithmProvider h, 0: h = 0
    Erase b: Derive = output: Erase output
    Exit Function
Failed:
    number = Err.Number
    If h <> 0 Then BCryptCloseAlgorithmProvider h, 0
    Erase b: Erase output
    Err.Raise number, , "MSG-001"
End Function
Public Function NewVerifier(ByVal password As String) As String
    Dim salt(0 To 31) As Byte, derived() As Byte
    CheckText password, 128, True, "パスワード", False
    If ScalarLength(password) < 12 Then Err.Raise vbObjectError + 713, , "MSG-005|パスワード"
    If BCryptGenRandom(0, salt(0), 32, &H2) <> 0 Then Err.Raise vbObjectError + 712, , "MSG-001"
    derived = Derive(password, salt)
    NewVerifier = "PBKDF2-SHA256$v=1$i=600000$s=" & HexBytes(salt) & "$dk=" & HexBytes(derived)
    Erase salt: Erase derived
End Function
Public Function VerifyPassword(ByVal password As String, ByVal verifier As String) As Boolean
    Dim pieces() As String, salt() As Byte, expected() As Byte, actual() As Byte, i As Long, difference As Long
    On Error GoTo Denied
    If ScalarLength(password) < 12 Or ScalarLength(password) > 128 Then Exit Function
    pieces = Split(verifier, "$")
    If UBound(pieces) <> 4 Then Exit Function
    If pieces(0) <> "PBKDF2-SHA256" Or pieces(1) <> "v=1" Or pieces(2) <> "i=600000" Then Exit Function
    If Left$(pieces(3), 2) <> "s=" Or Left$(pieces(4), 3) <> "dk=" Then Exit Function
    salt = FromHex(Mid$(pieces(3), 3)): expected = FromHex(Mid$(pieces(4), 4))
    actual = Derive(password, salt)
    For i = 0 To 31: difference = difference Or (expected(i) Xor actual(i)): Next
    VerifyPassword = (difference = 0)
Denied:
    Erase salt: Erase expected: Erase actual
End Function
Public Function Sha256(ByVal value As String) As String
    Dim h As LongPtr, b() As Byte, output(0 To 31) As Byte, algorithm As String, n As Long
    On Error GoTo Failed
    algorithm = "SHA256": b = Utf8(value)
    If BCryptOpenAlgorithmProvider(h, StrPtr(algorithm), 0, 0) <> 0 Then Err.Raise vbObjectError + 712
    If BCryptHash(h, 0, 0, b(0), UBound(b) + 1, output(0), 32) <> 0 Then Err.Raise vbObjectError + 712
    Sha256 = HexBytes(output): BCryptCloseAlgorithmProvider h, 0: Erase b
    Exit Function
Failed:
    n = Err.Number
    If h <> 0 Then BCryptCloseAlgorithmProvider h, 0
    Erase b: Err.Raise n, , "MSG-020"
End Function
Public Function RandomToken() As String
    Dim bytes(0 To 15) As Byte
    If BCryptGenRandom(0, bytes(0), 16, &H2) <> 0 Then Reject "MSG-020"
    RandomToken = HexBytes(bytes): Erase bytes
End Function
Public Function FileContentHash(ByVal path As String) As String
    Dim bytes() As Byte, length As Long, number As Integer, h As LongPtr, output(0 To 31) As Byte, alg As String, errNumber As Long
    On Error GoTo Failed
    number = FreeFile: Open path For Binary Access Read Lock Write As #number
    length = LOF(number): ReDim bytes(0 To IIf(length > 0, length - 1, 0))
    If length > 0 Then Get #number, , bytes
    Close #number: number = 0: alg = "SHA256"
    If BCryptOpenAlgorithmProvider(h, StrPtr(alg), 0, 0) <> 0 Then Reject "MSG-013"
    If BCryptHash(h, 0, 0, bytes(0), length, output(0), 32) <> 0 Then Reject "MSG-013"
    FileContentHash = HexBytes(output): BCryptCloseAlgorithmProvider h, 0: Erase bytes: Exit Function
Failed:
    errNumber = Err.Number
    On Error Resume Next
    If number <> 0 Then Close #number
    If h <> 0 Then BCryptCloseAlgorithmProvider h, 0
    Erase bytes
    On Error GoTo 0
    Err.Raise errNumber, , "MSG-013"
End Function
