Attribute VB_Name = "modEvidenceSearchAllR5"
Option Explicit
Option Compare Binary
Private checks As Long
Private checkLog As String
Private Sub Verify(ByVal condition As Boolean, ByVal label As String)
    checks = checks + 1
    checkLog = checkLog & CStr(checks) & vbTab & IIf(condition, "PASS", "FAIL") & vbTab & label & vbCrLf
    If Not condition Then Err.Raise vbObjectError + 221, , label
End Sub
Public Function EvidenceSearchAllR5() As String
    Dim frm As Access.Form, db As DAO.Database, rs As DAO.Recordset, name As Variant
    Dim classId As Long, year As Long, grade As String, gradeName As String
    On Error GoTo Failed
    If InStr(1, CurrentProject.FullName, "\build\20261012-evidence-01-r5\", vbTextCompare) = 0 Then Err.Raise vbObjectError + 221, , "Disposable R5 test build required"
    If InStr(1, CurrentProject.Name, "20261012-build-04-access-single-", vbTextCompare) <> 1 Then Err.Raise vbObjectError + 221, , "Test-only filename required"
    checks = 0: checkLog = ""
    Set db = CurrentDb()
    Set rs = db.OpenRecordset("SELECT TOP 1 c.class_id,c.school_year,c.grade_code,g.code_name FROM m_class c INNER JOIN m_code g ON c.grade_category=g.category_id AND c.grade_code=g.code_value ORDER BY c.class_id", dbOpenSnapshot)
    If rs.EOF Then Err.Raise vbObjectError + 221, , "Run application fixture tests first"
    classId = rs!class_id: year = rs!school_year: grade = rs!grade_code: gradeName = rs!code_name: rs.Close
    DoCmd.OpenForm "frmStudentSearch"
    Set frm = Forms("frmStudentSearch")
    For Each name In Array("cboSchoolYear", "cboGrade", "cboClass", "cboPrefecture")
        Verify Nz(frm.Controls(name).Column(1), "") = "すべて", "initial visible all " & name
        Verify IsNull(SearchFilterValue(frm, CStr(name))), "initial NULL criterion " & name
    Next
    frm!cboGrade = "00"
    Verify SearchFilterValue(frm, "cboGrade") = "00", "grade 00 retains its real meaning"
    ClearSearch
    Verify SearchClick("SEARCH") And frm!lblCount.Caption <> "検索失敗", "all sentinels reach production DAO search as NULL"
    frm!cboClass = classId: ClassChanged "CLASS"
    Verify SearchFilterValue(frm, "cboClass") = classId And frm!cboSchoolYear = year And frm!cboGrade = grade, "class choice synchronizes actual year and grade"
    Verify InStr(1, frm!cboClass.Column(1), gradeName, vbBinaryCompare) > 0, "class display includes grade name"
    RefreshClassChoices frm, Null
    Verify frm!cboClass = classId, "candidate refresh preserves compatible class"
    frm!cboGrade = IIf(grade = "00", "01", "00"): ClassChanged "GRADE"
    Verify IsNull(SearchFilterValue(frm, "cboClass")) And frm!cboClass.Column(1) = "すべて" And frm!lblMessage.Caption = MessageText("W-STU-107"), "incompatible class clears to all and preserves W-STU-107"
    frm!chkUnassignedOnly = True: ClassChanged "UNASSIGNED"
    Verify IsNull(SearchFilterValue(frm, "cboSchoolYear")) And IsNull(SearchFilterValue(frm, "cboGrade")) And IsNull(SearchFilterValue(frm, "cboClass")) And frm!cboSchoolYear.Column(1) = "すべて" And frm!cboGrade.Column(1) = "すべて" And frm!cboClass.Column(1) = "すべて" And Not frm!cboSchoolYear.Enabled And Not frm!cboGrade.Enabled And Not frm!cboClass.Enabled, "unassigned shows all NULL choices and disables class filters"
    ClearSearch
    For Each name In Array("cboSchoolYear", "cboGrade", "cboClass", "cboPrefecture")
        Verify Nz(frm.Controls(name).Column(1), "") = "すべて" And IsNull(SearchFilterValue(frm, CStr(name))), "clear restores all and NULL " & name
    Next
    Verify frm!cboSchoolYear.Enabled And frm!cboGrade.Enabled And frm!cboClass.Enabled, "clear re-enables class filters"
    Verify SearchClick("SEARCH") And frm!lblCount.Caption <> "検索失敗", "clear restores successful production search"
    EvidenceSearchAllR5 = "PASS|checks=" & CStr(checks) & vbCrLf & checkLog
    DoCmd.Close acForm, "frmStudentSearch"
    Exit Function
Failed:
    EvidenceSearchAllR5 = "FAIL|checks=" & CStr(checks) & "|" & CStr(Err.Number) & "|" & Err.Description & vbCrLf & checkLog
    On Error Resume Next: rs.Close: DoCmd.Close acForm, "frmStudentSearch"
End Function
