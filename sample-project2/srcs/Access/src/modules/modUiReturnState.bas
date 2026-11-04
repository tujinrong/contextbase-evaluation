Option Compare Binary
Option Explicit
Public Sub UiCaptureSearchReturn(ByVal f As Access.Form)
    Dim state As New clsSearchReturnState, s As clsFormUiState, key As Variant, row As Variant
    Set s = UiState(f): UiCaptureText f
    state.RawEmployeeNo = UiRaw(f, "txtEmployeeNo"): state.RawName = UiRaw(f, "txtName")
    If s.Raw.Exists("cboDepartment") Then state.RawDepartment = CStr(s.Raw("cboDepartment"))
    If s.Raw.Exists("cboStatus") Then state.RawStatus = CStr(s.Raw("cboStatus"))
    If s.AcceptedCodes.Exists("cboDepartment") Then state.AcceptedDepartmentCode = s.AcceptedCodes("cboDepartment") Else state.AcceptedDepartmentCode = f!cboDepartment.Value
    If s.AcceptedCodes.Exists("cboStatus") Then state.AcceptedStatusCode = s.AcceptedCodes("cboStatus") Else state.AcceptedStatusCode = f!cboStatus.Value
    For Each key In s.Pending.Keys: state.PendingComboRaw.Add CStr(key), CStr(s.Pending(key)): Next
    state.SearchState = gSearchState: state.ResultState = gSearchResultState
    state.HasAppliedCriteria = Not gAppliedCriteria Is Nothing: state.AppliedValid = gAppliedValid
    Set state.AppliedCriteria = gAppliedCriteria
    If Not gSearchRows Is Nothing Then
        For Each row In gSearchRows: state.ResultRows.Add row: Next
    End If
    For Each row In CachedRows(f!cboDepartment): state.DepartmentRows.Add row: Next
    For Each row In CachedRows(f!cboStatus): state.StatusRows.Add row: Next
    state.SelectedEmployeeId = gSelectedEmployee
    state.FocusControl = UiLogicalOwner(f, f.ActiveControl.Name)
    If f.ActiveControl.ControlType = acCommandButton And s.Pending.Exists(s.LastEditFocus) Then state.FocusControl = s.LastEditFocus
    UiCaptureEmployeeViewport f, state
    Set gSearchReturn = state
    ' gSearchRaw remains a compatibility raw-code snapshot for existing callers;
    ' the return class is authoritative and preserves display/Pending separately.
    Set gSearchRaw = CreateObject("Scripting.Dictionary")
    gSearchRaw("EmployeeNo") = state.RawEmployeeNo: gSearchRaw("NameRaw") = state.RawName
    gSearchRaw("Department") = state.AcceptedDepartmentCode: gSearchRaw("Status") = state.AcceptedStatusCode
End Sub
Public Sub UiLoadSearch(ByVal f As Access.Form)
    Dim s As clsFormUiState, key As Variant
    Set s = UiState(f)
    If gSearchReturn Is Nothing Then
        FillCombo f!cboDepartment, "DEPARTMENT", True, "", True
        FillCombo f!cboStatus, "EMPLOYMENT_STATUS", True, "", True
        UiSetTextValue f, "txtEmployeeNo", Null: UiSetTextValue f, "txtName", Null
        f!cboDepartment = Null: f!cboStatus = "01"
        Set gCriteria = New clsSearchCriteria: gCriteria.EmployeeNo = Null: gCriteria.Department = Null: gCriteria.Status = "01"
        Set gSearchRows = New Collection: gSelectedEmployee = Null
        gSearchWasExecuted = False: gSearchState = "Unsearched": gSearchResultState = "NoResult"
        Set gAppliedCriteria = Nothing: gAppliedValid = False
        UiRememberCombo f, "cboDepartment": UiRememberCombo f, "cboStatus"
    Else
        SetRows f!cboDepartment, gSearchReturn.DepartmentRows
        SetRows f!cboStatus, gSearchReturn.StatusRows
        UiSetTextValue f, "txtEmployeeNo", gSearchReturn.RawEmployeeNo
        UiSetTextValue f, "txtName", gSearchReturn.RawName
        f!cboDepartment = gSearchReturn.AcceptedDepartmentCode: f!cboStatus = gSearchReturn.AcceptedStatusCode
        s.AcceptedCodes("cboDepartment") = gSearchReturn.AcceptedDepartmentCode
        s.AcceptedCodes("cboStatus") = gSearchReturn.AcceptedStatusCode
        s.Raw("cboDepartment") = gSearchReturn.RawDepartment: s.Raw("cboStatus") = gSearchReturn.RawStatus
        For Each key In gSearchReturn.PendingComboRaw.Keys: s.Pending(CStr(key)) = gSearchReturn.PendingComboRaw(key): Next
        Set gSearchRows = gSearchReturn.ResultRows: gSelectedEmployee = gSearchReturn.SelectedEmployeeId
        gSearchState = gSearchReturn.SearchState: gSearchResultState = gSearchReturn.ResultState
        Set gAppliedCriteria = gSearchReturn.AppliedCriteria: gAppliedValid = gSearchReturn.AppliedValid
        gSearchWasExecuted = (gSearchState = "Searched")
    End If
    SetRows f!lstEmployees, gSearchRows
    If gSearchState = "Searched" Then f!lblCount.Caption = CStr(gSearchRows.Count) & "件" Else f!lblCount.Caption = IIf(gSearchState = "Changed", "条件変更・未検索", "未検索")
    f!cmdEdit.Enabled = False: f!cmdExport.Enabled = False
    UiCollapseSelectedDetails f
    RestoreEmployeeSelection f
    UiSyncPendingEditors f
