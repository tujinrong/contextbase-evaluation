using System.Globalization;
using System.IO.Compression;
using System.Runtime.InteropServices;
using System.Text;
using System.Xml.Linq;
using CareerManagement.Application;
using ClosedXML.Excel;

namespace CareerManagement.Infrastructure.Reports;

public interface ITextWidthMeasurer { double Width(string text); }
public sealed class GdiTextWidthMeasurer:ITextWidthMeasurer
{
    public double Width(string text)
    {
        if(!OperatingSystem.IsWindows())throw BusinessException.Error(13);
        var dc=CreateCompatibleDC(IntPtr.Zero);if(dc==IntPtr.Zero)throw BusinessException.Error(13);
        var font=CreateFontW(-14,0,0,0,400,0,0,0,1,0,0,5,0,"Meiryo");
        if(font==IntPtr.Zero){DeleteDC(dc);throw BusinessException.Error(13);}
        var old=SelectObject(dc,font);
        try
        {
            var face=new StringBuilder(80);
            if(GetTextFaceW(dc,80,face)==0||!(face.ToString().Equals("Meiryo",StringComparison.OrdinalIgnoreCase)||face.ToString()=="メイリオ"))throw BusinessException.Error(13);
            if(!GetTextExtentPoint32W(dc,text,text.Length,out var size))throw BusinessException.Error(13);
            return size.Cx;
        }
        finally {SelectObject(dc,old);DeleteObject(font);DeleteDC(dc);}
    }
    [StructLayout(LayoutKind.Sequential)]private struct Size {public int Cx;public int Cy;}
    [DllImport("gdi32.dll")]private static extern IntPtr CreateCompatibleDC(IntPtr hdc);
    [DllImport("gdi32.dll")]private static extern bool DeleteDC(IntPtr hdc);
    [DllImport("gdi32.dll")]private static extern bool DeleteObject(IntPtr value);
    [DllImport("gdi32.dll")]private static extern IntPtr SelectObject(IntPtr dc,IntPtr value);
    [DllImport("gdi32.dll",CharSet=CharSet.Unicode)]private static extern IntPtr CreateFontW(int height,int width,int angle,int orientation,int weight,uint italic,uint underline,uint strike,uint charset,uint output,uint clip,uint quality,uint pitch,string face);
    [DllImport("gdi32.dll",CharSet=CharSet.Unicode)]private static extern bool GetTextExtentPoint32W(IntPtr dc,string value,int length,out Size size);
    [DllImport("gdi32.dll",CharSet=CharSet.Unicode)]private static extern int GetTextFaceW(IntPtr dc,int count,StringBuilder name);
}
public sealed record TextSlice(string Text,string FollowingSeparator);
public static class ReportText
{
    // Published ClosedXML 0.105.1 Value strips exactly one initial apostrophe.
    public static void SetExact(IXLCell cell,string text)
    {
        cell.Style.NumberFormat.Format="@";
        cell.Value=text.StartsWith('\'')?"'"+text:text;
        cell.Style.IncludeQuotePrefix=false;
        if(cell.GetText()!=text||cell.HasFormula)throw BusinessException.Error(37);
    }
    public static IReadOnlyList<TextSlice> Split(string value,double maxPixels,ITextWidthMeasurer measure)
    {
        var result=new List<TextSlice>();var logical=value.Split('\n');
        for(var line=0;line<logical.Length;line++)
        {
            var current=new StringBuilder();var enumerator=StringInfo.GetTextElementEnumerator(logical[line]);
            while(enumerator.MoveNext())
            {
                var element=enumerator.GetTextElement();var candidate=current.ToString()+element;
                if(current.Length>0&&(Validation.ScalarLength(candidate)>32||measure.Width(candidate)>maxPixels))
                {result.Add(new(current.ToString(),""));current.Clear();}
                if(measure.Width(element)>maxPixels)throw BusinessException.Error(13);
                current.Append(element);
            }
            result.Add(new(current.ToString(),line<logical.Length-1?"\n":""));
        }
        if(string.Concat(result.Select(x=>x.Text+x.FollowingSeparator))!=value)throw BusinessException.Error(37);
        return result;
    }
}
public sealed class ReportService(ITextWidthMeasurer measure)
{
    private sealed record CellProof(string Sheet,string Address,string Value);
    private sealed record FieldProof(string Original,IReadOnlyList<(CellProof Cell,string Separator)> Slices);
    private sealed class PageFlow { public int Row {get;set;}=3; public double UsedPoints {get;set;}=39; }
    public MemoryStream Create(ReportSnapshot snapshot,CancellationToken ct)
    {
        try
        {
            var proofs=new List<CellProof>();var fields=new List<FieldProof>();
            using var book=new XLWorkbook();var main=book.AddWorksheet("職務経歴書");var career=book.AddWorksheet("案件経歴");
            var local=TimeZoneInfo.ConvertTime(snapshot.Captured.Utc,TimeZoneInfo.FindSystemTimeZoneById("Tokyo Standard Time"));
            var date=snapshot.Captured.Date.ToString("yyyy年MM月dd日",CultureInfo.InvariantCulture)+"現在";
            var stamp="作成日時（JST）："+local.ToString("yyyy年MM月dd日 HH:mm",CultureInfo.InvariantCulture);
            var employee=snapshot.Employee.Employee;
            var navy=XLColor.FromHtml("#173650");var gray=XLColor.FromHtml("#AEB8C5");
            foreach(var sheet in book.Worksheets)
            {
                sheet.Columns(1,24).Width=3;sheet.Rows().Height=15;
                sheet.Style.Font.FontName="Meiryo";sheet.Style.Font.FontSize=10.5;
                sheet.Style.Font.FontColor=XLColor.FromHtml("#202B38");sheet.Style.Fill.BackgroundColor=XLColor.White;
                sheet.Style.Alignment.Vertical=XLAlignmentVerticalValues.Top;
                sheet.PageSetup.PaperSize=XLPaperSize.A4Paper;sheet.PageSetup.PageOrientation=XLPageOrientation.Portrait;
                sheet.PageSetup.Margins.Top=sheet.PageSetup.Margins.Bottom=sheet.PageSetup.Margins.Left=sheet.PageSetup.Margins.Right=15/25.4;
                sheet.PageSetup.Margins.Header=sheet.PageSetup.Margins.Footer=7/25.4;sheet.PageSetup.FitToPages(1,0);
                var footerLines=ReportText.Split(employee.Name,530,measure).Select(x=>x.Text).ToList();
                footerLines.Add(sheet.Name+" ／ "+stamp);
                sheet.PageSetup.Footer.Center.AddText(string.Join("\n",footerLines).Replace("&","&&",StringComparison.Ordinal)).FontSize=10.5;
                sheet.PageSetup.Footer.Right.AddText(XLHFPredefinedText.PageNumber);sheet.PageSetup.Footer.Right.AddText(" / ");sheet.PageSetup.Footer.Right.AddText(XLHFPredefinedText.NumberOfPages);
            }
            void Cell(IXLWorksheet sheet,int row,int start,int end,string value,double size=10.5)
            {
                ct.ThrowIfCancellationRequested();var range=sheet.Range(row,start,row,end);range.Merge();range.Style.Font.FontSize=size;
                range.Style.Font.Bold=size>=11;
                if(size>=11)range.Style.Font.FontColor=navy;
                var cell=range.FirstCell();ReportText.SetExact(cell,value);proofs.Add(new(sheet.Name,cell.Address.ToStringRelative(),value));
            }
            void HeadingLine(IXLWorksheet sheet,int row)
            {
                var border=sheet.Range(row,1,row,24).Style.Border;
                border.BottomBorder=XLBorderStyleValues.Medium;border.BottomBorderColor=navy;
            }
            void TableBorders(IXLWorksheet sheet,int row)
            {
                foreach(var range in new[]{sheet.Range(row,1,row,6),sheet.Range(row,7,row,24)})
                {range.Style.Border.OutsideBorder=XLBorderStyleValues.Thin;range.Style.Border.OutsideBorderColor=gray;}
            }
            void Title(IXLWorksheet sheet,string value)
            {
                sheet.Range(1,1,2,24).Merge();ReportText.SetExact(sheet.Cell(1,1),value);sheet.Cell(1,1).Style.Font.FontSize=18;sheet.Cell(1,1).Style.Font.Bold=true;sheet.Cell(1,1).Style.Font.FontColor=navy;
                proofs.Add(new(sheet.Name,"A1",value));sheet.Row(1).Height=21;sheet.Row(2).Height=18;
            }
            // A4 841.89pt - top15mm42.52pt - bottom15mm42.52pt = 756.85pt.
            // Three footer lines begin above the nominal bottom margin. Reserve a further 56.85pt:
            // explicit page body <=700pt, including 21+18pt title rows and every continuation line.
            // No blank rows are inserted to reach a modulo boundary (that produced empty printed pages).
            const double pageBodyPoints=700;
            void Ensure(IXLWorksheet sheet,PageFlow flow,double needed,string? continuation=null)
            {
                if(flow.UsedPoints+needed<=pageBodyPoints)return;
                sheet.PageSetup.AddHorizontalPageBreak(flow.Row-1);flow.UsedPoints=0;
                if(continuation is not null)
                {
                    foreach(var slice in ReportText.Split(continuation+"（続き）",630*10.5/11,measure))
                    {
                        Cell(sheet,flow.Row++,1,24,slice.Text,11);flow.UsedPoints+=15;
                    }
                    HeadingLine(sheet,flow.Row-1);
                }
                if(flow.UsedPoints+needed>pageBodyPoints)throw BusinessException.Error(13);
            }
            void Spacer(PageFlow flow)
            {if(flow.UsedPoints+15<=pageBodyPoints){flow.Row++;flow.UsedPoints+=15;}}
            // 24 columns at width3 are approximately669px; conservative GDI budgets are630/465px.
            void Field(IXLWorksheet sheet,PageFlow flow,string label,string? text,bool full=false,string? continuation=null,double size=10.5)
            {
                var value=text??"";
                // GDI uses the body10.5pt font. Reserve the proportional width when rendering11pt headings.
                var pixels=(full?630:465)*10.5/size;
                var slices=ReportText.Split(value,pixels,measure);var evidence=new List<(CellProof,string)>();
                for(var i=0;i<slices.Count;i++)
                {
                    ct.ThrowIfCancellationRequested();
                    Ensure(sheet,flow,15,continuation??label);
                    if(!full)Cell(sheet,flow.Row,1,6,i==0?label:label+"（続き）",size);
                    var col=full?1:7;Cell(sheet,flow.Row,col,24,slices[i].Text,size);
                    if(!full)TableBorders(sheet,flow.Row);
                    if(size>=11&&i==slices.Count-1)HeadingLine(sheet,flow.Row);
                    evidence.Add((new(sheet.Name,sheet.Cell(flow.Row,col).Address.ToStringRelative(),slices[i].Text),slices[i].FollowingSeparator));flow.Row++;flow.UsedPoints+=15;
                }
                fields.Add(new(value,evidence));
            }
            Title(main,"職務経歴書");var mainFlow=new PageFlow();Field(main,mainFlow,"基準日",date,true);Field(main,mainFlow,"作成日時",stamp,true);
            Field(main,mainFlow,"氏名",employee.Name+"（"+employee.Kana+"）");
            var dep=snapshot.Codes.Single(x=>x.Category=="DEPARTMENT"&&x.Code==employee.DepartmentCode).Name;
            Field(main,mainFlow,"社員番号・所属",employee.EmployeeNo+" ／ "+dep);Spacer(mainFlow);
            while(mainFlow.Row<8)Spacer(mainFlow);
            foreach(var block in new[]{("職務要約",employee.CareerSummary),("活かせる経験・知識・技術",employee.Skills),("資格",employee.Qualifications),("自己PR",employee.SelfPr)})
            {
                Ensure(main,mainFlow,30);Cell(main,mainFlow.Row,1,24,block.Item1,11);HeadingLine(main,mainFlow.Row++);mainFlow.UsedPoints+=15;
                Field(main,mainFlow,block.Item1,block.Item2,true);Spacer(mainFlow);
            }
            main.PageSetup.PrintAreas.Add(1,1,mainFlow.Row-1,24);
            Title(career,"案件経歴");var careerFlow=new PageFlow();Field(career,careerFlow,"氏名・基準日",employee.Name+" ／ "+date,true);Field(career,careerFlow,"作成日時",stamp,true);
            var ordered=snapshot.Employee.Careers.OrderByDescending(x=>x.Values.StartMonth).ThenByDescending(x=>x.CareerId).ToArray();
            for(var i=0;i<ordered.Length;i++)
            {
                ct.ThrowIfCancellationRequested();var v=ordered[i].Values;var heading=$"{i+1:00}　{v.ProjectName}";
                var headingLines=ReportText.Split(heading,465*10.5/11,measure).Count;
                Ensure(career,careerFlow,(headingLines+1)*15,heading);
                Field(career,careerFlow,"案件連番・案件名",heading,false,heading,11);
                var end=v.EndMonth??snapshot.Captured.Month;var months=(end.Year-v.StartMonth.Year)*12+end.Month-v.StartMonth.Month+1;
                var period=v.StartMonth.ToString("yyyy年MM月",CultureInfo.InvariantCulture)+"～"+(v.EndMonth?.ToString("yyyy年MM月",CultureInfo.InvariantCulture)??"現在")+$"（{months}か月）";
                Field(career,careerFlow,"期間",period,false,heading);
                foreach(var block in new[]{("所属会社",v.CompanyName),("概要",v.Description),("担当業務",v.Duties),("工程",v.Phases),("実績・工夫",v.Achievements),("開発環境",v.Technologies)})
                    Field(career,careerFlow,block.Item1,block.Item2,false,heading);
                var role=snapshot.Codes.Single(x=>x.Category=="PROJECT_ROLE"&&x.Code==v.RoleCode).Name;
                Field(career,careerFlow,"役割・人数",role+$" ／ {v.TeamSize}名",false,heading);Spacer(careerFlow);
            }
            career.PageSetup.PrintAreas.Add(1,1,careerFlow.Row-1,24);
            // Excel may replace an inherited default height with 17.25pt for Meiryo.
            // Persist ht/customHeight on EVERY used row; page budgets must use actual row heights.
            for(var r=3;r<mainFlow.Row;r++)main.Row(r).Height=15;
            for(var r=3;r<careerFlow.Row;r++)career.Row(r).Height=15;
            var output=new MemoryStream();book.SaveAs(output);ct.ThrowIfCancellationRequested();
            if(output.Length>32L*1024*1024){output.Dispose();throw BusinessException.Error(13);}
            output.Position=0;
            using(var verify=new XLWorkbook(output))
            {
                if(!verify.Worksheets.Select(x=>x.Name).SequenceEqual(new[]{"職務経歴書","案件経歴"})||verify.Worksheets.Any(x=>x.Visibility!=XLWorksheetVisibility.Visible))throw BusinessException.Error(37);
                foreach(var proof in proofs)
                {
                    var cell=verify.Worksheet(proof.Sheet).Cell(proof.Address);
                    if(cell.GetText()!=proof.Value||cell.HasFormula||cell.DataType!=XLDataType.Text&&proof.Value.Length!=0)throw BusinessException.Error(37);
                }
                foreach(var field in fields)
                    if(string.Concat(field.Slices.Select(x=>verify.Worksheet(x.Cell.Sheet).Cell(x.Cell.Address).GetText()+x.Separator))!=field.Original)throw BusinessException.Error(37);
                if(verify.Worksheets.SelectMany(x=>x.CellsUsed()).Any(x=>x.HasFormula))throw BusinessException.Error(37);
            }
            output.Position=0;
            using(var zip=new ZipArchive(output,ZipArchiveMode.Read,true))
            {
                if(zip.Entries.Any(x=>x.FullName.Contains("vbaProject",StringComparison.OrdinalIgnoreCase)||x.FullName.Contains("externalLinks",StringComparison.OrdinalIgnoreCase)||x.FullName.Contains("connections",StringComparison.OrdinalIgnoreCase)))throw BusinessException.Error(37);
                XNamespace ns="http://schemas.openxmlformats.org/spreadsheetml/2006/main";
                foreach(var entry in zip.Entries.Where(x=>x.FullName.StartsWith("xl/worksheets/sheet",StringComparison.Ordinal)&&x.FullName.EndsWith(".xml",StringComparison.Ordinal)))
                {
                    using var xml=entry.Open();var document=XDocument.Load(xml);
                    foreach(var rowElement in document.Descendants(ns+"row"))
                    {
                        var index=(int?)rowElement.Attribute("r")??0;
                        var expected=index==1?21:index==2?18:15;
                        if((double?)rowElement.Attribute("ht")!=expected||(string?)rowElement.Attribute("customHeight")!="1")throw BusinessException.Error(37);
                    }
                }
            }
            output.Position=0;return output;
        }
        catch(BusinessException){throw;}
        catch(OperationCanceledException){throw;}
        catch {throw BusinessException.Error(13);}
    }
}
