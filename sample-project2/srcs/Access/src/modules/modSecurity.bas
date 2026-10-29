Option Compare Binary
Option Explicit
Public gSession As clsSession
Public gBusy As Boolean
Public gEditor As clsEmployeeEdit
Public gCriteria As clsSearchCriteria
Public gCode As clsCodeEdit
Public gOriginal As clsEmployeeEdit
Public Sub EnsureSession()
    If gSession Is Nothing Then Set gSession = New clsSession
End Sub
Public Function TouchActivity() As Boolean
    EnsureSession
    If Not gSession.IsAuthenticated Then Exit Function
    If GetTickCount64() - gSession.LastActivityTick >= 1800000 Then
        gSession.Clear: Exit Function
    End If
    gSession.LastActivityTick = GetTickCount64(): TouchActivity = True
End Function
Public Sub RequireCurrent(ByVal session As clsSession, ByVal requiredRole As String, ByVal db As DAO.Database)
    Dim q As DAO.QueryDef, r As DAO.Recordset
    If session Is Nothing Then Reject "MSG-002"
    If Not session.IsAuthenticated Then Reject "MSG-002"
    If GetTickCount64() - session.LastActivityTick >= 1800000 Then session.Clear: Reject "MSG-002"
    Set q = Query(db, "PARAMETERS p Text(40); SELECT * FROM m_app_user WHERE user_id=p", session.UserId)
    Set r = ReadOne(q)
    If r.EOF Then session.Clear: Reject "MSG-002"
    If Not r!is_enabled Then session.Clear: Reject "MSG-002"
    If r!role_id <> "ADMIN" And r!role_id <> "STAFF" Then Reject "MSG-003"
    session.RoleId = r!role_id: session.DisplayName = r!display_name
    If requiredRole = "ADMIN" And session.RoleId <> "ADMIN" Then Reject "MSG-003"
    r.Close: q.Close
End Sub
Public Function Authenticate(ByVal login As String, ByVal password As String) As clsResult
    Dim u As New clsUnitOfWork, q As DAO.QueryDef, r As DAO.Recordset, now As Date, passed As Boolean, userId As String, role As String, name As String, count As Long, i As Long, c As Long
    On Error GoTo Failed
    Call EnsureSession: gSession.Clear
    If ScalarLength(login) > 20 Then GoTo Denied
    login = UCase$(CStr(Nz(SaveText(login), "")))
    If Len(login) < 1 Or Len(login) > 20 Then GoTo Denied
    For i = 1 To Len(login)
        c = AscW(Mid$(login, i, 1))
        If Not ((c >= 48 And c <= 57) Or (c >= 65 And c <= 90)) Then GoTo Denied
    Next
    If ScalarLength(password) < MinimumPasswordScalars Or ScalarLength(password) > 128 Then GoTo Denied
    u.OpenUnit True
    Set q = Query(u.Db, "PARAMETERS p Text(20); SELECT * FROM m_app_user WHERE login_id=p", login)
    Set r = ReadOne(q, True)
    If r.EOF Then GoTo Denied
    If Not r!is_enabled Or (r!role_id <> "ADMIN" And r!role_id <> "STAFF") Then GoTo Denied
    now = UtcNow()
    count = r!failed_count
    If count < 0 Or count > 5 Then GoTo Denied
    If count = 5 And IsNull(r!locked_until) Then GoTo Denied
    If count <> 5 And Not IsNull(r!locked_until) Then GoTo Denied
    If Not IsNull(r!locked_until) Then
        If r!locked_until > now Then GoTo Denied
        count = 0
    End If
    passed = VerifyPassword(password, CStr(r!password_verifier))
    r.Edit
    If passed Then
        r!failed_count = 0: r!locked_until = Null
        userId = r!user_id: role = r!role_id: name = r!display_name
    Else
        count = count + 1: If count > 5 Then count = 5
        r!failed_count = count: r!locked_until = Null
        If count = 5 Then r!locked_until = DateAdd("n", 15, now)
    End If
    r.Update: r.Close: q.Close: u.Commit: u.CloseUnit
    password = ""
    If Not passed Then GoTo Denied
    gSession.UserId = userId: gSession.RoleId = role: gSession.DisplayName = name
    gSession.LastActivityTick = GetTickCount64(): gSession.IsAuthenticated = True
    Set Authenticate = MakeResult("OK"): Exit Function
Denied:
    u.Cancel: u.CloseUnit: password = ""
    Set Authenticate = MakeResult("Validation", "MSG-001"): Exit Function
Failed:
    Resume Denied
End Function
Public Function Authorize(ByVal requiredRole As String) As clsResult
    Call EnsureSession
    Set Authorize = AuthorizeSession(gSession, requiredRole)
End Function
Public Function AuthorizeSession(ByVal session As clsSession, ByVal requiredRole As String) As clsResult
    Dim u As New clsUnitOfWork, text As String
    On Error GoTo Failed
    u.OpenUnit True: RequireCurrent session, requiredRole, u.Db
    u.Commit: u.CloseUnit: Set AuthorizeSession = MakeResult("OK"): Exit Function
Failed:
    text = Err.Description: Set AuthorizeSession = Failure(text, u, True)
End Function
