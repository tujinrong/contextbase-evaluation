Option Compare Binary
Option Explicit
Public Function Query(ByVal db As DAO.Database, ByVal sql As String, ParamArray values() As Variant) As DAO.QueryDef
    Dim q As DAO.QueryDef, i As Long
    Set q = db.CreateQueryDef("", sql)
    If q.Parameters.Count > 0 Then
        For i = 0 To q.Parameters.Count - 1: q.Parameters(i).Value = values(i): Next
    End If
    Set Query = q
End Function
Public Function Scalar(ByVal db As DAO.Database, ByVal sql As String) As Variant
    Dim rs As DAO.Recordset
    Set rs = db.OpenRecordset(sql, dbOpenSnapshot)
    If rs.EOF Then Reject "MSG-020"
    Scalar = rs.Fields(0).Value: rs.Close
End Function
Public Function ReadOne(ByVal q As DAO.QueryDef, Optional ByVal writable As Boolean = False) As DAO.Recordset
    Dim r As DAO.Recordset
    Set r = q.OpenRecordset(IIf(writable, dbOpenDynaset, dbOpenSnapshot))
    If Not r.EOF Then
        r.MoveLast
        If r.RecordCount <> 1 Then Reject "MSG-020"
        r.MoveFirst
    End If
    Set ReadOne = r
End Function
Public Function MakeResult(ByVal kind As String, Optional ByVal message As String = "", Optional ByVal field As String = "") As clsResult
    Dim result As New clsResult
    result.Kind = kind: result.MessageId = message: result.FieldId = field
    Set MakeResult = result
End Function
Public Function Failure(ByVal errorText As String, ByVal u As clsUnitOfWork, Optional ByVal readOnly As Boolean = False) As clsResult
    Dim msg As String, fields() As String, kind As String
    fields = Split(errorText, "|"): msg = fields(0)
    If Left$(msg, 4) <> "MSG-" Then msg = IIf(readOnly, "MSG-040", "MSG-017")
    If Not u Is Nothing Then
        If Not u.Cancel() And Not readOnly Then msg = "MSG-034"
        u.CloseUnit
    End If
    kind = "Validation"
    Select Case msg
        Case "MSG-002": kind = "AuthExpired"
        Case "MSG-003": kind = "Forbidden"
        Case "MSG-008": kind = "Conflict"
        Case "MSG-019": kind = "NotFound"
        Case "MSG-020": kind = "Integrity"
        Case "MSG-027", "MSG-029": kind = "Busy"
        Case "MSG-034": kind = "CommitUnknown"
        Case "MSG-017": kind = "DbRolledBack"
        Case "MSG-028", "MSG-040": kind = "ReadFailure"
    End Select
    Dim result As clsResult
    Set result = MakeResult(kind, msg)
    If UBound(fields) > 0 Then result.FieldId = fields(1)
    If UBound(fields) > 1 Then If IsNumeric(fields(2)) Then result.CareerOrdinal = CLng(fields(2))
    If msg = "MSG-026" And IsNumeric(result.FieldId) Then result.CareerOrdinal = CLng(result.FieldId)
    Set Failure = result
End Function
Public Sub CheckCode(ByVal db As DAO.Database, ByVal category As String, ByVal code As String, ByVal allowStopped As Boolean, Optional ByVal stored As Boolean = False)
    Dim q As DAO.QueryDef, r As DAO.Recordset
    Set q = Query(db, "PARAMETERS a Text(24), b Text(2); SELECT * FROM m_code WHERE category_id=a AND code=b", category, code)
    Set r = ReadOne(q)
    If r.EOF Then Reject IIf(stored, "MSG-020", "MSG-016")
    If Not allowStopped And Not r!is_enabled Then Reject "MSG-016"
    If CLng(r!revision) < 1 Then Reject "MSG-020"
    r.Close: q.Close
End Sub
Public Function CareerFromRow(ByVal r As DAO.Recordset) As clsCareerDraft
    Dim c As New clsCareerDraft
    c.PersistentId = r!career_id: c.StartMonth = Nz(r!start_month, 0): c.EndMonth = r!end_month
    c.Company = Nz(r!company_name, ""): c.Project = Nz(r!project_name, ""): c.Description = Nz(r!description, ""): c.Duties = Nz(r!duties, "")
    c.Achievements = r!achievements: c.Technologies = r!technologies: c.Phases = r!phases
    c.RoleCode = r!role_code: c.TeamSize = r!team_size
    Set CareerFromRow = c
End Function
Public Function EmployeeFromRow(ByVal r As DAO.Recordset) As clsEmployeeEdit
    Dim e As New clsEmployeeEdit
    e.EmployeeId = r!employee_id: e.ExpectedRevision = r!revision: e.EmployeeNo = r!employee_no
    e.Name = Nz(r!employee_name, ""): e.Kana = Nz(r!employee_kana, ""): e.Department = Nz(r!department_code, ""): e.Status = Nz(r!employment_status, "")
    e.JoinDate = Nz(r!join_date, 0): e.Summary = r!career_summary: e.Skills = r!skills: e.Qualifications = r!qualifications: e.SelfPr = r!self_pr
    Set EmployeeFromRow = e
