Attribute VB_Name = "modStudentForms"
Option Explicit
Option Compare Binary
Private contexts As Object
Private listRows As Object
Private edits As Object
Private initializes As Boolean

Private Sub EnsureMaps()
    If contexts Is Nothing Then Set contexts = Map()
    If listRows Is Nothing Then Set listRows = Map()
    If edits Is Nothing Then Set edits = Map()
End Sub
Public Function InitSearch(ByVal frm As Access.Form) As Boolean
    Dim ctx As clsSearchContext
    Dim stage As String
    On Error GoTo Failed
    Set ctx = New clsSearchContext
    stage = "EnsureMaps": EnsureMaps
    stage = "Authorize": Authorize "Read"
    stage = "SetTag": frm.Tag = GuidText()
    stage = "ResetContext": ctx.Reset frm.Tag: frm!txtContextRevision = ctx.Revision: frm!txtContextId = ctx.ContextId
    stage = "AddContext": contexts.Add frm.Tag, ctx
    initializes = True
    stage = "SearchChoices": RefreshSearchChoices frm
    SetSearchAllSelections frm
    stage = "Defaults": frm!chkEnrolled = True: frm!chkLeave = True
    frm!chkGraduated = False: frm!chkWithdrawn = False
    frm!cboPageSize = 20
    frm!cboSortKey = "studentNo": frm!cboSortDirection = "asc"
    frm!lblTitle.Caption = "学生検索 ／ " & CurrentRole() & " ／ " & CurrentUserId()
    frm!cmdNew.Visible = CurrentRole() <> "Reader"
    frm!cmdOpenSelected.Caption = IIf(CurrentRole() = "Reader", "選択行の参照", "選択行の編集／参照")
    frm!cmdFirst.Enabled = False: frm!cmdPrev.Enabled = False: frm!cmdNext.Enabled = False: frm!cmdLast.Enabled = False
    Dim emptyRows As New Collection
    stage = "AddRows": listRows.Add frm.Tag, emptyRows
    initializes = False: InitSearch = True
    Exit Function
Failed:
    Dim errorText As String
    errorText = FailureMessage(Err.Description, Err.Number, "InitSearch:" & stage)
    On Error Resume Next
    frm!lblMessage.Caption = MessageText(errorText)
    frm!cmdSearch.Enabled = False: frm!cmdNew.Enabled = False
    initializes = False
End Function
Private Function ReadCriteria(ByVal frm As Access.Form) As clsSearchCriteria
    Dim raw As Object
    Set raw = Map()
    raw.Add "studentNo", frm!txtStudentNo: raw.Add "name", frm!txtName
    raw.Add "class", SearchFilterValue(frm, "cboClass")
    raw.Add "status01", Nz(frm!chkEnrolled, False): raw.Add "status02", Nz(frm!chkLeave, False)
    raw.Add "status03", Nz(frm!chkGraduated, False): raw.Add "status04", Nz(frm!chkWithdrawn, False)
    Set ReadCriteria = NormalizeCriteria(raw, BusinessDay(UtcNow()))
End Function
Public Function SearchFilterValue(ByVal frm As Access.Form, ByVal controlName As String) As Variant
    SearchFilterValue = frm.Controls(controlName).Value
    If frm.Name = "frmStudentSearch" And controlName = "cboClass" Then
        If Nz(SearchFilterValue, "") = "0" Then SearchFilterValue = Null
    End If
End Function
Private Sub SetSearchAllSelections(ByVal frm As Access.Form)
    frm!cboClass = 0
