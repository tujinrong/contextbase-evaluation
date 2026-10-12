Imports System.Drawing
Imports System.Windows.Forms
Imports StudentManagement.WinForms.Controls

Namespace Forms
    Partial Public Class FrmStudentSearch
        Public ReadOnly txtStudentNo As New TextBox With {.MaxLength = 30}
        Public ReadOnly txtName As New TextBox With {.MaxLength = 16}
        Public ReadOnly txtKana As New TextBox With {.MaxLength = 72}
        Public ReadOnly cboSchoolYear As New ComboBox
        Public ReadOnly cboGrade As New ComboBox
        Public ReadOnly cboClass As New ComboBox
        Public ReadOnly chkUnassignedOnly As New CheckBox With {.Text = "未所属のみ"}
        Public ReadOnly clbStatuses As New CheckedListBox With {.CheckOnClick = True, .Height = 70}
        Public ReadOnly cboPrefecture As New ComboBox
        Public ReadOnly txtPhone As New TextBox With {.MaxLength = 40}
        Public ReadOnly txtAdmissionFrom As New TextBox With {.MaxLength = 10}
        Public ReadOnly txtAdmissionTo As New TextBox With {.MaxLength = 10}
        Public ReadOnly btnSearch As New Button With {.Text = "検索"}
        Public ReadOnly btnClear As New Button With {.Text = "クリア"}
        Public ReadOnly btnNew As New Button With {.Text = "新規登録"}
        Public ReadOnly btnMenu As New Button With {.Text = "メニューへ"}
        Public ReadOnly btnFirst As New Button With {.Text = "先頭"}
        Public ReadOnly btnPrev As New Button With {.Text = "前へ"}
        Public ReadOnly btnNext As New Button With {.Text = "次へ"}
        Public ReadOnly btnLast As New Button With {.Text = "最後"}
        Public ReadOnly btnSort As New Button With {.Text = "並び順・件数を反映", .Width = 165}
        Public ReadOnly cboPageSize As New ComboBox With {.Width = 80}
        Public ReadOnly cboSortKey As New ComboBox With {.Width = 120}
        Public ReadOnly cboSortDirection As New ComboBox With {.Width = 90}
        Public ReadOnly lblMessage As New Label With {.AutoSize = False, .Height = 50, .Dock = DockStyle.Top, .ForeColor = Color.Maroon}
        Public ReadOnly lblCount As New Label With {.AutoSize = True, .Text = "未検索", .Padding = New Padding(8)}
        Public ReadOnly lblSearchedAt As New Label With {.AutoSize = True}
        Public ReadOnly dgvStudents As New DataGridView With {.Dock = DockStyle.Fill, .ReadOnly = True, .AllowUserToAddRows = False, .AllowUserToDeleteRows = False, .AutoGenerateColumns = False, .SelectionMode = DataGridViewSelectionMode.FullRowSelect}
        Private Sub InitializeComponent()
            Text = "学生管理：検索" : Width = 1350 : Height = 900 : MinimumSize = New Size(1000, 700)
            AutoScaleMode = AutoScaleMode.Dpi : Font = New Font("Yu Gothic UI", 10)
            Dim panel As New TableLayoutPanel With {.Dock = DockStyle.Top, .ColumnCount = 4, .RowCount = 6, .Height = 285}
            panel.ColumnStyles.Add(New ColumnStyle(SizeType.Absolute, 175)) : panel.ColumnStyles.Add(New ColumnStyle(SizeType.Percent, 50))
            panel.ColumnStyles.Add(New ColumnStyle(SizeType.Absolute, 175)) : panel.ColumnStyles.Add(New ColumnStyle(SizeType.Percent, 50))
            Dim labels = {"学籍番号（15文字）", "氏名（8文字）", "氏名カナ（入力36文字）", "年度", "学年", "クラス", "未所属のみ", "在籍区分（全解除は全区分）", "都道府県", "電話（入力20文字）", "入学日・開始 yyyy-MM-dd", "入学日・終了 yyyy-MM-dd"}
            Dim fields As Control() = {txtStudentNo, txtName, txtKana, cboSchoolYear, cboGrade, cboClass, chkUnassignedOnly, clbStatuses, cboPrefecture, txtPhone, txtAdmissionFrom, txtAdmissionTo}
            For i = 0 To fields.Length - 1
                Dim row = i \ 2 : Dim col = (i Mod 2) * 2
                panel.Controls.Add(New Label With {.Text = labels(i), .Dock = DockStyle.Fill, .TextAlign = ContentAlignment.MiddleLeft}, col, row)
                fields(i).Dock = DockStyle.Fill : fields(i).AccessibleName = labels(i) : panel.Controls.Add(fields(i), col + 1, row)
            Next
            For Each combo In {cboSchoolYear, cboGrade, cboClass, cboPrefecture, cboPageSize, cboSortKey, cboSortDirection}
                combo.DropDownStyle = ComboBoxStyle.DropDownList
            Next
            clbStatuses.Items.AddRange({New Choice("01", "在学"), New Choice("02", "休学"), New Choice("03", "卒業"), New Choice("04", "退学")})
            clbStatuses.SetItemChecked(0, True) : clbStatuses.SetItemChecked(1, True)
            cboPageSize.Items.AddRange({20, 50, 100}) : cboPageSize.SelectedIndex = 0
            cboSortKey.Items.AddRange({New Choice("studentNo", "学籍番号"), New Choice("name", "氏名"), New Choice("admissionDate", "入学日"), New Choice("updatedAt", "更新日時")}) : cboSortKey.SelectedIndex = 0
            cboSortDirection.Items.AddRange({New Choice("asc", "昇順"), New Choice("desc", "降順")}) : cboSortDirection.SelectedIndex = 0
            Dim actions As New FlowLayoutPanel With {.Dock = DockStyle.Top, .Height = 45}
            actions.Controls.AddRange({btnSearch, btnClear, btnNew, btnMenu})
            Dim result As New FlowLayoutPanel With {.Dock = DockStyle.Top, .Height = 45}
            result.Controls.AddRange({lblCount, cboPageSize, cboSortKey, cboSortDirection, btnSort})
            Dim pager As New FlowLayoutPanel With {.Dock = DockStyle.Bottom, .Height = 45}
            pager.Controls.AddRange({btnFirst, btnPrev, btnNext, btnLast, lblSearchedAt})
            Dim properties = {"StudentNo", "StudentName", "StudentNameKana", "BirthDateWareki", "YearGrade", "ClassDisplay", "EnrollmentStatusName", "Address", "PhoneNumber", "UpdatedAt"}
            Dim captions = {"学籍番号", "氏名", "氏名カナ", "生年月日（和暦）", "年度／学年", "クラス", "在籍区分", "住所", "本人電話", "更新日時"}
            For i = 0 To properties.Length - 1
                dgvStudents.Columns.Add(New DataGridViewTextBoxColumn With {.DataPropertyName = properties(i), .HeaderText = captions(i), .Width = If(i = 7, 220, 125), .SortMode = DataGridViewColumnSortMode.NotSortable})
            Next
            dgvStudents.Columns.Add(New DataGridViewButtonColumn With {.Name = "colAction", .HeaderText = "編集／参照", .Text = "開く", .UseColumnTextForButtonValue = True})
            Controls.Add(dgvStudents) : Controls.Add(pager) : Controls.Add(result) : Controls.Add(actions) : Controls.Add(panel) : Controls.Add(lblMessage)
        End Sub
    End Class
End Namespace
