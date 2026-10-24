Attribute VB_Name = "modSelfTests"
Option Explicit
Option Compare Binary
Private checks As Long
Private checkLog As String
Private Sub Check(ByVal value As Boolean, ByVal label As String)
    checks = checks + 1
    checkLog = checkLog & CStr(checks) & vbTab & IIf(value, "PASS", "FAIL") & vbTab & label & vbCrLf
    Dim fileNumber As Integer
    fileNumber = FreeFile
    Open CurrentProject.Path & "\fixture-progress.log" For Append As #fileNumber
    Print #fileNumber, CStr(checks) & vbTab & IIf(value, "PASS", "FAIL") & vbTab & label
    Close #fileNumber
    If Not value Then Err.Raise vbObjectError + 190, , "Assertion failed: " & label
End Sub
' Run only against a newly generated disposable backend. Deliberately rejects populated data.
Public Function RunSelfTests() As String
    Dim tx As New clsUnitOfWork, repo As New clsStudentRepository, rs As DAO.Recordset, service As New clsStudentService
    Dim classRaw As Object, raw As Object, result As Object, old As Object, confirm As New clsConfirmation, otherConfirm As New clsConfirmation
    Dim classId As Long, id As Long, otherId As Long, year As Long, utc As Date, day As String, expected As Long, normalized As Object, criteria As Object
    On Error GoTo Failed
    checks = 0: checkLog = "": Authorize "Master": utc = UtcNow(): day = BusinessDay(utc)
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
    criteria.Add "studentNo", Null: criteria.Add "name", Null: criteria.Add "class", Null
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
Public Function TestDraft(ByVal classId As Long, ByVal day As String) As Object
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
Public Function TestCheckLog() As String
    TestCheckLog = checkLog
