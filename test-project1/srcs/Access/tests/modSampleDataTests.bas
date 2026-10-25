Attribute VB_Name = "modSampleDataTests"
Option Explicit
Option Compare Binary
Private assertions As Long
Private results As String

Private Sub AssertSample(ByVal condition As Boolean, ByVal label As String)
    assertions = assertions + 1
    results = results & CStr(assertions) & vbTab & IIf(condition, "PASS", "FAIL") & vbTab & label & vbCrLf
    If Not condition Then Err.Raise vbObjectError + 197, , label
End Sub

Public Function SampleDataTestLog() As String
    SampleDataTestLog = results
End Function

Private Function CountSampleRows(ByVal sql As String) As Long
    Dim db As DAO.Database, rs As DAO.Recordset
    Set db = CurrentDb: Set rs = db.OpenRecordset(sql, dbOpenSnapshot)
    CountSampleRows = rs.Fields(0).Value: rs.Close
End Function

Private Function SampleScalar(ByVal sql As String) As Variant
    Dim db As DAO.Database, rs As DAO.Recordset
    Set db = CurrentDb: Set rs = db.OpenRecordset(sql, dbOpenSnapshot)
    If rs.EOF Then Err.Raise vbObjectError + 197, , "Missing sample query row"
    SampleScalar = rs.Fields(0).Value: rs.Close
End Function

' Includes data/metadata/audit values to catch a destructive reset or silent row-version change.
Private Function SampleSnapshot() As String
    Dim db As DAO.Database, rs As DAO.Recordset, fld As DAO.Field, table As Variant, v As String
    Set db = CurrentDb
    For Each table In Array("m_code_category", "m_code", "m_class", "m_student", "t_operation_log")
        Set rs = db.OpenRecordset("SELECT * FROM " & table & " ORDER BY 1", dbOpenSnapshot)
        Do Until rs.EOF
            For Each fld In rs.Fields
                If IsNull(fld.Value) Then
                    SampleSnapshot = SampleSnapshot & "N;"
                Else
                    v = CStr(fld.Value): SampleSnapshot = SampleSnapshot & CStr(Len(v)) & ":" & v & ";"
                End If
            Next
            rs.MoveNext
        Loop
        rs.Close
    Next
End Function

Private Function SampleCriteria(ByVal defaultStatuses As Boolean) As Object
    Dim raw As Object
    Set raw = Map(): raw.Add "studentNo", Null: raw.Add "name", Null: raw.Add "class", Null
    raw.Add "status01", defaultStatuses: raw.Add "status02", defaultStatuses: raw.Add "status03", False: raw.Add "status04", False
    Set SampleCriteria = raw
End Function

Private Function IndependentDraft(ByVal classId As Long, ByVal studentNo As String) As Object
    Dim raw As Object, k As Variant
    Set raw = Map()
    For Each k In SavedFields(): raw.Add k, Null: Next
    raw.Remove "birth_date"
    raw("student_no") = studentNo: raw("student_name") = "利用者見本": raw("student_name_kana") = "リヨウシャミホン"
    raw.Add "birth_era", "HEISEI": raw.Add "birth_year", "15": raw.Add "birth_month", "4": raw.Add "birth_day", "2"
    raw("gender_code") = "0": raw("postal_code") = "000-0099": raw("prefecture_code") = "13"
    raw("address_line1") = "ユーザー入力の架空住所": raw("email_address") = "user@example.invalid"
    raw("admission_date") = BusinessDay(UtcNow()): raw("enrollment_status_code") = "01": raw("class_id") = classId
    raw("remarks") = "サンプル投入処理が変更してはいけないユーザー入力"
    raw.Add "school_year", Null: raw.Add "grade_code", Null
    Set IndependentDraft = raw
End Function

