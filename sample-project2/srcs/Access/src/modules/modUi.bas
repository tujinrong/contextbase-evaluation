Option Compare Binary
Option Explicit
Public gSearchRows As Collection
Public gSelectedEmployee As Variant
Public gSearchRaw As Object
Public gSearchWasExecuted As Boolean
Private setupStep As Integer
Private setupFirst As String
Private setupAdmin As String
Private setupStaff As String
Private initialisingFormName As String
Public Function UiIsInitialisingForm(ByVal f As Access.Form) As Boolean
    UiIsInitialisingForm = (initialisingFormName <> "" And initialisingFormName = f.Name)
End Function
Public Sub UiLoad(ByVal f As Access.Form)
    Dim result As clsResult, rows As New Collection, initialized As Boolean, priorInitialisingForm As String, ui As clsFormUiState
    On Error GoTo Failed
    Set ui = UiState(f): ui.IsInitializing = True
    priorInitialisingForm = initialisingFormName: initialisingFormName = f.Name
    gUiLoading = True: EnsureSession
    If f.Name = "frmLogin" Then
        UiSetTextValue f, "txtPassword", Null
        If CurrentDb.Properties("SP2_Staging").Value And DCount("*", "m_app_user") = 0 Then
            setupStep = 1: UiSetTextValue f, "txtLoginId", "admin": f!txtLoginId.Locked = True
            f!lblMessage.Caption = "配布前初期設定：admin のパスワードを入力してください（次に同じ値を再入力）。"
        Else
            setupStep = 0: f!txtLoginId.Locked = False
        End If
        initialized = True: GoTo Done
    End If
    Set result = UiAuthorize(f, IIf(f.Name = "frmCodeMaster", "ADMIN", "STAFF"))
    If result.Kind <> "OK" Then ShowResult f, result: GoTo Done
    Select Case f.Name
    Case "frmMenu"
        f!lblActor.Caption = gSession.DisplayName & " ／ " & gSession.RoleId
        f!cmdCodeMaster.Visible = (gSession.RoleId = "ADMIN"): f!cmdCodeMaster.Enabled = (gSession.RoleId = "ADMIN")
        f!lblCodeHelp.Visible = (gSession.RoleId = "ADMIN")
    Case "frmEmployeeSearch"
        UiLoadSearch f
    Case "frmEmployeeEditor"
        If gEditor Is Nothing Then Reject "MSG-020"
        gCareerIndex = 0: FillEditor f: gDirty = False: gDraftDirty = False
    Case "frmCodeMaster"
        rows.Add Array("DEPARTMENT", "部署"): rows.Add Array("EMPLOYMENT_STATUS", "在籍区分"): rows.Add Array("PROJECT_ROLE", "案件役割")
        SetRows f!cboCategory, rows: f!cboCategory = "DEPARTMENT": Set gCode = Nothing
        UiState(f).AcceptedCategory = "DEPARTMENT"
        LoadCodeRows f: ClearCode f
    End Select
    initialized = True
Done:
    initialisingFormName = priorInitialisingForm
    gUiLoading = False
    ui.IsInitializing = False
    If initialized Then
        UiCaptureText f
        If f.Name = "frmEmployeeEditor" Or f.Name = "frmCodeMaster" Then UiUpdateIdentity f
    End If
    Exit Sub
Failed:
    initialisingFormName = priorInitialisingForm
    If Not ui Is Nothing Then ui.IsInitializing = False
    gUiLoading = False: Set result = MakeResult("ReadFailure", "MSG-040"): ShowResult f, result
End Sub
Public Sub UiTimer(ByVal f As Access.Form)
    UiDeferredWork f
    EnsureSession
    If Not gSession.IsAuthenticated Then Exit Sub
    If GetTickCount64() - gSession.LastActivityTick >= 1800000 Then
        gSession.Clear
        If gBusy Then gExportCancel = True Else LogoutNow
    End If
End Sub
Public Sub UiKey(ByVal f As Access.Form, ByRef key As Integer, Optional ByVal shift As Integer = 0)
    Dim active As Object
    UiCancelDeferredPending f
    If f.Name = "frmEmployeeSearch" Then UiCancelViewportRestore f
    If gBusy Then
        If key = vbKeyEscape And f.Name = "frmEmployeeSearch" Then gExportCancel = True
        key = 0: Exit Sub
    End If
    If f.Name <> "frmLogin" Then
        If Not TouchActivity() Then key = 0: LogoutNow: Exit Sub
    End If
    If UiPendingKey(f, key, shift) Then Exit Sub
    If key = vbKeyEscape And (f.Name = "frmEmployeeEditor" Or f.Name = "frmCodeMaster") Then
        UiCapturePendingOnEscape f: key = 0: UiAction f, "cmdCancel": Exit Sub
    End If
    If key = vbKeyReturn And f.Name = "frmEmployeeSearch" Then
        If UiTryGetActiveControl(f, active) Then
            If InStr(1, "|txtEmployeeNo|txtName|cboDepartment|cboStatus|", "|" & UiLogicalOwner(f, active.Name) & "|", vbBinaryCompare) > 0 Then
                key = 0: UiAction f, "cmdSearch": Exit Sub
            End If
        End If
    End If
    UiRouteTab f, key, shift
End Sub
Public Sub UiMouse(ByVal f As Access.Form)
    UiCancelDeferredPending f
    If f.Name = "frmEmployeeSearch" Then UiCancelViewportRestore f
    If Not gBusy And f.Name <> "frmLogin" Then
        If Not TouchActivity() Then LogoutNow
    End If
