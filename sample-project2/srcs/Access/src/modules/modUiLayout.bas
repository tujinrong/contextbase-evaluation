Option Compare Binary
Option Explicit
Private Declare PtrSafe Function GetDC Lib "user32" (ByVal hwnd As LongPtr) As LongPtr
Private Declare PtrSafe Function ReleaseDC Lib "user32" (ByVal hwnd As LongPtr, ByVal dc As LongPtr) As Long
Private Declare PtrSafe Function GetDeviceCaps Lib "gdi32" (ByVal dc As LongPtr, ByVal index As Long) As Long
Private Declare PtrSafe Function CreateFontW Lib "gdi32" (ByVal height As Long, ByVal width As Long, ByVal escapement As Long, ByVal orientation As Long, ByVal weight As Long, ByVal italic As Long, ByVal underline As Long, ByVal strikeout As Long, ByVal charset As Long, ByVal outputPrecision As Long, ByVal clipPrecision As Long, ByVal quality As Long, ByVal pitch As Long, ByVal face As LongPtr) As LongPtr
Private Declare PtrSafe Function SelectObject Lib "gdi32" (ByVal dc As LongPtr, ByVal value As LongPtr) As LongPtr
Private Declare PtrSafe Function DeleteObject Lib "gdi32" (ByVal value As LongPtr) As Long
Private Type UI_TEXT_SIZE
    cx As Long
    cy As Long
