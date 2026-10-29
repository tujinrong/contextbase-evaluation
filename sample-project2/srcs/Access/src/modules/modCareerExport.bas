Option Compare Binary
Option Explicit
Private Declare PtrSafe Function MoveFileExW Lib "kernel32" (ByVal source As LongPtr, ByVal target As LongPtr, ByVal flags As Long) As Long
Private Declare PtrSafe Function GetStringTypeW Lib "kernel32" (ByVal kind As Long, ByVal source As LongPtr, ByVal chars As Long, ByRef flags As Integer) As Long
Private Declare PtrSafe Function CreateCompatibleDC Lib "gdi32" (ByVal device As LongPtr) As LongPtr
Private Declare PtrSafe Function CreateFontW Lib "gdi32" (ByVal height As Long, ByVal width As Long, ByVal escapement As Long, ByVal orientation As Long, ByVal weight As Long, ByVal italic As Long, ByVal underline As Long, ByVal strikeout As Long, ByVal charset As Long, ByVal outputPrecision As Long, ByVal clipPrecision As Long, ByVal quality As Long, ByVal pitch As Long, ByVal face As LongPtr) As LongPtr
Private Declare PtrSafe Function SelectObject Lib "gdi32" (ByVal device As LongPtr, ByVal item As LongPtr) As LongPtr
Private Declare PtrSafe Function DeleteObject Lib "gdi32" (ByVal item As LongPtr) As Long
Private Declare PtrSafe Function DeleteDC Lib "gdi32" (ByVal device As LongPtr) As Long
Private Type TEXTSIZE
    width As Long
    height As Long
End Type
Private Declare PtrSafe Function GetTextExtentPoint32W Lib "gdi32" (ByVal device As LongPtr, ByVal text As LongPtr, ByVal length As Long, ByRef size As TEXTSIZE) As Long
Private exportRequest As String
Private exportRunning As Boolean
Private measureDC As LongPtr
Private measureFont As LongPtr
Private previousFont As LongPtr
Private measuredBodyWidth As Double
Private measuredWholeWidth As Double
Private originalText As Object
Private rowStyles As Object
Private pagePlans As Object
Private pageEnds As Object
Private pageCaps As Object
Private caseContexts As Object
Private sectionContexts As Object
Private textGroup As Long
Private Function FitsText(ByVal value As String, Optional ByVal wide As Boolean = False) As Boolean
    Dim size As TEXTSIZE
    If value = "" Then FitsText = True: Exit Function
    If GetTextExtentPoint32W(measureDC, StrPtr(value), Len(value), size) = 0 Then Reject "MSG-037"
    FitsText = (size.width <= IIf(wide, measuredWholeWidth, measuredBodyWidth) And size.height <= 24)
End Function
Public Function ReadReport(ByVal employeeId As Long, ByVal session As clsSession) As clsResult
    Dim u As New clsUnitOfWork, snapshot As New clsReportSnapshot, q As DAO.QueryDef, r As DAO.Recordset, result As clsResult, text As String
    On Error GoTo Failed
    u.OpenUnit True: RequireCurrent session, "STAFF", u.Db
    snapshot.CapturedAtUtc = UtcNow(): snapshot.BusinessDate = DateValue(DateAdd("h", 9, snapshot.CapturedAtUtc))
    Set snapshot.Employee = LoadAggregate(u.Db, employeeId, True)
    If snapshot.Employee.Careers.Count = 0 Then Reject "MSG-012"
    Set snapshot.Names = CreateObject("Scripting.Dictionary")
    Set r = u.Db.OpenRecordset("SELECT category_id, code, code_name FROM m_code", dbOpenSnapshot)
    Do While Not r.EOF
        snapshot.Names.Add CStr(r!category_id) & "/" & CStr(r!code), CStr(r!code_name): r.MoveNext
    Loop
    r.Close: u.Commit: u.CloseUnit
    Set result = MakeResult("OK"): Set result.Value = snapshot: Set ReadReport = result: Exit Function
Failed:
    text = Err.Description
    If Left$(text, 4) <> "MSG-" Then text = "MSG-028"
    Set ReadReport = Failure(text, u, True)
