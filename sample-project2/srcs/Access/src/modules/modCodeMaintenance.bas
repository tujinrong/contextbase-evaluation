Option Compare Binary
Option Explicit
Public Function ReadCodes(ByVal category As String, ByVal session As clsSession) As clsResult
    Dim u As New clsUnitOfWork, q As DAO.QueryDef, r As DAO.Recordset, rows As New Collection, result As clsResult, text As String
    On Error GoTo Failed
    u.OpenUnit True: RequireCurrent session, "ADMIN", u.Db
    If category <> "DEPARTMENT" And category <> "EMPLOYMENT_STATUS" And category <> "PROJECT_ROLE" Then Reject "MSG-016"
    Set q = Query(u.Db, "PARAMETERS p Text(24); SELECT * FROM m_code WHERE category_id=p ORDER BY sort_order, code", category)
    Set r = q.OpenRecordset(dbOpenSnapshot)
    Do While Not r.EOF
        rows.Add Array(CStr(r!code), CStr(r!code_name), CInt(r!sort_order), CBool(r!is_enabled), CLng(r!revision))
        If rows.Count > 99 Then Reject "MSG-020"
        r.MoveNext
    Loop
    r.Close: q.Close: u.Commit: u.CloseUnit
    Set result = MakeResult("OK"): Set result.Value = rows: Set ReadCodes = result: Exit Function
Failed:
    text = Err.Description: Set ReadCodes = Failure(text, u, True)
End Function
Public Function SaveCode(ByVal edit As clsCodeEdit, ByVal session As clsSession) As clsResult
    Dim u As New clsUnitOfWork, q As DAO.QueryDef, r As DAO.Recordset, version As Long, text As String
    On Error GoTo Failed
    u.OpenUnit True: RequireCurrent session, "ADMIN", u.Db
    If edit.CategoryId = "EMPLOYMENT_STATUS" Then Reject "MSG-023"
    If edit.CategoryId <> "DEPARTMENT" And edit.CategoryId <> "PROJECT_ROLE" Then Reject "MSG-016"
    If Not ValidCode(edit.Code) Then Reject "MSG-005", "コード"
    CheckText edit.Name, 40, True, "名称": edit.Name = SaveText(edit.Name)
    If edit.SortOrder < 1 Or edit.SortOrder > 999 Then Reject "MSG-005", "表示順"
    Set q = Query(u.Db, "PARAMETERS a Text(24), b Text(2); SELECT * FROM m_code WHERE category_id=a AND code=b", edit.CategoryId, edit.Code)
    Set r = ReadOne(q, True)
    If edit.IsNew Then
        If Not r.EOF Then Reject "MSG-022"
        r.Close: q.Close
        Set q = Query(u.Db, "PARAMETERS a Text(24); SELECT Count(*) AS n FROM m_code WHERE category_id=a", edit.CategoryId)
        Set r = q.OpenRecordset(dbOpenSnapshot): If r!n >= 99 Then Reject "MSG-024"
        r.Close: q.Close
        Set r = u.Db.OpenRecordset("m_code", dbOpenDynaset): r.AddNew
        r!category_id = edit.CategoryId: r!code = edit.Code: version = 1
    Else
        If r.EOF Then Reject "MSG-020"
        If Not Same(edit.ExpectedRevision, r!revision) Then Reject "MSG-008"
        If Same(edit.Name, r!code_name) And Same(edit.SortOrder, r!sort_order) And Same(edit.IsEnabled, r!is_enabled) Then
            r.Close: q.Close: u.Cancel: u.CloseUnit: Set SaveCode = MakeResult("NoChange", "MSG-021"): Exit Function
        End If
        If CLng(r!revision) = 2147483647 Then Reject "MSG-039"
        version = CLng(r!revision) + 1: r.Edit
    End If
    r!code_name = edit.Name: r!sort_order = edit.SortOrder: r!is_enabled = edit.IsEnabled
    r!updated_at = UtcNow(): r!updated_by = session.UserId: r!revision = version: r.Update
    r.Close: If Not q Is Nothing Then q.Close
    u.Commit: u.CloseUnit
    edit.ExpectedRevision = version: edit.IsNew = False
    Set SaveCode = MakeResult("OK", "MSG-014"): Exit Function
Failed:
    text = Err.Description: If Err.Number = 3022 Then text = "MSG-022"
    Set SaveCode = Failure(text, u)
End Function
