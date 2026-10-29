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
    Dim result As clsResult, rows As New Collection, initialized As Boolean, priorInitialisingForm As String
    On Error GoTo Failed
    priorInitialisingForm = initialisingFormName: initialisingFormName = f.Name
    gUiLoading = True: EnsureSession
    If f.Name = "frmLogin" Then
        f!txtPassword = Null
        If CurrentDb.Properties("SP2_Staging").Value And DCount("*", "m_app_user") = 0 Then
            setupStep = 1: f!txtLoginId = "admin": f!txtLoginId.Locked = True
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
    Case "frmEmployeeSearch"
        FillCombo f!cboDepartment, "DEPARTMENT", True, "", True: FillCombo f!cboStatus, "EMPLOYMENT_STATUS", True, "", True
        If gCriteria Is Nothing Then
            Set gCriteria = New clsSearchCriteria: gCriteria.EmployeeNo = Null: gCriteria.Department = Null: gCriteria.Status = "01"
            Set gSearchRows = New Collection: gSelectedEmployee = Null
        End If
        f!txtEmployeeNo = gCriteria.EmployeeNo: f!txtName = gCriteria.NameRaw: f!cboDepartment = gCriteria.Department: f!cboStatus = gCriteria.Status
        If Not gSearchRaw Is Nothing Then
            f!txtEmployeeNo = gSearchRaw("EmployeeNo"): f!txtName = gSearchRaw("NameRaw")
            f!cboDepartment = gSearchRaw("Department"): f!cboStatus = gSearchRaw("Status")
        End If
        If gSearchRows Is Nothing Then Set gSearchRows = New Collection
        SetRows f!lstEmployees, gSearchRows: f!lblCount.Caption = IIf(gSearchWasExecuted, CStr(gSearchRows.Count) & "件", "未検索")
        f!cmdEdit.Enabled = False: f!cmdExport.Enabled = False
        RestoreEmployeeSelection f
    Case "frmEmployeeEditor"
        If gEditor Is Nothing Then Reject "MSG-020"
        FillEditor f: gDirty = False: gDraftDirty = False: gCareerIndex = 0
    Case "frmCodeMaster"
        rows.Add Array("DEPARTMENT", "部署"): rows.Add Array("EMPLOYMENT_STATUS", "在籍区分"): rows.Add Array("PROJECT_ROLE", "案件役割")
        SetRows f!cboCategory, rows: f!cboCategory = "DEPARTMENT": Set gCode = Nothing
        LoadCodeRows f: ClearCode f
    End Select
    initialized = True
Done:
    initialisingFormName = priorInitialisingForm
    gUiLoading = False
    ' Initial loading uses logical busy protection without moving focus to a
    ' footer on an as-yet unpainted form. Select the first field after setup.
    If initialized Then
        f.Repaint
        Select Case f.Name
        Case "frmLogin"
            If setupStep > 0 Then f!txtPassword.SetFocus Else f!txtLoginId.SetFocus
        Case "frmMenu": f!cmdEmployeeSearch.SetFocus
        Case "frmEmployeeSearch": f!txtEmployeeNo.SetFocus
        Case "frmEmployeeEditor"
            If IsNull(gEditor.EmployeeId) Then f!txtEmployeeNo.SetFocus Else f!txtEmployeeName.SetFocus
        Case "frmCodeMaster": f!cboCategory.SetFocus
        End Select
    End If
    Exit Sub
Failed:
    initialisingFormName = priorInitialisingForm
    gUiLoading = False: Set result = MakeResult("ReadFailure", "MSG-040"): ShowResult f, result
End Sub
Public Sub UiTimer(ByVal f As Access.Form)
    EnsureSession
    If Not gSession.IsAuthenticated Then Exit Sub
    If GetTickCount64() - gSession.LastActivityTick >= 1800000 Then
        gSession.Clear
        If gBusy Then gExportCancel = True Else LogoutNow
    End If
End Sub
Public Sub UiKey(ByVal f As Access.Form, ByRef key As Integer)
    If gBusy Then
        If key = vbKeyEscape And f.Name = "frmEmployeeSearch" Then gExportCancel = True: key = 0
        key = 0
        Exit Sub
    End If
    If f.Name <> "frmLogin" Then
        If Not TouchActivity() Then key = 0: LogoutNow
    End If
End Sub
Public Sub UiMouse(ByVal f As Access.Form)
    If Not gBusy And f.Name <> "frmLogin" Then
        If Not TouchActivity() Then LogoutNow
    End If
