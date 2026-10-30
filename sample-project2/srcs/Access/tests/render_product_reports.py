"""Render actual product-created XLSX via owned Excel; no native UI claim."""
from pathlib import Path
import argparse,datetime as dt,hashlib,json,shutil,sys,gc
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import build
from pypdf import PdfReader
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--fixture-record',type=Path,required=True);a=p.parse_args()
    candidate=a.candidate.resolve();candidate_sha=sha(candidate)
    fixture=json.loads(a.fixture_record.read_text(encoding='utf-8-sig'))
    if fixture['artifactSha256']!=candidate_sha or any(c['status']!='PASS' for c in fixture['checks']):raise RuntimeError('Completed fixture/candidate version required')
    source=ROOT/'.tmp/tests';work=ROOT/'.tmp/build-agent/ui-regeneration/product-reports';work.mkdir(parents=True,exist_ok=True)
    final=ROOT/'build/test-results/reports';final.mkdir(parents=True,exist_ok=True)
    pairs=[('normal','roundtrip.xlsx'),('numeric','roundtrip-numeric.xlsx'),('long','roundtrip-long.xlsx')]
    before=set(build.win32process.EnumProcesses());app=book=ws=setup=page=None;handle=None;records=[]
    started=dt.datetime.now(dt.timezone.utc).isoformat();build.pythoncom.CoInitialize()
    try:
        app=build.win32com.client.gencache.EnsureDispatch(build.win32com.client.DispatchEx('Excel.Application'))
        app.Visible=False;app.DisplayAlerts=False;app.EnableEvents=False;app.AutomationSecurity=3
        office_version=str(app.Version);office_build=str(app.Build);printer=str(app.ActivePrinter)
        pid=build.win32process.GetWindowThreadProcessId(app.Hwnd)[1]
        if pid in before:raise RuntimeError('PDF Excel is not newly owned')
        handle=build.win32api.OpenProcess(0x100000|0x400,False,pid)
        print(json.dumps({'step':'owned-product-pdf','pid':pid,'artifactSha256':candidate_sha}),flush=True)
        for label,filename in pairs:
            original=source/filename;before_sha=sha(original);copied=work/('report-'+label+'.xlsx')
            shutil.copy2(original,copied)
            if sha(copied)!=before_sha:raise RuntimeError('Product workbook copy differs')
            book=app.Workbooks.Open(str(copied),0,True)
            sheets=[]
            for index in range(1,book.Worksheets.Count+1):
                ws=book.Worksheets(index);setup=ws.PageSetup
                heights=[float(ws.Rows(i).RowHeight) for i in range(1,ws.UsedRange.Rows.Count+1)]
                breaks=[{'row':int(page.Location.Row),'type':int(page.Type)} for page in ws.HPageBreaks]
                sheets.append({'name':ws.Name,'pageCount':int(setup.Pages.Count),'paperSize':setup.PaperSize,'orientation':setup.Orientation,'zoom':setup.Zoom,'fitToPagesWide':setup.FitToPagesWide,'fitToPagesTall':setup.FitToPagesTall,'totalColumnWidthPoints':float(ws.Range('A1:X1').Width),'columnWidthsPoints':[float(ws.Columns(i).Width) for i in range(1,25)],'printArea':setup.PrintArea,'printTitleRows':setup.PrintTitleRows,'rowHeightsPoints':heights,'horizontalPageBreaks':breaks,'verticalPageBreakColumns':[int(page.Location.Column) for page in ws.VPageBreaks],'footer':setup.CenterFooter,'visible':ws.Visible})
                page=setup=ws=None
            pdf=work/('report-'+label+'.pdf')
            if pdf.exists():pdf.unlink()
            print(json.dumps({'step':'product-pdf:before','case':label,'sheetPages':[x['pageCount'] for x in sheets]}),flush=True)
            book.ExportAsFixedFormat(0,str(pdf),0,True,False)
            book.Close(False);book=None;build.release()
            if sha(copied)!=before_sha or sha(original)!=before_sha:raise RuntimeError('Readonly PDF export changed product workbook')
            actual_pages=len(PdfReader(str(pdf)).pages)
            if actual_pages!=sum(x['pageCount'] for x in sheets):raise RuntimeError('PDF page count differs from actual Excel pages')
            for path in (copied,pdf):shutil.copy2(path,final/path.name)
            records.append({'case':label,'workbook':{'file':(final/copied.name).relative_to(ROOT).as_posix(),'sha256':before_sha},'pdf':{'file':(final/pdf.name).relative_to(ROOT).as_posix(),'sha256':sha(pdf),'pages':actual_pages},'sheets':sheets})
        app.Quit();app=None;build.release()
        wait=build.win32event.WaitForSingleObject(handle,10000);code=build.win32process.GetExitCodeProcess(handle)
        if wait or code:raise RuntimeError('Owned product PDF Excel failed normal exit')
        if sha(candidate)!=candidate_sha:raise RuntimeError('Candidate changed during PDF export')
        result={'schemaVersion':1,'status':'PRODUCT_PDF_EXPORTED_API_ONLY','runId':'sp2-ui-regenerate-20261029','artifactSha256':candidate_sha,'fixtureRecordSha256':sha(a.fixture_record),'fixtureTestSourceSha256':fixture['testSourceSha256'],'startedAtUtc':started,'endedAtUtc':dt.datetime.now(dt.timezone.utc).isoformat(),'officeVersion':office_version,'officeBuild':office_build,'printer':printer,'ownedExcelPid':pid,'exitCode':code,'records':records,'measurementSources':[{'file':'tests/render_product_reports.py','sha256':sha(Path(__file__))},{'file':'tools/build.py','sha256':sha(ROOT/'tools/build.py')},{'file':'src/forms/definitions.py','sha256':sha(ROOT/'src/forms/definitions.py')},{'file':'database/schema.py','sha256':sha(ROOT/'database/schema.py')}],'nativeExcelPreview':False,'paperPrint':False,'formalScore':None}
        out=ROOT/'build/test-results/product-report-pdf.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({'status':result['status'],'records':[{'case':x['case'],'pages':x['pdf']['pages'],'file':x['pdf']['file']} for x in records],'ownedPid':pid,'exitCode':code}),flush=True)
    finally:
        page=setup=ws=None
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