End Sub
Public Function SearchClick(Optional ByVal operation As String = "SEARCH") As Boolean
    Dim frm As Access.Form, ctx As clsSearchContext, d As clsSearchCriteria, result As Object, rows As Collection
    Dim acquired As Boolean, requestError As String
    On Error GoTo Failed
    Set frm = Screen.ActiveForm: Set ctx = contexts(frm.Tag)
    If Nz(frm!IsBusy, False) Then Exit Function
    requestError = ctx.RequestError(frm.Tag, Nz(frm!txtContextId, ""), frm!txtContextRevision)
    If requestError <> "" Then
        If requestError = "W-SRC-002" Then ResetSearchForm frm, ctx
        frm!lblMessage.Caption = MessageText(requestError): Exit Function
    End If
    ctx.Acquire frm.Tag, Nz(frm!txtContextId, ""), frm!txtContextRevision: acquired = True: frm!IsBusy = True
    If operation = "SEARCH" Then
        Set d = ReadCriteria(frm): ctx.Page = 1
    Else
        If ctx.AppliedCriteria Is Nothing Then GoTo Done
        Set d = ctx.AppliedCriteria.Clone()
        Select Case operation
        Case "NEXT": ctx.Page = ctx.Page + 1
        Case "PREV": If ctx.Page > 1 Then ctx.Page = ctx.Page - 1
        Case "FIRST": ctx.Page = 1
        Case "LAST": ctx.Page = 500
        Case "SORT": ctx.Page = 1
        Case "REFRESH"
        Case Else: Err.Raise vbObjectError + 150, , "E-SRC-002"
        End Select
    End If
    ctx.PageSize = CLng(frm!cboPageSize): ctx.SortKey = frm!cboSortKey: ctx.Direction = frm!cboSortDirection
    Set result = SearchStudents(d, ctx.Page, ctx.PageSize, ctx.SortKey, ctx.Direction)
    frm!lblMessage.Caption = "": frm!txtSelectedDetails = Null
    If result("kind") = "Found" Or result("kind") = "LimitExceeded" Then
        Set ctx.AppliedCriteria = d.Clone()
        If result.Exists("page") Then ctx.Page = result("page")
        Set rows = result("rows"): Set listRows(frm.Tag) = rows
        If result("kind") = "LimitExceeded" Then
            frm!lblCount.Caption = "10,000件超過"
        ElseIf result("total") = 0 Then
            frm!lblCount.Caption = "検索結果 0件"
        Else
            frm!lblCount.Caption = CStr(result("total")) & "件／取得範囲 " & CStr((ctx.Page - 1) * ctx.PageSize + 1) & "－" & CStr((ctx.Page - 1) * ctx.PageSize + rows.Count)
        End If
        frm!lblSearchedAt.Caption = "検索日時：" & Format$(DateAdd("h", 9, result("at")), "yyyy/mm/dd hh:nn:ss")
    Else
        Set rows = New Collection: Set listRows(frm.Tag) = rows
        frm!lblCount.Caption = "検索失敗"
    End If
    If result("kind") = "Found" Or result("kind") = "LimitExceeded" Then ctx.Advance: frm!txtContextRevision = ctx.Revision: frm!txtContextId = ctx.ContextId
    frm!lstStudents.Requery
    frm!cmdFirst.Enabled = result("kind") = "Found" And ctx.Page > 1
    frm!cmdPrev.Enabled = frm!cmdFirst.Enabled
    frm!cmdNext.Enabled = result("kind") = "Found" And ctx.Page * ctx.PageSize < result("total")
    frm!cmdLast.Enabled = frm!cmdNext.Enabled
    If result("message") <> "" Then frm!lblMessage.Caption = MessageText(result("message"))
Done:
    ctx.ReleaseUpdate: frm!IsBusy = False: SearchClick = True
    Exit Function
Failed:
    Dim msg As String
    msg = Err.Description
    On Error Resume Next
    If acquired Then
        Set rows = New Collection: Set listRows(frm.Tag) = rows
        frm!lstStudents.Requery: frm!txtSelectedDetails = Null
        ctx.ReleaseUpdate
    End If
    frm!IsBusy = False: frm!lblMessage.Caption = MessageText(msg)
