Attribute VB_Name = "modNativeQualityTests"
Option Explicit
Option Compare Binary

' Imported only into the disposable native-quality copy, never into the product.
Private Declare PtrSafe Function GetFocus Lib "user32" () As LongPtr
Private Declare PtrSafe Function SendMessageW Lib "user32" (ByVal hwnd As LongPtr, ByVal message As Long, ByVal wParam As LongPtr, ByVal lParam As LongPtr) As LongPtr
Private results As String

Private Sub Verify(ByVal passed As Boolean, ByVal name As String, Optional ByVal detail As String = "")
    results = results & IIf(passed, "PASS", "FAIL") & "|" & name & "|" & Replace(Replace(detail, vbCr, " "), vbLf, " ") & vbCrLf
End Sub

Private Sub NativeType(ByVal ctl As Access.TextBox, ByVal value As String)
    Dim hwnd As LongPtr, i As Long, key As Long
    ctl.SetFocus
    ctl.SelStart = 0: ctl.SelLength = Len(ctl.Text)
    hwnd = GetFocus()
    If hwnd = 0 Then Err.Raise vbObjectError + 190, , "Native edit window has no keyboard focus"
    SendMessageW hwnd, &H100, vbKeyDelete, 1
    SendMessageW hwnd, &H101, vbKeyDelete, 1
    For i = 1 To Len(value)
        key = AscW(Mid$(value, i, 1)) And &HFFFF&
        SendMessageW hwnd, &H102, key, 1
    Next
    DoEvents
End Sub

Private Sub Snapshot(ByVal frm As Access.Form, ByVal values As Object)
    Dim ctl As Access.Control
    For Each ctl In frm.Controls
        If ctl.ControlType = acTextBox Or ctl.ControlType = acComboBox Then values.Add ctl.Name, ctl.Value
    Next
End Sub

Private Sub Restore(ByVal frm As Access.Form, ByVal values As Object)
    Dim key As Variant
    On Error Resume Next
    For Each key In values.Keys
        frm.Controls(key).Value = values(key)
    Next
    frm!txtStudentName.SetFocus
End Sub

Private Sub VerifyGeometry(ByVal frm As Access.Form)
    Dim ctl As Access.Control, other As Access.Control, checked As Long, overlap As String
    Dim fontCount As Long, badFont As String, badBounds As String
    For Each ctl In frm.Controls
        If ctl.Visible Then
            If ctl.Left < 0 Or ctl.Top < 0 Or ctl.Left + ctl.Width > frm.Width Or ctl.Top + ctl.Height > frm.Section(acDetail).Height Then badBounds = badBounds & ctl.Name & ";"
            If ctl.ControlType <> acRectangle And ctl.ControlType <> acCheckBox Then
                fontCount = fontCount + 1
                If ctl.FontName <> "Yu Gothic UI" Or ctl.FontSize <> 11 Then badFont = badFont & ctl.Name & ";"
                If ctl.ControlType = acLabel And ctl.Height < 330 Then badFont = badFont & ctl.Name & ":height;"
            End If
        End If
        If ctl.Visible And (ctl.ControlType = acTextBox Or ctl.ControlType = acComboBox Or ctl.ControlType = acCommandButton) Then
            checked = checked + 1
            For Each other In frm.Controls
                If other.Visible And StrComp(ctl.Name, other.Name, vbBinaryCompare) < 0 Then
                    If other.ControlType = acTextBox Or other.ControlType = acComboBox Or other.ControlType = acCommandButton Then
                        If ctl.Left < other.Left + other.Width And other.Left < ctl.Left + ctl.Width And ctl.Top < other.Top + other.Height And other.Top < ctl.Top + ctl.Height Then overlap = overlap & ctl.Name & "/" & other.Name & ";"
                    End If
                End If
            Next
        End If
    Next
    Verify fontCount > 10 And badFont = "", frm.Name & ": explicit readable Japanese font and label height", badFont
    Verify badBounds = "", frm.Name & ": controls remain in fixed form bounds", badBounds
    Verify checked > 10 And overlap = "", frm.Name & ": interactive controls do not overlap", overlap
    Verify frm.DefaultView = 0 And frm.RecordSource = "", frm.Name & ": native unbound single form"
    Verify frm.AllowEdits And frm.AllowAdditions And Not frm.AllowDeletions, frm.Name & ": deterministic form edit permissions"
    Verify Not frm.RecordSelectors And Not frm.NavigationButtons, frm.Name & ": native record chrome omitted for unbound workflow"
