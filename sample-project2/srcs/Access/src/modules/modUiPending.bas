Option Compare Binary
Option Explicit

Public Function UiPendingOwners(ByVal f As Access.Form) As Variant
    Select Case f.Name
    Case "frmEmployeeSearch": UiPendingOwners = Array("cboDepartment", "cboStatus")
    Case "frmEmployeeEditor": UiPendingOwners = Array("cboDepartment", "cboStatus", "cboRole")
    Case "frmCodeMaster": UiPendingOwners = Array("cboCategory")
    Case Else: UiPendingOwners = Array()
    End Select
End Function
Public Function UiLogicalOwner(ByVal f As Access.Form, ByVal physicalName As String) As String
    Dim owner As Variant
    UiLogicalOwner = physicalName
    For Each owner In UiPendingOwners(f)
        If physicalName = "txtPending_" & CStr(owner) Then UiLogicalOwner = CStr(owner): Exit Function
    Next
End Function
Public Function UiIsPendingPhysical(ByVal name As String) As Boolean
    UiIsPendingPhysical = (Left$(name, 11) = "txtPending_" Or Left$(name, 15) = "lbl_txtPending_")
End Function
Public Function UiEffectiveFocus(ByVal f As Access.Form, ByVal logicalName As String) As String
    Dim s As clsFormUiState: Set s = UiState(f)
    UiEffectiveFocus = logicalName
    If s.Pending.Exists(logicalName) Then
        If f.Controls("txtPending_" & logicalName).Visible Then UiEffectiveFocus = "txtPending_" & logicalName
    End If
End Function
Public Sub UiCapturePendingEditors(ByVal f As Access.Form)
    Dim s As clsFormUiState, owner As Variant, active As String, name As String, raw As String
    Set s = UiState(f)
    On Error Resume Next
    active = f.ActiveControl.Name
    Err.Clear
    On Error GoTo 0
    For Each owner In UiPendingOwners(f)
        name = "txtPending_" & CStr(owner)
        If active = name And s.Pending.Exists(CStr(owner)) Then
            raw = CStr(Nz(f.Controls(name).Text, ""))
            s.Pending(CStr(owner)) = raw: s.Raw(CStr(owner)) = raw
        End If
    Next
End Sub
Private Sub UiHidePendingEditor(ByVal f As Access.Form, ByVal owner As String)
    Dim s As clsFormUiState, name As String, active As String, prior As Boolean, number As Long, description As String
    Set s = UiState(f): name = "txtPending_" & owner: prior = s.IsRestoringSelection
    On Error Resume Next
    active = f.ActiveControl.Name
    Err.Clear
    On Error GoTo Failed
    If active = name Then
        s.IsRestoringSelection = True
        If f.Controls(owner).Visible And f.Controls(owner).Enabled Then
            f.Controls(owner).SetFocus
        ElseIf f.Name = "frmEmployeeEditor" Then
            UiFocusTabHeader f
        Else
            f!cmdMenu.SetFocus
        End If
        s.IsRestoringSelection = prior
    End If
    f.Controls(name).Visible = False: f.Controls("lbl_" & name).Visible = False
    f.Controls(name).TabStop = False: f.Controls(name).Enabled = False: f.Controls(name).Locked = True
    f.Controls("lbl_" & owner).Visible = f.Controls(owner).Visible
    If s.PendingTabStops.Exists(owner) Then
        f.Controls(owner).TabStop = CBool(s.PendingTabStops(owner))
        s.PendingTabStops.Remove owner
    End If
    If Not s.Pending.Exists(owner) Then f.Controls(name).Value = Null
    s.IsRestoringSelection = prior
    Exit Sub
Failed:
    number = Err.Number: description = Err.Description: s.IsRestoringSelection = prior
    Err.Raise number, , description
