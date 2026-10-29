Option Compare Binary
Option Explicit
Public PersistentId As Variant
Public TemporaryId As String
Public StartMonth As Date
Public EndMonth As Variant
Public Company As String
Public Project As String
Public Description As String
Public Duties As String
Public Achievements As Variant
Public Technologies As Variant
Public Phases As Variant
Public RoleCode As String
Public TeamSize As Integer
Private Sub Class_Initialize()
    PersistentId = Null: EndMonth = Null: Achievements = Null: Technologies = Null: Phases = Null
    TemporaryId = NewRequestId()
End Sub
