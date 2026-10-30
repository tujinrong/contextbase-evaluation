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
Public RestorePendingPhase As Integer
Public RestorePendingAttempts As Integer
Public OriginalTimerInterval As Long
Public DeferredTimerOwned As Boolean
Public DeferredWorkRunning As Boolean
Public ViewportRestoreState As clsSearchReturnState
Public ViewportRestoreAttempts As Integer
Public IsUnloading As Boolean
Public LayoutFailure As String
Public PendingTabStops As Object
Public PickerOwner As String
Public PickerCommitKey As Boolean
Public PickerPointerInside As Boolean
Public PickerTyping As Boolean
Public BusyOverlayDepth As Long
Private Sub Class_Initialize()
    Set Raw = CreateObject("Scripting.Dictionary")
    Set AcceptedCodes = CreateObject("Scripting.Dictionary")
    Set Pending = CreateObject("Scripting.Dictionary")
    Set ExplicitComboChoice = CreateObject("Scripting.Dictionary")
    Set PendingTabStops = CreateObject("Scripting.Dictionary")
    AcceptedListKey = Null
End Sub
