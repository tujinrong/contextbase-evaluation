Option Compare Binary
Option Explicit
Public CategoryId As String
Public Code As String
Public Name As String
Public SortOrder As Integer
Public IsEnabled As Boolean
Public ExpectedRevision As Variant
Public IsNew As Boolean
Private Sub Class_Initialize()
    ExpectedRevision = Null: IsNew = True: SortOrder = 1: IsEnabled = True
End Sub
