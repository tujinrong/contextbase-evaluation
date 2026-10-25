Attribute VB_Name = "modPostalPasteTests"
Option Explicit
Option Compare Binary

' Imported into the owned disposable ACCDB only. Handler calls and native paste probes are reported separately.
Private Declare PtrSafe Function GetFocus Lib "user32" () As LongPtr
Private Declare PtrSafe Function SendMessageW Lib "user32" (ByVal hwnd As LongPtr, ByVal message As Long, ByVal wParam As LongPtr, ByVal lParam As LongPtr) As LongPtr
Private assertions As Long
Private checks As String
Private originalRows As Long

Private Sub VerifyPostal(ByVal condition As Boolean, ByVal label As String)
    assertions = assertions + 1
    checks = checks & IIf(condition, "PASS", "FAIL") & "|" & label & vbCrLf
    If Not condition Then Err.Raise vbObjectError + 198, , label
End Sub

Public Function PostalPasteTestLog() As String
    PostalPasteTestLog = checks
End Function

Public Function PostalPasteAssertions() As Long
    PostalPasteAssertions = assertions
End Function

Private Function PostalCodeOnly(ByVal line As String) As String
    Dim i As Long, c As String, quoted As Boolean
    If UCase$(Left$(LTrim$(line), 4)) = "REM " Then Exit Function
    For i = 1 To Len(line)
        c = Mid$(line, i, 1)
        If c = """" Then
            If quoted And i < Len(line) Then
                If Mid$(line, i + 1, 1) = """" Then i = i + 1: GoTo NextCharacter
            End If
            quoted = Not quoted
        ElseIf Not quoted Then
            If c = "'" Then Exit For
            PostalCodeOnly = PostalCodeOnly & c
        End If
NextCharacter:
    Next
End Function

Public Function PostalProductPasteContract() As String
    Dim component As Object, rx As Object, line As Long, count As Long, code As String, found As String
    On Error GoTo Failed
    Set rx = CreateObject("VBScript.RegExp")
    rx.Pattern = "\bRunCommand\s*\(?\s*acCmdPaste\b": rx.IgnoreCase = True
    For Each component In Application.VBE.ActiveVBProject.VBComponents
        If component.Name <> "modPostalPasteTests" Then
            count = count + 1: code = ""
            For line = 1 To component.CodeModule.CountOfLines
                code = code & " " & PostalCodeOnly(component.CodeModule.Lines(line, 1))
            Next
            code = Replace(code, "_", " ")
            If rx.Test(code) Then found = found & component.Name & ";"
        End If
    Next
    VerifyPostal count > 5, "production VBA modules and form modules were inspected independently in the built copy"
    VerifyPostal found = "", "generated application does not call programmatic RunCommand acCmdPaste; supported UI uses PostalPaste"
    PostalProductPasteContract = "PASS|components=" & CStr(count)
    Exit Function
Failed:
    PostalProductPasteContract = "FAIL|" & CStr(Err.Number) & "|" & Err.Description & "|components=" & found
End Function

Public Function PostalFixtureInitialize() As String
    On Error GoTo Failed
    assertions = 0: checks = ""
    originalRows = DCount("*", "m_student")
    VerifyPostal originalRows > 0, "seeded source has existing students for readback"
    VerifyPostal CurrentRole() <> "Reader", "existing authenticated sample role permits editing"
    DoCmd.OpenForm "frmStudentEdit", acNormal, , , , acWindowNormal, "|"
    Forms("frmStudentEdit").Visible = True
    VerifyPostal Not Forms("frmStudentEdit")!txtStudentNo.Locked, "new form initialized successfully with editable business key"
    VerifyPostal Forms("frmStudentEdit")!txtPostalCode.InputMask = "000\-0000;1;_", "seven-position native mask with nonstored separator"
    PostalFixtureInitialize = "PASS"
    Exit Function
Failed:
    PostalFixtureInitialize = "FAIL|" & CStr(Err.Number) & "|" & Err.Description
End Function

