Option Compare Binary
Option Explicit
Private target As Access.Form
Private states As Object
Private previousBusy As Boolean
Private priorFocus As String
Private priorRight As Long
Private priorDown As Long
Private physicalOverlay As Boolean
Private active As Boolean
Public Sub Acquire(ByVal f As Access.Form)
    Dim c As Object, kind As Long, locked As Variant, anchor As String
    On Error GoTo Failed
    Set target = f: Set states = CreateObject("Scripting.Dictionary")
    previousBusy = gBusy: gBusy = True: active = True: priorFocus = "": physicalOverlay = False
    ' Form.Load runs before the first normal paint. Moving to a footer here
    ' scrolls the new form before it is visible and leaves its Tab header above
    ' the viewport. Keep the logical guard; native controls need no overlay
    ' until the initial form setup has finished. Runtime overlays are unchanged.
    If UiIsInitialisingForm(f) Then Exit Sub
    priorFocus = FocusName(f)
    priorRight = -CLng(f.CurrentSectionLeft): priorDown = -CLng(f.CurrentSectionTop)
    If priorRight < 0 Then priorRight = 0
    If priorDown < 0 Then priorDown = 0
    physicalOverlay = True
    Select Case f.Name
    Case "frmLogin": anchor = "cmdExit"
    Case "frmMenu": anchor = "cmdLogout"
    Case "frmEmployeeEditor": anchor = "cmdCancel"
    Case Else: anchor = "cmdMenu"
    End Select
    For Each c In f.Controls
        kind = c.ControlType
        If kind = acTextBox Or kind = acComboBox Or kind = acCheckBox Or kind = acListBox Or kind = acTabCtl Or kind = acCommandButton Then
            locked = Null
            If kind = acTextBox Or kind = acComboBox Or kind = acCheckBox Or kind = acListBox Then locked = CBool(c.Locked)
            states.Add c.Name, Array(kind, CBool(c.Enabled), locked, CBool(c.TabStop))
        End If
    Next
    ' The anchor is outside all tabs. Its handler still refuses reentry with MSG-029.
    f.Controls(anchor).SetFocus
    For Each c In f.Controls
        If states.Exists(c.Name) Then
            kind = c.ControlType
            If kind = acTextBox Or kind = acComboBox Or kind = acCheckBox Or kind = acListBox Then c.Locked = True
            If c.Name <> anchor Then c.Enabled = False
            c.TabStop = False
        End If
    Next
    Exit Sub
Failed:
    Dim number As Long, description As String
    number = Err.Number: description = Err.Description
    Restore
    Err.Raise number, , description
End Sub
Private Function FocusName(ByVal f As Access.Form) As String
    On Error GoTo Missing
    FocusName = f.ActiveControl.Name
Missing:
End Function
Public Sub Restore()
    Dim key As Variant, state As Variant, c As Object, canFocus As Boolean
    If Not active Then Exit Sub
    active = False
    On Error GoTo Finished
    If Not CurrentProject.AllForms(target.Name).IsLoaded Then GoTo Finished
    ' Restore parent tabs first, then children. The caller applies its new model state afterwards.
    For Each key In states.Keys
        state = states(key)
        If CLng(state(0)) = acTabCtl Then target.Controls(CStr(key)).Enabled = CBool(state(1))
    Next
    For Each key In states.Keys
        state = states(key): Set c = target.Controls(CStr(key))
        c.Enabled = CBool(state(1)): c.TabStop = CBool(state(3))
        If Not IsNull(state(2)) Then c.Locked = CBool(state(2))
    Next
    ' SetFocus alone scrolls only enough to expose the old control, leaving Tab
    ' captions above the viewport. Restore the saved native page offsets first.
    If physicalOverlay Then target.GoToPage 1, priorRight, priorDown
    If priorFocus <> "" Then
        If target.Controls(priorFocus).Enabled And target.Controls(priorFocus).Visible Then target.Controls(priorFocus).SetFocus
    End If
Finished:
    gBusy = previousBusy: Set target = Nothing: Set states = Nothing
End Sub
Private Sub Class_Terminate()
    On Error Resume Next
    Restore
End Sub
