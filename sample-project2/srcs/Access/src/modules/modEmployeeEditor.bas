Option Compare Binary
Option Explicit
Public Function CareerSame(ByVal a As clsCareerDraft, ByVal b As clsCareerDraft) As Boolean
    CareerSame = Same(a.StartMonth, b.StartMonth) And Same(a.EndMonth, b.EndMonth) And Same(a.Company, b.Company) And Same(a.Project, b.Project) And Same(a.Description, b.Description) And Same(a.Duties, b.Duties) And Same(a.Achievements, b.Achievements) And Same(a.Technologies, b.Technologies) And Same(a.Phases, b.Phases) And Same(a.RoleCode, b.RoleCode) And Same(a.TeamSize, b.TeamSize)
End Function
Public Function EmployeeSame(ByVal a As clsEmployeeEdit, ByVal b As clsEmployeeEdit) As Boolean
    Dim c As clsCareerDraft, old As clsCareerDraft
    If Not (Same(a.EmployeeNo, b.EmployeeNo) And Same(a.Name, b.Name) And Same(a.Kana, b.Kana) And Same(a.Department, b.Department) And Same(a.Status, b.Status) And Same(a.JoinDate, b.JoinDate) And Same(a.Summary, b.Summary) And Same(a.Skills, b.Skills) And Same(a.Qualifications, b.Qualifications) And Same(a.SelfPr, b.SelfPr)) Then Exit Function
    If a.Careers.Count <> b.Careers.Count Then Exit Function
    For Each c In a.Careers
        If IsNull(c.PersistentId) Then Exit Function
        Set old = FindCareer(b.Careers, CLng(c.PersistentId))
        If old Is Nothing Then Exit Function
        If Not CareerSame(c, old) Then Exit Function
    Next
    EmployeeSame = True
End Function
Public Function FindCareer(ByVal items As Collection, ByVal id As Long) As clsCareerDraft
    Dim c As clsCareerDraft
    For Each c In items
        If Not IsNull(c.PersistentId) Then
            If CLng(c.PersistentId) = id Then Set FindCareer = c: Exit Function
        End If
    Next
End Function
Public Sub NormalizeCareer(ByVal c As clsCareerDraft, ByVal today As Date)
    CheckText c.Company, 100, True, "会社名": CheckText c.Project, 100, True, "案件名"
    CheckText c.Description, 1000, True, "業務概要": CheckText c.Duties, 1000, True, "担当業務"
    CheckText c.Achievements, 1000, False, "実績": CheckText c.Technologies, 500, False, "技術環境": CheckText c.Phases, 200, False, "工程"
    c.Company = SaveText(c.Company): c.Project = SaveText(c.Project): c.Description = SaveText(c.Description): c.Duties = SaveText(c.Duties)
    c.Achievements = SaveText(c.Achievements): c.Technologies = SaveText(c.Technologies): c.Phases = SaveText(c.Phases)
    If c.TeamSize < 1 Or c.TeamSize > 999 Then Reject "MSG-005", "チーム人数"
    If Not ValidCode(c.RoleCode) Then Reject "MSG-016", "役割"
    If Day(c.StartMonth) <> 1 Or c.StartMonth <> DateValue(c.StartMonth) Or c.StartMonth < DateSerial(1900, 1, 1) Or c.StartMonth > DateSerial(Year(today), Month(today), 1) Then Reject "MSG-007", "開始年月"
    If Not IsNull(c.EndMonth) Then
        If Day(c.EndMonth) <> 1 Or c.EndMonth <> DateValue(c.EndMonth) Or c.EndMonth < c.StartMonth Or c.EndMonth > DateSerial(Year(today), Month(today), 1) Then Reject "MSG-007", "終了年月"
    End If
End Sub
Public Sub NormalizeEmployee(ByVal e As clsEmployeeEdit, ByVal today As Date)
    Dim c As clsCareerDraft, previous As clsCareerDraft, i As Long, j As Long
    If Not Digits(e.EmployeeNo, 6) Then Reject "MSG-005", "社員番号"
    CheckText e.Name, 40, True, "氏名": CheckText e.Kana, 80, True, "カナ"
    CheckText e.Summary, 1000, False, "職務要約": CheckText e.Skills, 1000, False, "スキル": CheckText e.Qualifications, 1000, False, "資格": CheckText e.SelfPr, 1000, False, "自己PR"
    e.Name = SaveText(e.Name): e.Kana = SaveText(e.Kana, True): CheckText e.Kana, 80, True, "カナ"
    CheckKana e.Kana
    e.Summary = SaveText(e.Summary): e.Skills = SaveText(e.Skills): e.Qualifications = SaveText(e.Qualifications): e.SelfPr = SaveText(e.SelfPr)
    If Not ValidCode(e.Department) Or Not ValidCode(e.Status) Then Reject "MSG-016"
    If e.JoinDate < DateSerial(1900, 1, 1) Or e.JoinDate > today Or e.JoinDate <> DateValue(e.JoinDate) Then Reject "MSG-005", "入社日"
    If e.Careers.Count > 20 Then Reject "MSG-018"
    On Error GoTo CareerInvalid
    For i = 1 To e.Careers.Count
        Set c = e.Careers(i): NormalizeCareer c, today
        For j = 1 To i - 1
            Set previous = e.Careers(j)
            If CareerSame(c, previous) Then Reject "MSG-026", CStr(i)
        Next
    Next
    Exit Sub
