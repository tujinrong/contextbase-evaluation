Attribute VB_Name = "modConfirmationForms"
Option Explicit
Option Compare Binary
Public ConfirmationRows As Collection
Public ConfirmationAccepted As Boolean
Public ConfirmationReason As Variant
Public ConfirmationMode As String
Public ConfirmationStudentNo As String

Public Function InitConfirmation(ByVal frm As Access.Form) As Boolean
    ConfirmationAccepted = False
    frm!txtReason = ConfirmationReason
    If ConfirmationMode = "DELETE" Then
        frm!lblPrompt.Caption = "学生 " & ConfirmationStudentNo & " を論理削除します。理由を入力し、確認してください。"
    Else
        If ConfirmationRows Is Nothing Then Set ConfirmationRows = New Collection
        frm!lblPrompt.Caption = CStr(ConfirmationRows.Count) & "件の同一人物候補があります。表示は最大20件です。氏名・生年月日・クラスを確認し、別人として続行する理由を入力してください。"
        frm!lstCandidates.Requery
    End If
    InitConfirmation = True
End Function
Public Function ConfirmationOk() As Boolean
    On Error GoTo Failed
    ConfirmationReason = TextValue(Screen.ActiveForm!txtReason, 60, 60, "memo")
    If IsNull(ConfirmationReason) Then Err.Raise vbObjectError + 143, , "E-STU-020"
    ConfirmationAccepted = True
    DoCmd.Close acForm, Screen.ActiveForm.Name
    Exit Function
Failed:
    Screen.ActiveForm!lblError.Caption = MessageText(Err.Description)
End Function
Public Function ConfirmationCancel() As Boolean
    ConfirmationAccepted = False
    DoCmd.Close acForm, Screen.ActiveForm.Name
End Function
Public Function CandidateListCallback(ctl As Control, id As Variant, row As Variant, col As Variant, code As Variant) As Variant
    Dim item As Object
    Select Case code
    Case acLBInitialize: CandidateListCallback = True
    Case acLBOpen: CandidateListCallback = Timer + 1
    Case acLBGetRowCount
        If ConfirmationRows Is Nothing Then CandidateListCallback = 0: Exit Function
        CandidateListCallback = ConfirmationRows.Count
        If ConfirmationRows.Count > 20 Then CandidateListCallback = 20
    Case acLBGetColumnCount: CandidateListCallback = 4
    Case acLBGetColumnWidth, acLBGetFormat: CandidateListCallback = -1
    Case acLBGetValue
        If ConfirmationRows Is Nothing Then Exit Function
        If row < 0 Or row >= ConfirmationRows.Count Or row >= 20 Then Exit Function
        Set item = ConfirmationRows(row + 1)
        Select Case col
        Case 0: CandidateListCallback = item("student_no")
        Case 1: CandidateListCallback = item("student_name")
        Case 2: CandidateListCallback = FormatBirthDate(item("birth_date"))
        Case 3: CandidateListCallback = item("class_display")
        End Select
    End Select
End Function