Public Function RunSampleDataTests() As String
    Dim output As String, before As String, after As String, year As Long, classId As Long, fullId As Long, historicId As Long
    Dim raw As Object, result As Object, criteriaRaw As Object, criteria As clsSearchCriteria, old As Object, k As Variant
    Dim service As New clsStudentService, confirmation As New clsConfirmation, id As Long, editedVersion As Long, userId As Long
    Dim parts As Variant, db As DAO.Database, classRaw As Object, customClassId As Long, deletedId As Long
    On Error GoTo Failed
    assertions = 0: results = "": Set db = CurrentDb
    AssertSample CBool(db.Properties("StudentTestFixture")), "disposable fixture required"
    AssertSample CountSampleRows("SELECT Count(*) FROM m_student") = 0, "initial fixture contains no students"
    AssertSample CountSampleRows("SELECT Count(*) FROM m_class") = 0, "initial fixture contains no classes"
    AssertSample CountSampleRows("SELECT Count(*) FROM t_operation_log") = 0, "initial fixture contains no audits"
    AssertSample CountSampleRows("SELECT Count(*) FROM m_code_category") = 5 And CountSampleRows("SELECT Count(*) FROM m_code") = 70, "approved initial masters present"
    before = SampleSnapshot(): output = EnsureSampleData(): after = SampleSnapshot()
    AssertSample Left$(output, 5) = "FAIL|", "bootstrap insertion requires explicit build or test permission"
    AssertSample before = after, "permission rejection changes no business row or audit"
    db.Properties.Append db.CreateProperty("StudentSampleBootstrapAllowed", dbBoolean, True)
    output = EnsureSampleData()
    AssertSample Left$(output, 5) = "PASS|", "first seed succeeds: " & output
    Set db = CurrentDb
    db.Properties("StudentSampleBootstrapAllowed") = False
    AssertSample InStr(1, output, "|classesAdded=4|studentsAdded=12|", vbBinaryCompare) > 0, "first seed adds exact class and student counts"
    AssertSample CountSampleRows("SELECT Count(*) FROM m_class") = 4, "four demonstration classes"
    AssertSample CountSampleRows("SELECT Count(*) FROM m_student") = 12, "twelve demonstration students"
    AssertSample CountSampleRows("SELECT Count(*) FROM t_operation_log") = 16, "all sixteen class/student creates audited"
    AssertSample CountSampleRows("SELECT Count(*) FROM t_operation_log WHERE before_version Is Not Null OR after_version<>1 OR operation_type<>'CREATE'") = 0, "seed uses new version one creates only"
    AssertSample CStr(db.Properties("StudentSampleDataVersion")) = "ACCESS-DEMO-V1", "sample version explicitly recorded"
    AssertSample CStr(db.Properties("StudentSampleMarker")) = "[SAMPLE:ACCESS-DEMO-V1]", "fictitious sample marker recorded"
    AssertSample CStr(db.Properties("StudentSampleBasisDay")) = BusinessDay(UtcNow()), "initial baseline is actual JST business day"
    year = CLng(Left$(BusinessDay(UtcNow()), 4)): If Mid$(BusinessDay(UtcNow()), 6, 2) < "04" Then year = year - 1
    AssertSample CLng(db.Properties("StudentSampleSchoolYear")) = year, "April-based school year"
    AssertSample CountSampleRows("SELECT Count(*) FROM m_class WHERE is_active=True AND school_year=" & year) = 3, "three current active classes"
    AssertSample CountSampleRows("SELECT Count(*) FROM m_class WHERE is_active=False AND school_year=" & year - 1) = 1, "one previous-year stopped class"
    AssertSample CountSampleRows("SELECT Count(*) FROM m_student WHERE enrollment_status_code='01'") = 7, "seven enrolled students"
    AssertSample CountSampleRows("SELECT Count(*) FROM m_student WHERE enrollment_status_code='02'") = 2, "two students on leave"
    AssertSample CountSampleRows("SELECT Count(*) FROM m_student WHERE enrollment_status_code='03'") = 2, "two graduated students"
    AssertSample CountSampleRows("SELECT Count(*) FROM m_student WHERE enrollment_status_code='04'") = 1, "one withdrawn student"
    AssertSample CountSampleRows("SELECT Count(*) FROM m_student WHERE Len(postal_code)<>7 OR postal_code Like '*[!0-9]*'") = 0, "all postal values are exactly seven ASCII digits"
    AssertSample SampleScalar("SELECT postal_code FROM m_student WHERE student_no='DEMO-" & year & "-001'") = "0000001", "postal leading zeros survive storage"
    AssertSample SampleScalar("SELECT postal_code FROM m_student WHERE student_no='DEMO-" & year & "-002'") = "0000002", "fullwidth postal input normalized"
    AssertSample SampleScalar("SELECT phone_number FROM m_student WHERE student_no='DEMO-" & year & "-001'") = "00000000000", "eleven-digit phone normalized"
    AssertSample SampleScalar("SELECT phone_number FROM m_student WHERE student_no='DEMO-" & year & "-002'") = "0000000000", "ten-digit phone normalized"
    AssertSample CountSampleRows("SELECT Count(*) FROM m_student WHERE email_address Not Like '*@example.invalid'") = 0, "sample mail addresses use reserved invalid domain"
    AssertSample CountSampleRows("SELECT Count(*) FROM m_student WHERE address_line1 Not Like '*架空*' OR Left(remarks,Len('[SAMPLE:ACCESS-DEMO-V1]'))<>'[SAMPLE:ACCESS-DEMO-V1]'") = 0, "sample records explicitly fictitious"
    AssertSample CountSampleRows("SELECT Count(*) FROM m_student WHERE emergency_contact_name Is Not Null AND relationship_category='RELATIONSHIP' AND relationship_code='07' AND emergency_phone_number='0000000000'") = 1, "one complete emergency contact group"
    AssertSample CountSampleRows("SELECT Count(*) FROM m_student WHERE emergency_contact_name Is Null AND relationship_category Is Null AND relationship_code Is Null AND emergency_phone_number Is Null") = 11, "optional emergency groups are true NULL"
    AssertSample SampleScalar("SELECT birth_date FROM m_student WHERE student_no='DEMO-" & year & "-002'") = "1989-01-07", "Showa final-day sample"
    AssertSample SampleScalar("SELECT birth_date FROM m_student WHERE student_no='DEMO-" & year & "-003'") = "1989-01-08", "Heisei first-day sample"
    AssertSample SampleScalar("SELECT birth_date FROM m_student WHERE student_no='DEMO-" & year & "-004'") = "2019-05-01", "Reiwa first-day sample"
    AssertSample SampleScalar("SELECT birth_date FROM m_student WHERE student_no='DEMO-" & year & "-005'") = "2004-02-29", "Gregorian leap-day sample"
    AssertSample SampleScalar("SELECT student_name FROM m_student WHERE student_no='DEMO-" & year & "-010'") = "見本" & ChrW(&HD842) & ChrW(&HDFB7) & "子", "supplementary Unicode name exact UTF-16 roundtrip"
    AssertSample SampleScalar("SELECT class_name FROM m_class WHERE class_code='DEMO-A' AND school_year=" & year) = "見本" & ChrW(&H30FB) & "通常", "normal class contains exact U+30FB middle dot"
    AssertSample SampleScalar("SELECT class_name FROM m_class WHERE class_code='DEMO-B' AND school_year=" & year) = "見本" & ChrW(&H30FB) & "満員", "full class contains exact U+30FB middle dot"
    AssertSample SampleScalar("SELECT class_name FROM m_class WHERE class_code='DEMO-C' AND school_year=" & year) = "見本" & ChrW(&H30FB) & "空席", "empty class contains exact U+30FB middle dot"
    AssertSample SampleScalar("SELECT class_name FROM m_class WHERE class_code='DEMO-H' AND school_year=" & year - 1) = "見本" & ChrW(&H30FB) & "前年度", "historical class contains exact U+30FB middle dot"
    AssertSample InStr(1, SampleScalar("SELECT remarks FROM m_student WHERE student_no='DEMO-" & year & "-010'"), "人物" & ChrW(&H30FB) & "連絡先", vbBinaryCompare) > 0, "sample note contains exact middle dot rather than ANSI replacement"
    AssertSample CountSampleRows("SELECT Count(*) FROM m_student WHERE birth_date>admission_date OR admission_date>'" & BusinessDay(UtcNow()) & "'") = 0, "birth and admission temporal validity"
    AssertSample CountSampleRows("SELECT Count(*) FROM m_student WHERE enrollment_status_code In ('01','02') AND enrollment_end_date Is Not Null") = 0, "active students have NULL end date"
    AssertSample CountSampleRows("SELECT Count(*) FROM m_student WHERE enrollment_status_code In ('03','04') AND (enrollment_end_date Is Null OR enrollment_end_date>'" & BusinessDay(UtcNow()) & "' OR enrollment_end_date<admission_date)") = 0, "ended students have valid past end date"
    Set criteriaRaw = SampleCriteria(True): Set criteria = NormalizeCriteria(criteriaRaw, BusinessDay(UtcNow()))
    Set result = SearchStudents(criteria, "studentNo", "asc")
    AssertSample result("kind") = "Found" And result("total") = 9, "default real search finds nine active or leave students"
    Set criteriaRaw = SampleCriteria(False): Set criteria = NormalizeCriteria(criteriaRaw, BusinessDay(UtcNow()))
    Set result = SearchStudents(criteria, "studentNo", "asc")
    AssertSample result("kind") = "Found" And result("total") = 12, "all-state real search finds all twelve students"
    criteriaRaw("studentNo") = "DEMO-" & year & "-001": Set criteria = NormalizeCriteria(criteriaRaw, BusinessDay(UtcNow()))
    Set result = SearchStudents(criteria, "studentNo", "asc")
    AssertSample result("total") = 1, "stable-key prefix search"
    criteriaRaw("studentNo") = Null: criteriaRaw("name") = "見本": Set criteria = NormalizeCriteria(criteriaRaw, BusinessDay(UtcNow()))
    Set result = SearchStudents(criteria, "name", "asc")
    AssertSample result("total") = 12, "sample name partial search"
    classId = SampleScalar("SELECT class_id FROM m_class WHERE class_code='DEMO-C' AND school_year=" & year)
    fullId = SampleScalar("SELECT class_id FROM m_class WHERE class_code='DEMO-B' AND school_year=" & year)
    historicId = SampleScalar("SELECT class_id FROM m_class WHERE class_code='DEMO-H' AND school_year=" & year - 1)
    AssertSample CountSampleRows("SELECT Count(*) FROM m_student WHERE class_id=" & fullId & " AND enrollment_status_code In ('01','02')") = 2, "full class includes on-leave occupancy"
    AssertSample CountSampleRows("SELECT Count(*) FROM m_student WHERE class_id=" & classId) = 0, "empty class available for new enrollment"
    criteriaRaw("name") = Null: criteriaRaw("class") = historicId: Set criteria = NormalizeCriteria(criteriaRaw, BusinessDay(UtcNow()))
    Set result = SearchStudents(criteria, "studentNo", "asc")
    AssertSample result("total") = 3, "historical class searchable for ended enrollment"
    before = SampleSnapshot(): output = EnsureSampleData(): after = SampleSnapshot()
    AssertSample Left$(output, 5) = "PASS|" And InStr(1, output, "|classesAdded=0|studentsAdded=0|", vbBinaryCompare) > 0, "second seed is idempotent"
    AssertSample before = after, "second seed changes no master/student/version/audit values"
    Set raw = IndependentDraft(fullId, "USER-FULL"): Set confirmation = New clsConfirmation
    Set result = service.SaveStudent(raw, Null, Null, "sample-full", confirmation, False, Null)
    AssertSample result("message") = "E-STU-102", "production service rejects extra seat in full sample class"
    AssertSample before = SampleSnapshot(), "rejected full-class insert changes no row or audit"
    raw("class_id") = classId: raw("student_no") = "USER-NEW"
    Set result = service.SaveStudent(raw, Null, Null, "sample-user", confirmation, False, Null)
    AssertSample result("kind") = "Saved", "new user can register in empty sample class": userId = result("student_id")
    id = SampleScalar("SELECT student_id FROM m_student WHERE student_no='DEMO-" & year & "-001'")
    Set old = service.LoadStudent(id): Set raw = Map()
    For Each k In SavedFields(): raw.Add k, old(k): Next
    raw.Remove "birth_date": parts = BirthParts(old("birth_date"))
    raw.Add "birth_era", parts(0): raw.Add "birth_year", parts(1): raw.Add "birth_month", parts(2): raw.Add "birth_day", parts(3)
    raw.Add "school_year", Null: raw.Add "grade_code", Null: raw("address_line2") = "利用者が編集した値"
    Set confirmation = New clsConfirmation
    Set result = service.SaveStudent(raw, id, old("row_version"), "sample-edit", confirmation, False, Null)
    AssertSample result("kind") = "Saved", "sample student is editable through production service": editedVersion = result("row_version")
    Set classRaw = Map()
    classRaw.Add "school_year", CStr(year): classRaw.Add "grade_code", "01": classRaw.Add "class_code", "USER-C"
    classRaw.Add "class_name", "利用者クラス": classRaw.Add "valid_from", CStr(year) & "-04-01": classRaw.Add "valid_to", CStr(year + 1) & "-03-31"
    classRaw.Add "capacity", "3": classRaw.Add "display_order", "99": classRaw.Add "is_active", True: classRaw.Add "remarks", "利用者が整備したクラス"
    Set result = MaintainClass(classRaw, Null, Null)
    AssertSample result("kind") = "Saved", "user-created class through production maintenance": customClassId = result("class_id")
    classRaw("class_code") = "DEMO-C": classRaw("class_name") = "利用者変更クラス": classRaw("capacity") = "6"
    classRaw("remarks") = "[SAMPLE:ACCESS-DEMO-V1] 利用者による変更"
    Set result = MaintainClass(classRaw, classId, 1)
    AssertSample result("kind") = "Saved", "sample class is editable through production maintenance"
    deletedId = SampleScalar("SELECT student_id FROM m_student WHERE student_no='DEMO-" & year & "-007'")
    Set result = service.DeleteStudent(deletedId, 1, "サンプル再投入で復活しないことを確認", True)
    AssertSample result("kind") = "Saved", "sample row can be logically deleted"
    before = SampleSnapshot(): output = EnsureSampleData(): after = SampleSnapshot()
    AssertSample Left$(output, 5) = "PASS|", "reapplication after user activity succeeds"
    AssertSample before = after, "reapplication preserves all user-created/edited rows and audit/version history"
    Set old = service.LoadStudent(id)
    AssertSample old("address_line2") = "利用者が編集した値" And old("row_version") = editedVersion, "edited sample value and version preserved"
    Set old = service.LoadStudent(userId)
    AssertSample old("student_no") = "USER-NEW" And old("remarks") = "サンプル投入処理が変更してはいけないユーザー入力", "non-sample user record preserved"
    AssertSample SampleScalar("SELECT class_name FROM m_class WHERE class_id=" & customClassId) = "利用者クラス", "non-sample user class preserved"
    AssertSample SampleScalar("SELECT class_name FROM m_class WHERE class_id=" & classId) = "利用者変更クラス", "user edits to sample class preserved"
    AssertSample CBool(SampleScalar("SELECT is_deleted FROM m_student WHERE student_id=" & deletedId)), "logical deletion of sample row is not reversed"
    ' Simulate a damaged deployment in this disposable fixture; no backfill is allowed outside bootstrap.
    db.Execute "DELETE FROM m_student WHERE student_no='DEMO-" & year & "-012'", dbFailOnError
    before = SampleSnapshot(): output = EnsureSampleData(): after = SampleSnapshot()
    AssertSample Left$(output, 5) = "FAIL|", "missing published sample key fails before insertion"
    AssertSample before = after, "published-key failure does not backfill or alter audit/version history"
    ' Remove only the sample marker from an editable sample row: the bootstrap must fail closed.
    db.Execute "UPDATE m_student SET remarks='利用者が所有する既存キー' WHERE student_id=" & id, dbFailOnError
    before = SampleSnapshot(): output = EnsureSampleData(): after = SampleSnapshot()
    AssertSample Left$(output, 5) = "FAIL|", "reserved key without marker fails closed"
    AssertSample before = after, "reserved-key collision neither inserts nor overwrites existing data"
    RunSampleDataTests = CStr(assertions) & " assertions passed"
    Exit Function
Failed:
    RunSampleDataTests = "FAILED after " & CStr(assertions) & " checks: " & CStr(Err.Number) & " " & Err.Description
End Function