End Type
Private Declare PtrSafe Function GetTextExtentPoint32W Lib "gdi32" (ByVal dc As LongPtr, ByVal text As LongPtr, ByVal length As Long, ByRef size As UI_TEXT_SIZE) As Long
Private Function CaptionWidth(ByVal text As String) As Long
    Dim dc As LongPtr, font As LongPtr, old As LongPtr, dpi As Long, face As String, size As UI_TEXT_SIZE
    On Error GoTo Cleanup
    dc = GetDC(0): If dc = 0 Then Exit Function
    dpi = GetDeviceCaps(dc, 90): If dpi < 1 Then GoTo Cleanup
    face = "Yu Gothic UI"
    font = CreateFontW(-CLng(11# * dpi / 72#), 0, 0, 0, 400, 0, 0, 0, 1, 0, 0, 0, 0, StrPtr(face))
    If font = 0 Then GoTo Cleanup
    old = SelectObject(dc, font)
    If GetTextExtentPoint32W(dc, StrPtr(text), Len(text), size) <> 0 Then CaptionWidth = CLng(size.cx * 1440# / dpi)
Cleanup:
    If old <> 0 Then SelectObject dc, old
    If font <> 0 Then DeleteObject font
    If dc <> 0 Then ReleaseDC 0, dc
End Function
Public Sub UiResize(ByVal f As Access.Form)
    Dim s As clsFormUiState, available As Long, delta As Long, titleWidth As Long
    Set s = UiState(f)
    If s.IsResizing Then Exit Sub
    On Error GoTo Failed
    s.IsResizing = True: available = f.InsideWidth - 720
    If available < 3000 Then GoTo Finished
    If f.Name = "frmLogin" Then
        titleWidth = IIf(available < 6200, available, 6200)
        f!lblScreenTitle.Width = titleWidth: f!lblLoginHelp.Width = titleWidth
        f!lblScreenTitle.Left = IIf(f.InsideWidth - titleWidth - 360 < 6345, f.InsideWidth - titleWidth - 360, 6345)
        f!lblLoginHelp.Left = f!lblScreenTitle.Left
        GoTo Finished
    End If
    f!lblScreenTitle.Width = IIf(available < 18180, available, 18180)
    Select Case f.Name
    Case "frmMenu"
        f!lblActor.Width = IIf(available < 15000, available, 15000)
    Case "frmEmployeeSearch"
        f!cmdMenu.Left = f.InsideWidth - 360 - f!cmdMenu.Width
        f!lblScreenTitle.Width = f!cmdMenu.Left - 540
    Case "frmEmployeeEditor"
        f!lblEmployeeIdentity.Width = IIf(available < 18180, available, 18180)
        If CaptionWidth(f!lblEmployeeIdentity.Caption) + 120 > f!lblEmployeeIdentity.Width Then delta = 330
        f!lblEmployeeIdentity.Height = 330 + delta
        f!tabEmployee.Top = 1365 + delta: f!tabEmployee.Width = IIf(available < 18180, available, 18180)
        f.Section(acHeader).Height = 2400 + delta: f.Section(acDetail).Height = 7920
        f!cmdCancel.Left = f.InsideWidth - 360 - f!cmdCancel.Width
        f!cmdSave.Left = f!cmdCancel.Left - 180 - f!cmdSave.Width
        If f!cmdSave.Left > 540 Then f!lblSaveScope.Width = IIf(f!cmdSave.Left - 540 < 10800, f!cmdSave.Left - 540, 10800)
    Case "frmCodeMaster"
        f!cmdMenu.Left = f.InsideWidth - 360 - f!cmdMenu.Width
        f!lblScreenTitle.Width = f!cmdMenu.Left - 540
        f!lblCodeIdentity.Width = IIf(available < 18180, available, 18180)
    End Select
Finished:
    s.IsResizing = False
    Exit Sub
Failed:
    s.LayoutFailure = CStr(Err.Number) & ": " & Err.Description
    s.IsResizing = False
End Sub
Public Sub UiActivate(ByVal f As Access.Form)
    Dim s As clsFormUiState, target As String: Set s = UiState(f)
    On Error GoTo Failed
    If s.Activated Or s.IsInitializing Then Exit Sub
    s.Activated = True
    UiResize f
    f.GoToPage 1, 0, 0
    Select Case f.Name
    Case "frmLogin": If f!txtLoginId.Locked Then f!txtPassword.SetFocus Else f!txtLoginId.SetFocus
    Case "frmMenu": f!cmdEmployeeSearch.SetFocus
    Case "frmEmployeeSearch"
        UiSyncPendingEditors f
        If Not gSearchReturn Is Nothing Then
            If gSearchReturn.FocusControl <> "" Then
                target = UiEffectiveFocus(f, gSearchReturn.FocusControl)
                If f.Controls(target).Visible And f.Controls(target).Enabled Then
                    f.Controls(target).SetFocus
                Else
                    f!txtEmployeeNo.SetFocus
                End If
            Else
                f!txtEmployeeNo.SetFocus
            End If
            ' Activate precedes Current/GotFocus and the native OGrid may not yet
            ' be visible. Restore only after this event returns to Access.
            UiQueueViewportRestore f, gSearchReturn
        Else
            f!txtEmployeeNo.SetFocus
        End If
    Case "frmEmployeeEditor": If IsNull(gEditor.EmployeeId) Then f!txtEmployeeNo.SetFocus Else f!txtEmployeeName.SetFocus
    Case "frmCodeMaster": f!cboCategory.SetFocus
    End Select
    Exit Sub
Failed:
    UiRecordLayoutFailure f, "ACTIVATE", Err.Number, Err.Description
End Sub
Public Sub UiRecordLayoutFailure(ByVal f As Access.Form, ByVal stage As String, ByVal number As Long, ByVal description As String)
    ' Record an actual display failure without discarding raw/accepted/Pending
    ' state or leaking an unhandled VBA dialog into normal navigation.
    On Error Resume Next
    UiState(f).LayoutFailure = stage & "|" & CStr(number) & "|" & description
    If f.Name = "frmEmployeeSearch" Then
        f!lblSelection.Caption = MessageText("MSG-040") & " 入力表示を復元できませんでした。原入力は保持しています。"
    Else
        f!lblMessage.Caption = MessageText("MSG-040") & " 入力表示を復元できませんでした。原入力は保持しています。"
    End If
End Sub
Public Sub UiPageGroup(ByVal f As Access.Form, ByVal page As Integer)
    Dim ctl As Control
    For Each ctl In f.Controls
        If Left$(ctl.Tag, 5) = "PAGE:" And Not UiIsPendingPhysical(ctl.Name) Then ctl.Visible = (ctl.Tag = "PAGE:" & CStr(page))
    Next
    UiSyncPendingEditors f
End Sub
Public Sub UiFocusTabHeader(ByVal f As Access.Form)
    Dim tabs As Access.TabControl, index As Integer
    If UiIsInitialisingForm(f) Or UiState(f).IsInitializing Or Not UiState(f).Activated Then Exit Sub
    Set tabs = f!tabEmployee
    index = tabs.Value
    If Not tabs.Visible Or Not tabs.Enabled Then Err.Raise 5, "SP2.UiFocusTabHeader", "The tab header is unavailable."
    If index < 0 Or index >= tabs.Pages.Count Then Err.Raise 5, "SP2.UiFocusTabHeader", "The active page is invalid."
    ' Access TabControl has no SetFocus method. Its active Page does.
    tabs.Pages(index).SetFocus
End Sub
Public Sub UiForcePage(ByVal f As Access.Form, ByVal page As Integer)
    Dim s As clsFormUiState, number As Long, description As String
    Set s = UiState(f): On Error GoTo Failed
    s.IsSwitchingPage = True
    UiFocusTabHeader f
    UiPageGroup f, page
    s.AcceptedPage = page: f!tabEmployee.Value = page
    s.IsSwitchingPage = False: Exit Sub
Failed:
    number = Err.Number: description = Err.Description: s.IsSwitchingPage = False
    Err.Raise number, , description
End Sub
Public Sub UiSwitchPage(ByVal f As Access.Form)
    Dim s As clsFormUiState, requested As Integer, errorText As String
    Set s = UiState(f)
    If s.IsSwitchingPage Or s.IsInitializing Or gUiLoading Then Exit Sub
    requested = f!tabEmployee.Value
    If requested = s.AcceptedPage Then Exit Sub
    On Error GoTo Failed
    s.IsSwitchingPage = True: f!tabEmployee.Value = s.AcceptedPage
    UiCaptureText f
    If gBusy Then GoTo Declined
    UiRequireNoPending f
    If Not UiResolveDraft(f) Then GoTo Declined
    UiFocusTabHeader f
    UiPageGroup f, requested
    s.AcceptedPage = requested: f!tabEmployee.Value = requested
    f.GoToPage 1, 0, 0
    If requested = 0 Then
        If IsNull(gEditor.EmployeeId) Then f!txtEmployeeNo.SetFocus Else f!txtEmployeeName.SetFocus
    Else
        If gEditor.Careers.Count = 0 Then f!cmdAddCareer.SetFocus Else f!lstCareers.SetFocus
    End If
    s.IsSwitchingPage = False: Exit Sub
Declined:
    If s.LastEditFocus <> "" Then
        If f.Controls(s.LastEditFocus).Visible And f.Controls(s.LastEditFocus).Enabled Then f.Controls(s.LastEditFocus).SetFocus
    End If
    UiRestoreFirstPending f
    s.IsSwitchingPage = False: Exit Sub
Failed:
    errorText = Err.Description: s.IsSwitchingPage = False
    Err.Raise vbObjectError + 731, "SP2.UiSwitchPage", errorText
End Sub
Public Sub UiRestoreFirstPending(ByVal f As Access.Form)
    Dim s As clsFormUiState, key As Variant: Set s = UiState(f)
    UiSyncPendingEditors f
    For Each key In UiPendingOwners(f)
        If s.Pending.Exists(CStr(key)) Then
            If f.Name = "frmEmployeeEditor" And Not f.Controls(CStr(key)).Visible Then
                UiForcePage f, IIf(CStr(key) = "cboRole", 1, 0)
            End If
            UiBindPendingEditor f, CStr(key), True: Exit Sub
        End If
    Next
End Sub
Public Sub UiArmDeferredTimer(ByVal f As Access.Form, ByVal interval As Long)
    Dim s As clsFormUiState: Set s = UiState(f)
    If Not s.DeferredTimerOwned Then
        s.OriginalTimerInterval = f.TimerInterval: s.DeferredTimerOwned = True
    End If
    If f.TimerInterval = 0 Or f.TimerInterval > interval Then f.TimerInterval = interval
End Sub
Private Sub UiFinishDeferredTimer(ByVal f As Access.Form)
    Dim s As clsFormUiState: Set s = UiState(f)
    If Not s.DeferredTimerOwned Then Exit Sub
    If s.RestorePendingControl <> "" Or Not s.ViewportRestoreState Is Nothing Then Exit Sub
    f.TimerInterval = s.OriginalTimerInterval: s.DeferredTimerOwned = False
End Sub
Public Sub UiQueueViewportRestore(ByVal f As Access.Form, ByVal state As clsSearchReturnState)
    Dim s As clsFormUiState: Set s = UiState(f)
    If state Is Nothing Then Exit Sub
    If state.ViewportPositionStatus = "NO_ROWS" Then Exit Sub
    Set s.ViewportRestoreState = state: s.ViewportRestoreAttempts = 0
    UiArmDeferredTimer f, 50
End Sub
Public Sub UiCancelViewportRestore(ByVal f As Access.Form)
    Dim s As clsFormUiState: Set s = UiState(f)
    If Not s.ViewportRestoreState Is Nothing Then
        s.ViewportRestoreState.ViewportPositionStatus = "RESTORE_SUPERSEDED"
        Set s.ViewportRestoreState = Nothing
    End If
    UiFinishDeferredTimer f
End Sub
Public Sub UiCancelDeferredPending(ByVal f As Access.Form)
    Dim s As clsFormUiState: Set s = UiState(f)
    ' Supersede only the display job; the original Pending/accepted/raw survives.
    s.RestorePendingControl = "": s.RestorePendingPhase = 0
    UiFinishDeferredTimer f
End Sub
Public Sub UiDeferredWork(ByVal f As Access.Form)
    Dim s As clsFormUiState, name As String, rows As Collection, done As Boolean, number As Long, description As String
    Set s = UiState(f)
    If Not s.DeferredTimerOwned Or s.DeferredWorkRunning Then Exit Sub
    On Error GoTo Failed
    s.DeferredWorkRunning = True
    If Not s.ViewportRestoreState Is Nothing Then
        ' A new Search/Clear/condition change or a new return snapshot supersedes
        ' this request. Never append an old warning to the new search result.
        If gSearchReturn Is Nothing Then
            UiCancelViewportRestore f
        ElseIf Not (gSearchReturn Is s.ViewportRestoreState) Then
            UiCancelViewportRestore f
        Else
            Set rows = CachedRows(f!lstEmployees)
            If Not (rows Is s.ViewportRestoreState.ResultRows) Then UiCancelViewportRestore f
        End If
    End If
    If s.RestorePendingControl <> "" Then
        name = s.RestorePendingControl
        s.RestorePendingAttempts = s.RestorePendingAttempts + 1
        If s.IsInitializing Or s.IsUnloading Or gBusy Then
            If s.RestorePendingAttempts >= 3 Then
                UiRecordLayoutFailure f, "PENDING_FORM_NOT_READY", 5, "Pending display was not ready within three Timer events."
                s.RestorePendingControl = ""
            End If
        ElseIf Not s.Pending.Exists(name) Then
            s.RestorePendingControl = ""
        Else
            done = UiRestorePending(f, name)
            s.RestorePendingControl = "": s.RestorePendingPhase = 0
        End If
        If s.RestorePendingControl <> "" Then GoTo Finished
    End If
    If Not s.ViewportRestoreState Is Nothing Then
        s.ViewportRestoreAttempts = s.ViewportRestoreAttempts + 1
        If s.IsInitializing Or s.IsUnloading Or gBusy Then
            If s.ViewportRestoreAttempts >= 3 Then
                s.ViewportRestoreState.ViewportPositionStatus = "RESTORE_UNAVAILABLE:FORM_NOT_READY"
                f!lblSelection.Caption = f!lblSelection.Caption & " ／ 一覧位置は未復帰です。選択・検索条件は保持しています。"
                Set s.ViewportRestoreState = Nothing
            End If
        Else
            f.Repaint
            done = UiRestoreEmployeeViewport(f, s.ViewportRestoreState, s.ViewportRestoreAttempts < 3)
            If done Then Set s.ViewportRestoreState = Nothing
        End If
    End If
Finished:
    s.DeferredWorkRunning = False
    If s.RestorePendingControl = "" And s.ViewportRestoreState Is Nothing Then
        UiFinishDeferredTimer f
    Else
        f.TimerInterval = 50
    End If
    Exit Sub
Failed:
    number = Err.Number: description = Err.Description
    s.IsRestoringSelection = False
    UiRecordLayoutFailure f, "DEFERRED", number, description
    If Not s.ViewportRestoreState Is Nothing Then
        s.ViewportRestoreState.ViewportPositionStatus = "RESTORE_UNAVAILABLE:DEFERRED_ERROR_" & CStr(number)
        Set s.ViewportRestoreState = Nothing
        f!lblSelection.Caption = f!lblSelection.Caption & " ／ 一覧位置は未復帰です。選択・検索条件は保持しています。"
    End If
    s.RestorePendingControl = ""
    Resume Finished
End Sub
Public Sub UiRouteTab(ByVal f As Access.Form, ByRef key As Integer, ByVal shift As Integer)
    Dim sequence As String, names As Variant, current As String, i As Long, nextIndex As Long, count As Long, ctl As Object, active As Object
    Dim sourceName As String, sourceType As Long, sourceWasPicker As Boolean, targetName As String, number As Long, description As String
    If key <> vbKeyTab Or (shift And 6) <> 0 Then Exit Sub
    On Error GoTo Failed
    If Not UiTryGetActiveControl(f, active) Then Exit Sub
    sourceName = active.Name: sourceType = active.ControlType
    current = UiLogicalOwner(f, sourceName)
    sourceWasPicker = (UiState(f).PickerOwner = current And UiState(f).Pending.Exists(current))
    ' Preserve unknown text and finish this Control's Undo before SetFocus can
    ' raise native NotInList while the destination focus move is in progress.
    ' Existing picker acceptance/cancellation rules remain in the shared path.
    UiCapturePendingOnEscape f
    Select Case f.Name
    Case "frmLogin": sequence = "txtLoginId|txtPassword|cmdLogin|cmdExit"
    Case "frmMenu": sequence = "cmdEmployeeSearch|cmdCodeMaster|cmdLogout"
    Case "frmEmployeeSearch": sequence = "txtEmployeeNo|txtName|cboDepartment|cboStatus|cmdSearch|cmdClear|lstEmployees|txtSelectedDetails|cmdNew|cmdEdit|cmdExport|cmdMenu"
    Case "frmEmployeeEditor"
        If UiState(f).AcceptedPage = 0 Then
            sequence = "tabEmployee|txtEmployeeNo|txtEmployeeName|txtEmployeeKana|cboDepartment|cboStatus|txtJoinDate|txtSummary|txtSkills|txtQualifications|txtSelfPr|cmdSave|cmdCancel"
        Else
            sequence = "tabEmployee|lstCareers|cmdAddCareer|cmdRemoveCareer|txtStartMonth|txtEndMonth|cboRole|txtTeamSize|txtCompany|txtProject|txtDescription|txtDuties|txtAchievements|txtTechnologies|txtPhases|cmdApplyCareer|cmdSave|cmdCancel"
        End If
    Case "frmCodeMaster": sequence = "cboCategory|cmdNew|lstCodes|txtCode|txtCodeName|txtSortOrder|chkEnabled|cmdSave|cmdCancel|cmdMenu"
    End Select
    If sequence = "" Then Exit Sub
    ' Resolve the original logical source and each currently available target
    ' after capture may have displayed a Pending proxy or ended its picker.
    names = Split(sequence, "|"): current = UiLogicalOwner(f, sourceName)
    If f.Name = "frmEmployeeEditor" Then
        If sourceType = acPage Then current = "tabEmployee"
    End If
    For i = 0 To UBound(names)
        If names(i) = current Then
            nextIndex = i
            For count = 1 To UBound(names) + 1
                nextIndex = nextIndex + IIf((shift And 1) <> 0, -1, 1)
                If nextIndex < 0 Then nextIndex = UBound(names)
                If nextIndex > UBound(names) Then nextIndex = 0
                Set ctl = f.Controls(UiEffectiveFocus(f, CStr(names(nextIndex))))
                If ctl.Visible And ctl.Enabled And ctl.TabStop Then
                    targetName = ctl.Name: key = 0
                    If ctl.ControlType = acTabCtl Then UiFocusTabHeader f Else ctl.SetFocus
                    Exit Sub
                End If
            Next
        End If
    Next
    Exit Sub
Failed:
    number = Err.Number: description = Err.Description: key = 0
    UiRecordLayoutFailure f, "TAB_ROUTE_" & current & "_" & targetName & IIf(sourceWasPicker, "_PICKER", ""), number, description
End Sub
