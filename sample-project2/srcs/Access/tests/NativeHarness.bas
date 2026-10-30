Option Compare Binary
Option Explicit
Public Function NativeFlags() As String
    NativeFlags = CStr(gDirty) & "|" & CStr(gDraftDirty) & "|" & CStr(gBusy) & "|" & CStr(gUiLoading)
End Function
Public Function NativeViewportState() As String
    If gSearchReturn Is Nothing Then NativeViewportState = "NONE": Exit Function
    NativeViewportState = "selectedId=" & CStr(Nz(gSearchReturn.SelectedEmployeeId, "")) & "|topId=" & CStr(Nz(gSearchReturn.TopVisibleEmployeeId, "")) & "|status=" & gSearchReturn.ViewportPositionStatus
End Function
Public Function NativeLayoutFailure() As String
    On Error GoTo NoActive
    NativeLayoutFailure = UiState(Screen.ActiveForm).LayoutFailure
    Exit Function
NoActive:
    NativeLayoutFailure = "NO_ACTIVE_FORM"
End Function
Private Function NativeJsonValue(ByVal value As Variant) As String
    Dim text As String, i As Integer
    If IsNull(value) Or IsEmpty(value) Then NativeJsonValue = "null": Exit Function
    Select Case VarType(value)
    Case vbBoolean
        NativeJsonValue = LCase$(CStr(value))
    Case vbByte, vbInteger, vbLong
        NativeJsonValue = CStr(value)
    Case vbString
        text = Replace(CStr(value), "\", "\\")
        text = Replace(text, Chr$(34), "\" & Chr$(34))
        For i = 0 To 31
            text = Replace(text, Chr$(i), "\u" & Right$("0000" & Hex$(i), 4))
        Next
        NativeJsonValue = Chr$(34) & text & Chr$(34)
    Case Else
        Err.Raise vbObjectError + 1009, , "Unexpected non-scalar native observation."
    End Select
End Function
Private Function NativeDictionaryJson(ByVal values As Object) As String
    Dim key As Variant, result As String, separator As String
    For Each key In values.Keys
        result = result & separator & NativeJsonValue(CStr(key)) & ":" & NativeJsonValue(values(key))
        separator = ","
    Next
    NativeDictionaryJson = "{" & result & "}"
End Function
Private Function NativeSearchSnapshot(ByVal f As Access.Form, ByVal s As clsFormUiState) As String
    Dim result As String, name As Variant, ctl As Object, active As String, text As Variant, textAvailable As Boolean, controls As String, separator As String, extra As String
    On Error Resume Next
    active = f.ActiveControl.Name
    Err.Clear
    On Error GoTo 0
    For Each name In Array("txtEmployeeNo", "txtName", "cboDepartment", "cboStatus")
        Set ctl = f.Controls(CStr(name)): text = Null: textAvailable = False: extra = ""
        If active = CStr(name) Then
            On Error Resume Next
            text = ctl.Text: textAvailable = (Err.Number = 0)
            Err.Clear
            On Error GoTo 0
        End If
        If ctl.ControlType = acComboBox Then extra = ",""limitToList"":" & NativeJsonValue(ctl.LimitToList) & ",""boundColumn"":" & CStr(ctl.BoundColumn) & ",""listIndex"":" & CStr(ctl.ListIndex)
        controls = controls & separator & NativeJsonValue(CStr(name)) & ":{""value"":" & NativeJsonValue(ctl.Value) & ",""focused"":" & NativeJsonValue(active = CStr(name)) & ",""textAvailable"":" & NativeJsonValue(textAvailable) & ",""text"":" & NativeJsonValue(text) & extra & "}"
        separator = ","
    Next
    result = "{""form"":""frmEmployeeSearch"",""searchState"":" & NativeJsonValue(gSearchState) & ",""resultState"":" & NativeJsonValue(gSearchResultState) & ",""selectedId"":" & NativeJsonValue(gSelectedEmployee) & ",""listCount"":" & CStr(f!lstEmployees.ListCount)
    result = result & ",""shadowRaw"":" & NativeDictionaryJson(s.Raw) & ",""acceptedCodes"":" & NativeDictionaryJson(s.AcceptedCodes) & ",""pending"":" & NativeDictionaryJson(s.Pending) & ",""controls"":{" & controls & "}}"
    NativeSearchSnapshot = result
End Function
Public Function NativeSearchValues() As String
    Dim f As Access.Form, s As clsFormUiState, first As String, second As String
    If Not CurrentProject.AllForms("frmEmployeeSearch").IsLoaded Then NativeSearchValues = "{""available"":false,""reason"":""F03_NOT_LOADED""}": Exit Function
    Set f = Forms("frmEmployeeSearch")
    ' Load created this state already. These getters never call UiRaw, capture,
    ' validation, SetFocus, .Value= or any dictionary setter.
    Set s = UiState(f)
    first = NativeSearchSnapshot(f, s): second = NativeSearchSnapshot(f, s)
    NativeSearchValues = "{""available"":true,""snapshot"":" & first & ",""readOnlyObservationStable"":" & NativeJsonValue(StrComp(first, second, vbBinaryCompare) = 0) & "}"
End Function
Private Function NativeFormSnapshot(ByVal f As Access.Form, ByVal s As clsFormUiState) As String
    Dim ctl As Object, active As String, text As Variant, textAvailable As Boolean, controls As String, separator As String, extra As String
    On Error Resume Next
    active = f.ActiveControl.Name
    Err.Clear
    On Error GoTo 0
    For Each ctl In f.Controls
        If ctl.ControlType = acComboBox Or (ctl.ControlType = acTextBox And Left$(ctl.Name, 11) = "txtPending_") Then
            text = Null: textAvailable = False: extra = ""
            If active = ctl.Name Then
                On Error Resume Next
                text = ctl.Text: textAvailable = (Err.Number = 0)
                Err.Clear
                On Error GoTo 0
            End If
            If ctl.ControlType = acComboBox Then extra = ",""limitToList"":" & NativeJsonValue(ctl.LimitToList) & ",""boundColumn"":" & CStr(ctl.BoundColumn) & ",""listIndex"":" & CStr(ctl.ListIndex)
            controls = controls & separator & NativeJsonValue(ctl.Name) & ":{""value"":" & NativeJsonValue(ctl.Value) & ",""visible"":" & NativeJsonValue(ctl.Visible) & ",""enabled"":" & NativeJsonValue(ctl.Enabled) & ",""locked"":" & NativeJsonValue(ctl.Locked) & ",""tabStop"":" & NativeJsonValue(ctl.TabStop) & ",""focused"":" & NativeJsonValue(active = ctl.Name) & ",""textAvailable"":" & NativeJsonValue(textAvailable) & ",""text"":" & NativeJsonValue(text) & extra & "}"
            separator = ","
        ElseIf ctl.ControlType = acLabel And (Left$(ctl.Name, 15) = "lbl_txtPending_" Or Left$(ctl.Name, 7) = "lbl_cbo") Then
            controls = controls & separator & NativeJsonValue(ctl.Name) & ":{""caption"":" & NativeJsonValue(ctl.Caption) & ",""visible"":" & NativeJsonValue(ctl.Visible) & "}"
            separator = ","
        End If
    Next
    NativeFormSnapshot = "{""form"":" & NativeJsonValue(f.Name) & ",""acceptedCategory"":" & NativeJsonValue(s.AcceptedCategory) & ",""acceptedPage"":" & CStr(s.AcceptedPage) & ",""acceptedListKey"":" & NativeJsonValue(s.AcceptedListKey) & ",""shadowRaw"":" & NativeDictionaryJson(s.Raw) & ",""acceptedCodes"":" & NativeDictionaryJson(s.AcceptedCodes) & ",""pending"":" & NativeDictionaryJson(s.Pending) & ",""controls"":{" & controls & "}}"
End Function
Public Function NativeFormValues() As String
    Dim f As Access.Form, s As clsFormUiState, first As String, second As String
    Set f = Screen.ActiveForm
    If f.Name <> "frmEmployeeSearch" And f.Name <> "frmEmployeeEditor" And f.Name <> "frmCodeMaster" Then
        NativeFormValues = "{""available"":false,""reason"":""NON_BUSINESS_FORM_EXCLUDED""}": Exit Function
    End If
    Set s = UiState(f)
    ' Pure scalar/dictionary reads from existing state; no capture/validation/focus/value assignment.
    first = NativeFormSnapshot(f, s): second = NativeFormSnapshot(f, s)
    NativeFormValues = "{""available"":true,""snapshot"":" & first & ",""readOnlyObservationStable"":" & NativeJsonValue(StrComp(first, second, vbBinaryCompare) = 0) & "}"
End Function
Private Function NativeExpectedScrollEmployee(ByVal number As Long) As clsEmployeeEdit
    Dim e As New clsEmployeeEdit
    e.EmployeeNo = Format$(910000 + number, "000000")
    e.Name = "スクロール診断 " & Format$(number, "00")
    e.Kana = "スクロール シンダン"
    e.Department = "01": e.Status = "01": e.JoinDate = DateSerial(2020, 1, 1)
    e.Summary = "NATIVE-SCROLL-FIXTURE-v1"
    Set NativeExpectedScrollEmployee = e
End Function
Private Sub NativeRequireScrollEmployee(ByVal actual As clsEmployeeEdit, ByVal expected As clsEmployeeEdit)
    If IsNull(actual.EmployeeId) Or IsNull(actual.ExpectedRevision) Then Err.Raise vbObjectError + 993, , "Fixture identity absent."
    If CLng(actual.ExpectedRevision) <> 1 Or Not EmployeeSame(actual, expected) Then Err.Raise vbObjectError + 994, , "Existing fixture namespace differs; no reset permitted."
End Sub
Public Function NativeFixtureSearchRows() As String
    Dim criteria As New clsSearchCriteria, result As clsResult, rows As Collection, row As Variant
    Dim existing As Object, originals As New Collection, original As clsEmployeeEdit, actual As clsEmployeeEdit, expected As clsEmployeeEdit
    Dim i As Long, inserted As Long, skipped As Long, missing As Long, baselineCount As Long, originalCount As Long
    Dim suffix As String, originalIds As Variant, id As Variant
    suffix = "\.tmp\native-current\CareerManagement-native.accdb"
    If StrComp(Right$(CurrentProject.FullName, Len(suffix)), suffix, vbTextCompare) <> 0 Then Err.Raise vbObjectError + 995, , "Owned native copy required."
    If Not NativePrepare("search-unsearched", "123") Then Err.Raise vbObjectError + 996, , "Normal authentication/preparation failed."
    criteria.EmployeeNo = Null: criteria.Department = Null: criteria.Status = Null: criteria.NameRaw = ""
    Set result = SearchEmployees(criteria, gSession)
    If result.Kind <> "OK" Then Err.Raise vbObjectError + 997, , "Normal search failed."
    Set rows = result.Value: baselineCount = rows.Count
    Set existing = CreateObject("Scripting.Dictionary")
    ' Preflight ALL namespace rows and original aggregates before any insertion.
    For Each row In rows
        If Left$(CStr(row(1)), 3) = "910" Then
            i = CLng(Right$(CStr(row(1)), 3))
            If i < 1 Or i > 197 Then Err.Raise vbObjectError + 998, , "Unexpected fixture namespace row; no changes permitted."
            Set result = ReadEmployee(CLng(row(0)), gSession)
            If result.Kind <> "OK" Then Err.Raise vbObjectError + 999, , "Normal fixture read failed."
            Set actual = result.Value: Set expected = NativeExpectedScrollEmployee(i)
            NativeRequireScrollEmployee actual, expected
            existing.Add expected.EmployeeNo, True
        ElseIf CStr(row(1)) = "000001" Or CStr(row(1)) = "000002" Or CStr(row(1)) = "000003" Then
            Set result = ReadEmployee(CLng(row(0)), gSession)
            If result.Kind <> "OK" Then Err.Raise vbObjectError + 1000, , "Original employee read failed."
            Set actual = result.Value: originals.Add CloneEmployee(actual): originalCount = originalCount + 1
        End If
    Next
    If originalCount <> 3 Then Err.Raise vbObjectError + 1001, , "Three original employees must remain present."
    missing = 197 - existing.Count
    If baselineCount + missing > 200 Then Err.Raise vbObjectError + 1002, , "Normal 200-employee limit would be exceeded."
    For i = 1 To 197
        Set expected = NativeExpectedScrollEmployee(i)
        If existing.Exists(expected.EmployeeNo) Then
            skipped = skipped + 1
        Else
            Set result = SaveEmployee(expected, gSession)
            If result.Kind <> "OK" Then Err.Raise vbObjectError + 1003, , "Normal employee save failed; no reset attempted."
            Set actual = result.Value: NativeRequireScrollEmployee actual, expected
            inserted = inserted + 1
        End If
    Next
    For Each original In originals
        Set result = ReadEmployee(CLng(original.EmployeeId), gSession)
        If result.Kind <> "OK" Then Err.Raise vbObjectError + 1004, , "Original employee reread failed."
        Set actual = result.Value
        If Not Same(actual.EmployeeId, original.EmployeeId) Or Not Same(actual.ExpectedRevision, original.ExpectedRevision) Or Not EmployeeSame(actual, original) Then Err.Raise vbObjectError + 1005, , "Original aggregate changed."
    Next
    Set result = SearchEmployees(criteria, gSession)
    If result.Kind <> "OK" Then Err.Raise vbObjectError + 1006, , "Final normal search failed."
    Set rows = result.Value
    If rows.Count <> baselineCount + inserted Then Err.Raise vbObjectError + 1007, , "Unexpected final employee count."
    If Not NativePrepare("search", "123") Then Err.Raise vbObjectError + 1008, , "Final screen preparation failed."
    NativeFixtureSearchRows = "inserted=" & CStr(inserted) & "|skipped=" & CStr(skipped) & "|originalsPreserved=3|total=" & CStr(rows.Count)
End Function
Public Function NativePrepare(ByVal target As String, Optional ByVal password As String = "") As Boolean
    Dim n As Variant, f As Access.Form, result As clsResult
    EnsureSession
    If gDirty Or gDraftDirty Or gBusy Then Err.Raise vbObjectError + 990, , "Resolve current edits using the native UI before preparation."
    For Each n In Array("frmLogin", "frmMenu", "frmEmployeeSearch", "frmEmployeeEditor", "frmCodeMaster")
        If CurrentProject.AllForms(CStr(n)).IsLoaded Then
            If UiState(Forms(CStr(n))).Pending.Count > 0 Then Err.Raise vbObjectError + 991, , "Resolve Pending using native UI before preparation."
        End If
    Next
    If target = "login" Then LogoutNow: NativePrepare = True: Exit Function
    If Not gSession.IsAuthenticated Then
        If password = "" Then Err.Raise vbObjectError + 992, , "Explicit public DEMO API authentication required."
        Set result = Authenticate("admin", password): password = ""
        If result.Kind <> "OK" Then Exit Function
    End If
    gAllowClose = True
    For Each n In Array("frmEmployeeEditor", "frmCodeMaster", "frmEmployeeSearch", "frmMenu", "frmLogin")
        If CurrentProject.AllForms(CStr(n)).IsLoaded Then DoCmd.Close acForm, CStr(n), acSaveNo
    Next
    gAllowClose = False
    DoCmd.OpenForm "frmMenu"
    If target = "menu" Then NativePrepare = True: Exit Function
    If target = "code" Then UiAction Forms("frmMenu"), "cmdCodeMaster": NativePrepare = True: Exit Function
    UiAction Forms("frmMenu"), "cmdEmployeeSearch"
    Set f = Forms("frmEmployeeSearch")
    If target = "search-unsearched" Then NativePrepare = True: Exit Function
    UiAction f, "cmdSearch"
    If target = "search" Then NativePrepare = True: Exit Function
    If target = "editor-new" Then UiAction f, "cmdNew": NativePrepare = True: Exit Function
    If f!lstEmployees.ListCount = 0 Then Exit Function
    f!lstEmployees = CLng(f!lstEmployees.Column(0, 0)): UiSelected f, "lstEmployees"
    UiAction f, "cmdEdit"
    If target = "careers" Then
        Forms("frmEmployeeEditor")!tabEmployee = 1
        UiSelected Forms("frmEmployeeEditor"), "tabEmployee"
    End If
    NativePrepare = True
End Function
