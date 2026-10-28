Attribute VB_Name = "modAccessRibbon"
Option Explicit
Option Compare Binary

Private ribbonLoaded As Boolean
Private studentRibbonName As String
Private postalMenuName As String

' Preserve the standard Access ribbon. Only its built-in Paste command is
' repurposed, and only while the postal text box owns the form's input focus.
Public Function InstallStudentRibbon(ByVal frm As Access.Form) As Boolean
    Dim xml As String
    On Error GoTo Failed
    If Not ribbonLoaded Then
        ' LoadCustomUI names live for the Access process, beyond CloseCurrentDatabase.
        ' A new VBA project instance must not collide with a previously loaded name.
        studentRibbonName = "StudentNativeInput_" & Replace(Replace(Replace(GuidText(), "-", ""), "{", ""), "}", "")
        xml = "<customUI xmlns=""http://schemas.microsoft.com/office/2009/07/customui""><commands>" & _
              "<command idMso=""Paste"" onAction=""StudentPasteCommand""/>" & _
              "</commands></customUI>"
        Application.LoadCustomUI studentRibbonName, xml
        ribbonLoaded = True
    End If
    frm.RibbonName = studentRibbonName
    InstallPostalShortcutMenu frm
    InstallStudentRibbon = True
    Exit Function
Failed:
    On Error Resume Next
    frm!txtPostalCode.Locked = True
    frm!cmdSave.Enabled = False
    frm!lblMessage.Caption = MessageText("E-COM-004")
End Function

Private Sub InstallPostalShortcutMenu(ByVal frm As Access.Form)
    Dim popup As Office.CommandBar, button As Office.CommandBarControl
    If postalMenuName = "" Then
        postalMenuName = "StudentPostal_" & Replace(Replace(Replace(GuidText(), "-", ""), "{", ""), "}", "")
        Set popup = Application.CommandBars.Add(postalMenuName, msoBarPopup, False, True)
        ' Native Access edit commands keep their normal enabled state and behavior.
        popup.Controls.Add Type:=msoControlButton, Id:=128, Temporary:=True
        Set button = popup.Controls.Add(Type:=msoControlButton, Id:=21, Temporary:=True)
        button.BeginGroup = True
        popup.Controls.Add Type:=msoControlButton, Id:=19, Temporary:=True
        Set button = popup.Controls.Add(Type:=msoControlButton, Id:=22, Temporary:=True)
        button.OnAction = "=PostalPaste()"
        button.Tag = "StudentPostalValidatedPaste"
    End If
    frm.ShortcutMenu = True
    frm!txtPostalCode.ShortcutMenuBar = postalMenuName
End Sub

Public Function PostalInputActive() As Boolean
    On Error GoTo NotPostal
    If Screen.ActiveForm.Name <> "frmStudentEdit" Then Exit Function
    If Screen.ActiveControl.Name <> "txtPostalCode" Then Exit Function
    PostalInputActive = True
NotPostal:
End Function

Public Sub StudentPasteCommand(ByVal control As Office.IRibbonControl, ByRef cancelDefault)
    On Error GoTo Failed
    cancelDefault = False
    If Not PostalInputActive() Then Exit Sub
    cancelDefault = True
    PostalPaste
    Exit Sub
Failed:
    ' Do not fall back to truncating native paste after a postal paste failure.
    If PostalInputActive() Then cancelDefault = True
End Sub
