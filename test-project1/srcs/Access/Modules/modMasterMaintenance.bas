Attribute VB_Name = "modMasterMaintenance"
Option Explicit
Option Compare Binary

' Administrative entry points only; normal student forms do not expose these operations.
Public Function MaintainClass(ByVal raw As Object, ByVal target As Variant, ByVal expected As Variant) As Object
    Dim tx As New clsUnitOfWork, repo As New clsStudentRepository, rs As DAO.Recordset, old As Object, d As Object, result As Object
    Dim id As Long, version As Long, utc As Date, user As String, day As String, k As Variant, changed As String, before As Variant, refs As Long, seats As Long
    Set result = Map(): Set MaintainClass = result
    On Error GoTo Failed
    Authorize "Master": utc = UtcNow(): day = BusinessDay(utc): user = CurrentUserId(): Set d = Map()
    d.Add "school_year", PositiveId(NFKC(CStr(raw("school_year"))))
    If d("school_year") < 1900 Or d("school_year") > 9998 Then Err.Raise vbObjectError + 140, , "E-DATE-003"
    d.Add "grade_category", "GRADE": d.Add "grade_code", TextValue(raw("grade_code"), 2, 2, "code")
    d.Add "class_code", TextValue(raw("class_code"), 9, 9, "number")
    d.Add "class_name", TextValue(raw("class_name"), 18, 18, "text")
    d.Add "valid_from", StrictIso(raw("valid_from"), True): d.Add "valid_to", StrictIso(raw("valid_to"), True)
    d.Add "capacity", Null
    If Nz(raw("capacity"), "") <> "" Then d("capacity") = PositiveId(raw("capacity"))
    If Not IsNull(d("capacity")) Then If d("capacity") > 9999 Then Err.Raise vbObjectError + 140, , "E-MST-004"
    d.Add "display_order", NonnegativeInteger(raw("display_order"))
    d.Add "is_active", CBool(raw("is_active")): d.Add "remarks", TextValue(raw("remarks"), 120, 120, "memo")
    If IsNull(d("class_code")) Or IsNull(d("class_name")) Or IsNull(d("grade_code")) Then Err.Raise vbObjectError + 140, , "E-STU-001"
    If Not Match(d("class_code"), "^[A-Z0-9][A-Z0-9-]{0,8}$") Then Err.Raise vbObjectError + 140, , "E-MST-002"
    If d("valid_from") < CStr(d("school_year")) & "-04-01" Or d("valid_to") > CStr(d("school_year") + 1) & "-03-31" Or d("valid_from") > d("valid_to") Then Err.Raise vbObjectError + 140, , "E-MST-004"
    If Not IsNull(target) Then id = PositiveId(target): expected = PositiveId(expected)
    tx.BeginWork: Set repo.Database = tx.Database
    If id <> 0 Then
        Set old = repo.ClassById(id)
        If old Is Nothing Then Err.Raise vbObjectError + 140, , "E-STU-010"
        If old("row_version") <> expected Then Err.Raise vbObjectError + 140, , "E-STU-105"
        If old("school_year") <> d("school_year") Or old("class_code") <> d("class_code") Then Err.Raise vbObjectError + 140, , "E-MST-003"
        Set rs = repo.Query("pId LONG", "SELECT Count(*) AS n FROM m_student WHERE class_id=pId", Array(id)): refs = rs!n: rs.Close
        seats = repo.Occupancy(id, 0)
        If refs > 0 And old("grade_code") <> d("grade_code") Then Err.Raise vbObjectError + 140, , "E-MST-003"
        If seats > 0 And Not d("is_active") Then Err.Raise vbObjectError + 140, , "E-MST-004"
        If Not IsNull(d("capacity")) Then If d("capacity") < seats Then Err.Raise vbObjectError + 140, , "E-MST-004"
        If seats > 0 And (day < d("valid_from") Or day > d("valid_to")) Then Err.Raise vbObjectError + 140, , "E-MST-004"
    End If
    repo.CheckCode "GRADE", d("grade_code"), IIf(old Is Nothing, Null, ValueOrNull(old, "grade_code")), day
    Set rs = repo.Query("pYear LONG,pCode TEXT(18),pId LONG", "SELECT class_id FROM m_class WHERE school_year=pYear AND class_code=pCode AND class_id<>pId", Array(d("school_year"), d("class_code"), id))
    If Not rs.EOF Then rs.Close: Err.Raise vbObjectError + 140, , "E-MST-002"
    rs.Close
    Set rs = repo.Query("pId LONG,pYear LONG,pGrade TEXT(4),pName TEXT(36)", "SELECT class_id FROM m_class WHERE class_id<>pId AND school_year=pYear AND grade_code=pGrade AND class_name=pName", Array(id, d("school_year"), d("grade_code"), d("class_name")))
    If Not rs.EOF Then result.Add "warning", "W-MST-001"
    rs.Close
    id = WriteMaster(repo.Database, "m_class", "class_id", id, old, d, utc, user, version, changed, before)
    If changed = "" Then tx.CloseWork: result.Add "kind", "NoChange": Exit Function
    MasterAudit repo.Database, "m_class", CStr(id), before, version, changed, utc, user
    tx.Commit: tx.CloseWork: result.Add "kind", "Saved": result.Add "class_id", id: result.Add "row_version", version
    Exit Function
