Imports System.Drawing
Imports System.Linq
Imports System.Text.Json
Imports System.Windows.Forms
Imports StudentManagement.WinForms.Application
Imports StudentManagement.WinForms.Domain
Imports StudentManagement.WinForms.Forms

Namespace GuiEvidence
    Friend Module InitialFocusRegression
        Public Function Run(path As String) As Integer
            Dim cases As New List(Of Object)
            For Each scenario In {"new", "edit", "viewer"}
              For Each layoutWidth In {1180,1280}
                Dim testRole As Role = If(scenario = "viewer", Role.Viewer, Role.Administrator)
                Dim service As New StudentApplicationService(New FixtureService(path), testRole)
                Dim studentId As Long? = If(scenario = "new", Nothing, CType(1, Long?))
                Using form As New FrmStudentEdit(service, studentId)
                    form.ClientSize = New Size(layoutWidth,610)
                    Dim failure As Exception = Nothing
                    Dim ticks = 0
                    Dim initial As Object = Nothing
                    Using timer As New Timer With {.Interval = 50}
                        AddHandler form.Shown, Sub() timer.Start()
                        AddHandler timer.Tick, Sub()
                                                   ticks += 1
                                                   If ticks < 4 Then Return
                                                   timer.Stop()
                                                   Try
                                                       Dim panel = form.Controls.OfType(Of Panel)().Single(Function(c) c.AutoScroll)
                                                       Dim expected As Control = If(scenario = "new", DirectCast(form.txtStudentNo, Control), If(scenario = "edit", DirectCast(form.txtStudentName, Control), DirectCast(form.btnBack, Control)))
                                                       initial = New With {.screen = scenario, .focus = If(form.lblMessage.Focused, "message", If(form.txtStudentNo.Focused, "studentNo", If(form.txtStudentName.Focused, "studentName", If(form.btnBack.Focused, "back", "other")))), .scrollY = panel.AutoScrollPosition.Y, .messageTabStop = form.lblMessage.TabStop, .deviceDpi = form.DeviceDpi, .activeControl = If(form.ActiveControl Is Nothing, "none", form.ActiveControl.AccessibleName)}
                                                       Console.WriteLine(JsonSerializer.Serialize(New With {.initialObservation = initial}))
                                                       Check(Not form.lblMessage.TabStop, scenario & " message excluded from tab traversal", cases)
                                                       Check(expected.Focused OrElse form.ActiveControl Is expected, scenario & " initial active control is first editable field or viewer back", cases)
                                                       Check(panel.AutoScrollPosition.Y = 0, scenario & " initial scroll starts at top", cases)
                                                       Check(panel.ClientRectangle.Contains(panel.PointToClient(form.txtStudentNo.PointToScreen(Point.Empty))), scenario & " student number row is initially visible", cases)
                                                       Check(form.lblMessage.ReadOnly AndAlso form.lblMessage.Multiline AndAlso form.lblMessage.ScrollBars = ScrollBars.Vertical AndAlso Not form.lblMessage.Visible, scenario & " long read-only message remains intact", cases)
                                                       For Each item In form.Fields
                                                           Dim position=form.PointToClient(item.Value.PointToScreen(Point.Empty))
                                                           Check(position.X>=0 AndAlso position.Y>=0 AndAlso position.X+item.Value.Width<=form.ClientSize.Width AndAlso position.Y+item.Value.Height<=form.ClientSize.Height, scenario & " compact field fully visible " & layoutWidth.ToString() & " " & item.Key,cases)
                                                       Next
                                                       For Each button In {form.btnSave,form.btnReset,form.btnReload,form.btnDelete,form.btnBack}
                                                           Dim position=form.PointToClient(button.PointToScreen(Point.Empty))
                                                           Check(position.Y+button.Height<=form.ClientSize.Height,scenario & " action visible " & button.Text,cases)
                                                       Next
                                                       Check(form.txtRemarks.AcceptsReturn AndAlso form.txtOperationReason.AcceptsReturn AndAlso form.txtOperationReason.ScrollBars=ScrollBars.Vertical,scenario & " long text native scrolling",cases)
                                                       form.lblMessage.Text=String.Join(Environment.NewLine,Enumerable.Repeat("E-STU-001 項目を確認してください。",12))
                                                       Check(form.lblMessage.Visible AndAlso form.lblMessage.Height>24 AndAlso panel.ClientSize.Height<610,scenario & " errors push content into scroll viewport",cases)
                                                       form.lblMessage.Text=""
                                                       Dim evidence=Environment.GetEnvironmentVariable("STUDENT_UI_EVIDENCE_DIR")
                                                       If Not String.IsNullOrEmpty(evidence) Then
                                                           IO.Directory.CreateDirectory(evidence)
                                                           Using bitmap As New Bitmap(form.Width,form.Height)
                                                               form.DrawToBitmap(bitmap,New Rectangle(Point.Empty,bitmap.Size))
                                                               bitmap.Save(IO.Path.Combine(evidence,scenario & "-" & layoutWidth.ToString() & ".png"),Imaging.ImageFormat.Png)
                                                           End Using
                                                       End If
                                                       If scenario <> "viewer" Then
                                                           Dim nextField As Control = If(scenario = "new", DirectCast(form.txtStudentName, Control), DirectCast(form.txtStudentNameKana, Control))
                                                           form.SelectNextControl(expected, True, True, True, False)
                                                           Check(nextField.Focused OrElse form.ActiveControl Is nextField, scenario & " next tab follows field order", cases)
                                                       Else
                                                           Check(Not form.txtStudentNo.Enabled AndAlso form.txtStudentName.ReadOnly AndAlso form.txtStudentName.Enabled, "viewer text supports read-only navigation", cases)
                                                       End If
                                                   Catch ex As Exception
                                                       failure = ex
                                                   Finally
                                                       form.Close()
                                                   End Try
                                               End Sub
                        System.Windows.Forms.Application.Run(form)
                    End Using
                    If failure IsNot Nothing Then
                        Console.Error.WriteLine(failure.ToString())
                        Console.WriteLine(JsonSerializer.Serialize(New With {.profile = "VB.NET_WinForms", .passed = cases.Count, .failed = 1, .observation = initial, .database = "NOT_RUN", .actualFormShown = True, .screenshots = "DrawToBitmap when STUDENT_UI_EVIDENCE_DIR is set", .adapter = "test-only concrete adapter substitution"}))
                        Return 1
                    End If
                End Using
              Next
            Next
            If Not SearchRegression(path,cases) Then Return 1
            Console.WriteLine(JsonSerializer.Serialize(New With {.profile = "VB.NET_WinForms", .passed = cases.Count, .failed = 0, .cases = cases, .database = "NOT_RUN", .actualFormShown = True, .screenshots = "DrawToBitmap when STUDENT_UI_EVIDENCE_DIR is set", .adapter = "test-only concrete adapter substitution"}))
            Return 0
        End Function
        Private Function SearchRegression(path As String,cases As List(Of Object)) As Boolean
            Dim backend As New FixtureService(path)
            Dim rows=Enumerable.Range(1,10000).Select(Function(i) New StudentRow(i,"TEST-" & i.ToString("D5"),"試験氏名","シケンシメイ",New DateOnly(2008,5,15),2026,"1年","A","試験クラス","在学")).ToArray()
            backend.OverrideRows=rows
            Using form As New FrmStudentSearch(New StudentApplicationService(backend,Role.Administrator)), timer As New Timer With {.Interval=80}
                Dim failure As Exception=Nothing : Dim ticks=0
                AddHandler form.Shown,Sub() timer.Start()
                AddHandler timer.Tick,Sub()
                    ticks+=1 : If ticks<3 Then Return
                    timer.Stop()
                    Try
                        Dim presenter=DirectCast(GetType(FrmStudentSearch).GetField("_presenter",Reflection.BindingFlags.Instance Or Reflection.BindingFlags.NonPublic).GetValue(form),Presenters.StudentSearchPresenter)
                        Check(form.ClientSize=New Size(1180,610),"scroll native client 1180x610",cases)
                        Check(backend.SearchCalls=0,"scroll initialization does not query students",cases)
                        Check(form.StatusChecks.Length=4 AndAlso form.StatusChecks.All(Function(x) x.Parent Is form.pnlStatuses),"scroll four native checkboxes",cases)
                        form.btnSearch.PerformClick()
                        Check(form.dgvStudents.RowCount=10000 AndAlso backend.SearchCalls=1,"scroll retrieves all 10000 once",cases)
                        Check(form.dgvStudents.Columns.Count=7 AndAlso form.dgvStudents.Columns.Cast(Of DataGridViewColumn)().Sum(Function(x) x.Width)=1146,"scroll seven exact width columns",cases)
                        form.dgvStudents.CurrentCell=form.dgvStudents.Rows(100).Cells(0)
                        form.dgvStudents.FirstDisplayedScrollingRowIndex=90
                        Dim context=System.Text.Json.Nodes.JsonNode.Parse(presenter.CaptureContext()).AsObject()
                        Check(backend.SearchCalls=1 AndAlso context("FirstDisplayedScrollingRowIndex").GetValue(Of Integer)()=90,"scroll is local and context records top",cases)
                        Check(context("SelectedStudentId").GetValue(Of Long)()=101,"scroll selection uses hidden student id",cases)
                        form.txtStudentNo.Text="  ａ-1 "
                        form.cboSortKey.SelectedIndex=1
                        Check(backend.SearchCalls=2 AndAlso backend.LastSort="name:asc" AndAlso String.IsNullOrEmpty(backend.LastCriteria.StudentNo),"scroll sort uses applied criteria",cases)
                        Check(form.txtStudentNo.Text="  ａ-1 " AndAlso form.lblMessage.Text.Contains("まだ反映"),"scroll sort preserves pending raw",cases)
                        Check(form.dgvStudents.FirstDisplayedScrollingRowIndex=0,"scroll sort resets top",cases)
                        form.dgvStudents.FirstDisplayedScrollingRowIndex=80
                        presenter.RefreshAsync(presenter.ContextRevision).GetAwaiter().GetResult()
                        Check(form.dgvStudents.FirstDisplayedScrollingRowIndex=80 AndAlso form.txtStudentNo.Text="  ａ-1 ","scroll editor return keeps top and pending draft",cases)
                        context=System.Text.Json.Nodes.JsonNode.Parse(presenter.CaptureContext()).AsObject() : Dim revision=presenter.ContextRevision
                        Dim foreign=System.Text.Json.Nodes.JsonNode.Parse(context.ToJsonString()).AsObject() : foreign("Owner")="other"
                        Dim denied=False
                        Try : presenter.RestoreContext(foreign.ToJsonString(),revision) : Catch ex As InvalidOperationException : denied=True : End Try
                        Check(denied AndAlso form.dgvStudents.RowCount=10000 AndAlso presenter.ContextRevision=revision,"scroll foreign context leaves current state intact",cases)
                        Dim beforeCalls=backend.SearchCalls
                        presenter.SearchAsync(presenter.ContextRevision-1).GetAwaiter().GetResult()
                        Check(backend.SearchCalls=beforeCalls AndAlso form.dgvStudents.RowCount=10000 AndAlso presenter.ContextRevision=revision,"scroll stale command cannot mutate current state or query",cases)
                        Dim evidence=Environment.GetEnvironmentVariable("STUDENT_UI_EVIDENCE_DIR")
                        If Not String.IsNullOrEmpty(evidence) Then
                            Using bitmap As New Bitmap(form.Width,form.Height)
                                form.DrawToBitmap(bitmap,New Rectangle(Point.Empty,bitmap.Size)) : bitmap.Save(IO.Path.Combine(evidence,"search-1180.png"),Imaging.ImageFormat.Png)
                            End Using
                        End If
                        backend.OverrideRows=rows.Concat({rows(0)}).ToArray() : form.btnSearch.PerformClick()
                        Check(form.dgvStudents.RowCount=0 AndAlso form.lblCount.Text="上限超過" AndAlso form.lblMessage.Text.Contains("W-SRC-001"),"scroll 10001 returns no partial list",cases)
                        backend.OverrideRows=Array.Empty(Of StudentRow)() : form.btnSearch.PerformClick()
                        Check(form.dgvStudents.RowCount=0 AndAlso form.lblCount.Text.StartsWith("0件"),"scroll zero complete result",cases)
                        context=System.Text.Json.Nodes.JsonNode.Parse(presenter.CaptureContext()).AsObject() : revision=presenter.ContextRevision : context("SchemaVersion")="student-search-compact-1"
                        Check(Not presenter.RestoreContext(context.ToJsonString(),revision) AndAlso form.txtStudentNo.Text="" AndAlso form.cboSortKey.SelectedIndex=0 AndAlso form.lblCount.Text="未検索","scroll compact schema resets raw applied sort and results",cases)
                        Dim calls=backend.SearchCalls : presenter.RefreshAsync(presenter.ContextRevision).GetAwaiter().GetResult()
                        Check(backend.SearchCalls=calls,"scroll unsearched editor return does not query",cases)
                    Catch ex As Exception
                        failure=ex
                    Finally
                        form.Close()
                    End Try
                End Sub
                System.Windows.Forms.Application.Run(form)
                If failure IsNot Nothing Then Console.Error.WriteLine(failure.ToString()) : Return False
            End Using
            Return True
        End Function
        Private Sub Check(ok As Boolean, id As String, cases As List(Of Object))
            If Not ok Then Throw New InvalidOperationException("FAILED: " & id)
            cases.Add(New With {.id = id, .passed = True})
        End Sub
    End Module
End Namespace
