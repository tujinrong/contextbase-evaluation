Option Compare Binary
Option Explicit
Private evidence As String
Private Sub Assert(ByVal id As String, ByVal success As Boolean, Optional ByVal detail As String = "")
    evidence = evidence & id & "|" & IIf(success, "PASS", "FAIL") & IIf(detail <> "", "|" & detail, "") & vbLf
    If Not success Then Err.Raise vbObjectError + 900, , id & IIf(detail <> "", "/" & detail, "")
End Sub
Private Function EmployeeId(ByVal no As String) As Long
    EmployeeId = DLookup("employee_id", "m_employee", "employee_no='" & no & "'")
End Function
Private Function GetEdit(ByVal no As String) As clsEmployeeEdit
    Dim result As clsResult
    Set result = ReadEmployee(EmployeeId(no), gSession)
    Assert "read-aggregate", result.Kind = "OK": Set GetEdit = result.Value
End Function
Private Function Criteria() As clsSearchCriteria
    Dim value As New clsSearchCriteria
    value.EmployeeNo = Null: value.Department = Null: value.Status = "01": value.NameRaw = ""
    Set Criteria = value
End Function
Private Sub ResetControl(ByVal user As String)
    CurrentDb.Execute "UPDATE m_app_user SET failed_count=0, locked_until=Null, is_enabled=True WHERE user_id='" & user & "'", dbFailOnError