End Sub
Public Sub UiChanged(ByVal f As Access.Form, ByVal ctl As String)
    Dim raw As String, ui As clsFormUiState
    Set ui = UiState(f)
    If gUiLoading Or ui.IsInitializing Or ui.IsRestoringSelection Then Exit Sub
    If UiLogicalOwner(f, ctl) <> ctl Then UiPendingChanged f, ctl: Exit Sub
    If f.Name = "frmEmployeeSearch" Then UiCancelViewportRestore f
    If ctl = "txtSelectedDetails" Then Exit Sub
    If f.Controls(ctl).ControlType = acTextBox Then UiRecordTextChange f, ctl
    If f.Name = "frmEmployeeSearch" Then
        InvalidateSearch f
    ElseIf f.Name = "frmEmployeeEditor" Then
        gDirty = True
        If IsCareerControl(ctl) Then gDraftDirty = True
        UiUpdateIdentity f
    ElseIf f.Name = "frmCodeMaster" Then
        gDirty = True: UiUpdateIdentity f
    End If
End Sub
Private Function IsCareerControl(ByVal ctl As String) As Boolean
    IsCareerControl = InStr(1, "|txtStartMonth|txtEndMonth|txtCompany|txtProject|txtDescription|txtDuties|txtAchievements|txtTechnologies|txtPhases|cboRole|txtTeamSize|", "|" & ctl & "|", vbBinaryCompare) > 0
End Function
Public Sub UiBeforeUpdate(ByVal f As Access.Form, ByVal name As String, ByRef cancel As Integer)
    Dim maximum As Long, raw As String
    On Error GoTo Invalid
    If gUiLoading Then Exit Sub
    Select Case name
    Case "txtPassword": maximum = 128
    Case "txtLoginId": maximum = 20
    Case "txtEmployeeNo": maximum = 6
    Case "txtEmployeeName", "txtName", "txtCodeName": maximum = 40
    Case "txtEmployeeKana": maximum = 80
    Case "txtJoinDate": maximum = 10
    Case "txtStartMonth", "txtEndMonth": maximum = 7
    Case "txtCompany", "txtProject": maximum = 100
    Case "txtTeamSize", "txtSortOrder": maximum = 3
    Case "txtCode": maximum = 2
    Case "txtTechnologies": maximum = 500
    Case "txtPhases": maximum = 200
    Case Else: maximum = 1000
    End Select
    raw = UiRaw(f, name)
    If ScalarLength(raw) > maximum Then GoTo Invalid
    Exit Sub
Invalid:
    ' Unbound invalid raw may leave this field to reach Cancel. Central actions reject it.
    cancel = False
    If f.Name = "frmEmployeeSearch" Then
        f!lblSelection.Caption = MessageText("MSG-005", "入力欄（" & CStr(maximum) & "字以内）")
    Else
        f!lblMessage.Caption = MessageText("MSG-005", "入力欄（" & CStr(maximum) & "字以内）")
    End If
End Sub
Public Sub UiSelected(ByVal f As Access.Form, ByVal ctl As String, Optional ByVal nativeComboCommit As Boolean = False)
    Dim row As Variant, index As Long, result As clsResult, ui As clsFormUiState, requested As Variant, previous As Variant
    On Error GoTo Failed
    Set ui = UiState(f)
    If gUiLoading Or ui.IsInitializing Or ui.IsRestoringSelection Then Exit Sub
    If ctl = "tabEmployee" Then UiSwitchPage f: Exit Sub
    If gBusy Then Exit Sub
    If nativeComboCommit And f.Controls(ctl).ControlType = acComboBox Then UiMarkPendingCandidate f, ctl
    If f.Name = "frmEmployeeSearch" Then UiCancelViewportRestore f
    If f.Name <> "frmLogin" Then If Not TouchActivity() Then LogoutNow: Exit Sub
    If f.Controls(ctl).ControlType = acComboBox And ctl <> "cboCategory" Then
        If Not UiAcceptCombo(f, ctl) Then Exit Sub
    End If
    Select Case f.Name
    Case "frmEmployeeSearch"
        If ctl = "lstEmployees" Then
            gSelectedEmployee = f!lstEmployees.Value
            f!cmdEdit.Enabled = Not IsNull(gSelectedEmployee): f!cmdExport.Enabled = Not IsNull(gSelectedEmployee)
            UiSelectedEmployeeDetails f
        Else
            UiChanged f, ctl
        End If
    Case "frmEmployeeEditor"
        If ctl = "lstCareers" Then
            requested = f!lstCareers.Value
            ui.IsRestoringSelection = True: f!lstCareers = IIf(gCareerIndex > 0, gCareerIndex, Null): ui.IsRestoringSelection = False
            UiCaptureText f: UiRequireNoPending f
            If Not UiResolveDraft(f) Then UiRestoreDeclined f: Exit Sub
            index = CLng(Nz(requested, 0))
            If index > 0 And index <= gEditor.Careers.Count Then
                gCareerIndex = index: Set gEditor.ActiveDraft = CloneCareer(gEditor.Careers(index))
                FillDraft f, gEditor.ActiveDraft
                ui.IsRestoringSelection = True: f!lstCareers = index: ui.IsRestoringSelection = False
                ui.AcceptedListKey = index
            End If
        Else
            UiChanged f, ctl
        End If
    Case "frmCodeMaster"
        If ctl = "cboCategory" Then
            requested = f!cboCategory.Value: previous = ui.AcceptedCategory
            ui.IsRestoringSelection = True: f!cboCategory = previous: ui.IsRestoringSelection = False
            If ui.Pending.Exists("cboCategory") Then
                If Not ui.ExplicitComboChoice.Exists("cboCategory") Then UiRestoreDeclined f: Exit Sub
                If Not CBool(ui.ExplicitComboChoice("cboCategory")) Then UiRestoreDeclined f: Exit Sub
                If Same(requested, previous) Then
                    ui.Pending.Remove "cboCategory": UiRememberCombo f, "cboCategory"
                    UiFinishPendingChoice f, "cboCategory": Exit Sub
                End If
            End If
            If Not ConfirmDiscard(f) Then UiRestoreDeclined f: Exit Sub
            UiClearPending f
            ui.IsRestoringSelection = True: f!cboCategory = requested: ui.IsRestoringSelection = False
            ui.AcceptedCategory = CStr(requested): UiRememberCombo f, "cboCategory"
            UiFinishPendingChoice f, "cboCategory"
            LoadCodeRows f: ClearCode f
        ElseIf ctl = "lstCodes" Then
            requested = f!lstCodes.Value
            ui.IsRestoringSelection = True: f!lstCodes = ui.AcceptedListKey: ui.IsRestoringSelection = False
            UiCaptureText f: UiRequireNoPending f
            If Not ConfirmDiscard(f) Then UiRestoreDeclined f: Exit Sub
            For Each row In CachedRows(f!lstCodes)
                If CStr(row(0)) = CStr(Nz(requested, "")) Then
                    Set gCode = New clsCodeEdit: gCode.CategoryId = CStr(f!cboCategory.Value)
                    gCode.Code = CStr(row(1)): gCode.Name = CStr(row(2)): gCode.SortOrder = CInt(row(3))
                    gCode.IsEnabled = CBool(row(4)): gCode.ExpectedRevision = CLng(row(5)): gCode.IsNew = False
                    ui.AcceptedListKey = requested
                    ui.IsRestoringSelection = True: f!lstCodes = requested: ui.IsRestoringSelection = False
                    FillCode f: Exit For
                End If
            Next
        Else
            gDirty = True: UiUpdateIdentity f
        End If
    End Select
    Exit Sub
