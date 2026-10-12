Imports System.Drawing
Imports System.Windows.Forms
Imports StudentManagement.WinForms.Controls

Namespace Forms
    Partial Public Class FrmStudentEdit
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
        Public ReadOnly lblMessage As New TextBox With {.ReadOnly = True, .Multiline = True, .ScrollBars = ScrollBars.Vertical, .Dock = DockStyle.Top, .Height = 70, .ForeColor = Color.Maroon}
        Public ReadOnly btnSave As New Button With {.Text = "登録／更新"}
        Public ReadOnly btnDelete As New Button With {.Text = "論理削除"}
        Public ReadOnly btnReset As New Button With {.Text = "入力クリア／編集取消", .Width = 160}
        Public ReadOnly btnReload As New Button With {.Text = "最新情報を再読込", .Width = 145}
        Public ReadOnly btnBack As New Button With {.Text = "検索へ戻る", .Width = 120}
        Public ReadOnly Fields As New Dictionary(Of String, Control)
        Public ReadOnly Errors As New ErrorProvider
        Private Sub InitializeComponent()
            Width = 1100 : Height = 930 : MinimumSize = New Size(850, 650) : AutoScaleMode = AutoScaleMode.Dpi : Font = New Font("Yu Gothic UI", 10)
            Dim labels = {"学籍番号 ※ 15文字（新規だけ）", "氏名 ※ 8文字", "氏名カナ ※ 入力36／保存18文字", "生年月日 ※ 和暦4入力", "性別 ※（未回答可）", "郵便番号 ※ 入力10／保存7桁", "都道府県 ※", "住所1 ※ 45文字", "住所2 45文字", "本人電話 入力20文字", "本人メール 60文字", "入学日 ※ yyyy-MM-dd", "在籍区分 ※", "卒業・退学日（03/04は必須）", "選択補助：年度", "選択補助：学年", "クラス（01/02は必須）", "所属人数・定員（参考）", "緊急連絡先氏名 8文字", "緊急連絡先続柄", "緊急電話 入力20文字", "備考 120文字", "確認・変更理由 60文字", "更新日時・更新者"}
            Dim names = {"StudentNo", "StudentName", "StudentNameKana", "BirthDateInput", "GenderCode", "PostalCode", "PrefectureCode", "AddressLine1", "AddressLine2", "PhoneNumber", "EmailAddress", "AdmissionDate", "EnrollmentStatusCode", "EnrollmentEndDate", "SchoolYear", "GradeCode", "ClassId", "Capacity", "EmergencyContactName", "RelationshipCode", "EmergencyPhoneNumber", "Remarks", "Reason", "UpdatedAt"}
            Dim controls As Control() = {txtStudentNo, txtStudentName, txtStudentNameKana, birthDateInput, cboGender, txtPostalCode, cboPrefecture, txtAddressLine1, txtAddressLine2, txtPhoneNumber, txtEmailAddress, dtpAdmissionDate, cboEnrollmentStatus, dtpEnrollmentEndDate, cboSchoolYear, cboGrade, cboClass, lblCapacity, txtEmergencyContactName, cboRelationship, txtEmergencyPhoneNumber, txtRemarks, txtOperationReason, lblUpdatedAt}
            Dim body As New TableLayoutPanel With {.Dock = DockStyle.Top, .AutoSize = True, .ColumnCount = 2, .RowCount = controls.Length, .Padding = New Padding(8)}
            body.ColumnStyles.Add(New ColumnStyle(SizeType.Absolute, 300)) : body.ColumnStyles.Add(New ColumnStyle(SizeType.Percent, 100))
            For i = 0 To controls.Length - 1
                body.RowStyles.Add(New RowStyle(SizeType.Absolute, If(i = 21, 85, If(i = 22, 65, 43))))
                body.Controls.Add(New Label With {.Text = labels(i), .Dock = DockStyle.Fill, .TextAlign = ContentAlignment.MiddleLeft}, 0, i)
                controls(i).Dock = DockStyle.Fill : controls(i).AccessibleName = labels(i) : body.Controls.Add(controls(i), 1, i) : Fields.Add(names(i), controls(i))
            Next
            For Each combo In {cboGender, cboPrefecture, cboEnrollmentStatus, cboSchoolYear, cboGrade, cboClass, cboRelationship}
                combo.DropDownStyle = ComboBoxStyle.DropDownList
            Next
            Errors.ContainerControl = Me
            Dim scroll As New Panel With {.Dock = DockStyle.Fill, .AutoScroll = True} : scroll.Controls.Add(body)
            Dim actions As New FlowLayoutPanel With {.Dock = DockStyle.Bottom, .Height = 52}
            actions.Controls.AddRange({btnSave, btnReset, btnReload, btnDelete, btnBack})
            Me.Controls.Add(scroll) : Me.Controls.Add(actions) : Me.Controls.Add(lblMessage)
        End Sub
    End Class
End Namespace