End Function
Public Function RunExtendedTests() As String
    Dim tx As New clsUnitOfWork, repo As New clsStudentRepository, service As New clsStudentService, rs As DAO.Recordset
    Dim raw As Object, result As Object, old As Object, confirmation As New clsConfirmation, d As Object, codeRaw As Object
    Dim id As Long, classId As Long, version As Long, mask As Long, utc As Date, day As String, auditCount As Long
    On Error GoTo Failed
    checks = 0: checkLog = "": Authorize "Master": CheckFixture
    utc = UtcNow(): day = BusinessDay(utc)
    Set result = ReapplyInitialMasters(): Check result("kind") = "NoChange", "initial 5/70 reapplication no change"
    tx.BeginWork: Set repo.Database = tx.Database
    Set rs = repo.Database.OpenRecordset("SELECT * FROM m_student WHERE student_no='TEST-001'")
    If rs.EOF Then Err.Raise vbObjectError + 191, , "First run RunSelfTests on this disposable fixture"
    Set old = repo.RowMap(rs): id = old("student_id"): classId = old("class_id"): version = old("row_version"): rs.Close: tx.CloseWork
    Set raw = TestDraft(classId, day)
    raw("emergency_contact_name") = "山田一郎": raw("relationship_code") = "01": raw("emergency_phone_number") = "090-1234-5678"
    Set result = service.SaveStudent(raw, id, version, "extended", confirmation, False, Null)
    Check result("kind") = "Saved", "R74-02 full emergency save": version = result("row_version")
    Set old = service.LoadStudent(id)
    Check old("relationship_category") = "RELATIONSHIP" And old("relationship_code") = "01", "derived category/code readback"
    Check old("emergency_contact_name") = "山田一郎" And old("emergency_phone_number") = "09012345678", "emergency Unicode/phone roundtrip"
    ProbeReferencedParent "DELETE FROM m_code WHERE category_id='RELATIONSHIP' AND code_value='01'", "R74-08 actual student parent delete rejected"
    ProbeReferencedParent "UPDATE m_code SET code_value='08' WHERE category_id='RELATIONSHIP' AND code_value='01'", "R74-08 actual student parent key update rejected"
    raw("emergency_contact_name") = Null: raw("relationship_code") = Null: raw("emergency_phone_number") = Null
    Set result = service.SaveStudent(raw, id, version, "extended", confirmation, False, Null)
    Check result("kind") = "Saved", "R74-03 all emergency clear": version = result("row_version")
    Set old = service.LoadStudent(id)
    Check IsNull(old("relationship_category")) And IsNull(old("relationship_code")) And IsNull(old("emergency_contact_name")) And IsNull(old("emergency_phone_number")), "all four NULL readback"
    tx.BeginWork: Set repo.Database = tx.Database
    Set rs = repo.Database.OpenRecordset("SELECT TOP 1 * FROM t_operation_log WHERE target_table='m_student' ORDER BY log_id DESC")
    Check InStr(1, rs!changed_columns, """relationship_category""", vbBinaryCompare) > 0, "R74-03 classification included in changed columns"
    Check InStr(1, rs!changed_columns, "山田", vbBinaryCompare) = 0, "audit omits raw personal values": rs.Close: tx.CloseWork
    Set result = service.SaveStudent(raw, id, version, "extended", confirmation, False, Null)
    Check result("kind") = "NoChange", "R74-12 cleared re-save no change"
    raw("emergency_contact_name") = "一部のみ"
    Set result = service.SaveStudent(raw, id, version, "extended", confirmation, False, Null)
    Check result("message") = "E-STU-019", "partial emergency rejected before DAO"
    raw("emergency_contact_name") = Null: raw("phone_number") = Null
    Set result = service.SaveStudent(raw, id, version, "extended", confirmation, False, Null)
    Check result("message") = "E-STU-018", "R74-09 contact still required": raw("phone_number") = "0312345678"
    For mask = 0 To 15
        ProbeStudentNullPattern old, mask, mask = 0 Or mask = 15
    Next
    ProbeStudentInvalidCode old, "RELATIONSHIP", "98", "R74-06 full student FK rejects unknown code"
    ProbeStudentInvalidCode old, "GRADE", "01", "R74-07 full student row rejects different category"
    raw("student_name") = String$(9, "名")
    Set result = service.SaveStudent(raw, id, version, "extended", confirmation, False, Null)
    Check InStr(result("message"), "E-STU-002|fieldKey=student_name|field=氏名|max=8") = 1, "field/max message parameters"
    raw("student_name") = "山田太郎"
    FixtureRole "Reader"
    Set result = service.SaveStudent(raw, id, version, "extended", confirmation, False, Null)
    Check result("message") = "E-COM-002", "Reader cannot save"
    Set result = service.DeleteStudent(id, version, "検証", True)
    Check result("message") = "E-COM-002", "Reader cannot delete"
    Set old = service.LoadStudent(id): Check old("student_id") = id, "Reader can read"
    FixtureRole "Staff"
    Set result = service.DeleteStudent(id, version, "検証", True): Check result("message") = "E-COM-002", "Staff cannot delete"
    Set result = ReapplyInitialMasters(): Check result("message") = "E-COM-002", "Staff cannot maintain masters"
    FixtureRole "invalid"
    Set result = service.SaveStudent(raw, id, version, "extended", confirmation, False, Null)
    Check result("message") = "E-COM-001", "unrecognized role is authentication failure"
    FixtureRole "Admin"
    ' Force only audit append failure; no data or version changes may survive.
    tx.BeginWork: tx.Database.Execute "ALTER TABLE t_operation_log ADD COLUMN fixture_required TEXT(1) NOT NULL", dbFailOnError: tx.Commit: tx.CloseWork
    raw("address_line2") = "履歴失敗で取消"
    Set result = service.SaveStudent(raw, id, version, "extended", confirmation, False, Null)
    Check Left$(result("message"), 9) = "E-COM-004", "R74-10 audit failure returns system error"
    Set old = service.LoadStudent(id)
    Check old("row_version") = version And IsNull(old("address_line2")), "R74-10 student/row version rollback"
    tx.BeginWork: tx.Database.Execute "ALTER TABLE t_operation_log DROP COLUMN fixture_required", dbFailOnError: tx.Commit: tx.CloseWork
    Set codeRaw = Map(): codeRaw.Add "code_name", "検証用": codeRaw.Add "display_order", "99": codeRaw.Add "is_active", True
    codeRaw.Add "valid_from", "1900-01-01": codeRaw.Add "valid_to", Null: codeRaw.Add "remarks", Null
    Set result = MaintainCode("RELATIONSHIP", "98", codeRaw, Null): Check result("kind") = "Saved", "admin code create"
    codeRaw("is_active") = False
    Set result = MaintainCode("RELATIONSHIP", "98", codeRaw, 1): Check result("kind") = "Saved", "admin code disable"
    Check LatestMasterOperation() = "DISABLE", "active to stopped audit DISABLE"
    codeRaw("code_name") = "名称変更"
    Set result = MaintainCode("RELATIONSHIP", "98", codeRaw, 2): Check result("kind") = "Saved", "stopped code rename"
    Check LatestMasterOperation() = "UPDATE", "R74-14 stopped rename audit UPDATE"
    codeRaw("is_active") = True
    Set result = MaintainCode("RELATIONSHIP", "98", codeRaw, 3): Check result("kind") = "Saved", "code enable"
    Check LatestMasterOperation() = "ENABLE", "stopped to active audit ENABLE"
    Set result = ReapplyInitialMasters(): Check result("message") = "E-MST-001", "seed difference stops without overwrite"
    codeRaw("is_active") = False
    Set result = MaintainCode("ENROLLMENT_STATUS", "01", codeRaw, 1): Check result("message") = "E-MST-003", "protected enrollment code stop refused"
    Set result = MaintainCode("RELATIONSHIP", "XX", codeRaw, Null): Check Left$(result("message"), 9) = "E-STU-009", "code values digits only"
    Set raw = TestDraft(classId, day): raw("student_no") = "TEST-CLEAR": raw("student_name") = "佐藤花子": raw("student_name_kana") = "サトウハナコ"
    Set result = service.SaveStudent(raw, Null, Null, "zero-set", confirmation, False, Null)
    Check result("kind") = "Saved", "second distinct student at last seat"
    Dim candidateId As Long, candidateVersion As Long, extra As New clsConfirmation
    candidateId = result("student_id"): candidateVersion = result("row_version")
    raw("student_no") = "TEST-ZERO": raw("enrollment_status_code") = "03": raw("enrollment_end_date") = day: raw("class_id") = Null
    Set result = service.SaveStudent(raw, Null, Null, "zero-set", extra, False, Null)
    Check result("kind") = "ConfirmationRequired", "duplicate original set pinned"
    Set result = service.DeleteStudent(candidateId, candidateVersion, "試験の集合変更", True): Check result("kind") = "Saved", "remove all duplicate candidates"
    Set result = service.SaveStudent(raw, Null, Null, "zero-set", extra, True, "別人確認")
    Check result("kind") = "ConfirmationRequired" And result("candidates").Count = 0, "candidate set to zero requires reconfirmation"
    Set result = service.SaveStudent(raw, Null, Null, "zero-set", extra, True, "再確認")
    Check result("kind") = "Saved", "zero-set reconfirmed save"
    Dim endedId As Long, endedVersion As Long
    endedId = result("student_id"): endedVersion = result("row_version")
    raw("enrollment_status_code") = "01": raw("enrollment_end_date") = Null: raw("class_id") = classId
    FixtureRole "Staff"
    Set result = service.SaveStudent(raw, endedId, endedVersion, "ended", confirmation, False, "訂正")
    Check result("message") = "E-COM-002", "R74-15 Staff ended correction forbidden"
    FixtureRole "Admin"
    Set result = service.SaveStudent(raw, endedId, endedVersion, "ended", confirmation, False, Null)
    Check result("message") = "E-STU-106", "Admin ended correction needs reason"
    Set result = service.SaveStudent(raw, endedId, endedVersion, "ended", confirmation, False, "在籍区分の訂正")
    Check result("kind") = "Saved", "Admin ended correction with reason saves"
    Set result = service.SaveStudent(raw, Null, 1, "malformed", confirmation, False, Null)
    Check result("message") = "E-COM-003", "new target rejects unexpected version"
    Set result = service.DeleteStudent(endedId, endedVersion, "旧版削除", True)
    Check result("message") = "E-STU-105", "delete rechecks expected version"
    Check MessageText("E-STU-001|field=氏名") = "E-STU-001: 氏名を入力してください。", "message expansion"
    RunExtendedTests = CStr(checks) & " assertions passed"
    Exit Function