End Function
Private Sub Checkpoint()
    If GateIsOwned() Then Reject "MSG-020"
    DoEvents
    If gSession Is Nothing Then Reject "MSG-002"
    If Not gSession.IsAuthenticated Then Reject "MSG-002"
    If GetTickCount64() - gSession.LastActivityTick >= 1800000 Then Reject "MSG-002"
    If gExportCancel Then Reject "MSG-030"
End Sub
Private Sub PutText(ByVal ws As Object, ByVal address As String, ByVal value As String, ByVal expected As Collection, Optional ByVal group As Long = 0, Optional ByVal before As String = "")
    expected.Add Array(CStr(ws.Name), address, value, group, before)
End Sub
Private Sub FlushText(ByVal ws As Object, ByVal expected As Collection)
    Dim lastRow As Long, item As Variant, row As Long, col As Long, values() As Variant, actual As Variant, cell As Object, key As Variant, kind As String, span As Object
    For Each item In expected
        If CStr(item(0)) = CStr(ws.Name) Then
            row = CLng(Mid$(CStr(item(1)), 2)): If row > lastRow Then lastRow = row
        End If
    Next
    If lastRow < 5 Then Reject "MSG-037"
    ReDim values(1 To lastRow - 4, 1 To 24)
    For Each item In expected
        If CStr(item(0)) = CStr(ws.Name) Then
            row = CLng(Mid$(CStr(item(1)), 2)): col = IIf(Left$(CStr(item(1)), 1) = "A", 1, 7)
            If row <= 4 Then ws.Range(CStr(item(1))).Value2 = CStr(item(2)) Else values(row - 4, col) = CStr(item(2))
        End If
    Next
    ws.Range("A5:X" & CStr(lastRow)).Value2 = values
    ws.Range("A5:F" & CStr(lastRow)).Merge True: ws.Range("G5:X" & CStr(lastRow)).Merge True
    ws.Range("A5:X" & CStr(lastRow)).Borders.LineStyle = 1
    ws.Range("A5:X" & CStr(lastRow)).Borders.Color = &HC5B8AE
    ws.Range("A5:F" & CStr(lastRow)).Font.Size = 11: ws.Range("A5:F" & CStr(lastRow)).Font.Bold = True
    For Each key In rowStyles.Keys
        If Left$(CStr(key), Len(ws.Name) + 1) = ws.Name & "|" Then
            row = CLng(Mid$(CStr(key), Len(ws.Name) + 2)): kind = rowStyles(key)
            Set span = ws.Range("A" & row & ":X" & row)
            If Left$(kind, 4) = "wide" Then
                span.UnMerge: span.Merge
                span.Font.Size = 10.5: span.Font.Bold = False
            End If
            If kind = "wide-heading" Or kind = "pair-heading" Then
                span.Font.Size = 11: span.Font.Bold = True
                span.Borders(9).LineStyle = 1: span.Borders(9).Color = &H503617
            End If
            Set span = Nothing
        End If
    Next
    actual = ws.Range("A1:X" & CStr(lastRow)).Value2
    For Each item In expected
        If CStr(item(0)) = CStr(ws.Name) Then
            row = CLng(Mid$(CStr(item(1)), 2)): col = IIf(Left$(CStr(item(1)), 1) = "A", 1, 7)
            If CStr(Nz(actual(row, col), "")) <> CStr(item(2)) Then
                Set cell = ws.Range(CStr(item(1))): cell.NumberFormat = "@": cell.Value2 = "'" & CStr(item(2))
                If CStr(Nz(cell.Value2, "")) <> CStr(item(2)) Or cell.HasFormula Then Reject "MSG-037"
                Set cell = Nothing
            End If
        End If
    Next