End Function
Public Function LoadAggregate(ByVal db As DAO.Database, ByVal employeeId As Long, Optional ByVal strictValues As Boolean = False) As clsEmployeeEdit
    Dim q As DAO.QueryDef, r As DAO.Recordset, e As clsEmployeeEdit, c As clsCareerDraft
    Set q = Query(db, "PARAMETERS p Long; SELECT * FROM m_employee WHERE employee_id=p", employeeId)
    Set r = ReadOne(q)
    If r.EOF Then Reject "MSG-019"
    If CStr(Nz(r!department_category, "")) <> "DEPARTMENT" Or CStr(Nz(r!employment_category, "")) <> "EMPLOYMENT_STATUS" Then Reject "MSG-020"
    Set e = EmployeeFromRow(r): r.Close: q.Close
    CheckCode db, "DEPARTMENT", e.Department, True, True
    CheckCode db, "EMPLOYMENT_STATUS", e.Status, True, True
    Set q = Query(db, "PARAMETERS p Long; SELECT * FROM t_career WHERE employee_id=p ORDER BY start_month DESC, career_id DESC", employeeId)
    Set r = q.OpenRecordset(dbOpenSnapshot)
    Do While Not r.EOF
        If CStr(Nz(r!role_category, "")) <> "PROJECT_ROLE" Or CLng(r!employee_id) <> employeeId Then Reject "MSG-020"
        Set c = CareerFromRow(r): CheckCode db, "PROJECT_ROLE", c.RoleCode, True, True
        e.Careers.Add c: e.LoadedCareerIds.Add CLng(c.PersistentId), CStr(c.PersistentId)
        If e.Careers.Count > 20 Then Reject "MSG-020"
        r.MoveNext
    Loop
    r.Close: q.Close
    If IsNull(e.ExpectedRevision) Then Reject "MSG-020"
    If CLng(e.ExpectedRevision) < 1 Or Not Digits(e.EmployeeNo, 6) Then Reject "MSG-020"
    If strictValues Then CheckStoredAggregate e
    Set LoadAggregate = e
End Function
Public Sub WriteEmployee(ByVal r As DAO.Recordset, ByVal e As clsEmployeeEdit, ByVal actor As String, ByVal at As Date, ByVal version As Long)
    r!employee_no = e.EmployeeNo: r!employee_name = e.Name: r!employee_kana = e.Kana
    r!department_category = "DEPARTMENT": r!department_code = e.Department
    r!employment_category = "EMPLOYMENT_STATUS": r!employment_status = e.Status
    r!join_date = e.JoinDate: r!career_summary = e.Summary: r!skills = e.Skills: r!qualifications = e.Qualifications: r!self_pr = e.SelfPr
    r!updated_at = at: r!updated_by = actor: r!revision = version
End Sub
Public Sub WriteCareer(ByVal r As DAO.Recordset, ByVal c As clsCareerDraft, ByVal employeeId As Long)
    r!employee_id = employeeId: r!start_month = c.StartMonth: r!end_month = c.EndMonth
    r!company_name = c.Company: r!project_name = c.Project: r!description = c.Description: r!duties = c.Duties
    r!achievements = c.Achievements: r!technologies = c.Technologies: r!phases = c.Phases
    r!role_category = "PROJECT_ROLE": r!role_code = c.RoleCode: r!team_size = c.TeamSize
End Sub
Public Sub AssertIntegrity(ByVal db As DAO.Database)
    Dim t As DAO.TableDef, count As Long, q As DAO.QueryDef, r As DAO.Recordset, e As clsEmployeeEdit
    For Each t In db.TableDefs
        If Left$(t.Name, 4) <> "MSys" And Left$(t.Name, 1) <> "~" Then count = count + 1
    Next
    If count <> 5 Then Reject "MSG-020"
    If db.TableDefs("m_app_user").Fields.Count <> 8 Or db.TableDefs("m_employee").Fields.Count <> 16 Or db.TableDefs("t_career").Fields.Count <> 14 Or db.TableDefs("m_code_category").Fields.Count <> 2 Or db.TableDefs("m_code").Fields.Count <> 8 Then Reject "MSG-020"
    If Scalar(db, "SELECT Count(*) FROM m_employee") > 200 Then Reject "MSG-020"
    If Scalar(db, "SELECT Count(*) FROM m_code_category") <> 3 Then Reject "MSG-020"
    If Scalar(db, "SELECT Count(*) FROM m_code WHERE category_id='EMPLOYMENT_STATUS'") <> 3 Then Reject "MSG-020"
    Set r = db.OpenRecordset("SELECT employee_id FROM m_employee", dbOpenSnapshot)
    Do While Not r.EOF
        Set e = LoadAggregate(db, CLng(r!employee_id), True): r.MoveNext
    Loop
    r.Close
    Set r = db.OpenRecordset("SELECT category_id, Count(*) AS n FROM m_code GROUP BY category_id", dbOpenSnapshot)
    Do While Not r.EOF
        If r!n > 99 Then Reject "MSG-020"
        r.MoveNext
    Loop
    r.Close
    If Scalar(db, "SELECT Count(*) FROM t_career AS c LEFT JOIN m_employee AS e ON c.employee_id=e.employee_id WHERE e.employee_id Is Null") <> 0 Then Reject "MSG-020"
    If Scalar(db, "SELECT Count(*) FROM m_app_user WHERE failed_count<0 OR failed_count>5 OR role_id Not In ('ADMIN','STAFF')") <> 0 Then Reject "MSG-020"
End Sub
