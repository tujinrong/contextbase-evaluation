Option Compare Binary
Option Explicit
Public Function SearchEmployees(ByVal criteria As clsSearchCriteria, ByVal session As clsSession) As clsResult
    Dim u As New clsUnitOfWork, q As DAO.QueryDef, r As DAO.Recordset, rows As New Collection, row As Variant, key As String, result As clsResult, text As String
    On Error GoTo Failed
    u.OpenUnit True: RequireCurrent session, "STAFF", u.Db
    If Not IsNull(criteria.EmployeeNo) Then
        If Not Digits(CStr(criteria.EmployeeNo), 6) Then Reject "MSG-005", "社員番号"
    End If
    CheckText criteria.NameRaw, 40, False, "氏名・カナ"
    key = NameKey(criteria.NameRaw): If ScalarLength(key) > 40 Then Reject "MSG-005", "氏名・カナ"
    If Not IsNull(criteria.Department) Then CheckCode u.Db, "DEPARTMENT", CStr(criteria.Department), True
    If Not IsNull(criteria.Status) Then CheckCode u.Db, "EMPLOYMENT_STATUS", CStr(criteria.Status), True
    Set q = Query(u.Db, "PARAMETERS n Text(6), d Text(2), s Text(2); SELECT * FROM m_employee WHERE (n Is Null OR employee_no=n) AND (d Is Null OR department_code=d) AND (s Is Null OR employment_status=s) ORDER BY employee_no", criteria.EmployeeNo, criteria.Department, criteria.Status)
    Set r = q.OpenRecordset(dbOpenSnapshot)
    Do While Not r.EOF
        If key = "" Or InStr(1, NameKey(CStr(r!employee_name)), key, vbBinaryCompare) > 0 Or InStr(1, NameKey(CStr(r!employee_kana)), key, vbBinaryCompare) > 0 Then
            CheckCode u.Db, "DEPARTMENT", CStr(r!department_code), True, True
            CheckCode u.Db, "EMPLOYMENT_STATUS", CStr(r!employment_status), True, True
            rows.Add Array(CLng(r!employee_id), CStr(r!employee_no), CStr(r!employee_name), CStr(r!employee_kana), CodeName(u.Db, "DEPARTMENT", CStr(r!department_code)), CodeName(u.Db, "EMPLOYMENT_STATUS", CStr(r!employment_status)), Format$(r!join_date, "yyyy-mm-dd"))
            If rows.Count > 200 Then Reject "MSG-010"
        End If
        r.MoveNext
    Loop
    r.Close: q.Close: u.Commit: u.CloseUnit
    Set result = MakeResult("OK", IIf(rows.Count = 0, "MSG-009", "")): Set result.Value = rows: Set SearchEmployees = result: Exit Function
Failed:
    text = Err.Description: Set SearchEmployees = Failure(text, u, True)
End Function
Public Function CodeName(ByVal db As DAO.Database, ByVal category As String, ByVal code As String) As String
    Dim q As DAO.QueryDef, r As DAO.Recordset
    Set q = Query(db, "PARAMETERS a Text(24), b Text(2); SELECT code_name FROM m_code WHERE category_id=a AND code=b", category, code)
    Set r = ReadOne(q): If r.EOF Then Reject "MSG-020"
    CodeName = r!code_name: r.Close: q.Close
End Function
Public Function ReadEmployee(ByVal id As Long, ByVal session As clsSession) As clsResult
    Dim u As New clsUnitOfWork, result As clsResult, e As clsEmployeeEdit, text As String
    On Error GoTo Failed
    u.OpenUnit True: RequireCurrent session, "STAFF", u.Db
    Set e = LoadAggregate(u.Db, id): u.Commit: u.CloseUnit
    Set result = MakeResult("OK"): Set result.Value = e: Set ReadEmployee = result: Exit Function
Failed:
    text = Err.Description: Set ReadEmployee = Failure(text, u, True)
End Function