End Function
Public Function StudentListCallback(ctl As Control, id As Variant, row As Variant, col As Variant, code As Variant) As Variant
    Dim key As String, rows As Collection, item As Object
    On Error GoTo NotReady
    Select Case code
    Case acLBInitialize: StudentListCallback = True: Exit Function
    Case acLBOpen: StudentListCallback = CLng(Timer) + 1: Exit Function
    Case acLBGetColumnCount: StudentListCallback = 8: Exit Function
    Case acLBGetColumnWidth, acLBGetFormat: StudentListCallback = -1: Exit Function
    Case acLBEnd: Exit Function
    End Select
    EnsureMaps: key = ctl.Parent.Tag
    If code = acLBGetRowCount Then StudentListCallback = 0
    If Not listRows.Exists(key) Then Exit Function
    Set rows = listRows(key)
    Select Case code
    Case acLBInitialize: StudentListCallback = True
    Case acLBOpen: StudentListCallback = Timer + 1
    Case acLBGetRowCount: StudentListCallback = rows.Count
    Case acLBGetColumnCount: StudentListCallback = 8
    Case acLBGetColumnWidth: StudentListCallback = -1
    Case acLBGetFormat: StudentListCallback = -1
    Case acLBGetValue
        If row < 0 Or row >= rows.Count Then Exit Function
        Set item = rows(row + 1)
        Select Case col
        Case 0: StudentListCallback = item("student_id")
        Case 1: StudentListCallback = item("student_no")
        Case 2: StudentListCallback = item("student_name") & " ／ " & item("student_name_kana")
        Case 3: StudentListCallback = FormatBirthDate(item("birth_date"))
        Case 4: StudentListCallback = Nz(item("school_year"), "－") & "／" & item("grade_name")
        Case 5: StudentListCallback = item("class_display")
        Case 6: StudentListCallback = item("enrollment_name")
        Case 7: StudentListCallback = IIf(CurrentRole() = "Reader", "参照", "編集／参照")
        End Select
    End Select
    Exit Function
NotReady:
    If code = acLBGetRowCount Then StudentListCallback = 0
End Function
Public Function ClassChanged(Optional ByVal changed As String = "") As Boolean
    Dim frm As Access.Form, classroom As Object, original As Object, originalId As Variant, classCleared As Boolean
    If initializes Then Exit Function
    Set frm = Screen.ActiveForm
    If frm.Name = "frmStudentSearch" Then
        frm!lblMessage.Caption = "条件変更はまだ一覧に反映されていません。"
        Exit Function
    End If
    originalId = Null
    If frm.Name = "frmStudentEdit" Then
        Set original = edits(frm.Tag)("original")
        If Not original Is Nothing Then originalId = original("class_id")
        DirtyEdit
    End If
    If Not IsNull(SearchFilterValue(frm, "cboClass")) Then
        Set classroom = CandidateClass(SearchFilterValue(frm, "cboClass"))
        If Not classroom Is Nothing Then
            If changed = "CLASS" Then
                initializes = True
                frm!cboSchoolYear = classroom("school_year"): frm!cboGrade = classroom("grade_code")
                initializes = False
            ElseIf changed = "YEAR" Or changed = "GRADE" Then
                If (Nz(SearchFilterValue(frm, "cboSchoolYear"), "") <> "" And Nz(SearchFilterValue(frm, "cboSchoolYear"), "") <> CStr(classroom("school_year"))) Or (Nz(SearchFilterValue(frm, "cboGrade"), "") <> "" And Nz(SearchFilterValue(frm, "cboGrade"), "") <> classroom("grade_code")) Then
                    frm!cboClass = Null
                    frm!lblMessage.Caption = MessageText("W-STU-107")
                    classCleared = True
                End If
            End If
        End If
    End If
    RefreshClassChoices frm, originalId
    If frm.Name = "frmStudentEdit" Then RefreshCapacity frm
End Function
Public Function OpenStudent(ByVal fresh As Boolean) As Boolean
    Dim frm As Access.Form, id As Variant, expectedRevision As Long
    Set frm = Screen.ActiveForm: id = Null
    expectedRevision = CLng(frm!txtContextRevision)
    If fresh Then
        Authorize "Save"
    Else
        If IsNull(frm!lstStudents) Then Exit Function
        id = frm!lstStudents
    End If
    DoCmd.OpenForm "frmStudentEdit", , , , , acDialog, Nz(id, "") & "|" & frm.Tag
    If CLng(frm!txtContextRevision) <> expectedRevision Then Exit Function
    If contexts(frm.Tag).AppliedCriteria Is Nothing Then Exit Function
    SearchClick "REFRESH"
