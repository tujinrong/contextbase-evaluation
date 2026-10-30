Option Compare Binary
Option Explicit
Public Raw As Object
Public AcceptedCodes As Object
Public Pending As Object
Public ExplicitComboChoice As Object
Public IsInitializing As Boolean
Public IsSwitchingPage As Boolean
Public IsRestoringSelection As Boolean
Public IsResizing As Boolean
Public Activated As Boolean
Public DraftReflected As Boolean
Public AcceptedPage As Integer
Public AcceptedCategory As String
Public AcceptedListKey As Variant
Public LastEditFocus As String
Public RestorePendingControl As String
Public OriginalTimerInterval As Long
Public IsUnloading As Boolean
Public LayoutFailure As String
Private Sub Class_Initialize()
    Set Raw = CreateObject("Scripting.Dictionary")
    Set AcceptedCodes = CreateObject("Scripting.Dictionary")
    Set Pending = CreateObject("Scripting.Dictionary")
    Set ExplicitComboChoice = CreateObject("Scripting.Dictionary")
    AcceptedListKey = Null
End Sub