End Sub
Public Sub UiCollapseSelectedDetails(ByVal f As Access.Form)
    Dim activeName As String, paint As Long, number As Long, description As String
    On Error Resume Next
    activeName = f.ActiveControl.Name
    Err.Clear
    On Error GoTo Failed
    paint = UiBeginPaint()
    If activeName = "txtSelectedDetails" Then f!lstEmployees.SetFocus
    UiSetIfChanged f!txtSelectedDetails, "Value", Null
    UiSetIfChanged f!txtSelectedDetails, "Visible", False
    UiSetIfChanged f!txtSelectedDetails, "Height", 330
    UiSetIfChanged f.Section(acDetail), "Height", 7500
    UiEndPaint paint: Exit Sub
Failed:
    number = Err.Number: description = Err.Description
    On Error Resume Next
    UiEndPaint paint
    On Error GoTo 0
    Err.Raise number, "SP2.UiCollapseSelectedDetails", description
End Sub
Public Sub UiSelectedEmployeeDetails(ByVal f As Access.Form)
    Dim row As Variant, paint As Long, number As Long, description As String, activeName As String
    On Error Resume Next
    activeName = f.ActiveControl.Name
    Err.Clear
    On Error GoTo Failed
    paint = UiBeginPaint()
    If activeName = "txtSelectedDetails" Then f!lstEmployees.SetFocus
    If IsNull(gSelectedEmployee) Or gSearchRows Is Nothing Then GoTo EmptySelection
    For Each row In gSearchRows
        If CLng(row(0)) = CLng(gSelectedEmployee) Then
            UiSetIfChanged f!lblSelection, "Caption", CStr(row(1)) & "  " & CStr(row(2))
            UiSetIfChanged f!txtSelectedDetails, "Value", "社員番号：" & CStr(row(1)) & vbCrLf & "氏名：" & CStr(row(2)) & vbCrLf & "氏名カナ：" & CStr(row(3)) & vbCrLf & "部署：" & CStr(row(4)) & vbCrLf & "在籍：" & CStr(row(5)) & " ／ 入社日：" & CStr(row(6))
            UiSetIfChanged f!txtSelectedDetails, "Height", 1980
            UiSetIfChanged f.Section(acDetail), "Height", 9450
            UiSetIfChanged f!txtSelectedDetails, "Visible", True
            UiEndPaint paint: Exit Sub
        End If
    Next
EmptySelection:
    UiCollapseSelectedDetails f
    UiEndPaint paint: Exit Sub
Failed:
    number = Err.Number: description = Err.Description
    On Error Resume Next
    UiEndPaint paint
    On Error GoTo 0
    Err.Raise number, "SP2.UiSelectedEmployeeDetails", description
End Sub
Public Sub UiUpdateIdentity(ByVal f As Access.Form)
    Dim s As clsFormUiState, name As String, code As String, mode As String, identityChanged As Boolean
    Set s = UiState(f)
    If f.Name = "frmEmployeeEditor" Then
        mode = IIf(IsNull(gEditor.EmployeeId), "新規", "編集")
        UiSetIfChanged f!lblScreenTitle, "Caption", "社員登録・編集［" & mode & "］"
        name = UiRaw(f, "txtEmployeeName"): code = UiRaw(f, "txtEmployeeNo")
        identityChanged = UiSetIfChanged(f!lblEmployeeIdentity, "Caption", IIf(mode = "新規", "新規社員：", "") & code & " " & name)
        UiSetIfChanged f!pgCareer, "Caption", "経歴（" & CStr(gEditor.Careers.Count + IIf(gCareerIndex = 0 And Not gEditor.ActiveDraft Is Nothing, 1, 0)) & "件）"
        If gEditor.ActiveDraft Is Nothing Then
            UiSetIfChanged f!lblCareerEditHeading, "Caption", "選択経歴の編集（未選択）"
            UiSetIfChanged f!lblDraftState, "Caption", "経歴未選択"
        Else
            UiSetIfChanged f!lblCareerEditHeading, "Caption", "選択経歴の編集：" & UiRaw(f, "txtProject")
            If gDraftDirty Then
                UiSetIfChanged f!lblDraftState, "Caption", "未反映・未保存"
            ElseIf s.DraftReflected Then
                UiSetIfChanged f!lblDraftState, "Caption", "反映済み・未保存"
            Else
                UiSetIfChanged f!lblDraftState, "Caption", "保存済みの経歴（入力変更なし）"
            End If
        End If
        UiSetIfChanged f!lblSaveScope, "Caption", "社員と全経歴の追加・変更・除去をまとめて保存します。"
        If identityChanged And Not s.IsInitializing Then UiResize f
    ElseIf f.Name = "frmCodeMaster" Then
        name = CStr(Nz(f!cboCategory.Column(1), ""))
        If gCode Is Nothing Then
            UiSetIfChanged f!lblCodeIdentity, "Caption", name & " ／ 未選択"
        Else
            mode = IIf(gCode.IsNew, "新規", "編集")
            If gCode.CategoryId = "EMPLOYMENT_STATUS" Then mode = "参照専用"
            UiSetIfChanged f!lblCodeIdentity, "Caption", name & " / " & UiRaw(f, "txtCode") & " " & UiRaw(f, "txtCodeName") & "［" & mode & "］"
        End If
        UiSetIfChanged f!lblCodeEditHeading, "Caption", "選択コードの編集" & IIf(CStr(Nz(f!cboCategory.Value, "")) = "EMPLOYMENT_STATUS", "（固定在籍は参照専用）", "")
    End If
End Sub