End Function
Public Function ClearSearch() As Boolean
    Dim frm As Access.Form, ctx As clsSearchContext, message As String
    Set frm = Screen.ActiveForm: Set ctx = contexts(frm.Tag)
    If Nz(frm!IsBusy, False) Then Exit Function
    message = ctx.RequestError(frm.Tag, Nz(frm!txtContextId, ""), frm!txtContextRevision)
    If message <> "" And message <> "W-SRC-002" Then frm!lblMessage.Caption = MessageText(message): Exit Function
    ResetSearchForm frm, ctx
    If message <> "" Then frm!lblMessage.Caption = MessageText(message)
    ClearSearch = True
End Function
Private Sub ResetSearchForm(ByVal frm As Access.Form, ByVal ctx As clsSearchContext)
    Dim emptyRows As New Collection
    initializes = True
    frm!txtStudentNo = Null: frm!txtName = Null: frm!txtSelectedDetails = Null
    SetSearchAllSelections frm
    frm!chkEnrolled = True: frm!chkLeave = True: frm!chkGraduated = False: frm!chkWithdrawn = False
    frm!cboPageSize = 20: frm!cboSortKey = "studentNo": frm!cboSortDirection = "asc"
    ctx.Reset frm.Tag: frm!txtContextRevision = ctx.Revision: frm!txtContextId = ctx.ContextId: Set listRows(frm.Tag) = emptyRows
    RefreshClassChoices frm, Null
    frm!cmdFirst.Enabled = False: frm!cmdPrev.Enabled = False: frm!cmdNext.Enabled = False: frm!cmdLast.Enabled = False
    frm!lstStudents.Requery: frm!lblCount.Caption = "未検索": frm!lblSearchedAt.Caption = "": frm!lblMessage.Caption = "": initializes = False
End Sub
Public Function SearchMenu() As Boolean
    If Nz(Screen.ActiveForm!IsBusy, False) Then Exit Function
    DoCmd.Close acForm, Screen.ActiveForm.Name
    SearchMenu = True
End Function

Public Function InitEdit(ByVal frm As Access.Form) As Boolean
    Dim state As Object, service As New clsStudentService, args As Variant, old As Object, conf As New clsConfirmation
    EnsureMaps: Authorize "Read"
    frm.Tag = GuidText(): Set state = Map(): args = Split(Nz(frm.OpenArgs, "|"), "|")
    state.Add "id", Null: state.Add "version", Null: state.Add "original", Nothing
    state.Add "confirmation", conf: state.Add "busy", False: state.Add "dirty", False
    edits.Add frm.Tag, state
    If args(0) <> "" Then
        Set old = service.LoadStudent(PositiveId(args(0)))
        state("id") = old("student_id"): state("version") = old("row_version")
        Set state("original") = old
        ShowDraft frm, old
    Else
        frm!cboGender = "0": frm!cboEnrollmentStatus = "01": frm!cboSchoolYear = CurrentSchoolYear()
    End If
    RefreshCodeChoices frm, old
    RefreshClassChoices frm, ValueOrClass(old)
    RefreshCapacity frm
    If IsNull(state("id")) Then
        Dim initialRepo As New clsStudentRepository, initialTx As New clsUnitOfWork
        initialTx.BeginWork: Set initialRepo.Database = initialTx.Database
        initialRepo.CheckCode "GENDER", "0", Null, BusinessDay(UtcNow())
        initialRepo.CheckCode "ENROLLMENT_STATUS", "01", Null, BusinessDay(UtcNow())
        initialTx.CloseWork
        If frm!cboClass.ListCount = 0 Then frm!lblMessage.Caption = MessageText("W-STU-108")
    End If
    frm!txtEnrollmentEndDate.Enabled = Nz(frm!cboEnrollmentStatus, "") = "03" Or Nz(frm!cboEnrollmentStatus, "") = "04"
    frm!txtStudentNo.Locked = Not IsNull(state("id"))
    frm!cmdDelete.Visible = CurrentRole() = "Admin" And Not IsNull(state("id"))
    If CurrentRole() = "Reader" Then
        Dim ctl As Access.Control
        For Each ctl In frm.Controls
            If ctl.ControlType = acTextBox Or ctl.ControlType = acComboBox Then ctl.Locked = True
        Next
        frm!cmdSave.Visible = False: frm!cmdReset.Visible = False
    End If
    frm!lblTitle.Caption = "学生登録・編集 ／ " & IIf(CurrentRole() = "Reader", "参照", IIf(IsNull(state("id")), "新規", "編集")) & " ／ " & CurrentUserId() & " ／ *必須・長文は Shift+F2"
    InitEdit = True
