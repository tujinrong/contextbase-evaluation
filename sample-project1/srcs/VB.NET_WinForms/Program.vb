Imports System.Windows.Forms
Imports StudentManagement.WinForms.Application
Imports StudentManagement.WinForms.Forms

Module Program
    <STAThread>
    Public Sub Main()
        System.Windows.Forms.Application.SetHighDpiMode(HighDpiMode.PerMonitorV2)
        System.Windows.Forms.Application.EnableVisualStyles()
        System.Windows.Forms.Application.SetCompatibleTextRenderingDefault(False)
        Try
            Dim connection = Environment.GetEnvironmentVariable("STUDENT_DB_CONNECTION")
            If String.IsNullOrWhiteSpace(connection) Then Throw New InvalidOperationException("STUDENT_DB_CONNECTIONに証明書検証付きSQL Server接続文字列を設定してください。")
            Dim service = New StudentApplicationService(connection)
            System.Windows.Forms.Application.Run(New FrmStudentSearch(service))
        Catch ex As Exception
            MessageBox.Show(If(TypeOf ex Is InvalidOperationException, ex.Message, "起動設定を確認してください。"), "学生管理", MessageBoxButtons.OK, MessageBoxIcon.Error)
        End Try
    End Sub
End Module
