Imports System.Windows.Forms
Imports StudentManagement.WinForms.Application
Imports StudentManagement.WinForms.Presenters

Namespace Forms
    Public Partial Class FrmStudentSearch
        Inherits Form
        Private _observedRevision As Long
        Private ReadOnly _presenter As StudentSearchPresenter
        Public Sub New(service As StudentApplicationService)
            InitializeComponent()
            _presenter = New StudentSearchPresenter(Me, service)
            AddHandler _presenter.RevisionPublished,Sub(revision) _observedRevision=revision
            AddHandler Shown, Async Sub(sender, e) Await _presenter.InitializeAsync()
            AddHandler btnSearch.Click, Async Sub(sender, e) Await _presenter.SearchAsync(_observedRevision)
            AddHandler btnClear.Click, Sub(sender, e) _presenter.Clear(_observedRevision)
            AddHandler btnNew.Click, Async Sub(sender, e) Await _presenter.EditAsync(Nothing,_observedRevision)
            AddHandler btnMenu.Click, Sub(sender, e) Close()
            AddHandler cboSortKey.SelectedIndexChanged, Async Sub(sender, e) Await _presenter.SortAsync(_observedRevision)
            AddHandler cboSortDirection.SelectedIndexChanged, Async Sub(sender, e) Await _presenter.SortAsync(_observedRevision)
            AddHandler dgvStudents.Scroll, Sub(sender, e) _presenter.RememberPosition()
            AddHandler dgvStudents.SelectionChanged, Sub(sender, e) _presenter.RememberPosition()
            AddHandler dgvStudents.CellContentClick, Async Sub(sender, e)
                                                        If e.RowIndex >= 0 AndAlso dgvStudents.Columns(e.ColumnIndex).Name = "colAction" Then Await _presenter.OpenRowAsync(e.RowIndex,_observedRevision)
                                                    End Sub
            For Each field As Control In {txtStudentNo, txtName}
                AddHandler field.TextChanged, Sub(sender, e) _presenter.MarkDraftChanged()
            Next
            AddHandler cboClass.SelectedIndexChanged, Sub(sender, e) _presenter.MarkDraftChanged()
            For Each status In StatusChecks
                AddHandler status.CheckedChanged, Sub(sender, e) _presenter.MarkDraftChanged()
            Next
            AddHandler FormClosed, Sub(sender, e) _presenter.Dispose()
        End Sub
    End Class
End Namespace
