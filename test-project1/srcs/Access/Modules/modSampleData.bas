Attribute VB_Name = "modSampleData"
Option Explicit
Option Compare Binary

' Opt-in demo bootstrap for a freshly generated sample ACCDB. Never run from Form_Load.
' User request: initially include fictitious data, separate from disposable test fixtures.
Public Const SampleDataVersion As String = "ACCESS-DEMO-V1"
Public Const SampleDataMarker As String = "[SAMPLE:ACCESS-DEMO-V1]"

Public Function EnsureSampleData() As String
    Dim day As String, seedDay As String, schoolYear As Long, i As Long, j As Long, raw As Object, result As Object
    Dim classes(1 To 4) As Long, classAdds As Long, studentAdds As Long, studentNo As String, missing As Long, mayInsert As Boolean
    Dim service As New clsStudentService, confirmation As clsConfirmation
    On Error GoTo Failed
    Authorize "Master"
    day = BusinessDay(UtcNow()): seedDay = CStr(SampleProperty("StudentSampleBasisDay", day))
    seedDay = CStr(StrictIso(seedDay, True))
    schoolYear = CLng(Left$(seedDay, 4))
    If Mid$(seedDay, 6, 2) < "04" Then schoolYear = schoolYear - 1
    If schoolYear < 1901 Or schoolYear > 9998 Or seedDay > day Then Err.Raise vbObjectError + 196, , "Invalid sample basis day"
    If CStr(SampleProperty("StudentSampleDataVersion", SampleDataVersion)) <> SampleDataVersion Then Err.Raise vbObjectError + 196, , "Unsupported sample version"
    mayInsert = SampleBootstrapAllowed()

    ' Inspect every reserved key before adding anything. A user's coincident key is a conflict.
    For i = 1 To 4
        Set raw = SampleClassDraft(i, schoolYear)
        classes(i) = ExistingSampleClass(raw("school_year"), raw("class_code"))
        If classes(i) = 0 Then missing = missing + 1
    Next
    For i = 1 To 12
        studentNo = SampleStudentNumber(schoolYear, i)
        j = ExistingSampleStudent(studentNo)
        If j = 0 Then missing = missing + 1
    Next
    If missing > 0 And Not mayInsert Then Err.Raise vbObjectError + 196, , "Missing sample keys; insertion is allowed only in build staging or an explicit disposable fixture"
    SetSampleProperty "StudentSampleBasisDay", dbText, seedDay
    SetSampleProperty "StudentSampleSchoolYear", dbLong, schoolYear
    SetSampleProperty "StudentSampleMarker", dbText, SampleDataMarker

    For i = 1 To 4
        If classes(i) = 0 Then
            Set raw = SampleClassDraft(i, schoolYear)
            Set result = MaintainClass(raw, Null, Null)
            RequireSampleSaved result, "class " & CStr(i)
            classes(i) = result("class_id"): classAdds = classAdds + 1
        End If
    Next
    For i = 1 To 12
        studentNo = SampleStudentNumber(schoolYear, i)
        If ExistingSampleStudent(studentNo) = 0 Then
            j = 1
            If i = 8 Or i = 9 Then j = 2
            If i >= 10 Then j = 4
            Set raw = SampleStudentDraft(i, schoolYear, classes(j))
            Set confirmation = New clsConfirmation
            Set result = service.SaveStudent(raw, Null, Null, "sample-bootstrap-" & CStr(i), confirmation, False, Null)
            RequireSampleSaved result, "student " & studentNo
            studentAdds = studentAdds + 1
        End If
    Next
    SetSampleProperty "StudentSampleDataVersion", dbText, SampleDataVersion
    EnsureSampleData = "PASS|version=" & SampleDataVersion & "|basisDay=" & seedDay & "|schoolYear=" & CStr(schoolYear) & "|classesAdded=" & CStr(classAdds) & "|studentsAdded=" & CStr(studentAdds) & "|expectedClasses=4|expectedStudents=12|fictitious=True|existingRowsChanged=False"
    Exit Function
Failed:
    EnsureSampleData = "FAIL|sample bootstrap|" & CStr(Err.Number) & "|" & Err.Description
End Function