Failed:
    ui.IsRestoringSelection = False
    Set result = Failure(Err.Description, Nothing, True): ShowResult f, result
End Sub
Public Sub UiAction(ByVal f As Access.Form, ByVal action As String)
    Dim result As clsResult, e As clsEmployeeEdit, index As Long, id As Variant, text As String, category As String
    On Error GoTo Failed
    If gBusy Then ShowResult f, MakeResult("Busy", "MSG-029"): Exit Sub
    If f.Name = "frmEmployeeSearch" Then UiCancelViewportRestore f
    ' Capture before authorization overlays can disable/re-enable the list and
    ' scroll its selected row into view. Selection and viewport are independent.
    If f.Name = "frmEmployeeSearch" And (action = "cmdNew" Or action = "cmdEdit") Then
        UiCapturePendingOnEscape f
        UiCaptureSearchReturn f
    End If
    UiCaptureText f
    If (f.Name = "frmEmployeeSearch" And action = "cmdSearch") Or (f.Name = "frmEmployeeEditor" And action <> "cmdCancel") Or (f.Name = "frmCodeMaster" And (action = "cmdSave" Or action = "cmdNew")) Then UiRequireNoPending f
    If action = "cmdExit" Then EnsureSession: gSession.Clear: Application.Quit acQuitSaveNone: Exit Sub
    If action = "cmdLogout" Then
        If Not ConfirmDiscard(f) Then Exit Sub
        LogoutNow: Exit Sub
    End If
    If f.Name <> "frmLogin" Then If Not TouchActivity() Then LogoutNow: Exit Sub
    gBusy = True
    If f.Name <> "frmLogin" Then
        Set result = UiAuthorize(f, IIf(f.Name = "frmCodeMaster", "ADMIN", "STAFF"))
        If result.Kind <> "OK" Then ShowResult f, result: GoTo Done
    End If
    Select Case f.Name
    Case "frmLogin"
        If setupStep > 0 Then
            SetupSubmit f: GoTo Done
        End If
        ValidateLoginInput f
        Set result = UiAuthenticate(f, CStr(Nz(f!txtLoginId, "")), CStr(Nz(f!txtPassword, "")))
        UiSetTextValue f, "txtPassword", Null
        If result.Kind = "OK" Then
            Navigate f, "frmMenu"
        Else
            ShowResult f, result: f!txtPassword.SetFocus
        End If
    Case "frmMenu"
        Set result = UiAuthorize(f, IIf(action = "cmdCodeMaster", "ADMIN", "STAFF"))
        If result.Kind <> "OK" Then ShowResult f, result: GoTo Done
        If action = "cmdEmployeeSearch" Then Set gCriteria = Nothing: Set gSearchRaw = Nothing: Set gSearchReturn = Nothing: Set gAppliedCriteria = Nothing: gAppliedValid = False: gSearchWasExecuted = False: Set gSearchRows = Nothing: Navigate f, "frmEmployeeSearch"
        If action = "cmdCodeMaster" Then Navigate f, "frmCodeMaster"
    Case "frmEmployeeSearch"
        Select Case action
        Case "cmdSearch": ExecuteSearch f
        Case "cmdClear"
            gUiLoading = True
            UiSetTextValue f, "txtEmployeeNo", Null: UiSetTextValue f, "txtName", Null
            f!cboDepartment = Null: f!cboStatus = "01": gUiLoading = False
            UiClearPending f: UiRememberCombo f, "cboDepartment": UiRememberCombo f, "cboStatus"
            InvalidateSearch f
            gSearchState = "Unsearched": gSearchResultState = "NoResult": Set gAppliedCriteria = Nothing
            f!lblCount.Caption = "未検索": f!lblSelection.Caption = "条件を指定して検索してください。"
        Case "cmdMenu": Set gCriteria = Nothing: Set gSearchRaw = Nothing: Set gSearchReturn = Nothing: Set gAppliedCriteria = Nothing: gAppliedValid = False: gSearchWasExecuted = False: Set gSearchRows = Nothing: Navigate f, "frmMenu"
        Case "cmdNew", "cmdEdit"
            Set result = UiAuthorize(f, "STAFF"): If result.Kind <> "OK" Then ShowResult f, result: GoTo Done
            If action = "cmdNew" Then
                Set gEditor = New clsEmployeeEdit: gEditor.Status = "01": Set gOriginal = Nothing
            Else
                id = SelectedId(f): Set result = UiReadEmployee(f, CLng(id))
                If result.Kind <> "OK" Then ShowResult f, result: GoTo Done
                Set gEditor = result.Value: Set gOriginal = CloneEmployee(gEditor)
            End If
            gDirty = False: gDraftDirty = False: Navigate f, "frmEmployeeEditor"
        Case "cmdExport"
            id = SelectedId(f): gExportCancel = False
            Set result = UiExport(f, CLng(id)): ShowResult f, result
        End Select
    Case "frmEmployeeEditor"
        If gEditor.Outcome = "CommitUnknown" And action <> "cmdCancel" Then ShowResult f, MakeResult("CommitUnknown", "MSG-034"): GoTo Done
        Select Case action
        Case "cmdAddCareer"
            If Not UiResolveDraft(f) Then GoTo Done
            If gEditor.Careers.Count >= 20 Then Reject "MSG-018"
            Set gEditor.ActiveDraft = New clsCareerDraft: gCareerIndex = 0
            FillDraft f, gEditor.ActiveDraft: gDraftDirty = True: gDirty = True: SyncCareerButtons f: UiUpdateIdentity f: f!txtStartMonth.SetFocus
        Case "cmdApplyCareer": ApplyDraft f
        Case "cmdRemoveCareer"
            If gCareerIndex < 1 Or gCareerIndex > gEditor.Careers.Count Then Reject "MSG-025"
            If MsgBox(MessageText("MSG-031") & " DBへの除去は全体保存で確定します。", vbYesNo + vbQuestion + vbDefaultButton2, UiDialogTitle(f, True)) <> vbYes Then GoTo Done
            Set e = gEditor: id = e.Careers(gCareerIndex).PersistentId
            If Not IsNull(id) Then e.RemovedCareerIds.Add CLng(id)
            e.Careers.Remove gCareerIndex: Set e.ActiveDraft = Nothing: gCareerIndex = 0: gDraftDirty = False: gDirty = True
            RefreshCareers f: ClearDraft f
        Case "cmdSave"
            ReadEditor f
            If Not gEditor.ActiveDraft Is Nothing Then ApplyDraft f
            Set e = CloneEmployee(gEditor): Set result = UiSaveEmployee(f, e)
            ShowResult f, result
            If result.Kind = "OK" Then
                Set e = result.Value: gSelectedEmployee = e.EmployeeId: gDirty = False: gDraftDirty = False
                Navigate f, "frmEmployeeSearch"
                gSelectedEmployee = e.EmployeeId
                If ExecuteSearch(Forms("frmEmployeeSearch")) Then
                    ShowResult Forms("frmEmployeeSearch"), MakeResult("OK", "MSG-014")
                Else
                    Forms("frmEmployeeSearch")!lblSelection.Caption = MessageText("MSG-014") & vbCrLf & Forms("frmEmployeeSearch")!lblSelection.Caption
                End If
            End If
        Case "cmdCancel"
            If gEditor.Outcome = "CommitUnknown" Then
                ShowResult f, MakeResult("CommitUnknown", "MSG-034")
                If MsgBox(MessageText("MSG-015"), vbYesNo + vbQuestion + vbDefaultButton2, UiDialogTitle(f)) <> vbYes Then GoTo Done
            ElseIf Not ConfirmDiscard(f) Then
                GoTo Done
            End If
            UiClearPending f
            gDirty = False: gDraftDirty = False: Navigate f, "frmEmployeeSearch"
        End Select
    Case "frmCodeMaster"
        If f.Tag = "CommitUnknown" Then
            ShowResult f, MakeResult("CommitUnknown", "MSG-034")
            If action <> "cmdCancel" Then GoTo Done
            If MsgBox(MessageText("MSG-015"), vbYesNo + vbQuestion + vbDefaultButton2, UiDialogTitle(f)) <> vbYes Then GoTo Done
            f.Tag = "": LoadCodeRows f: ReloadSelectedCode f: GoTo Done
        End If
        Select Case action
        Case "cmdNew"
            If Not ConfirmDiscard(f) Then GoTo Done
            category = CStr(f!cboCategory)
            If category = "EMPLOYMENT_STATUS" Then Reject "MSG-023"
            If CachedRows(f!lstCodes).Count >= 99 Then Reject "MSG-024"
            Set gCode = New clsCodeEdit: gCode.CategoryId = category: FillCode f: f!txtCode.SetFocus
        Case "cmdSave"
            If gCode Is Nothing Then Reject "MSG-016"
            If Not gCode.IsNew Then
                If gCode.IsEnabled And Not CBool(Nz(f!chkEnabled, False)) Then
                    If MsgBox(MessageText("MSG-038"), vbYesNo + vbQuestion + vbDefaultButton2, UiDialogTitle(f)) <> vbYes Then GoTo Done
                End If
            End If
            gCode.Code = UiRaw(f, "txtCode"): gCode.Name = UiRaw(f, "txtCodeName"): gCode.SortOrder = ReadInteger(UiRaw(f, "txtSortOrder"), "並び順"): gCode.IsEnabled = CBool(Nz(f!chkEnabled, False))
            Set result = UiSaveCode(f, gCode): ShowResult f, result
            If result.Kind = "OK" Then
                gDirty = False
                If LoadCodeRows(f) Then
                    ReloadSelectedCode f: ShowResult f, result
                Else
                    ClearCode f: f!lblMessage.Caption = MessageText("MSG-014") & vbCrLf & MessageText("MSG-040")
                End If
            End If
        Case "cmdCancel"
            If Not ConfirmDiscard(f) Then GoTo Done
            If gCode Is Nothing Then GoTo Done
            If gCode.IsNew Then ClearCode f Else LoadCodeRows f: ReloadSelectedCode f
        Case "cmdMenu"
            If Not ConfirmDiscard(f) Then GoTo Done
            gDirty = False: Navigate f, "frmMenu"
        End Select
    End Select