End Sub
Public Function RunSuite(ByVal adminPassword As String, ByVal staffPassword As String, ByVal cycle As Long, ByVal reportPath As String) As String
    Dim result As clsResult, nextResult As clsResult, e As clsEmployeeEdit, other As clsEmployeeEdit, c As clsCareerDraft, copy As clsCareerDraft
    Dim criteria_ As clsSearchCriteria, code As clsCodeEdit, u As New clsUnitOfWork, version As Long, at As Date, text As String, i As Long, verifier As String, errorText As String, id As Long, scalar As String
    On Error GoTo Failed
    evidence = ""
    Assert "schema-five-tables", CurrentDb.TableDefs("m_employee").Fields.Count = 16 And CurrentDb.TableDefs("t_career").Fields.Count = 14
    Assert "seed-counts", DCount("*", "m_employee") = 3 And DCount("*", "t_career") = 3 And DCount("*", "m_code") = 9 And DCount("*", "m_app_user") = 2
    scalar = ChrW(&HD83D) & ChrW(&HDE00)
    Assert "unicode-scalar", ScalarLength(scalar & "a") = 2
    verifier = NewVerifier("vector test " & scalar & "  ")
    Assert "cng-correct", VerifyPassword("vector test " & scalar & "  ", verifier)
    Assert "cng-original-spaces", Not VerifyPassword("vector test " & scalar, verifier)
    Assert "cng-unknown-version", Not VerifyPassword("vector test " & scalar & "  ", Replace(verifier, "$v=1$", "$v=2$"))
    Set result = Authenticate("  STAFF  ", staffPassword)
    Assert "auth-result-object", Not result Is Nothing
    Assert "auth-session-object", Not gSession Is Nothing
    Assert "API-login-staff", result.Kind = "OK" And gSession.RoleId = "STAFF"
    Set result = Authorize("ADMIN"): Assert "API-role-admin-reject", result.MessageId = "MSG-003"
    Set code = New clsCodeEdit: code.CategoryId = "DEPARTMENT": code.Code = "04": code.Name = "権限拒否試験": code.SortOrder = 4
    Set result = SaveCode(code, gSession): Assert "API-staff-code-write-denied", result.MessageId = "MSG-003" And DCount("*", "m_code") = 9
    gSession.LastActivityTick = GetTickCount64() - 1800000
    Assert "API-idle-no-revive", Not TouchActivity() And Not gSession.IsAuthenticated
    ResetControl "SP2STAFF"
    For i = 1 To 5
        Set result = Authenticate("staff", "wrong isolated test password")
        Assert "lock-failure-" & CStr(i), result.MessageId = "MSG-001" And DLookup("failed_count", "m_app_user", "user_id='SP2STAFF'") = i
    Next
    at = DLookup("locked_until", "m_app_user", "user_id='SP2STAFF'")
    Set result = Authenticate("staff", staffPassword)
    Assert "API-locked-no-extend", result.MessageId = "MSG-001" And DLookup("locked_until", "m_app_user", "user_id='SP2STAFF'") = at And DLookup("failed_count", "m_app_user", "user_id='SP2STAFF'") = 5
    CurrentDb.Execute "UPDATE m_app_user SET locked_until=DateAdd('n',-1,Now()) WHERE user_id='SP2STAFF'", dbFailOnError
    ' Use UTC directly (host locale Now is deliberately not the application clock).
    Set u = New clsUnitOfWork: u.OpenUnit True
    u.Db.OpenRecordset("SELECT * FROM m_app_user WHERE user_id='SP2STAFF'", dbOpenDynaset).Close
    Dim q As DAO.QueryDef
    Set q = Query(u.Db, "PARAMETERS p DateTime; UPDATE m_app_user SET locked_until=p WHERE user_id='SP2STAFF'", DateAdd("s", -1, UtcNow()))
    q.Execute dbFailOnError: q.Close: u.Commit: u.CloseUnit
    Set result = Authenticate("staff", staffPassword)
    Assert "API-lock-elapsed-reset", result.Kind = "OK" And DLookup("failed_count", "m_app_user", "user_id='SP2STAFF'") = 0 And IsNull(DLookup("locked_until", "m_app_user", "user_id='SP2STAFF'"))
    Set criteria_ = Criteria(): Set result = SearchEmployees(criteria_, gSession)
    Assert "API-initial-search", result.Kind = "OK" And result.Value.Count = 2
    criteria_.EmployeeNo = "000001": criteria_.NameRaw = "ﾔﾏﾀﾞ ﾀﾛｳ": criteria_.Department = "01"
    Assert "nfkc-kana-equivalence", Same(NameKey(criteria_.NameRaw), NameKey("ヤマダ タロウ"))
    Set result = SearchEmployees(criteria_, gSession)
    Assert "P10-kind-" & result.Kind & "-" & result.MessageId, result.Kind = "OK"
    Assert "API-kana-and-filter", result.Value.Count = 1
    criteria_.NameRaw = "[?*%_": Set result = SearchEmployees(criteria_, gSession)
    Assert "literal-wildcard", result.Kind = "OK" And result.Value.Count = 0
    criteria_.EmployeeNo = "1": Set result = SearchEmployees(criteria_, gSession): Assert "search-number-format", result.MessageId = "MSG-005"
    Set e = GetEdit("000001"): version = e.ExpectedRevision: at = DLookup("updated_at", "m_employee", "employee_id=" & e.EmployeeId)
    Set result = SaveEmployee(e, gSession)
    Assert "API-employee-nochange-audit", result.Kind = "NoChange" And DLookup("revision", "m_employee", "employee_id=" & e.EmployeeId) = version And DLookup("updated_at", "m_employee", "employee_id=" & e.EmployeeId) = at
    Set other = CloneEmployee(e): e.Careers(1).Duties = e.Careers(1).Duties & "追加"
    Set result = SaveEmployee(e, gSession): Assert "API-child-only-parent-version", result.Kind = "OK" And DLookup("revision", "m_employee", "employee_id=" & e.EmployeeId) = version + 1
    Set result = SaveEmployee(other, gSession): Assert "API-stale-nochange-conflict", result.MessageId = "MSG-008"
    Set e = GetEdit("000001"): Set copy = CloneCareer(e.Careers(1)): copy.PersistentId = Null: e.Careers.Add copy
    Set result = SaveEmployee(e, gSession): Assert "API-duplicate-eleven-values", result.MessageId = "MSG-026"
    Set e = GetEdit("000001"): Set c = e.Careers(1): e.RemovedCareerIds.Add CLng(c.PersistentId): e.Careers.Remove 1
    Set result = SaveEmployee(e, gSession): Assert "explicit-remove", result.Kind = "OK" And DCount("*", "t_career", "employee_id=" & e.EmployeeId) = 1
    Set e = New clsEmployeeEdit: e.EmployeeNo = "000004": e.Name = "架空 追加": e.Kana = "ｶｸｳ ﾂｲｶ": e.Department = "01": e.Status = "01": e.JoinDate = BusinessDate()
    e.Summary = String$(998, "あ") & scalar
    Set result = SaveEmployee(e, gSession): Assert "new-employee-longtext", result.Kind = "OK"
    Set e = result.Value: Set nextResult = ReadEmployee(CLng(e.EmployeeId), gSession): Set other = nextResult.Value
    Assert "unicode-longtext-readback", Same(e.Summary, other.Summary) And ScalarLength(other.Summary) = 999 And other.Kana = "カクウ ツイカ"
    Set result = ReadReport(CLng(e.EmployeeId), gSession): Assert "API-zero-career-report-reject", result.MessageId = "MSG-012"
    other.Name = "修正": other.Kana = "abc": Set result = SaveEmployee(other, gSession): Assert "kana-allowlist", result.MessageId = "MSG-005" And other.Kana = "abc"
    Set other = CloneEmployee(e): other.EmployeeId = Null: other.ExpectedRevision = Null
    Set result = SaveEmployee(other, gSession): Assert "API-employee-number-duplicate-sequential", result.MessageId = "MSG-006"
    Set result = Authenticate("admin", adminPassword): Assert "admin-login", result.Kind = "OK"
    Set code = New clsCodeEdit: code.CategoryId = "DEPARTMENT": code.Code = "04": code.Name = "架空部署": code.SortOrder = 4
    Set result = SaveCode(code, gSession): Assert "code-add", result.Kind = "OK"
    version = code.ExpectedRevision: Set result = SaveCode(code, gSession): Assert "API-code-nochange-audit", result.Kind = "NoChange" And code.ExpectedRevision = version
    code.IsEnabled = False: Set result = SaveCode(code, gSession): Assert "code-stop", result.Kind = "OK"
    Set code = New clsCodeEdit: code.CategoryId = "EMPLOYMENT_STATUS": code.Code = "04": code.Name = "禁止": code.SortOrder = 4
    Set result = SaveCode(code, gSession): Assert "API-fixed-status-reject", result.MessageId = "MSG-023"
    Set e = GetEdit("000001")
    Set result = ExportCareer(CLng(e.EmployeeId), gSession, reportPath)
    Assert "excel-two-sheet-roundtrip", result.Kind = "OK"
    If cycle >= 2 Then BoundarySuite adminPassword, staffPassword, reportPath
    RunSuite = evidence: Exit Function
