Attribute VB_Name = "modStudentRules"
Option Explicit
Option Compare Binary

Public Function Map() As Object
    Set Map = CreateObject("Scripting.Dictionary")
    Map.CompareMode = vbBinaryCompare
End Function
Public Function CopyMap(ByVal original As Object) As Object
    Dim k As Variant
    Set CopyMap = Map()
    For Each k In original.Keys: CopyMap.Add k, original(k): Next
End Function
Public Function SavedFields() As Variant
    SavedFields = Split("student_no student_name student_name_kana birth_date gender_code postal_code prefecture_code address_line1 address_line2 phone_number email_address admission_date enrollment_status_code enrollment_end_date class_id emergency_contact_name relationship_code emergency_phone_number remarks", " ")
End Function
Public Function EqualValue(ByVal a As Variant, ByVal b As Variant) As Boolean
    If IsNull(a) Or IsNull(b) Then
        EqualValue = IsNull(a) And IsNull(b)
    Else
        EqualValue = StrComp(CStr(a), CStr(b), vbBinaryCompare) = 0
    End If
End Function
Public Function Fingerprint(ByVal d As Object) As String
    Dim k As Variant, s As String
    For Each k In SavedFields()
        s = Nz(d(k), "")
        Fingerprint = Fingerprint & CStr(Len(s)) & ":" & s & ";" & CStr(IsNull(d(k))) & ";"
    Next
End Function
Public Function PositiveId(ByVal v As Variant) As Long
    Dim s As String
    s = Nz(v, "")
    If Not Match(s, "^[0-9]{1,10}$") Then Err.Raise vbObjectError + 119, , "E-COM-003"
    If CDec(s) < 1 Or CDec(s) > 2147483647@ Then Err.Raise vbObjectError + 119, , "E-COM-003"
    PositiveId = CLng(s)
End Function
Public Function NormalizeDraft(ByVal raw As Object, ByVal day As String) As Object
    Dim d As Object, k As Variant
    Set d = Map()
    d.Add "student_no", TextValue(raw("student_no"), 15, 15, "number")
    d.Add "student_name", TextValue(raw("student_name"), 8, 8, "text")
    d.Add "student_name_kana", TextValue(raw("student_name_kana"), 36, 18, "kana")
    d.Add "birth_date", ParseBirthDate(Nz(raw("birth_era"), ""), Nz(raw("birth_year"), ""), Nz(raw("birth_month"), ""), Nz(raw("birth_day"), ""), day)
    d.Add "gender_code", TextValue(raw("gender_code"), 1, 1, "code")
    d.Add "postal_code", TextValue(raw("postal_code"), 10, 7, "postal")
    d.Add "prefecture_code", TextValue(raw("prefecture_code"), 2, 2, "code")
    d.Add "address_line1", TextValue(raw("address_line1"), 45, 45, "text")
    d.Add "address_line2", TextValue(raw("address_line2"), 45, 45, "text")
    d.Add "phone_number", TextValue(raw("phone_number"), 20, 16, "phone")
    d.Add "email_address", TextValue(raw("email_address"), 60, 60, "email")
    d.Add "admission_date", StrictIso(raw("admission_date"), True)
    d.Add "enrollment_status_code", TextValue(raw("enrollment_status_code"), 2, 2, "code")
    d.Add "enrollment_end_date", StrictIso(raw("enrollment_end_date"), False)
    If Nz(raw("class_id"), "") = "" Then d.Add "class_id", Null Else d.Add "class_id", PositiveId(raw("class_id"))
    d.Add "emergency_contact_name", TextValue(raw("emergency_contact_name"), 8, 8, "text")
    d.Add "relationship_code", TextValue(raw("relationship_code"), 2, 2, "code")
    d.Add "emergency_phone_number", TextValue(raw("emergency_phone_number"), 20, 16, "phone")
    d.Add "remarks", TextValue(raw("remarks"), 120, 120, "memo")
    For Each k In Split("student_no student_name student_name_kana gender_code postal_code prefecture_code address_line1 enrollment_status_code", " ")
        If IsNull(d(k)) Then Err.Raise vbObjectError + 120, , "E-STU-001: " & k
    Next
    If Not Match(d("student_no"), "^[A-Z0-9][A-Z0-9-]{0,14}$") Then Err.Raise vbObjectError + 120, , "E-STU-003"
    If Not Match(d("gender_code"), "^[0-9]$") Or Not Match(d("prefecture_code"), "^[0-9]{2}$") Or Not Match(d("enrollment_status_code"), "^0[1-4]$") Then Err.Raise vbObjectError + 120, , "E-STU-009"
    If Not Match(d("postal_code"), "^[0-9]{7}$") Then Err.Raise vbObjectError + 120, , "E-STU-015"
    For Each k In Array("phone_number", "emergency_phone_number")
        If Not IsNull(d(k)) Then
            If Not Match(d(k), "^(0[0-9]{9,10}|\+[1-9][0-9]{6,14})$") Then Err.Raise vbObjectError + 120, , "E-STU-016"
        End If
    Next
    If Not IsNull(d("email_address")) Then
        If Not Match(d("email_address"), "^[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+(\.[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+)*@[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?(\.[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$") Then Err.Raise vbObjectError + 120, , "E-STU-017"
    End If
    If IsNull(d("phone_number")) And IsNull(d("email_address")) And IsNull(d("emergency_phone_number")) Then Err.Raise vbObjectError + 120, , "E-STU-018"
    If (IsNull(d("emergency_contact_name")) Xor IsNull(d("relationship_code"))) Or (IsNull(d("relationship_code")) Xor IsNull(d("emergency_phone_number"))) Then Err.Raise vbObjectError + 120, , "E-STU-019"
    If Not IsNull(d("relationship_code")) Then
        If Not Match(d("relationship_code"), "^[0-9]{2}$") Then Err.Raise vbObjectError + 120, , "E-STU-009"
    End If
    If d("birth_date") > d("admission_date") Or d("admission_date") < "1900-01-01" Or d("admission_date") > day Then Err.Raise vbObjectError + 120, , "E-STU-007"
    If d("enrollment_status_code") = "01" Or d("enrollment_status_code") = "02" Then
        If IsNull(d("class_id")) Then Err.Raise vbObjectError + 120, , "E-STU-012"
        If Not IsNull(d("enrollment_end_date")) Then Err.Raise vbObjectError + 120, , "E-STU-008"
    Else
        If IsNull(d("enrollment_end_date")) Then Err.Raise vbObjectError + 120, , "E-STU-008"
        If d("enrollment_end_date") < d("admission_date") Or d("enrollment_end_date") > day Then Err.Raise vbObjectError + 120, , "E-STU-008"
    End If
    d.Add "name_key", TextValue(d("student_name"), 8, 160, "nameKey")
    d.Add "kana_key", WithoutWhite(d("student_name_kana"))
    Set NormalizeDraft = d
End Function

Public Function Seat(ByVal d As Object) As Variant
    Seat = Null
    If d Is Nothing Then Exit Function
    If d("enrollment_status_code") = "01" Or d("enrollment_status_code") = "02" Then Seat = d("class_id")
End Function