CareerInvalid:
    Dim errorText As String
    errorText = Err.Description
    Err.Raise vbObjectError + 731, "SP2", errorText & "|" & CStr(i)
End Sub
Public Sub CheckStoredAggregate(ByVal e As clsEmployeeEdit)
    Dim normalized As clsEmployeeEdit
    On Error GoTo Invalid
    If IsNull(e.ExpectedRevision) Then GoTo Invalid
    If CLng(e.ExpectedRevision) < 1 Then GoTo Invalid
    Set normalized = CloneEmployee(e)
    NormalizeEmployee normalized, BusinessDate()
    If Not EmployeeSame(normalized, e) Then GoTo Invalid
    Exit Sub
Invalid:
    Reject "MSG-020"
End Sub
Public Function CloneCareer(ByVal c As clsCareerDraft) As clsCareerDraft
    Dim value As New clsCareerDraft
    value.PersistentId = c.PersistentId: value.TemporaryId = c.TemporaryId: value.StartMonth = c.StartMonth: value.EndMonth = c.EndMonth
    value.Company = c.Company: value.Project = c.Project: value.Description = c.Description: value.Duties = c.Duties
    value.Achievements = c.Achievements: value.Technologies = c.Technologies: value.Phases = c.Phases: value.RoleCode = c.RoleCode: value.TeamSize = c.TeamSize
    Set CloneCareer = value
End Function
Public Function CloneEmployee(ByVal e As clsEmployeeEdit) As clsEmployeeEdit
    Dim value As New clsEmployeeEdit, c As clsCareerDraft, id As Variant
    value.EmployeeId = e.EmployeeId: value.ExpectedRevision = e.ExpectedRevision: value.EmployeeNo = e.EmployeeNo
    value.Name = e.Name: value.Kana = e.Kana: value.Department = e.Department: value.Status = e.Status: value.JoinDate = e.JoinDate
    value.Summary = e.Summary: value.Skills = e.Skills: value.Qualifications = e.Qualifications: value.SelfPr = e.SelfPr: value.Outcome = e.Outcome
    For Each c In e.Careers: value.Careers.Add CloneCareer(c): Next
    For Each id In e.LoadedCareerIds: value.LoadedCareerIds.Add CLng(id): Next
    For Each id In e.RemovedCareerIds: value.RemovedCareerIds.Add CLng(id): Next
    If Not e.ActiveDraft Is Nothing Then Set value.ActiveDraft = CloneCareer(e.ActiveDraft)
    Set CloneEmployee = value
End Function
Private Sub CheckOwnership(ByVal e As clsEmployeeEdit, ByVal current As clsEmployeeEdit)
    Dim expected As Object, received As Object, removed As Object, id As Variant, c As clsCareerDraft, key As Variant
    Set expected = CreateObject("Scripting.Dictionary"): Set received = CreateObject("Scripting.Dictionary"): Set removed = CreateObject("Scripting.Dictionary")
    For Each id In e.LoadedCareerIds
        If expected.Exists(CStr(id)) Then Reject "MSG-025"
        expected.Add CStr(id), True
    Next
    If expected.Count <> current.Careers.Count Then Reject "MSG-020"
    For Each c In current.Careers
        If Not expected.Exists(CStr(c.PersistentId)) Then Reject "MSG-020"
    Next
    For Each id In e.RemovedCareerIds
        key = CStr(id)
        If removed.Exists(key) Or Not expected.Exists(key) Then Reject "MSG-025"
        removed.Add key, True
    Next
    For Each c In e.Careers
        If Not IsNull(c.PersistentId) Then
            key = CStr(c.PersistentId)
            If received.Exists(key) Or removed.Exists(key) Or Not expected.Exists(key) Then Reject "MSG-025"
            received.Add key, True
        End If
    Next
    If received.Count + removed.Count <> expected.Count Then Reject "MSG-025"