Failed:
    RunExtendedTests = "FAILED after " & CStr(checks) & " checks: " & CStr(Err.Number) & " " & Err.Description
    On Error Resume Next: tx.CloseWork: FixtureRole "Admin"
End Function
Private Sub ProbeReferencedParent(ByVal sql As String, ByVal label As String)
    Dim tx As New clsUnitOfWork, accepted As Boolean, number As Long
    On Error GoTo Rejected
    tx.BeginWork: tx.Database.Execute sql, dbFailOnError: accepted = True
Rejected:
    number = Err.Number
    On Error Resume Next: tx.CloseWork: On Error GoTo 0
    Check Not accepted And number = 3200, label & " DAO=" & CStr(number)
End Sub
Public Function RunFormTests() As String
    Dim frm As Access.Form, service As New clsStudentService, old As Object, id As Long, savedName As String, item As Object, i As Long, receivedRevision As Long
    On Error GoTo Failed
    checks = 0: checkLog = "": Authorize "Master": CheckFixture
    DoCmd.OpenForm "frmStudentSearch"
    Set frm = Forms("frmStudentSearch")
    Check frm.RecordSource = "", "search form unbound"
    Check frm!cboPageSize = 20 And frm!cboSortKey = "studentNo" And frm!cboSortDirection = "asc", "initial search page/sort defaults"
    Check frm!chkEnrolled And frm!chkLeave And Not Nz(frm!chkGraduated, False) And Not Nz(frm!chkWithdrawn, False), "initial 01/02 statuses"
    Check StudentListCallback(frm!lstStudents, 1, 0, 0, acLBGetRowCount) = 0, "initial form does not load students"
    SearchClick "SEARCH"
    Check StudentListCallback(frm!lstStudents, 1, 0, 0, acLBGetRowCount) = 2, "native list callback rows"
    receivedRevision = CLng(frm!txtContextRevision)
    frm!txtContextRevision = receivedRevision - 1: SearchClick "NEXT"
    Check StudentListCallback(frm!lstStudents, 1, 0, 0, acLBGetRowCount) = 2, "stale search revision preserves current list"
    ClearSearch
    Check StudentListCallback(frm!lstStudents, 1, 0, 0, acLBGetRowCount) = 2, "stale clear revision cannot erase results"
    frm!txtContextRevision = receivedRevision
    id = StudentListCallback(frm!lstStudents, 1, 0, 0, acLBGetValue)
    frm!lstStudents = id: SelectedStudentDetails
    Check InStr(frm!txtSelectedDetails, "山田太郎") > 0, "selected full text presentation"
    frm!txtName = "一致なし"
    SearchClick "NEXT"
    Check StudentListCallback(frm!lstStudents, 1, 0, 0, acLBGetRowCount) = 2, "page uses AppliedCriteria, not edited raw conditions"
    SearchClick "SEARCH"
    Check StudentListCallback(frm!lstStudents, 1, 0, 0, acLBGetRowCount) = 0, "explicit search applies changed conditions"
    ClearSearch
    Check StudentListCallback(frm!lstStudents, 1, 0, 0, acLBGetRowCount) = 0 And frm!lblCount.Caption = "未検索", "clear resets results/context"
    Check frm!cboClass.Enabled And frm!cboClass = 0, "clear restores all-class filter"
    Check frm!lstStudents.ColumnCount = 8, "hidden ID and seven visible native columns"
    Check frm.Width <= 19200 And frm.Section(acDetail).Height <= 9750, "search fits 1280x650 at 96 dpi"
    Check frm!cmdOpenSelected.OnClick = "=OpenStudent(False)", "explicit selected row action"
    Check frm!txtName.Height >= 510 And frm!txtName.FontSize >= 9, "search minimum input size and font"
    DoCmd.OpenForm "frmDiscardConfirm"
    Check Forms("frmDiscardConfirm").Modal And Forms("frmDiscardConfirm").PopUp, "discard is a separate modal popup"
    Check Forms("frmDiscardConfirm")!cmdCancel.Default And Forms("frmDiscardConfirm")!cmdCancel.Cancel, "discard default and escape cancel"
    DiscardCancel
    frm.SetFocus
    DoCmd.Close acForm, frm.Name
    DoCmd.OpenForm "frmStudentEdit", , , , , , CStr(id) & "|form-test"
    Set frm = Forms("frmStudentEdit")
    Check frm.RecordSource = "", "edit form unbound"
    Check frm.Width <= 19200 And frm.Section(acDetail).Height <= 9750, "editor fits 1280x650 at 96 dpi"
    Check frm!txtRemarks.EnterKeyBehavior And frm!txtRemarks.Height > 510, "multiline memo remains editable"
    Check frm!txtOperationReason.EnterKeyBehavior And frm!cmdSave.Top + frm!cmdSave.Height <= 9750, "reason and save fit compact editor"
    Check frm!txtStudentNo.Locked And frm!cmdDelete.Visible, "existing no immutable and Admin delete action"
    Check InStr(frm!lblCapacity.Caption, "2／2") > 0, "occupancy/capacity reference display"
    Check frm!cboBirthEra = "HEISEI" And CLng(frm!txtBirthYear) = 15 And CLng(frm!txtBirthMonth) = 4 And CLng(frm!txtBirthDay) = 2, "saved birth -> four era controls"
    Set old = service.LoadStudent(id): savedName = old("student_name")
    frm!txtStudentName = "移動未保存": DoCmd.Close acForm, frm.Name
    Set old = service.LoadStudent(id): Check old("student_name") = savedName, "form movement does not auto-save"
    FixtureRole "Reader"
    DoCmd.OpenForm "frmStudentEdit", , , , , , CStr(id) & "|reader-test"
    Set frm = Forms("frmStudentEdit")
    Check frm!txtStudentName.Locked And Not frm!cmdSave.Visible And Not frm!cmdDelete.Visible, "Reader physical form locks/hides writes"
    DoCmd.Close acForm, frm.Name: FixtureRole "Admin"
    DoCmd.OpenForm "frmStudentEdit"
    Set frm = Forms("frmStudentEdit")
    Check frm!cboGender = "0" And frm!cboEnrollmentStatus = "01", "new form initial codes"
    Check IsNull(frm!cboBirthEra) And IsNull(frm!txtAdmissionDate), "new birth/admission empty"
    Check Not IsNull(frm!cboSchoolYear), "new current school year"
    DoCmd.Close acForm, frm.Name
    ConfirmationMode = "DUPLICATE": ConfirmationReason = Null: Set ConfirmationRows = New Collection
    DoCmd.OpenForm "frmDuplicateConfirm": Set frm = Forms("frmDuplicateConfirm")
    Check frm!cmdCancel.Default And frm!cmdCancel.Cancel, "confirmation default/Esc is cancel"
    Check CandidateListCallback(frm!lstCandidates, 1, 0, 0, acLBGetRowCount) = 0, "changed candidate set to zero opens actual dialog"
    ConfirmationOk
    Check Not ConfirmationAccepted And frm!lblError.Caption <> "", "empty confirmation reason keeps dialog open"
    frm!txtReason = "別人の再確認": ConfirmationOk
    Check ConfirmationAccepted And ConfirmationReason = "別人の再確認", "valid dialog reason accepted"
    Set ConfirmationRows = New Collection
    For i = 1 To 21
        Set item = Map(): item.Add "student_no", "C" & CStr(i): item.Add "student_name", "候補": item.Add "birth_date", "2003-04-02": item.Add "class_display", "参照クラス"
        ConfirmationRows.Add item
    Next
    DoCmd.OpenForm "frmDuplicateConfirm": Set frm = Forms("frmDuplicateConfirm")
    Check CandidateListCallback(frm!lstCandidates, 1, 0, 0, acLBGetRowCount) = 20 And InStr(frm!lblPrompt.Caption, "21件") > 0, "actual candidate dialog shows 20 of full 21"
    Check CandidateListCallback(frm!lstCandidates, 1, 0, 2, acLBGetValue) = FormatBirthDate("2003-04-02"), "candidate birth date era display"
    ConfirmationCancel: Check Not ConfirmationAccepted, "candidate cancel rejects continuation"
    ConfirmationMode = "DELETE": ConfirmationReason = Null: ConfirmationStudentNo = "TEST-UI"
    DoCmd.OpenForm "frmDeleteConfirm": Set frm = Forms("frmDeleteConfirm")
    Check InStr(frm!lblPrompt.Caption, "TEST-UI") > 0, "delete dialog binds original target"
    frm!txtReason = "試験取消": ConfirmationCancel
    Check Not ConfirmationAccepted, "delete dialog cancellation"
    RunFormTests = CStr(checks) & " assertions passed"
    Exit Function
