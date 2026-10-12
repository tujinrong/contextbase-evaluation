Imports System.Windows.Forms
Imports StudentManagement.WinForms.Application
Imports StudentManagement.WinForms.Presenters

Namespace Forms
    Public Partial Class FrmStudentEdit
        Inherits Form
        Private ReadOnly _presenter As StudentEditPresenter
        <System.ComponentModel.Browsable(False), System.ComponentModel.DesignerSerializationVisibility(System.ComponentModel.DesignerSerializationVisibility.Hidden)>
        Public Property ResultNotice As String = ""
        Public Sub New(service As StudentApplicationService, id As Long?)
            InitializeComponent()
            _presenter = New StudentEditPresenter(Me, service, id)
            AddHandler Shown, Async Sub(sender, e)
                                  Await _presenter.InitializeAsync()
                                  If Not IsDisposed AndAlso IsHandleCreated Then BeginInvoke(New MethodInvoker(AddressOf FocusInitialField))
                              End Sub
            AddHandler btnSave.Click, Async Sub(sender, e) Await _presenter.SaveAsync()
            AddHandler btnDelete.Click, Async Sub(sender, e) Await _presenter.DeleteAsync()
            AddHandler btnReset.Click, Sub(sender, e) _presenter.Reset()
            AddHandler btnReload.Click, Async Sub(sender, e) Await _presenter.ReloadAsync()
            AddHandler btnBack.Click, Sub(sender, e) Close()
            AddHandler cboSchoolYear.SelectedIndexChanged, Sub(sender, e) _presenter.RefreshClasses()
            AddHandler cboGrade.SelectedIndexChanged, Sub(sender, e) _presenter.RefreshClasses()
            AddHandler cboClass.SelectedIndexChanged, Sub(sender, e) _presenter.SelectClass()
            AddHandler cboEnrollmentStatus.SelectedIndexChanged, Sub(sender, e) _presenter.StatusChanged()
            AddHandler FormClosing, Sub(sender, e) e.Cancel = Not _presenter.CanClose()
            AddHandler FormClosed, Sub(sender, e) _presenter.Dispose()
        End Sub
        Private Sub FocusInitialField()
            If IsDisposed Then Return
            Dim first = Fields.Values.Where(Function(control) control.CanSelect AndAlso control.TabStop).OrderBy(Function(control) control.TabIndex).FirstOrDefault()
            If first IsNot Nothing Then
                first.Focus()
            Else
                btnBack.Focus()
            End If
            _studentScroll.AutoScrollPosition = System.Drawing.Point.Empty
        End Sub
    End Class
End Namespace
