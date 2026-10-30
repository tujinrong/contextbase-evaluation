Option Compare Binary
Option Explicit
Private formStates As Object
Public gSearchReturn As clsSearchReturnState
Public gSearchState As String
Public gSearchResultState As String
Public gAppliedCriteria As clsSearchCriteria
Public gAppliedValid As Boolean
Public Function UiState(ByVal f As Access.Form) As clsFormUiState
    If formStates Is Nothing Then Set formStates = CreateObject("Scripting.Dictionary")
    If Not formStates.Exists(f.Name) Then formStates.Add f.Name, New clsFormUiState
    Set UiState = formStates(f.Name)
End Function
Public Sub UiReleaseState(ByVal formName As String)
    If formStates Is Nothing Then Exit Sub
    If formStates.Exists(formName) Then formStates.Remove formName
End Sub
Public Function UiTryGetActiveControl(ByVal f As Access.Form, ByRef ctl As Object) As Boolean
    Dim number As Long, description As String, source As String
    Set ctl = Nothing
    On Error GoTo Missing
    Set ctl = f.ActiveControl
    UiTryGetActiveControl = Not ctl Is Nothing
    Exit Function
Missing:
    number = Err.Number: description = Err.Description: source = Err.Source
    Set ctl = Nothing
    ' A Form can receive a background/pane key without an active Control.
    ' This is not evidence of a failed Pending display or a consumed key.
    If number = 2474 Then Err.Clear: Exit Function
    Err.Raise number, source, description
End Function
Public Sub UiSetRaw(ByVal f As Access.Form, ByVal name As String, ByVal value As Variant)
    Dim s As clsFormUiState: Set s = UiState(f)
    s.Raw(name) = CStr(Nz(value, ""))
End Sub
Public Sub UiSetTextValue(ByVal f As Access.Form, ByVal name As String, ByVal value As Variant)
    ' Explicit canonical/clear/return assignment; never refresh unrelated fields.
    f.Controls(name).Value = value
    UiSetRaw f, name, value
End Sub
Public Sub UiRecordTextChange(ByVal f As Access.Form, ByVal name As String)
    Dim activeName As String
    On Error Resume Next
    activeName = f.ActiveControl.Name
    Err.Clear
    On Error GoTo 0
    If activeName = name Then
        UiSetRaw f, name, f.Controls(name).Text
    Else
        ' Explicit COM test/preparation calls must signal the changed Value.
        UiSetRaw f, name, f.Controls(name).Value
    End If
End Sub
Public Function UiRaw(ByVal f As Access.Form, ByVal name As String) As String
    Dim s As clsFormUiState, ctl As Object, activeName As String, owner As String
    Set s = UiState(f): Set ctl = f.Controls(name)
    owner = UiLogicalOwner(f, name)
    If owner <> name Then
        UiCapturePendingEditors f
        If s.Pending.Exists(owner) Then
            UiRaw = CStr(s.Pending(owner))
        ElseIf s.Raw.Exists(owner) Then
            UiRaw = CStr(s.Raw(owner))
        End If
        Exit Function
    End If
    ' During Form.Load there may be no ActiveControl yet. Its absence does not
    ' prevent reading the unbound Value used to initialize the raw snapshot.
    On Error Resume Next
    activeName = f.ActiveControl.Name
    Err.Clear
    On Error GoTo Stored
    If activeName = name And ctl.ControlType = acTextBox Then
        s.Raw(name) = CStr(Nz(ctl.Text, ""))
    ElseIf ctl.ControlType = acTextBox And Not s.Raw.Exists(name) Then
        ' Access trims a TextBox Value when focus leaves it. The last Change
        ' snapshot is authoritative until a deliberate canonical assignment.
        s.Raw(name) = CStr(Nz(ctl.Value, ""))
    End If
Stored:
    If s.Raw.Exists(name) Then UiRaw = CStr(s.Raw(name))
End Function
Public Sub UiCaptureText(ByVal f As Access.Form)
    Dim ctl As Control, raw As String
    UiCapturePendingEditors f
    For Each ctl In f.Controls
        If ctl.ControlType = acTextBox And ctl.Name <> "txtSelectedDetails" And Not UiIsPendingPhysical(ctl.Name) Then raw = UiRaw(f, ctl.Name)
    Next
End Sub
Public Sub UiComboChanged(ByVal f As Access.Form, ByVal name As String)
    Dim s As clsFormUiState, text As String
    Set s = UiState(f)
    If gUiLoading Or s.IsInitializing Or s.IsRestoringSelection Or gBusy Then Exit Sub
    On Error GoTo Finished
    text = CStr(Nz(f.Controls(name).Text, ""))
    If s.PickerOwner = name And Not s.PickerTyping Then Exit Sub
    If s.Pending.Exists(name) Then s.Pending(name) = text
    If s.RestorePendingControl = name Then UiCancelDeferredPending f
    s.Raw(name) = text: s.ExplicitComboChoice(name) = True
    UiChanged f, name