Failed:
    RunFormTests = "FAILED after " & CStr(checks) & " checks: " & CStr(Err.Number) & " " & Err.Description
    On Error Resume Next: FixtureRole "Admin"
    DoCmd.Close acForm, "frmStudentEdit": DoCmd.Close acForm, "frmStudentSearch": DoCmd.Close acForm, "frmDuplicateConfirm": DoCmd.Close acForm, "frmDeleteConfirm"
End Function
Public Function PrepareRaceFixture() As String
    Dim raw As Object, day As String, year As Long, result As Object
    Authorize "Master": CheckFixture
    day = BusinessDay(UtcNow()): year = CLng(Left$(day, 4)): If Mid$(day, 6, 2) < "04" Then year = year - 1
    Set raw = Map(): raw.Add "school_year", CStr(year): raw.Add "grade_code", "00": raw.Add "class_code", "RACE-1"
    raw.Add "class_name", "競合試験専用": raw.Add "valid_from", CStr(year) & "-04-01": raw.Add "valid_to", CStr(year + 1) & "-03-31"
    raw.Add "capacity", "1": raw.Add "display_order", "1": raw.Add "is_active", True: raw.Add "remarks", Null
    Set result = MaintainClass(raw, Null, Null)
    PrepareRaceFixture = result("kind")