End Function
Public Function FieldControls() As Variant
    FieldControls = Split("txtStudentNo txtStudentName txtStudentNameKana BirthDateIso cboGender txtPostalCode cboPrefecture txtAddressLine1 txtAddressLine2 txtPhoneNumber txtEmailAddress txtAdmissionDate cboEnrollmentStatus txtEnrollmentEndDate cboClass txtEmergencyContactName cboRelationship txtEmergencyPhoneNumber txtRemarks", " ")
End Function
Private Sub ShowDraft(ByVal frm As Access.Form, ByVal d As Object)
    Dim fields As Variant, controls As Variant, i As Long, parts As Variant
    fields = SavedFields(): controls = FieldControls(): initializes = True
    For i = 0 To UBound(fields)
        If fields(i) <> "birth_date" Then frm.Controls(controls(i)).Value = d(fields(i))
    Next
    parts = BirthParts(d("birth_date"))
    frm!cboBirthEra = parts(0): frm!txtBirthYear = parts(1): frm!txtBirthMonth = parts(2): frm!txtBirthDay = parts(3)
    frm!txtStudentId = d("student_id")
    If Not IsNull(d("class_id")) Then
        Dim classroom As Object
        Set classroom = CandidateClass(d("class_id"))
        If Not classroom Is Nothing Then frm!cboSchoolYear = classroom("school_year"): frm!cboGrade = classroom("grade_code")
    Else
        frm!cboSchoolYear = Null: frm!cboGrade = Null
    End If
    frm!lblUpdated.Caption = Format$(DateAdd("h", 9, d("updated_at")), "yyyy/mm/dd hh:nn:ss") & " " & d("updated_by")
    initializes = False
End Sub
Private Function ReadDraft(ByVal frm As Access.Form) As Object
    Dim fields As Variant, controls As Variant, i As Long, d As Object
    Set d = Map(): fields = SavedFields(): controls = FieldControls()
    For i = 0 To UBound(fields)
        If fields(i) <> "birth_date" Then d.Add fields(i), frm.Controls(controls(i)).Value
    Next
    d.Add "birth_era", frm!cboBirthEra: d.Add "birth_year", frm!txtBirthYear
    d.Add "birth_month", frm!txtBirthMonth: d.Add "birth_day", frm!txtBirthDay
    d.Add "school_year", frm!cboSchoolYear: d.Add "grade_code", frm!cboGrade
    Set ReadDraft = d
End Function
Public Function DirtyEdit() As Boolean
    If initializes Then Exit Function
    edits(Screen.ActiveForm.Tag)("dirty") = True
End Function
Public Function StatusChanged() As Boolean
    Dim frm As Access.Form
    Set frm = Screen.ActiveForm
    If initializes Then Exit Function
    If Nz(frm!cboEnrollmentStatus, "") = "01" Or Nz(frm!cboEnrollmentStatus, "") = "02" Then
        frm!txtEnrollmentEndDate = Null: frm!txtEnrollmentEndDate.Enabled = False
    Else
        frm!txtEnrollmentEndDate.Enabled = True
    End If
    DirtyEdit
    ClassChanged
End Function
Private Function ValueOrClass(ByVal old As Object) As Variant
    ValueOrClass = Null
    If Not old Is Nothing Then ValueOrClass = old("class_id")