Public Function PostalFixtureCase(ByVal label As String, ByVal route As String, ByVal expected As String, ByVal accepted As Boolean) As String
    Dim frm As Access.Form, code As Integer, modifiers As Integer, prior As String, displayed As String
    On Error GoTo Failed
    Set frm = Forms("frmStudentEdit"): prior = "5555555"
    frm!txtPostalCode = prior: frm!lblMessage.Caption = ""
    frm!txtPostalCode.SetFocus
    frm!txtPostalCode.SelStart = 0: frm!txtPostalCode.SelLength = Len(frm!txtPostalCode.Text)
    Select Case route
    Case "CtrlV": code = vbKeyV: modifiers = 2
    Case "ShiftInsert": code = vbKeyInsert: modifiers = 1
    Case Else: Err.Raise vbObjectError + 198, , "Unsupported route"
    End Select
    PostalKeyDown code, modifiers
    VerifyPostal code = 0, label & ": native default paste is suppressed by event bridge"
    displayed = frm!txtPostalCode.Text
    If accepted Then
        VerifyPostal Nz(frm!txtPostalCode.Value, "NULL") = expected, label & ": complete clipboard normalizes to expected seven digits"
        VerifyPostal displayed = Left$(expected, 3) & "-" & Mid$(expected, 4), label & ": real masked Text is 3-4"
        VerifyPostal frm!lblMessage.Caption = "", label & ": successful paste clears error"
        frm!txtStudentName.SetFocus
        VerifyPostal Nz(frm!txtPostalCode.Value, "NULL") = expected, label & ": committing field keeps seven digits and leading zeros"
    Else
        VerifyPostal Nz(frm!txtPostalCode.Value, "NULL") = prior, label & ": rejected complete clipboard leaves prior Value intact"
        VerifyPostal displayed = "555-5555", label & ": rejected clipboard leaves masked Text intact"
        VerifyPostal frm!lblMessage.Caption = MessageText("E-STU-015"), label & ": postal-specific error text is shown"
    End If
    PostalFixtureCase = "PASS"
    Exit Function
Failed:
    PostalFixtureCase = "FAIL|" & CStr(Err.Number) & "|" & Err.Description
End Function

Public Function PostalFixtureExisting() As String
    Dim db As DAO.Database, rs As DAO.Recordset, id As Long, stored As String, version As Long
    Dim frm As Access.Form
    On Error GoTo Failed
    Set db = CurrentDb
    Set rs = db.OpenRecordset("SELECT TOP 1 student_id,postal_code,row_version FROM m_student WHERE is_deleted=False ORDER BY student_id", dbOpenSnapshot)
    id = rs!student_id: stored = rs!postal_code: version = rs!row_version: rs.Close
    PostalFixtureCloseForm
    DoCmd.OpenForm "frmStudentEdit", acNormal, , , , acWindowNormal, CStr(id) & "|"
    Set frm = Forms("frmStudentEdit"): frm.Visible = True
    VerifyPostal frm!txtStudentNo.Locked, "existing record keeps immutable business key locked"
    VerifyPostal Nz(frm!txtPostalCode.Value, "NULL") = stored, "existing saved postal Value loads exactly"
    frm!txtPostalCode.SetFocus
    VerifyPostal frm!txtPostalCode.Text = Left$(stored, 3) & "-" & Mid$(stored, 4), "existing saved postal Text displays 3-4"
    VerifyPostal CLng(DLookup("row_version", "m_student", "student_id=" & CStr(id))) = version, "opening masked existing record does not change its version"
    PostalFixtureExisting = "PASS"
    Exit Function
Failed:
    PostalFixtureExisting = "FAIL|" & CStr(Err.Number) & "|" & Err.Description
End Function

Public Function PostalFixtureServiceRejects(ByVal postal As String, ByVal expectedCode As String) As String
    Dim db As DAO.Database, rs As DAO.Recordset, raw As Object, k As Variant, parts As Variant, result As Object
    Dim service As New clsStudentService, confirmation As New clsConfirmation, beforeRows As Long, beforeAudit As Long
    On Error GoTo Failed
    Set db = CurrentDb
    Set rs = db.OpenRecordset("SELECT TOP 1 * FROM m_student WHERE is_deleted=False ORDER BY student_id", dbOpenSnapshot)
    Set raw = Map()
    For Each k In SavedFields(): raw.Add k, rs.Fields(k).Value: Next
    parts = BirthParts(rs!birth_date): rs.Close
    raw.Remove "birth_date"
    raw.Add "birth_era", parts(0): raw.Add "birth_year", parts(1): raw.Add "birth_month", parts(2): raw.Add "birth_day", parts(3)
    raw.Add "school_year", Null: raw.Add "grade_code", Null
    raw("student_no") = "POSTAL-NEW": raw("postal_code") = postal
    beforeRows = DCount("*", "m_student"): beforeAudit = DCount("*", "t_operation_log")
    Set result = service.SaveStudent(raw, Null, Null, "postal-raw-reject", confirmation, False, Null)
    VerifyPostal result("kind") <> "Saved" And result("kind") <> "ConfirmationRequired", "raw service call rejects postal input outside UI mask"
    VerifyPostal Split(CStr(result("message")), "|")(0) = expectedCode, "raw service rejection has expected postal/length code " & expectedCode
    VerifyPostal DCount("*", "m_student") = beforeRows And DCount("*", "t_operation_log") = beforeAudit, "rejected raw service call changes neither students nor audits"
    PostalFixtureServiceRejects = "PASS"
    Exit Function
