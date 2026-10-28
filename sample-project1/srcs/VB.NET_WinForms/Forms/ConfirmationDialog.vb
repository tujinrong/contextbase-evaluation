Imports System.Drawing
Imports System.Windows.Forms

Namespace Forms
    Public Class ConfirmationDialog
        Inherits Form
        Private ReadOnly _reason As New TextBox With {.Multiline = True, .MaxLength = 120, .Dock = DockStyle.Bottom, .Height = 64}
        Public ReadOnly Property Reason As String
            Get
                Return _reason.Text
            End Get
        End Property
        Public Sub New(content As String, accept As String)
            Me.Text = "確認" : ClientSize = New Size(640,326) : MinimumSize = New Size(650,360) : Font = New Font("Segoe UI",9) : StartPosition = FormStartPosition.CenterParent
            Dim contentBox As New TextBox With {.Text = content, .ReadOnly = True, .Multiline = True, .Dock = DockStyle.Fill, .ScrollBars = ScrollBars.Vertical}
            Dim title As New Label With {.Text = "理由を60文字以内で入力してください。", .Dock = DockStyle.Bottom, .Height = 30}
            Dim row As New FlowLayoutPanel With {.Dock = DockStyle.Bottom, .Height = 43, .FlowDirection = FlowDirection.RightToLeft, .Padding = New Padding(8)}
            Dim cancel As New Button With {.Text = "取消", .DialogResult = DialogResult.Cancel}
            Dim ok As New Button With {.Text = accept, .Width = 210}
            AddHandler ok.Click, Sub(sender, e)
                                     If String.IsNullOrWhiteSpace(_reason.Text) OrElse _reason.Text.EnumerateRunes().Count() > 60 Then
                                         MessageBox.Show(Me, "理由を60文字以内で入力してください。") : Return
                                     End If
                                     DialogResult = DialogResult.OK
                                 End Sub
            row.Controls.Add(cancel) : row.Controls.Add(ok)
            CancelButton = cancel : AcceptButton = cancel
            Controls.Add(contentBox) : Controls.Add(title) : Controls.Add(_reason) : Controls.Add(row)
        End Sub
    End Class
End Namespace