Done:
    gBusy = False: Exit Sub
Failed:
    text = Err.Description: gUiLoading = False: gBusy = False
    If f.Name = "frmLogin" Then UiSetTextValue f, "txtPassword", Null
    Set result = Failure(text, Nothing, True): ShowResult f, result
    If f.Name = "frmLogin" Then UiState(f).Raw("txtPassword") = "": f!txtPassword.SetFocus
End Sub
Private Sub ValidateLoginInput(ByVal f As Access.Form)
    Dim login As String, password As String, i As Long, u As Long
    login = CStr(Nz(f!txtLoginId, "")): password = CStr(Nz(f!txtPassword, ""))
    CheckText login, 20, True, "ログインID"
    login = UCase$(CStr(Nz(SaveText(login), "")))
    For i = 1 To Len(login)
        u = AscW(Mid$(login, i, 1))
        If Not ((u >= 48 And u <= 57) Or (u >= 65 And u <= 90)) Then Reject "MSG-005", "ログインID"
    Next
    CheckText password, 128, True, "パスワード", False
    If ScalarLength(password) < MinimumPasswordScalars Then Reject "MSG-005", "パスワード"
End Sub
Private Sub SetupSubmit(ByVal f As Access.Form)
    Dim password As String, overlay As New clsUiBusyState, initialized As Boolean
    password = CStr(Nz(f!txtPassword, "")): CheckText password, 128, True, "パスワード", False
    If ScalarLength(password) < MinimumPasswordScalars Then Reject "MSG-005", "パスワード"
    If setupStep Mod 2 = 1 Then
        setupFirst = password: setupStep = setupStep + 1: f!lblMessage.Caption = "同じパスワードをもう一度入力してください。"
    Else
        If StrComp(setupFirst, password, vbBinaryCompare) <> 0 Then setupFirst = "": setupStep = setupStep - 1: Reject "MSG-005", "確認用パスワード"
        If setupStep = 2 Then
            setupAdmin = password: setupStep = 3: UiSetTextValue f, "txtLoginId", "staff": f!lblMessage.Caption = "staff のパスワードを入力してください。"
        Else
            setupStaff = password
            overlay.Acquire f: initialized = InitializeDemo(setupAdmin, setupStaff): overlay.Restore
            If initialized Then
                setupStep = 0: setupAdmin = "": setupStaff = "": setupFirst = ""
                f!txtLoginId.Locked = False: UiSetTextValue f, "txtLoginId", Null: f!lblMessage.Caption = "初期設定が完了しました。配布前検査を行ってください。"
            End If
        End If
    End If
    UiSetTextValue f, "txtPassword", Null: password = ""
