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
Public Sub UiSetRaw(ByVal f As Access.Form, ByVal name As String, ByVal value As Variant)
    Dim s As clsFormUiState: Set s = UiState(f)
    s.Raw(name) = CStr(Nz(value, ""))
End Sub
Public Function UiRaw(ByVal f As Access.Form, ByVal name As String) As String
    Dim s As clsFormUiState, ctl As Object, activeName As String
    Set s = UiState(f): Set ctl = f.Controls(name)
    On Error GoTo Stored
    activeName = f.ActiveControl.Name
    If activeName = name And ctl.ControlType = acTextBox Then
        s.Raw(name) = CStr(Nz(ctl.Text, ""))
    ElseIf ctl.ControlType = acTextBox Then
        s.Raw(name) = CStr(Nz(ctl.Value, ""))
    End If
Stored:
    If s.Raw.Exists(name) Then UiRaw = CStr(s.Raw(name))
End Function
Public Sub UiCaptureText(ByVal f As Access.Form)
    Dim ctl As Control, raw As String
    For Each ctl In f.Controls
        If ctl.ControlType = acTextBox And ctl.Name <> "txtSelectedDetails" Then raw = UiRaw(f, ctl.Name)
    Next
End Sub
Public Sub UiComboChanged(ByVal f As Access.Form, ByVal name As String)
    Dim s As clsFormUiState, text As String
    Set s = UiState(f)
    If gUiLoading Or s.IsInitializing Or s.IsRestoringSelection Or gBusy Then Exit Sub
    On Error GoTo Finished
    text = CStr(Nz(f.Controls(name).Text, ""))
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
    If f.Name = "frmEmployeeSearch" Then
        f!lblSelection.Caption = MessageText("MSG-016") & " 未採用の入力があります：" & name
    Else
        f!lblMessage.Caption = MessageText("MSG-016") & " 未採用の入力があります：" & name
    End If
    Exit Sub
Failed:
    number = Err.Number: description = Err.Description: s.IsRestoringSelection = False
    Err.Raise number, , description
End Sub
Public Sub UiCapturePendingOnEscape(ByVal f As Access.Form)
    Dim ctl As Object, text As String, response As Integer, valid As Boolean
    Set ctl = f.ActiveControl
    If ctl.ControlType <> acComboBox Then Exit Sub
    text = CStr(Nz(ctl.Text, ""))
    If text = "" Then Exit Sub
    If ctl.ListIndex >= 0 Then valid = (StrComp(text, CStr(Nz(ctl.Column(1), "")), vbBinaryCompare) = 0)
    If Not valid Then UiNotInList f, ctl.Name, text, response
End Sub
Public Sub UiRestoreDeclined(ByVal f As Access.Form)
    Dim s As clsFormUiState, key As Variant
    Set s = UiState(f)
    If s.IsUnloading Then
        For Each key In s.Pending.Keys
            s.RestorePendingControl = CStr(key): s.OriginalTimerInterval = f.TimerInterval: f.TimerInterval = 1: Exit Sub
        Next
    Else
        UiRestoreFirstPending f
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
    s.AcceptedCodes(name) = ctl.Value
    If ctl.ListIndex >= 0 Then s.Raw(name) = CStr(Nz(ctl.Column(1), "")) Else s.Raw(name) = ""
    If s.Pending.Exists(name) Then s.Pending.Remove name
    s.ExplicitComboChoice(name) = False: UiAcceptCombo = True
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
    For Each key In s.Pending.Keys
        UiRestorePending f, CStr(key)
        Reject "MSG-016", CStr(key)
    Next
End Sub
Public Sub UiRestorePending(ByVal f As Access.Form, ByVal name As String)
    Dim s As clsFormUiState, number As Long, description As String
    Set s = UiState(f)
    If Not s.Pending.Exists(name) Then Exit Sub
    On Error GoTo Failed
    s.IsRestoringSelection = True
    f.Controls(name).SetFocus: f.Controls(name).Text = CStr(s.Pending(name))
    s.IsRestoringSelection = False: Exit Sub
Failed:
    number = Err.Number: description = Err.Description: s.IsRestoringSelection = False
    Err.Raise number, , description
End Sub
Public Sub UiClearPending(ByVal f As Access.Form, Optional ByVal careerOnly As Boolean = False)
    Dim s As clsFormUiState, key As Variant
    Set s = UiState(f)
    For Each key In s.Pending.Keys
        If Not careerOnly Or CStr(key) = "cboRole" Then s.Pending.Remove key
    Next
End Sub
Public Sub UiGotFocus(ByVal f As Access.Form, ByVal name As String)
    Dim s As clsFormUiState, kind As Long
    Set s = UiState(f)
    If s.IsInitializing Or s.IsRestoringSelection Then Exit Sub
    kind = f.Controls(name).ControlType
    If kind = acTextBox Or kind = acComboBox Or kind = acCheckBox Or kind = acListBox Then s.LastEditFocus = name
    If s.Pending.Exists(name) And Not gBusy Then UiRestorePending f, name
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
