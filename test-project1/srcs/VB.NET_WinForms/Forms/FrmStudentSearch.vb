Imports System.Windows.Forms
Imports StudentManagement.WinForms.Application
Imports StudentManagement.WinForms.Presenters

Namespace Forms
    Public Partial Class FrmStudentSearch
        Inherits Form
        Private ReadOnly _presenter As StudentSearchPresenter
        Public Sub New(service As StudentApplicationService)
            InitializeComponent()
            _presenter = New StudentSearchPresenter(Me, service)
            AddHandler Shown, Async Sub(sender, e) Await _presenter.InitializeAsync()
            AddHandler btnSearch.Click, Async Sub(sender, e) Await _presenter.SearchAsync()
            AddHandler btnClear.Click, Sub(sender, e) _presenter.Clear()
            AddHandler btnNew.Click, Async Sub(sender, e) Await _presenter.EditAsync(Nothing)
            AddHandler btnMenu.Click, Sub(sender, e) Close()
            AddHandler btnSort.Click, Async Sub(sender, e) Await _presenter.MoveAsync(1)
            AddHandler btnFirst.Click, Async Sub(sender, e) Await _presenter.MoveAsync(1)
            AddHandler btnPrev.Click, Async Sub(sender, e) Await _presenter.MoveRelativeAsync(-1)
            AddHandler btnNext.Click, Async Sub(sender, e) Await _presenter.MoveRelativeAsync(1)
            AddHandler btnLast.Click, Async Sub(sender, e) Await _presenter.MoveLastAsync()
            AddHandler dgvStudents.CellContentClick, Async Sub(sender, e)
                                                        If e.RowIndex >= 0 AndAlso dgvStudents.Columns(e.ColumnIndex).Name = "colAction" Then Await _presenter.OpenRowAsync(e.RowIndex)
                                                    End Sub
            For Each field As Control In {txtStudentNo, txtName}
                AddHandler field.TextChanged, Sub(sender, e) _presenter.MarkDraftChanged()
            Next
            AddHandler cboClass.SelectedIndexChanged, Sub(sender, e) _presenter.MarkDraftChanged()
            AddHandler clbStatuses.ItemCheck, Sub(sender, e) _presenter.MarkDraftChanged()
            AddHandler FormClosed, Sub(sender, e) _presenter.Dispose()
        End Sub
    End Class
End Namespace