End Sub
Public Sub UiUnload(ByVal f As Access.Form, ByRef cancel As Integer)
    Dim ui As clsFormUiState: Set ui = UiState(f)
    If f.Name = "frmEmployeeSearch" Then UiCancelViewportRestore f
    If gAllowClose Then Exit Sub
    If gBusy Then cancel = True: If f.Name = "frmEmployeeSearch" Then gExportCancel = True
    If gBusy Then Exit Sub
    If f.Name = "frmEmployeeEditor" Or f.Name = "frmCodeMaster" Then
        ui.IsUnloading = True
        UiCaptureText f
        If Not ConfirmDiscard(f) Then cancel = True
        ui.IsUnloading = False
    End If
End Sub
Public Sub UiClosed(ByVal f As Access.Form)
    DetachRows f.Name
    UiReleaseState f.Name
    If f.Name = "frmLogin" Then setupFirst = "": setupAdmin = "": setupStaff = ""
    If f.Name = "frmEmployeeEditor" Then
        Set gEditor = Nothing: Set gOriginal = Nothing: gDirty = False: gDraftDirty = False: gCareerIndex = 0
        If Not gAllowClose Then
            If Not gSession Is Nothing Then
                If gSession.IsAuthenticated Then DoCmd.OpenForm "frmEmployeeSearch"
            End If
        End If
    ElseIf f.Name = "frmCodeMaster" Then
        Set gCode = Nothing: gDirty = False
        If Not gAllowClose Then
            If Not gSession Is Nothing Then
                If gSession.IsAuthenticated Then DoCmd.OpenForm "frmMenu"
            End If
        End If
    End If
End Sub
Public Sub InvalidateSearch(ByVal f As Access.Form)
    Dim rows As New Collection
    Set gSearchRows = rows: gSelectedEmployee = Null
    gSearchWasExecuted = False: gSearchState = "Changed": gSearchResultState = "NoResult": gAppliedValid = False
    UiCollapseSelectedDetails f
    SetRows f!lstEmployees, rows: f!lstEmployees = Null: f!lblCount.Caption = "未検索": f!lblSelection.Caption = "条件が変更されました。検索してください。"
    f!cmdEdit.Enabled = False: f!cmdExport.Enabled = False
End Sub
Private Function SelectedId(ByVal f As Access.Form) As Long
    If IsNull(f!lstEmployees) Or gSearchRows Is Nothing Then Reject "MSG-011"
    If f!lstEmployees.ListIndex < 0 Or gSearchRows.Count = 0 Then Reject "MSG-011"
    SelectedId = CLng(f!lstEmployees.Value)
