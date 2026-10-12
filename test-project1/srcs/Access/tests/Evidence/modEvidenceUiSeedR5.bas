Attribute VB_Name = "modEvidenceUiSeedR5"
Option Explicit
Option Compare Binary

' Only injected into the newly generated test ACCDB; never the production ACCDB.
Public Function EvidenceSeedUiR5() As String
    Dim db As DAO.Database, rs As DAO.Recordset, td As DAO.TableDef
    Dim raw As Object, result As Object, cls As Object, service As New clsStudentService
    Dim confirmation As clsConfirmation, day As String, year As Long, classId As Long, i As Long
    Dim names As Variant, kana As Variant, states As Variant, log As String
    On Error GoTo Failed
    If InStr(1, CurrentProject.FullName, "\build\20261012-evidence-01-ui-r5\", vbTextCompare) = 0 Then Err.Raise vbObjectError + 210, , "Owned evidence build folder required"
    If CurrentProject.Name <> "20261012-build-04-access-single-evidence-01-ui-r5.accdb" Then Err.Raise vbObjectError + 210, , "Exact fresh evidence filename required"
    Set db = CurrentDb()
    If db.Properties("StudentBackendPath") <> "SELF" Then Err.Raise vbObjectError + 210, , "SingleFile SELF required"
    For Each td In db.TableDefs
        If Left$(td.Name, 4) <> "MSys" And td.Connect <> "" Then Err.Raise vbObjectError + 210, , "External links forbidden"
    Next
    For Each names In Array("m_student", "m_class", "t_operation_log")
        Set rs = db.OpenRecordset("SELECT Count(*) AS n FROM " & CStr(names), dbOpenSnapshot)
        If rs!n <> 0 Then Err.Raise vbObjectError + 210, , "Fresh empty business tables required"
        rs.Close
    Next
    day = BusinessDay(UtcNow()): year = CLng(Left$(day, 4))
    If Mid$(day, 6, 2) < "04" Then year = year - 1
    Set cls = Map()
    cls.Add "school_year", CStr(year): cls.Add "grade_code", "01": cls.Add "class_code", "TEST-UI"
    cls.Add "class_name", "架空撮影A組": cls.Add "valid_from", CStr(year) & "-04-01": cls.Add "valid_to", CStr(year + 1) & "-03-31"
    cls.Add "capacity", "30": cls.Add "display_order", "0": cls.Add "is_active", True: cls.Add "remarks", "撮影用の架空データ"
    Set result = MaintainClass(cls, Null, Null)
    If result("kind") <> "Saved" Then Err.Raise vbObjectError + 210, , "MaintainClass returned " & result("kind") & " " & result("message")
    classId = result("class_id"): log = "class=" & CStr(classId) & ":Saved" & vbCrLf
    names = Array("仮名 太郎", "仮名 花子", "仮名 次郎")
    kana = Array("カナ タロウ", "カナ ハナコ", "カナ ジロウ")
    states = Array("01", "02", "03")
    For i = 0 To 2
        Set raw = TestDraft(classId, day)
        raw("student_no") = "TEST-ACE-00" & CStr(i + 1)
        raw("student_name") = names(i): raw("student_name_kana") = kana(i)
        raw("birth_era") = "HEISEI": raw("birth_year") = "20": raw("birth_month") = "05": raw("birth_day") = "15"
        raw("postal_code") = "1000001": raw("prefecture_code") = "13"
        raw("address_line1") = "架空試験町1": raw("address_line2") = "撮影専用"
        raw("phone_number") = "0000000000": raw("email_address") = "fixture" & CStr(i + 1) & "@example.invalid"
        raw("admission_date") = CStr(year) & "-04-01": raw("enrollment_status_code") = states(i)
        raw("enrollment_end_date") = Null
        If i = 2 Then raw("enrollment_end_date") = day
        raw("school_year") = CStr(year): raw("grade_code") = "01"
        raw("remarks") = "画面撮影用の架空データ。共有SQLには接続しない。"
        Set confirmation = New clsConfirmation
        Set result = service.SaveStudent(raw, Null, Null, "evidence-ui-r5-" & CStr(i + 1), confirmation, False, Null)
        If result("kind") <> "Saved" Then Err.Raise vbObjectError + 210, , "SaveStudent " & CStr(i + 1) & " returned " & result("kind") & " " & result("message")
        log = log & raw("student_no") & ":Saved:id=" & CStr(result("student_id")) & ":version=" & CStr(result("row_version")) & vbCrLf
    Next
    Set rs = db.OpenRecordset("SELECT Count(*) AS n FROM m_student", dbOpenSnapshot)
    If rs!n <> 3 Then Err.Raise vbObjectError + 210, , "Expected 3 students"
    rs.Close
    Set rs = db.OpenRecordset("SELECT Count(*) AS n FROM t_operation_log WHERE operation_type='CREATE'", dbOpenSnapshot)
    If rs!n <> 4 Then Err.Raise vbObjectError + 210, , "Expected 4 CREATE audits"
    rs.Close
    EvidenceSeedUiR5 = "PASS|businessDay=" & day & "|students=3|classes=1|audits=4" & vbCrLf & log
    Exit Function
Failed:
    EvidenceSeedUiR5 = "FAIL|" & CStr(Err.Number) & "|" & Err.Description & vbCrLf & log
    On Error Resume Next
    If Not rs Is Nothing Then rs.Close
End Function