End Sub
Public Sub UiBindPendingEditor(ByVal f As Access.Form, ByVal owner As String, ByVal focusRequested As Boolean)
    Dim s As clsFormUiState, name As String, prior As Boolean, number As Long, description As String, active As String
    Set s = UiState(f): name = "txtPending_" & owner: prior = s.IsRestoringSelection
    If s.BusyOverlayDepth > 0 Then Exit Sub
    On Error GoTo Failed
    UiCapturePendingEditors f
    If Not s.Pending.Exists(owner) Or Not f.Controls(owner).Visible Then
        UiHidePendingEditor f, owner: s.IsRestoringSelection = prior: Exit Sub
    End If
    If s.PickerOwner = owner Then Exit Sub
    s.IsRestoringSelection = True
    If Not s.PendingTabStops.Exists(owner) Then s.PendingTabStops(owner) = f.Controls(owner).TabStop
    On Error Resume Next
    active = f.ActiveControl.Name
    Err.Clear
    On Error GoTo Failed
    ' Capture above already read the active edit buffer. Reassigning Value here
    ' would disturb its caret/selection and could trim the displayed raw text.
    If active <> name Then
        If StrComp(CStr(Nz(f.Controls(name).Value, "")), CStr(s.Pending(owner)), vbBinaryCompare) <> 0 Then f.Controls(name).Value = CStr(s.Pending(owner))
    End If
    f.Controls(name).Left = f.Controls(owner).Left: f.Controls(name).Top = f.Controls(owner).Top
    f.Controls(name).Width = f.Controls(owner).Width - 360: f.Controls(name).Height = f.Controls(owner).Height
    f.Controls("lbl_" & name).Left = f.Controls("lbl_" & owner).Left
    f.Controls("lbl_" & name).Top = f.Controls("lbl_" & owner).Top
    f.Controls("lbl_" & name).Width = f.Controls("lbl_" & owner).Width
    f.Controls("lbl_" & name).Height = f.Controls("lbl_" & owner).Height
    f.Controls(owner).TabStop = False
    f.Controls(name).Visible = True: f.Controls(name).Enabled = True: f.Controls(name).Locked = False: f.Controls(name).TabStop = True
    f.Controls("lbl_" & name).Visible = True: f.Controls("lbl_" & owner).Visible = False
    s.IsRestoringSelection = prior
    If focusRequested Then
        If s.IsInitializing Or s.IsUnloading Or Not s.Activated Then
            s.RestorePendingControl = owner: s.RestorePendingPhase = 0: s.RestorePendingAttempts = 0
            UiArmDeferredTimer f, 50
        Else
            f.Controls(name).SetFocus
        End If
    End If
    Exit Sub
Failed:
    number = Err.Number: description = Err.Description: s.IsRestoringSelection = prior
    UiRecordLayoutFailure f, "PENDING_BIND_" & owner, number, description
End Sub
Public Sub UiSyncPendingEditors(ByVal f As Access.Form)
    Dim owner As Variant
    For Each owner In UiPendingOwners(f): UiBindPendingEditor f, CStr(owner), False: Next
End Sub
Public Sub UiPendingChanged(ByVal f As Access.Form, ByVal physicalName As String)
    Dim s As clsFormUiState, owner As String, raw As String, active As String
    Set s = UiState(f): owner = UiLogicalOwner(f, physicalName)
    If owner = physicalName Or s.IsRestoringSelection Or s.IsInitializing Or gUiLoading Or gBusy Then Exit Sub
    On Error GoTo Failed
    active = f.ActiveControl.Name
    If active <> physicalName Or Not s.Pending.Exists(owner) Then Exit Sub
    raw = CStr(Nz(f.Controls(physicalName).Text, ""))
    s.Pending(owner) = raw: s.Raw(owner) = raw
    UiChanged f, owner
    UiPendingNotice f
    Exit Sub
Failed:
    UiRecordLayoutFailure f, "PENDING_CHANGE_" & owner, Err.Number, Err.Description