End Function
Public Function ExecuteSearch(ByVal f As Access.Form) As Boolean
    Dim result As clsResult
    On Error GoTo Failed
    UiCaptureText f: UiRequireNoPending f: CaptureSearchRaw f
    gSearchState = "Searching": f!lblCount.Caption = "検索中"
    Set gCriteria = New clsSearchCriteria
    gCriteria.EmployeeNo = SaveText(UiRaw(f, "txtEmployeeNo")): gCriteria.NameRaw = UiRaw(f, "txtName")
    gCriteria.Department = UiAcceptedCode(f, "cboDepartment"): gCriteria.Status = UiAcceptedCode(f, "cboStatus")
    Set result = UiSearch(f, gCriteria)
    If result.Kind <> "OK" Then GoTo Rejected
    Set gSearchRows = result.Value: SetRows f!lstEmployees, gSearchRows
    f!lblCount.Caption = CStr(gSearchRows.Count) & "件": f!lblSelection.Caption = "社員を選択してください。"
    gSearchWasExecuted = True: gSearchState = "Searched": gSearchResultState = IIf(gSearchRows.Count = 0, "Zero", "Rows")
    Set gAppliedCriteria = gCriteria: gAppliedValid = True
    f!cmdEdit.Enabled = False: f!cmdExport.Enabled = False
    RestoreEmployeeSelection f: ShowResult f, result
    ExecuteSearch = True: Exit Function
Failed:
    Set result = Failure(Err.Description, Nothing, True)
Rejected:
    InvalidateSearch f
    If result.MessageId = "MSG-010" Then
        gSearchResultState = "Limit": f!lblCount.Caption = "200件を超えています"
    ElseIf result.Kind = "Validation" Then
        gSearchResultState = "NoResult": f!lblCount.Caption = "条件エラー・未検索"
    Else
        gSearchResultState = "Failure": f!lblCount.Caption = "検索失敗"
    End If
    ShowResult f, result
End Function
Private Sub CaptureSearchRaw(ByVal f As Access.Form)
    Set gSearchRaw = CreateObject("Scripting.Dictionary")
    gSearchRaw.Add "EmployeeNo", UiRaw(f, "txtEmployeeNo"): gSearchRaw.Add "NameRaw", UiRaw(f, "txtName")
    gSearchRaw.Add "Department", UiAcceptedCode(f, "cboDepartment"): gSearchRaw.Add "Status", UiAcceptedCode(f, "cboStatus")
End Sub
Public Sub RestoreEmployeeSelection(ByVal f As Access.Form)
    Dim values As Variant
    If IsNull(gSelectedEmployee) Or IsEmpty(gSelectedEmployee) Then Exit Sub
    For Each values In gSearchRows
        If CLng(values(0)) = CLng(gSelectedEmployee) Then
            f!lstEmployees = CLng(gSelectedEmployee): f!cmdEdit.Enabled = True: f!cmdExport.Enabled = True
            UiSelectedEmployeeDetails f: Exit Sub
        End If
    Next
    gSelectedEmployee = Null
End Sub
Private Sub FillEditor(ByVal f As Access.Form)
    Dim e As clsEmployeeEdit: Set e = gEditor
    FillCombo f!cboDepartment, "DEPARTMENT", False, e.Department
    FillCombo f!cboStatus, "EMPLOYMENT_STATUS", False, e.Status
    UiSetTextValue f, "txtEmployeeNo", e.EmployeeNo
    f!txtEmployeeNo.Locked = Not IsNull(e.EmployeeId): f!txtEmployeeNo.Enabled = True: f!txtEmployeeNo.TabStop = True
    UiSetTextValue f, "txtEmployeeName", e.Name: UiSetTextValue f, "txtEmployeeKana", e.Kana
    f!cboDepartment = SaveText(e.Department): f!cboStatus = SaveText(e.Status)
    UiSetTextValue f, "txtJoinDate", IIf(e.JoinDate = 0, Null, Format$(e.JoinDate, "yyyy-mm-dd"))
    UiSetTextValue f, "txtSummary", e.Summary: UiSetTextValue f, "txtSkills", e.Skills
    UiSetTextValue f, "txtQualifications", e.Qualifications: UiSetTextValue f, "txtSelfPr", e.SelfPr
    RefreshCareers f: ClearDraft f
    UiState(f).AcceptedPage = 0: UiPageGroup f, 0: f!tabEmployee = 0
    UiRememberCombo f, "cboDepartment": UiRememberCombo f, "cboStatus"
    SyncCareerButtons f
End Sub
Private Sub SyncCareerButtons(ByVal f As Access.Form)
    Dim editing As Boolean, planned As Long
    editing = Not gEditor.ActiveDraft Is Nothing
    planned = gEditor.Careers.Count
    If editing And gCareerIndex = 0 Then planned = planned + 1
    f!cmdAddCareer.Enabled = (planned < 20 And gEditor.Outcome <> "CommitUnknown")
    f!cmdApplyCareer.Enabled = editing And gEditor.Outcome <> "CommitUnknown"
    f!cmdRemoveCareer.Enabled = editing And gCareerIndex > 0 And gEditor.Outcome <> "CommitUnknown"
End Sub
Private Sub ReadEditor(ByVal f As Access.Form)
    With gEditor
        .EmployeeNo = UiRaw(f, "txtEmployeeNo"): .Name = UiRaw(f, "txtEmployeeName"): .Kana = UiRaw(f, "txtEmployeeKana")
        .Department = CStr(Nz(UiAcceptedCode(f, "cboDepartment"), "")): .Status = CStr(Nz(UiAcceptedCode(f, "cboStatus"), "")): .JoinDate = ReadDate(UiRaw(f, "txtJoinDate"), False, False, "入社日", BusinessDate())
        .Summary = UiRaw(f, "txtSummary"): .Skills = UiRaw(f, "txtSkills"): .Qualifications = UiRaw(f, "txtQualifications"): .SelfPr = UiRaw(f, "txtSelfPr")
    End With