Private Function SampleBootstrapAllowed() As Boolean
    Dim flag As Variant, fixture As Variant, path As String
    flag = SampleProperty("StudentSampleBootstrapAllowed", False)
    If VarType(flag) <> vbBoolean Then Err.Raise vbObjectError + 196, , "Invalid bootstrap permission property"
    If Not flag Then Exit Function
    fixture = SampleProperty("StudentTestFixture", False)
    If VarType(fixture) <> vbBoolean Then Err.Raise vbObjectError + 196, , "Invalid fixture property"
    If fixture Then SampleBootstrapAllowed = True: Exit Function
    path = LCase$(Replace(CurrentProject.Path, "/", "\"))
    If Right$(path, Len("\.tmp\generation")) = "\.tmp\generation" And LCase$(CurrentProject.Name) = "frontend.accdb" Then
        SampleBootstrapAllowed = True
    Else
        Err.Raise vbObjectError + 196, , "Bootstrap permission is valid only in generated staging or a disposable fixture"
    End If
End Function

Private Sub RequireSampleSaved(ByVal result As Object, ByVal item As String)
    Dim message As String
    If result("kind") <> "Saved" Then
        If result.Exists("message") Then message = Nz(result("message"), "")
        Err.Raise vbObjectError + 196, , "Sample " & item & ": " & result("kind") & " " & message
    End If
End Sub

Private Function SampleProperty(ByVal name As String, ByVal fallback As Variant) As Variant
    Dim db As DAO.Database
    Set db = CurrentDb
    On Error GoTo Missing
    SampleProperty = db.Properties(name).Value
    Exit Function
Missing:
    If Err.Number <> 3270 Then Err.Raise Err.Number, , Err.Description
    SampleProperty = fallback
End Function

Private Sub SetSampleProperty(ByVal name As String, ByVal kind As Long, ByVal value As Variant)
    Dim db As DAO.Database, prop As DAO.Property
    Set db = CurrentDb
    On Error GoTo Missing
    Set prop = db.Properties(name)
    On Error GoTo 0
    If Not EqualValue(prop.Value, value) Then Err.Raise vbObjectError + 196, , "Existing sample metadata differs: " & name
    Exit Sub
Missing:
    If Err.Number <> 3270 Then Err.Raise Err.Number, , Err.Description
    Resume AppendProperty
AppendProperty:
    On Error GoTo 0
    db.Properties.Append db.CreateProperty(name, kind, value)
End Sub

Private Function ExistingSampleClass(ByVal year As Long, ByVal code As String) As Long
    Dim tx As New clsUnitOfWork, repo As New clsStudentRepository, rs As DAO.Recordset
    Dim n As Long, description As String
    On Error GoTo Failed
    tx.BeginWork: Set repo.Database = tx.Database
    Set rs = repo.Query("pYear LONG,pCode TEXT(18)", "SELECT class_id,remarks FROM m_class WHERE school_year=pYear AND class_code=pCode", Array(year, code))
    If Not rs.EOF Then
        If Left$(Nz(rs!remarks, ""), Len(SampleDataMarker)) <> SampleDataMarker Then Err.Raise vbObjectError + 196, , "Reserved sample class key belongs to existing data: " & code
        ExistingSampleClass = rs!class_id
    End If
    rs.Close: tx.CloseWork
    Exit Function
Failed:
    n = Err.Number: description = Err.Description
    On Error Resume Next: If Not rs Is Nothing Then rs.Close
    tx.CloseWork: On Error GoTo 0
    Err.Raise n, , description
End Function

Private Function ExistingSampleStudent(ByVal studentNo As String) As Long
    Dim tx As New clsUnitOfWork, repo As New clsStudentRepository, rs As DAO.Recordset
    Dim n As Long, description As String
    On Error GoTo Failed
    tx.BeginWork: Set repo.Database = tx.Database
    Set rs = repo.Query("pNo TEXT(30)", "SELECT student_id,remarks FROM m_student WHERE student_no=pNo", Array(studentNo))
    If Not rs.EOF Then
        If Left$(Nz(rs!remarks, ""), Len(SampleDataMarker)) <> SampleDataMarker Then Err.Raise vbObjectError + 196, , "Reserved sample student key belongs to existing data: " & studentNo
        ExistingSampleStudent = rs!student_id
    End If
    rs.Close: tx.CloseWork
    Exit Function
Failed:
    n = Err.Number: description = Err.Description
    On Error Resume Next: If Not rs Is Nothing Then rs.Close
    tx.CloseWork: On Error GoTo 0
    Err.Raise n, , description
End Function

Private Function SampleStudentNumber(ByVal year As Long, ByVal i As Long) As String
    SampleStudentNumber = "DEMO-" & CStr(year) & "-" & Format$(i, "000")
End Function

Private Function SampleClassDraft(ByVal i As Long, ByVal year As Long) As Object
    Dim d As Object
    Set d = Map()
    If i = 4 Then year = year - 1
    d.Add "school_year", CStr(year): d.Add "grade_code", IIf(i = 4, "02", "01")
    d.Add "class_code", Choose(i, "DEMO-A", "DEMO-B", "DEMO-C", "DEMO-H")
    d.Add "class_name", "見本" & ChrW(&H30FB) & Choose(i, "通常", "満員", "空席", "前年度")
    d.Add "valid_from", CStr(year) & "-04-01": d.Add "valid_to", CStr(year + 1) & "-03-31"
    d.Add "capacity", CStr(Choose(i, 20, 2, 5, 20)): d.Add "display_order", CStr(i * 10)
    d.Add "is_active", i <> 4: d.Add "remarks", SampleDataMarker & " 架空クラス。自由に編集できるサンプル。"
    Set SampleClassDraft = d
End Function

Private Function SampleStudentDraft(ByVal i As Long, ByVal year As Long, ByVal classId As Long) As Object
    Dim d As Object, k As Variant, p As Variant
    Set d = Map()
    For Each k In SavedFields(): d.Add k, Null: Next
    d.Remove "birth_date"
    d("student_no") = SampleStudentNumber(year, i)
    d("student_name") = Choose(i, "見本春子", "見本夏男", "見本秋子", "見本冬男", "見本青葉", "見本朱音", "見本光", "見本空", "見本陸", "見本" & ChrW(&HD842) & ChrW(&HDFB7) & "子", "見本花", "見本星")
    d("student_name_kana") = Choose(i, "ミホンハルコ", "みほん なつお", "ミホンアキコ", "ミホンフユオ", "ミホンアオバ", "ミホンアカネ", "ミホンヒカル", "ミホンソラ", "ミホンリク", "ミホンヨシコ", "ミホンハナ", "ミホンホシ")
    p = BirthParts(Choose(i, "2003-04-02", "1989-01-07", "1989-01-08", "2019-05-01", "2004-02-29", "2002-12-31", "2003-01-01", "2001-06-15", "2000-08-20", "1999-03-03", "2000-10-10", "2001-11-11"))
    d.Add "birth_era", p(0): d.Add "birth_year", p(1): d.Add "birth_month", p(2): d.Add "birth_day", p(3)
    d("gender_code") = Choose(((i - 1) Mod 4) + 1, "0", "1", "2", "9")
    d("postal_code") = IIf(i = 2, "０００－０００２", "000-" & Format$(i, "0000"))
    d("prefecture_code") = "13": d("address_line1") = "サンプル市見本町" & CStr(i) & "（架空住所）"
    If i Mod 2 = 0 Then d("address_line2") = "見本棟 " & Format$(i, "000") & "号（架空）"
    d("email_address") = "sample-" & Format$(i, "000") & "@example.invalid"
    If i = 1 Then d("phone_number") = "000-0000-0000"
    If i = 2 Then d("phone_number") = "000-000-0000"
    d("admission_date") = CStr(year) & "-04-01"
    d("enrollment_status_code") = "01"
    If i = 7 Or i = 9 Then d("enrollment_status_code") = "02"
    If i >= 10 Then
        d("admission_date") = CStr(year - 1) & "-04-01"
        d("enrollment_status_code") = IIf(i = 12, "04", "03")
        d("enrollment_end_date") = CStr(year) & "-03-31"
    End If
    d("class_id") = classId
    If i = 3 Then
        d("emergency_contact_name") = "見本保護者": d("relationship_code") = "07": d("emergency_phone_number") = "000-000-0000"
    End If
    d("remarks") = SampleDataMarker & " 架空データ。実在の人物" & ChrW(&H30FB) & "連絡先ではありません。"
    d.Add "school_year", CStr(IIf(i >= 10, year - 1, year)): d.Add "grade_code", IIf(i >= 10, "02", "01")
    Set SampleStudentDraft = d
End Function
