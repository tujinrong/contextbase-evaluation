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
        Public ReadOnly txtRemarks As New TextBox With {.MaxLength = 240, .Multiline = True, .AcceptsReturn=True, .ScrollBars = ScrollBars.Vertical, .Height = 75}
        Public ReadOnly txtOperationReason As New TextBox With {.MaxLength = 120, .Multiline = True, .AcceptsReturn=True, .ScrollBars=ScrollBars.Vertical, .Height = 55}
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
        Private ReadOnly _editSurface As New Panel With {.MinimumSize = New Size(1180, 610), .Size = New Size(1180, 610)}
        Private Sub InitializeComponent()
            ClientSize = New Size(1180, 610) : MinimumSize = New Size(640, 420)
            AutoScaleDimensions = New SizeF(96.0F, 96.0F) : AutoScaleMode = AutoScaleMode.Dpi : Font = New Font("Segoe UI", 9.0F)
            BackColor = SystemColors.Control
            lblMessage.Height = 24 : lblMessage.Visible = False : lblMessage.BackColor = SystemColors.Control
            Dim basic As New GroupBox With {.Text = "基本情報", .Bounds = New Rectangle(8,34,1164,104), .Anchor = AnchorStyles.Top Or AnchorStyles.Left Or AnchorStyles.Right}
            Dim middle As New TableLayoutPanel With {.Bounds = New Rectangle(8,146,1164,194), .ColumnCount = 3, .RowCount = 1, .Margin = Padding.Empty, .Padding = Padding.Empty, .Anchor = AnchorStyles.Top Or AnchorStyles.Left Or AnchorStyles.Right}
            middle.ColumnStyles.Add(New ColumnStyle(SizeType.Percent,100)) : middle.ColumnStyles.Add(New ColumnStyle(SizeType.Absolute,8)) : middle.ColumnStyles.Add(New ColumnStyle(SizeType.Absolute,400))
            Dim address As New GroupBox With {.Text="住所・本人連絡先", .Dock=DockStyle.Fill, .Margin=Padding.Empty}
            Dim enrollment As New GroupBox With {.Text="在籍・所属", .Dock=DockStyle.Fill, .Margin=Padding.Empty}
            middle.Controls.Add(address,0,0) : middle.Controls.Add(enrollment,2,0)
            Dim other As New GroupBox With {.Text="緊急連絡先・備考・理由", .Bounds=New Rectangle(8,348,1164,164), .Anchor=AnchorStyles.Top Or AnchorStyles.Bottom Or AnchorStyles.Left Or AnchorStyles.Right}
            _editSurface.Controls.AddRange({basic,middle,other})
            Put(_editSurface,"StudentId",lblStudentId,"学生管理番号",20,4,80,104,144)
            Note(_editSurface,"必須：*　条件付き：※　学籍番号は登録後変更不可",772,6,400)
            Put(basic,"StudentNo",txtStudentNo,"学籍番号 *",12,20,80,96,144)
            Put(basic,"StudentName",txtStudentName,"氏名 *",264,20,44,312,128)
            Put(basic,"StudentNameKana",txtStudentNameKana,"氏名カナ *",464,20,64,532,260)
            Put(basic,"BirthDateInput",birthDateInput,"生年月日 *",12,58,80,96,300)
            Put(basic,"GenderCode",cboGender,"性別 *",464,58,64,532,104)
            Note(basic,"生年月日は和暦、その他の日付は西暦",816,60,330)
            Put(address,"PostalCode",txtPostalCode,"郵便番号 *",12,20,80,96,104)
            Put(address,"PrefectureCode",cboPrefecture,"都道府県 *",228,20,72,304,128)
            Put(address,"AddressLine1",txtAddressLine1,"住所1 *",12,52,80,96,640,True)
            Put(address,"AddressLine2",txtAddressLine2,"住所2",12,84,80,96,640,True)
            Put(address,"PhoneNumber",txtPhoneNumber,"本人電話 ※",12,116,80,96,176)
            Note(address,"※本人電話・メール・緊急電話のいずれか1つ以上",296,116,440)
            Put(address,"EmailAddress",txtEmailAddress,"メール ※",12,148,80,96,640,True)
            Put(enrollment,"AdmissionDate",dtpAdmissionDate,"入学日 *",12,20,100,116,116)
            Put(enrollment,"EnrollmentStatusCode",cboEnrollmentStatus,"在籍 *",244,20,36,284,96)
            Put(enrollment,"EnrollmentEndDate",dtpEnrollmentEndDate,"卒業・退学日 ※",12,52,100,116,116)
            Put(enrollment,"SchoolYear",cboSchoolYear,"年度",244,52,36,284,96)
            Put(enrollment,"GradeCode",cboGrade,"学年",12,84,100,116,116)
            Put(enrollment,"ClassId",cboClass,"クラス ※",12,116,100,116,264)
            Put(enrollment,"Capacity",lblCapacity,"所属人数・定員",12,148,100,116,264)
            Put(other,"EmergencyContactName",txtEmergencyContactName,"緊急氏名 ※",12,20,80,96,128)
            Put(other,"RelationshipCode",cboRelationship,"続柄 ※",248,20,44,296,96)
            Put(other,"EmergencyPhoneNumber",txtEmergencyPhoneNumber,"緊急電話 ※",416,20,68,488,176)
            Note(other,"※緊急氏名・続柄・電話は全部空、または全部入力",696,22,450)
            Put(other,"Remarks",txtRemarks,"備考",12,52,80,96,640,True,64)
            Put(other,"Reason",txtOperationReason,"確認・変更理由 ※",776,52,100,880,264,False,64)
            txtRemarks.Anchor = txtRemarks.Anchor Or AnchorStyles.Bottom
            txtOperationReason.Anchor = AnchorStyles.Top Or AnchorStyles.Bottom Or AnchorStyles.Right
            Dim reasonLabel=other.Controls.OfType(Of Label)().Last(Function(x) x.Text="確認・変更理由 ※") : reasonLabel.Anchor=AnchorStyles.Top Or AnchorStyles.Right
            Note(other,"備考：120文字以内・改行可。カーソル移動・スクロールで全文を確認。",96,130,640,AnchorStyles.Bottom Or AnchorStyles.Left)
            Note(other,"理由：必要な操作で60文字以内",880,130,264,AnchorStyles.Bottom Or AnchorStyles.Right)
            lblUpdatedAt.AutoSize=False : lblUpdatedAt.Bounds=New Rectangle(20,520,1132,20) : lblUpdatedAt.Anchor=AnchorStyles.Bottom Or AnchorStyles.Left Or AnchorStyles.Right
            _editSurface.Controls.Add(lblUpdatedAt) : Fields.Add("UpdatedAt",lblUpdatedAt)
            btnSave.Text="登録／更新" : btnReset.Text="編集取消" : btnReload.Text="最新情報を再読込"
            Dim actions={btnSave,btnReset,btnReload,btnBack,btnDelete}
            Dim xs={20,116,220,376,1056} : Dim widths={88,96,148,112,96}
            For i=0 To actions.Length-1
                actions(i).Bounds=New Rectangle(xs(i),548,widths(i),27) : actions(i).TabIndex=24+i
                actions(i).Anchor=AnchorStyles.Bottom Or If(i=4,AnchorStyles.Right,AnchorStyles.Left)
                _editSurface.Controls.Add(actions(i))
            Next
            Note(_editSurface,"入力可能。未保存の変更は［登録／更新］で保存してください。",8,582,1164,AnchorStyles.Bottom Or AnchorStyles.Left Or AnchorStyles.Right)
            For Each combo In {cboGender,cboPrefecture,cboEnrollmentStatus,cboSchoolYear,cboGrade,cboClass,cboRelationship}
                combo.DropDownStyle=ComboBoxStyle.DropDownList : combo.DropDownWidth=Math.Max(combo.Width,320)
            Next
            Errors.ContainerControl=Me
            _studentScroll.Controls.Add(_editSurface) : Controls.Add(_studentScroll) : Controls.Add(lblMessage)
            AddHandler _studentScroll.ClientSizeChanged,Sub() _editSurface.Size=New Size(Math.Max(_editSurface.MinimumSize.Width,_studentScroll.ClientSize.Width),Math.Max(_editSurface.MinimumSize.Height,_studentScroll.ClientSize.Height))
            AddHandler lblMessage.TextChanged,Sub() LayoutMessage()
            AddHandler ClientSizeChanged,Sub() LayoutMessage()
        End Sub
        Private Sub LayoutMessage()
            lblMessage.Visible=lblMessage.TextLength>0
            If lblMessage.Visible Then lblMessage.Height=Math.Min(CInt(160*DeviceDpi/96),Math.Max(CInt(24*DeviceDpi/96),TextRenderer.MeasureText(lblMessage.Text,lblMessage.Font,New Size(Math.Max(100,ClientSize.Width-24),Integer.MaxValue),TextFormatFlags.WordBreak).Height+10))
        End Sub
        Private Sub Put(parent As Control,key As String,field As Control,label As String,lx As Integer,y As Integer,lw As Integer,x As Integer,w As Integer,Optional stretch As Boolean=False,Optional h As Integer=24)
            Dim caption As New Label With {.Text=label,.Bounds=New Rectangle(lx,y,lw,24),.TextAlign=ContentAlignment.MiddleLeft}
            field.AutoSize=False : field.Dock=DockStyle.None : field.Bounds=New Rectangle(x,y,w,h) : field.TabIndex=Fields.Count : field.AccessibleName=label
            If stretch Then field.Anchor=AnchorStyles.Top Or AnchorStyles.Left Or AnchorStyles.Right
            parent.Controls.Add(caption) : parent.Controls.Add(field) : Fields.Add(key,field)
        End Sub
        Private Sub Note(parent As Control,text As String,x As Integer,y As Integer,w As Integer,Optional anchor As AnchorStyles=AnchorStyles.Top Or AnchorStyles.Left)
            parent.Controls.Add(New Label With {.Text=text,.Bounds=New Rectangle(x,y,w,20),.Anchor=anchor})
        End Sub
    End Class
End Namespace
