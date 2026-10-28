Imports System.IO
Imports System.Text.Json
Imports System.Windows.Forms
Imports StudentManagement.WinForms.Domain
Imports StudentManagement.WinForms.Forms
Imports StudentManagement.WinForms.Presenters
Imports StudentManagement.WinForms.Application

Namespace GuiEvidence
    Module Program
        <STAThread>
        Public Function Main(args As String()) As Integer
            Dim path=IO.Path.Combine(AppContext.BaseDirectory,"fixture.json")
            If args.SequenceEqual({"--self-test"}) Then Return SelfTest(path)
            If args.SequenceEqual({"--ui-regression"}) Then
                System.Windows.Forms.Application.SetHighDpiMode(HighDpiMode.DpiUnaware)
                System.Windows.Forms.Application.EnableVisualStyles()
                System.Windows.Forms.Application.SetCompatibleTextRenderingDefault(False)
                Return InitialFocusRegression.Run(path)
            End If
            If (args.Length<>2 AndAlso args.Length<>4) OrElse args(0)<>"--screen" OrElse Not {"search","new","edit"}.Contains(args(1)) OrElse (args.Length=4 AndAlso args(2)<>"--role") Then
                Console.Error.WriteLine("Use --self-test, --ui-regression or --screen search|new|edit [--role admin|staff|viewer]") : Return 2
            End If
            Dim roleName=If(args.Length=4,args(3),"admin")
            If Not {"admin","staff","viewer"}.Contains(roleName) Then Throw New ArgumentException("Invalid fixture role")
            Dim role=If(roleName="admin",Domain.Role.Administrator,If(roleName="staff",Domain.Role.Staff,Domain.Role.Viewer))
            Dim service As New StudentApplicationService(New FixtureService(path),role)
            System.Windows.Forms.Application.SetHighDpiMode(HighDpiMode.PerMonitorV2)
            System.Windows.Forms.Application.EnableVisualStyles()
            System.Windows.Forms.Application.SetCompatibleTextRenderingDefault(False)
            If args(1)="search" Then
                Using form As New FrmStudentSearch(service)
                    AddHandler form.Shown,Sub() form.btnSearch.PerformClick()
                    System.Windows.Forms.Application.Run(form)
                End Using
            Else
                Using form As New FrmStudentEdit(service,If(args(1)="edit",CType(1,Long?),Nothing))
                    System.Windows.Forms.Application.Run(form)
                End Using
            End If
            Return 0
        End Function
        Private Function SelfTest(path As String) As Integer
            Dim cases As New List(Of String)
            Dim check As Action(Of Boolean,String)=Sub(ok,id)
                                                       If Not ok Then Throw New Exception(id)
                                                       cases.Add(id)
                                                   End Sub
            Dim backend As New FixtureService(path)
            Dim service As New StudentApplicationService(backend,Role.Administrator)
            check(backend.LookupAsync(False).Result.Classes.All(Function(c) c.Occupied=0),"FIX-VB-001 search lookup omits occupancy")
            check(backend.LookupAsync().Result.Classes.Sum(Function(c) c.Occupied)=2,"FIX-VB-002 editor occupancy")
            Using form As New FrmStudentSearch(service), presenter As New StudentSearchPresenter(form,service)
                presenter.InitializeAsync().GetAwaiter().GetResult()
                presenter.SearchAsync(presenter.ContextRevision).GetAwaiter().GetResult()
                check(form.dgvStudents.RowCount=2 AndAlso form.lblCount.Text.StartsWith("2件"),"FIX-VB-003 original presenter default status filter")
                form.txtStudentNo.Text="TEST-VB-002" : presenter.SearchAsync(presenter.ContextRevision).GetAwaiter().GetResult()
                check(form.dgvStudents.RowCount=1,"FIX-VB-004 original presenter selected fixture")
                form.txtStudentNo.Text="TEST-NONE" : presenter.SearchAsync(presenter.ContextRevision).GetAwaiter().GetResult()
                check(form.dgvStudents.RowCount=0 AndAlso form.lblCount.Text.StartsWith("0件"),"FIX-VB-005 zero results")
                presenter.Clear(presenter.ContextRevision) : check(form.lblCount.Text="未検索","FIX-VB-006 original clear state")
                check(form.dgvStudents.Columns.Count=7,"COMPACT-VB-001 seven result columns")
                presenter.SearchAsync(presenter.ContextRevision).GetAwaiter().GetResult()
                Dim context=presenter.CaptureContext() : Dim revision=presenter.ContextRevision
                check(presenter.RestoreContext(context,revision),"COMPACT-VB-002 current context restores")
                Dim state=System.Text.Json.Nodes.JsonNode.Parse(context).AsObject()
                For Each key In {"Owner","Session","WindowId","StateId"}
                    Dim wrong=System.Text.Json.Nodes.JsonNode.Parse(context).AsObject() : wrong(key)="wrong"
                    Dim denied=False
                    Try : presenter.RestoreContext(wrong.ToJsonString(),revision) : Catch ex As InvalidOperationException : denied=ex.Message.Contains("E-COM-003") : End Try
                    check(denied,"COMPACT-VB-003 ownership boundary " & key)
                Next
                Dim stale=False
                Try : presenter.RestoreContext(context,revision-1) : Catch ex As InvalidOperationException : stale=True : End Try
                check(stale,"COMPACT-VB-004 stale revision rejected")
                For Each field In {"StudentNameKana","SchoolYear","GradeCode","UnassignedOnly","PrefectureCode","PhoneNumber","AdmissionFrom","AdmissionTo","Unexpected","Page","PageSize","Offset"}
                    Dim invalid=System.Text.Json.Nodes.JsonNode.Parse(context).AsObject()
                    invalid("Criteria").AsObject()(field)="obsolete"
                    Dim denied=False
                    Try : presenter.RestoreContext(invalid.ToJsonString(),revision) : Catch ex As InvalidOperationException : denied=ex.Message.Contains("E-COM-003") : End Try
                    check(denied,"COMPACT-VB-005 unknown criteria rejected " & field)
                Next
                state("SchemaVersion")="student-search-old"
                check(Not presenter.RestoreContext(state.ToJsonString(),revision) AndAlso form.lblCount.Text="未検索" AndAlso form.lblMessage.Text.Contains("旧形式") AndAlso form.StatusChecks(0).Checked AndAlso form.StatusChecks(1).Checked AndAlso form.dgvStudents.RowCount=0,"COMPACT-VB-006 old schema resets whole state")
                presenter.SearchAsync(presenter.ContextRevision).GetAwaiter().GetResult() : state=System.Text.Json.Nodes.JsonNode.Parse(presenter.CaptureContext()).AsObject() : revision=presenter.ContextRevision : state.Remove("SchemaVersion")
                check(Not presenter.RestoreContext(state.ToJsonString(),revision) AndAlso form.lblMessage.Text.Contains("旧形式"),"COMPACT-VB-007 missing schema resets")
                presenter.SearchAsync(presenter.ContextRevision).GetAwaiter().GetResult() : state=System.Text.Json.Nodes.JsonNode.Parse(presenter.CaptureContext()).AsObject() : revision=presenter.ContextRevision : state("ExpiresAt")=DateTimeOffset.UtcNow.AddMinutes(-1).ToString("O")
                check(Not presenter.RestoreContext(state.ToJsonString(),revision) AndAlso form.lblMessage.Text.Contains("W-SRC-002"),"COMPACT-VB-008 expired context resets")
                form.txtStudentNo.Text="TEST-VB-00"
                For Each status In form.StatusChecks : status.Checked=False : Next
                presenter.SearchAsync(presenter.ContextRevision).GetAwaiter().GetResult()
                check(form.dgvStudents.RowCount=3,"COMPACT-VB-009 empty statuses means all")
                form.txtStudentNo.Text="VB-001" : presenter.SearchAsync(presenter.ContextRevision).GetAwaiter().GetResult()
                check(form.dgvStudents.RowCount=0,"COMPACT-VB-010 student number is prefix")
            End Using
            Using form As New FrmStudentEdit(service,1), presenter As New StudentEditPresenter(form,service,1)
                presenter.InitializeAsync().GetAwaiter().GetResult()
                check(form.txtStudentNo.Text="TEST-VB-001" AndAlso form.txtStudentName.Text="仮名 太郎" AndAlso Not form.txtStudentNo.Enabled,"FIX-VB-007 original editor immutable number")
                Dim before=form.txtStudentName.Text : presenter.SaveAsync().GetAwaiter().GetResult()
                check(form.lblMessage.Text.Contains("DB未接続") AndAlso form.txtStudentName.Text=before AndAlso form.ResultNotice="","FIX-VB-008 fixture refuses writes retains raw")
            End Using
            Using form As New FrmStudentEdit(service,Nothing), presenter As New StudentEditPresenter(form,service,Nothing)
                presenter.InitializeAsync().GetAwaiter().GetResult()
                check(form.txtStudentNo.Text="" AndAlso form.txtStudentNo.Enabled,"FIX-VB-009 original new screen defaults")
            End Using
            Dim viewer As New StudentApplicationService(backend,Role.Viewer)
            Using form As New FrmStudentEdit(viewer,1), presenter As New StudentEditPresenter(form,viewer,1)
                presenter.InitializeAsync().GetAwaiter().GetResult()
                check(Not form.btnSave.Enabled AndAlso Not form.btnDelete.Enabled AndAlso form.Text.Contains("参照"),"FIX-VB-010 fixture viewer display flags only")
            End Using
            Dim first=backend.GetAsync(1).Result : first.Draft.StudentName="試験変更"
            check(backend.GetAsync(1).Result.Draft.StudentName="仮名 太郎","FIX-VB-011 fixture returns detached draft")
            For Each id As Long In {1L,2L,3L}
                Dim normalized=StudentNormalizer.Normalize(backend.GetAsync(id).Result.Draft,New DateOnly(2026,10,12))
                check(normalized.Text("student_no").StartsWith("TEST-VB-"),"FIX-VB-012 valid fictional draft " & id.ToString())
            Next
            check(backend.GetAsync(999).Result Is Nothing,"FIX-VB-013 missing fixture returns Nothing")
            Console.WriteLine(JsonSerializer.Serialize(New With {.profile="VB.NET_WinForms",.passed=cases.Count,.failed=0,.cases=cases,.database="NOT_RUN",.interactiveUI="NOT_RUN",.screenshots="NOT_RUN",.backend="fixture"}))
            Return 0
        End Function
    End Module
End Namespace
