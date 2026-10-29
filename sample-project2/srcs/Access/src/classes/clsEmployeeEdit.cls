Option Compare Binary
Option Explicit
Public EmployeeId As Variant
Public ExpectedRevision As Variant
Public EmployeeNo As String
Public Name As String
Public Kana As String
Public Department As String
Public Status As String
Public JoinDate As Date
Public Summary As Variant
Public Skills As Variant
Public Qualifications As Variant
Public SelfPr As Variant
Public Careers As Collection
Public LoadedCareerIds As Collection
Public RemovedCareerIds As Collection
Public ActiveDraft As clsCareerDraft
Public Outcome As String
Private Sub Class_Initialize()
    EmployeeId = Null: ExpectedRevision = Null
    Summary = Null: Skills = Null: Qualifications = Null: SelfPr = Null
    Set Careers = New Collection: Set LoadedCareerIds = New Collection: Set RemovedCareerIds = New Collection
End Sub