Failed:
    PostalFixtureServiceRejects = "FAIL|" & CStr(Err.Number) & "|" & Err.Description
End Function

Public Function PostalFixtureNativeProbe(ByVal route As String, ByVal expectedAccepted As Boolean) As String
    Dim frm As Access.Form, text As String, value As String, number As Long, hwnd As LongPtr, postalMessage As String
    Dim ribbon As String, activeControl As String, postalActive As String, guardActive As String, menu As String, button As Object
    On Error GoTo Failed
    Set frm = Forms("frmStudentEdit")
    frm!txtPostalCode = "5555555": frm!lblMessage.Caption = ""
    frm!txtPostalCode.SetFocus
    frm!txtPostalCode.SelStart = 0: frm!txtPostalCode.SelLength = Len(frm!txtPostalCode.Text)
    ribbon = frm.RibbonName: activeControl = Screen.ActiveControl.Name
    postalActive = CStr(PostalInputActive()): guardActive = CStr(PostalPasteGuardActive())
    menu = frm!txtPostalCode.ShortcutMenuBar
    VerifyPostal PostalPasteGuardActive(), "native paste probe has the owned focused edit guard installed"
    If route = "RunCommand" Then
        DoCmd.RunCommand acCmdPaste
    ElseIf route = "Ribbon" Then
        Application.CommandBars.ExecuteMso "Paste"
    ElseIf route = "Popup" Then
        VerifyPostal Len(menu) > 0, "postal native popup has an explicitly assigned menu"
        Set button = Application.CommandBars(menu).Controls(4)
        VerifyPostal button.Tag = "StudentPostalValidatedPaste" And button.OnAction = "=PostalPaste()", "actual native popup Paste button calls the validated bridge"
        Call button.Execute
    ElseIf route = "WM_PASTE" Then
        hwnd = GetFocus()
        If hwnd = 0 Then Err.Raise vbObjectError + 198, , "Native edit focus handle unavailable"
        SendMessageW hwnd, &H302, 0, 0
    Else
        Err.Raise vbObjectError + 198, , "Unsupported native paste route"
    End If
    DoEvents
    text = frm!txtPostalCode.Text
    ' Native Access edits keep Text separate from Value until focus commits a valid field.
    If expectedAccepted Then frm!txtStudentName.SetFocus
Done:
    On Error Resume Next
    value = Nz(frm!txtPostalCode.Value, "NULL")
    postalMessage = IIf(frm!lblMessage.Caption = "", "EMPTY", IIf(frm!lblMessage.Caption = MessageText("E-STU-015"), "POSTAL_ERROR", "OTHER_ERROR"))
    frm!txtPostalCode.Undo
    frm!txtPostalCode = "5555555"
    PostalFixtureNativeProbe = CStr(number) & "|" & text & "|" & value & "|" & postalMessage & "|" & ribbon & "|" & activeControl & "|" & postalActive & "|" & guardActive & "|" & menu
    Exit Function
Failed:
    number = Err.Number
    On Error Resume Next
    text = frm!txtPostalCode.Text
    GoTo Done
End Function

Private Sub PostalFixtureCloseForm()
    If CurrentProject.AllForms("frmStudentEdit").IsLoaded Then
        If Not DetachPostalPasteGuard() Then Err.Raise vbObjectError + 198, , "Fixture could not detach its owned native paste guard"
        ' The copy is disposable and no row is saved; bypass only its unsaved-close prompt.
        Forms("frmStudentEdit").OnUnload = ""
        DoCmd.Close acForm, "frmStudentEdit", acSaveNo
    End If
End Sub

Public Function PostalFixtureCleanup() As String
    On Error GoTo Failed
    PostalFixtureCloseForm
    VerifyPostal DCount("*", "m_student") = originalRows, "suite did not add or delete any student rows"
    PostalFixtureCleanup = "PASS"
    Exit Function
Failed:
    PostalFixtureCleanup = "FAIL|" & CStr(Err.Number) & "|" & Err.Description
End Function
