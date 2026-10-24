Imports System.Drawing
Imports System.Windows.Forms
Imports StudentManagement.WinForms.Controls

Namespace Forms
    Partial Public Class FrmStudentSearch
        Public ReadOnly txtStudentNo As New TextBox With {.MaxLength = 30}
        Public ReadOnly txtName As New TextBox With {.MaxLength = 16}
        Public ReadOnly cboClass As New ComboBox
        Public ReadOnly clbStatuses As New CheckedListBox With {.CheckOnClick = True, .Height = 38, .MultiColumn = True, .ColumnWidth = 85}
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
            Text = "学生管理：検索" : ClientSize = New Size(1280, 650) : MinimumSize = New Size(850, 500)
            AutoScaleDimensions = New SizeF(96.0F, 96.0F) : AutoScaleMode = AutoScaleMode.Dpi : Font = New Font("Yu Gothic UI", 9)
            Dim panel As New TableLayoutPanel With {.Dock = DockStyle.Top, .ColumnCount = 6, .RowCount = 2, .Height = 90, .Padding = New Padding(6)}
            For i = 0 To 2
                panel.ColumnStyles.Add(New ColumnStyle(SizeType.Absolute, 90)) : panel.ColumnStyles.Add(New ColumnStyle(SizeType.Percent, 33.33F))
            Next
            Dim labels = {"学籍番号", "氏名", "クラス", "在籍区分（全解除は全区分）"}
            Dim fields As Control() = {txtStudentNo, txtName, cboClass, clbStatuses}
            For i = 0 To 2
                panel.Controls.Add(New Label With {.Text = labels(i), .Dock = DockStyle.Fill, .TextAlign = ContentAlignment.MiddleLeft}, i * 2, 0)
                fields(i).MinimumSize = New Size(0,34) : fields(i).Dock = DockStyle.Fill : fields(i).AccessibleName = labels(i) : fields(i).TabIndex = i : panel.Controls.Add(fields(i), i * 2 + 1, 0)
            Next
            panel.Controls.Add(New Label With {.Text = labels(3), .Dock = DockStyle.Fill}, 0, 1)
            panel.Controls.Add(clbStatuses, 1, 1) : panel.SetColumnSpan(clbStatuses, 5) : clbStatuses.Dock = DockStyle.Fill : clbStatuses.AccessibleName = "在籍区分" : clbStatuses.TabIndex = 3
            For Each combo In {cboClass, cboPageSize, cboSortKey, cboSortDirection}
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
            dgvStudents.AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill
            dgvStudents.DefaultCellStyle.WrapMode = DataGridViewTriState.True : dgvStudents.AutoSizeRowsMode = DataGridViewAutoSizeRowsMode.AllCells
            Dim properties = {"StudentNo", "NameDisplay", "BirthDateWareki", "YearGrade", "ClassDisplay", "EnrollmentStatusName"}
            Dim captions = {"学籍番号", "氏名／カナ", "生年月日（和暦）", "年度／学年", "クラス", "在籍区分"}
            Dim widths = {15, 21, 16, 13, 18, 9}
            For i = 0 To properties.Length - 1
                dgvStudents.Columns.Add(New DataGridViewTextBoxColumn With {.DataPropertyName = properties(i), .HeaderText = captions(i), .FillWeight = widths(i), .MinimumWidth = 70, .SortMode = DataGridViewColumnSortMode.NotSortable})
            Next
            dgvStudents.Columns.Add(New DataGridViewButtonColumn With {.Name = "colAction", .HeaderText = "操作", .Text = "開く", .FillWeight = 8, .UseColumnTextForButtonValue = True})
            Controls.Add(dgvStudents) : Controls.Add(pager) : Controls.Add(result) : Controls.Add(actions) : Controls.Add(panel) : Controls.Add(lblMessage)
        End Sub
    End Class
End Namespace