End Sub
Public Sub UiChanged(ByVal f As Access.Form, ByVal ctl As String)
    If gUiLoading Then Exit Sub
    If f.Name = "frmEmployeeSearch" Then
        InvalidateSearch f
    ElseIf f.Name = "frmEmployeeEditor" Then
        gDirty = True
        If IsCareerControl(ctl) Then gDraftDirty = True
    ElseIf f.Name = "frmCodeMaster" Then
        gDirty = True
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
    raw = CStr(Nz(f.Controls(name).Value, ""))
    If ScalarLength(raw) > maximum Then GoTo Invalid
    Exit Sub
Invalid:
    cancel = True
    ShowResult f, MakeResult("Validation", "MSG-005", "入力欄（" & CStr(maximum) & "字以内）")
End Sub
Public Sub UiSelected(ByVal f As Access.Form, ByVal ctl As String)
    Dim row As Variant, index As Long, result As clsResult
    On Error GoTo Failed
    If gUiLoading Or gBusy Then Exit Sub
    If f.Name <> "frmLogin" Then If Not TouchActivity() Then LogoutNow: Exit Sub
    Select Case f.Name
    Case "frmEmployeeSearch"
        If ctl = "lstEmployees" Then
            gSelectedEmployee = f!lstEmployees.Value
            f!cmdEdit.Enabled = Not IsNull(gSelectedEmployee): f!cmdExport.Enabled = Not IsNull(gSelectedEmployee)
            If Not IsNull(gSelectedEmployee) Then f!lblSelection.Caption = f!lstEmployees.Column(1) & "  " & f!lstEmployees.Column(2)
        Else
            UiChanged f, ctl
        End If
    Case "frmEmployeeEditor"
        If ctl = "lstCareers" Then
            index = CLng(Nz(f!lstCareers.Value, 0))
            If Not ResolveDraft(f) Then
                gUiLoading = True: f!lstCareers = IIf(gCareerIndex > 0, gCareerIndex, Null): gUiLoading = False: Exit Sub
            End If
            If index > 0 And index <= gEditor.Careers.Count Then
                gCareerIndex = index: Set gEditor.ActiveDraft = CloneCareer(gEditor.Careers(index)): FillDraft f, gEditor.ActiveDraft
            End If
        ElseIf ctl = "tabEmployee" Then
            If Not ResolveDraft(f) Then gUiLoading = True: f!tabEmployee.Value = 1: gUiLoading = False
            SyncCareerButtons f
        Else
            UiChanged f, ctl
        End If
    Case "frmCodeMaster"
        If ctl = "cboCategory" Then
            If Not ConfirmDiscard() Then
                gUiLoading = True: If Not gCode Is Nothing Then f!cboCategory = gCode.CategoryId
                gUiLoading = False: Exit Sub
            End If
            LoadCodeRows f: ClearCode f
        ElseIf ctl = "lstCodes" Then
            If Not ConfirmDiscard() Then
                If Not gCode Is Nothing Then gUiLoading = True: f!lstCodes = gCode.Code: gUiLoading = False
                Exit Sub
            End If
            index = f!lstCodes.ListIndex
            If index >= 0 Then
                row = CachedRows(f!lstCodes)(index + 1)
                Set gCode = New clsCodeEdit: gCode.CategoryId = f!cboCategory: gCode.Code = row(0): gCode.Name = row(1)
                gCode.SortOrder = row(2): gCode.IsEnabled = row(3): gCode.ExpectedRevision = row(4): gCode.IsNew = False
                FillCode f
            End If
        Else
            gDirty = True
        End If
    End Select
    Exit Sub
Failed:
    ShowResult f, MakeResult("Validation", "MSG-040")
