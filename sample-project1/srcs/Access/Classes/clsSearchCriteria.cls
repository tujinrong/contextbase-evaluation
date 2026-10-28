VERSION 1.0 CLASS
BEGIN
  MultiUse = -1
END
Attribute VB_Name = "clsSearchCriteria"
Option Explicit
Option Compare Binary
Public StudentNoPrefix As String
Public NameKey As String
Public ClassId As Variant
Private statuses(1 To 4) As Boolean
Public Property Get StatusSelected(ByVal index As Long) As Boolean
    StatusSelected = statuses(index)
End Property
Public Property Let StatusSelected(ByVal index As Long, ByVal value As Boolean)
    statuses(index) = value
End Property
Private Sub Class_Initialize()
    ClassId = Null
End Sub
Public Function Clone() As clsSearchCriteria
    Dim result As New clsSearchCriteria, i As Long
    result.StudentNoPrefix = StudentNoPrefix: result.NameKey = NameKey: result.ClassId = ClassId
    For i = 1 To 4: result.StatusSelected(i) = StatusSelected(i): Next
    Set Clone = result
End Function
