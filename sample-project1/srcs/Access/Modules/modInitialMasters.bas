Attribute VB_Name = "modInitialMasters"
Option Explicit
Option Compare Binary

' Administrative approved-seed entry. Reapplication never silently changes a difference.
Public Function ReapplyInitialMasters() As Object
    Dim tx As New clsUnitOfWork, repo As New clsStudentRepository, result As Object, rs As DAO.Recordset
    Dim category As Variant, code As Variant, categoryCount As Long, codeCount As Long, isInitialEmpty As Boolean, utc As Date, user As String
    Set result = Map(): Set ReapplyInitialMasters = result
    On Error GoTo Failed
    Authorize "Master": utc = UtcNow(): user = CurrentUserId()
    tx.BeginWork: Set repo.Database = tx.Database
    Set rs = tx.Database.OpenRecordset("SELECT Count(*) AS n FROM m_code_category"): categoryCount = rs!n: rs.Close
    Set rs = tx.Database.OpenRecordset("SELECT Count(*) AS n FROM m_code"): codeCount = rs!n: rs.Close
    isInitialEmpty = categoryCount = 0 And codeCount = 0
    If Not isInitialEmpty And (categoryCount <> 5 Or codeCount <> 70) Then Err.Raise vbObjectError + 143, , "E-MST-001"
    For Each category In ApprovedCategories()
        If isInitialEmpty Then
            Set rs = tx.Database.OpenRecordset("m_code_category", dbOpenDynaset): rs.AddNew
            rs!category_id = category(0): rs!category_name = category(1): rs!code_length = category(2): rs!allow_add = category(3)
            rs!is_active = True: rs!remarks = Null: rs!row_version = 1
            rs!created_at = utc: rs!created_by = user: rs!updated_at = utc: rs!updated_by = user: rs.Update
        Else
            Set rs = repo.Query("pCat TEXT(48)", "SELECT * FROM m_code_category WHERE category_id=pCat", Array(category(0)))
            If rs.EOF Then Err.Raise vbObjectError + 143, , "E-MST-001"
            If Not EqualValue(rs!category_name, category(1)) Or rs!code_length <> category(2) Or rs!allow_add <> category(3) Or Not rs!is_active Or Not IsNull(rs!remarks) Then Err.Raise vbObjectError + 143, , "E-MST-001"
        End If
        rs.Close
    Next
    For Each code In ApprovedCodes()
        If isInitialEmpty Then
            Set rs = tx.Database.OpenRecordset("m_code", dbOpenDynaset): rs.AddNew
            rs!category_id = code(0): rs!code_value = code(1): rs!code_name = code(2): rs!display_order = code(3)
            rs!is_active = True: rs!valid_from = "1900-01-01": rs!valid_to = Null: rs!is_protected = code(4): rs!remarks = Null
            rs!row_version = 1: rs!created_at = utc: rs!created_by = user: rs!updated_at = utc: rs!updated_by = user: rs.Update
        Else
            Set rs = repo.Query("pCat TEXT(48),pCode TEXT(20)", "SELECT * FROM m_code WHERE category_id=pCat AND code_value=pCode", Array(code(0), code(1)))
            If rs.EOF Then Err.Raise vbObjectError + 143, , "E-MST-001"
            If Not EqualValue(rs!code_name, code(2)) Or rs!display_order <> code(3) Or Not rs!is_active Or rs!valid_from <> "1900-01-01" Or Not IsNull(rs!valid_to) Or rs!is_protected <> code(4) Or Not IsNull(rs!remarks) Then Err.Raise vbObjectError + 143, , "E-MST-001"
        End If
        rs.Close
    Next
    If isInitialEmpty Then tx.Commit
    tx.CloseWork: result.Add "kind", IIf(isInitialEmpty, "Saved", "NoChange"): result.Add "message", "I-STU-004"
    Exit Function
Failed:
    Dim errorText As String, errorNumber As Long
    errorText = Err.Description: errorNumber = Err.Number
    Resume FailureCleanup
FailureCleanup:
    On Error Resume Next
    If Not rs Is Nothing Then rs.Close
    Set rs = Nothing
    tx.CloseWork
    Err.Clear
    On Error GoTo 0
    If Left$(errorText, 2) <> "E-" Then errorText = "E-COM-004"
    result.Add "kind", ErrorKind(errorText): result.Add "message", errorText
End Function