Finished:
End Sub
Public Sub UiNotInList(ByVal f As Access.Form, ByVal name As String, ByVal newData As String, ByRef response As Integer)
    Dim s As clsFormUiState, number As Long, description As String
    Set s = UiState(f): response = acDataErrContinue
    s.Pending(name) = newData: s.Raw(name) = newData: s.ExplicitComboChoice(name) = False
    On Error GoTo Failed
    s.IsRestoringSelection = True
    f.Controls(name).Undo
    s.IsRestoringSelection = False
    If f.Name = "frmEmployeeEditor" Or f.Name = "frmCodeMaster" Then gDirty = True
    If s.PickerOwner = name Then s.PickerOwner = "": s.PickerCommitKey = False
    UiBindPendingEditor f, name, False
    UiPendingNotice f
    Exit Sub
Failed:
    number = Err.Number: description = Err.Description: s.IsRestoringSelection = False
    Err.Raise number, , description
End Sub
Public Sub UiCapturePendingOnEscape(ByVal f As Access.Form)
    Dim ctl As Object, text As String, response As Integer, valid As Boolean
    ' Pending may still be empty: capture a not-yet-raised NotInList value.
    If Not UiTryGetActiveControl(f, ctl) Then Exit Sub
    If UiLogicalOwner(f, ctl.Name) <> ctl.Name Then UiCapturePendingEditors f: Exit Sub
    If ctl.ControlType <> acComboBox Then Exit Sub
    text = CStr(Nz(ctl.Text, ""))
    If text = "" Then Exit Sub
    If ctl.ListIndex >= 0 Then valid = (StrComp(text, CStr(Nz(ctl.Column(1), "")), vbBinaryCompare) = 0)
    If Not valid Then UiNotInList f, ctl.Name, text, response
End Sub
Public Sub UiRestoreDeclined(ByVal f As Access.Form)
    Dim s As clsFormUiState, key As Variant
    Set s = UiState(f)
    If s.PickerOwner <> "" Then UiEndPendingPicker f, False
    UiSyncPendingEditors f
    If s.IsUnloading Then
        If s.Pending.Exists(s.LastEditFocus) Then
            s.RestorePendingControl = s.LastEditFocus: s.RestorePendingPhase = 0: s.RestorePendingAttempts = 0
            UiArmDeferredTimer f, 1: Exit Sub
        End If
        For Each key In s.Pending.Keys
            s.RestorePendingControl = CStr(key): s.RestorePendingPhase = 0: s.RestorePendingAttempts = 0
            UiArmDeferredTimer f, 1: Exit Sub
        Next
    Else
        If s.Pending.Exists(s.LastEditFocus) Then UiBindPendingEditor f, s.LastEditFocus, True Else UiRestoreFirstPending f
    End If
End Sub
Public Function UiAcceptCombo(ByVal f As Access.Form, ByVal name As String) As Boolean
    Dim s As clsFormUiState, ctl As Object, explicitChoice As Boolean
    Set s = UiState(f): Set ctl = f.Controls(name)
    If s.IsRestoringSelection Or s.IsInitializing Or gUiLoading Then Exit Function
    explicitChoice = False
    If s.ExplicitComboChoice.Exists(name) Then explicitChoice = CBool(s.ExplicitComboChoice(name))
    If s.Pending.Exists(name) And Not explicitChoice Then Exit Function
    If ctl.ListIndex < 0 And Not IsNull(ctl.Value) Then Exit Function
    If s.Pending.Exists(name) Then
        If ctl.ListIndex < 0 Then Exit Function
        If Not Same(ctl.Value, ctl.Column(0, ctl.ListIndex)) Then Exit Function
    End If
    s.AcceptedCodes(name) = ctl.Value
    If ctl.ListIndex >= 0 Then s.Raw(name) = CStr(Nz(ctl.Column(1), "")) Else s.Raw(name) = ""
    If s.Pending.Exists(name) Then s.Pending.Remove name
    s.ExplicitComboChoice(name) = False: UiAcceptCombo = True
    UiFinishPendingChoice f, name
End Function
Public Sub UiRememberCombo(ByVal f As Access.Form, ByVal name As String)
    Dim s As clsFormUiState, ctl As Object
    Set s = UiState(f): Set ctl = f.Controls(name)
    s.AcceptedCodes(name) = ctl.Value
    If ctl.ListIndex >= 0 Then s.Raw(name) = CStr(Nz(ctl.Column(1), "")) Else s.Raw(name) = ""
End Sub
Public Function UiAcceptedCode(ByVal f As Access.Form, ByVal name As String) As Variant
    Dim s As clsFormUiState: Set s = UiState(f)
    If s.Pending.Exists(name) Then Reject "MSG-016", name
    If s.AcceptedCodes.Exists(name) Then UiAcceptedCode = s.AcceptedCodes(name) Else UiAcceptedCode = f.Controls(name).Value
