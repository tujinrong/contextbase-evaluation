Option Compare Binary
Option Explicit
Public RawEmployeeNo As String
Public RawName As String
Public RawDepartment As String
Public RawStatus As String
Public AcceptedDepartmentCode As Variant
Public AcceptedStatusCode As Variant
Public PendingComboRaw As Object
Public SearchState As String
Public HasAppliedCriteria As Boolean
Public AppliedValid As Boolean
Public AppliedCriteria As clsSearchCriteria
Public ResultState As String
Public ResultRows As Collection
Public DepartmentRows As Collection
Public StatusRows As Collection
Public SelectedEmployeeId As Variant
Public TopVisibleEmployeeId As Variant
Public ViewportPositionStatus As String
Public FocusControl As String
Private Sub Class_Initialize()
    Set PendingComboRaw = CreateObject("Scripting.Dictionary")
    Set ResultRows = New Collection
    Set DepartmentRows = New Collection: Set StatusRows = New Collection
    AcceptedDepartmentCode = Null: AcceptedStatusCode = Null
    SelectedEmployeeId = Null: TopVisibleEmployeeId = Null
    ' The viewport is captured independently from the selected employee ID.
    ViewportPositionStatus = "NOT_CAPTURED"
    SearchState = "Unsearched": ResultState = "NoResult"
End Sub