End Sub

Public Function NativeQualityTests() As String
    Dim frm As Access.Form, original As Object, oldValues As Object, name As Variant, rectangle As Access.Control, label As Access.Control
    Dim record As DAO.Recordset, existingId As Long, expectedNo As String, oldPostal As Variant, typed As String, count As Long
    Dim stage As String, formName As String, service As New clsStudentService, confirmation As New clsConfirmation, saved As Object, raw As Object, fields As Variant, controls As Variant, i As Long, savedId As Long
    results = ""
    On Error GoTo Failed
    stage = "Direct edit before any search initialization"
    DoCmd.OpenForm "frmStudentEdit", , , , , acHidden, "|"
    Set frm = Forms("frmStudentEdit"): Set original = CreateObject("Scripting.Dictionary")
    Snapshot frm, original
    Verify InStr(frm!lblTitle.Caption, "新規") > 0 And InStr(frm!lblMessage.Caption, "初期化") = 0, "Direct new form before search: initialization completes", frm!lblMessage.Caption
    Verify Not frm!txtStudentNo.Locked And frm!txtStudentNo.Enabled And frm!cmdSave.Enabled, "Direct new form before search: business key and save are enabled"
    If Not frm!cmdSave.Enabled Then Err.Raise vbObjectError + 194, , "Direct new form initialization failed"
    frm.Visible = True
    NativeType frm!txtStudentNo, "QA-DIRECT-001"
    frm!txtStudentName.SetFocus
    Verify Nz(frm!txtStudentNo.Value, "") = "QA-DIRECT-001", "Direct new form before search: actual native business key input succeeds"
    Restore frm, original
    Verify Not EditHasChanges(frm), "Direct new form before search: restoring raw input clears the draft"
    DoCmd.Close acForm, frm.Name, acSaveNo
    Set frm = Nothing: Set original = Nothing
    stage = "Open search"
    DoCmd.OpenForm "frmStudentSearch", , , , , acHidden
    Set frm = Forms("frmStudentSearch")
    VerifyGeometry frm
    Verify frm!txtStudentNo.Enabled And Not frm!txtStudentNo.Locked And frm!txtStudentNo.TabStop, "Search prefix: keyboard entry enabled"
    Verify frm!txtSelectedDetails.Locked And frm!txtSelectedDetails.TabStop, "Selected details: readonly copy and native zoom remain available"
    Verify frm!txtStudentNo.TabIndex < frm!txtName.TabIndex And frm!txtName.TabIndex < frm!cboClass.TabIndex, "Search: logical condition tab order"
    Verify frm!lstStudents.RowSource = "", "Search: user-defined row callback has no inherited query source"
    frm!IsBusy = True
    On Error Resume Next
    DoCmd.Close acForm, frm.Name, acSaveNo
    Err.Clear
    On Error GoTo Failed
    Verify CurrentProject.AllForms("frmStudentSearch").IsLoaded, "Search: native close is cancelled during busy processing"
    If Not CurrentProject.AllForms("frmStudentSearch").IsLoaded Then Err.Raise vbObjectError + 195, , "Busy form was unexpectedly unloaded"
    frm!IsBusy = False
    DoCmd.Close acForm, frm.Name, acSaveNo
    Verify Not CurrentProject.AllForms("frmStudentSearch").IsLoaded, "Search: native close succeeds after busy processing ends"

    stage = "Open new student"
    DoCmd.OpenForm "frmStudentEdit", , , , , acHidden, "|"
    Set frm = Forms("frmStudentEdit"): Set original = CreateObject("Scripting.Dictionary")
    Snapshot frm, original
    VerifyGeometry frm
    Verify InStr(frm!lblTitle.Caption, "新規") > 0 And InStr(frm!lblMessage.Caption, "初期化") = 0, "New student: initialization reaches editable state", frm!lblMessage.Caption
    Verify frm!txtStudentId.Locked And Not frm!txtStudentId.TabStop And IsNull(frm!txtStudentId.Value), "Internal management key: automatic and outside tab order"
    Verify Not frm!txtStudentNo.Locked And frm!txtStudentNo.Enabled And frm!txtStudentNo.TabStop, "New business key: editable and focusable"
    Verify frm!txtStudentNo.TabIndex = 0, "New business key: first tab stop"
    For Each name In Array("grpBasic", "grpContact", "grpEnrollment", "grpEmergency", "grpRemarks")
        Set rectangle = frm.Controls(name): Set label = frm.Controls("lbl" & name)
        Verify rectangle.ControlType = acRectangle And rectangle.BackStyle = 0, CStr(name) & ": decorative rectangle has no option value"
        Verify label.BackStyle = 1 And label.BackColor = frm.Section(acDetail).BackColor And label.Width < rectangle.Width / 2 And label.Left > rectangle.Left And label.Top < rectangle.Top And label.Top + label.Height > rectangle.Top, CStr(name) & ": compact native caption crosses frame edge"
    Next
    Verify frm!txtPostalCode.InputMask = "000\-0000;1;_", "Postal code: seven required digit mask excludes display hyphen from value", frm!txtPostalCode.InputMask
    Verify frm!txtPostalCode.OnKeyPress = "[Event Procedure]" And frm!txtPostalCode.OnKeyDown = "[Event Procedure]" And frm!txtPostalCode.BeforeUpdate = "[Event Procedure]", "Postal code: native typing paste and commit event bridges are wired"
    Verify frm.ShortcutMenu And Left$(frm!txtPostalCode.ShortcutMenuBar, 14) = "StudentPostal_", "Postal code: native context menu is attached to the field"
    Verify Application.CommandBars(frm!txtPostalCode.ShortcutMenuBar).Controls(4).OnAction = "=PostalPaste()", "Postal code: context Paste uses whole-value validation"
    Verify frm!txtPhoneNumber.InputMask = "" And frm!txtEmergencyPhoneNumber.InputMask = "", "Variable telephone formats: no invented fixed digit mask"
    Verify frm!txtAdmissionDate.InputMask = "" And frm!txtEnrollmentEndDate.InputMask = "", "ISO date normalization: fullwidth input contract remains available"
    Verify frm!txtBirthYear.TabIndex < frm!txtBirthMonth.TabIndex And frm!txtBirthMonth.TabIndex < frm!txtBirthDay.TabIndex And frm!txtBirthDay.TabIndex < frm!cboGender.TabIndex, "Birth date: era year month day follow logical order"

    stage = "Native new business key typing"
    frm.Visible = True
    NativeType frm!txtStudentNo, "QA-NATIVE-001"
    frm!txtStudentName.SetFocus
    Verify Nz(frm!txtStudentNo.Value, "") = "QA-NATIVE-001", "New business key: native WM_CHAR typing changes actual control value", Nz(frm!txtStudentNo.Value, "NULL")
    frm!txtStudentNo = original("txtStudentNo")

    stage = "Native postal typing"
    NativeType frm!txtPostalCode, "0123456"
    Verify PostalPasteGuardActive(), "Postal code: focused native edit owns the paste guard"
    typed = frm!txtPostalCode.Text
    Verify typed = "012-3456", "Postal code: native edit displays 3-4 including leading zero", typed
    frm!txtStudentName.SetFocus
    Verify Not PostalPasteGuardActive(), "Postal code: leaving the field detaches the native paste guard"
    Verify Nz(frm!txtPostalCode.Value, "") = "0123456", "Postal code: committed native value has exactly seven digits", Nz(frm!txtPostalCode.Value, "NULL")
    NativeType frm!txtPostalCode, "0012345"
    frm!txtStudentName.SetFocus
    Verify Nz(frm!txtPostalCode.Value, "") = "0012345", "Postal code: two leading zeros survive replacement and commit", Nz(frm!txtPostalCode.Value, "NULL")
    NativeType frm!txtPostalCode, "１２３４５６７"
    typed = frm!txtPostalCode.Text
    frm!txtStudentName.SetFocus
    Verify Nz(frm!txtPostalCode.Value, "") = "1234567" And typed = "123-4567", "Postal code: fullwidth WM_CHAR digits normalize before native mask", typed
    NativeType frm!txtPostalCode, "01234567"
    typed = frm!txtPostalCode.Text
    frm!txtStudentName.SetFocus
    Verify typed = "012-3456" And Nz(frm!txtPostalCode.Value, "") = "0123456", "Postal code: eighth typed digit cannot create an eighth position", typed
    NativeType frm!txtPostalCode, "ABCDEF0"
    typed = frm!txtPostalCode.Text
    Verify InStr(typed, "A") = 0 And InStr(typed, "B") = 0 And InStr(typed, "C") = 0, "Postal code: alphabetic WM_CHAR input is refused by native mask", typed
    frm!txtPostalCode.Undo
    frm!txtPostalCode = "0012345"
    frm!txtStudentName.SetFocus

    stage = "Save typed new key through actual business service"
    NativeType frm!txtStudentNo, "QA-NATIVE-001"
    frm!txtStudentName.SetFocus
    frm!txtStudentName = "試験 新生": frm!txtStudentNameKana = "シケン シンセイ"
    frm!cboBirthEra = "HEISEI": frm!txtBirthYear = "20": frm!txtBirthMonth = "05": frm!txtBirthDay = "15"
    frm!cboGender = "0": frm!cboPrefecture = "13": frm!txtAddressLine1 = "見本市試験町1-2"
    frm!txtPhoneNumber = "03-0000-0000": frm!txtAdmissionDate = CStr(frm!cboSchoolYear.Value) & "-04-01"
    frm!cboEnrollmentStatus = "01"
    Set record = CurrentDb.OpenRecordset("SELECT TOP 1 class_id FROM m_class WHERE is_active=True ORDER BY class_id", dbOpenSnapshot)
    If record.EOF Then Err.Raise vbObjectError + 193, , "Sample class missing"
    frm!cboClass = record!class_id: record.Close
    Set raw = CreateObject("Scripting.Dictionary"): fields = SavedFields(): controls = FieldControls()
    For i = 0 To UBound(fields)
        If fields(i) <> "birth_date" Then raw.Add fields(i), frm.Controls(controls(i)).Value
    Next
    raw.Add "birth_era", frm!cboBirthEra.Value: raw.Add "birth_year", frm!txtBirthYear.Value
    raw.Add "birth_month", frm!txtBirthMonth.Value: raw.Add "birth_day", frm!txtBirthDay.Value
    raw.Add "school_year", frm!cboSchoolYear.Value: raw.Add "grade_code", frm!cboGrade.Value
    Set saved = service.SaveStudent(raw, Null, Null, GuidText(), confirmation, False, Null)
    Verify saved("kind") = "Saved", "New form raw values: actual service creates a record", saved("kind") & ": " & saved("message")
    If saved("kind") = "Saved" Then
        Set record = CurrentDb.OpenRecordset("SELECT student_id,postal_code FROM m_student WHERE student_no='QA-NATIVE-001'", dbOpenSnapshot)
        savedId = record!student_id
        Verify record!postal_code = "0012345", "New form: persistence stores seven postal digits with leading zeros", record!postal_code
        record.Close
    End If
    Restore frm, original
    Verify Not EditHasChanges(frm), "New student: restoring raw values clears unsaved change detection"
    DoCmd.Close acForm, frm.Name, acSaveNo

    If savedId > 0 Then
        stage = "Reopen newly saved student"
        DoCmd.OpenForm "frmStudentEdit", , , , , acHidden, CStr(savedId) & "|"
        Set frm = Forms("frmStudentEdit")
        Verify frm!txtStudentNo.Value = "QA-NATIVE-001" And frm!txtStudentNo.Locked, "Newly saved form: business key reloads as immutable"
        Verify frm!txtPostalCode.Value = "0012345", "Newly saved form: postal digits survive reopen"
        Verify Not EditHasChanges(frm), "Newly saved form: initial read does not create unsaved changes"
        DoCmd.Close acForm, frm.Name, acSaveNo
    End If

    stage = "Existing student key and reload"
    Set record = CurrentDb.OpenRecordset("SELECT TOP 1 student_id,student_no,postal_code FROM m_student WHERE is_deleted=False ORDER BY student_id", dbOpenSnapshot)
    If record.EOF Then Err.Raise vbObjectError + 191, , "Native regression needs seeded sample students"
    existingId = record!student_id: expectedNo = record!student_no: oldPostal = record!postal_code
    record.Close
    DoCmd.OpenForm "frmStudentEdit", , , , , acHidden, CStr(existingId) & "|"
    Set frm = Forms("frmStudentEdit"): Set oldValues = CreateObject("Scripting.Dictionary")
    Snapshot frm, oldValues
    Verify frm!txtStudentNo.Locked And frm!txtStudentNo.Enabled, "Existing business key: readonly and still copyable"
    Verify Nz(frm!txtStudentNo.Value, "") = expectedNo, "Existing business key: exact value loads"
    frm.Visible = True
    frm!txtStudentNo.SetFocus
    SendMessageW GetFocus(), &H102, AscW("X"), 1
    frm!txtStudentName.SetFocus
    Verify Nz(frm!txtStudentNo.Value, "") = expectedNo, "Existing business key: native typing cannot change immutable value"
    frm!txtPostalCode.SetFocus
    Verify frm!txtPostalCode.Text = Left$(CStr(oldPostal), 3) & "-" & Mid$(CStr(oldPostal), 4), "Existing postal code: seven stored digits render 3-4", frm!txtPostalCode.Text
    frm!txtStudentName.SetFocus
    CurrentDb.Execute "UPDATE m_student SET remarks='最新再読込の試験',row_version=row_version+1 WHERE student_id=" & CStr(existingId), dbFailOnError
    ResetEdit True
    Verify Nz(frm!txtRemarks.Value, "") = "最新再読込の試験", "Existing student: latest reload reads an externally changed record"
    Verify Nz(frm!txtStudentNo.Value, "") = expectedNo And Nz(frm!txtPostalCode.Value, "") = CStr(oldPostal), "Existing student: latest reload preserves immutable key and exact postal digits"
    Verify Not EditHasChanges(frm), "Existing student: read and reload do not create a dirty draft"
    DoCmd.Close acForm, frm.Name, acSaveNo
    Set frm = Nothing
    NativeQualityTests = results
    Exit Function
Failed:
    Verify False, "Fatal native quality regression", stage & ": " & Err.Number & " " & Err.Description
    On Error Resume Next
    If Not frm Is Nothing Then
        If frm.Name = "frmStudentEdit" Then
            If Not oldValues Is Nothing Then
                Restore frm, oldValues
            ElseIf Not original Is Nothing Then
                Restore frm, original
            End If
        End If
        DoCmd.Close acForm, frm.Name, acSaveNo
    End If
    NativeQualityTests = results
End Function