End Function
Public Function SaveEdit(Optional ByVal confirmed As Boolean = False) As Boolean
    Dim frm As Access.Form, state As Object, service As New clsStudentService, raw As Object, result As Object, candidates As Collection
    On Error GoTo Failed
    Set frm = Screen.ActiveForm: Set state = edits(frm.Tag)
    If state("busy") Then Exit Function
    state("busy") = True: Set raw = ReadDraft(frm)
    Set result = service.SaveStudent(raw, state("id"), state("version"), frm.Tag, state("confirmation"), confirmed, frm!txtOperationReason)
    state("busy") = False
    If result("kind") = "ConfirmationRequired" Then
        Set candidates = result("candidates")
        Set ConfirmationRows = candidates: ConfirmationMode = "DUPLICATE": ConfirmationReason = frm!txtOperationReason
        DoCmd.OpenForm "frmDuplicateConfirm", , , , , acDialog
        If ConfirmationAccepted Then frm!txtOperationReason = ConfirmationReason: SaveEdit True
        Set ConfirmationRows = Nothing
    ElseIf result("kind") = "Saved" Then
        state("dirty") = False
        Dim savedMessage As String
        savedMessage = MessageText(result("message"), "studentNo", result("student_no"))
        If result.Exists("warning") Then If result("warning") <> "" Then savedMessage = savedMessage & vbCrLf & MessageText(result("warning"))
        MsgBox savedMessage, vbInformation
        DoCmd.Close acForm, frm.Name
    Else
        DisplayInputError frm, result("message")
        If result("kind") = "Unknown" Then MsgBox "再保存前に検索で結果を確認してください。", vbExclamation
    End If
    Exit Function
Failed:
    Dim textError As String
    textError = Err.Description
    On Error Resume Next: state("busy") = False: frm!lblMessage.Caption = MessageText(textError)
End Function
Public Function DeleteEdit() As Boolean
    Dim frm As Access.Form, state As Object, service As New clsStudentService, result As Object, reason As String
    Set frm = Screen.ActiveForm: Set state = edits(frm.Tag)
    If state("busy") Then Exit Function
    ConfirmationMode = "DELETE": ConfirmationStudentNo = Nz(frm!txtStudentNo, ""): ConfirmationReason = Null
    DoCmd.OpenForm "frmDeleteConfirm", , , , , acDialog
    If Not ConfirmationAccepted Then Exit Function
    reason = ConfirmationReason
    Set result = service.DeleteStudent(state("id"), state("version"), reason, True)
    If result("kind") = "Saved" Then state("dirty") = False: DoCmd.Close acForm, frm.Name Else frm!lblMessage.Caption = MessageText(result("message"))
End Function
Public Function ResetEdit(Optional ByVal reload As Boolean = False) As Boolean
    Dim frm As Access.Form, state As Object, service As New clsStudentService, old As Object
    Set frm = Screen.ActiveForm: Set state = edits(frm.Tag)
    If state("busy") Then Exit Function
    If Not ConfirmDiscard() Then Exit Function
    If IsNull(state("id")) Then
        Dim ctl As Access.Control
        initializes = True
        For Each ctl In frm.Controls
            If ctl.ControlType = acTextBox Or ctl.ControlType = acComboBox Then ctl.Value = Null
        Next
        frm!cboGender = "0": frm!cboEnrollmentStatus = "01": frm!cboSchoolYear = CurrentSchoolYear(): initializes = False
    Else
        If reload Then
            Set old = service.LoadStudent(state("id"))
            state("version") = old("row_version"): Set state("original") = old
        Else
            Set old = state("original")
        End If
        ShowDraft frm, old
    End If
    RefreshCodeChoices frm, old: RefreshClassChoices frm, ValueOrClass(old): RefreshCapacity frm
    frm!txtEnrollmentEndDate.Enabled = Nz(frm!cboEnrollmentStatus, "") = "03" Or Nz(frm!cboEnrollmentStatus, "") = "04"
    state("confirmation").Consumed = True
    state("dirty") = False