End Sub
Public Sub UiAction(ByVal f As Access.Form, ByVal action As String)
    Dim result As clsResult, e As clsEmployeeEdit, index As Long, id As Variant, text As String, category As String
    On Error GoTo Failed
    If gBusy Then ShowResult f, MakeResult("Busy", "MSG-029"): Exit Sub
    If action = "cmdExit" Then EnsureSession: gSession.Clear: Application.Quit acQuitSaveNone: Exit Sub
    If action = "cmdLogout" Then LogoutNow: Exit Sub
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
        f!txtPassword = Null
        If result.Kind = "OK" Then Navigate f, "frmMenu" Else ShowResult f, result
    Case "frmMenu"
        Set result = UiAuthorize(f, IIf(action = "cmdCodeMaster", "ADMIN", "STAFF"))
        If result.Kind <> "OK" Then ShowResult f, result: GoTo Done
        If action = "cmdEmployeeSearch" Then Set gCriteria = Nothing: Set gSearchRaw = Nothing: gSearchWasExecuted = False: Set gSearchRows = Nothing: Navigate f, "frmEmployeeSearch"
        If action = "cmdCodeMaster" Then Navigate f, "frmCodeMaster"
    Case "frmEmployeeSearch"
        Select Case action
        Case "cmdSearch": ExecuteSearch f
        Case "cmdClear"
            gUiLoading = True: f!txtEmployeeNo = Null: f!txtName = Null: f!cboDepartment = Null: f!cboStatus = "01": gUiLoading = False
            InvalidateSearch f
        Case "cmdMenu": Set gCriteria = Nothing: Set gSearchRaw = Nothing: gSearchWasExecuted = False: Set gSearchRows = Nothing: Navigate f, "frmMenu"
        Case "cmdNew", "cmdEdit"
            CaptureSearchRaw f
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
            If Not ResolveDraft(f) Then GoTo Done
            If gEditor.Careers.Count >= 20 Then Reject "MSG-018"
            Set gEditor.ActiveDraft = New clsCareerDraft: gCareerIndex = 0
            FillDraft f, gEditor.ActiveDraft: gDraftDirty = True: gDirty = True: f!txtStartMonth.SetFocus
        Case "cmdApplyCareer": ApplyDraft f
        Case "cmdRemoveCareer"
            If gCareerIndex < 1 Or gCareerIndex > gEditor.Careers.Count Then Reject "MSG-025"
            If MsgBox(MessageText("MSG-031"), vbYesNo + vbQuestion + vbDefaultButton2) <> vbYes Then GoTo Done
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
                If ExecuteSearch(Forms("frmEmployeeSearch")) Then
                    ShowResult Forms("frmEmployeeSearch"), MakeResult("OK", "MSG-014")
                Else
                    Forms("frmEmployeeSearch")!lblSelection.Caption = MessageText("MSG-014") & vbCrLf & MessageText("MSG-040")
                End If
            End If
        Case "cmdCancel"
            If gEditor.Outcome = "CommitUnknown" Then
                ShowResult f, MakeResult("CommitUnknown", "MSG-034")
                If MsgBox(MessageText("MSG-015"), vbYesNo + vbQuestion + vbDefaultButton2) <> vbYes Then GoTo Done
            ElseIf Not ConfirmDiscard() Then
                GoTo Done
            End If
            gDirty = False: gDraftDirty = False: Navigate f, "frmEmployeeSearch"
        End Select
    Case "frmCodeMaster"
        If f.Tag = "CommitUnknown" Then
            ShowResult f, MakeResult("CommitUnknown", "MSG-034")
            If action <> "cmdCancel" Then GoTo Done
            If MsgBox(MessageText("MSG-015"), vbYesNo + vbQuestion + vbDefaultButton2) <> vbYes Then GoTo Done
            f.Tag = "": LoadCodeRows f: ReloadSelectedCode f: GoTo Done
        End If
        Select Case action
        Case "cmdNew"
            If Not ConfirmDiscard() Then GoTo Done
            category = CStr(f!cboCategory)
            If category = "EMPLOYMENT_STATUS" Then Reject "MSG-023"
            If CachedRows(f!lstCodes).Count >= 99 Then Reject "MSG-024"
            Set gCode = New clsCodeEdit: gCode.CategoryId = category: FillCode f: f!txtCode.SetFocus
        Case "cmdSave"
            If gCode Is Nothing Then Reject "MSG-016"
            If Not gCode.IsNew Then
                If gCode.IsEnabled And Not CBool(Nz(f!chkEnabled, False)) Then
                    If MsgBox(MessageText("MSG-038"), vbYesNo + vbQuestion + vbDefaultButton2) <> vbYes Then GoTo Done
                End If
            End If
            gCode.Code = CStr(Nz(f!txtCode, "")): gCode.Name = CStr(Nz(f!txtCodeName, "")): gCode.SortOrder = ReadInteger(f!txtSortOrder, "並び順"): gCode.IsEnabled = CBool(Nz(f!chkEnabled, False))
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
            If Not ConfirmDiscard() Then GoTo Done
            If gCode Is Nothing Then GoTo Done
            If gCode.IsNew Then ClearCode f Else LoadCodeRows f: ReloadSelectedCode f
        Case "cmdMenu"
            If Not ConfirmDiscard() Then GoTo Done
            gDirty = False: Navigate f, "frmMenu"
        End Select
    End Select
