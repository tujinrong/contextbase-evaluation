Option Compare Binary
Option Explicit
Private busySeen As Boolean
Private busyInputsBlocked As Boolean
Private busyKeyBlocked As Boolean
Private busyEscapeAccepted As Boolean
Private busyTickError As String
Private busyTickArmed As Boolean

Private Function ControlState(ByVal f As Access.Form) As String
    Dim ctl As Access.Control, text As String
    For Each ctl In f.Controls
        Select Case ctl.ControlType
        Case acTextBox, acComboBox, acListBox, acCheckBox
            text = text & ctl.Name & ":" & CStr(ctl.Enabled) & ":" & CStr(ctl.Locked) & ";"
        Case acCommandButton, acTabCtl
            text = text & ctl.Name & ":" & CStr(ctl.Enabled) & ";"
        End Select
    Next
    ControlState = text
End Function
Private Function OpenBusySearch(ByVal selected As Boolean) As Access.Form
    Dim f As Access.Form, id As Long
    Set gCriteria = Nothing: Set gSearchRaw = Nothing: Set gSearchRows = Nothing: gSelectedEmployee = Null: gSearchWasExecuted = False
    DoCmd.OpenForm "frmEmployeeSearch": Set f = Forms("frmEmployeeSearch")
    f!txtEmployeeNo = "000001": UiChanged f, "txtEmployeeNo": UiAction f, "cmdSearch"
    Need gSearchRows.Count = 1, "Busy fixture search failed"
    If selected Then
        id = CLng(DLookup("employee_id", "m_employee", "employee_no='000001'"))
        f!lstEmployees = id: UiSelected f, "lstEmployees"
    End If
    Set OpenBusySearch = f
End Function
Public Function IndependentBusyTick() As Boolean
    Dim f As Access.Form, name As Variant, key As Integer
    On Error GoTo Failed
    If Not busyTickArmed Or Not gBusy Then IndependentBusyTick = True: Exit Function
    If Not IndependentExportRunningProbe() Then IndependentBusyTick = True: Exit Function
    busyTickArmed = False: busySeen = True: busyInputsBlocked = True
    Set f = Forms("frmEmployeeSearch")
    For Each name In Array("txtEmployeeNo", "txtName", "cboDepartment", "cboStatus", "lstEmployees")
        If f.Controls(CStr(name)).Enabled And Not f.Controls(CStr(name)).Locked Then busyInputsBlocked = False
    Next
    key = vbKeyA: UiKey f, key: busyKeyBlocked = (key = 0)
    key = vbKeyEscape: UiKey f, key: busyEscapeAccepted = (key = 0 And gExportCancel)
    IndependentBusyTick = True: Exit Function
Failed:
    busyTickError = Err.Description: busyTickArmed = False: gExportCancel = True
    IndependentBusyTick = True
End Function

Private Sub Need(ByVal value As Boolean, ByVal detail As String)
    If Not value Then Err.Raise vbObjectError + 1910, "IndependentReview", detail
End Sub
Private Sub CloseReviewForms()
    Dim i As Long
    gAllowClose = True: gBusy = False: gDirty = False: gDraftDirty = False
    For i = Forms.Count - 1 To 0 Step -1
        DoCmd.Close acForm, Forms(i).Name, acSaveNo
    Next
    gAllowClose = False: Set gEditor = Nothing: Set gOriginal = Nothing
End Sub
Private Function ReviewEmployee(ByVal number As String) As clsEmployeeEdit
    Dim result As clsResult, id As Long
    id = CLng(DLookup("employee_id", "m_employee", "employee_no='" & number & "'"))
    Set result = ReadEmployee(id, gSession): Need result.Kind = "OK", "ReadEmployee failed"
    Set ReviewEmployee = result.Value
End Function
Private Function OpenReviewEditor() As Access.Form
    Dim f As Access.Form
    Set gEditor = ReviewEmployee("000001"): Set gOriginal = CloneEmployee(gEditor)
    DoCmd.OpenForm "frmEmployeeEditor"
    Set f = Forms("frmEmployeeEditor")
    Need CStr(Nz(f!txtEmployeeNo, "")) = "000001", "Natural editor Form_Load lost the employee"
    Need f!cboDepartment.ListCount >= 3 And f!cboStatus.ListCount = 3, "Natural editor Form_Load department/status initialization failed"
    Need f!lstCareers.ListCount = gEditor.Careers.Count, "Natural editor Form_Load career rows differ"
    Need CStr(f!lblMessage.Caption) <> MessageText("MSG-040"), "Natural editor Form_Load reported read failure"
    Set OpenReviewEditor = f
