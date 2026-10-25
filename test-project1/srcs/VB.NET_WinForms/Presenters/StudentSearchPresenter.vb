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
    ' SCR-STU-001 / student-search-scroll-2: authoritative form state, no query paging.
    Public Class StudentSearchPresenter
        Implements IDisposable
        Private ReadOnly _view As FrmStudentSearch
        Private ReadOnly _service As StudentApplicationService
        Private ReadOnly _lifetime As New CancellationTokenSource()
        Private _lookup As Core.LookupSet
        Public Event RevisionPublished(revision As Long)
        Public Const SearchSchema As String = "student-search-scroll-2"
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
        Private _draft As New Core.SearchDraft()
        Private _applied As Core.SearchCriteria
        Private _appliedRaw As Core.SearchDraft
        Private _sortKey As String = "studentNo"
        Private _sortDirection As String = "asc"
        Private _selectedId As Long?
        Private _scroll As Integer
        Private _lastUsed As DateTimeOffset
        Private _requestSequence As Long
        Private _busy As Boolean
        Private _ready As Boolean
        Private _binding As Boolean
        Private _rows As IReadOnlyList(Of Core.StudentRow) = Array.Empty(Of Core.StudentRow)()
        Public Sub New(view As FrmStudentSearch, service As StudentApplicationService)
            _view = view : _service = service
        End Sub
        Private Function Alive() As Boolean
            Return Not _view.IsDisposed AndAlso Not _lifetime.IsCancellationRequested
        End Function
        Public Async Function InitializeAsync() As Task
            Await RunAsync(Async Function()
                               Await _service.AuthenticateAsync(_lifetime.Token)
                               If Not Alive() Then Return
                               _lookup = Await _service.LookupAsync(_lifetime.Token, includeOccupancy:=False)
                               If Not Alive() Then Return
                               _ready = {"01", "02", "03", "04"}.All(Function(value) _lookup.Codes.Any(Function(x) x.CategoryId = "ENROLLMENT_STATUS" AndAlso x.CodeValue = value))
                               _contextOwner = _service.User.Principal : _contextSession = _service.User.SessionId
                               _view.btnNew.Visible = _service.CanEdit
                               RefreshClasses() : ResetState()
                               _view.lblMessage.Text = If(_ready, "未検索 / " & _service.User.Principal, "E-COM-004 必須コードが不足しています。")
                           End Function)
        End Function
        Private Shared Function Value(combo As ComboBox) As String
            Return If(TryCast(combo.SelectedItem, Choice)?.Value, "")
        End Function
        Public Sub RefreshClasses()
            If _lookup Is Nothing Then Return
            _view.cboClass.Items.Clear() : _view.cboClass.Items.Add(New Choice("", "すべて"))
            For Each cls In _lookup.Classes.OrderByDescending(Function(x) x.SchoolYear).ThenBy(Function(x) x.GradeCode).ThenBy(Function(x) x.ClassCode).ThenBy(Function(x) x.ClassId)
                Dim grade = _lookup.Codes.FirstOrDefault(Function(x) x.CategoryId = "GRADE" AndAlso x.CodeValue = cls.GradeCode)?.CodeName
                _view.cboClass.Items.Add(New Choice(cls.ClassId.ToString(CultureInfo.InvariantCulture), $"{cls.SchoolYear} / {If(grade, "不整合")} / {cls.ClassCode} / {cls.ClassName}", cls.IsActive))
            Next
            _view.cboClass.SelectedIndex = 0
        End Sub
        Private Function Snapshot() As Core.SearchDraft
            Return New Core.SearchDraft With {.StudentNo = _view.txtStudentNo.Text, .StudentName = _view.txtName.Text, .ClassId = Value(_view.cboClass), .EnrollmentStatusCodes = _view.StatusChecks.Where(Function(x) x.Checked).Select(Function(x) CStr(x.Tag)).ToArray()}
        End Function
        Private Shared Function Clone(Of T)(value As T) As T
            Return JsonSerializer.Deserialize(Of T)(JsonSerializer.Serialize(value))
        End Function
        Public Sub MarkDraftChanged()
            If _binding OrElse _busy OrElse Not _ready Then Return
            _draft = Snapshot() : Touch()
            If _applied IsNot Nothing Then _view.lblMessage.Text = If(Pending(), "条件を変更しました。検索結果にはまだ反映されていません。", "検索条件は最終実行条件と同じです。")
        End Sub
        Private Function Pending() As Boolean
            Return _appliedRaw IsNot Nothing AndAlso JsonSerializer.Serialize(_draft) <> JsonSerializer.Serialize(_appliedRaw)
        End Function
        Public Sub RememberPosition()
            If _binding OrElse _applied Is Nothing Then Return
            Dim selected = SelectedRowId()
            Dim top = If(_view.dgvStudents.RowCount > 0, Math.Max(0, _view.dgvStudents.FirstDisplayedScrollingRowIndex), 0)
            If Not Nullable.Equals(selected, _selectedId) OrElse top <> _scroll Then _selectedId = selected : _scroll = top : Touch()
        End Sub
        Private Function SelectedRowId() As Long?
            Dim row = TryCast(_view.dgvStudents.CurrentRow?.DataBoundItem, ListRow)
            Return If(row Is Nothing, CType(Nothing, Long?), row.StudentId)
        End Function
        Public Function CaptureContext(Optional capturePosition As Boolean=True) As String
            _draft = Snapshot()
            If capturePosition Then RememberPosition()
            Return JsonSerializer.Serialize(New With {.SchemaVersion = SearchSchema, .StateId = _stateId, .WindowId = _windowId, .Owner = _contextOwner, .Session = _contextSession, .Revision = _revision, .ExpiresAt = _lastUsed.AddMinutes(30), .Criteria = _applied, .Draft = _draft, .SortKey = _sortKey, .SortDirection = _sortDirection, .SelectedStudentId = _selectedId, .FirstDisplayedScrollingRowIndex = _scroll})
        End Function
        Private Shared Sub Keys(value As JsonElement, names As String())
            If value.ValueKind <> JsonValueKind.Object Then Throw New JsonException("Object required")
            Dim actual = value.EnumerateObject().Select(Function(x) x.Name).ToArray()
            If actual.Distinct(StringComparer.Ordinal).Count() <> actual.Length OrElse actual.Any(Function(x) Not names.Contains(x, StringComparer.Ordinal)) Then Throw New JsonException("Unknown or duplicate state member")
        End Sub
        Public Function RestoreContext(serialized As String, expectedRevision As Long) As Boolean
            Try
                Using document = JsonDocument.Parse(serialized)
                    Dim root = document.RootElement
                    ' Check current authority before expiry/format resets. A foreign or stale caller cannot clear state.
                    If root.GetProperty("StateId").GetString() <> _stateId OrElse root.GetProperty("WindowId").GetString() <> _windowId OrElse root.GetProperty("Owner").GetString() <> _service.User.Principal OrElse root.GetProperty("Session").GetString() <> _service.User.SessionId OrElse expectedRevision <> _revision OrElse root.GetProperty("Revision").GetInt64() <> _revision Then Throw New InvalidOperationException("E-COM-003 検索状態の所有者・画面・版が一致しません。")
                    If _lastUsed.AddMinutes(30) <= DateTimeOffset.UtcNow OrElse root.GetProperty("ExpiresAt").GetDateTimeOffset() <= DateTimeOffset.UtcNow Then
                        ResetState() : _view.lblMessage.Text = "W-SRC-002 検索条件の保持期限が切れました。" : Return False
                    End If
                    Dim schema As JsonElement
                    If Not root.TryGetProperty("SchemaVersion", schema) OrElse schema.ValueKind <> JsonValueKind.String OrElse schema.GetString() <> SearchSchema Then
                        ResetState() : _view.lblMessage.Text = "旧形式の検索状態のため初期化しました。" : Return False
                    End If
                    Keys(root, {"SchemaVersion", "StateId", "WindowId", "Owner", "Session", "Revision", "ExpiresAt", "Criteria", "Draft", "SortKey", "SortDirection", "SelectedStudentId", "FirstDisplayedScrollingRowIndex"})
                    Dim criteria As Core.SearchCriteria = Nothing
                    If root.GetProperty("Criteria").ValueKind <> JsonValueKind.Null Then
                        Keys(root.GetProperty("Criteria"), {"StudentNo", "StudentName", "ClassId", "EnrollmentStatusCodes"})
                        criteria = root.GetProperty("Criteria").Deserialize(Of Core.SearchCriteria)()
                    End If
                    Keys(root.GetProperty("Draft"), {"StudentNo", "StudentName", "ClassId", "EnrollmentStatusCodes"})
                    Dim raw = root.GetProperty("Draft").Deserialize(Of Core.SearchDraft)()
                    If JsonSerializer.Serialize(criteria) <> JsonSerializer.Serialize(_applied) OrElse JsonSerializer.Serialize(raw) <> JsonSerializer.Serialize(_draft) OrElse root.GetProperty("SortKey").GetString() <> _sortKey OrElse root.GetProperty("SortDirection").GetString() <> _sortDirection Then Throw New JsonException("State does not match the current authoritative revision")
                    Dim suppliedSelected = root.GetProperty("SelectedStudentId")
                    Dim selected As Long? = If(suppliedSelected.ValueKind = JsonValueKind.Null, CType(Nothing, Long?), suppliedSelected.GetInt64())
                    If Not Nullable.Equals(selected, _selectedId) OrElse root.GetProperty("FirstDisplayedScrollingRowIndex").GetInt32() <> _scroll Then Throw New JsonException("Display position does not match current state")
                    Return _applied IsNot Nothing
                End Using
            Catch ex As Exception When TypeOf ex Is JsonException OrElse TypeOf ex Is KeyNotFoundException OrElse TypeOf ex Is FormatException OrElse (TypeOf ex Is InvalidOperationException AndAlso Not ex.Message.StartsWith("E-COM-003", StringComparison.Ordinal))
                Throw New InvalidOperationException("E-COM-003 検索状態に未知・廃止項目または不正な値があります。", ex)
            End Try
        End Function
        Public Async Function SearchAsync(expectedRevision As Long) As Task
            Await RunAsync(Async Function()
                               If Not ValidateCurrent(expectedRevision) Then Return
                               _draft = Snapshot()
                               Dim raw = Clone(_draft)
                               Dim criteria = raw.Normalize()
                               Await ExecuteAsync(criteria, raw, Value(_view.cboSortKey), Value(_view.cboSortDirection), False)
                           End Function)
        End Function
        Private Function ValidateCurrent(expectedRevision As Long) As Boolean
            If _revision = 0 Then Throw New InvalidOperationException("E-COM-003 検索状態が未発行です。")
            If expectedRevision<>_revision Then Throw New InvalidOperationException("E-COM-003 検索状態の版が一致しません。再取得して確認してください。")
            Dim wasSearched = _applied IsNot Nothing
            Dim before = _revision
            Dim valid = RestoreContext(CaptureContext(False), expectedRevision)
            Return valid OrElse (Not wasSearched AndAlso _applied Is Nothing AndAlso _revision = before)
        End Function
        Public Async Function SortAsync(expectedRevision As Long) As Task
            Await RunAsync(Async Function()
                               If Not ValidateCurrent(expectedRevision) OrElse _applied Is Nothing Then Return
                               RememberPosition()
                               Await ExecuteAsync(Clone(_applied), Clone(_appliedRaw), Value(_view.cboSortKey), Value(_view.cboSortDirection), False)
                           End Function)
        End Function
        Public Async Function RefreshAsync(expectedRevision As Long) As Task
            Await RunAsync(Async Function()
                               If Not ValidateCurrent(expectedRevision) OrElse _applied Is Nothing Then Return
                               Await ExecuteAsync(Clone(_applied), Clone(_appliedRaw), _sortKey, _sortDirection, True)
                           End Function)
        End Function
        Private Async Function ExecuteAsync(criteria As Core.SearchCriteria, raw As Core.SearchDraft, sort As String, direction As String, restoreScroll As Boolean) As Task
            If Not {"studentNo", "name", "admissionDate", "updatedAt"}.Contains(sort) OrElse Not {"asc", "desc"}.Contains(direction) Then Throw New InvalidOperationException("E-COM-003 並び順が不正です。")
            Dim selected = _selectedId : Dim top = If(restoreScroll, _scroll, 0)
            If _requestSequence = Long.MaxValue Then Throw New InvalidOperationException("E-COM-003 検索要求連番が上限です。")
            _requestSequence += 1 : Dim generation = _requestSequence
            ClearRows()
            Dim result = Await _service.SearchAsync(Clone(criteria), sort, direction, _lifetime.Token)
            If Not Alive() OrElse generation <> _requestSequence Then Return
            If result.Status = Core.SearchStatus.Success OrElse result.Status = Core.SearchStatus.LimitExceeded Then
                _applied = Clone(criteria) : _appliedRaw = Clone(raw) : _sortKey = sort : _sortDirection = direction : Touch()
            End If
            _rows = result.Items
            _binding = True
            Try
                _view.dgvStudents.DataSource = result.Items.Select(Function(x) New ListRow With {.StudentId = x.StudentId, .StudentNo = x.StudentNo, .NameDisplay = x.StudentName & Environment.NewLine & x.StudentNameKana, .BirthDateWareki = x.BirthDateWareki, .YearGrade = If(x.SchoolYear.HasValue, x.SchoolYear.ToString() & Environment.NewLine & If(x.GradeName, "不整合"), "－"), .ClassDisplay = If(x.ClassCode, "－") & " / " & If(x.ClassName, "－"), .EnrollmentStatusName = If(x.EnrollmentStatusName, "不整合")}).ToList()
                _view.dgvStudents.ClearSelection() : _view.dgvStudents.CurrentCell = Nothing
                _selectedId = Nothing
                For Each gridRow As DataGridViewRow In _view.dgvStudents.Rows
                    If Nullable.Equals(DirectCast(gridRow.DataBoundItem, ListRow).StudentId, selected) Then gridRow.Selected = True : _view.dgvStudents.CurrentCell = gridRow.Cells(0) : _selectedId = selected : Exit For
                Next
                _scroll = If(_rows.Count = 0, 0, Math.Clamp(top, 0, _rows.Count - 1))
                If _view.dgvStudents.RowCount > 0 AndAlso _view.dgvStudents.IsHandleCreated Then _view.dgvStudents.FirstDisplayedScrollingRowIndex = _scroll
            Finally
                _binding = False
            End Try
            _view.lblCount.Text = If(result.LimitExceeded, "上限超過", If(result.Count.HasValue, result.Count.Value.ToString(CultureInfo.InvariantCulture) & "件（全件一括表示・一覧内スクロール）", "検索失敗"))
            _view.lblSearchedAt.Text = If(result.SearchedAt.HasValue, "検索日時：" & result.SearchedAt.Value.ToOffset(TimeSpan.FromHours(9)).ToString("yyyy/MM/dd HH:mm:ss") & "　最終条件：学籍番号=" & If(raw.StudentNo,"*") & " 氏名=" & If(raw.StudentName,"*") & " クラス=" & If(raw.ClassId,"*") & " 在籍=" & String.Join("/",raw.EnrollmentStatusCodes), "")
            _view.lblMessage.Text = If(result.LimitExceeded, "W-SRC-001 検索結果が10,000件を超えています。条件を追加してください。", If(result.Errors.Count > 0, String.Join(Environment.NewLine, result.Errors.Select(Function(x) x.Code & " " & x.Message)), If(result.Count.GetValueOrDefault() = 0, "I-SRC-001 該当する学生がありません。", "検索が完了しました。")))
            If Pending() Then _view.lblMessage.Text &= " 条件変更はまだ反映されていません。"
        End Function
        Public Function OpenRowAsync(index As Integer,expectedRevision As Long) As Task
            If index < 0 OrElse index >= _view.dgvStudents.RowCount Then Return Task.CompletedTask
            Dim row = TryCast(_view.dgvStudents.Rows(index).DataBoundItem, ListRow)
            Return If(row Is Nothing, Task.CompletedTask, EditAsync(row.StudentId,expectedRevision))
        End Function
        Public Async Function EditAsync(id As Long?,expectedRevision As Long) As Task
            Await RunAsync(Async Function()
                               If Not ValidateCurrent(expectedRevision) OrElse (id Is Nothing AndAlso Not _service.CanEdit) Then Return
                               RememberPosition()
                               Dim returnRevision=_revision
                               Dim notice As String
                               Using editor As New FrmStudentEdit(_service, id)
                                   editor.ShowDialog(_view) : notice = editor.ResultNotice
                               End Using
                               If Not Alive() Then Return
                               If _applied IsNot Nothing AndAlso ValidateCurrent(returnRevision) Then Await ExecuteAsync(Clone(_applied), Clone(_appliedRaw), _sortKey, _sortDirection, True)
                               If notice <> "" Then _view.lblMessage.Text = notice
                           End Function)
        End Function
        Public Sub Clear(expectedRevision As Long)
            If _busy Then Return
            If _revision > 0 Then ValidateCurrent(expectedRevision)
            ResetState()
        End Sub
        Private Sub ResetState()
            If _requestSequence = Long.MaxValue Then Throw New InvalidOperationException("E-COM-003 検索要求連番が上限です。")
            _requestSequence += 1 : _applied = Nothing : _appliedRaw = Nothing
            _draft = New Core.SearchDraft() : _sortKey = "studentNo" : _sortDirection = "asc"
            _binding = True
            Try
                _view.txtStudentNo.Clear() : _view.txtName.Clear()
                If _view.cboClass.Items.Count > 0 Then _view.cboClass.SelectedIndex = 0
                _view.cboSortKey.SelectedIndex = 0 : _view.cboSortDirection.SelectedIndex = 0
                For i = 0 To _view.StatusChecks.Length - 1
                    _view.StatusChecks(i).Checked = i < 2
                Next
                ClearRows()
            Finally
                _binding = False
            End Try
            Touch()
            _view.lblCount.Text = "未検索" : _view.lblMessage.Text = "未検索" : _view.lblSearchedAt.Text = ""
            UpdateButtons()
        End Sub
        Private Sub ClearRows()
            _binding = True
            Try
                _rows = Array.Empty(Of Core.StudentRow)() : _selectedId = Nothing : _scroll = 0 : _view.dgvStudents.DataSource = Nothing
            Finally
                _binding = False
            End Try
        End Sub
        Private Async Function RunAsync(operation As Func(Of Task)) As Task
            If _busy OrElse Not Alive() Then Return
            _busy = True : UpdateButtons()
            Try
                Await operation()
            Catch ex As OperationCanceledException
            Catch ex As Exception
                If Alive() Then
                    If Not (TypeOf ex Is InvalidOperationException AndAlso ex.Message.StartsWith("E-COM-003",StringComparison.Ordinal)) Then
                        ClearRows() : _view.lblCount.Text = "検索失敗" : _view.lblSearchedAt.Text = ""
                    End If
                    _view.lblMessage.Text = If(TypeOf ex Is Core.InputValidationException, String.Join(Environment.NewLine, DirectCast(ex, Core.InputValidationException).Errors.Select(Function(x) x.Code & " " & x.Message)), If(TypeOf ex Is InvalidOperationException, ex.Message, "E-COM-004 処理に失敗しました。入力は保持しています。"))
                End If
            Finally
                _busy = False : If Alive() Then UpdateButtons()
            End Try
        End Function
        Private Sub UpdateButtons()
            For Each field As Control In New Control() {_view.txtStudentNo, _view.txtName, _view.cboClass, _view.pnlStatuses, _view.cboSortKey, _view.cboSortDirection}
                field.Enabled = Not _busy
            Next
            DirectCast(_view.dgvStudents.Columns("colAction"), DataGridViewButtonColumn).Text = If(_service.CanEdit, "編集", "参照")
            _view.dgvStudents.Enabled = Not _busy
            _view.btnSearch.Enabled = Not _busy AndAlso _ready : _view.btnClear.Enabled = Not _busy : _view.btnNew.Enabled = Not _busy AndAlso _service.CanEdit : _view.btnMenu.Enabled = Not _busy
        End Sub
        Private Sub Touch()
            If _revision = Long.MaxValue Then Throw New InvalidOperationException("E-COM-003 検索状態の版が上限です。")
            _revision += 1 : _lastUsed = DateTimeOffset.UtcNow
            RaiseEvent RevisionPublished(_revision)
        End Sub
        Public Sub Dispose() Implements IDisposable.Dispose
            _lifetime.Cancel() : _lifetime.Dispose()
        End Sub
        Private NotInheritable Class ListRow
            Public Property StudentId As Long
            Public Property StudentNo As String
            Public Property NameDisplay As String
            Public Property BirthDateWareki As String
            Public Property YearGrade As String
            Public Property ClassDisplay As String
            Public Property EnrollmentStatusName As String
        End Class
    End Class
End Namespace
