using System.IO.Compression;
using System.Xml.Linq;
using ClosedXML.Excel;

static class IndependentReportChecks
{
    static readonly string[] Chapters = ["職務要約", "活かせる経験・知識・技術", "資格", "自己PR"];
    static void Need(bool value, string message) { if (!value) throw new InvalidOperationException(message); }
    static bool Meiryo(IXLFont font) => font.FontName is "Meiryo" or "メイリオ";
    public static IEnumerable<(string Id, Action Test)> Cases(XLWorkbook book, byte[] content, int careers)
    {
        var rowBorders = Borders(content);
        yield return ("full-width-chapters-and-body", () =>
        {
            var sheet = book.Worksheet(1);
            foreach (var name in Chapters)
            {
                var matches = sheet.CellsUsed().Where(x => x.GetText() == name).ToArray(); Need(matches.Length == 1, "Chapter missing or repeated: " + name);
                var cell = matches[0]; var row = cell.Address.RowNumber; var merged = cell.MergedRange();
                Need(cell.Address.ColumnNumber == 1 && merged.RangeAddress.FirstAddress.ColumnNumber == 1 && merged.RangeAddress.LastAddress.ColumnNumber == 24 && merged.RowCount() == 1, "Chapter must use one A:X heading row: " + name);
                Need(Meiryo(cell.Style.Font) && cell.Style.Font.FontSize == 11 && cell.Style.Font.Bold, "Chapter must be Meiryo11pt bold: " + name);
                var body = sheet.Cell(row + 1, 1); var bodyRange = body.MergedRange();
                Need(bodyRange.RangeAddress.FirstAddress.ColumnNumber == 1 && bodyRange.RangeAddress.LastAddress.ColumnNumber == 24 && bodyRange.RowCount() == 1, "First body line must be next row A:X: " + name);
                Need(Meiryo(body.Style.Font) && body.Style.Font.FontSize == 10.5, "Body must be Meiryo10.5pt: " + name);
            }
        });
        yield return ("project-headings-eleven-bold", () =>
        {
            var sheet = book.Worksheet(2); var first = sheet.CellsUsed().Where(x => x.GetText() == "案件連番・案件名").ToArray();
            Need(first.Length == careers, "Wrong initial project heading count");
            foreach (var label in sheet.CellsUsed().Where(x => x.GetText().StartsWith("案件連番・案件名", StringComparison.Ordinal)))
            {
                var value = sheet.Cell(label.Address.RowNumber, 7);
                Need(Meiryo(label.Style.Font) && label.Style.Font.FontSize == 11 && label.Style.Font.Bold && Meiryo(value.Style.Font) && value.Style.Font.FontSize == 11 && value.Style.Font.Bold, "Initial/wrapped project heading must be11pt bold at row " + label.Address.RowNumber);
            }
        });
        yield return ("navy-section-and-project-lines", () =>
        {
            foreach (var sheet in book.Worksheets)
            foreach (var cell in sheet.CellsUsed().Where(x => Chapters.Contains(x.GetText(), StringComparer.Ordinal) || x.GetText() == "案件連番・案件名"))
            {
                var first = cell.Address.RowNumber; var last = first;
                if (cell.GetText() == "案件連番・案件名") while (sheet.Cell(last + 1, 1).GetText().StartsWith("案件連番・案件名（続き）", StringComparison.Ordinal)) last++;
                Need(Enumerable.Range(first, last - first + 1).Any(row => rowBorders[sheet.Position].TryGetValue(row, out var colors) && colors.Contains("173650")), "Missing navy heading-block bottom line: " + sheet.Name + " " + cell.Address);
            }
        });
        yield return ("gray-table-outlines", () =>
        {
            string[] labels = ["氏名", "社員番号・所属", "期間", "所属会社", "役割・人数"];
            foreach (var sheet in book.Worksheets)
            {
                var cells = sheet.CellsUsed().Where(x => x.Address.ColumnNumber == 1 && labels.Contains(x.GetText(), StringComparer.Ordinal)).ToArray();
                Need(cells.Length >= 2, "Table fixture is missing: " + sheet.Name);
                foreach (var cell in cells) Need(rowBorders[sheet.Position].TryGetValue(cell.Address.RowNumber, out var colors) && colors.Contains("aeb8c5"), "Missing gray table outline: " + sheet.Name + " " + cell.Address);
            }
        });
        yield return ("paper-column-row-geometry", () =>
        {
            foreach (var sheet in book.Worksheets)
            {
                Need(sheet.PageSetup.PaperSize == XLPaperSize.A4Paper && sheet.PageSetup.PageOrientation == XLPageOrientation.Portrait, "A4 portrait changed");
                Need(sheet.PageSetup.PagesWide == 1 && sheet.PageSetup.PagesTall == 0, "One-width/automatic-height print setting changed");
                Need(new[] { sheet.PageSetup.Margins.Left, sheet.PageSetup.Margins.Right, sheet.PageSetup.Margins.Top, sheet.PageSetup.Margins.Bottom }.All(x => Math.Abs(x - 15 / 25.4) < .0001), "15mm margins changed");
                Need(Math.Abs(sheet.PageSetup.Margins.Header - 7 / 25.4) < .0001 && Math.Abs(sheet.PageSetup.Margins.Footer - 7 / 25.4) < .0001, "7mm header/footer changed");
                Need(Enumerable.Range(1, 24).All(x => Math.Abs(sheet.Column(x).Width - 3) < .0001), "24 columns at width3 changed");
                Need(sheet.Row(1).Height == 21 && sheet.Row(2).Height == 18 && Enumerable.Range(3, sheet.LastRowUsed()!.RowNumber() - 2).All(r => sheet.Row(r).Height == 15), "Explicit21/18/15pt row geometry changed");
                Need(sheet.Cell(1, 1).Style.Font.FontSize == 18 && Meiryo(sheet.Cell(1, 1).Style.Font), "18pt Meiryo title changed");
            }
        });
        yield return ("white-paper-and-body-font", () =>
        {
            foreach (var sheet in book.Worksheets)
            foreach (var cell in sheet.CellsUsed())
            {
                Need(Meiryo(cell.Style.Font) && cell.Style.Font.FontSize is 10.5 or 11 or 18, "Unexpected paper font: " + sheet.Name + " " + cell.Address);
                Need(cell.Style.Fill.PatternType == XLFillPatternValues.None || cell.Style.Fill.PatternType == XLFillPatternValues.Solid && cell.Style.Fill.BackgroundColor.Equals(XLColor.White), "Paper background is not white: " + sheet.Name + " " + cell.Address);
            }
        });
    }
    static Dictionary<int, Dictionary<int, HashSet<string>>> Borders(byte[] bytes)
    {
        using var stream = new MemoryStream(bytes); using var zip = new ZipArchive(stream, ZipArchiveMode.Read);
        XNamespace ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main";
        XDocument Read(string path) { using var entry = zip.GetEntry(path)!.Open(); return XDocument.Load(entry); }
        var styles = Read("xl/styles.xml"); var borders = styles.Root!.Element(ns + "borders")!.Elements().ToArray(); var formats = styles.Root.Element(ns + "cellXfs")!.Elements().ToArray();
        var result = new Dictionary<int, Dictionary<int, HashSet<string>>>();
        for (var i = 1; i <= 2; i++)
        {
            var rows = new Dictionary<int, HashSet<string>>();
            foreach (var row in Read($"xl/worksheets/sheet{i}.xml").Descendants(ns + "row"))
            {
                var colors = new HashSet<string>(StringComparer.OrdinalIgnoreCase); rows[(int)row.Attribute("r")!] = colors;
                foreach (var cell in row.Elements(ns + "c"))
                {
                    var border = borders[(int?)formats[(int?)cell.Attribute("s") ?? 0].Attribute("borderId") ?? 0];
                    foreach (var side in border.Elements().Where(x => x.Attribute("style") is not null))
                    {
                        var rgb = (string?)side.Element(ns + "color")?.Attribute("rgb"); if (rgb is { Length: >= 6 }) colors.Add(rgb[^6..]);
                    }
                }
            }
            result[i] = rows;
        }
        return result;
    }
}