Done:
    gBusy = False: Exit Sub
Failed:
    text = Err.Description: gUiLoading = False: gBusy = False
    If f.Name = "frmLogin" Then f!txtPassword = Null
    Set result = Failure(text, Nothing, True): ShowResult f, result
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
            setupAdmin = password: setupStep = 3: f!txtLoginId = "staff": f!lblMessage.Caption = "staff のパスワードを入力してください。"
        Else
            setupStaff = password
            overlay.Acquire f: initialized = InitializeDemo(setupAdmin, setupStaff): overlay.Restore
            If initialized Then
                setupStep = 0: setupAdmin = "": setupStaff = "": setupFirst = ""
                f!txtLoginId.Locked = False: f!txtLoginId = Null: f!lblMessage.Caption = "初期設定が完了しました。配布前検査を行ってください。"
            End If
        End If
    End If
    f!txtPassword = Null: password = ""
End Sub
Public Sub UiUnload(ByVal f As Access.Form, ByRef cancel As Integer)
    If gAllowClose Then Exit Sub
    If gBusy Then cancel = True: If f.Name = "frmEmployeeSearch" Then gExportCancel = True
    If gBusy Then Exit Sub
    If f.Name = "frmEmployeeEditor" Or f.Name = "frmCodeMaster" Then
        If Not ConfirmDiscard() Then cancel = True
    End If
End Sub
Public Sub UiClosed(ByVal f As Access.Form)
    DetachRows f.Name
    If f.Name = "frmLogin" Then setupFirst = "": setupAdmin = "": setupStaff = ""
End Sub
Private Sub InvalidateSearch(ByVal f As Access.Form)
    Dim rows As New Collection
    Set gSearchRows = rows: gSelectedEmployee = Null
    gSearchWasExecuted = False
    SetRows f!lstEmployees, rows: f!lstEmployees = Null: f!lblCount.Caption = "未検索": f!lblSelection.Caption = "条件が変更されました。検索してください。"
    f!cmdEdit.Enabled = False: f!cmdExport.Enabled = False
End Sub
Private Function SelectedId(ByVal f As Access.Form) As Long
    If IsNull(f!lstEmployees) Or gSearchRows Is Nothing Then Reject "MSG-011"
    If f!lstEmployees.ListIndex < 0 Or gSearchRows.Count = 0 Then Reject "MSG-011"
    SelectedId = CLng(f!lstEmployees.Value)
End Function
Private Function ExecuteSearch(ByVal f As Access.Form) As Boolean
    Dim result As clsResult
    CaptureSearchRaw f
    Set gCriteria = New clsSearchCriteria
    gCriteria.EmployeeNo = SaveText(f!txtEmployeeNo): gCriteria.NameRaw = CStr(Nz(f!txtName, "")): gCriteria.Department = f!cboDepartment: gCriteria.Status = f!cboStatus
    Set result = UiSearch(f, gCriteria)
    If result.Kind <> "OK" Then InvalidateSearch f: ShowResult f, result: Exit Function
    Set gSearchRows = result.Value: SetRows f!lstEmployees, gSearchRows: f!lblCount.Caption = CStr(gSearchRows.Count) & "件"
    gSearchWasExecuted = True
    f!cmdEdit.Enabled = False: f!cmdExport.Enabled = False: RestoreEmployeeSelection f: ShowResult f, result
    ExecuteSearch = True
End Function
Private Sub CaptureSearchRaw(ByVal f As Access.Form)
    Set gSearchRaw = CreateObject("Scripting.Dictionary")
    gSearchRaw.Add "EmployeeNo", f!txtEmployeeNo.Value: gSearchRaw.Add "NameRaw", f!txtName.Value
    gSearchRaw.Add "Department", f!cboDepartment.Value: gSearchRaw.Add "Status", f!cboStatus.Value
End Sub
Private Sub RestoreEmployeeSelection(ByVal f As Access.Form)
    Dim values As Variant
    If IsNull(gSelectedEmployee) Or IsEmpty(gSelectedEmployee) Then Exit Sub
    For Each values In gSearchRows
        If CLng(values(0)) = CLng(gSelectedEmployee) Then
            f!lstEmployees = CLng(gSelectedEmployee): f!cmdEdit.Enabled = True: f!cmdExport.Enabled = True
            f!lblSelection.Caption = CStr(values(1)) & "  " & CStr(values(2)): Exit Sub
        End If
    Next
    gSelectedEmployee = Null