End Sub
Private Function ClusterEnd(ByVal value As String, ByVal first As Long) As Long
    Dim i As Long, u As Long, flags As Integer, joined As Boolean
    i = first
    Do
        u = AscW(Mid$(value, i, 1)) And &HFFFF&
        If u >= &HD800& And u <= &HDBFF& Then i = i + 2 Else i = i + 1
        If i > Len(value) Then Exit Do
        u = AscW(Mid$(value, i, 1)) And &HFFFF&
        If u = &H200D& Then
            i = i + 1: If i > Len(value) Then Reject "MSG-037"
        Else
            flags = 0
            If GetStringTypeW(4, StrPtr(Mid$(value, i, 1)), 1, flags) = 0 Then Reject "MSG-037"
            If (flags And 7) = 0 And Not (u >= &HFE00& And u <= &HFE0F&) Then
                ' Emoji skin-tone modifier (U+1F3FB..U+1F3FF) and supplementary variation selectors.
                If u = &HD83C& And i < Len(value) Then
                    u = AscW(Mid$(value, i + 1, 1)) And &HFFFF&
                    If u >= &HDFFB& And u <= &HDFFF& Then i = i + 2 Else Exit Do
                ElseIf u = &HDB40& And i < Len(value) Then
                    u = AscW(Mid$(value, i + 1, 1)) And &HFFFF&
                    If u >= &HDD00& And u <= &HDDEF& Then i = i + 2 Else Exit Do
                Else
                    Exit Do
                End If
                If i > Len(value) Then Exit Do
                ClusterEnd = i: Exit Function
            End If
        End If
    Loop
    ClusterEnd = i
End Function
Private Function TextPieces(ByVal source As String, Optional ByVal wide As Boolean = False) As Collection
    Dim answer As New Collection, lines As Variant, line As Variant, first As Long, last As Long, after As Long, segment As String, lineNumber As Long, width As Double, ch As String, i As Long
    ScalarLength source: lines = Split(source, vbLf)
    For Each line In lines
        first = 1
        Do
            segment = "": width = 0: last = first
            Do While last <= Len(CStr(line))
                after = ClusterEnd(CStr(line), last): ch = Mid$(CStr(line), last, after - last)
                For i = 1 To Len(ch)
                    If (AscW(Mid$(ch, i, 1)) And &HFFFF&) < 128 Then width = width + 0.5 Else width = width + 1
                Next
                If width > IIf(wide, 32, 24) And Len(segment) > 0 Then Exit Do
                If Not FitsText(segment & ch, wide) Then
                    If Len(segment) = 0 Then Reject "MSG-037"
                    Exit Do
                End If
                segment = segment & ch: last = after
                If ScalarLength(segment) >= 32 Then Exit Do
            Loop
            If segment = "" And Len(CStr(line)) > 0 Then Reject "MSG-037"
            answer.Add Array(segment, IIf(lineNumber > 0 And first = 1, vbLf, ""))
            first = last
            If first > Len(CStr(line)) Then Exit Do
        Loop
        lineNumber = lineNumber + 1
    Next
    Set TextPieces = answer
End Function
Private Sub EnsureMeasure(ByVal ws As Object)
    Dim face As String
    If measureDC = 0 Then
        face = "メイリオ": measureDC = CreateCompatibleDC(0)
        measureFont = CreateFontW(-14, 0, 0, 0, 400, 0, 0, 0, 1, 0, 0, 4, 0, StrPtr(face))
        If measureDC = 0 Or measureFont = 0 Then Reject "MSG-037"
        previousFont = SelectObject(measureDC, measureFont)
    End If
    measuredBodyWidth = CDbl(ws.Range("G5:X5").Width) * 96 / 72 - 8
    measuredWholeWidth = CDbl(ws.Range("A5:X5").Width) * 96 / 72 - 8
End Sub
Private Sub StartPage(ByVal ws As Object, ByRef row As Long, ByVal expected As Collection, ByVal repeatContext As Boolean)
    Dim planned As Collection, context As Variant, pieces As Collection, piece As Variant, title As String
    Set planned = pagePlans(ws.Name): planned.Add row
    pageEnds(ws.Name) = row + CLng(pageCaps(ws.Name))
    If Not repeatContext Then Exit Sub
    context = caseContexts(ws.Name)
    If CStr(context(0)) <> "" Then
        Set pieces = TextPieces(CStr(context(1)))
        If pieces.Count + 1 >= CLng(pageCaps(ws.Name)) Then Reject "MSG-037"
        For Each piece In pieces
            PutText ws, "A" & row, "案件" & CStr(context(0)) & "（続き）", expected
            PutText ws, "G" & row, CStr(piece(0)), expected
            rowStyles(ws.Name & "|" & CStr(row)) = "pair-heading": row = row + 1
        Next
    Else
        title = CStr(sectionContexts(ws.Name))
        If title <> "" Then
            PutText ws, "A" & row, title & "（続き）", expected
            rowStyles(ws.Name & "|" & CStr(row)) = "wide-heading": row = row + 1
        End If
    End If
