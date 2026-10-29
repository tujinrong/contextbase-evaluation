Option Compare Binary
Option Explicit
Private Sub InsertRow(ByVal db As DAO.Database, ByVal table As String, ByVal fields As Variant, ByVal values As Variant)
    Dim r As DAO.Recordset, i As Long
    Set r = db.OpenRecordset(table, dbOpenDynaset): r.AddNew
    For i = 0 To UBound(fields): r.Fields(CStr(fields(i))).Value = values(i): Next
    r.Update: r.Close
End Sub
Private Function SeedEmployee(ByVal db As DAO.Database, ByVal values As Variant, ByVal at As Date) As Long
    Dim e As New clsEmployeeEdit, r As DAO.Recordset
    e.EmployeeNo = values(0): e.Name = values(1): e.Kana = values(2): e.Department = values(3): e.Status = values(4)
    e.JoinDate = values(5): e.Summary = values(6): e.Skills = values(7): e.Qualifications = values(8): e.SelfPr = values(9)
    Set r = db.OpenRecordset("m_employee", dbOpenDynaset): r.AddNew
    WriteEmployee r, e, "SP2ADMIN", at, 1: r.Update: r.Bookmark = r.LastModified: SeedEmployee = r!employee_id: r.Close
End Function
Private Sub SeedCareer(ByVal db As DAO.Database, ByVal id As Long, ByVal values As Variant)
    Dim c As New clsCareerDraft, r As DAO.Recordset
    c.StartMonth = values(0): c.EndMonth = values(1): c.Company = values(2): c.Project = values(3): c.Description = values(4): c.Duties = values(5)
    c.Achievements = values(6): c.Technologies = values(7): c.RoleCode = values(8): c.TeamSize = values(9): c.Phases = values(10)
    NormalizeCareer c, BusinessDate()
    Set r = db.OpenRecordset("t_career", dbOpenDynaset): r.AddNew: WriteCareer r, c, id: r.Update: r.Close
End Sub
Public Function InitializeDemo(ByVal adminPassword As String, ByVal staffPassword As String) As Boolean
    Dim u As New clsUnitOfWork, categories As Variant, names As Variant, codes As Variant, group As Variant, i As Long, j As Long, at As Date, id1 As Long, id2 As Long, id3 As Long, text As String
    On Error GoTo Failed
    If Not CurrentDb.Properties("SP2_Staging").Value Then Reject "MSG-020"
    If InStr(1, CurrentProject.FullName, "\.tmp\", vbTextCompare) = 0 Then Reject "MSG-020"
    If BusinessDate() < DateSerial(2026, 10, 27) Then Reject "MSG-020"
    u.OpenUnit True
    If Scalar(u.Db, "SELECT Count(*) FROM m_app_user") <> 0 Or Scalar(u.Db, "SELECT Count(*) FROM m_code") <> 0 Or Scalar(u.Db, "SELECT Count(*) FROM m_employee") <> 0 Or Scalar(u.Db, "SELECT Count(*) FROM t_career") <> 0 Or Scalar(u.Db, "SELECT Count(*) FROM m_code_category") <> 0 Then Reject "MSG-020"
    at = UtcNow()
    categories = Array("DEPARTMENT", "EMPLOYMENT_STATUS", "PROJECT_ROLE"): names = Array("部署", "在籍状況", "役割")
    codes = Array(Array("開発", "基盤", "管理"), Array("在職", "休職", "退職"), Array("メンバー", "リーダー", "PM"))
    For i = 0 To 2
        InsertRow u.Db, "m_code_category", Array("category_id", "category_name"), Array(categories(i), names(i))
    Next
    For i = 0 To 2
        group = codes(i)
        For j = 0 To 2
            InsertRow u.Db, "m_code", Array("category_id", "code", "code_name", "sort_order", "is_enabled", "updated_at", "updated_by", "revision"), Array(categories(i), Format$(j + 1, "00"), group(j), j + 1, True, at, "SP2ADMIN", 1)
        Next
    Next
    InsertRow u.Db, "m_app_user", Array("user_id", "login_id", "display_name", "password_verifier", "role_id", "is_enabled", "failed_count", "locked_until"), Array("SP2ADMIN", "DEMOADMIN", "DEMO管理者", NewVerifier(adminPassword), "ADMIN", True, 0, Null)
    InsertRow u.Db, "m_app_user", Array("user_id", "login_id", "display_name", "password_verifier", "role_id", "is_enabled", "failed_count", "locked_until"), Array("SP2STAFF", "DEMOSTAFF", "DEMO担当者", NewVerifier(staffPassword), "STAFF", True, 0, Null)
    adminPassword = "": staffPassword = ""
    id1 = SeedEmployee(u.Db, Array("000001", "山田 太郎", "ヤマダ タロウ", "01", "01", DateSerial(2022, 4, 1), "業務システムの開発と運用を担当。", "C#、SQL、要件整理", "架空資格A／2023年06月", "利用部門の相談を仕様へ整理することを得意とします。"), at)
    id2 = SeedEmployee(u.Db, Array("000002", "佐藤 花子", "サトウ ハナコ", "02", "01", DateSerial(2024, 4, 1), "基盤運用と監視改善を担当。", "Windows、運用設計", Null, "定常作業を整理し、引継ぎやすい運用を心掛けています。"), at)
    id3 = SeedEmployee(u.Db, Array("000003", "鈴木 一郎", "スズキ イチロウ", "03", "03", DateSerial(2021, 4, 1), "管理業務を担当。", "文書整理", Null, Null), at)
    SeedCareer u.Db, id1, Array(DateSerial(2022, 4, 1), DateSerial(2024, 3, 1), "デモ開発株式会社", "受発注管理改善（架空）", "受発注管理の画面改善。", "設計、実装、試験を担当。", "入力確認の手順を整理。", "OS: Windows／言語・FW: C#／DB: SQL Server", "01", 5, "基本設計、製造、試験")
    SeedCareer u.Db, id1, Array(DateSerial(2024, 4, 1), Null, "デモ開発株式会社", "社員情報管理（架空）", "社内管理システムの改善。", "業務整理と画面設計を担当。", "申請項目を共通化。", "OS: Windows／言語・FW: ASP.NET Core／DB: SQL Server", "02", 4, "要件整理、基本設計")
    SeedCareer u.Db, id2, Array(DateSerial(2024, 4, 1), Null, "デモ基盤株式会社", "運用監視改善（架空）", "監視と運用手順の改善。", "監視条件と手順書を整備。", "作業漏れの確認表を作成。", "OS: Windows／DB: 未使用", "01", 3, "運用設計、運用")
    AssertIntegrity u.Db
    u.Commit: u.CloseUnit: InitializeDemo = True: Exit Function
Failed:
    text = Err.Description: u.Cancel: u.CloseUnit: adminPassword = "": staffPassword = ""
    Err.Raise vbObjectError + 760, , "Initial setup failed (no secrets logged). " & Left$(text, 7)
End Function