End Function
Public Function RaceSaveFixture(ByVal number As String, ByVal name As String) As String
    Dim tx As New clsUnitOfWork, rs As DAO.Recordset, raw As Object, service As New clsStudentService, confirmation As New clsConfirmation, result As Object, classId As Long
    On Error GoTo Failed
    CheckFixture
    tx.BeginWork: Set rs = tx.Database.OpenRecordset("SELECT class_id FROM m_class WHERE class_code='RACE-1'")
    classId = rs!class_id: rs.Close: tx.CloseWork
    Set raw = TestDraft(classId, BusinessDay(UtcNow()))
    raw("student_no") = number: raw("student_name") = name: raw("student_name_kana") = name
    Set result = service.SaveStudent(raw, Null, Null, number, confirmation, False, Null)
    RaceSaveFixture = result("kind") & "|" & result("message")
    Exit Function
Failed:
    RaceSaveFixture = "Failed|" & CStr(Err.Number) & "|" & Err.Description
    On Error Resume Next: tx.CloseWork
End Function
Private Sub CheckFixture()
    Dim path As String
    path = CurrentDb.Properties("StudentBackendPath")
    If path = "SELF" Then path = CurrentProject.FullName
    If InStr(1, path, CurrentProject.Path & "\", vbTextCompare) <> 1 Or InStr(1, path, "\Access\build\", vbTextCompare) = 0 Then Err.Raise vbObjectError + 191, , "Disposable Access build fixture required"
    If Not CurrentDb.Properties("StudentTestFixture") Then Err.Raise vbObjectError + 191, , "Generated test-only fixture required"
End Sub
Private Sub FixtureRole(ByVal role As String)
    Dim fs As Object, stream As Object, q As DAO.QueryDef, db As DAO.Database
    CheckFixture
    If CurrentDb.Properties("StudentBackendPath") = "SELF" Then
        Set db = CurrentDb
        If role = "invalid" Then
            Set q = db.CreateQueryDef("", "PARAMETERS pUser TEXT(128); DELETE FROM t_app_role WHERE user_id=pUser")
        Else
            Set q = db.CreateQueryDef("", "PARAMETERS pUser TEXT(128); DELETE FROM t_app_role WHERE user_id=pUser")
            q.Parameters!pUser = CurrentUserId(): q.Execute dbFailOnError: q.Close
            Set q = db.CreateQueryDef("", "PARAMETERS pUser TEXT(128),pRole TEXT(10); INSERT INTO t_app_role(user_id,role_name) VALUES(pUser,pRole)")
            q.Parameters!pRole = role
        End If
        q.Parameters!pUser = CurrentUserId(): q.Execute dbFailOnError: q.Close
        Exit Sub
    End If
    Set fs = CreateObject("Scripting.FileSystemObject")
    Set stream = fs.CreateTextFile(CurrentProject.Path & "\roles.conf", True, True)
    stream.WriteLine CurrentUserId() & "=" & role: stream.Close
End Sub
Private Sub ProbeStudentNullPattern(ByVal original As Object, ByVal mask As Long, ByVal allowed As Boolean)
    Dim values As Variant
    values = Array(Null, Null, Null, Null)
    If (mask And 1) <> 0 Then values(0) = "検証親"
    If (mask And 2) <> 0 Then values(1) = "RELATIONSHIP"
    If (mask And 4) <> 0 Then values(2) = "01"
    If (mask And 8) <> 0 Then values(3) = "0312345678"
    ProbeStudent original, values, allowed, "R74-04 full student NULL pattern " & CStr(mask)
End Sub
Private Sub ProbeStudentInvalidCode(ByVal original As Object, ByVal category As String, ByVal code As String, ByVal label As String)
    ProbeStudent original, Array("検証親", category, code, "0312345678"), False, label
End Sub
Private Sub ProbeStudent(ByVal original As Object, ByVal values As Variant, ByVal allowed As Boolean, ByVal label As String)
    Dim tx As New clsUnitOfWork, rs As DAO.Recordset, k As Variant, accepted As Boolean, errorNumber As Long
    On Error GoTo Rejected
    tx.BeginWork: Set rs = tx.Database.OpenRecordset("m_student", dbOpenDynaset): rs.AddNew
    For Each k In original.Keys
        If k <> "student_id" Then rs.Fields(k).Value = original(k)
    Next
    rs!student_no = "PROBE-74": rs!emergency_contact_name = values(0): rs!relationship_category = values(1): rs!relationship_code = values(2): rs!emergency_phone_number = values(3)
    rs.Update: accepted = True
Rejected:
    errorNumber = Err.Number
    On Error Resume Next: rs.Close: tx.CloseWork: On Error GoTo 0
    Check accepted = allowed, label & " DAO=" & CStr(errorNumber)
    If Not allowed Then Check errorNumber = 3317 Or errorNumber = 3201, "rejection is row rule/FK"
End Sub
Private Function LatestMasterOperation() As String
    Dim tx As New clsUnitOfWork, rs As DAO.Recordset
    tx.BeginWork: Set rs = tx.Database.OpenRecordset("SELECT TOP 1 operation_type FROM t_operation_log WHERE target_table='m_code' ORDER BY log_id DESC")
    LatestMasterOperation = rs!operation_type: rs.Close: tx.CloseWork
End Function

Private Function CriteriaFixture() As Object
    Dim raw As Object
    Set raw = Map()
    raw.Add "studentNo", Null: raw.Add "name", Null: raw.Add "class", Null
    raw.Add "status01", True: raw.Add "status02", True: raw.Add "status03", False: raw.Add "status04", False
    Set CriteriaFixture = raw
End Function
Private Function CriteriaRejected(ByVal raw As Object, ByVal expected As String) As Boolean
    Dim d As clsSearchCriteria
    On Error GoTo Rejected
    Set d = NormalizeCriteria(raw, BusinessDay(UtcNow()))
    Exit Function
Rejected:
    CriteriaRejected = Err.Description = expected
End Function
Public Function RunSearchContractTests() As String
    Dim raw As Object, d As clsSearchCriteria, result As Object, key As Variant, row As Object
    Dim ctx As New clsSearchContext, oldRevision As Long, frm As Access.Form
    On Error GoTo Failed
    checks = 0: checkLog = "": Authorize "Master": CheckFixture
    Set raw = CriteriaFixture(): Set d = NormalizeCriteria(raw, BusinessDay(UtcNow()))
    Check d.StudentNoPrefix = "" And d.NameKey = "" And IsNull(d.ClassId), "four criteria empty optional fields"
    For Each key In Array("kana", "phone", "year", "grade", "prefecture", "unassigned", "from", "to", "unknown")
        raw.Add CStr(key), Null
        Check CriteriaRejected(raw, "E-SRC-001"), "reject even empty retired or unknown key " & CStr(key)
        raw.Remove key
    Next
    raw("status01") = "true": Check CriteriaRejected(raw, "E-SRC-001"), "reject nonboolean native status"
    raw("status01") = True: raw("studentNo") = "ＴＥＳＴ－"
    Set d = NormalizeCriteria(raw, BusinessDay(UtcNow())): Check d.StudentNoPrefix = "TEST-", "prefix normalization"
    Set result = SearchStudents(d, 1, 20, "updatedAt", "desc")
    Check result("kind") = "Found" And result("rows").Count = 2, "updated timestamp remains permitted internal sort"
    For Each row In result("rows")
        For Each key In Array("address_display", "address_line1", "phone_number", "updated_at", "name_key", "admission_date", "class_id", "enrollment_status_code")
            Check Not row.Exists(key), "display DTO omits " & CStr(key)
        Next
        Check row.Count = 9, "display DTO has eight values plus hidden student ID"
    Next
    raw("name") = "*": Set d = NormalizeCriteria(raw, BusinessDay(UtcNow()))
    Set result = SearchStudents(d, 1, 20, "studentNo", "asc")
    Check result("total") = 0, "name wildcard is compared as literal"
    Set raw = CriteriaFixture(): Set d = NormalizeCriteria(raw, BusinessDay(UtcNow()))
    d.ClassId = 2147483647: Set result = SearchStudents(d, 1, 20, "studentNo", "asc")
    Check result("message") = "E-STU-010", "nonexistent class rejected"
    ctx.Reset "test-form": oldRevision = ctx.Revision
    Check ctx.CriteriaFormatVersion = 2 And oldRevision > 0, "fresh version two context"
    Check ctx.RequestError("test-form", ctx.ContextId, oldRevision) = "", "valid context owner session form revision"
    Check ctx.RequestError("another-form", ctx.ContextId, oldRevision) = "E-COM-002", "foreign form rejected"
    Check ctx.RequestError("test-form", "wrong-state", oldRevision) = "E-COM-002", "foreign state identifier rejected"
    Check ctx.RequestError("test-form", ctx.ContextId, Null) = "E-SRC-002", "missing revision rejected"
    ctx.Acquire "test-form", ctx.ContextId, oldRevision
    Check ctx.RequestError("test-form", ctx.ContextId, oldRevision) = "E-SRC-002", "same-revision reentry rejected"
    ctx.Advance: ctx.ReleaseUpdate
    Check ctx.RequestError("test-form", ctx.ContextId, oldRevision) = "E-SRC-002", "old revision rejected after update"
    ctx.CriteriaFormatVersion = 1
    Check ctx.RequestError("test-form", ctx.ContextId, ctx.Revision) = "W-SRC-002", "old format expires"
    ctx.Reset "test-form": ctx.LastUsedAt = DateAdd("n", -30, UtcNow())
    Check ctx.RequestError("test-form", ctx.ContextId, ctx.Revision) = "W-SRC-002", "thirty minute expiry"
    RunSearchContractTests = CStr(checks) & " assertions passed": Exit Function
Failed:
    RunSearchContractTests = "FAILED after " & CStr(checks) & " checks: " & CStr(Err.Number) & " " & Err.Description
End Function
