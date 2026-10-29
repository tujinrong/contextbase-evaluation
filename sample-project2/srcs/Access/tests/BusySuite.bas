Option Compare Binary
Option Explicit
Private log As String
Private Sub Check(ByVal id As String, ByVal okay As Boolean)
    log = log & id & "|" & IIf(okay, "PASS", "FAIL") & vbLf
    If Not okay Then Err.Raise vbObjectError + 970, , id
End Sub
Private Function State(ByVal f As Access.Form) As String
    Dim c As Object, kind As Long, answer As String
    For Each c In f.Controls
        kind = c.ControlType
        If kind = acTextBox Or kind = acComboBox Or kind = acCheckBox Or kind = acListBox Or kind = acTabCtl Or kind = acCommandButton Then
            answer = answer & c.Name & ":" & CStr(c.Enabled) & ":" & CStr(c.TabStop)
            If kind = acTextBox Or kind = acComboBox Or kind = acCheckBox Or kind = acListBox Then answer = answer & ":" & CStr(c.Locked)
            answer = answer & ";"
        End If
    Next
    State = answer
End Function
Private Sub ThrowInsideOverlay(ByVal f As Access.Form)
    Dim overlay As New clsUiBusyState
    overlay.Acquire f
    Err.Raise vbObjectError + 971, , "expected fixture failure"
End Sub
Private Function FailureRestored(ByVal f As Access.Form) As Boolean
    Dim before As String
    before = State(f)
    On Error GoTo Caught
    ThrowInsideOverlay f
    Exit Function
Caught:
    FailureRestored = (before = State(f) And Not gBusy)
End Function
Public Function RunBusySuite(ByVal password As String) As String
    Dim f As Access.Form, overlay As clsUiBusyState, before As String, c As Object, kind As Long, okay As Boolean, key As Integer
    On Error GoTo Failed
    log = "": Check "open-new-editor", PrepareUi("editor-new", password)
    Set f = Forms("frmEmployeeEditor")
    Check "new-business-key-editable", f!txtEmployeeNo.Enabled And Not f!txtEmployeeNo.Locked
    Check "unselected-career-disabled", Not f!txtCompany.Enabled And Not f!cmdApplyCareer.Enabled And Not f!cmdRemoveCareer.Enabled
    before = State(f): Set overlay = New clsUiBusyState: overlay.Acquire f
    okay = gBusy
    For Each c In f.Controls
        kind = c.ControlType
        If kind = acTextBox Or kind = acComboBox Or kind = acCheckBox Or kind = acListBox Or kind = acTabCtl Then okay = okay And Not c.Enabled
        If kind = acTextBox Or kind = acComboBox Or kind = acCheckBox Or kind = acListBox Then okay = okay And c.Locked
    Next
    Check "busy-all-edit-select-controls-disabled", okay
    key = 65: UiKey f, key: Check "busy-letter-key-swallowed", key = 0
    gExportCancel = False: key = vbKeyEscape: UiKey f, key
    Check "busy-editor-esc-no-export-cancel", key = 0 And Not gExportCancel
    overlay.Restore: Set overlay = Nothing
    Check "normal-overlay-exact-property-restore", before = State(f) And Not gBusy
    Check "exception-overlay-exact-property-restore", FailureRestored(f)
    UiAction f, "cmdAddCareer"
    Check "new-career-desired-state-not-reverted", f!txtCompany.Enabled And Not f!txtCompany.Locked And f!cmdApplyCareer.Enabled And Not f!cmdRemoveCareer.Enabled
    Check "open-existing-editor", PrepareUi("editor-edit")
    Set f = Forms("frmEmployeeEditor")
    before = State(f): Set overlay = New clsUiBusyState: overlay.Acquire f: overlay.Restore: Set overlay = Nothing
    Check "existing-key-stays-readonly", f!txtEmployeeNo.Enabled And f!txtEmployeeNo.Locked And before = State(f)
    f!txtEmployeeName = "": UiAction f, "cmdSave"
    Check "validation-restores-input-mode", f!txtEmployeeName.Enabled And Not f!txtEmployeeName.Locked And f!txtEmployeeNo.Locked And f!cmdSave.Enabled And Not gBusy
    Check "open-code", PrepareUi("code")
    Set f = Forms("frmCodeMaster"): UiAction f, "cmdNew"
    Check "new-code-key-editable", f!txtCode.Enabled And Not f!txtCode.Locked
    f!txtCode = "04": f!txtCodeName = "busy架空部署": f!txtSortOrder = "4": f!chkEnabled = True
    UiAction f, "cmdSave"
    Check "saved-code-key-becomes-readonly", f!txtCode.Enabled And f!txtCode.Locked And Not gCode.IsNew And f!cmdSave.Enabled And Not gBusy
    Check "open-search", PrepareUi("search")
    Set f = Forms("frmEmployeeSearch"): f!lstEmployees = Null: UiSelected f, "lstEmployees"
    before = State(f): Set overlay = New clsUiBusyState: overlay.Acquire f
    gExportCancel = False: key = vbKeyEscape: UiKey f, key
    Check "search-busy-esc-owned-cancel", key = 0 And gExportCancel
    overlay.Restore: Set overlay = Nothing: gExportCancel = False
    Check "cancel-restores-search-selection-mode", before = State(f) And Not f!cmdEdit.Enabled And Not f!cmdExport.Enabled And Not gBusy
    UiAction f, "cmdSearch"
    Check "search-success-unselected-mode", Not f!cmdEdit.Enabled And Not f!cmdExport.Enabled And f!txtName.Enabled And Not f!txtName.Locked And Not gBusy
    RunBusySuite = log: Exit Function
Failed:
    RunBusySuite = log & "suite-error|FAIL|" & Left$(Err.Description, 80)
End Function
