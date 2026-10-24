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
              For Each layoutWidth In {1280,1366}
                Dim testRole As Role = If(scenario = "viewer", Role.Viewer, Role.Administrator)
                Dim service As New StudentApplicationService(New FixtureService(path), testRole)
                Dim studentId As Long? = If(scenario = "new", Nothing, CType(1, Long?))
                Using form As New FrmStudentEdit(service, studentId)
                    form.ClientSize = New Size(layoutWidth,650)
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
                                                       Check(form.lblMessage.ReadOnly AndAlso form.lblMessage.Multiline AndAlso form.lblMessage.ScrollBars = ScrollBars.Vertical AndAlso form.lblMessage.Height = 70, scenario & " long read-only message remains intact", cases)
                                                       For Each item In form.Fields
                                                           Dim position=form.PointToClient(item.Value.PointToScreen(Point.Empty))
                                                           Check(position.X>=0 AndAlso position.Y>=0 AndAlso position.X+item.Value.Width<=form.ClientSize.Width AndAlso position.Y+item.Value.Height<=form.ClientSize.Height, scenario & " compact field fully visible " & layoutWidth.ToString() & " " & item.Key,cases)
                                                       Next
                                                       For Each button In {form.btnSave,form.btnReset,form.btnReload,form.btnDelete,form.btnBack}
                                                           Dim position=form.PointToClient(button.PointToScreen(Point.Empty))
                                                           Check(position.Y+button.Height<=form.ClientSize.Height,scenario & " action visible " & button.Text,cases)
                                                       Next
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
                                                           Check(Not form.txtStudentNo.Enabled AndAlso Not form.txtStudentName.Enabled, "viewer fields remain disabled", cases)
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
            Console.WriteLine(JsonSerializer.Serialize(New With {.profile = "VB.NET_WinForms", .passed = cases.Count, .failed = 0, .cases = cases, .database = "NOT_RUN", .actualFormShown = True, .screenshots = "DrawToBitmap when STUDENT_UI_EVIDENCE_DIR is set", .adapter = "test-only concrete adapter substitution"}))
            Return 0
        End Function
        Private Sub Check(ok As Boolean, id As String, cases As List(Of Object))
            If Not ok Then Throw New InvalidOperationException("FAILED: " & id)
            cases.Add(New With {.id = id, .passed = True})
        End Sub
    End Module
End Namespace
