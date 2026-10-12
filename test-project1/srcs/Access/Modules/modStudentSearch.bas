Attribute VB_Name = "modStudentSearch"
Option Explicit
Option Compare Binary

Public Function NormalizeCriteria(ByVal raw As Object, ByVal day As String) As Object
    Dim d As Object, k As Variant, s As String
    Set d = Map()
    d.Add "studentNo", TextValue(raw("studentNo"), 15, 15, "number")
    d.Add "name", TextValue(raw("name"), 8, 160, "nameKey")
    d.Add "kana", TextValue(raw("kana"), 36, 18, "kana")
    If Not IsNull(d("kana")) Then d("kana") = WithoutWhite(d("kana"))
    d.Add "phone", TextValue(raw("phone"), 20, 16, "phone")
    d.Add "from", StrictIso(raw("from"), False): d.Add "to", StrictIso(raw("to"), False)
    For Each k In Array("from", "to")
        If Not IsNull(d(k)) Then
            If d(k) < "1900-01-01" Or d(k) > day Then Err.Raise vbObjectError + 140, , "E-DATE-002"
        End If
    Next
    If Not IsNull(d("from")) And Not IsNull(d("to")) Then
        If d("from") > d("to") Then Err.Raise vbObjectError + 140, , "E-STU-006"
    End If
    d.Add "year", Null: d.Add "class", Null
    If Nz(raw("year"), "") <> "" Then
        s = NFKC(raw("year"))
        If Not Match(s, "^[0-9]{4}$") Then Err.Raise vbObjectError + 140, , "E-DATE-003"
        If CLng(s) < 1900 Or CLng(s) > 9998 Then Err.Raise vbObjectError + 140, , "E-DATE-003"
        d("year") = CLng(s)
    End If
    If Nz(raw("class"), "") <> "" Then d("class") = PositiveId(raw("class"))
    d.Add "grade", TextValue(raw("grade"), 2, 2, "code")
    d.Add "prefecture", TextValue(raw("prefecture"), 2, 2, "code")
    d.Add "unassigned", CBool(raw("unassigned"))
    If d("unassigned") And (Not IsNull(d("year")) Or Not IsNull(d("grade")) Or Not IsNull(d("class"))) Then Err.Raise vbObjectError + 140, , "E-SRC-001"
    For Each k In Array("01", "02", "03", "04"): d.Add "status" & k, CBool(raw("status" & k)): Next
    If Not IsNull(d("studentNo")) Then
        If Not Match(d("studentNo"), "^[A-Z0-9][A-Z0-9-]{0,14}$") Then Err.Raise vbObjectError + 140, , "E-STU-003"
    End If
    If Not IsNull(d("phone")) Then
        If Not Match(d("phone"), "^(0[0-9]{9,10}|\+[1-9][0-9]{6,14})$") Then Err.Raise vbObjectError + 140, , "E-STU-016"
    End If
    Set NormalizeCriteria = d
End Function

Public Function SearchStudents(ByVal d As Object, ByVal page As Long, ByVal pageSize As Long, ByVal sortKey As String, ByVal direction As String) As Object
    Dim tx As New clsUnitOfWork, repo As New clsStudentRepository, rs As DAO.Recordset, rows(0 To 10000) As Object
    Dim item As Object, c As Object, result As Object, view As Collection, count As Long, include As Boolean
    Dim statusAny As Boolean, k As Variant, i As Long, first As Long, last As Long
    Set result = Map(): Set SearchStudents = result
    On Error GoTo Failed
    Authorize "Read"
    If page < 1 Or (pageSize <> 20 And pageSize <> 50 And pageSize <> 100) Then Err.Raise vbObjectError + 141, , "E-SRC-002"
    If sortKey <> "studentNo" And sortKey <> "name" And sortKey <> "admissionDate" And sortKey <> "updatedAt" Then Err.Raise vbObjectError + 141, , "E-SRC-002"
    If direction <> "asc" And direction <> "desc" Then Err.Raise vbObjectError + 141, , "E-SRC-002"
    tx.BeginWork: Set repo.Database = tx.Database
    ValidateSelections repo, d
    statusAny = d("status01") Or d("status02") Or d("status03") Or d("status04")
    Set rs = tx.Database.OpenRecordset("SELECT student_id,student_no,student_name,student_name_kana,name_key,kana_key,birth_date,admission_date,class_id,enrollment_status_code,prefecture_code,address_line1,phone_number,emergency_phone_number,updated_at FROM m_student WHERE is_deleted=False", dbOpenSnapshot)
    Do Until rs.EOF
        include = True
        If Not IsNull(d("studentNo")) Then include = StrComp(Left$(rs!student_no, Len(d("studentNo"))), d("studentNo"), vbBinaryCompare) = 0
        If Not IsNull(d("name")) Then include = include And InStr(1, rs!name_key, d("name"), vbBinaryCompare) > 0
        If Not IsNull(d("kana")) Then include = include And InStr(1, rs!kana_key, d("kana"), vbBinaryCompare) > 0
        If Not IsNull(d("class")) Then include = include And EqualValue(rs!class_id, d("class"))
        If d("unassigned") Then include = include And IsNull(rs!class_id)
        If Not IsNull(d("prefecture")) Then include = include And EqualValue(rs!prefecture_code, d("prefecture"))
        If Not IsNull(d("phone")) Then include = include And (EqualValue(rs!phone_number, d("phone")) Or EqualValue(rs!emergency_phone_number, d("phone")))
        If Not IsNull(d("from")) Then include = include And rs!admission_date >= d("from")
        If Not IsNull(d("to")) Then include = include And rs!admission_date <= d("to")
        If statusAny Then include = include And d("status" & rs!enrollment_status_code)
        Set c = Nothing
        If Not IsNull(rs!class_id) Then Set c = repo.ClassById(rs!class_id)
        If Not IsNull(d("year")) Then
            If c Is Nothing Then include = False Else include = include And c("school_year") = d("year")
        End If
        If Not IsNull(d("grade")) Then
            If c Is Nothing Then include = False Else include = include And c("grade_code") = d("grade")
        End If
        If include Then
            Set item = repo.RowMap(rs)
            item.Remove "emergency_phone_number"
            If c Is Nothing Then
                item.Add "school_year", Null: item.Add "grade_name", "－": item.Add "class_display", "－"
            Else
                item.Add "school_year", c("school_year")
                item.Add "grade_name", repo.CodeName("GRADE", c("grade_code"))
                item.Add "class_display", c("class_code") & " " & c("class_name")
                If Not c("is_active") Then item("class_display") = item("class_display") & " [停止]"
            End If
            item.Add "enrollment_name", repo.CodeName("ENROLLMENT_STATUS", rs!enrollment_status_code)
            item.Add "address_display", repo.CodeName("PREFECTURE", rs!prefecture_code) & " " & rs!address_line1
            Set rows(count) = item: count = count + 1
            If count = 10001 Then Exit Do
        End If
        rs.MoveNext
    Loop
    rs.Close: tx.CloseWork
    result.Add "total", count: result.Add "at", UtcNow()
    Set view = New Collection
    result.Add "rows", view
    If count > 10000 Then result.Add "kind", "LimitExceeded": result.Add "message", "W-SRC-001": Exit Function
    If count = 0 Then result.Add "kind", "Found": result.Add "message", "I-SRC-001": result.Add "page", 1: Exit Function
    SortRows rows, 0, count - 1, SortColumn(sortKey), direction
    If page > (count + pageSize - 1) \ pageSize Then page = (count + pageSize - 1) \ pageSize
    first = (page - 1) * pageSize: last = first + pageSize - 1
    If last >= count Then last = count - 1
    For i = first To last
        rows(i).Remove "name_key": rows(i).Remove "kana_key": rows(i).Remove "admission_date"
        view.Add rows(i)
    Next
    result.Add "page", page: result.Add "kind", "Found": result.Add "message", ""
    Exit Function
