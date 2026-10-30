Attribute VB_Name = "ActiveControlGuardSuite"
Option Compare Binary
Option Explicit
Private Function ACGJ(ByVal value As Variant) As String
    Dim text As String, i As Long
    If IsNull(value) Or IsEmpty(value) Then ACGJ = "null": Exit Function
    Select Case VarType(value)
    Case vbBoolean: ACGJ = LCase$(CStr(value))
    Case vbByte, vbInteger, vbLong: ACGJ = CStr(value)
    Case vbString
        text = Replace(CStr(value), "\", "\\")
        text = Replace(text, Chr$(34), "\" & Chr$(34))
        For i = 0 To 31: text = Replace(text, Chr$(i), "\u" & Right$("0000" & Hex$(i), 4)): Next
        ACGJ = Chr$(34) & text & Chr$(34)
    Case Else: Err.Raise 5, , "Unsupported observation type."
    End Select
End Function
Private Function ACGD(ByVal values As Object) As String
    Dim key As Variant, text As String, separator As String
    For Each key In values.Keys
        text = text & separator & ACGJ(CStr(key)) & ":" & ACGJ(values(key)): separator = ","
    Next
    ACGD = "{" & text & "}"
End Function
Public Function ACGSnapshot() As String
    Dim f As Access.Form, state As clsFormUiState, ctl As Object, activeError As Long, activeName As Variant
    Set f = Forms("frmEmployeeSearch"): Set state = UiState(f)
    activeName = Null
    On Error Resume Next
    Set ctl = f.ActiveControl: activeError = Err.Number: Err.Clear
    If Not ctl Is Nothing Then activeName = ctl.Name
    On Error GoTo 0
    ACGSnapshot = "{""activeError"":" & ACGJ(activeError) & ",""activeName"":" & ACGJ(activeName) & ",""controlCount"":" & ACGJ(f.Controls.Count)
    ACGSnapshot = ACGSnapshot & ",""layoutFailure"":" & ACGJ(state.LayoutFailure) & ",""pending"":" & ACGD(state.Pending) & ",""raw"":" & ACGD(state.Raw) & ",""accepted"":" & ACGD(state.AcceptedCodes) & "}"
End Function
Public Function ACGCleanup() As Boolean
    Dim i As Long
    gAllowClose = True: gBusy = False: gDirty = False: gDraftDirty = False
    For i = Forms.Count - 1 To 0 Step -1: DoCmd.Close acForm, Forms(i).Name, acSaveNo: Next
    ACGCleanup = (Forms.Count = 0)
    ' Keep gAllowClose=True until the owned test database actually closes.
End Function
Public Function ACGPrepareOriginal(ByVal hidden As Boolean) As String
    Dim result As clsResult, cleaned As Boolean
    On Error GoTo Failed
    cleaned = ACGCleanup()
    Set result = Authenticate("admin", "123")
    If result.Kind <> "OK" Then Err.Raise 5, , "Fixture authentication failed."
    gAllowClose = False
    If hidden Then
        DoCmd.OpenForm "frmEmployeeSearch", acNormal, , , , acHidden
    Else
        DoCmd.OpenForm "frmEmployeeSearch"
    End If
    ACGPrepareOriginal = ACGSnapshot()
    Exit Function
Failed:
    ACGPrepareOriginal = "{""errorNumber"":" & ACGJ(Err.Number) & ",""errorDescription"":" & ACGJ(Err.Description) & "}"
End Function
Public Function ACGNormalTab(ByVal reverse As Boolean) As String
    Dim f As Access.Form, key As Integer, modifier As Integer, before As String
    On Error GoTo Failed
    Set f = Forms("frmEmployeeSearch")
    If reverse Then f!txtName.SetFocus Else f!txtEmployeeNo.SetFocus
    before = ACGSnapshot(): key = vbKeyTab
    If reverse Then modifier = 1
    UiKey f, key, modifier
    ACGNormalTab = "{""before"":" & before & ",""after"":" & ACGSnapshot() & ",""keyAfter"":" & ACGJ(key) & "}"
    Exit Function
Failed:
    ACGNormalTab = "{""errorNumber"":" & ACGJ(Err.Number) & ",""errorDescription"":" & ACGJ(Err.Description) & "}"
End Function
Public Function ACGNormalReturn(ByVal pending As Boolean) As String
    Dim f As Access.Form, key As Integer, response As Integer, before As String
    On Error GoTo Failed
    Set f = Forms("frmEmployeeSearch")
    UiClearPending f
    UiSetTextValue f, "txtEmployeeNo", "000001": UiChanged f, "txtEmployeeNo"
    UiSetTextValue f, "txtName", "": UiChanged f, "txtName"
    If pending Then
        UiNotInList f, "cboDepartment", "guard unknown  ", response
        UiChanged f, "cboDepartment": f!txtPending_cboDepartment.SetFocus
    Else
        f!txtEmployeeNo.SetFocus
    End If
    f!lblSelection.Caption = "": before = ACGSnapshot(): key = vbKeyReturn
    UiKey f, key, 0
    ACGNormalReturn = "{""before"":" & before & ",""after"":" & ACGSnapshot() & ",""keyAfter"":" & ACGJ(key) & ",""searchState"":" & ACGJ(gSearchState)
    ACGNormalReturn = ACGNormalReturn & ",""listCount"":" & ACGJ(f!lstEmployees.ListCount) & ",""message"":" & ACGJ(f!lblSelection.Caption) & "}"
    Exit Function
Failed:
    ACGNormalReturn = "{""errorNumber"":" & ACGJ(Err.Number) & ",""errorDescription"":" & ACGJ(Err.Description) & "}"
End Function
Public Function ACGEscapeUnaccepted() As String
    Dim f As Access.Form, text As String, before As String, prepared As Long
    Set f = Forms("frmEmployeeSearch"): UiClearPending f
    f!cboDepartment.SetFocus: text = "guard new unknown  "
    before = ACGSnapshot()
    On Error Resume Next
    f!cboDepartment.Text = text: prepared = Err.Number: Err.Clear
    On Error GoTo 0
    If prepared = 0 Then UiCapturePendingOnEscape f
    ACGEscapeUnaccepted = "{""preparationError"":" & ACGJ(prepared) & ",""before"":" & before & ",""after"":" & ACGSnapshot() & "}"
End Function
Public Function ACGRunNoActive(ByVal mode As String, ByVal inputKey As Integer, ByVal withPending As Boolean) As String
    Dim f As Access.Form, state As clsFormUiState, before As String, key As Integer, handled As Variant, number As Long, description As String
    Set f = Forms("frmEmployeeSearch"): Set state = UiState(f)
    state.Pending.RemoveAll: state.Raw.RemoveAll: state.AcceptedCodes.RemoveAll
    If withPending Then
        state.Pending("cboDepartment") = "guard pending  ": state.Raw("cboDepartment") = "guard pending  ": state.AcceptedCodes("cboDepartment") = Null
    End If
    before = ACGSnapshot(): key = inputKey: handled = Null
    On Error GoTo Failed
    Select Case mode
    Case "pending": handled = UiPendingKey(f, key, 0)
    Case "key": UiKey f, key, 0
    Case "tab": UiRouteTab f, key, 0
    Case "escape": UiCapturePendingOnEscape f
    Case Else: Err.Raise 5, , "Unknown guard case."
    End Select
    GoTo Finished
Failed:
    number = Err.Number: description = Err.Description: Err.Clear
Finished:
    ACGRunNoActive = "{""mode"":" & ACGJ(mode) & ",""inputKey"":" & ACGJ(inputKey) & ",""keyAfter"":" & ACGJ(key) & ",""handled"":" & ACGJ(handled)
    ACGRunNoActive = ACGRunNoActive & ",""errorNumber"":" & ACGJ(number) & ",""errorDescription"":" & ACGJ(description) & ",""before"":" & before & ",""after"":" & ACGSnapshot() & "}"
End Function
Public Function ACGUnexpectedError() As String
    Dim absent As Access.Form, ctl As Object, accepted As Boolean, directNumber As Long, directSource As String, directDescription As String
    Dim helperNumber As Long, helperSource As String, helperDescription As String
    On Error Resume Next
    Set ctl = absent.ActiveControl
    directNumber = Err.Number: directSource = Err.Source: directDescription = Err.Description: Err.Clear
    accepted = UiTryGetActiveControl(absent, ctl)
    helperNumber = Err.Number: helperSource = Err.Source: helperDescription = Err.Description: Err.Clear
    On Error GoTo 0
    ACGUnexpectedError = "{""directNumber"":" & ACGJ(directNumber) & ",""directSource"":" & ACGJ(directSource) & ",""directDescription"":" & ACGJ(directDescription)
    ACGUnexpectedError = ACGUnexpectedError & ",""helperNumber"":" & ACGJ(helperNumber) & ",""helperSource"":" & ACGJ(helperSource) & ",""helperDescription"":" & ACGJ(helperDescription) & ",""accepted"":" & ACGJ(accepted) & "}"
End Function