End Sub
Public Function SaveEmployee(ByVal e As clsEmployeeEdit, ByVal session As clsSession) As clsResult
    Dim u As New clsUnitOfWork, q As DAO.QueryDef, r As DAO.Recordset, current As clsEmployeeEdit, c As clsCareerDraft, old As clsCareerDraft, id As Variant, at As Date, nextVersion As Long, employeeId As Long, description As String, result As clsResult, duplicate As Long
    On Error GoTo Failed
    If session Is Nothing Then Reject "MSG-002"
    If Not session.IsAuthenticated Then Reject "MSG-002"
    Set result = AuthorizeSession(session, "STAFF")
    If result.Kind <> "OK" Then Set SaveEmployee = result: Exit Function
    Set e = CloneEmployee(e)
    NormalizeEmployee e, BusinessDate()
    u.OpenUnit True: RequireCurrent session, "STAFF", u.Db
    If IsNull(e.EmployeeId) Then
        Set current = New clsEmployeeEdit
        If e.LoadedCareerIds.Count <> 0 Or e.RemovedCareerIds.Count <> 0 Then Reject "MSG-025"
        For Each c In e.Careers
            If Not IsNull(c.PersistentId) Then Reject "MSG-025"
        Next
    Else
        Set current = LoadAggregate(u.Db, CLng(e.EmployeeId))
        If Not Same(e.ExpectedRevision, current.ExpectedRevision) Then Reject "MSG-008"
        If e.EmployeeNo <> current.EmployeeNo Then Reject "MSG-025"
        CheckOwnership e, current
        If Not gOriginal Is Nothing Then
            If Same(gOriginal.EmployeeId, current.EmployeeId) And Same(gOriginal.ExpectedRevision, current.ExpectedRevision) Then
                If Not EmployeeSame(current, gOriginal) Then Reject "MSG-020"
            End If
        End If
    End If
    CheckCode u.Db, "DEPARTMENT", e.Department, (Not IsNull(e.EmployeeId) And e.Department = current.Department)
    CheckCode u.Db, "EMPLOYMENT_STATUS", e.Status, (Not IsNull(e.EmployeeId) And e.Status = current.Status)
    For Each c In e.Careers
        Set old = Nothing
        If Not IsNull(c.PersistentId) Then Set old = FindCareer(current.Careers, CLng(c.PersistentId))
        If old Is Nothing Then CheckCode u.Db, "PROJECT_ROLE", c.RoleCode, False Else CheckCode u.Db, "PROJECT_ROLE", c.RoleCode, (old.RoleCode = c.RoleCode)
    Next
    Set q = Query(u.Db, "PARAMETERS n Text(6); SELECT employee_id FROM m_employee WHERE employee_no=n", e.EmployeeNo)
    Set r = ReadOne(q)
    If Not r.EOF Then
        If IsNull(e.EmployeeId) Then Reject "MSG-006"
        If CLng(r!employee_id) <> CLng(e.EmployeeId) Then Reject "MSG-006"
    End If
    r.Close: q.Close
    If IsNull(e.EmployeeId) Then
        If Scalar(u.Db, "SELECT Count(*) FROM m_employee") >= 200 Then Reject "MSG-018"
        nextVersion = 1
    Else
        If EmployeeSame(e, current) Then
            u.Cancel: u.CloseUnit: Set SaveEmployee = MakeResult("NoChange", "MSG-021"): Exit Function
        End If
        If CLng(current.ExpectedRevision) = 2147483647 Then Reject "MSG-039"
        nextVersion = CLng(current.ExpectedRevision) + 1
    End If
    at = UtcNow()
    If IsNull(e.EmployeeId) Then
        Set r = u.Db.OpenRecordset("m_employee", dbOpenDynaset): r.AddNew
    Else
        Set q = Query(u.Db, "PARAMETERS p Long, v Long; SELECT * FROM m_employee WHERE employee_id=p AND revision=v", CLng(e.EmployeeId), CLng(e.ExpectedRevision))
        Set r = ReadOne(q, True): If r.EOF Then Reject "MSG-008"
        r.Edit
    End If
    WriteEmployee r, e, session.UserId, at, nextVersion: r.Update
    r.Bookmark = r.LastModified: employeeId = r!employee_id: r.Close
    If Not q Is Nothing Then q.Close
    For Each id In e.RemovedCareerIds
        Set q = Query(u.Db, "PARAMETERS p Long, c Long; DELETE FROM t_career WHERE employee_id=p AND career_id=c", employeeId, CLng(id))
        q.Execute dbFailOnError: If q.RecordsAffected <> 1 Then Reject "MSG-025"
        q.Close
    Next
    For Each c In e.Careers
        Set old = Nothing
        If Not IsNull(c.PersistentId) Then Set old = FindCareer(current.Careers, CLng(c.PersistentId))
        If old Is Nothing Then
            Set r = u.Db.OpenRecordset("t_career", dbOpenDynaset): r.AddNew
            WriteCareer r, c, employeeId: r.Update: r.Bookmark = r.LastModified
            r.Close
        ElseIf Not CareerSame(c, old) Then
            Set q = Query(u.Db, "PARAMETERS p Long, c Long; SELECT * FROM t_career WHERE employee_id=p AND career_id=c", employeeId, CLng(c.PersistentId))
            Set r = ReadOne(q, True): If r.EOF Then Reject "MSG-025"
            r.Edit: WriteCareer r, c, employeeId: r.Update: r.Close: q.Close
        End If
    Next
    Set current = LoadAggregate(u.Db, employeeId, True)
    If current.Careers.Count <> e.Careers.Count Then Reject "MSG-020"
    u.Commit: u.CloseUnit
    e.EmployeeId = employeeId: e.ExpectedRevision = nextVersion: e.Outcome = "OK"
    Set result = MakeResult("OK", "MSG-014"): Set result.Value = e: Set SaveEmployee = result
    Exit Function
Failed:
    description = Err.Description
    If Err.Number = 3022 Then description = "MSG-006"
    Set SaveEmployee = Failure(description, u)
End Function