Failed:
    Dim e As String
    e = Err.Description
    On Error Resume Next: If Not rs Is Nothing Then rs.Close
    tx.CloseWork: On Error GoTo 0
    result.Add "kind", "SystemError"
    If Left$(e, 2) <> "E-" Then e = "E-COM-004"
    result.Add "message", e
End Function

Private Sub ValidateSelections(ByVal repo As clsStudentRepository, ByVal d As Object)
    Dim rs As DAO.Recordset, c As Object
    If Not IsNull(d("grade")) Then repo.CheckCode "GRADE", d("grade"), d("grade"), "1900-01-01"
    If Not IsNull(d("prefecture")) Then repo.CheckCode "PREFECTURE", d("prefecture"), d("prefecture"), "1900-01-01"
    If Not IsNull(d("year")) Then
        Set rs = repo.Query("pYear LONG", "SELECT class_id FROM m_class WHERE school_year=pYear", Array(d("year")))
        If rs.EOF Then rs.Close: Err.Raise vbObjectError + 142, , "E-STU-014"
        rs.Close
    End If
    If IsNull(d("class")) Then Exit Sub
    Set c = repo.ClassById(d("class"))
    If c Is Nothing Then Err.Raise vbObjectError + 142, , "E-STU-010"
    If Not IsNull(d("year")) Then
        If c("school_year") <> d("year") Then Err.Raise vbObjectError + 142, , "E-STU-014"
    End If
    If Not IsNull(d("grade")) Then
        If c("grade_code") <> d("grade") Then Err.Raise vbObjectError + 142, , "E-STU-014"
    End If
End Sub
Private Function SortColumn(ByVal key As String) As String
    Select Case key
    Case "studentNo": SortColumn = "student_no"
    Case "name": SortColumn = "name_key"
    Case "admissionDate": SortColumn = "admission_date"
    Case "updatedAt": SortColumn = "updated_at"
    End Select
End Function
Private Function CompareRow(ByVal a As Object, ByVal b As Object, ByVal key As String, ByVal direction As String) As Long
    If key = "updated_at" Then
        If a(key) < b(key) Then
            CompareRow = -1
        ElseIf a(key) > b(key) Then
            CompareRow = 1
        End If
    Else
        CompareRow = StrComp(CStr(a(key)), CStr(b(key)), vbBinaryCompare)
    End If
    If direction = "desc" Then CompareRow = -CompareRow
    If CompareRow = 0 Then
        If a("student_id") < b("student_id") Then
            CompareRow = -1
        ElseIf a("student_id") > b("student_id") Then
            CompareRow = 1
        End If
    End If
End Function
Private Sub SortRows(ByRef rows() As Object, ByVal lo As Long, ByVal hi As Long, ByVal key As String, ByVal direction As String)
    Dim i As Long, j As Long, pivot As Object, temp As Object
    i = lo: j = hi: Set pivot = rows((lo + hi) \ 2)
    Do While i <= j
        Do While CompareRow(rows(i), pivot, key, direction) < 0: i = i + 1: Loop
        Do While CompareRow(rows(j), pivot, key, direction) > 0: j = j - 1: Loop
        If i <= j Then
            Set temp = rows(i): Set rows(i) = rows(j): Set rows(j) = temp
            i = i + 1: j = j - 1
        End If
    Loop
    If lo < j Then SortRows rows, lo, j, key, direction
    If i < hi Then SortRows rows, i, hi, key, direction
End Sub
