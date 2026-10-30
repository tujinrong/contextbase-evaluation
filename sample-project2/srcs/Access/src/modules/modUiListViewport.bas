Option Compare Binary
Option Explicit
' The measured Access OGrid is NOT a Win32 LISTBOX. No LB_* messages are used.
' Windows API contract: GetScrollInfo / WM_VSCROLL (SB_THUMBPOSITION).
Private Declare PtrSafe Function EnumChildWindows Lib "user32" (ByVal parent As LongPtr, ByVal callback As LongPtr, ByVal data As LongPtr) As Long
Private Declare PtrSafe Function IsWindowVisible Lib "user32" (ByVal hwnd As LongPtr) As Long
Private Declare PtrSafe Function IsChild Lib "user32" (ByVal parent As LongPtr, ByVal child As LongPtr) As Long
Private Declare PtrSafe Function GetClassNameW Lib "user32" (ByVal hwnd As LongPtr, ByVal name As LongPtr, ByVal count As Long) As Long
Private Declare PtrSafe Function GetWindowRect Lib "user32" (ByVal hwnd As LongPtr, ByRef rect As VIEW_RECT) As Long
Private Declare PtrSafe Function GetWindowThreadProcessId Lib "user32" (ByVal hwnd As LongPtr, ByRef pid As Long) As Long
Private Declare PtrSafe Function GetCurrentProcessId Lib "kernel32" () As Long
Private Declare PtrSafe Function GetDpiForWindow Lib "user32" (ByVal hwnd As LongPtr) As Long
Private Declare PtrSafe Function GetScrollInfo Lib "user32" (ByVal hwnd As LongPtr, ByVal bar As Long, ByRef info As VIEW_SCROLLINFO) As Long
Private Declare PtrSafe Function SendMessageW Lib "user32" (ByVal hwnd As LongPtr, ByVal message As Long, ByVal wParam As LongPtr, ByVal lParam As LongPtr) As LongPtr
Private Type VIEW_RECT
    Left As Long
    Top As Long
    Right As Long
    Bottom As Long
End Type
Private Type VIEW_SCROLLINFO
    cbSize As Long
    mask As Long
    minimum As Long
    maximum As Long
    page As Long
    position As Long
    track As Long
End Type
Private findParent As LongPtr, findPid As Long, foundGrid As LongPtr
Private gridCount As Long, matchingCount As Long
Private expectedWidth As Double, expectedHeight As Double, tolerance As Double
Public Function UiViewportEnum(ByVal hwnd As LongPtr, ByVal ignored As LongPtr) As Long
    Dim name As String, count As Long, pid As Long, rect As VIEW_RECT
    UiViewportEnum = 1
    If IsWindowVisible(hwnd) = 0 Or IsChild(findParent, hwnd) = 0 Then Exit Function
    GetWindowThreadProcessId hwnd, pid
    If pid <> findPid Then Exit Function
    name = String$(64, vbNullChar): count = GetClassNameW(hwnd, StrPtr(name), Len(name))
    If Left$(name, count) <> "OGrid" Then Exit Function
    gridCount = gridCount + 1
    If GetWindowRect(hwnd, rect) = 0 Then Exit Function
    If Abs((rect.Right - rect.Left) - expectedWidth) > tolerance Or Abs((rect.Bottom - rect.Top) - expectedHeight) > tolerance Then Exit Function
    matchingCount = matchingCount + 1: foundGrid = hwnd
End Function
Private Function EmployeeGrid(ByVal f As Access.Form, ByRef reason As String) As LongPtr
    Dim ctl As Control, lists As Long, dpi As Long
    reason = "TARGET_UNAVAILABLE"
    If f.Name <> "frmEmployeeSearch" Then Exit Function
    For Each ctl In f.Controls: If ctl.ControlType = acListBox Then lists = lists + 1
    Next
    If lists <> 1 Or f!lstEmployees.ControlType <> acListBox Or Not f!lstEmployees.Visible Then Exit Function
    findParent = f.hwnd: findPid = 0
    GetWindowThreadProcessId findParent, findPid
    If findPid <> GetCurrentProcessId() Then reason = "OWNER_MISMATCH": Exit Function
    dpi = GetDpiForWindow(findParent)
    If dpi < 48 Or dpi > 768 Then reason = "DPI_UNAVAILABLE": Exit Function
    expectedWidth = f!lstEmployees.Width * CDbl(dpi) / 1440#
    expectedHeight = f!lstEmployees.Height * CDbl(dpi) / 1440#
    tolerance = 4# * CDbl(dpi) / 96# + 2#
    gridCount = 0: matchingCount = 0: foundGrid = 0
    EnumChildWindows findParent, AddressOf UiViewportEnum, 0
    If gridCount = 0 Then reason = "GRID_NOT_READY": Exit Function
    If gridCount <> 1 Then reason = "GRID_AMBIGUOUS": Exit Function
    If matchingCount <> 1 Then reason = "GRID_GEOMETRY_MISMATCH": Exit Function
    EmployeeGrid = foundGrid: reason = ""
End Function
Private Function ReadPosition(ByVal hwnd As LongPtr, ByVal count As Long, ByRef index As Long) As Boolean
    Dim info As VIEW_SCROLLINFO
    info.cbSize = LenB(info): info.mask = &H17
    If GetScrollInfo(hwnd, 1, info) = 0 Then Exit Function
    If info.minimum <> 0 Or info.maximum < 0 Or info.position < 0 Or info.position >= count Or info.position > info.maximum Then Exit Function
    If info.page < 0 Or info.page > info.maximum + 1 Then Exit Function
    index = info.position: ReadPosition = True