End Function
Public Function RunReviewCase(ByVal caseId As String, ByVal staffPassword As String, Optional ByVal adminPassword As String = "") As String
    Dim result As clsResult, nextResult As clsResult, e As clsEmployeeEdit, stale As clsEmployeeEdit
    Dim f As Access.Form, criteria As New clsSearchCriteria, row As Variant, revision As Long, id As Long, text As String, previousTimer As String, previousInterval As Long
    On Error GoTo Failed
    CloseReviewForms
    Set result = Authenticate("staff", staffPassword): Need result.Kind = "OK", "Fixture authentication failed"
    Select Case caseId
    Case "IR-A01-seed-and-schema"
        Need CurrentDb.TableDefs("m_app_user").Fields.Count = 8 And CurrentDb.TableDefs("m_employee").Fields.Count = 16 And CurrentDb.TableDefs("t_career").Fields.Count = 14 And CurrentDb.TableDefs("m_code_category").Fields.Count = 2 And CurrentDb.TableDefs("m_code").Fields.Count = 8, "Five-table 48-field schema differs"
        Need DCount("*", "m_employee") = 3 And DCount("*", "t_career") = 3 And DCount("*", "m_code") = 9, "Seed counts differ"
    Case "IR-A02-failure4-success-reset"
        CurrentDb.Execute "UPDATE m_app_user SET failed_count=4,locked_until=Null WHERE user_id='SP2STAFF'", dbFailOnError
        Set result = Authenticate("staff", staffPassword)
        Need result.Kind = "OK" And DLookup("failed_count", "m_app_user", "user_id='SP2STAFF'") = 0 And IsNull(DLookup("locked_until", "m_app_user", "user_id='SP2STAFF'")), "Success did not reset prior four failures"
    Case "IR-A03-search-native-seven-columns"
        criteria.EmployeeNo = "000001": criteria.NameRaw = "": criteria.Department = Null: criteria.Status = Null
        Set result = SearchEmployees(criteria, gSession): Need result.Kind = "OK" And result.Value.Count = 1, "Exact search failed"
        row = result.Value(1): Need UBound(row) = 6, "Search row must include hidden ID and six visible values"
        Need row(3) = DLookup("employee_kana", "m_employee", "employee_no='000001'"), "Kana column is missing/misbound"
        DoCmd.OpenForm "frmEmployeeSearch": Set f = Forms("frmEmployeeSearch")
        Need f!lstEmployees.ColumnCount = 7, "Native ListBox has a different column count"
        Need f!cboDepartment.ListCount = 4 And f!cboStatus.ListCount = 4 And CStr(Nz(f!cboStatus, "")) = "01", "Natural search Form_Load candidate/default initialization failed"
        Need CStr(f!lblSelection.Caption) <> MessageText("MSG-040"), "Natural search Form_Load reported read failure"
    Case "IR-A04-version-before-nochange"
        Set e = ReviewEmployee("000001"): Set stale = CloneEmployee(e): revision = CLng(e.ExpectedRevision)
        e.Careers(1).Duties = e.Careers(1).Duties & " IR"
        Set result = SaveEmployee(e, gSession): Need result.Kind = "OK", "Child change failed"
        Need DLookup("revision", "m_employee", "employee_no='000001'") = revision + 1, "Child-only save did not advance parent once"
        Set result = SaveEmployee(stale, gSession): Need result.MessageId = "MSG-008", "Stale no-change was accepted"
    Case "IR-A05-missing-loaded-child-rejected"
        Set e = ReviewEmployee("000001"): revision = CLng(e.ExpectedRevision): e.Careers.Remove 1
        Set result = SaveEmployee(e, gSession): Need result.MessageId = "MSG-025", "Missing child was inferred as deletion"
        Need DLookup("revision", "m_employee", "employee_no='000001'") = revision, "Rejected request changed parent"
    Case "IR-A06-correctable-saved-value"
        id = CLng(DLookup("employee_id", "m_employee", "employee_no='000003'"))
        CurrentDb.Execute "UPDATE m_employee SET employee_name=' ' WHERE employee_id=" & CStr(id), dbFailOnError
        Set result = ReadEmployee(id, gSession): Need result.Kind = "OK", "Correctable saved value blocked editing"
        Set e = result.Value: Need e.Name = " ", "Saved raw text was hidden or normalized"
        Set nextResult = ReadReport(id, gSession): Need nextResult.MessageId = "MSG-020", "Invalid saved value was accepted for output"
        e.Name = "Corrected fixture": Set result = SaveEmployee(e, gSession): Need result.Kind = "OK", "Corrected value could not be saved"
    Case "IR-A07-raw-preserved-on-invalid-kana"
        Set e = ReviewEmployee("000003"): e.Name = "  raw name  ": e.Kana = "abc"
        Set result = SaveEmployee(e, gSession): Need result.MessageId = "MSG-005", "Non-kana text was accepted"
        Need e.Name = "  raw name  " And e.Kana = "abc", "Failed save changed caller raw text"
    Case "IR-A08-longtext-supplementary-roundtrip"
        Set e = ReviewEmployee("000003"): text = String$(999, ChrW(&H3042)) & ChrW(&HD83D) & ChrW(&HDE00)
        e.Summary = text: Set result = SaveEmployee(e, gSession): Need result.Kind = "OK", "Legal LongText save failed"
        Set e = ReviewEmployee("000003"): Need e.Summary = text And ScalarLength(CStr(e.Summary)) = 1000, "LongText scalar content was shortened"
    Case "IR-A09-login-required-input-focus"
        DoCmd.OpenForm "frmLogin": Set f = Forms("frmLogin")
        f!txtLoginId = Null: f!txtPassword = "irrelevant fixture input": f!cmdLogin.SetFocus
        UiAction f, "cmdLogin"
        text = MessageText("MSG-004", "")
        Need Right$(CStr(f!lblMessage.Caption), Len(text)) = text, "Missing input did not produce MSG004"
        Need Screen.ActiveControl.Name = "txtLoginId", "Required-input focus differs"
        Need CStr(Nz(f!txtPassword, "")) = "", "Password was retained after failed login"
    Case "IR-A10-save-field-error-focus"
        Set f = OpenReviewEditor(): f!txtEmployeeName = "": f!cmdSave.SetFocus
        UiAction f, "cmdSave"
        Need Screen.ActiveControl.Name = "txtEmployeeName" And f!tabEmployee.Value = 0, "Save error did not select name field/basic tab"
    Case "IR-A11-empty-new-reservation-required"
        Set f = OpenReviewEditor(): revision = CLng(gEditor.ExpectedRevision): f!tabEmployee.Value = 1
        UiAction f, "cmdAddCareer"
        Need f!cboRole.ListCount >= 3 And f!cboRole.Enabled, "Adding a career did not load/enable current role candidates"
        f!cmdSave.SetFocus: UiAction f, "cmdSave"
        text = MessageText("MSG-004", "")
        Need Right$(CStr(f!lblMessage.Caption), Len(text)) = text, "Empty reserved career was silently ignored"
        Need DLookup("revision", "m_employee", "employee_no='000001'") = revision, "Empty reservation changed parent"
    Case "IR-A12-unknown-save-guard"
        Set f = OpenReviewEditor(): revision = CLng(gEditor.ExpectedRevision): gEditor.Outcome = "CommitUnknown"
        UiAction f, "cmdSave"
        Need f!lblMessage.Caption = MessageText("MSG-034"), "Unknown save did not stay blocked"
        Need Not f!cmdSave.Enabled And DLookup("revision", "m_employee", "employee_no='000001'") = revision, "Unknown guard changed or enabled save"
    Case "IR-A13-idle-exact-expiry"
        gSession.LastActivityTick = GetTickCount64() - 1800000
        Need Not TouchActivity() And Not gSession.IsAuthenticated, "First input revived an expired session"
    Case "IR-A15-unsearched-raw-survives-new-cancel"
        Set gCriteria = Nothing: Set gSearchRows = Nothing: gSelectedEmployee = Null
        DoCmd.OpenForm "frmEmployeeSearch": Set f = Forms("frmEmployeeSearch")
        f!txtEmployeeNo = "777777": UiChanged f, "txtEmployeeNo"
        f!cmdNew.SetFocus: UiAction f, "cmdNew"
        Set f = Forms("frmEmployeeEditor"): f!cmdCancel.SetFocus: UiAction f, "cmdCancel"
        Set f = Forms("frmEmployeeSearch")
        Need CStr(Nz(f!txtEmployeeNo, "")) = "777777", "Unsearched employee-number raw was lost by New then untouched Cancel"
        Need gSearchRows.Count = 0 And IsNull(gSelectedEmployee) And Not f!cmdEdit.Enabled And Not f!cmdExport.Enabled, "Cancel changed unsearched result/selection state"
    Case "IR-A16-busy-export-key-cancel-and-restore"
        Set f = OpenBusySearch(True): text = ControlState(f): id = CLng(gSelectedEmployee)
        previousTimer = f.OnTimer: previousInterval = f.TimerInterval
        busySeen = False: busyInputsBlocked = False: busyKeyBlocked = False: busyEscapeAccepted = False: busyTickError = "": busyTickArmed = True: gExportCancel = False
        f.OnTimer = "=IndependentBusyTick()": f.TimerInterval = 10
        UiAction f, "cmdExport"
        f.TimerInterval = 0: f.OnTimer = previousTimer: f.TimerInterval = previousInterval
        Need busySeen And busyTickError = "", "Busy checkpoint was not observed: " & busyTickError
        Need busyInputsBlocked, "Busy export left an input control editable"
        Need busyKeyBlocked And busyEscapeAccepted, "Busy normal key was not suppressed or Esc was not consumed"
        Need Not gBusy And ControlState(f) = text, "Cancelled export did not restore prior enabled/locked states"
        Need CStr(f!lblSelection.Caption) = MessageText("MSG-030"), "Esc did not cancel before the save dialog"
        Need CLng(gSelectedEmployee) = id And CLng(f!lstEmployees) = id And f!cmdEdit.Enabled And f!cmdExport.Enabled, "Cancel lost the prior valid selection"
    Case "IR-A17-busy-validation-restores-disabled-controls"
        Set f = OpenReviewEditor(): f!txtEmployeeName = "": text = ControlState(f): revision = CLng(gEditor.ExpectedRevision)
        Need Not f!cmdApplyCareer.Enabled And Not f!cmdRemoveCareer.Enabled, "Fixture must have no selected career"
        UiAction f, "cmdSave"
        Need Not gBusy And ControlState(f) = text, "Validation failure did not restore prior control states"
        Need Not f!cmdApplyCareer.Enabled And Not f!cmdRemoveCareer.Enabled And Not f!txtEmployeeName.Locked, "Validation enabled an unselected career operation or retained a lock"
        Need DLookup("revision", "m_employee", "employee_no='000001'") = revision, "Rejected save changed the parent"
    Case "IR-A18-busy-search-restores-unselected-controls"
        Set f = OpenBusySearch(False): text = ControlState(f)
        Need Not f!cmdEdit.Enabled And Not f!cmdExport.Enabled, "Fixture must have no selected employee"
        UiAction f, "cmdSearch"
        Need Not gBusy And ControlState(f) = text, "Successful search did not restore prior control states"
        Need IsNull(gSelectedEmployee) And Not f!cmdEdit.Enabled And Not f!cmdExport.Enabled And gSearchRows.Count = 1, "Successful search enabled an unselected employee operation"
        CloseReviewForms
        Set result = Authenticate("admin", adminPassword): Need result.Kind = "OK", "Admin fixture authentication failed"
        DoCmd.OpenForm "frmCodeMaster": Set f = Forms("frmCodeMaster")
        Need CStr(Nz(f!cboCategory, "")) = "DEPARTMENT" And f!lstCodes.ListCount = 3, "Natural code Form_Load candidate initialization failed"
        Need Not f!cmdSave.Enabled And Not f!cmdCancel.Enabled And f!cmdNew.Enabled, "Natural code Form_Load model-state buttons differ"
        Need CStr(f!lblMessage.Caption) <> MessageText("MSG-040"), "Natural code Form_Load reported read failure"
    Case Else
        Err.Raise vbObjectError + 1911, , "Unknown independent case"
    End Select
    CloseReviewForms: RunReviewCase = "PASS": Exit Function
Failed:
    text = Left$(Err.Description, 180)
    On Error Resume Next
    CloseReviewForms
    RunReviewCase = "FAIL|" & text
End Function
