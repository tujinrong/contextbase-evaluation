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
    state.FocusControl = f.ActiveControl.Name
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
        f!txtEmployeeNo = Null: f!txtName = Null: f!cboDepartment = Null: f!cboStatus = "01"
        Set gCriteria = New clsSearchCriteria: gCriteria.EmployeeNo = Null: gCriteria.Department = Null: gCriteria.Status = "01"
        Set gSearchRows = New Collection: gSelectedEmployee = Null
        gSearchWasExecuted = False: gSearchState = "Unsearched": gSearchResultState = "NoResult"
        Set gAppliedCriteria = Nothing: gAppliedValid = False
        UiRememberCombo f, "cboDepartment": UiRememberCombo f, "cboStatus"
    Else
        SetRows f!cboDepartment, gSearchReturn.DepartmentRows
        SetRows f!cboStatus, gSearchReturn.StatusRows
        f!txtEmployeeNo = gSearchReturn.RawEmployeeNo: f!txtName = gSearchReturn.RawName
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
End Sub
Public Sub UiCollapseSelectedDetails(ByVal f As Access.Form)
    Dim activeName As String
    On Error GoTo NoActive
    activeName = f.ActiveControl.Name
NoActive:
    On Error GoTo 0
    If activeName = "txtSelectedDetails" Then f!lstEmployees.SetFocus
    f!txtSelectedDetails = Null: f!txtSelectedDetails.Visible = False
    f!txtSelectedDetails.Height = 330: f.Section(acDetail).Height = 7500
End Sub
Public Sub UiSelectedEmployeeDetails(ByVal f As Access.Form)
    Dim row As Variant
    UiCollapseSelectedDetails f
    If IsNull(gSelectedEmployee) Or gSearchRows Is Nothing Then Exit Sub
    For Each row In gSearchRows
        If CLng(row(0)) = CLng(gSelectedEmployee) Then
            f!lblSelection.Caption = CStr(row(1)) & "  " & CStr(row(2))
            f!txtSelectedDetails = "社員番号：" & CStr(row(1)) & vbCrLf & "氏名：" & CStr(row(2)) & vbCrLf & "氏名カナ：" & CStr(row(3)) & vbCrLf & "部署：" & CStr(row(4)) & vbCrLf & "在籍：" & CStr(row(5)) & " ／ 入社日：" & CStr(row(6))
            f!txtSelectedDetails.Height = 1980: f.Section(acDetail).Height = 9450: f!txtSelectedDetails.Visible = True
            Exit Sub
        End If
    Next
End Sub
Public Sub UiUpdateIdentity(ByVal f As Access.Form)
    Dim s As clsFormUiState, name As String, code As String, mode As String
    Set s = UiState(f)
    If f.Name = "frmEmployeeEditor" Then
        mode = IIf(IsNull(gEditor.EmployeeId), "新規", "編集")
        f!lblScreenTitle.Caption = "社員登録・編集［" & mode & "］"
        name = UiRaw(f, "txtEmployeeName"): code = UiRaw(f, "txtEmployeeNo")
        f!lblEmployeeIdentity.Caption = IIf(mode = "新規", "新規社員：", "") & code & " " & name
        f!pgCareer.Caption = "経歴（" & CStr(gEditor.Careers.Count + IIf(gCareerIndex = 0 And Not gEditor.ActiveDraft Is Nothing, 1, 0)) & "件）"
        If gEditor.ActiveDraft Is Nothing Then
            f!lblCareerEditHeading.Caption = "選択経歴の編集（未選択）": f!lblDraftState.Caption = "経歴未選択"
        Else
            f!lblCareerEditHeading.Caption = "選択経歴の編集：" & UiRaw(f, "txtProject")
            If gDraftDirty Then
                f!lblDraftState.Caption = "未反映・未保存"
            ElseIf s.DraftReflected Then
                f!lblDraftState.Caption = "反映済み・未保存"
            Else
                f!lblDraftState.Caption = "保存済みの経歴（入力変更なし）"
            End If
        End If
        f!lblSaveScope.Caption = "社員と全経歴の追加・変更・除去をまとめて保存します。"
        UiResize f
    ElseIf f.Name = "frmCodeMaster" Then
        name = CStr(Nz(f!cboCategory.Column(1), ""))
        If gCode Is Nothing Then
            f!lblCodeIdentity.Caption = name & " ／ 未選択"
        Else
            mode = IIf(gCode.IsNew, "新規", "編集")
            If gCode.CategoryId = "EMPLOYMENT_STATUS" Then mode = "参照専用"
            f!lblCodeIdentity.Caption = name & " / " & UiRaw(f, "txtCode") & " " & UiRaw(f, "txtCodeName") & "［" & mode & "］"
        End If
        f!lblCodeEditHeading.Caption = "選択コードの編集" & IIf(CStr(Nz(f!cboCategory.Value, "")) = "EMPLOYMENT_STATUS", "（固定在籍は参照専用）", "")
    End If
End Sub