End Function
Public Sub UiCaptureEmployeeViewport(ByVal f As Access.Form, ByVal state As clsSearchReturnState)
    Dim hwnd As LongPtr, index As Long, reason As String, row As Variant
    On Error GoTo Failed
    state.TopVisibleEmployeeId = Null: state.ViewportPositionStatus = "CAPTURE_UNAVAILABLE"
    If state.ResultRows.Count = 0 Then state.ViewportPositionStatus = "NO_ROWS": Exit Sub
    If f!lstEmployees.ListCount <> state.ResultRows.Count Then state.ViewportPositionStatus = "CAPTURE_ROW_COUNT_MISMATCH": Exit Sub
    hwnd = EmployeeGrid(f, reason)
    If hwnd = 0 Then state.ViewportPositionStatus = "CAPTURE_" & reason: Exit Sub
    If Not ReadPosition(hwnd, state.ResultRows.Count, index) Then state.ViewportPositionStatus = "CAPTURE_POSITION_UNAVAILABLE": Exit Sub
    row = state.ResultRows(index + 1)
    If Not Same(f!lstEmployees.Column(0, index), row(0)) Then state.ViewportPositionStatus = "CAPTURE_ID_MISMATCH": Exit Sub
    state.TopVisibleEmployeeId = CLng(row(0))
    state.ViewportPositionStatus = "CAPTURED": Exit Sub
Failed:
    state.ViewportPositionStatus = "CAPTURE_ERROR_" & CStr(Err.Number)
End Sub
Public Function UiRestoreEmployeeViewport(ByVal f As Access.Form, ByVal state As clsSearchReturnState, Optional ByVal deferNotReady As Boolean = False) As Boolean
    Dim hwnd As LongPtr, index As Long, readBack As Long, found As Boolean, row As Variant, selected As Variant, reason As String, priorRestoring As Boolean, priorCaption As String, selectedCaptured As Boolean
    On Error GoTo Failed
    UiRestoreEmployeeViewport = True
    If state Is Nothing Then Exit Function
    priorRestoring = UiState(f).IsRestoringSelection: priorCaption = f!lblSelection.Caption
    If state.ViewportPositionStatus = "NO_ROWS" Then Exit Function
    If IsNull(state.TopVisibleEmployeeId) Then reason = state.ViewportPositionStatus: GoTo Unavailable
    For Each row In CachedRows(f!lstEmployees)
        If CLng(row(0)) = CLng(state.TopVisibleEmployeeId) Then found = True: Exit For
        index = index + 1
    Next
    If Not found Or index < 0 Or index >= 200 Then reason = "TOP_ID_NOT_IN_RESULT": GoTo Unavailable
    hwnd = EmployeeGrid(f, reason)
    If hwnd = 0 Then
        If reason = "GRID_NOT_READY" And deferNotReady Then
            state.ViewportPositionStatus = "RESTORE_PENDING_GRID_NOT_READY"
            UiRestoreEmployeeViewport = False: Exit Function
        End If
        GoTo Unavailable
    End If
    selected = f!lstEmployees.Value: selectedCaptured = True
    UiState(f).IsRestoringSelection = True
    ' Our business limit is 200, so the documented 16-bit thumb field suffices.
    SendMessageW hwnd, &H115, CLng(index * 65536 + 4), 0
    SendMessageW hwnd, &H115, 8, 0
    UiState(f).IsRestoringSelection = priorRestoring
    If Not ReadPosition(hwnd, f!lstEmployees.ListCount, readBack) Then reason = "RESTORE_READBACK_UNAVAILABLE": GoTo Unavailable
    If readBack <> index Then reason = "RESTORE_POSITION_MISMATCH": GoTo Unavailable
    If Not Same(selected, f!lstEmployees.Value) Or Not Same(selected, gSelectedEmployee) Then
        UiState(f).IsRestoringSelection = True
        f!lstEmployees.Value = selected: gSelectedEmployee = selected
        f!cmdEdit.Enabled = Not IsNull(selected): f!cmdExport.Enabled = Not IsNull(selected)
        UiSelectedEmployeeDetails f
        UiState(f).IsRestoringSelection = priorRestoring
        reason = "RESTORE_SELECTION_CHANGED": GoTo Unavailable
    End If
    state.ViewportPositionStatus = "RESTORED": Exit Function
Failed:
    reason = "RESTORE_ERROR_" & CStr(Err.Number)
Unavailable:
    On Error GoTo SelectionFailure
    If selectedCaptured Then
        UiState(f).IsRestoringSelection = True
        If Not Same(selected, f!lstEmployees.Value) Or Not Same(selected, gSelectedEmployee) Then
            f!lstEmployees.Value = selected: gSelectedEmployee = selected
            f!cmdEdit.Enabled = Not IsNull(selected): f!cmdExport.Enabled = Not IsNull(selected)
            UiSelectedEmployeeDetails f
        End If
        If Not Same(selected, f!lstEmployees.Value) Or Not Same(selected, gSelectedEmployee) Then GoTo SelectionFailure
    End If
    UiState(f).IsRestoringSelection = priorRestoring
    state.ViewportPositionStatus = "RESTORE_UNAVAILABLE:" & reason
    f!lblSelection.Caption = priorCaption & " ／ 一覧位置は未復帰です。選択・検索条件は保持しています。"
    Exit Function
SelectionFailure:
    UiState(f).IsRestoringSelection = priorRestoring
    state.ViewportPositionStatus = "RESTORE_SELECTION_UNCONFIRMED:" & reason
    gSelectedEmployee = selected
    f!cmdMenu.SetFocus: f!cmdEdit.Enabled = False: f!cmdExport.Enabled = False
    f!lblSelection.Caption = priorCaption & " ／ 一覧位置と選択の復元を確認できませんでした。社員を再選択してください。検索条件は保持しています。"
End Function
