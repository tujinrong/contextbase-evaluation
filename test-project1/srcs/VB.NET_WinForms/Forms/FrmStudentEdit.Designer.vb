Imports System.Drawing
Imports System.Windows.Forms
Imports StudentManagement.WinForms.Controls

Namespace Forms
    Partial Public Class FrmStudentEdit
        Public ReadOnly lblStudentId As New Label With {.AutoSize = True, .Text = "自動採番"}
        Public ReadOnly txtStudentNo As New TextBox With {.MaxLength = 30}
        Public ReadOnly txtStudentName As New TextBox With {.MaxLength = 16}
        Public ReadOnly txtStudentNameKana As New TextBox With {.MaxLength = 72}
        Public ReadOnly birthDateInput As New JapaneseBirthDateControl
        Public ReadOnly cboGender As New ComboBox
        Public ReadOnly txtPostalCode As New TextBox With {.MaxLength = 20}
        Public ReadOnly cboPrefecture As New ComboBox
        Public ReadOnly txtAddressLine1 As New TextBox With {.MaxLength = 90}
        Public ReadOnly txtAddressLine2 As New TextBox With {.MaxLength = 90}
        Public ReadOnly txtPhoneNumber As New TextBox With {.MaxLength = 40}
        Public ReadOnly txtEmailAddress As New TextBox With {.MaxLength = 120}
        Public ReadOnly dtpAdmissionDate As New NullableDateControl
        Public ReadOnly cboEnrollmentStatus As New ComboBox
        Public ReadOnly dtpEnrollmentEndDate As New NullableDateControl
        Public ReadOnly cboSchoolYear As New ComboBox
        Public ReadOnly cboGrade As New ComboBox
        Public ReadOnly cboClass As New ComboBox
        Public ReadOnly lblCapacity As New Label With {.AutoSize = True}
        Public ReadOnly txtEmergencyContactName As New TextBox With {.MaxLength = 16}
        Public ReadOnly cboRelationship As New ComboBox
        Public ReadOnly txtEmergencyPhoneNumber As New TextBox With {.MaxLength = 40}
        Public ReadOnly txtRemarks As New TextBox With {.MaxLength = 240, .Multiline = True, .ScrollBars = ScrollBars.Vertical, .Height = 75}
        Public ReadOnly txtOperationReason As New TextBox With {.MaxLength = 120, .Multiline = True, .Height = 55}
        Public ReadOnly lblUpdatedAt As New Label With {.AutoSize = True}
        Public ReadOnly lblMessage As New TextBox With {.ReadOnly = True, .TabStop = False, .Multiline = True, .ScrollBars = ScrollBars.Vertical, .Dock = DockStyle.Top, .Height = 70, .ForeColor = Color.Maroon}
        Public ReadOnly btnSave As New Button With {.Text = "登録／更新"}
        Public ReadOnly btnDelete As New Button With {.Text = "論理削除"}
        Public ReadOnly btnReset As New Button With {.Text = "入力クリア／編集取消", .Width = 160}
        Public ReadOnly btnReload As New Button With {.Text = "最新情報を再読込", .Width = 145}
        Public ReadOnly btnBack As New Button With {.Text = "検索へ戻る", .Width = 120}
        Public ReadOnly Fields As New Dictionary(Of String, Control)
        Public ReadOnly Errors As New ErrorProvider
        Private ReadOnly _studentScroll As New Panel With {.Dock = DockStyle.Fill, .AutoScroll = True, .TabIndex = 0}
        Private Sub InitializeComponent()
            ClientSize = New Size(1280, 650) : MinimumSize = New Size(850, 500) : AutoScaleDimensions = New SizeF(96.0F, 96.0F) : AutoScaleMode = AutoScaleMode.Dpi : Font = New Font("Yu Gothic UI", 9)
            Dim body As New TableLayoutPanel With {.Dock = DockStyle.Top, .AutoSize = True, .ColumnCount = 1, .Padding = New Padding(6), .MinimumSize = New Size(1160, 0), .TabIndex = 0}
            Dim basic As New TableLayoutPanel With {.Dock = DockStyle.Top, .ColumnCount = 6, .RowCount = 2, .Height = 86, .TabIndex = 0}
            For i = 0 To 2
                basic.ColumnStyles.Add(New ColumnStyle(SizeType.Absolute, 90)) : basic.ColumnStyles.Add(New ColumnStyle(SizeType.Percent, 33.33F))
            Next
            Dim basicFields As Control() = {lblStudentId, txtStudentNo, txtStudentName, txtStudentNameKana, birthDateInput, cboGender}
            Dim basicLabels = {"学生管理番号", "学籍番号 ※15文字", "氏名 ※8文字", "カナ ※入力36／保存18", "生年月日 ※和暦", "性別 ※"}
            Dim basicNames = {"StudentId", "StudentNo", "StudentName", "StudentNameKana", "BirthDateInput", "GenderCode"}
            For i = 0 To 5
                Dim col = (i Mod 3) * 2 : Dim row = i \ 3
                basic.Controls.Add(New Label With {.Text = basicLabels(i), .Dock = DockStyle.Fill, .TextAlign = ContentAlignment.MiddleLeft}, col, row)
                basicFields(i).MinimumSize = New Size(0,34) : basicFields(i).Dock = DockStyle.Fill : basicFields(i).TabIndex = i : basicFields(i).AccessibleName = basicLabels(i) : basic.Controls.Add(basicFields(i), col + 1, row) : Fields.Add(basicNames(i), basicFields(i))
            Next
            body.Controls.Add(basic)
            Dim columns As New TableLayoutPanel With {.Dock = DockStyle.Top, .AutoSize = True, .ColumnCount = 3, .TabIndex = 1}
            For i = 0 To 2
                columns.ColumnStyles.Add(New ColumnStyle(SizeType.Percent, 33.33F))
            Next
            columns.Controls.Add(BuildSection("住所・本人連絡先", {"郵便番号 ※入力10／保存7", "都道府県 ※", "住所1 ※45文字", "住所2 45文字", "本人電話 入力20", "本人メール60文字"}, {"PostalCode", "PrefectureCode", "AddressLine1", "AddressLine2", "PhoneNumber", "EmailAddress"}, {txtPostalCode, cboPrefecture, txtAddressLine1, txtAddressLine2, txtPhoneNumber, txtEmailAddress}, 0), 0, 0)
            columns.Controls.Add(BuildSection("在籍・所属", {"入学日 ※西暦", "在籍区分 ※", "卒業・退学日 03/04必須", "選択補助：年度", "選択補助：学年", "クラス 01/02必須", "人数・定員（参考）"}, {"AdmissionDate", "EnrollmentStatusCode", "EnrollmentEndDate", "SchoolYear", "GradeCode", "ClassId", "Capacity"}, {dtpAdmissionDate, cboEnrollmentStatus, dtpEnrollmentEndDate, cboSchoolYear, cboGrade, cboClass, lblCapacity}, 1), 1, 0)
            columns.Controls.Add(BuildSection("緊急連絡先・備考・理由", {"緊急氏名8文字", "続柄（3項目一式）", "緊急電話 入力20", "備考120文字", "確認・変更理由60文字"}, {"EmergencyContactName", "RelationshipCode", "EmergencyPhoneNumber", "Remarks", "Reason"}, {txtEmergencyContactName, cboRelationship, txtEmergencyPhoneNumber, txtRemarks, txtOperationReason}, 2), 2, 0)
            body.Controls.Add(columns)
            lblUpdatedAt.Dock = DockStyle.Top : lblUpdatedAt.Padding = New Padding(4) : body.Controls.Add(lblUpdatedAt) : Fields.Add("UpdatedAt", lblUpdatedAt)
            Dim actions As New FlowLayoutPanel With {.Dock = DockStyle.Top, .AutoSize = True, .MinimumSize = New Size(0, 45), .TabIndex = 2}
            actions.Controls.AddRange({btnSave, btnReset, btnReload, btnDelete, btnBack})
            For i = 0 To actions.Controls.Count - 1
                actions.Controls(i).TabIndex = i : actions.Controls(i).MinimumSize = New Size(0, 34)
            Next
            body.Controls.Add(actions)
            For Each combo In {cboGender, cboPrefecture, cboEnrollmentStatus, cboSchoolYear, cboGrade, cboClass, cboRelationship}
                combo.DropDownStyle = ComboBoxStyle.DropDownList
            Next
            Errors.ContainerControl = Me
            _studentScroll.Controls.Add(body)
            Me.Controls.Add(_studentScroll) : Me.Controls.Add(lblMessage)
        End Sub
        Private Function BuildSection(title As String, labels As String(), names As String(), controls As Control(), tab As Integer) As Control
            Dim group As New GroupBox With {.Text = title, .Dock = DockStyle.Top, .AutoSize = True, .Padding = New Padding(4, 18, 4, 4), .TabIndex = tab}
            Dim grid As New TableLayoutPanel With {.Dock = DockStyle.Top, .AutoSize = True, .ColumnCount = 2}
            grid.ColumnStyles.Add(New ColumnStyle(SizeType.Absolute, 100)) : grid.ColumnStyles.Add(New ColumnStyle(SizeType.Percent, 100))
            For i = 0 To controls.Length - 1
                grid.RowStyles.Add(New RowStyle(SizeType.Absolute, If(names(i) = "Remarks", 62, If(names(i) = "Reason", 56, 40))))
                grid.Controls.Add(New Label With {.Text = labels(i), .Dock = DockStyle.Fill, .TextAlign = ContentAlignment.MiddleLeft}, 0, i)
                controls(i).MinimumSize = New Size(0,34) : controls(i).Dock = DockStyle.Fill : controls(i).TabIndex = i : controls(i).AccessibleName = labels(i) : grid.Controls.Add(controls(i), 1, i) : Fields.Add(names(i), controls(i))
            Next
            group.Controls.Add(grid) : Return group
        End Function
    End Class
End Namespace