End Sub
Private Sub RefreshCareers(ByVal f As Access.Form)
    Dim rows As New Collection, c As clsCareerDraft, i As Long, selected As String
    If gCareerIndex > 0 And gCareerIndex <= gEditor.Careers.Count Then selected = gEditor.Careers(gCareerIndex).TemporaryId
    SortCareers gEditor
    For Each c In gEditor.Careers
        i = i + 1: If c.TemporaryId = selected Then gCareerIndex = i
        rows.Add Array(i, Format$(c.StartMonth, "yyyy-mm"), IIf(IsNull(c.EndMonth), "継続中", Format$(Nz(c.EndMonth, 0), "yyyy-mm")), c.Project)
    Next
    SetRows f!lstCareers, rows
    SyncCareerButtons f
    If Not UiState(f).IsInitializing Then UiUpdateIdentity f
End Sub
Private Sub SortCareers(ByVal e As clsEmployeeEdit)
    Dim ordered As New Collection, c As clsCareerDraft, old As clsCareerDraft, i As Long, before As Boolean, inserted As Boolean
    For Each c In e.Careers
        inserted = False
        For i = 1 To ordered.Count
            Set old = ordered(i): before = (c.StartMonth > old.StartMonth)
            If c.StartMonth = old.StartMonth And Not IsNull(c.PersistentId) Then
                If IsNull(old.PersistentId) Then before = True Else before = CLng(c.PersistentId) > CLng(old.PersistentId)
            End If
            If before Then ordered.Add c, , i: inserted = True: Exit For
        Next
        If Not inserted Then ordered.Add c
    Next
    Set e.Careers = ordered
End Sub
Private Sub ClearDraft(ByVal f As Access.Form)
    Dim names As Variant, name As Variant
    gUiLoading = True
    names = Array("txtStartMonth", "txtEndMonth", "txtCompany", "txtProject", "txtDescription", "txtDuties", "txtAchievements", "txtTechnologies", "txtPhases", "cboRole", "txtTeamSize")
    For Each name In names
        If f.Controls(CStr(name)).ControlType = acTextBox Then UiSetTextValue f, CStr(name), Null Else f.Controls(CStr(name)).Value = Null
        f.Controls(CStr(name)).Enabled = False: f.Controls(CStr(name)).Locked = True: f.Controls(CStr(name)).TabStop = False
    Next
    f!cmdApplyCareer.Enabled = False: f!cmdRemoveCareer.Enabled = False: gUiLoading = False
    SyncCareerButtons f: UiUpdateIdentity f
End Sub
Private Sub FillDraft(ByVal f As Access.Form, ByVal c As clsCareerDraft)
    Dim names As Variant, name As Variant
    gUiLoading = True: UiState(f).DraftReflected = False
    FillCombo f!cboRole, "PROJECT_ROLE", False, c.RoleCode
    names = Array("txtStartMonth", "txtEndMonth", "txtCompany", "txtProject", "txtDescription", "txtDuties", "txtAchievements", "txtTechnologies", "txtPhases", "cboRole", "txtTeamSize")
    For Each name In names: f.Controls(CStr(name)).Enabled = True: f.Controls(CStr(name)).Locked = False: f.Controls(CStr(name)).TabStop = True: Next
    UiSetTextValue f, "txtStartMonth", IIf(c.StartMonth = 0, Null, Format$(c.StartMonth, "yyyy-mm"))
    UiSetTextValue f, "txtEndMonth", IIf(IsNull(c.EndMonth), Null, Format$(Nz(c.EndMonth, 0), "yyyy-mm"))
    UiSetTextValue f, "txtCompany", c.Company: UiSetTextValue f, "txtProject", c.Project
    UiSetTextValue f, "txtDescription", c.Description: UiSetTextValue f, "txtDuties", c.Duties
    UiSetTextValue f, "txtAchievements", c.Achievements: UiSetTextValue f, "txtTechnologies", c.Technologies
    UiSetTextValue f, "txtPhases", c.Phases: f!cboRole = SaveText(c.RoleCode)
    UiSetTextValue f, "txtTeamSize", IIf(c.TeamSize = 0, Null, CStr(c.TeamSize))
    f!cmdApplyCareer.Enabled = True: f!cmdRemoveCareer.Enabled = (gCareerIndex > 0): gDraftDirty = False: gUiLoading = False
    UiRememberCombo f, "cboRole": UiCaptureText f: SyncCareerButtons f: UiUpdateIdentity f
End Sub
Public Sub UiFocusCareer(ByVal f As Access.Form, ByVal ordinal As Long)
    gCareerIndex = ordinal: Set gEditor.ActiveDraft = CloneCareer(gEditor.Careers(ordinal))
    FillDraft f, gEditor.ActiveDraft
