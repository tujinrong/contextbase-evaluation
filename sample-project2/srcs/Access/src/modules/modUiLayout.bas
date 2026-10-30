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
    Dim s As clsFormUiState: Set s = UiState(f)
    If s.Activated Or s.IsInitializing Then Exit Sub
    s.Activated = True
    UiResize f
    f.GoToPage 1, 0, 0
    Select Case f.Name
    Case "frmLogin": If f!txtLoginId.Locked Then f!txtPassword.SetFocus Else f!txtLoginId.SetFocus
    Case "frmMenu": f!cmdEmployeeSearch.SetFocus
    Case "frmEmployeeSearch"
        If Not gSearchReturn Is Nothing Then
            If gSearchReturn.FocusControl <> "" Then
                If f.Controls(gSearchReturn.FocusControl).Visible And f.Controls(gSearchReturn.FocusControl).Enabled Then
                    f.Controls(gSearchReturn.FocusControl).SetFocus
                Else
                    f!txtEmployeeNo.SetFocus
                End If
            Else
                f!txtEmployeeNo.SetFocus
            End If
            UiRestoreFirstPending f
        Else
            f!txtEmployeeNo.SetFocus
        End If
    Case "frmEmployeeEditor": If IsNull(gEditor.EmployeeId) Then f!txtEmployeeNo.SetFocus Else f!txtEmployeeName.SetFocus
    Case "frmCodeMaster": f!cboCategory.SetFocus
    End Select
End Sub
Public Sub UiPageGroup(ByVal f As Access.Form, ByVal page As Integer)
    Dim ctl As Control
    For Each ctl In f.Controls
        If Left$(ctl.Tag, 5) = "PAGE:" Then ctl.Visible = (ctl.Tag = "PAGE:" & CStr(page))
    Next
End Sub
Public Sub UiForcePage(ByVal f As Access.Form, ByVal page As Integer)
    Dim s As clsFormUiState, number As Long, description As String
    Set s = UiState(f): On Error GoTo Failed
    s.IsSwitchingPage = True
    f!tabEmployee.SetFocus
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
    f!tabEmployee.SetFocus
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
    For Each key In s.Pending.Keys
        If f.Controls(CStr(key)).Visible And f.Controls(CStr(key)).Enabled Then UiRestorePending f, CStr(key): Exit Sub
    Next
End Sub
Public Sub UiDeferredPending(ByVal f As Access.Form)
    Dim s As clsFormUiState, name As String: Set s = UiState(f)
    If s.RestorePendingControl = "" Then Exit Sub
    name = s.RestorePendingControl: s.RestorePendingControl = ""
    f.TimerInterval = s.OriginalTimerInterval
    UiRestorePending f, name
End Sub
Public Sub UiRouteTab(ByVal f As Access.Form, ByRef key As Integer, ByVal shift As Integer)
    Dim sequence As String, names As Variant, current As String, i As Long, nextIndex As Long, count As Long, ctl As Object
    If key <> vbKeyTab Or (shift And 6) <> 0 Then Exit Sub
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
    names = Split(sequence, "|"): current = f.ActiveControl.Name
    For i = 0 To UBound(names)
        If names(i) = current Then
            nextIndex = i
            For count = 1 To UBound(names) + 1
                nextIndex = nextIndex + IIf((shift And 1) <> 0, -1, 1)
                If nextIndex < 0 Then nextIndex = UBound(names)
                If nextIndex > UBound(names) Then nextIndex = 0
                Set ctl = f.Controls(CStr(names(nextIndex)))
                If ctl.Visible And ctl.Enabled And ctl.TabStop Then ctl.SetFocus: key = 0: Exit Sub
            Next
        End If
    Next
End Sub
