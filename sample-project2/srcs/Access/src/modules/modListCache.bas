Option Compare Binary
Option Explicit
Private caches As Object
Private handles As Object
Private nextHandle As Long
Private Sub EnsureCaches()
    If caches Is Nothing Then Set caches = CreateObject("Scripting.Dictionary")
    If handles Is Nothing Then Set handles = CreateObject("Scripting.Dictionary")
End Sub
Private Function CacheKey(ByVal ctl As Access.Control) As String
    CacheKey = ctl.Parent.Name & "." & ctl.Name
End Function
Public Sub SetRows(ByVal ctl As Access.Control, ByVal rows As Collection)
    EnsureCaches
    If caches.Exists(CacheKey(ctl)) Then caches.Remove CacheKey(ctl)
    caches.Add CacheKey(ctl), rows
    ctl.RowSource = ""
    Select Case ctl.Name
    Case "lstEmployees": ctl.RowSourceType = "UiEmployeesRows"
    Case "lstCareers": ctl.RowSourceType = "UiCareersRows"
    Case "lstCodes": ctl.RowSourceType = "UiCodesRows"
    Case Else: ctl.RowSourceType = "ListRows"
    End Select
    ctl.Requery
End Sub
Public Function CachedRows(ByVal ctl As Access.Control) As Collection
    EnsureCaches
    If Not caches.Exists(CacheKey(ctl)) Then caches.Add CacheKey(ctl), New Collection
    Set CachedRows = caches(CacheKey(ctl))
End Function
Public Sub DetachRows(ByVal formName As String)
    Dim key As Variant
    EnsureCaches
    For Each key In caches.Keys
        If Left$(CStr(key), Len(formName) + 1) = formName & "." Then caches.Remove key
    Next
End Sub
Public Function ListRows(ByVal ctl As Control, ByVal id As Variant, ByVal row As Variant, ByVal col As Variant, ByVal code As Variant) As Variant
    Dim rows As Collection, values As Variant, key As String
    EnsureCaches
    Select Case code
    Case acLBInitialize
        ListRows = True
    Case acLBOpen
        If nextHandle = 2147483647 Then Reject "MSG-020"
        nextHandle = nextHandle + 1
        handles.Add CStr(nextHandle), CacheKey(ctl): ListRows = nextHandle
    Case acLBGetRowCount
        Set rows = CachedRows(ctl): ListRows = rows.Count
    Case acLBGetColumnCount
        ListRows = ctl.ColumnCount
    Case acLBGetColumnWidth
        ListRows = -1
    Case acLBGetValue
        If Not handles.Exists(CStr(id)) Then ListRows = Null: Exit Function
        key = handles(CStr(id))
        If Not caches.Exists(key) Then ListRows = Null: Exit Function
        Set rows = caches(key)
        If row < 0 Or row >= rows.Count Then ListRows = Null: Exit Function
        values = rows(CLng(row) + 1)
        If col < 0 Or col > UBound(values) Then
            ListRows = Null
        ElseIf ctl.Name = "lstCodes" And CLng(col) = 4 Then
            ListRows = IIf(CBool(values(4)), "〇", "")
        Else
            ListRows = values(CLng(col))
        End If
    Case acLBGetFormat
        ListRows = Null
    Case acLBEnd
        If handles.Exists(CStr(id)) Then handles.Remove CStr(id)
        ListRows = Null
    End Select
End Function
