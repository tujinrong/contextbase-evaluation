Attribute VB_Name = "PendingApiSuite"
Option Compare Binary
Option Explicit
Public Function PendingApiCompilePing() As Long
    PendingApiCompilePing = 1
End Function
Private Function J(ByVal v As Variant) As String
    Dim s As String, i As Long
    If IsNull(v) Or IsEmpty(v) Then J = "null": Exit Function
    Select Case VarType(v)
    Case vbBoolean: J = LCase$(CStr(v))
    Case vbByte, vbInteger, vbLong: J = CStr(v)
    Case vbString
        s = Replace(CStr(v), "\", "\\"): s = Replace(s, Chr$(34), "\" & Chr$(34))
        For i = 0 To 31: s = Replace(s, Chr$(i), "\u" & Right$("0000" & Hex$(i), 4)): Next
        J = Chr$(34) & s & Chr$(34)
    Case Else: Err.Raise 5, , "Unexpected observation variant."
    End Select
End Function
Private Function D(ByVal values As Object) As String
    Dim key As Variant, s As String, sep As String
    For Each key In values.Keys: s = s & sep & J(CStr(key)) & ":" & J(values(key)): sep = ",": Next
    D = "{" & s & "}"
End Function
Private Function Snapshot(ByVal f As Access.Form) As String
    Dim ui As clsFormUiState, owner As Variant, c As Object, label As Object, child As Object
    Dim s As String, sep As String, names As String, childSep As String, extras As String
    Set ui = UiState(f)
    For Each owner In UiPendingOwners(f)
        Set c = f.Controls("txtPending_" & CStr(owner)): Set label = f.Controls("lbl_" & c.Name)
        names = "": childSep = ""
        For Each child In c.Controls
            If child.ControlType = acLabel Then names = names & childSep & J(child.Name): childSep = ","
        Next
        s = s & sep & J(CStr(owner)) & ":{""value"":" & J(c.Value) & ",""visible"":" & J(c.Visible) & ",""enabled"":" & J(c.Enabled) & ",""locked"":" & J(c.Locked) & ",""tabStop"":" & J(c.TabStop)
        s = s & ",""labelVisible"":" & J(label.Visible) & ",""labelCaption"":" & J(label.Caption) & ",""ownerLabelCaption"":" & J(f.Controls("lbl_" & CStr(owner)).Caption) & ",""ownerLabelVisible"":" & J(f.Controls("lbl_" & CStr(owner)).Visible)
        s = s & ",""attachedLabels"":" & "[" & names & "],""ownerValue"":" & J(f.Controls(CStr(owner)).Value) & ",""ownerLimitToList"":" & J(f.Controls(CStr(owner)).LimitToList) & ",""ownerBoundColumn"":" & J(f.Controls(CStr(owner)).BoundColumn) & ",""ownerListCount"":" & J(f.Controls(CStr(owner)).ListCount) & "}"
        sep = ","
    Next
    If f.Name = "frmEmployeeSearch" Then
        extras = ",""message"":" & J(f!lblSelection.Caption) & ",""searchState"":" & J(gSearchState) & ",""resultState"":" & J(gSearchResultState) & ",""listCount"":" & J(f!lstEmployees.ListCount)
    Else
        extras = ",""message"":" & J(f!lblMessage.Caption)
    End If
    Snapshot = "{""form"":" & J(f.Name) & ",""raw"":" & D(ui.Raw) & ",""accepted"":" & D(ui.AcceptedCodes) & ",""pending"":" & D(ui.Pending) & ",""acceptedCategory"":" & J(ui.AcceptedCategory) & ",""acceptedPage"":" & J(ui.AcceptedPage) & ",""acceptedListKey"":" & J(ui.AcceptedListKey) & ",""dirty"":" & J(gDirty) & ",""draftDirty"":" & J(gDraftDirty) & ",""busy"":" & J(gBusy) & ",""layoutFailure"":" & J(ui.LayoutFailure) & ",""helpers"":{" & s & "}" & extras & "}"
End Function
Private Sub CleanFixtureForms()
    Dim i As Long
    gAllowClose = True: gBusy = False: gDirty = False: gDraftDirty = False
    For i = Forms.Count - 1 To 0 Step -1: DoCmd.Close acForm, Forms(i).Name, acSaveNo: Next
    gAllowClose = False
    Set gEditor = Nothing: Set gOriginal = Nothing: Set gCode = Nothing: Set gCriteria = Nothing
    Set gSearchRaw = Nothing: Set gSearchRows = Nothing: Set gSearchReturn = Nothing: Set gAppliedCriteria = Nothing
    gAppliedValid = False: gSearchWasExecuted = False
End Sub
Private Sub Pending(ByVal f As Access.Form, ByVal owner As String, ByVal raw As String)
    Dim response As Integer
    UiNotInList f, owner, raw, response
    If response <> acDataErrContinue Then Err.Raise 5, , "NotInList did not return Continue."
End Sub
Public Function PendingApiInitialize() As String
    Dim result As clsResult
    Set result = Authenticate("admin", "123")
    PendingApiInitialize = "{""kind"":" & J(result.Kind) & ",""messageId"":" & J(result.MessageId) & "}"
End Function
Public Function RunPendingApiCase(ByVal caseId As String) As String
    Select Case caseId
    Case "F03-SIMULTANEOUS": RunPendingApiCase = PendingApiCase1()
    Case "F03-NEW-CANCEL": RunPendingApiCase = PendingApiCase2()
    Case "F04-PARENT-CHILD": RunPendingApiCase = PendingApiCase3()
    Case "F06-CATEGORY": RunPendingApiCase = PendingApiCase4()
    Case Else: Err.Raise 5, , "Unknown API case."
    End Select
End Function
Private Function PendingApiCase1() As String
    Dim f As Access.Form, source As String, before As String, after As String, second As String, third As String, fourth As String
    Dim criteria As New clsSearchCriteria, r As clsResult, row As Variant, employeeId As Long, careerCount As Long
    On Error GoTo Failed
        CleanFixtureForms: DoCmd.OpenForm "frmMenu": UiAction Forms("frmMenu"), "cmdEmployeeSearch"
        Set f = Forms("frmEmployeeSearch")
        UiSetTextValue f, "txtEmployeeNo", " 00 "
        UiSetTextValue f, "txtName", "RawName " & ChrW(&H3000)
        before = Snapshot(f)
        Pending f, "cboDepartment", "dept-unknown " & ChrW(&H3000)
        Pending f, "cboStatus", "status-unknown  "
        after = Snapshot(f)
        PendingApiCase1 = "{""before"":" & before & ",""after"":" & after & "}"
    Exit Function
Failed:
    PendingApiCase1 = "{""harnessError"":" & J(Err.Description) & ",""errorNumber"":" & J(Err.Number) & "}"
End Function

Private Function PendingApiCase2() As String
    Dim f As Access.Form, source As String, before As String, after As String, second As String, third As String, fourth As String
    Dim criteria As New clsSearchCriteria, r As clsResult, row As Variant, employeeId As Long, careerCount As Long
    On Error GoTo Failed
        Set f = Forms("frmEmployeeSearch"): before = Snapshot(f)
        UiAction f, "cmdNew"
        If Not CurrentProject.AllForms("frmEmployeeEditor").IsLoaded Then Err.Raise 5, , "New API did not open editor."
        Set f = Forms("frmEmployeeEditor"): second = Snapshot(f)
        UiAction f, "cmdCancel"
        If Not CurrentProject.AllForms("frmEmployeeSearch").IsLoaded Then Err.Raise 5, , "Untouched cancel API did not return search."
        Set f = Forms("frmEmployeeSearch"): after = Snapshot(f)
        PendingApiCase2 = "{""before"":" & before & ",""editor"":" & second & ",""after"":" & after & "}"
    Exit Function
Failed:
    PendingApiCase2 = "{""harnessError"":" & J(Err.Description) & ",""errorNumber"":" & J(Err.Number) & "}"
End Function

Private Function PendingApiCase3() As String
    Dim f As Access.Form, source As String, before As String, after As String, second As String, third As String, fourth As String
    Dim criteria As New clsSearchCriteria, r As clsResult, row As Variant, employeeId As Long, careerCount As Long
    Dim noticeBeforeApply As String
    On Error GoTo Failed
        CleanFixtureForms
        criteria.EmployeeNo = "000001": criteria.NameRaw = "": criteria.Department = Null: criteria.Status = Null
        Set r = SearchEmployees(criteria, gSession): If r.Kind <> "OK" Or r.Value.Count <> 1 Then Err.Raise 5, , "Employee fixture lookup failed."
        row = r.Value(1): employeeId = CLng(row(0))
        Set r = ReadEmployee(employeeId, gSession): If r.Kind <> "OK" Then Err.Raise 5, , "Employee fixture read failed."
        Set gEditor = r.Value: Set gOriginal = CloneEmployee(gEditor)
        DoCmd.OpenForm "frmEmployeeEditor": Set f = Forms("frmEmployeeEditor")
        If gEditor.Careers.Count < 1 Then Err.Raise 5, , "A saved career is required."
        UiForcePage f, 1: UiFocusCareer f, 1: UiForcePage f, 0
        UiSetTextValue f, "txtEmployeeName", "ParentRaw " & ChrW(&H3000): UiChanged f, "txtEmployeeName"
        before = Snapshot(f)
        Pending f, "cboDepartment", "parent-dept " & ChrW(&H3000)
        Pending f, "cboStatus", "parent-status  "
        UiForcePage f, 1
        Pending f, "cboRole", "child-role " & ChrW(&H3000)
        second = Snapshot(f)
        f!lblMessage.Caption = "": source = CStr(f!lblMessage.Caption)
        UiAction f, "cmdSave": after = Snapshot(f)
        UiClearPending f, True: third = Snapshot(f)
        UiClearPending f: UiForcePage f, 1
        Pending f, "cboRole", "role-only " & ChrW(&H3000)
        careerCount = gEditor.Careers.Count
        f!lblMessage.Caption = "": noticeBeforeApply = CStr(f!lblMessage.Caption)
        UiAction f, "cmdApplyCareer": fourth = Snapshot(f)
        PendingApiCase3 = "{""before"":" & before & ",""threePending"":" & second & ",""afterSaveRejected"":" & after & ",""afterCareerOnlyClear"":" & third & ",""afterRoleApplyRejected"":" & fourth & ",""careerCountBeforeApply"":" & J(careerCount) & ",""careerCountAfterApply"":" & J(gEditor.Careers.Count) & ",""guardNoticeBeforeSave"":" & J(source) & ",""guardNoticeBeforeApply"":" & J(noticeBeforeApply) & "}"
    Exit Function
Failed:
    PendingApiCase3 = "{""harnessError"":" & J(Err.Description) & ",""errorNumber"":" & J(Err.Number) & "}"
End Function

Private Function PendingApiCase4() As String
    Dim f As Access.Form, source As String, before As String, after As String, second As String, third As String, fourth As String
    Dim criteria As New clsSearchCriteria, r As clsResult, row As Variant, employeeId As Long, careerCount As Long
    On Error GoTo Failed
        CleanFixtureForms: DoCmd.OpenForm "frmCodeMaster": Set f = Forms("frmCodeMaster")
        If f!lstCodes.ListCount < 1 Then Err.Raise 5, , "A saved code is required."
        f!lstCodes = CStr(f!lstCodes.Column(0, 0)): UiSelected f, "lstCodes"
        If gCode Is Nothing Then Err.Raise 5, , "Code fixture selection failed."
        UiSetTextValue f, "txtCodeName", "CodeRaw " & ChrW(&H3000): UiChanged f, "txtCodeName"
        before = Snapshot(f)
        Pending f, "cboCategory", "unknown-category " & ChrW(&H3000)
        second = Snapshot(f)
        f!lblMessage.Caption = "": source = CStr(f!lblMessage.Caption)
        UiAction f, "cmdSave": after = Snapshot(f)
        PendingApiCase4 = "{""before"":" & before & ",""pending"":" & second & ",""afterSaveRejected"":" & after & ",""codeCategory"":" & J(gCode.CategoryId) & ",""codeKey"":" & J(gCode.Code) & ",""guardNoticeBeforeSave"":" & J(source) & "}"
    Exit Function
Failed:
    PendingApiCase4 = "{""harnessError"":" & J(Err.Description) & ",""errorNumber"":" & J(Err.Number) & "}"
End Function

Public Function PendingApiCleanup() As Boolean
    CleanFixtureForms
    gAllowClose = True
    PendingApiCleanup = True
End Function
Public Function PendingApiTeardownState() As String
    PendingApiTeardownState = "{""openFormCount"":" & CStr(Forms.Count) & ",""allowOwnedClose"":" & J(gAllowClose) & "}"
End Function