End Sub
Private Sub FillEditor(ByVal f As Access.Form)
    Dim e As clsEmployeeEdit: Set e = gEditor
    FillCombo f!cboDepartment, "DEPARTMENT", False, e.Department
    FillCombo f!cboStatus, "EMPLOYMENT_STATUS", False, e.Status
    f!txtEmployeeNo = e.EmployeeNo: f!txtEmployeeNo.Locked = Not IsNull(e.EmployeeId): f!txtEmployeeNo.Enabled = True: f!txtEmployeeNo.TabStop = IsNull(e.EmployeeId)
    f!txtEmployeeName = e.Name: f!txtEmployeeKana = e.Kana: f!cboDepartment = SaveText(e.Department): f!cboStatus = SaveText(e.Status)
    f!txtJoinDate = IIf(e.JoinDate = 0, Null, Format$(e.JoinDate, "yyyy-mm-dd"))
    f!txtSummary = e.Summary: f!txtSkills = e.Skills: f!txtQualifications = e.Qualifications: f!txtSelfPr = e.SelfPr
    RefreshCareers f: ClearDraft f: f!tabEmployee = 0
    SyncCareerButtons f
End Sub
Private Sub SyncCareerButtons(ByVal f As Access.Form)
    Dim editing As Boolean
    editing = Not gEditor.ActiveDraft Is Nothing
    f!cmdApplyCareer.Enabled = editing And gEditor.Outcome <> "CommitUnknown"
    f!cmdRemoveCareer.Enabled = editing And gCareerIndex > 0 And gEditor.Outcome <> "CommitUnknown"
End Sub
Private Sub ReadEditor(ByVal f As Access.Form)
    With gEditor
        .EmployeeNo = CStr(Nz(f!txtEmployeeNo, "")): .Name = CStr(Nz(f!txtEmployeeName, "")): .Kana = CStr(Nz(f!txtEmployeeKana, ""))
        .Department = CStr(Nz(f!cboDepartment, "")): .Status = CStr(Nz(f!cboStatus, "")): .JoinDate = ReadDate(f!txtJoinDate, False, False, "入社日", BusinessDate())
        .Summary = f!txtSummary: .Skills = f!txtSkills: .Qualifications = f!txtQualifications: .SelfPr = f!txtSelfPr
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
    f!cmdAddCareer.Enabled = (gEditor.Careers.Count < 20 And gEditor.Outcome <> "CommitUnknown")
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
    For Each name In names: f.Controls(CStr(name)).Value = Null: f.Controls(CStr(name)).Enabled = False: Next
    f!cmdApplyCareer.Enabled = False: f!cmdRemoveCareer.Enabled = False: gUiLoading = False
End Sub
Private Sub FillDraft(ByVal f As Access.Form, ByVal c As clsCareerDraft)
    Dim names As Variant, name As Variant
    gUiLoading = True
    FillCombo f!cboRole, "PROJECT_ROLE", False, c.RoleCode
    names = Array("txtStartMonth", "txtEndMonth", "txtCompany", "txtProject", "txtDescription", "txtDuties", "txtAchievements", "txtTechnologies", "txtPhases", "cboRole", "txtTeamSize")
    For Each name In names: f.Controls(CStr(name)).Enabled = True: Next
    f!txtStartMonth = IIf(c.StartMonth = 0, Null, Format$(c.StartMonth, "yyyy-mm")): f!txtEndMonth = IIf(IsNull(c.EndMonth), Null, Format$(Nz(c.EndMonth, 0), "yyyy-mm"))
    f!txtCompany = c.Company: f!txtProject = c.Project: f!txtDescription = c.Description: f!txtDuties = c.Duties: f!txtAchievements = c.Achievements
    f!txtTechnologies = c.Technologies: f!txtPhases = c.Phases: f!cboRole = SaveText(c.RoleCode): f!txtTeamSize = IIf(c.TeamSize = 0, Null, CStr(c.TeamSize))
    f!cmdApplyCareer.Enabled = True: f!cmdRemoveCareer.Enabled = (gCareerIndex > 0): gDraftDirty = False: gUiLoading = False
End Sub
Public Sub UiFocusCareer(ByVal f As Access.Form, ByVal ordinal As Long)
    gCareerIndex = ordinal: Set gEditor.ActiveDraft = CloneCareer(gEditor.Careers(ordinal))
    FillDraft f, gEditor.ActiveDraft
