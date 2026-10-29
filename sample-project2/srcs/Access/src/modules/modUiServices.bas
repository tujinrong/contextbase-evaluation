Option Compare Binary
Option Explicit
' Busy overlays wrap only blocking service calls. They end BEFORE UI state transitions,
' so new-career enabled fields and saved-code immutable keys are never overwritten.
Public Function UiAuthorize(ByVal f As Access.Form, ByVal role As String) As clsResult
    Dim overlay As New clsUiBusyState
    overlay.Acquire f: Set UiAuthorize = Authorize(role): overlay.Restore
End Function
Public Function UiAuthenticate(ByVal f As Access.Form, ByVal login As String, ByVal password As String) As clsResult
    Dim overlay As New clsUiBusyState
    overlay.Acquire f: Set UiAuthenticate = Authenticate(login, password): password = "": overlay.Restore
End Function
Public Function UiSearch(ByVal f As Access.Form, ByVal criteria As clsSearchCriteria) As clsResult
    Dim overlay As New clsUiBusyState
    overlay.Acquire f: Set UiSearch = SearchEmployees(criteria, gSession): overlay.Restore
End Function
Public Function UiReadEmployee(ByVal f As Access.Form, ByVal id As Long) As clsResult
    Dim overlay As New clsUiBusyState
    overlay.Acquire f: Set UiReadEmployee = ReadEmployee(id, gSession): overlay.Restore
End Function
Public Function UiSaveEmployee(ByVal f As Access.Form, ByVal e As clsEmployeeEdit) As clsResult
    Dim overlay As New clsUiBusyState
    overlay.Acquire f: Set UiSaveEmployee = SaveEmployee(e, gSession): overlay.Restore
End Function
Public Function UiReadCodes(ByVal f As Access.Form, ByVal category As String) As clsResult
    Dim overlay As New clsUiBusyState
    overlay.Acquire f: Set UiReadCodes = ReadCodes(category, gSession): overlay.Restore
End Function
Public Function UiSaveCode(ByVal f As Access.Form, ByVal e As clsCodeEdit) As clsResult
    Dim overlay As New clsUiBusyState
    overlay.Acquire f: Set UiSaveCode = SaveCode(e, gSession): overlay.Restore
End Function
Public Function UiExport(ByVal f As Access.Form, ByVal id As Long) As clsResult
    Dim overlay As New clsUiBusyState
    overlay.Acquire f: Set UiExport = ExportCareer(id, gSession): overlay.Restore
End Function
Public Function OwnerForm(ByVal control As Object) As Access.Form
    Dim parent As Object, depth As Long
    Set parent = control
    For depth = 1 To 8
        If TypeOf parent Is Access.Form Then Set OwnerForm = parent: Exit Function
        Set parent = parent.Parent
    Next
    Reject "MSG-020"
End Function