End Sub
Public Sub UiPendingNotice(ByVal f As Access.Form)
    Dim s As clsFormUiState, owner As Variant, names As String, label As String
    Set s = UiState(f)
    For Each owner In UiPendingOwners(f)
        If s.Pending.Exists(CStr(owner)) Then
            label = Replace(f.Controls("lbl_" & CStr(owner)).Caption, "※", "")
            If names <> "" Then names = names & "、"
            names = names & label
        End If
    Next
    If names = "" Then
        If f.Name = "frmEmployeeSearch" Then
            If InStr(1, f!lblSelection.Caption, "未採用の入力があります：", vbBinaryCompare) > 0 Then f!lblSelection.Caption = ""
        Else
            If InStr(1, f!lblMessage.Caption, "未採用の入力があります：", vbBinaryCompare) > 0 Then f!lblMessage.Caption = ""
        End If
        Exit Sub
    End If
    If f.Name = "frmEmployeeSearch" Then
        f!lblSelection.Caption = MessageText("MSG-016") & " 未採用の入力があります：" & names
    Else
        f!lblMessage.Caption = MessageText("MSG-016") & " 未採用の入力があります：" & names
    End If
End Sub
Public Sub UiFinishPendingChoice(ByVal f As Access.Form, ByVal owner As String)
    Dim s As clsFormUiState: Set s = UiState(f)
    If s.PickerOwner = owner Then s.PickerOwner = "": s.PickerCommitKey = False
    UiBindPendingEditor f, owner, False
    UiPendingNotice f
End Sub
Public Sub UiEndPendingPicker(ByVal f As Access.Form, ByVal focusRequested As Boolean)
    Dim s As clsFormUiState, owner As String, prior As Boolean, number As Long, description As String
    Set s = UiState(f): owner = s.PickerOwner
    If owner = "" Then Exit Sub
    prior = s.IsRestoringSelection: On Error GoTo Failed
    s.PickerOwner = "": s.PickerCommitKey = False
    If s.Pending.Exists(owner) Then
        s.IsRestoringSelection = True
        If owner = "cboCategory" Then
            f.Controls(owner).Value = s.AcceptedCategory
        ElseIf s.AcceptedCodes.Exists(owner) Then
            f.Controls(owner).Value = s.AcceptedCodes(owner)
        End If
        s.IsRestoringSelection = prior
        UiBindPendingEditor f, owner, focusRequested
    End If
    Exit Sub
Failed:
    number = Err.Number: description = Err.Description: s.IsRestoringSelection = prior
    UiRecordLayoutFailure f, "PENDING_PICKER_END_" & owner, number, description
End Sub
Public Sub UiBeginPendingPicker(ByVal f As Access.Form, ByVal owner As String, ByVal openList As Boolean)
    Dim s As clsFormUiState, prior As Boolean, number As Long, description As String
    Set s = UiState(f)
    If Not s.Pending.Exists(owner) Then Exit Sub
    prior = s.IsRestoringSelection: On Error GoTo Failed
    UiCapturePendingEditors f
    s.PickerOwner = owner: s.PickerCommitKey = False: s.PickerTyping = False
    s.IsRestoringSelection = True
    f.Controls(owner).SetFocus
    UiHidePendingEditor f, owner
    s.IsRestoringSelection = prior
    If openList Then f.Controls(owner).Dropdown
    Exit Sub
Failed:
    number = Err.Number: description = Err.Description: s.IsRestoringSelection = prior
    UiRecordLayoutFailure f, "PENDING_PICKER_BEGIN_" & owner, number, description
End Sub
Public Function UiKnownCandidate(ByVal f As Access.Form, ByVal owner As String) As Boolean
    Dim ctl As Object, rows As Collection, row As Variant, index As Long
    Set ctl = f.Controls(owner): index = ctl.ListIndex
    Set rows = CachedRows(ctl)
    If index < 0 Or index >= rows.Count Then Exit Function
    row = rows(index + 1)
    ' Null is a genuine optional search row, not an unknown-code exception.
    If Not Same(ctl.Column(0, index), row(0)) Then Exit Function
    UiKnownCandidate = Same(ctl.Value, row(0))
