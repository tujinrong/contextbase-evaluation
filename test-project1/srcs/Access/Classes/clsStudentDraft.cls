VERSION 1.0 CLASS
BEGIN
  MultiUse = -1
END
Attribute VB_Name = "clsStudentDraft"
Option Explicit
Option Compare Binary
Public Values As Object
Private Sub Class_Initialize()
    Set Values = Map()
End Sub
Public Function Clone() As clsStudentDraft
    Dim d As New clsStudentDraft
    Set d.Values = CopyMap(Values)
    Set Clone = d
End Function
