"""Probe Excel footer formatting semantics, not product/PH07 acceptance."""
from pathlib import Path
import sys,json,hashlib,datetime
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import build
from pypdf import PdfReader
def main():
    work=ROOT/'.tmp/build-agent/ui-regeneration/print-format';work.mkdir(parents=True,exist_ok=True)
    before=set(build.win32process.EnumProcesses());app=book=ws=None;handle=None;records=[]
    build.pythoncom.CoInitialize()
    try:
        app=build.win32com.client.gencache.EnsureDispatch(build.win32com.client.DispatchEx('Excel.Application'))
        app.Visible=False;app.DisplayAlerts=False;app.EnableEvents=False
        pid=build.win32process.GetWindowThreadProcessId(app.Hwnd)[1]
        if pid in before:raise RuntimeError('Excel not newly owned')
        handle=build.win32api.OpenProcess(0x100000|0x400,False,pid)
        print(json.dumps({'step':'owned-print-probe','pid':pid}),flush=True)
        numeric='--numeric-only' in sys.argv
        numeric_name='1234567890123456789012345678901234567890'
        cases=[('10_5','10.5','&"Meiryo,Regular"&10.5Footer TEST SIZE 10.5\nSECOND FOOTER LINE'),('11','11','&"Meiryo,Regular"&11Footer TEST SIZE 11\nSECOND FOOTER LINE')]
        if numeric:
            cases=[('11-numeric-direct','11','&"Meiryo,Regular"&11'+numeric_name+'\nSECOND FOOTER LINE'),('11-numeric-delimited','11','&11&"Meiryo,Regular"'+numeric_name+'\nSECOND FOOTER LINE')]
        for label,size,text in cases:
            book=app.Workbooks.Add(-4167);ws=book.Worksheets(1)
            ws.Range('A1').Value2='Print formatting probe';ws.Range('A1').Font.Name='Meiryo';ws.Range('A1').Font.Size=10.5
            setup=ws.PageSetup;setup.PaperSize=9;setup.Orientation=1;setup.Zoom=100
            setup.LeftMargin=42.519685;setup.RightMargin=42.519685;setup.TopMargin=42.519685;setup.BottomMargin=42.519685
            setup.FooterMargin=19.84252;setup.PrintArea='$A$1:$X$5'
            setup.ScaleWithDocHeaderFooter=False;setup.AlignMarginsHeaderFooter=True
            setup.CenterFooter=text
            path=work/('footer-'+label+'.pdf')
            if path.exists():path.unlink()
            print(json.dumps({'step':'ExportAsFixedFormat:before','size':size}),flush=True)
            ws.ExportAsFixedFormat(0,str(path),0,True,False)
            readback=setup.CenterFooter;setup=None;ws=None
            book.Close(False);book=None
            spans=[]
            for page in PdfReader(str(path)).pages:
                def visitor(text,cm,tm,font,font_size):
                    if text.strip():spans.append({'text':text.strip(),'fontSize':font_size,'textMatrix':tm,'fontName':str((font or {}).get('/BaseFont',''))})
                page.extract_text(visitor_text=visitor)
            records.append({'case':label,'requestedSize':size,'expectedNumericName':numeric_name if numeric else 'NOT_APPLICABLE','readback':readback,'pdf':path.name,'pdfSha256':hashlib.sha256(path.read_bytes()).hexdigest(),'spans':spans})
        app.Quit();app=None;build.release()
        wait=build.win32event.WaitForSingleObject(handle,10000);code=build.win32process.GetExitCodeProcess(handle)
        if wait or code:raise RuntimeError('Owned print probe Excel did not exit normally')
        output={'kind':'Excel-formatting-API-probe-only','productPass':False,'ownedExcelPid':pid,'exitCode':code,'records':records}
        output['testSourceSha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        (work/('result-numeric.json' if numeric else 'result.json')).write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(output,ensure_ascii=False),flush=True)
    finally:
        ws=None
        if book is not None:
            try:book.Close(False)
            except Exception:pass
        book=None
        if app is not None:
            try:app.Quit()
            except Exception:pass
        app=None;build.release();build.pythoncom.CoUninitialize()
        if handle is not None:handle.Close()
if __name__=='__main__':main()
