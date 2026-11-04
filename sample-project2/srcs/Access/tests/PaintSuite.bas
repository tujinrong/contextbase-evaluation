Option Compare Binary
Option Explicit
Private report As String
Private Sub Need(ByVal id As String, ByVal okay As Boolean)
    report = report & id & "|" & IIf(okay, "PASS", "FAIL") & vbLf
    If Not okay Then Err.Raise vbObjectError + 981, "PaintSuite", id
End Sub
Private Function NavigationFailureRestored(ByVal f As Access.Form) As Boolean
    Dim outer As Long, expected As Long, priorAllow As Boolean
    priorAllow = gAllowClose: outer = UiBeginPaint()
    On Error GoTo ExpectedFailure
    Navigate f, "__SP2_missing_form__"
    GoTo Finished
ExpectedFailure:
    expected = Err.Number
    NavigationFailureRestored = (expected <> 0 And UiPaintDepth() = 1 And UiPaintOwnsEcho() And gAllowClose = priorAllow)
Finished:
    UiEndPaint outer
    NavigationFailureRestored = NavigationFailureRestored And UiPaintDepth() = 0 And Not UiPaintOwnsEcho()
End Function
Public Function PaintResizeStable(ByVal formName As String) As Boolean
    Dim f As Access.Form, before As Long
    Set f = Forms(formName): UiResize f: before = UiLayoutWriteCount(): UiResize f
    PaintResizeStable = (UiLayoutWriteCount() = before And UiPaintDepth() = 0 And Not UiPaintOwnsEcho() And UiState(f).LayoutFailure = "")
End Function
Public Function RunPaintSuite() As String
    Dim outer As Long, inner As Long, stray As Long, f As Access.Form, before As Long
    On Error GoTo Failed
    report = ""
    Need "initial-no-owned-freeze", UiPaintDepth() = 0 And Not UiPaintOwnsEcho()
    outer = UiBeginPaint(): inner = UiBeginPaint()
    Need "nested-owned-freeze", UiPaintDepth() = 2 And UiPaintOwnsEcho()
    UiEndPaint outer
    Need "out-of-order-release-keeps-inner", UiPaintDepth() = 1 And UiPaintOwnsEcho()
    UiEndPaint outer: stray = 2147483647: UiEndPaint stray
    Need "duplicate-and-foreign-release-no-effect", UiPaintDepth() = 1 And UiPaintOwnsEcho()
    UiEndPaint inner
    Need "final-release-restores", UiPaintDepth() = 0 And Not UiPaintOwnsEcho()
    UiOpenForm "frmLogin": Set f = Forms("frmLogin")
    Need "real-navigate-failure-unwinds-nested-scope", NavigationFailureRestored(f)
    Need "source-form-survives-navigation-error", CurrentProject.AllForms("frmLogin").IsLoaded
    UiResize f: before = UiLayoutWriteCount(): UiResize f
    Need "repeat-resize-no-native-writes", UiLayoutWriteCount() = before
    Need "resize-restores-owned-freeze", UiPaintDepth() = 0 And Not UiPaintOwnsEcho()
    RunPaintSuite = report: Exit Function
Failed:
    report = report & "error|" & CStr(Err.Number) & "|" & Err.Description & vbLf
    On Error Resume Next
    UiEndPaint inner: UiEndPaint outer
    RunPaintSuite = report
End Function