End Function
Public Sub UiRequireNoPending(ByVal f As Access.Form)
    Dim s As clsFormUiState, key As Variant
    Set s = UiState(f)
    If s.Pending.Count = 0 Then Exit Sub
    UiRestoreFirstPending f
    For Each key In UiPendingOwners(f)
        If s.Pending.Exists(CStr(key)) Then Reject "MSG-016", CStr(key)
    Next
End Sub
Public Function UiRestorePending(ByVal f As Access.Form, ByVal name As String) As Boolean
    Dim s As clsFormUiState, number As Long, description As String, prior As Boolean
    Set s = UiState(f)
    prior = s.IsRestoringSelection
    If Not s.Pending.Exists(name) Then UiRestorePending = True: Exit Function
    On Error GoTo Failed
    UiBindPendingEditor f, name, True
    If Not f.Controls("txtPending_" & name).Visible Then Err.Raise 5, , "Pending editor is not visible."
    If StrComp(CStr(Nz(f.Controls("txtPending_" & name).Value, "")), CStr(s.Pending(name)), vbBinaryCompare) <> 0 Then Err.Raise 5, , "Pending text readback differs."
    If s.AcceptedCodes.Exists(name) Then
        If Not Same(f.Controls(name).Value, s.AcceptedCodes(name)) Then Err.Raise 5, , "Accepted code changed during Pending display restoration."
    End If
    s.IsRestoringSelection = prior: UiRestorePending = True: Exit Function
Failed:
    number = Err.Number: description = Err.Description: s.IsRestoringSelection = prior
    UiRecordLayoutFailure f, "PENDING_" & name, number, description
End Function
Public Sub UiClearPending(ByVal f As Access.Form, Optional ByVal careerOnly As Boolean = False)
    Dim s As clsFormUiState, key As Variant
    Set s = UiState(f)
    For Each key In s.Pending.Keys
        If Not careerOnly Or CStr(key) = "cboRole" Then s.Pending.Remove key
    Next
    If s.PickerOwner <> "" Then
        If Not s.Pending.Exists(s.PickerOwner) Then s.PickerOwner = "": s.PickerCommitKey = False
    End If
    UiSyncPendingEditors f
End Sub
Public Sub UiGotFocus(ByVal f As Access.Form, ByVal name As String)
    Dim s As clsFormUiState, kind As Long, number As Long, description As String, owner As String
    Set s = UiState(f)
    If s.IsInitializing Or s.IsRestoringSelection Then Exit Sub
    On Error GoTo Failed
    owner = UiLogicalOwner(f, name)
    If s.PickerOwner <> "" And name <> s.PickerOwner Then UiEndPendingPicker f, False
    kind = f.Controls(name).ControlType
    If kind = acTextBox Or kind = acComboBox Or kind = acCheckBox Or kind = acListBox Then s.LastEditFocus = owner
    If owner <> name Then
        If s.Pending.Exists(owner) Then
            If StrComp(CStr(Nz(f.Controls(name).Text, "")), CStr(s.Pending(owner)), vbBinaryCompare) <> 0 Then
                s.IsRestoringSelection = True: f.Controls(name).Text = CStr(s.Pending(owner)): s.IsRestoringSelection = False
            End If
        End If
        Exit Sub
    End If
    If kind = acTextBox And s.Raw.Exists(name) Then
        If StrComp(CStr(Nz(f.Controls(name).Text, "")), CStr(s.Raw(name)), vbBinaryCompare) <> 0 Then
            s.IsRestoringSelection = True
            f.Controls(name).Text = CStr(s.Raw(name))
            s.IsRestoringSelection = False
        End If
    End If
    If kind = acComboBox And s.Pending.Exists(name) And Not gBusy Then UiBeginPendingPicker f, name, False
    Exit Sub
Failed:
    number = Err.Number: description = Err.Description: s.IsRestoringSelection = False
    UiRecordLayoutFailure f, "FOCUS_" & name, number, description
End Sub
Public Function UiDialogTitle(ByVal f As Access.Form, Optional ByVal career As Boolean = False) As String
    If f.Name = "frmEmployeeEditor" Then
        UiDialogTitle = CStr(Nz(f!txtEmployeeNo.Value, "新規社員")) & " " & UiRaw(f, "txtEmployeeName")
        If career Then UiDialogTitle = UiDialogTitle & " 経歴" & CStr(gCareerIndex) & " " & UiRaw(f, "txtStartMonth")
    ElseIf f.Name = "frmCodeMaster" Then
        UiDialogTitle = CStr(Nz(f!cboCategory.Column(1), "")) & " / " & UiRaw(f, "txtCode") & " " & UiRaw(f, "txtCodeName")
    Else
        UiDialogTitle = "社員経歴管理"
    End If
End Function
