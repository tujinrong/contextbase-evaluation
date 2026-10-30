Option Compare Binary
Option Explicit
Public gUiLoading As Boolean
Public gDirty As Boolean
Public gDraftDirty As Boolean
Public gCareerIndex As Long
Public gAllowClose As Boolean
Public gExportCancel As Boolean
Public Sub LogoutNow()
    Dim names As Variant, n As Variant
    Call EnsureSession: gSession.Clear: gAllowClose = True
    names = Array("frmEmployeeEditor", "frmCodeMaster", "frmEmployeeSearch", "frmMenu")
    For Each n In names
        If CurrentProject.AllForms(CStr(n)).IsLoaded Then DoCmd.Close acForm, CStr(n), acSaveNo
    Next
    gAllowClose = False: gDirty = False: gDraftDirty = False
    Set gEditor = Nothing: Set gOriginal = Nothing: Set gCode = Nothing: Set gCriteria = Nothing
    Set gSearchRaw = Nothing: Set gSearchRows = Nothing: gSearchWasExecuted = False
    Set gSearchReturn = Nothing: Set gAppliedCriteria = Nothing: gAppliedValid = False
    If Not CurrentProject.AllForms("frmLogin").IsLoaded Then DoCmd.OpenForm "frmLogin"
End Sub
Public Sub Navigate(ByVal from As Access.Form, ByVal target As String)
    Dim priorAllow As Boolean, number As Long, description As String
    On Error GoTo Failed
    priorAllow = gAllowClose: gAllowClose = True
    DoCmd.OpenForm target: DoCmd.Close acForm, from.Name, acSaveNo
    gAllowClose = priorAllow: Exit Sub
Failed:
    number = Err.Number: description = Err.Description: gAllowClose = priorAllow
    Err.Raise number, , description
End Sub
Public Function ConfirmDiscard(Optional ByVal f As Access.Form = Nothing) As Boolean
    Dim pending As Boolean, title As String, scope As String
    title = "入力確認"
    If Not f Is Nothing Then
        pending = (UiState(f).Pending.Count > 0)
        title = UiDialogTitle(f)
        If f.Name = "frmEmployeeEditor" Then scope = " 社員と全経歴の未保存変更を破棄します。"
        If f.Name = "frmCodeMaster" Then scope = " 編集中のコード1件の未保存変更を破棄します。"
    End If
    If Not gDirty And Not gDraftDirty And Not pending Then ConfirmDiscard = True: Exit Function
    ConfirmDiscard = (MsgBox(MessageText("MSG-015") & scope, vbYesNo + vbQuestion + vbDefaultButton2, title) = vbYes)
    If Not f Is Nothing Then
        If ConfirmDiscard Then UiClearPending f Else UiRestoreDeclined f
    End If
End Function
Public Sub FillCombo(ByVal ctl As Control, ByVal category As String, ByVal includeStopped As Boolean, Optional ByVal current As String = "", Optional ByVal includeEmpty As Boolean = False)
    Dim u As New clsUnitOfWork, q As DAO.QueryDef, r As DAO.Recordset, rows As New Collection, caption As String, overlay As New clsUiBusyState
    On Error GoTo Failed
    overlay.Acquire OwnerForm(ctl)
    u.OpenUnit True: RequireCurrent gSession, "STAFF", u.Db
    If includeEmpty Then rows.Add Array(Null, "すべて")
    Set q = Query(u.Db, "PARAMETERS p Text(24); SELECT * FROM m_code WHERE category_id=p ORDER BY sort_order, code", category)
    Set r = q.OpenRecordset(dbOpenSnapshot)
    Do While Not r.EOF
        If includeStopped Or r!is_enabled Or CStr(r!code) = current Then
            caption = CStr(r!code_name): If Not r!is_enabled Then caption = caption & "（停止）"
            rows.Add Array(CStr(r!code), caption)
        End If
        r.MoveNext
    Loop
    r.Close: q.Close: u.Commit: u.CloseUnit: overlay.Restore
    SetRows ctl, rows: Exit Sub
Failed:
    u.Cancel: u.CloseUnit: overlay.Restore: Reject "MSG-040"
End Sub