End Sub
Private Sub ApplyDraft(ByVal f As Access.Form)
    Dim c As clsCareerDraft, rows As New Collection, i As Long
    If gEditor.ActiveDraft Is Nothing Then Exit Sub
    Set c = CloneCareer(gEditor.ActiveDraft)
    c.StartMonth = ReadDate(f!txtStartMonth, True, False, "開始年月", BusinessDate()): c.EndMonth = ReadDate(f!txtEndMonth, True, True, "終了年月", BusinessDate())
    c.Company = CStr(Nz(f!txtCompany, "")): c.Project = CStr(Nz(f!txtProject, "")): c.Description = CStr(Nz(f!txtDescription, "")): c.Duties = CStr(Nz(f!txtDuties, ""))
    c.Achievements = f!txtAchievements: c.Technologies = f!txtTechnologies: c.Phases = f!txtPhases: c.RoleCode = CStr(Nz(f!cboRole, "")): c.TeamSize = ReadInteger(f!txtTeamSize, "チーム人数")
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
    Set gEditor.ActiveDraft = CloneCareer(c): gDraftDirty = False: gDirty = True
    RefreshCareers f: f!lstCareers = gCareerIndex
End Sub
Private Function ResolveDraft(ByVal f As Access.Form) As Boolean
    Dim answer As VbMsgBoxResult
    If Not gDraftDirty Then ResolveDraft = True: Exit Function
    answer = MsgBox(MessageText("MSG-032"), vbYesNoCancel + vbQuestion)
    If answer = vbYes Then ApplyDraft f: ResolveDraft = True
    If answer = vbNo Then
        If MsgBox(MessageText("MSG-033"), vbYesNo + vbQuestion + vbDefaultButton2) = vbYes Then
            gDraftDirty = False: ResolveDraft = True
        End If
    End If
End Function
Private Function LoadCodeRows(ByVal f As Access.Form) As Boolean
    Dim result As clsResult
    Set result = UiReadCodes(f, CStr(f!cboCategory))
    If result.Kind <> "OK" Then
        Dim emptyRows As New Collection
        SetRows f!lstCodes, emptyRows: f!cmdSave.Enabled = False: f!cmdNew.Enabled = False: f!cmdCancel.Enabled = False
        ShowResult f, result: Exit Function
    End If
    SetRows f!lstCodes, result.Value
    f!cmdNew.Enabled = (CStr(f!cboCategory) <> "EMPLOYMENT_STATUS" And CachedRows(f!lstCodes).Count < 99)
    LoadCodeRows = True
End Function
Private Sub ClearCode(ByVal f As Access.Form)
    gUiLoading = True: Set gCode = Nothing
    f!txtCode = Null: f!txtCodeName = Null: f!txtSortOrder = Null: f!chkEnabled = False
    f!txtCode.Enabled = False: f!txtCodeName.Enabled = False: f!txtSortOrder.Enabled = False: f!chkEnabled.Enabled = False
    f!cmdSave.Enabled = False: f!cmdCancel.Enabled = False: gDirty = False: gUiLoading = False
End Sub
Private Sub FillCode(ByVal f As Access.Form)
    Dim allowed As Boolean
    gUiLoading = True: allowed = gCode.CategoryId <> "EMPLOYMENT_STATUS"
    f!txtCode = gCode.Code: f!txtCodeName = gCode.Name: f!txtSortOrder = CStr(gCode.SortOrder): f!chkEnabled = gCode.IsEnabled
    f!txtCode.Enabled = allowed: f!txtCode.Locked = Not gCode.IsNew: f!txtCode.TabStop = gCode.IsNew And allowed
    f!txtCodeName.Enabled = allowed: f!txtSortOrder.Enabled = allowed: f!chkEnabled.Enabled = allowed
    f!cmdSave.Enabled = allowed: f!cmdCancel.Enabled = True: gDirty = False: gUiLoading = False
End Sub
Private Sub ReloadSelectedCode(ByVal f As Access.Form)
    Dim row As Variant
    If gCode Is Nothing Then ClearCode f: Exit Sub
    For Each row In CachedRows(f!lstCodes)
        If CStr(row(0)) = gCode.Code Then
            gCode.Name = row(1): gCode.SortOrder = row(2): gCode.IsEnabled = row(3): gCode.ExpectedRevision = row(4): gCode.IsNew = False
            f!lstCodes = gCode.Code: FillCode f: Exit Sub
        End If
    Next
    ClearCode f
End Sub
