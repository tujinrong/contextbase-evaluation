Attribute VB_Name = "modSelfTests"
Option Explicit
Option Compare Binary
Private checks As Long
Private Sub Check(ByVal value As Boolean, ByVal label As String)
    checks = checks + 1
    If Not value Then Err.Raise vbObjectError + 190, , "Assertion failed: " & label
End Sub
' Run only against a newly generated disposable backend. Deliberately rejects populated data.
Public Function RunSelfTests() As String
    Dim tx As New clsUnitOfWork, repo As New clsStudentRepository, rs As DAO.Recordset, service As New clsStudentService
    Dim classRaw As Object, raw As Object, result As Object, old As Object, confirm As New clsConfirmation, otherConfirm As New clsConfirmation
    Dim classId As Long, id As Long, otherId As Long, year As Long, utc As Date, day As String, expected As Long, normalized As Object, criteria As Object
    On Error GoTo Failed
    checks = 0: Authorize "Master": utc = UtcNow(): day = BusinessDay(utc)
    Check ScalarCount(ChrW(&HD842) & ChrW(&HDFB7)) = 1, "supplementary scalar"
    Check NFKC("Ａ１２") = "A12", "NFKC fullwidth"
    Check TextValue("やまだ　たろう", 36, 18, "kana") = "ヤマダ タロウ", "hiragana kana and space"
    Check TextValue("090-1234-5678", 20, 16, "phone") = "09012345678", "phone normalization"
    Check StrictIso("2024-02-29", True) = "2024-02-29", "Gregorian leap date"
    Check ParseBirthDate("SHOWA", "64", "1", "7", day) = "1989-01-07", "Showa final day"
    Check ParseBirthDate("HEISEI", "元", "1", "8", day) = "1989-01-08", "Heisei first day"
    Check ParseBirthDate("REIWA", "元", "5", "1", day) = "2019-05-01", "Reiwa first day"
    tx.BeginWork: Set repo.Database = tx.Database
    Set rs = repo.Database.OpenRecordset("SELECT Count(*) AS n FROM m_student")
    Check rs!n = 0, "fresh test backend": rs.Close: tx.CloseWork
    year = CLng(Left$(day, 4)): If Mid$(day, 6, 2) < "04" Then year = year - 1
    Set classRaw = Map()
    classRaw.Add "school_year", CStr(year): classRaw.Add "grade_code", "00": classRaw.Add "class_code", "TEST-1"
    classRaw.Add "class_name", "検証専用": classRaw.Add "valid_from", CStr(year) & "-04-01": classRaw.Add "valid_to", CStr(year + 1) & "-03-31"
    classRaw.Add "capacity", "2": classRaw.Add "display_order", "0": classRaw.Add "is_active", True: classRaw.Add "remarks", Null
    Set result = MaintainClass(classRaw, Null, Null): Check result("kind") = "Saved", "class maintenance commit"
    classId = result("class_id")
    Set raw = TestDraft(classId, day): Set normalized = NormalizeDraft(raw, day)
    Check normalized("student_no") = "TEST-001", "student no normalization"
    Set result = service.SaveStudent(raw, Null, Null, "selftest", confirm, False, Null)
    If result("kind") <> "Saved" Then Err.Raise vbObjectError + 190, , "create student returned " & result("kind") & " " & result("message") & " error=" & result("errorCode") & " " & result("diagnostic")
    Check result("kind") = "Saved", "create student": id = result("student_id"): expected = result("row_version")
    Check expected = 1, "new version"
    Set old = service.LoadStudent(id): Check old("student_name") = "山田太郎", "saved Unicode roundtrip"
    Set result = service.SaveStudent(raw, id, expected, "selftest", confirm, False, Null)
    Check result("kind") = "NoChange", "no change avoids version/audit"
    raw("address_line2") = "更新後"
    Set result = service.SaveStudent(raw, id, expected, "selftest", confirm, False, Null)
    Check result("kind") = "Saved", "update student": expected = result("row_version")
    Set result = service.SaveStudent(raw, id, expected - 1, "selftest", confirm, False, Null)
    Check result("kind") = "Conflict", "stale expected version"
    raw("student_no") = "TEST-002"
    Set result = service.SaveStudent(raw, Null, Null, "other-form", otherConfirm, False, Null)
    Check result("kind") = "ConfirmationRequired", "duplicate requires separate-person confirmation"
    Check result("candidates").Count = 1, "all duplicate candidates"
    Set result = service.SaveStudent(raw, Null, Null, "wrong-form", otherConfirm, True, "同姓同名の別人")
    Check result("kind") = "ConfirmationRequired", "confirmation bound to form"
    Set result = service.SaveStudent(raw, Null, Null, "wrong-form", otherConfirm, True, "同姓同名の別人")
    Check result("kind") = "Saved", "confirmed duplicate saves": otherId = result("student_id")
    raw("student_no") = "TEST-003": raw("student_name") = "佐藤花子": raw("student_name_kana") = "サトウハナコ"
    Set result = service.SaveStudent(raw, Null, Null, "third", confirm, False, Null)
    Check result("message") = "E-STU-102", "capacity rejects final additional seat"
    Set criteria = Map()
    criteria.Add "studentNo", Null: criteria.Add "name", Null: criteria.Add "kana", Null: criteria.Add "phone", Null
    criteria.Add "year", Null: criteria.Add "grade", Null: criteria.Add "class", Null: criteria.Add "prefecture", Null
    criteria.Add "unassigned", False: criteria.Add "from", Null: criteria.Add "to", Null
    criteria.Add "status01", True: criteria.Add "status02", True: criteria.Add "status03", False: criteria.Add "status04", False
    Set normalized = NormalizeCriteria(criteria, day)
    Set result = SearchStudents(normalized, 1, 20, "studentNo", "asc")
    Check result("kind") = "Found", "search succeeds": Check result("total") = 2, "count snapshot"
    Check result("rows").Count = 2, "page projection"
    Check Not result("rows")(1).Exists("email_address"), "list excludes undisplayed personal data"
    classRaw("capacity") = "1"
    Set result = MaintainClass(classRaw, classId, 1): Check result("message") = "E-MST-004", "master cannot shrink below occupancy"
    Set result = service.DeleteStudent(otherId, 1, "検証データの削除", True)
    Check result("kind") = "Saved", "logical delete commit"
    Set result = SearchStudents(normalized, 1, 20, "studentNo", "asc")
    Check result("total") = 1, "logical deletion excluded from search"
    tx.BeginWork: Set repo.Database = tx.Database
    Set rs = repo.Database.OpenRecordset("SELECT Count(*) AS n FROM t_operation_log")
    Check rs!n = 5, "master/create/update/create/delete atomic audits": rs.Close
    Set rs = repo.Database.OpenRecordset("SELECT lock_bit FROM t_write_guard WHERE guard_id=1")
    Check Not IsNull(rs!lock_bit), "guard remains present": rs.Close: tx.CloseWork
    RunSelfTests = CStr(checks) & " assertions passed"
    Exit Function
Failed:
    RunSelfTests = "FAILED after " & CStr(checks) & " checks: " & CStr(Err.Number) & " " & Err.Description
    On Error Resume Next: tx.CloseWork
End Function
Private Function TestDraft(ByVal classId As Long, ByVal day As String) As Object
    Dim k As Variant, d As Object
    Set d = Map()
    For Each k In SavedFields(): d.Add k, Null: Next
    d.Remove "birth_date"
    d("student_no") = "ＴＥＳＴ－００１": d("student_name") = "山田太郎": d("student_name_kana") = "やまだたろう"
    d.Add "birth_era", "HEISEI": d.Add "birth_year", "15": d.Add "birth_month", "4": d.Add "birth_day", "2"
    d("gender_code") = "0": d("postal_code") = "100-0001": d("prefecture_code") = "13"
    d("address_line1") = "東京都千代田区": d("phone_number") = "03-1234-5678"
    d("admission_date") = day: d("enrollment_status_code") = "01": d("class_id") = classId
    d.Add "school_year", Null: d.Add "grade_code", Null
    Set TestDraft = d
End Function
