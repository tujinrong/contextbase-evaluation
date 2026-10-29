Option Compare Binary
Option Explicit
Public Function UiVerificationFlags() As String
    UiVerificationFlags = CStr(gDirty) & "|" & CStr(gDraftDirty) & "|" & CStr(gBusy) & "|" & CStr(gUiLoading)
End Function
Public Function PrepareUi(ByVal screen As String, Optional ByVal password As String = "") As Boolean
    Dim result As clsResult, f As Access.Form
    EnsureSession
    If screen = "login" Then LogoutNow: PrepareUi = True: Exit Function
    If password <> "" Then
        Set result = Authenticate("admin", password)
        If result.Kind <> "OK" Then Exit Function
    End If
    gAllowClose = True: gDirty = False: gDraftDirty = False: gBusy = False
    Dim names As Variant, n As Variant
    names = Array("frmEmployeeEditor", "frmCodeMaster", "frmEmployeeSearch", "frmMenu")
    For Each n In names
        If CurrentProject.AllForms(CStr(n)).IsLoaded Then DoCmd.Close acForm, CStr(n), acSaveNo
    Next
    If CurrentProject.AllForms("frmLogin").IsLoaded Then DoCmd.Close acForm, "frmLogin", acSaveNo
    gAllowClose = False: DoCmd.OpenForm "frmMenu"
    If screen = "menu" Then PrepareUi = True: Exit Function
    If screen = "code" Then UiAction Forms("frmMenu"), "cmdCodeMaster": PrepareUi = True: Exit Function
    UiAction Forms("frmMenu"), "cmdEmployeeSearch"
    Set f = Forms("frmEmployeeSearch"): UiAction f, "cmdSearch"
    If screen = "search" Then PrepareUi = True: Exit Function
    If screen = "editor-new" Then UiAction f, "cmdNew": PrepareUi = True: Exit Function
    f!lstEmployees = CLng(f!lstEmployees.Column(0, 0)): UiSelected f, "lstEmployees"
    UiAction f, "cmdEdit"
    If screen = "careers" Then Forms("frmEmployeeEditor")!tabEmployee = 1
    PrepareUi = True
End Function
