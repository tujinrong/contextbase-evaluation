Imports System.Globalization
Imports System.Threading
Imports System.Threading.Tasks
Imports System.Windows.Forms
Imports StudentManagement.WinForms.Application
Imports StudentManagement.WinForms.Controls
Imports StudentManagement.WinForms.Forms
Imports Core = StudentManagement.Core

Namespace Presenters
    ' SCR-STU-001 / EV-SRC-001..006: form-instance context, 30-minute sliding expiry.
    Public Class StudentSearchPresenter
        Implements IDisposable
        Private ReadOnly _view As FrmStudentSearch
        Private ReadOnly _service As StudentApplicationService
        Private ReadOnly _lifetime As New CancellationTokenSource()
        Private _lookup As Core.LookupSet
        Private _applied As Core.SearchCriteria
        Private _lastUsed As DateTimeOffset
        Private _page As Integer = 1
        Private _total As Integer
        Private _busy As Boolean
        Private _refreshing As Boolean
        Private _ready As Boolean
        Private _rows As IReadOnlyList(Of Core.StudentRow) = Array.Empty(Of Core.StudentRow)()
        Public Sub New(view As FrmStudentSearch, service As StudentApplicationService)
            _view = view : _service = service
        End Sub
        Public Async Function InitializeAsync() As Task
            Await RunAsync(Async Function()
                               Await _service.AuthenticateAsync(_lifetime.Token)
                               _lookup = Await _service.LookupAsync(_lifetime.Token, includeOccupancy:=False)
                               Fill(_view.cboSchoolYear, _lookup.Classes.Select(Function(x) New Choice(x.SchoolYear.ToString(CultureInfo.InvariantCulture), x.SchoolYear.ToString(CultureInfo.InvariantCulture))).GroupBy(Function(x) x.Value).Select(Function(x) x.First()).OrderByDescending(Function(x) x.Value), "すべて")
                               Fill(_view.cboGrade, Codes("GRADE"), "すべて")
                               Fill(_view.cboPrefecture, Codes("PREFECTURE"), "すべて")
                               _ready = _lookup.Codes.Any(Function(x) x.CategoryId = "ENROLLMENT_STATUS" AndAlso x.CodeValue = "01")
                               _view.btnNew.Visible = _service.CanEdit
                               RefreshClasses()
                               _view.lblMessage.Text = If(_ready, "未検索 / " & _service.User.Principal, "E-COM-004 必須コードが不足しています。")
                           End Function)
        End Function
        Private Function Codes(category As String) As IEnumerable(Of Choice)
            Return _lookup.Codes.Where(Function(x) x.CategoryId = category).OrderBy(Function(x) x.DisplayOrder).ThenBy(Function(x) x.CodeValue).Select(Function(x) New Choice(x.CodeValue, x.CodeName))
        End Function
        Private Shared Sub Fill(combo As ComboBox, options As IEnumerable(Of Choice), emptyName As String)
            combo.Items.Clear() : combo.Items.Add(New Choice("", emptyName))
            For Each item In options
                combo.Items.Add(item)
            Next
            combo.SelectedIndex = 0
        End Sub
        Private Shared Function Value(combo As ComboBox) As String
            Return If(TryCast(combo.SelectedItem, Choice)?.Value, "")
        End Function
        Public Sub RefreshClasses()
            If _lookup Is Nothing OrElse _refreshing Then Return
            _refreshing = True
            Try
                If _view.chkUnassignedOnly.Checked Then
                    _view.cboSchoolYear.SelectedIndex = 0 : _view.cboGrade.SelectedIndex = 0 : _view.cboClass.SelectedIndex = 0
                End If
                _view.cboSchoolYear.Enabled = Not _view.chkUnassignedOnly.Checked : _view.cboGrade.Enabled = Not _view.chkUnassignedOnly.Checked : _view.cboClass.Enabled = Not _view.chkUnassignedOnly.Checked
                Dim oldId = Value(_view.cboClass)
                Dim year = Value(_view.cboSchoolYear) : Dim grade = Value(_view.cboGrade)
                Fill(_view.cboClass, _lookup.Classes.Where(Function(x) (year = "" OrElse x.SchoolYear.ToString() = year) AndAlso (grade = "" OrElse x.GradeCode = grade)).Select(Function(x) New Choice(x.ClassId.ToString(), $"{x.SchoolYear} / {x.ClassCode} / {x.ClassName}")), "すべて")
                For i = 0 To _view.cboClass.Items.Count - 1
                    If DirectCast(_view.cboClass.Items(i), Choice).Value = oldId Then _view.cboClass.SelectedIndex = i
                Next
                If oldId <> "" AndAlso Value(_view.cboClass) = "" Then _view.lblMessage.Text = "W-STU-107 選択条件が変わったためクラスの選択を解除しました。"
                If _applied IsNot Nothing Then _view.lblMessage.Text &= " 条件変更は未反映です。"
            Finally
                _refreshing = False
            End Try
        End Sub
        Public Sub SelectClass()
            If _lookup Is Nothing OrElse _refreshing Then Return
            Dim selected = _lookup.Classes.FirstOrDefault(Function(x) x.ClassId.ToString() = Value(_view.cboClass))
            If selected Is Nothing Then Return
            _refreshing = True
            Try
                SelectValue(_view.cboSchoolYear, selected.SchoolYear.ToString()) : SelectValue(_view.cboGrade, selected.GradeCode)
            Finally
                _refreshing = False
            End Try
        End Sub
        Private Shared Sub SelectValue(combo As ComboBox, value As String)
            For i = 0 To combo.Items.Count - 1
                If DirectCast(combo.Items(i), Choice).Value = value Then combo.SelectedIndex = i
            Next
        End Sub
        Private Function Snapshot() As Core.SearchCriteria
            Dim y As Integer : Dim id As Long
            Dim year As Integer? = If(Integer.TryParse(Value(_view.cboSchoolYear), y), CType(y, Integer?), Nothing)
            Dim cls As Long? = If(Long.TryParse(Value(_view.cboClass), id), CType(id, Long?), Nothing)
            Return New Core.SearchCriteria With {.StudentNo = _view.txtStudentNo.Text, .StudentName = _view.txtName.Text, .StudentNameKana = _view.txtKana.Text, .SchoolYear = year, .GradeCode = Value(_view.cboGrade), .ClassId = cls, .UnassignedOnly = _view.chkUnassignedOnly.Checked, .EnrollmentStatusCodes = _view.clbStatuses.CheckedItems.Cast(Of Choice)().Select(Function(x) x.Value).ToArray(), .PrefectureCode = Value(_view.cboPrefecture), .PhoneNumber = _view.txtPhone.Text, .AdmissionFrom = _view.txtAdmissionFrom.Text, .AdmissionTo = _view.txtAdmissionTo.Text}
        End Function
        Public Async Function SearchAsync() As Task
            Await RunAsync(Async Function()
                               Dim criteria = Snapshot()
                               If Await ExecuteAsync(criteria, 1) Then _applied = criteria : _lastUsed = DateTimeOffset.UtcNow
                           End Function)
        End Function
        Private Async Function ExecuteAsync(criteria As Core.SearchCriteria, page As Integer) As Task(Of Boolean)
            _view.dgvStudents.DataSource = Nothing
            criteria.Page = page : criteria.PageSize = CInt(_view.cboPageSize.SelectedItem) : criteria.SortKey = Value(_view.cboSortKey) : criteria.SortDirection = Value(_view.cboSortDirection)
            Dim result = Await _service.SearchAsync(criteria, _lifetime.Token)
            If _view.IsDisposed OrElse _lifetime.IsCancellationRequested Then Return False
            _page = page : _total = If(result.LimitExceeded, 0, result.Count)
            Dim maxPage = Math.Max(1, CInt(Math.Ceiling(_total / CDbl(criteria.PageSize))))
            If _page > maxPage AndAlso _total > 0 Then Return Await ExecuteAsync(criteria, maxPage)
            _rows = result.Items
            _view.dgvStudents.DataSource = result.Items.Select(Function(x) New With {.StudentNo = x.StudentNo, .StudentName = x.StudentName, .StudentNameKana = x.StudentNameKana, .BirthDateWareki = x.BirthDateWareki, .YearGrade = If(x.SchoolYear.HasValue, x.SchoolYear.ToString() & " / " & If(x.GradeName, "不整合"), "－"), .ClassDisplay = If(x.ClassCode, "－") & " / " & If(x.ClassName, "－"), .EnrollmentStatusName = If(x.EnrollmentStatusName, "不整合"), .Address = x.Address, .PhoneNumber = If(x.PhoneNumber, "－"), .UpdatedAt = x.UpdatedAt.ToOffset(TimeSpan.FromHours(9)).ToString("yyyy/MM/dd HH:mm:ss")}).ToList()
            _view.lblMessage.Text = If(result.LimitExceeded, "W-SRC-001 検索結果が10,000件を超えています。", If(result.Errors.Count > 0, String.Join(Environment.NewLine, result.Errors.Select(Function(x) x.Code & " " & x.Message)), If(result.Count = 0, "I-SRC-001 該当する学生がありません。", "検索が完了しました。")))
            _view.lblCount.Text = If(result.LimitExceeded, "上限超過", If(result.Count = 0, "0件 0–0", $"{result.Count}件 {(_page - 1) * criteria.PageSize + 1}–{Math.Min(_page * criteria.PageSize, result.Count)} / {_page}ページ"))
            _view.lblSearchedAt.Text = result.SearchedAt.ToOffset(TimeSpan.FromHours(9)).ToString("yyyy/MM/dd HH:mm:ss")
            Return Not result.LimitExceeded AndAlso result.Errors.Count = 0 AndAlso result.Outcome <> Core.Outcome.SystemError AndAlso result.Outcome <> Core.Outcome.Forbidden
        End Function
        Public Async Function MoveAsync(page As Integer) As Task
            Await RunAsync(Async Function()
                               If _applied Is Nothing Then Return
                               If DateTimeOffset.UtcNow - _lastUsed > TimeSpan.FromMinutes(30) Then
                                   Clear() : _view.lblMessage.Text = "W-SRC-002 検索条件の保持期限が切れました。" : Return
                               End If
                               Await ExecuteAsync(_applied, Math.Max(1, page)) : _lastUsed = DateTimeOffset.UtcNow
                           End Function)
        End Function
        Public Function MoveRelativeAsync(delta As Integer) As Task
            Return MoveAsync(_page + delta)
        End Function
        Public Function MoveLastAsync() As Task
            Return MoveAsync(Math.Max(1, CInt(Math.Ceiling(_total / CDbl(CInt(_view.cboPageSize.SelectedItem))))))
        End Function
        Public Function OpenRowAsync(index As Integer) As Task
            Return If(index >= 0 AndAlso index < _rows.Count, EditAsync(_rows(index).StudentId), Task.CompletedTask)
        End Function
        Public Async Function EditAsync(id As Long?) As Task
            Await RunAsync(Async Function()
                               If id Is Nothing AndAlso Not _service.CanEdit Then Return
                               Dim notice As String
                               Using editor As New FrmStudentEdit(_service, id)
                                   editor.ShowDialog(_view) : notice = editor.ResultNotice
                               End Using
                               If _applied IsNot Nothing Then Await ExecuteAsync(_applied, _page)
                               If notice <> "" Then _view.lblMessage.Text = notice
                           End Function)
        End Function
        Public Sub Clear()
            _applied = Nothing : _total = 0 : _rows = Array.Empty(Of Core.StudentRow)() : _view.dgvStudents.DataSource = Nothing
            _view.txtStudentNo.Clear() : _view.txtName.Clear() : _view.txtKana.Clear() : _view.txtPhone.Clear() : _view.txtAdmissionFrom.Clear() : _view.txtAdmissionTo.Clear()
            _view.chkUnassignedOnly.Checked = False
            For Each combo In {_view.cboSchoolYear, _view.cboGrade, _view.cboClass, _view.cboPrefecture, _view.cboPageSize, _view.cboSortKey, _view.cboSortDirection}
                If combo.Items.Count > 0 Then combo.SelectedIndex = 0
            Next
            For i = 0 To 3
                _view.clbStatuses.SetItemChecked(i, i < 2)
            Next
            _view.lblCount.Text = "未検索" : _view.lblMessage.Text = "未検索" : _view.lblSearchedAt.Text = "" : UpdateButtons()
        End Sub
        Private Async Function RunAsync(operation As Func(Of Task)) As Task
            If _busy Then Return
            _busy = True : UpdateButtons()
            Try
                Await operation()
            Catch ex As OperationCanceledException
            Catch ex As Exception
                If Not _view.IsDisposed Then _view.dgvStudents.DataSource = Nothing : _view.lblMessage.Text = If(TypeOf ex Is InvalidOperationException, ex.Message, "E-COM-004 処理に失敗しました。入力は保持しています。")
            Finally
                _busy = False : If Not _view.IsDisposed Then UpdateButtons()
            End Try
        End Function
        Private Sub UpdateButtons()
            _view.btnSearch.Enabled = Not _busy AndAlso _ready : _view.btnClear.Enabled = Not _busy : _view.btnNew.Enabled = Not _busy AndAlso _service.CanEdit
            _view.btnSort.Enabled = Not _busy AndAlso _applied IsNot Nothing
            _view.btnFirst.Enabled = Not _busy AndAlso _total > 0 AndAlso _page > 1 : _view.btnPrev.Enabled = _view.btnFirst.Enabled
            Dim lastPage = Math.Max(1, CInt(Math.Ceiling(_total / CDbl(CInt(_view.cboPageSize.SelectedItem)))))
            _view.btnNext.Enabled = Not _busy AndAlso _total > 0 AndAlso _page < lastPage : _view.btnLast.Enabled = _view.btnNext.Enabled
        End Sub
        Public Sub Dispose() Implements IDisposable.Dispose
            _lifetime.Cancel() : _lifetime.Dispose()
        End Sub
    End Class
End Namespace