Failed:
    RunSuite = evidence & "suite-error|FAIL|" & Left$(Err.Description, 80)
End Function
Private Sub BoundarySuite(ByVal adminPassword As String, ByVal staffPassword As String, ByVal reportPath As String)
    Dim e As clsEmployeeEdit, other As clsEmployeeEdit, c As clsCareerDraft, result As clsResult, id As Long, count As Long, i As Long
    Set e = GetEdit("000002"): Set other = CloneEmployee(e)
    Set c = New clsCareerDraft: c.StartMonth = DateSerial(2024, 4, 1): c.EndMonth = c.StartMonth: c.Company = "架空会社": c.Project = "並行案件": c.Description = "概要": c.Duties = "担当": c.RoleCode = "01": c.TeamSize = 1
    e.Careers.Add c: Set result = SaveEmployee(e, gSession): Assert "API-parallel-period-permitted", result.Kind = "OK"
    Set e = GetEdit("000002"): Set c = CloneCareer(e.Careers(1)): c.PersistentId = Null: c.Project = "異なる案件"
    For i = e.Careers.Count + 1 To 20
        Set c = CloneCareer(c): c.Project = "架空案件" & CStr(i): e.Careers.Add c
    Next
    Set result = SaveEmployee(e, gSession): Assert "API-careers-twenty", result.Kind = "OK"
    Set e = GetEdit("000002"): Set c = CloneCareer(e.Careers(1)): c.PersistentId = Null: c.Project = "21件目": e.Careers.Add c
    Set result = SaveEmployee(e, gSession): Assert "API-careers-twentyone-reject", result.MessageId = "MSG-018"
    Set e = GetEdit("000002"): e.Careers.Remove 1
    Set result = SaveEmployee(e, gSession): Assert "API-career-omission-reject", result.MessageId = "MSG-025"
    Set e = GetEdit("000002"): e.RemovedCareerIds.Add CLng(e.Careers(1).PersistentId)
    Set result = SaveEmployee(e, gSession): Assert "API-career-retain-remove-reject", result.MessageId = "MSG-025"
    Set e = GetEdit("000002"): e.Careers(1).PersistentId = DLookup("career_id", "t_career", "employee_id=" & EmployeeId("000001"))
    Set result = SaveEmployee(e, gSession): Assert "API-career-other-owner-reject", result.MessageId = "MSG-025"
    Set e = GetEdit("000002")
    Dim prefixes As Variant, prefix As String, index As Long
    prefixes = Array("'ABC", "''ABC", "'=1+1", "_x0041_", "=1+1", "+1", "@NAME", "-1", "元" & vbLf & "改行", "e" & ChrW(&H301), ChrW(&HD83D) & ChrW(&HDE00))
    e.Summary = String$(1000, "要"): e.Skills = String$(1000, "技"): e.Qualifications = String$(1000, "資"): e.SelfPr = String$(1000, "自")
    e.Name = String$(40, "界"): e.Kana = String$(80, "カ")
    For index = 1 To e.Careers.Count
        Set c = e.Careers(index): prefix = prefixes((index - 1) Mod (UBound(prefixes) + 1))
        c.Company = String$(100, "会"): c.Project = Format$(index, "00") & String$(98, "案")
        c.Description = prefix & String$(1000 - ScalarLength(prefix), "概")
        c.Duties = String$(1000, "担"): c.Achievements = String$(1000, "果"): c.Technologies = String$(500, "技"): c.Phases = String$(200, "工")
    Next
    Set result = SaveEmployee(e, gSession): Assert "API-twenty-maxlong-save", result.Kind = "OK"
    Set result = ExportCareer(CLng(e.EmployeeId), gSession, Replace(reportPath, ".xlsx", "-long.xlsx"))
    Assert "API-twenty-maxlong-excel-roundtrip", result.Kind = "OK", result.Kind & "/" & result.MessageId
    id = EmployeeId("000004")
    CurrentDb.Execute "UPDATE m_employee SET revision=2147483647 WHERE employee_id=" & CStr(id), dbFailOnError
    Set e = GetEdit("000004"): Set result = SaveEmployee(e, gSession): Assert "API-max-revision-nochange", result.Kind = "NoChange"
    e.Name = "版上限変更": Set result = SaveEmployee(e, gSession): Assert "API-max-revision-change-reject", result.MessageId = "MSG-039"
    Set result = Authenticate("staff", staffPassword): Assert "staff-relogin", result.Kind = "OK"
    CurrentDb.Execute "UPDATE m_app_user SET is_enabled=False WHERE user_id='SP2STAFF'", dbFailOnError
    Set result = Authorize("STAFF"): Assert "API-stopped-current-user", result.MessageId = "MSG-002"
    ResetControl "SP2STAFF"
End Sub