End Function
Private Function CurrentSchoolYear() As Long
    Dim day As String
    day = BusinessDay(UtcNow()): CurrentSchoolYear = CLng(Left$(day, 4))
    If Mid$(day, 6, 2) < "04" Then CurrentSchoolYear = CurrentSchoolYear - 1
End Function
Public Sub RefreshCapacity(ByVal frm As Access.Form)
    Dim tx As New clsUnitOfWork, repo As New clsStudentRepository, c As Object
    On Error GoTo Failed
    frm!lblCapacity.Caption = "人数／定員：－"
    If IsNull(frm!cboClass) Then Exit Sub
    Authorize "Read": tx.BeginWork: Set repo.Database = tx.Database
    Set c = repo.ClassById(PositiveId(frm!cboClass))
    If c Is Nothing Then
        frm!lblCapacity.Caption = "人数／定員：[不整合]"
    Else
        frm!lblCapacity.Caption = "人数／定員：" & CStr(repo.Occupancy(c("class_id"), 0)) & "／" & Nz(c("capacity"), "－") & "（参考）"
    End If
    tx.CloseWork
    Exit Sub
Failed:
    On Error Resume Next: tx.CloseWork: frm!lblCapacity.Caption = "人数／定員：[取得失敗]"
End Sub
Private Sub DisplayInputError(ByVal frm As Access.Form, ByVal message As String)
    Dim pieces As Variant, p As Variant, i As Long, field As String, fields As Variant, controls As Variant
    frm!lblMessage.Caption = MessageText(message)
    pieces = Split(message, "|")
    For i = 1 To UBound(pieces)
        p = Split(pieces(i), "=", 2)
        If UBound(p) = 1 Then If p(0) = "fieldKey" Then field = p(1)
    Next
    fields = SavedFields(): controls = FieldControls()
    On Error Resume Next
    For i = 0 To UBound(fields)
        If fields(i) = field Then
            If field = "birth_date" Then frm!cboBirthEra.SetFocus Else frm.Controls(controls(i)).SetFocus
            Exit Sub
        End If
    Next
End Sub
Public Function BackEdit() As Boolean
    Dim state As Object
    Set state = edits(Screen.ActiveForm.Tag)
    If state("busy") Then Exit Function
    If state("dirty") Then
        If Not ConfirmDiscard() Then Exit Function
    End If
    state("dirty") = False: DoCmd.Close acForm, Screen.ActiveForm.Name
End Function
Public Function CanCloseEdit(ByVal frm As Access.Form) As Boolean
    Dim state As Object
    If edits Is Nothing Then CanCloseEdit = True: Exit Function
    If Not edits.Exists(frm.Tag) Then CanCloseEdit = True: Exit Function
    Set state = edits(frm.Tag)
    CanCloseEdit = Not state("dirty")
    If Not CanCloseEdit Then CanCloseEdit = ConfirmDiscard()
    If CanCloseEdit Then edits.Remove frm.Tag
End Function
Public Sub CloseSearch(ByVal frm As Access.Form)
    If Not contexts Is Nothing Then If contexts.Exists(frm.Tag) Then contexts.Remove frm.Tag
    If Not listRows Is Nothing Then If listRows.Exists(frm.Tag) Then listRows.Remove frm.Tag
End Sub
Public Function SelectedStudentDetails() As Boolean
    Dim frm As Access.Form, rows As Collection, item As Object, i As Long
    Set frm = Screen.ActiveForm: frm!txtSelectedDetails = Null
    If IsNull(frm!lstStudents) Then Exit Function
    Set rows = listRows(frm.Tag)
    For i = 1 To rows.Count
        Set item = rows(i)
        If item("student_id") = frm!lstStudents Then
            frm!txtSelectedDetails = item("student_no") & "　" & item("student_name") & " ／ " & item("student_name_kana") & "　" & FormatBirthDate(item("birth_date")) & vbCrLf & Nz(item("school_year"), "－") & "／" & item("grade_name") & "　" & item("class_display") & "　" & item("enrollment_name")
            Exit For
        End If
    Next
End Function
