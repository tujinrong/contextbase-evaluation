Imports System.Drawing
Imports System.Windows.Forms
Imports StudentManagement.WinForms.Controls

Namespace Forms
    Partial Public Class FrmStudentSearch
        Public ReadOnly txtStudentNo As New TextBox With {.MaxLength = 30}
        Public ReadOnly txtName As New TextBox With {.MaxLength = 16}
        Public ReadOnly cboClass As New ComboBox
        Public ReadOnly pnlStatuses As New Panel
        Public ReadOnly StatusChecks As CheckBox() = {New CheckBox With {.Text = "在学", .Tag = "01", .Checked = True}, New CheckBox With {.Text = "休学", .Tag = "02", .Checked = True}, New CheckBox With {.Text = "卒業", .Tag = "03"}, New CheckBox With {.Text = "退学", .Tag = "04"}}
        Public ReadOnly btnSearch As New Button With {.Text = "検索"}
        Public ReadOnly btnClear As New Button With {.Text = "クリア"}
        Public ReadOnly btnNew As New Button With {.Text = "新規登録"}
        Public ReadOnly btnMenu As New Button With {.Text = "メニューへ"}
        Public ReadOnly cboSortKey As New ComboBox
        Public ReadOnly cboSortDirection As New ComboBox
        Public ReadOnly lblMessage As New Label With {.AutoSize = False, .ForeColor = SystemColors.WindowText}
        Public ReadOnly lblCount As New Label With {.AutoSize = False, .Text = "未検索"}
        Public ReadOnly lblSearchedAt As New Label With {.AutoSize = False}
        Public ReadOnly dgvStudents As New DataGridView With {.ReadOnly = True, .AllowUserToAddRows = False, .AllowUserToDeleteRows = False, .AutoGenerateColumns = False, .SelectionMode = DataGridViewSelectionMode.FullRowSelect, .MultiSelect = False, .RowHeadersVisible = False}
        Private ReadOnly _searchSurface As New Panel With {.Location = Point.Empty, .Size = New Size(1180, 610), .MinimumSize = New Size(1180, 610)}
        Private _messageExtra As Integer
        Private Sub InitializeComponent()
            Text = "学生管理システム − 学生検索" : ClientSize = New Size(1180, 610) : MinimumSize = New Size(640, 420)
            AutoScaleDimensions = New SizeF(96.0F, 96.0F) : AutoScaleMode = AutoScaleMode.Dpi : Font = New Font("Segoe UI", 9)
            BackColor = SystemColors.Control : ForeColor = SystemColors.WindowText : AutoScroll = True : AutoScrollMinSize = New Size(1180, 610)
            Dim conditions As New GroupBox With {.Text = "検索条件", .Location = New Point(8, 36), .Size = New Size(1164, 100), .Anchor = AnchorStyles.Top Or AnchorStyles.Left Or AnchorStyles.Right, .TabIndex = 0}
            SearchField(conditions, "学籍番号", txtStudentNo, 20, 56, 80, 144, 0)
            SearchField(conditions, "氏名", txtName, 272, 56, 44, 128, 1)
            SearchField(conditions, "クラス", cboClass, 472, 56, 64, 612, 2)
            cboClass.Anchor = AnchorStyles.Top Or AnchorStyles.Left Or AnchorStyles.Right : cboClass.DropDownWidth = 612
            SearchField(conditions, "在籍区分", pnlStatuses, 20, 96, 80, 560, 3)
            For i = 0 To StatusChecks.Length - 1
                StatusChecks(i).Name = "chkStatus" & CStr(StatusChecks(i).Tag)
                StatusChecks(i).SetBounds(i * 84, 0, 80, 24) : StatusChecks(i).TabIndex = i : pnlStatuses.Controls.Add(StatusChecks(i))
            Next
            Dim buttons = {btnSearch, btnClear, btnNew, btnMenu}
            Dim lefts = {720, 816, 912, 1032} : Dim widths = {88, 88, 112, 120}
            For i = 0 To buttons.Length - 1
                buttons(i).SetBounds(lefts(i) - conditions.Left, 94 - conditions.Top, widths(i), 27)
                buttons(i).TabIndex = i + 4 : buttons(i).Anchor = AnchorStyles.Top Or AnchorStyles.Right : conditions.Controls.Add(buttons(i))
            Next
            For Each combo In {cboClass, cboSortKey, cboSortDirection}
                combo.DropDownStyle = ComboBoxStyle.DropDownList
            Next
            cboSortKey.Items.AddRange({New Choice("studentNo", "学籍番号"), New Choice("name", "氏名"), New Choice("admissionDate", "入学日"), New Choice("updatedAt", "更新日時")}) : cboSortKey.SelectedIndex = 0
            cboSortDirection.Items.AddRange({New Choice("asc", "昇順"), New Choice("desc", "降順")}) : cboSortDirection.SelectedIndex = 0
            _searchSurface.Controls.Add(conditions)
            lblMessage.SetBounds(8, 8, 1164, 24) : lblMessage.Anchor = AnchorStyles.Top Or AnchorStyles.Left Or AnchorStyles.Right
            lblCount.SetBounds(8, 148, 740, 20)
            Dim sortLabel As New Label With {.Text = "並び順", .Location = New Point(772, 144), .Size = New Size(56, 24), .TextAlign = ContentAlignment.MiddleLeft, .Anchor = AnchorStyles.Top Or AnchorStyles.Right}
            cboSortKey.SetBounds(832, 144, 160, 24) : cboSortKey.TabIndex = 1 : cboSortKey.Anchor = AnchorStyles.Top Or AnchorStyles.Right
            Dim directionLabel As New Label With {.Text = "方向", .Location = New Point(1016, 144), .Size = New Size(36, 24), .TextAlign = ContentAlignment.MiddleLeft, .Anchor = AnchorStyles.Top Or AnchorStyles.Right}
            cboSortDirection.SetBounds(1056, 144, 96, 24) : cboSortDirection.TabIndex = 2 : cboSortDirection.Anchor = AnchorStyles.Top Or AnchorStyles.Right
            dgvStudents.SetBounds(8, 178, 1164, 390) : dgvStudents.TabIndex = 3 : dgvStudents.AccessibleName = "学生一覧"
            dgvStudents.Anchor = AnchorStyles.Top Or AnchorStyles.Bottom Or AnchorStyles.Left Or AnchorStyles.Right
            dgvStudents.AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.None
            dgvStudents.DefaultCellStyle.WrapMode = DataGridViewTriState.True : dgvStudents.AutoSizeRowsMode = DataGridViewAutoSizeRowsMode.DisplayedCells
            dgvStudents.RowTemplate.Height = 42 : dgvStudents.RowTemplate.MinimumHeight = 42
            dgvStudents.ColumnHeadersHeightSizeMode = DataGridViewColumnHeadersHeightSizeMode.DisableResizing : dgvStudents.ColumnHeadersHeight = 24
            Dim properties = {"StudentNo", "NameDisplay", "BirthDateWareki", "YearGrade", "ClassDisplay", "EnrollmentStatusName"}
            Dim captions = {"学籍番号", "氏名／カナ", "生年月日", "年度／学年", "クラス", "在籍区分"}
            Dim columnWidths = {144, 248, 150, 108, 290, 96}
            For i = 0 To properties.Length - 1
                dgvStudents.Columns.Add(New DataGridViewTextBoxColumn With {.Name = properties(i), .DataPropertyName = properties(i), .HeaderText = captions(i), .Width = columnWidths(i), .MinimumWidth = 70, .SortMode = DataGridViewColumnSortMode.NotSortable})
            Next
            dgvStudents.Columns.Add(New DataGridViewButtonColumn With {.Name = "colAction", .HeaderText = "操作", .Text = "編集", .Width = 110, .UseColumnTextForButtonValue = True})
            lblSearchedAt.SetBounds(8, 582, 1164, 20) : lblSearchedAt.Anchor = AnchorStyles.Bottom Or AnchorStyles.Left Or AnchorStyles.Right
            _searchSurface.Controls.AddRange({lblMessage, lblCount, sortLabel, cboSortKey, directionLabel, cboSortDirection, dgvStudents, lblSearchedAt})
            AddHandler lblMessage.TextChanged,Sub() LayoutSearchMessage()
            Controls.Add(_searchSurface)
            AddHandler ClientSizeChanged, Sub() _searchSurface.Size = New Size(Math.Max(ClientSize.Width, _searchSurface.MinimumSize.Width), Math.Max(ClientSize.Height, _searchSurface.MinimumSize.Height))
        End Sub
        Private Sub LayoutSearchMessage()
            Dim height=Math.Max(CInt(24*DeviceDpi/96),TextRenderer.MeasureText(lblMessage.Text,lblMessage.Font,New Size(Math.Max(100,lblMessage.Width),Integer.MaxValue),TextFormatFlags.WordBreak).Height+4)
            Dim extra=height-CInt(24*DeviceDpi/96) : Dim delta=extra-_messageExtra
            If delta=0 Then Return
            _messageExtra=extra : lblMessage.Height=height
            _searchSurface.MinimumSize=New Size(_searchSurface.MinimumSize.Width,CInt(610*DeviceDpi/96)+extra)
            _searchSurface.Size=New Size(Math.Max(ClientSize.Width,_searchSurface.MinimumSize.Width),Math.Max(ClientSize.Height,_searchSurface.MinimumSize.Height))
            For Each child As Control In _searchSurface.Controls
                If child Is lblMessage OrElse (child.Anchor And AnchorStyles.Bottom)<>0 Then Continue For
                child.Top+=delta
            Next
            dgvStudents.Top+=delta : dgvStudents.Height-=delta
            AutoScrollMinSize=_searchSurface.MinimumSize
        End Sub
        Private Shared Sub SearchField(group As GroupBox, caption As String, field As Control, x As Integer, y As Integer, labelWidth As Integer, width As Integer, tab As Integer)
            group.Controls.Add(New Label With {.Text = caption, .Location = New Point(x - group.Left, y - group.Top), .Size = New Size(labelWidth, 24), .TextAlign = ContentAlignment.MiddleLeft})
            field.SetBounds(x + labelWidth + 4 - group.Left, y - group.Top, width, 24)
            field.AccessibleName = caption : field.TabIndex = tab : group.Controls.Add(field)
        End Sub
    End Class
End Namespace