End Sub
Private Sub EnsureRows(ByVal ws As Object, ByRef row As Long, ByVal expected As Collection, Optional ByVal required As Long = 1, Optional ByVal repeatContext As Boolean = True)
    If required > CLng(pageCaps(ws.Name)) Then Reject "MSG-037"
    If CLng(pageEnds(ws.Name)) - row < required Then StartPage ws, row, expected, repeatContext
End Sub
Private Sub BeginCase(ByVal ws As Object, ByRef row As Long, ByVal ordinal As Long, ByVal title As String, ByVal expected As Collection)
    Dim pieces As Collection
    Set pieces = TextPieces(title)
    EnsureRows ws, row, expected, pieces.Count + 1, False
    caseContexts(ws.Name) = Array(Format$(ordinal, "00"), title)
End Sub
Private Sub WriteBlock(ByVal ws As Object, ByRef row As Long, ByVal label As String, ByVal source As Variant, ByVal expected As Collection, Optional ByVal heading As Boolean = False)
    Dim pieces As Collection, piece As Variant, index As Long, text As String, group As Long
    text = CStr(Nz(source, "")): Set pieces = TextPieces(text)
    textGroup = textGroup + 1: group = textGroup: originalText.Add CStr(group), text
    For Each piece In pieces
        EnsureRows ws, row, expected
        PutText ws, "A" & row, label & IIf(index > 0, "（続き）", ""), expected
        PutText ws, "G" & row, CStr(piece(0)), expected, group, CStr(piece(1))
        rowStyles(ws.Name & "|" & CStr(row)) = IIf(heading, "pair-heading", "pair-body")
        row = row + 1: index = index + 1
    Next
    Checkpoint
End Sub
Private Sub WriteWideBlock(ByVal ws As Object, ByRef row As Long, ByVal label As String, ByVal source As Variant, ByVal expected As Collection)
    Dim pieces As Collection, piece As Variant, text As String, group As Long
    sectionContexts(ws.Name) = label
    EnsureRows ws, row, expected, 2, False
    PutText ws, "A" & row, label, expected: rowStyles(ws.Name & "|" & CStr(row)) = "wide-heading": row = row + 1
    text = CStr(Nz(source, "")): Set pieces = TextPieces(text, True)
    textGroup = textGroup + 1: group = textGroup: originalText.Add CStr(group), text
    For Each piece In pieces
        EnsureRows ws, row, expected
        PutText ws, "A" & row, CStr(piece(0)), expected, group, CStr(piece(1))
        rowStyles(ws.Name & "|" & CStr(row)) = "wide-body": row = row + 1
    Next
    Checkpoint