Failed:
    MasterFailure tx, result, Err.Description
End Function

Public Function MaintainCode(ByVal category As String, ByVal code As String, ByVal raw As Object, ByVal expected As Variant) As Object
    Dim tx As New clsUnitOfWork, repo As New clsStudentRepository, rs As DAO.Recordset, cat As Object, old As Object, d As Object, result As Object
    Dim utc As Date, user As String, day As String, before As Variant, version As Long, changed As String, k As Variant, same As Boolean
    Set result = Map(): Set MaintainCode = result
    On Error GoTo Failed
    Authorize "Master": utc = UtcNow(): day = BusinessDay(utc): user = CurrentUserId()
    category = Nz(TextValue(category, 24, 24, "code"), ""): code = Nz(TextValue(code, 10, 10, "code"), "")
    Set d = Map(): d.Add "code_name", TextValue(raw("code_name"), 12, 12, "text")
    d.Add "display_order", NonnegativeInteger(raw("display_order")): d.Add "is_active", CBool(raw("is_active"))
    d.Add "valid_from", StrictIso(raw("valid_from"), True): d.Add "valid_to", StrictIso(raw("valid_to"), False)
    d.Add "remarks", TextValue(raw("remarks"), 120, 120, "memo")
    If IsNull(d("code_name")) Or d("valid_from") < "1900-01-01" Then Err.Raise vbObjectError + 141, , "E-STU-001"
    If Not IsNull(d("valid_to")) Then If d("valid_to") < d("valid_from") Then Err.Raise vbObjectError + 141, , "E-MST-004"
    tx.BeginWork: Set repo.Database = tx.Database
    Set rs = repo.Query("pCat TEXT(48)", "SELECT * FROM m_code_category WHERE category_id=pCat", Array(category))
    If rs.EOF Then rs.Close: Err.Raise vbObjectError + 141, , "E-MST-001"
    Set cat = repo.RowMap(rs): rs.Close
    If Len(code) <> cat("code_length") Or Not Match(code, "^[A-Z0-9-]+$") Then Err.Raise vbObjectError + 141, , "E-STU-009"
    Set rs = repo.Query("pCat TEXT(48),pCode TEXT(20)", "SELECT * FROM m_code WHERE category_id=pCat AND code_value=pCode", Array(category, code))
    If Not rs.EOF Then Set old = repo.RowMap(rs)
    rs.Close
    If old Is Nothing Then
        If Not IsNull(expected) Or Not cat("allow_add") Then Err.Raise vbObjectError + 141, , "E-MST-003"
        version = 1: before = Null
        Set rs = repo.Database.OpenRecordset("m_code", dbOpenDynaset): rs.AddNew
        rs!category_id = category: rs!code_value = code: rs!is_protected = False: rs!created_at = utc: rs!created_by = user
    Else
        If IsNull(expected) Then Err.Raise vbObjectError + 141, , "E-MST-002"
        If old("row_version") <> PositiveId(expected) Then Err.Raise vbObjectError + 141, , "E-STU-105"
        If old("is_protected") Then
            If Not d("is_active") Or Not IsNull(d("valid_to")) Or d("valid_from") > old("valid_from") Then Err.Raise vbObjectError + 141, , "E-MST-003"
        End If
        same = True
        For Each k In d.Keys: If Not EqualValue(d(k), old(k)) Then same = False
        Next
        If same Then tx.CloseWork: result.Add "kind", "NoChange": Exit Function
        before = old("row_version")
        If before = 2147483647 Then Err.Raise vbObjectError + 141, , "E-COM-004"
        version = before + 1
        Set rs = repo.Database.OpenRecordset("SELECT * FROM m_code", dbOpenDynaset)
        rs.FindFirst "category_id='" & Replace(category, "'", "''") & "' AND code_value='" & Replace(code, "'", "''") & "'"
        If rs.NoMatch Then Err.Raise vbObjectError + 141, , "E-MST-001"
        rs.Edit
    End If
    changed = "["
    For Each k In d.Keys
        rs.Fields(k).Value = d(k)
        If old Is Nothing Then
            changed = changed & """" & k & ""","
        ElseIf Not EqualValue(d(k), old(k)) Then
            changed = changed & """" & k & ""","
        End If
    Next
    changed = changed & """row_version"",""updated_at"",""updated_by""]"
    rs!row_version = version: rs!updated_at = utc: rs!updated_by = user: rs.Update: rs.Close
    MasterAudit repo.Database, "m_code", category & ":" & code, before, version, changed, utc, user
    tx.Commit: tx.CloseWork: result.Add "kind", "Saved": result.Add "row_version", version
    Exit Function
Failed:
    MasterFailure tx, result, Err.Description
End Function
Private Function NonnegativeInteger(ByVal raw As Variant) As Long
    Dim s As String
    s = NFKC(Nz(raw, "0"))
    If Not Match(s, "^[0-9]{1,10}$") Then Err.Raise vbObjectError + 142, , "E-COM-003"
    If CDec(s) > 2147483647@ Then Err.Raise vbObjectError + 142, , "E-COM-003"
    NonnegativeInteger = CLng(s)
End Function
Private Function ValueOrNull(ByVal d As Object, ByVal key As String) As Variant
    ValueOrNull = Null
    If Not d Is Nothing Then ValueOrNull = d(key)
End Function
Private Function WriteMaster(ByVal db As DAO.Database, ByVal table As String, ByVal idColumn As String, ByVal id As Long, ByVal old As Object, ByVal d As Object, ByVal utc As Date, ByVal user As String, ByRef version As Long, ByRef changed As String, ByRef before As Variant) As Long
    Dim rs As DAO.Recordset, k As Variant, same As Boolean
    If Not old Is Nothing Then
        same = True
        For Each k In d.Keys: If Not EqualValue(d(k), old(k)) Then same = False
        Next
        If same Then changed = "": WriteMaster = id: Exit Function
        before = old("row_version")
        If before = 2147483647 Then Err.Raise vbObjectError + 142, , "E-COM-004"
        version = before + 1
        Set rs = db.OpenRecordset("SELECT * FROM " & table & " WHERE " & idColumn & "=" & CStr(id), dbOpenDynaset): rs.Edit
    Else
        version = 1: before = Null: Set rs = db.OpenRecordset(table, dbOpenDynaset): rs.AddNew
        rs!created_at = utc: rs!created_by = user
    End If
    changed = "["
    For Each k In d.Keys
        rs.Fields(k).Value = d(k)
        If old Is Nothing Then
            changed = changed & """" & k & ""","
        ElseIf Not EqualValue(d(k), old(k)) Then
            changed = changed & """" & k & ""","
        End If
    Next
    changed = changed & """row_version"",""updated_at"",""updated_by""]"
    rs!row_version = version: rs!updated_at = utc: rs!updated_by = user: rs.Update: rs.Bookmark = rs.LastModified
    WriteMaster = rs.Fields(idColumn): rs.Close
End Function
Private Sub MasterAudit(ByVal db As DAO.Database, ByVal table As String, ByVal key As String, ByVal before As Variant, ByVal after As Long, ByVal changed As String, ByVal utc As Date, ByVal user As String)
    Dim rs As DAO.Recordset
    Set rs = db.OpenRecordset("t_operation_log", dbOpenDynaset): rs.AddNew
    rs!target_table = table: rs!target_key = key: rs!operation_type = IIf(IsNull(before), "CREATE", "UPDATE")
    rs!before_version = before: rs!after_version = after: rs!changed_columns = changed
    rs!executed_at = utc: rs!executed_by = user: rs!correlation_id = GuidText(): rs!duplicate_confirmed = False
    rs.Update: rs.Close
End Sub
Private Sub MasterFailure(ByVal tx As clsUnitOfWork, ByVal result As Object, ByVal message As String)
    Dim unknown As Boolean
    unknown = tx.CommitStarted
    On Error Resume Next: tx.CloseWork: On Error GoTo 0
    result.Add "kind", IIf(unknown, "Unknown", "ValidationFailed")
    If Left$(message, 2) <> "E-" Then message = "E-COM-004"
    result.Add "message", message
End Sub
