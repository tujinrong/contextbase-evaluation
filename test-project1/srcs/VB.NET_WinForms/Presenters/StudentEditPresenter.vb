Imports System.Globalization
Imports System.Text.Json
Imports System.Threading
Imports System.Threading.Tasks
Imports System.Windows.Forms
Imports StudentManagement.WinForms.Application
Imports StudentManagement.WinForms.Controls
Imports StudentManagement.WinForms.Forms
Imports Core = StudentManagement.Core

Namespace Presenters
    ' SCR-STU-002: raw draft, DB snapshot and expected version are distinct.
    Public Class StudentEditPresenter
        Implements IDisposable
        Private ReadOnly _view As FrmStudentEdit
        Private ReadOnly _service As StudentApplicationService
        Private ReadOnly _id As Long?
        Private ReadOnly _lifetime As New CancellationTokenSource
        Private _version As Long?
        Private _lookup As Core.LookupSet
        Private _original As Core.StudentDraft
        Private _originalYear As String = ""
        Private _originalGrade As String = ""
        Private _originalUi As String = ""
        Private _busy As Boolean
        Private _refreshing As Boolean
        Private _acceptClose As Boolean
        Public Sub New(view As FrmStudentEdit, service As StudentApplicationService, id As Long?)
            _view = view : _service = service : _id = id
            _view.Text = If(id.HasValue, If(service.CanEdit, "学生登録：編集", "学生登録：参照"), "学生登録：新規")
        End Sub
        Public Async Function InitializeAsync() As Task
            Await RunAsync(Async Function()
                               _lookup = Await _service.LookupAsync(_lifetime.Token)
                               _refreshing = True
                               For Each pair In New Dictionary(Of ComboBox, String) From {{_view.cboGender, "GENDER"}, {_view.cboPrefecture, "PREFECTURE"}, {_view.cboEnrollmentStatus, "ENROLLMENT_STATUS"}, {_view.cboGrade, "GRADE"}, {_view.cboRelationship, "RELATIONSHIP"}}
                                   FillCodes(pair.Key, pair.Value)
                               Next
                               Dim today = DateTimeOffset.UtcNow.ToOffset(TimeSpan.FromHours(9))
                               Dim year = If(today.Month < 4, today.Year - 1, today.Year)
                               _view.cboSchoolYear.Items.Add(New Choice("", "未選択"))
                               For Each y In _lookup.Classes.Select(Function(x) x.SchoolYear).Concat({year}).Distinct().OrderByDescending(Function(x) x)
                                   _view.cboSchoolYear.Items.Add(New Choice(y.ToString(), y.ToString()))
                               Next
                               _refreshing = False
                               Await LoadAsync()
                           End Function)
        End Function
        Private Sub FillCodes(combo As ComboBox, category As String)
            combo.Items.Clear() : combo.Items.Add(New Choice("", "未選択"))
            Dim today = DateOnly.FromDateTime(DateTimeOffset.UtcNow.ToOffset(TimeSpan.FromHours(9)).DateTime)
            For Each code In _lookup.Codes.Where(Function(x) x.CategoryId = category).OrderBy(Function(x) x.DisplayOrder).ThenBy(Function(x) x.CodeValue)
                combo.Items.Add(New Choice(code.CodeValue, code.CodeName, code.IsActive AndAlso code.ValidFrom <= today AndAlso (Not code.ValidTo.HasValue OrElse today <= code.ValidTo.Value)))
            Next
            combo.SelectedIndex = 0
        End Sub
        Private Async Function LoadAsync() As Task
            If _id.HasValue Then
                Dim data = Await _service.GetAsync(_id.Value, _lifetime.Token)
                If data Is Nothing Then Throw New InvalidOperationException("E-STU-103 対象の学生が見つからないか、既に削除されています。")
                _version = data.RowVersion : _original = data.Draft
                _original.BirthDateInput = Core.JapaneseDateService.ToInput(data.BirthDate)
                Dim cls = _lookup.Classes.FirstOrDefault(Function(x) _original.ClassId.HasValue AndAlso x.ClassId = _original.ClassId.Value)
                _originalYear = If(cls Is Nothing, "", cls.SchoolYear.ToString()) : _originalGrade = If(cls Is Nothing, "", cls.GradeCode)
                _view.lblUpdatedAt.Text = data.UpdatedAt.ToOffset(TimeSpan.FromHours(9)).ToString("yyyy/MM/dd HH:mm:ss") & " / " & data.UpdatedBy
            Else
                _original = New Core.StudentDraft()
                Dim today = DateTimeOffset.UtcNow.ToOffset(TimeSpan.FromHours(9))
                _originalYear = If(today.Month < 4, today.Year - 1, today.Year).ToString() : _originalGrade = ""
            End If
            LoadDraft(_original)
            _view.lblMessage.Text = If(_lookup.Classes.Count = 0, "W-STU-108 登録可能なクラスがありません。", "")
        End Function
        Private Shared Function Value(combo As ComboBox) As String
            Return If(TryCast(combo.SelectedItem, Choice)?.Value, "")
        End Function
        Private Shared Sub SelectValue(combo As ComboBox, value As String)
            combo.SelectedIndex = 0
            For i = 0 To combo.Items.Count - 1
                If DirectCast(combo.Items(i), Choice).Value = value Then combo.SelectedIndex = i : Return
            Next
            If value <> "" Then combo.Items.Add(New Choice(value, value & "（不整合：候補なし）", False)) : combo.SelectedIndex = combo.Items.Count - 1
        End Sub
        Private Sub LoadDraft(draft As Core.StudentDraft)
            _refreshing = True
            Try
                For Each prop In GetType(Core.StudentDraft).GetProperties().Where(Function(x) x.PropertyType Is GetType(String))
                    Dim control As Control = Nothing
                    If _view.Fields.TryGetValue(prop.Name, control) Then
                        Dim raw = TryCast(prop.GetValue(draft), String)
                        If TypeOf control Is TextBox Then DirectCast(control, TextBox).Text = If(raw, "")
                        If TypeOf control Is ComboBox Then SelectValue(DirectCast(control, ComboBox), If(raw, ""))
                    End If
                Next
                _view.birthDateInput.LoadRaw(draft.BirthDateInput)
                _view.dtpAdmissionDate.RawText = draft.AdmissionDate : _view.dtpEnrollmentEndDate.RawText = If(draft.EnrollmentEndDate, "")
                SelectValue(_view.cboSchoolYear, _originalYear) : SelectValue(_view.cboGrade, _originalGrade)
                _view.txtOperationReason.Clear()
            Finally
                _refreshing = False
            End Try
            RefreshClasses() : _refreshing = True : SelectValue(_view.cboClass, If(draft.ClassId?.ToString(), "")) : _refreshing = False : SelectClass()
            _view.Errors.Clear() : _originalUi = SnapshotText()
        End Sub
        Public Sub RefreshClasses()
            If _lookup Is Nothing OrElse _refreshing Then Return
            _refreshing = True
            Try
                Dim oldId = Value(_view.cboClass) : Dim year = Value(_view.cboSchoolYear) : Dim grade = Value(_view.cboGrade)
                _view.cboClass.Items.Clear() : _view.cboClass.Items.Add(New Choice("", "未選択"))
                Dim today = DateOnly.FromDateTime(DateTimeOffset.UtcNow.ToOffset(TimeSpan.FromHours(9)).DateTime)
                For Each cls In _lookup.Classes.Where(Function(x) (year = "" OrElse x.SchoolYear.ToString() = year) AndAlso (grade = "" OrElse x.GradeCode = grade))
                    _view.cboClass.Items.Add(New Choice(cls.ClassId.ToString(), $"{cls.SchoolYear} / {cls.ClassCode} / {cls.ClassName}", cls.IsActive AndAlso cls.ValidFrom <= today AndAlso today <= cls.ValidTo))
                Next
                _view.cboClass.SelectedIndex = 0
                For i = 0 To _view.cboClass.Items.Count - 1
                    If DirectCast(_view.cboClass.Items(i), Choice).Value = oldId Then _view.cboClass.SelectedIndex = i
                Next
                If oldId <> "" AndAlso Value(_view.cboClass) = "" Then _view.lblMessage.Text = "W-STU-107 選択条件が変わったためクラスの選択を解除しました。"
            Finally
                _refreshing = False
            End Try
        End Sub
        Public Sub SelectClass()
            If _lookup Is Nothing OrElse _refreshing Then Return
            Dim selected = _lookup.Classes.FirstOrDefault(Function(x) x.ClassId.ToString() = Value(_view.cboClass))
            If selected Is Nothing Then _view.lblCapacity.Text = "クラス未選択" : Return
            _refreshing = True
            Try
                SelectValue(_view.cboSchoolYear, selected.SchoolYear.ToString()) : SelectValue(_view.cboGrade, selected.GradeCode)
                _view.lblCapacity.Text = $"所属人数 {selected.Occupied} / 定員 {If(selected.Capacity.HasValue, selected.Capacity.ToString(), "制限なし")}（参考値）"
            Finally
                _refreshing = False
            End Try
        End Sub
        Public Sub StatusChanged()
            If Not _refreshing AndAlso (Value(_view.cboEnrollmentStatus) = "01" OrElse Value(_view.cboEnrollmentStatus) = "02") Then _view.dtpEnrollmentEndDate.RawText = ""
        End Sub
        Private Function ReadDraft() As Core.StudentDraft
            Dim idValue As Long
            Dim classId As Long? = If(Long.TryParse(Value(_view.cboClass), NumberStyles.None, CultureInfo.InvariantCulture, idValue), CType(idValue, Long?), Nothing)
            Return New Core.StudentDraft With {.StudentNo = _view.txtStudentNo.Text, .StudentName = _view.txtStudentName.Text, .StudentNameKana = _view.txtStudentNameKana.Text, .BirthDateInput = _view.birthDateInput.ReadRaw(), .GenderCode = Value(_view.cboGender), .PostalCode = _view.txtPostalCode.Text, .PrefectureCode = Value(_view.cboPrefecture), .AddressLine1 = _view.txtAddressLine1.Text, .AddressLine2 = _view.txtAddressLine2.Text, .PhoneNumber = _view.txtPhoneNumber.Text, .EmailAddress = _view.txtEmailAddress.Text, .AdmissionDate = _view.dtpAdmissionDate.RawText, .EnrollmentStatusCode = Value(_view.cboEnrollmentStatus), .EnrollmentEndDate = _view.dtpEnrollmentEndDate.RawText, .ClassId = classId, .EmergencyContactName = _view.txtEmergencyContactName.Text, .RelationshipCode = Value(_view.cboRelationship), .EmergencyPhoneNumber = _view.txtEmergencyPhoneNumber.Text, .Remarks = _view.txtRemarks.Text}
        End Function
        Private Function SnapshotText() As String
            Return JsonSerializer.Serialize(ReadDraft()) & ":" & Value(_view.cboSchoolYear) & ":" & Value(_view.cboGrade) & ":" & _view.txtOperationReason.Text
        End Function
        Public Async Function SaveAsync() As Task
            If Not _service.CanEdit Then Return
            Await RunAsync(Async Function()
                               _view.Errors.Clear()
                               Dim yearValue As Integer
                               Dim year As Integer? = If(Integer.TryParse(Value(_view.cboSchoolYear), yearValue), CType(yearValue, Integer?), Nothing)
                               Dim command As New Core.SaveRequest(ReadDraft(), _id, _version, year, Value(_view.cboGrade), Nothing, _view.txtOperationReason.Text)
                               Dim result = Await _service.SaveAsync(command, _lifetime.Token)
                               If result.Outcome = Core.Outcome.ConfirmationRequired Then
                                   Dim candidates = If(result.Candidates, Array.Empty(Of Core.StudentRow)())
                                   Dim content = $"同一人物候補 {result.CandidateCount}件（最大20件表示）。別人であることを確認してください。" & Environment.NewLine & String.Join(Environment.NewLine, candidates.Select(Function(x) $"{x.StudentNo}  {x.StudentName}  {x.BirthDateWareki}  {If(x.ClassName, "－")}"))
                                   Using dialog As New ConfirmationDialog(content, "別人と確認して続行")
                                       If dialog.ShowDialog(_view) <> DialogResult.OK Then Return
                                       _view.txtOperationReason.Text = dialog.Reason
                                       command = New Core.SaveRequest(ReadDraft(), _id, _version, year, Value(_view.cboGrade), result.ConfirmationToken, dialog.Reason)
                                       result = Await _service.SaveAsync(command, _lifetime.Token)
                                   End Using
                               End If
                               DisplayResult(result)
                           End Function)
        End Function
        Public Async Function DeleteAsync() As Task
            If Not _id.HasValue OrElse Not _version.HasValue OrElse Not _service.CanDelete Then Return
            Await RunAsync(Async Function()
                               Using dialog As New ConfirmationDialog("W-STU-105 この学生を論理削除します。削除後は通常検索できません。編集中の一般項目は保存しません。", "論理削除する")
                                   If dialog.ShowDialog(_view) <> DialogResult.OK Then Return
                                   DisplayResult(Await _service.DeleteAsync(_id.Value, _version.Value, dialog.Reason, _lifetime.Token))
                               End Using
                           End Function)
        End Function
        Private Sub DisplayResult(result As Core.SaveResult)
            Dim notice = If(result.Errors.Count > 0, String.Join(Environment.NewLine, result.Errors.Select(Function(x) x.Code & " " & x.Message)), If(result.Outcome = Core.Outcome.Saved, "保存しました。", If(result.Outcome = Core.Outcome.NoChange, "I-STU-004 変更内容がありません。", If(result.Outcome = Core.Outcome.Unknown, "E-COM-004 保存結果が不明です。再保存の前に検索で確認してください。", result.Outcome.ToString()))))
            _view.lblMessage.Text = notice & If(result.RequestId Is Nothing, "", " 受付番号：" & result.RequestId)
            Dim first As Control = Nothing
            For Each issue In result.Errors
                Dim control As Control = Nothing
                If _view.Fields.TryGetValue(issue.Field, control) Then _view.Errors.SetError(control, issue.Message) : If first Is Nothing Then first = control
            Next
            first?.Focus()
            If result.Outcome = Core.Outcome.Saved Then
                _view.ResultNotice = notice : _acceptClose = True : _view.Close()
            End If
        End Sub
        Public Sub Reset()
            If _busy OrElse _original Is Nothing Then Return
            If MessageBox.Show("入力内容を取り消しますか。", "確認", MessageBoxButtons.OKCancel, MessageBoxIcon.Question, MessageBoxDefaultButton.Button2) = DialogResult.OK Then LoadDraft(_original)
        End Sub
        Public Async Function ReloadAsync() As Task
            If Not _id.HasValue OrElse _busy Then Return
            If MessageBox.Show("最新情報を再読み込みしますか。入力中の変更は破棄されます。", "確認", MessageBoxButtons.OKCancel, MessageBoxIcon.Question, MessageBoxDefaultButton.Button2) = DialogResult.OK Then Await RunAsync(Function() LoadAsync())
        End Function
        Public Function CanClose() As Boolean
            If _acceptClose Then Return True
            If _busy Then Return False
            Return _originalUi = "" OrElse SnapshotText() = _originalUi OrElse MessageBox.Show("保存していない変更を破棄しますか。", "確認", MessageBoxButtons.OKCancel, MessageBoxIcon.Question, MessageBoxDefaultButton.Button2) = DialogResult.OK
        End Function
        Private Async Function RunAsync(operation As Func(Of Task)) As Task
            If _busy Then Return
            _busy = True : SetEnabled()
            Try
                Await operation()
            Catch ex As OperationCanceledException
            Catch ex As Exception
                If Not _view.IsDisposed Then _view.lblMessage.Text = If(TypeOf ex Is InvalidOperationException, ex.Message, "E-COM-004 処理に失敗しました。入力を保持しています。")
            Finally
                _busy = False : If Not _view.IsDisposed Then SetEnabled()
            End Try
        End Function
        Private Sub SetEnabled()
            For Each control In _view.Fields.Values
                If TypeOf control IsNot Label Then control.Enabled = Not _busy AndAlso _service.CanEdit
            Next
            _view.txtStudentNo.Enabled = Not _busy AndAlso _service.CanEdit AndAlso Not _id.HasValue
            _view.btnSave.Enabled = Not _busy AndAlso _service.CanEdit : _view.btnDelete.Enabled = Not _busy AndAlso _service.CanDelete AndAlso _id.HasValue
            _view.btnReset.Enabled = Not _busy : _view.btnReload.Enabled = Not _busy AndAlso _id.HasValue : _view.btnBack.Enabled = Not _busy
        End Sub
        Public Sub Dispose() Implements IDisposable.Dispose
            _lifetime.Cancel() : _lifetime.Dispose()
        End Sub
    End Class
End Namespace