End Function
Public Sub UiMarkPendingCandidate(ByVal f As Access.Form, ByVal owner As String)
    Dim s As clsFormUiState: Set s = UiState(f)
    If s.IsRestoringSelection Or s.IsInitializing Or gUiLoading Or gBusy Then Exit Sub
    If s.Pending.Exists(owner) And UiKnownCandidate(f, owner) Then s.ExplicitComboChoice(owner) = True
End Sub
Public Function UiPendingKey(ByVal f As Access.Form, ByRef key As Integer, ByVal shift As Integer) As Boolean
    Dim s As clsFormUiState, current As String, owner As String, active As Object
    Set s = UiState(f)
    If s.Pending.Count = 0 Then Exit Function
    On Error GoTo Failed
    If Not UiTryGetActiveControl(f, active) Then Exit Function
    current = active.Name: owner = UiLogicalOwner(f, current)
    If Not s.Pending.Exists(owner) Then Exit Function
    If (key = vbKeyDown And (shift And 4) <> 0) Or (key = vbKeyF4 And shift = 0) Then
        UiBeginPendingPicker f, owner, True: key = 0: UiPendingKey = True: Exit Function
    End If
    If s.PickerOwner = owner And current = owner Then
        If key = vbKeyEscape Then
            UiEndPendingPicker f, False
            s.RestorePendingControl = owner: s.RestorePendingPhase = 0: s.RestorePendingAttempts = 0
            UiArmDeferredTimer f, 50
            UiPendingKey = True: Exit Function
        End If
        If key = vbKeyReturn Then s.PickerCommitKey = True: UiPendingKey = True: Exit Function
        If key <> vbKeyUp And key <> vbKeyDown And key <> vbKeyLeft And key <> vbKeyRight And key <> vbKeyHome And key <> vbKeyEnd And key <> vbKeyPageUp And key <> vbKeyPageDown And key <> vbKeyTab Then s.PickerTyping = True
    End If
    If key = vbKeyEscape And f.Name = "frmEmployeeSearch" Then
        UiCapturePendingEditors f: key = 0: UiPendingKey = True
    End If
    If current <> owner And key = vbKeyReturn And f.Name <> "frmEmployeeSearch" Then key = 0: UiPendingKey = True
    Exit Function
Failed:
    UiRecordLayoutFailure f, "PENDING_KEY", Err.Number, Err.Description
    key = 0: UiPendingKey = True
End Function
Public Sub UiPendingComboMouse(ByVal f As Access.Form, ByVal owner As String, ByVal button As Integer, ByVal x As Single, ByVal y As Single)
    Dim s As clsFormUiState: Set s = UiState(f)
    If button <> 1 Or Not s.Pending.Exists(owner) Or s.IsRestoringSelection Then Exit Sub
    s.PickerPointerInside = (x >= 0 And x <= f.Controls(owner).Width And y >= 0 And y <= f.Controls(owner).Height)
End Sub
Public Sub UiPendingComboClick(ByVal f As Access.Form, ByVal owner As String)
    Dim s As clsFormUiState: Set s = UiState(f)
    If Not s.Pending.Exists(owner) Or s.IsRestoringSelection Or gBusy Then Exit Sub
    ' A plain Click/ListIndex is not proof: opening/closing the arrow can click.
    ' Same-value keyboard confirmation has a separate real KeyDown marker.
    If s.PickerOwner = owner And s.PickerCommitKey Then
        If UiKnownCandidate(f, owner) Then s.ExplicitComboChoice(owner) = True: UiSelected f, owner
    End If
    s.PickerPointerInside = False
End Sub
Public Sub UiPendingComboKeyUp(ByVal f As Access.Form, ByVal owner As String, ByVal key As Integer, ByVal shift As Integer)
    If key = vbKeyReturn Then UiPendingComboClick f, owner
End Sub
