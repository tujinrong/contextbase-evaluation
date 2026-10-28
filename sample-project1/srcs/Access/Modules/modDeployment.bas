Attribute VB_Name = "modDeployment"
Option Explicit
Option Compare Binary

Public Function DeploymentHealth() As String
    Dim tx As New clsUnitOfWork, rs As DAO.Recordset, table As Variant, counts As String, td As DAO.TableDef
    On Error GoTo Failed
    Authorize "Read": tx.BeginWork
    For Each table In Array("m_code_category", "m_code", "m_class", "m_student", "t_operation_log", "t_write_guard")
        Set rs = tx.Database.OpenRecordset("SELECT Count(*) AS n FROM " & table)
        counts = counts & table & "=" & CStr(rs!n) & "|": rs.Close
    Next
    For Each td In CurrentDb.TableDefs
        If Left$(td.Name, 4) <> "MSys" And td.Connect <> "" Then Err.Raise vbObjectError + 194, , "External table link found"
    Next
    tx.CloseWork
    DoCmd.OpenForm "frmStudentSearch"
    Dim frm As Access.Form
    Set frm = Forms("frmStudentSearch")
    If frm!lblCount.Caption <> "未検索" Or frm!cboSortKey <> "studentNo" Or frm!cboSortDirection <> "asc" Then Err.Raise vbObjectError + 194, , "Initial form state invalid"
    Dim ctl As Access.Control
    For Each ctl In frm.Controls
        If ctl.Name = "cboPageSize" Or ctl.Name = "cmdFirst" Or ctl.Name = "cmdPrev" Or ctl.Name = "cmdNext" Or ctl.Name = "cmdLast" Then Err.Raise vbObjectError + 194, , "Retired range control found"
    Next
    DoCmd.Close acForm, "frmStudentSearch"
    DeploymentHealth = "PASS|" & counts & "noExternalLinks=True|searchFormInitialized=True|role=" & CurrentRole()
    Exit Function
Failed:
    DeploymentHealth = "FAIL|" & CStr(Err.Number) & "|" & Err.Description
    On Error Resume Next: tx.CloseWork: DoCmd.Close acForm, "frmStudentSearch"
End Function