End Sub
Private Sub ConfigureSheet(ByVal ws As Object, ByVal title As String, ByVal snapshot As clsReportSnapshot, ByVal expected As Collection)
    Dim setup As Object, zoom As Long, columnWidth As Double, available As Double, footer As String, piece As Variant, parts As Collection, nameDisplay As String, capacity As Long, planned As New Collection, page As Object, tooWide As Boolean
    ws.Cells.Font.Name = "メイリオ": ws.Cells.Font.Size = 10.5: ws.Cells.NumberFormat = "@"
    columnWidth = 3: ws.Columns("A:X").ColumnWidth = columnWidth: ws.Rows.RowHeight = 18
    Set setup = ws.PageSetup
    setup.Orientation = 1: setup.PaperSize = 9
    setup.LeftMargin = 42.519685: setup.RightMargin = 42.519685: setup.TopMargin = 42.519685: setup.BottomMargin = 42.519685
    setup.HeaderMargin = 19.84252: setup.FooterMargin = 19.84252
    setup.PrintHeadings = False: setup.PrintGridlines = False: setup.PrintTitleColumns = ""
    setup.FitToPagesWide = False: setup.FitToPagesTall = False: setup.Zoom = 100
    setup.PrintArea = "$A$1:$X$5": ws.Range("X5").Value2 = "x": ws.DisplayPageBreaks = True
    ' A full-width probe uses the printer's actual page bands, with extra room for rounding/borders.
    available = 595.27559 - 85.03937 - 24
    Do
        tooWide = (CDbl(ws.Range("A1:X1").Width) > available)
        For Each page In ws.VPageBreaks
            If page.Location.Column > 1 And page.Location.Column <= 24 Then tooWide = True
        Next
        If setup.Pages.Count <> 1 Then tooWide = True
        If Not tooWide Then Exit Do
        columnWidth = columnWidth - 0.1
        If columnWidth < 2 Then Reject "MSG-037"
        ws.Columns("A:X").ColumnWidth = columnWidth
    Loop
    EnsureMeasure ws
    If title = "案件経歴" Then
        ws.Range("A1:X1").Merge: ws.Rows(1).RowHeight = 36
        Set parts = TextPieces(snapshot.Employee.Name, True)
        For Each piece In parts
            If nameDisplay <> "" Then nameDisplay = nameDisplay & vbLf
            nameDisplay = nameDisplay & CStr(piece(0))
        Next
        ws.Range("A2:X2").Merge: ws.Rows(2).RowHeight = 18 * parts.Count: ws.Range("A2").WrapText = True
        PutText ws, "A2", nameDisplay, expected
    Else
        ws.Range("A1:X2").Merge
    End If
    ws.Range("A1").Font.Size = 18: ws.Range("A1").Font.Bold = True: PutText ws, "A1", title, expected
    ws.Range("A3:X3").Merge: PutText ws, "A3", Format$(snapshot.BusinessDate, "yyyy年mm月dd日") & "現在", expected
    ws.Range("A4:X4").Merge: PutText ws, "A4", "作成日時（JST）：" & Format$(DateAdd("h", 9, snapshot.CapturedAtUtc), "yyyy年mm月dd日 hh:nn"), expected
    Set parts = TextPieces(snapshot.Employee.Name, True)
    For Each piece In parts
        If footer <> "" Then footer = footer & vbLf
        footer = footer & Replace(CStr(piece(0)), "&", "&&")
    Next
    footer = footer & vbLf & ws.Name & " ／ 作成JST " & Format$(DateAdd("h", 9, snapshot.CapturedAtUtc), "yyyy年mm月dd日 hh:nn") & "  &P/&N"
    zoom = Fix(available / CDbl(ws.Range("A1:X1").Width) * 100)
    If zoom < 100 Then Reject "MSG-037"
    If zoom > 100 Then zoom = 100
    ' PH07 Access-only technical override: FitTo ignores manual breaks (Microsoft Support).
    setup.FitToPagesWide = False: setup.FitToPagesTall = False: setup.Zoom = zoom
    setup.ScaleWithDocHeaderFooter = False: setup.AlignMarginsHeaderFooter = True
    setup.PrintTitleRows = "$1:$4": setup.CenterFooter = "&""メイリオ,Regular""&11" & footer
    capacity = Fix(((841.88976 - 85.03937 - 72) / (zoom / 100#) - CDbl(ws.Rows("1:4").Height)) / 18) - 1
    If capacity > 32 Then capacity = 32
    If capacity < 12 Then Reject "MSG-037"
    pageCaps.Add ws.Name, capacity: pageEnds.Add ws.Name, 5 + capacity: pagePlans.Add ws.Name, planned
    caseContexts.Add ws.Name, Array("", ""): sectionContexts.Add ws.Name, ""
    Set setup = Nothing
End Sub
Private Sub ApplyPages(ByVal ws As Object, ByVal lastRow As Long, Optional ByVal createBreaks As Boolean = True)
    Dim planned As Collection, row As Variant, actual As Object, page As Object, previous As String, signature As String, retry As Long
    Set planned = pagePlans(ws.Name)
    If createBreaks Then
        ws.ResetAllPageBreaks
        For Each row In planned: ws.HPageBreaks.Add ws.Cells(CLng(row), 1): Next
    End If
    ws.DisplayPageBreaks = True
    For Each page In ws.VPageBreaks
        If page.Location.Column > 1 And page.Location.Column <= 24 Then Reject "MSG-037"
    Next
    For retry = 1 To 3
        Set actual = CreateObject("Scripting.Dictionary"): signature = ""
        For Each page In ws.HPageBreaks
            If page.Location.row > 4 And page.Location.row <= lastRow Then
                actual.Add CStr(page.Location.row), True: signature = signature & CStr(page.Location.row) & ";"
            End If
        Next
        If actual.Count <> planned.Count Then Reject "MSG-037"
        For Each row In planned
            If Not actual.Exists(CStr(row)) Then Reject "MSG-037"
        Next
        If ws.PageSetup.Pages.Count <> planned.Count + 1 Then Reject "MSG-037"
        If ws.PageSetup.Zoom < 100 Then Reject "MSG-037"
        If retry > 1 And signature = previous Then Exit For
        previous = signature
    Next
    If retry > 3 Then Reject "MSG-037"
End Sub
Private Sub VerifyBook(ByVal book As Object, ByVal expected As Collection)
    Dim item As Variant, ws As Object, links As Variant, values As Variant, row As Long, col As Long, formula As Variant, restored As Object, key As Variant
    If book.Worksheets.Count <> 2 Or book.Sheets.Count <> 2 Then Reject "MSG-037"
    If book.Worksheets(1).Name <> "職務経歴書" Or book.Worksheets(2).Name <> "案件経歴" Then Reject "MSG-037"
    If book.Connections.Count <> 0 Or book.HasVBProject Then Reject "MSG-037"
    links = book.LinkSources(1): If Not IsEmpty(links) Then Reject "MSG-037"
    Set restored = CreateObject("Scripting.Dictionary")
    For Each ws In book.Worksheets
        If ws.Visible <> -1 Then Reject "MSG-037"
        formula = ws.UsedRange.HasFormula
        If IsNull(formula) Then Reject "MSG-037"
        If CBool(formula) Then Reject "MSG-037"
        ApplyPages ws, CLng(ws.UsedRange.Rows.Count), False
        ' Read/copy the bulk array once per sheet, not once per expected cell.
        values = ws.UsedRange.Value2
        For Each item In expected
            If CStr(item(0)) = CStr(ws.Name) Then
                row = CLng(Mid$(CStr(item(1)), 2)): col = IIf(Left$(CStr(item(1)), 1) = "A", 1, 7)
                If CStr(Nz(values(row, col), "")) <> CStr(item(2)) Then Reject "MSG-037"
                If Len(CStr(item(2))) > 0 Then If VarType(values(row, col)) <> vbString Then Reject "MSG-037"
                If CLng(item(3)) > 0 Then
                    key = CStr(item(3))
                    If Not restored.Exists(key) Then restored.Add key, ""
                    restored(key) = CStr(restored(key)) & CStr(item(4)) & CStr(Nz(values(row, col), ""))
                End If
            End If
        Next
    Next
    For Each key In originalText.Keys
        If Not restored.Exists(key) Then Reject "MSG-037"
        If StrComp(CStr(restored(key)), CStr(originalText(key)), vbBinaryCompare) <> 0 Then Reject "MSG-037"
    Next
    Set ws = Nothing: values = Empty
End Sub
Private Function FileStamp(ByVal path As String) As String
    If Len(Dir$(path)) = 0 Then Exit Function
    FileStamp = CStr(FileLen(path)) & "/" & CStr(CDbl(FileDateTime(path))) & "/" & FileContentHash(path)
End Function
Public Function ExportCareer(ByVal employeeId As Long, ByVal session As clsSession, Optional ByVal verificationPath As String = "") As clsResult
    Dim snapshot As clsReportSnapshot, result As clsResult, xl As Object, book As Object, cover As Object, careers As Object, expected As New Collection
    Dim c As clsCareerDraft, row As Long, ordinal As Long, months As Long, finish As Date, period As String, path As Variant, target As String, temporary As String, request As String, ownerRequest As String, overwrite As Boolean, stamp As String, u As clsUnitOfWork, text As String, published As Boolean, dot As Long, pageCount As Long, newPageCount As Long, retry As Long, ownedTemps As New Collection, ownedPath As Variant, face As String
    On Error GoTo Failed
    If exportRunning Then Set ExportCareer = MakeResult("Busy", "MSG-029"): Exit Function
    exportRunning = True: request = NewRequestId(): ownerRequest = request: exportRequest = request
    Set result = ReadReport(employeeId, session): If result.Kind <> "OK" Then Set ExportCareer = result: GoTo Cleanup
    Set snapshot = result.Value
    Set originalText = CreateObject("Scripting.Dictionary"): Set rowStyles = CreateObject("Scripting.Dictionary")
    Set pagePlans = CreateObject("Scripting.Dictionary"): Set pageEnds = CreateObject("Scripting.Dictionary"): Set pageCaps = CreateObject("Scripting.Dictionary")
    Set caseContexts = CreateObject("Scripting.Dictionary"): Set sectionContexts = CreateObject("Scripting.Dictionary"): textGroup = 0
    Set xl = CreateObject("Excel.Application"): xl.Visible = False: xl.DisplayAlerts = False: xl.EnableEvents = False
    Set book = xl.Workbooks.Add(-4167): Set cover = book.Worksheets(1): cover.Name = "職務経歴書"
    book.Styles("Normal").Font.Name = "メイリオ": book.Styles("Normal").Font.Size = 10.5
    Set careers = book.Worksheets.Add(, cover): careers.Name = "案件経歴"
    ConfigureSheet cover, "職務経歴書", snapshot, expected: ConfigureSheet careers, "案件経歴", snapshot, expected
    row = 5
    WriteBlock cover, row, "氏名", snapshot.Employee.Name & "（" & snapshot.Employee.Kana & "）", expected
    WriteBlock cover, row, "社員番号／所属", snapshot.Employee.EmployeeNo & " ／ " & snapshot.Names("DEPARTMENT/" & snapshot.Employee.Department), expected
    If row < 8 Then row = 8
    WriteWideBlock cover, row, "職務要約", snapshot.Employee.Summary, expected
    WriteWideBlock cover, row, "活かせる経験・知識・技術", snapshot.Employee.Skills, expected
    WriteWideBlock cover, row, "資格", snapshot.Employee.Qualifications, expected
    WriteWideBlock cover, row, "自己PR", snapshot.Employee.SelfPr, expected
    cover.PageSetup.PrintArea = "$A$1:$X$" & CStr(row - 1)
    row = 5
    For Each c In snapshot.Employee.Careers
        ordinal = ordinal + 1: finish = DateSerial(Year(snapshot.BusinessDate), Month(snapshot.BusinessDate), 1)
        If Not IsNull(c.EndMonth) Then finish = c.EndMonth
        months = DateDiff("m", c.StartMonth, finish) + 1
        period = Format$(c.StartMonth, "yyyy年mm月") & " ～ " & IIf(IsNull(c.EndMonth), "現在", Format$(finish, "yyyy年mm月")) & "（" & CStr(months \ 12) & "年" & CStr(months Mod 12) & "か月）"
        BeginCase careers, row, ordinal, c.Project, expected
        WriteBlock careers, row, Format$(ordinal, "00") & " 案件", c.Project, expected, True
        WriteBlock careers, row, "期間", period, expected
        WriteBlock careers, row, "会社名", c.Company, expected
        WriteBlock careers, row, "業務概要", c.Description, expected
        WriteBlock careers, row, "担当業務", c.Duties, expected
        WriteBlock careers, row, "担当工程", c.Phases, expected
        WriteBlock careers, row, "成果・工夫", c.Achievements, expected
        WriteBlock careers, row, "使用技術", c.Technologies, expected
        WriteBlock careers, row, "役割／人数", snapshot.Names("PROJECT_ROLE/" & c.RoleCode) & " ／ " & CStr(c.TeamSize) & "人", expected
        If row < CLng(pageEnds(careers.Name)) Then row = row + 1
    Next
    careers.PageSetup.PrintArea = "$A$1:$X$" & CStr(row - 1)
    FlushText cover, expected: FlushText careers, expected
    ApplyPages cover, CLng(cover.UsedRange.Rows.Count)
    ApplyPages careers, CLng(careers.UsedRange.Rows.Count)
    VerifyBook book, expected: Checkpoint
    Set result = Authorize("STAFF"): If result.Kind <> "OK" Then Set ExportCareer = result: GoTo Cleanup
ChoosePath:
    If verificationPath <> "" Then
        ' Explicit destination is restricted to owned test copies, never normal distribution.
        If InStr(1, CurrentProject.FullName, "\.tmp\", vbTextCompare) = 0 Or InStr(1, verificationPath, "\.tmp\", vbTextCompare) = 0 Then Reject "MSG-013"
        path = verificationPath
    Else
        path = xl.GetSaveAsFilename("職務経歴書_" & snapshot.Employee.EmployeeNo & "_" & Format$(snapshot.BusinessDate, "yyyymmdd") & ".xlsx", "Excel (*.xlsx), *.xlsx", , "経歴書の保存先")
        If VarType(path) = vbBoolean Then Reject "MSG-030"
    End If
    target = CStr(path)
    If LCase$(Right$(target, 5)) <> ".xlsx" Then Reject "MSG-013"
    overwrite = (Len(Dir$(target)) > 0): stamp = FileStamp(target)
    If overwrite Then
        If MsgBox("同名のファイルを上書きしますか。", vbYesNo + vbQuestion + vbDefaultButton2) <> vbYes Then GoTo ChoosePath
    End If
    dot = InStrRev(target, "\"): If dot = 0 Then Reject "MSG-013"
    temporary = Left$(target, dot) & ".sp2_" & request & ".xlsx"
    If Len(Dir$(temporary)) > 0 Then Reject "MSG-013"
    ownedTemps.Add temporary
    book.SaveAs temporary, 51, , , False, False, , , , , , False
    book.Close False: Set book = Nothing: Set cover = Nothing: Set careers = Nothing
    Set book = xl.Workbooks.Open(temporary, 0, True): VerifyBook book, expected
    book.Close False: Set book = Nothing: xl.Quit: Set xl = Nothing
    Checkpoint
ReconfirmDestination:
    If FileStamp(target) <> stamp Then
        If verificationPath <> "" Then Reject "MSG-013"
        If MsgBox("保存先のファイルが変更されています。現在のファイルを上書きしますか。", vbYesNo + vbQuestion + vbDefaultButton2) <> vbYes Then
            Set xl = CreateObject("Excel.Application"): xl.Visible = False: xl.DisplayAlerts = False: xl.EnableEvents = False
            Set book = xl.Workbooks.Open(temporary, 0, True)
            request = NewRequestId(): temporary = "": GoTo ChoosePath
        End If
        overwrite = (Len(Dir$(target)) > 0): stamp = FileStamp(target)
    End If
    Set u = New clsUnitOfWork: u.OpenUnit True: RequireCurrent session, "STAFF", u.Db
    If FileStamp(target) <> stamp Then u.Cancel: u.CloseUnit: GoTo ReconfirmDestination
    If gExportCancel Then Reject "MSG-030"
    If MoveFileExW(StrPtr(temporary), StrPtr(target), IIf(overwrite, 9, 8)) = 0 Then Reject "MSG-013"
    published = True: temporary = "": u.Commit: u.CloseUnit
    Set ExportCareer = MakeResult("OK", "MSG-014")
    GoTo Cleanup
Failed:
    text = Err.Description
    If Left$(text, 4) <> "MSG-" Then text = "MSG-013"
    If Not u Is Nothing Then u.Cancel: u.CloseUnit
    If published Then
        Set ExportCareer = MakeResult("OK", "MSG-014")
    Else
        Select Case text
        Case "MSG-002": Set ExportCareer = MakeResult("AuthExpired", text)
        Case "MSG-003": Set ExportCareer = MakeResult("Forbidden", text)
        Case "MSG-020": Set ExportCareer = MakeResult("Integrity", text)
        Case "MSG-027", "MSG-029": Set ExportCareer = MakeResult("Busy", text)
        Case "MSG-030": Set ExportCareer = MakeResult("Cancelled", text)
        Case Else: Set ExportCareer = MakeResult("ReportFailure", text)
        End Select
    End If
Cleanup:
    On Error Resume Next
    If Not book Is Nothing Then book.Close False
    Set book = Nothing: Set cover = Nothing: Set careers = Nothing
    If Not xl Is Nothing Then xl.Quit
    Set xl = Nothing
    For Each ownedPath In ownedTemps
        If CStr(ownedPath) <> target Then If Len(Dir$(CStr(ownedPath))) > 0 Then Kill CStr(ownedPath)
    Next
    If measureDC <> 0 And previousFont <> 0 Then SelectObject measureDC, previousFont
    If measureFont <> 0 Then DeleteObject measureFont
    If measureDC <> 0 Then DeleteDC measureDC
    measureDC = 0: measureFont = 0: previousFont = 0
    Set originalText = Nothing: Set rowStyles = Nothing: Set pagePlans = Nothing: Set pageEnds = Nothing: Set pageCaps = Nothing
    Set caseContexts = Nothing: Set sectionContexts = Nothing
    If exportRequest = ownerRequest Then exportRunning = False: exportRequest = ""
End Function