End Sub
Private Sub ApplyDraft(ByVal f As Access.Form)
    Dim c As clsCareerDraft, rows As New Collection, i As Long
    If gEditor.ActiveDraft Is Nothing Then Exit Sub
    Set c = CloneCareer(gEditor.ActiveDraft)
    c.StartMonth = ReadDate(UiRaw(f, "txtStartMonth"), True, False, "開始年月", BusinessDate()): c.EndMonth = ReadDate(UiRaw(f, "txtEndMonth"), True, True, "終了年月", BusinessDate())
    c.Company = UiRaw(f, "txtCompany"): c.Project = UiRaw(f, "txtProject"): c.Description = UiRaw(f, "txtDescription"): c.Duties = UiRaw(f, "txtDuties")
    c.Achievements = UiRaw(f, "txtAchievements"): c.Technologies = UiRaw(f, "txtTechnologies"): c.Phases = UiRaw(f, "txtPhases"): c.RoleCode = CStr(Nz(UiAcceptedCode(f, "cboRole"), "")): c.TeamSize = ReadInteger(UiRaw(f, "txtTeamSize"), "チーム人数")
    NormalizeCareer c, BusinessDate()
    If gCareerIndex = 0 Then
        If gEditor.Careers.Count >= 20 Then Reject "MSG-018"
        gEditor.Careers.Add c: gCareerIndex = gEditor.Careers.Count
    Else
        For i = 1 To gEditor.Careers.Count
            If i = gCareerIndex Then rows.Add c Else rows.Add gEditor.Careers(i)
        Next
        Set gEditor.Careers = rows
    End If
    Set gEditor.ActiveDraft = CloneCareer(c): gDraftDirty = False: gDirty = True: UiState(f).DraftReflected = True
    RefreshCareers f
    UiState(f).IsRestoringSelection = True: f!lstCareers = gCareerIndex: UiState(f).IsRestoringSelection = False
    SyncCareerButtons f: UiUpdateIdentity f
End Sub
Public Function UiResolveDraft(ByVal f As Access.Form) As Boolean
    Dim answer As VbMsgBoxResult
    If Not gDraftDirty Then UiResolveDraft = True: Exit Function
    answer = MsgBox(MessageText("MSG-032") & " はい：検査して反映、いいえ：破棄を再確認、キャンセル：入力を続けます。", vbYesNoCancel + vbQuestion + vbDefaultButton3, UiDialogTitle(f, True))
    If answer = vbYes Then ApplyDraft f: UiResolveDraft = True
    If answer = vbNo Then
        If MsgBox(MessageText("MSG-033") & " 現在明細だけが対象です。", vbYesNo + vbQuestion + vbDefaultButton2, UiDialogTitle(f, True)) = vbYes Then
            UiClearPending f, True
            If gCareerIndex > 0 Then
                Set gEditor.ActiveDraft = CloneCareer(gEditor.Careers(gCareerIndex)): FillDraft f, gEditor.ActiveDraft
            Else
                Set gEditor.ActiveDraft = Nothing: ClearDraft f
            End If
            gDraftDirty = False: UiResolveDraft = True
        End If
    End If
End Function
Private Function LoadCodeRows(ByVal f As Access.Form) As Boolean
    Dim result As clsResult, rows As New Collection, row As Variant
    Set result = UiReadCodes(f, CStr(f!cboCategory))
    If result.Kind <> "OK" Then
        Dim emptyRows As New Collection
        SetRows f!lstCodes, emptyRows: f!cmdSave.Enabled = False: f!cmdNew.Enabled = False: f!cmdCancel.Enabled = False
        ShowResult f, result: Exit Function
    End If
    For Each row In result.Value: rows.Add Array(row(0), row(0), row(1), row(2), row(3), row(4)): Next
    SetRows f!lstCodes, rows
    f!cmdNew.Enabled = (CStr(f!cboCategory) <> "EMPLOYMENT_STATUS" And CachedRows(f!lstCodes).Count < 99)
    LoadCodeRows = True
End Function
Private Sub ClearCode(ByVal f As Access.Form)
    gUiLoading = True: Set gCode = Nothing
    UiClearPending f
    UiSetTextValue f, "txtCode", Null: UiSetTextValue f, "txtCodeName", Null
    UiSetTextValue f, "txtSortOrder", Null: f!chkEnabled = False
    f!txtCode.Enabled = False: f!txtCodeName.Enabled = False: f!txtSortOrder.Enabled = False: f!chkEnabled.Enabled = False
    f!cmdSave.Enabled = False: f!cmdCancel.Enabled = False: gDirty = False: gUiLoading = False
    UiState(f).AcceptedListKey = Null: UiUpdateIdentity f
End Sub
Private Sub FillCode(ByVal f As Access.Form)
    Dim allowed As Boolean, names As Variant, name As Variant
    gUiLoading = True: allowed = (gCode.CategoryId <> "EMPLOYMENT_STATUS")
    UiSetTextValue f, "txtCode", gCode.Code: UiSetTextValue f, "txtCodeName", gCode.Name
    UiSetTextValue f, "txtSortOrder", CStr(gCode.SortOrder): f!chkEnabled = gCode.IsEnabled
    names = Array("txtCode", "txtCodeName", "txtSortOrder", "chkEnabled")
    For Each name In names
        f.Controls(CStr(name)).Enabled = True: f.Controls(CStr(name)).Locked = Not allowed: f.Controls(CStr(name)).TabStop = True
    Next
    f!txtCode.Locked = Not gCode.IsNew
    f!cmdSave.Enabled = allowed: f!cmdCancel.Enabled = True: gDirty = False: gUiLoading = False
    UiClearPending f: UiCaptureText f: UiUpdateIdentity f
End Sub
Private Sub ReloadSelectedCode(ByVal f As Access.Form)
    Dim row As Variant
    If gCode Is Nothing Then ClearCode f: Exit Sub
    For Each row In CachedRows(f!lstCodes)
        If CStr(row(0)) = gCode.Code Then
            gCode.Name = row(2): gCode.SortOrder = row(3): gCode.IsEnabled = row(4): gCode.ExpectedRevision = row(5): gCode.IsNew = False
            UiState(f).AcceptedListKey = gCode.Code
            UiState(f).IsRestoringSelection = True: f!lstCodes = gCode.Code: UiState(f).IsRestoringSelection = False
            FillCode f: Exit Sub
        End If
    Next
    ClearCode f
End Sub
