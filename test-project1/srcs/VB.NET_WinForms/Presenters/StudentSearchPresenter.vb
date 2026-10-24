Imports System.Text.Json
Imports System.Globalization
Imports System.Threading
Imports System.Threading.Tasks
Imports System.Windows.Forms
Imports StudentManagement.WinForms.Application
Imports StudentManagement.WinForms.Controls
Imports StudentManagement.WinForms.Forms
Imports Core = StudentManagement.WinForms.Domain

Namespace Presenters
    ' SCR-STU-001 / EV-SRC-001..006: form-instance context, 30-minute sliding expiry.
    Public Class StudentSearchPresenter
        Implements IDisposable
        Private ReadOnly _view As FrmStudentSearch
        Private ReadOnly _service As StudentApplicationService
        Private ReadOnly _lifetime As New CancellationTokenSource()
        Private _lookup As Core.LookupSet
        Public Const SearchSchema As String = "student-search-compact-1"
        Private ReadOnly _windowId As String = Guid.NewGuid().ToString("D")
        Private ReadOnly _stateId As String = Guid.NewGuid().ToString("D")
        Private _contextOwner As String = ""
        Private _contextSession As String = ""
        Private _revision As Long
        Public ReadOnly Property ContextRevision As Long
            Get
                Return _revision
            End Get
        End Property
        Private _applied As Core.SearchCriteria
        Private _lastUsed As DateTimeOffset
        Private _page As Integer = 1
        Private _total As Integer
        Private _requestSequence As Long
        Private _busy As Boolean
        Private _ready As Boolean
        Private _rows As IReadOnlyList(Of Core.StudentRow) = Array.Empty(Of Core.StudentRow)()
        Public Sub New(view As FrmStudentSearch, service As StudentApplicationService)
            _view = view : _service = service
        End Sub
        Public Async Function InitializeAsync() As Task
            Await RunAsync(Async Function()
                               Await _service.AuthenticateAsync(_lifetime.Token)
                               _lookup = Await _service.LookupAsync(_lifetime.Token, includeOccupancy:=False)
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
            If _lookup Is Nothing Then Return
            Fill(_view.cboClass, _lookup.Classes.OrderByDescending(Function(x) x.SchoolYear).ThenBy(Function(x) x.GradeCode).ThenBy(Function(x) x.ClassCode).Select(Function(x) New Choice(x.ClassId.ToString(CultureInfo.InvariantCulture), $"{x.SchoolYear} / {_lookup.Codes.FirstOrDefault(Function(c) c.CategoryId = "GRADE" AndAlso c.CodeValue = x.GradeCode)?.CodeName} / {x.ClassCode} / {x.ClassName}", x.IsActive)), "すべて")
        End Sub
        Public Sub MarkDraftChanged()
            If _applied IsNot Nothing Then _view.lblMessage.Text = "条件を変更しました。検索結果にはまだ反映されていません。"
        End Sub
        Public Function CaptureContext() As String
            Return JsonSerializer.Serialize(New With {.SchemaVersion = SearchSchema, .StateId = _stateId, .WindowId = _windowId, .Owner = _contextOwner, .Session = _contextSession, .Revision = _revision, .ExpiresAt = _lastUsed.AddMinutes(30), .Criteria = _applied})
        End Function
        Public Function RestoreContext(serialized As String, expectedRevision As Long) As Boolean
            Try
                Using document = JsonDocument.Parse(serialized)
                    Dim root = document.RootElement
                    If root.GetProperty("StateId").GetString() <> _stateId OrElse root.GetProperty("WindowId").GetString() <> _windowId OrElse root.GetProperty("Owner").GetString() <> _service.User.Principal OrElse root.GetProperty("Session").GetString() <> _service.User.SessionId OrElse expectedRevision <> _revision OrElse root.GetProperty("Revision").GetInt64() <> _revision Then Throw New InvalidOperationException("E-COM-003 検索状態の所有者・画面・版が一致しません。")
                    If _lastUsed.AddMinutes(30) <= DateTimeOffset.UtcNow OrElse root.GetProperty("ExpiresAt").GetDateTimeOffset() <= DateTimeOffset.UtcNow Then
                        Clear() : _view.lblMessage.Text = "W-SRC-002 検索条件の保持期限が切れました。" : Return False
                    End If
                    Dim schema As JsonElement
                    If Not root.TryGetProperty("SchemaVersion", schema) OrElse schema.GetString() <> SearchSchema Then
                        Clear() : _view.lblMessage.Text = "旧形式の検索状態のため初期化しました。" : Return False
                    End If
                    Dim allowed = New HashSet(Of String) From {"SchemaVersion", "StateId", "WindowId", "Owner", "Session", "Revision", "ExpiresAt", "Criteria"}
                    If root.EnumerateObject().Any(Function(x) Not allowed.Contains(x.Name)) Then Throw New JsonException("Unknown search state field")
                    _applied = JsonSerializer.Deserialize(Of Core.SearchCriteria)(root.GetProperty("Criteria").GetRawText())
                    Return _applied IsNot Nothing
                End Using
            Catch ex As JsonException
                Throw New InvalidOperationException("E-COM-003 検索状態に未知・廃止項目があります。", ex)
            End Try
        End Function
        Private Function Snapshot() As Core.SearchCriteria
            Dim id As Long
            Dim rawClass = Value(_view.cboClass)
            Dim cls As Long? = Nothing
            If rawClass <> "" Then
                If Not Long.TryParse(rawClass, NumberStyles.None, CultureInfo.InvariantCulture, id) OrElse id <= 0 Then Throw New InvalidOperationException("E-COM-003 クラス識別番号が不正です。")
                cls = id
            End If
            Return New Core.SearchCriteria With {.StudentNo = _view.txtStudentNo.Text, .StudentName = _view.txtName.Text, .ClassId = cls, .EnrollmentStatusCodes = _view.clbStatuses.CheckedItems.Cast(Of Choice)().Select(Function(x) x.Value).ToArray()}
        End Function
        Public Async Function SearchAsync() As Task
            Await RunAsync(Async Function()
                               Dim criteria = Snapshot()
                               If Await ExecuteAsync(criteria, 1) Then _applied = criteria : _lastUsed = DateTimeOffset.UtcNow : _contextOwner = _service.User.Principal : _contextSession = _service.User.SessionId : _revision = checkedRevision()
                           End Function)
        End Function
        Private Async Function ExecuteAsync(criteria As Core.SearchCriteria, page As Integer) As Task(Of Boolean)
            If _requestSequence = Long.MaxValue Then Throw New InvalidOperationException("E-COM-003 検索要求連番が上限です。")
            _requestSequence += 1 : Dim generation = _requestSequence
            _view.dgvStudents.DataSource = Nothing
            criteria.Page = page : criteria.PageSize = CInt(_view.cboPageSize.SelectedItem) : criteria.SortKey = Value(_view.cboSortKey) : criteria.SortDirection = Value(_view.cboSortDirection)
            Dim result = Await _service.SearchAsync(criteria, _lifetime.Token)
            If _view.IsDisposed OrElse _lifetime.IsCancellationRequested OrElse generation <> _requestSequence Then Return False
            _page = page : _total = If(result.LimitExceeded, 0, result.Count)
            Dim maxPage = Math.Max(1, CInt(Math.Ceiling(_total / CDbl(criteria.PageSize))))
            If _page > maxPage AndAlso _total > 0 Then Return Await ExecuteAsync(criteria, maxPage)
            _rows = result.Items
            _view.dgvStudents.DataSource = result.Items.Select(Function(x) New With {.StudentNo = x.StudentNo, .NameDisplay = x.StudentName & Environment.NewLine & x.StudentNameKana, .BirthDateWareki = x.BirthDateWareki, .YearGrade = If(x.SchoolYear.HasValue, x.SchoolYear.ToString() & " / " & If(x.GradeName, "不整合"), "－"), .ClassDisplay = If(x.ClassCode, "－") & " / " & If(x.ClassName, "－"), .EnrollmentStatusName = If(x.EnrollmentStatusName, "不整合")}).ToList()
            _view.lblMessage.Text = If(result.LimitExceeded, "W-SRC-001 検索結果が10,000件を超えています。", If(result.Errors.Count > 0, String.Join(Environment.NewLine, result.Errors.Select(Function(x) x.Code & " " & x.Message)), If(result.Count = 0, "I-SRC-001 該当する学生がありません。", "検索が完了しました。")))
            _view.lblCount.Text = If(result.LimitExceeded, "上限超過", If(result.Count = 0, "0件 0–0", $"{result.Count}件 {(_page - 1) * criteria.PageSize + 1}–{Math.Min(_page * criteria.PageSize, result.Count)} / {_page}ページ"))
            _view.lblSearchedAt.Text = result.SearchedAt.ToOffset(TimeSpan.FromHours(9)).ToString("yyyy/MM/dd HH:mm:ss")
            Return Not result.LimitExceeded AndAlso result.Errors.Count = 0 AndAlso result.Outcome <> Core.Outcome.SystemError AndAlso result.Outcome <> Core.Outcome.Forbidden
        End Function
        Public Async Function MoveAsync(page As Integer) As Task
            Await RunAsync(Async Function()
                               If _applied Is Nothing Then Return
                               If Not RestoreContext(CaptureContext(), _revision) Then Return
                               Await ExecuteAsync(_applied, Math.Max(1, page)) : _lastUsed = DateTimeOffset.UtcNow : _revision = checkedRevision()
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
                               If _applied IsNot Nothing AndAlso RestoreContext(CaptureContext(), _revision) Then Await ExecuteAsync(_applied, _page)
                               If notice <> "" Then _view.lblMessage.Text = notice
                           End Function)
        End Function
        Public Sub Clear()
            If _requestSequence = Long.MaxValue Then Throw New InvalidOperationException("E-COM-003 検索要求連番が上限です。")
            _requestSequence += 1
            _applied = Nothing : _total = 0 : _rows = Array.Empty(Of Core.StudentRow)() : _view.dgvStudents.DataSource = Nothing
            _view.txtStudentNo.Clear() : _view.txtName.Clear() : _revision = checkedRevision()
            For Each combo In {_view.cboClass, _view.cboPageSize, _view.cboSortKey, _view.cboSortDirection}
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
            For Each field As Control In New Control() {_view.txtStudentNo, _view.txtName, _view.cboClass, _view.clbStatuses, _view.cboPageSize, _view.cboSortKey, _view.cboSortDirection}
                field.Enabled = Not _busy
            Next
            DirectCast(_view.dgvStudents.Columns("colAction"), DataGridViewButtonColumn).Text = If(_service.CanEdit, "編集", "参照")
            _view.btnSearch.Enabled = Not _busy AndAlso _ready : _view.btnClear.Enabled = Not _busy : _view.btnNew.Enabled = Not _busy AndAlso _service.CanEdit
            _view.btnSort.Enabled = Not _busy AndAlso _applied IsNot Nothing
            _view.btnFirst.Enabled = Not _busy AndAlso _total > 0 AndAlso _page > 1 : _view.btnPrev.Enabled = _view.btnFirst.Enabled
            Dim lastPage = Math.Max(1, CInt(Math.Ceiling(_total / CDbl(CInt(_view.cboPageSize.SelectedItem)))))
            _view.btnNext.Enabled = Not _busy AndAlso _total > 0 AndAlso _page < lastPage : _view.btnLast.Enabled = _view.btnNext.Enabled
        End Sub
        Private Function checkedRevision() As Long
            If _revision = Long.MaxValue Then Throw New InvalidOperationException("E-COM-003 検索状態の版が上限です。")
            Return _revision + 1
        End Function
        Public Sub Dispose() Implements IDisposable.Dispose
            _lifetime.Cancel() : _lifetime.Dispose()
        End Sub
    End Class
End Namespace
