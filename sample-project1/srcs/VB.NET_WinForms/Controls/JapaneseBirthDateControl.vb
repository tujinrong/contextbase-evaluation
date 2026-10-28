Imports System.Windows.Forms
Imports Core = StudentManagement.WinForms.Domain

Namespace Controls
    ' REG-005 / UI-15. Each raw component is preserved rather than DateTimePicker coercion.
    Public Class JapaneseBirthDateControl
        Inherits UserControl
        Public ReadOnly Era As New ComboBox With {.DropDownStyle = ComboBoxStyle.DropDownList, .Width = 68}
        Public ReadOnly Year As New TextBox With {.MaxLength = 4, .Width = 40, .AccessibleName = "元号年"}
        Public ReadOnly Month As New TextBox With {.MaxLength = 2, .Width = 32, .AccessibleName = "生年月日の月"}
        Public ReadOnly Day As New TextBox With {.MaxLength = 2, .Width = 32, .AccessibleName = "生年月日の日"}
        Public Sub New()
            Height = 24
            Era.AccessibleName = "元号"
            Era.Items.AddRange({New Choice("", "未選択"), New Choice("REIWA", "令和"), New Choice("HEISEI", "平成"), New Choice("SHOWA", "昭和"), New Choice("TAISHO", "大正"), New Choice("MEIJI", "明治")})
            Era.SelectedIndex = 0
            Dim row As New FlowLayoutPanel With {.Dock = DockStyle.Fill, .WrapContents = False, .Margin = Padding.Empty, .Padding = Padding.Empty}
            row.Controls.AddRange({Era, Year, New Label With {.Text = "年", .AutoSize = True}, Month, New Label With {.Text = "月", .AutoSize = True}, Day, New Label With {.Text = "日", .AutoSize = True}})
            For Each part As Control In row.Controls
                part.Margin = New Padding(0,0,3,0)
                If TypeOf part Is Label Then part.AutoSize=False : part.Width=12 : part.Height=24
            Next
            Controls.Add(row)
        End Sub
        Public Function ReadRaw() As Core.BirthDateInput
            Return New Core.BirthDateInput(If(TryCast(Era.SelectedItem, Choice)?.Value, ""), Year.Text, Month.Text, Day.Text)
        End Function
        Public Sub LoadRaw(value As Core.BirthDateInput)
            For i = 0 To Era.Items.Count - 1
                If DirectCast(Era.Items(i), Choice).Value = value.Era Then Era.SelectedIndex = i
            Next
            Year.Text = value.Year : Month.Text = value.Month : Day.Text = value.Day
        End Sub
    End Class
End Namespace
