"""Actual ACE/VBA/Excel verification on a disposable copy. Never changes final ACCDB."""
from __future__ import annotations
import argparse, datetime as dt, gc, hashlib, json, shutil, sys, time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import build
def main():
    p=argparse.ArgumentParser(); p.add_argument('--cycle',type=int,required=True,choices=(1,2,3)); p.add_argument('--artifact',type=Path); p.add_argument('--manifest',type=Path); p.add_argument('--output-root',type=Path); args=p.parse_args()
    source=(args.artifact or build.ROOT/'build/CareerManagement.accdb').resolve()
    owned=build.ROOT/'.tmp/tests'; owned.mkdir(parents=True,exist_ok=True)
    target=owned/'CareerManagement-test.accdb'; report=owned/'roundtrip.xlsx'
    if target.exists(): target.unlink()
    if report.exists(): report.unlink()
    long_report=owned/'roundtrip-long.xlsx'
    if long_report.exists(): long_report.unlink()
    numeric_report=owned/'roundtrip-numeric.xlsx'
    if numeric_report.exists(): numeric_report.unlink()
    shutil.copy2(source,target)
    frozen=json.loads((args.manifest or source.parent/'seed-manifest.json').read_text(encoding='utf-8'))
    source_hash=build.sha(source)
    if source_hash != frozen['artifactSha256'] or not frozen.get('compileGate',{}).get('isCompiled'):
        raise RuntimeError('Staging is not the successfully compiled seed-manifest artifact')
    test_source_hash=build.sha(build.ROOT/'tests/TestSuite.bas')
    secret=build.win32crypt.CryptUnprotectData((build.ROOT/'.tmp/test-secrets.dpapi').read_bytes(),None,None,None,0)[1]
    passwords=json.loads(secret); secret=b''
    app=None; handle=None; owned_pid=None; started=dt.datetime.now(dt.timezone.utc).isoformat(); rows=[]; excel=[]; failure=None
    out=args.output_root or build.ROOT/'build/test-results'; out.mkdir(parents=True,exist_ok=True)
    evidence={'cycle':args.cycle,'startedAt':started,'inputManifestSha256':frozen['inputManifestSha256'],'artifactSha256':source_hash,'source':frozen['source'],'testSourceSha256':test_source_hash,'runnerSha256':build.sha(Path(__file__)),'checks':rows,'status':'RUNNING','scope':'real COM/VBA/DAO/ACE and dedicated Excel; UI value assignments are not keystroke evidence','ownedOffice':{'accessPid':None,'exitWait':None,'exitCode':None,'excel':excel},'unexecuted':['native keyboard/IME/DPI/printing','user acceptance','formal scoring'],'formalScore':None}
    def checkpoint():
        (out/f'cycle{args.cycle}.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
    before=set(build.win32process.EnumProcesses()); build.pythoncom.CoInitialize()
    build.suppress_owned_startup(target)
    try:
        app=build.win32com.client.gencache.EnsureDispatch(build.win32com.client.DispatchEx('Access.Application')); app.Visible=False
        hwnd=app.hWndAccessApp; hwnd=hwnd() if callable(hwnd) else hwnd
        owned_pid=build.win32process.GetWindowThreadProcessId(hwnd)[1]
        if owned_pid in before:raise RuntimeError('Test Access is not newly owned')
        handle=build.win32api.OpenProcess(0x100000|0x400,False,owned_pid)
        evidence['ownedOffice']['accessPid']=owned_pid
        print(json.dumps({'step':'owned-api-test','pid':owned_pid,'file':str(target)}),flush=True)
        app.OpenCurrentDatabase(str(target))
        c=app.VBE.ActiveVBProject.VBComponents.Add(1); c.Name='TestSuite'
        m=c.CodeModule
        if m.CountOfLines: m.DeleteLines(1,m.CountOfLines)
        m.AddFromString(build.vbe_text((build.ROOT/'tests/TestSuite.bas').read_text(encoding='utf-8'))); m=None; c=None
        app.DoCmd.RunCommand(126)
        if not app.IsCompiled: raise RuntimeError('Test-copy VBA project is not fully compiled')
        print(json.dumps({'step':'RunSuite:before','cycle':args.cycle}),flush=True)
        result=app.Run('RunSuite',passwords[0],passwords[1],args.cycle,str(report)); passwords.clear()
        print(json.dumps({'step':'RunSuite:after','cycle':args.cycle}),flush=True)
        if isinstance(result,tuple): result=result[0]
        for line in result.splitlines():
            parts=line.split('|',2); rows.append(dict(id=parts[0],status=parts[1],**({'detail':parts[2]} if len(parts)>2 else {})))
        evidence['status']='RUNSUITE_RETURNED';checkpoint()
        journal=app.Run('ExportOfficeJournalText')
        if isinstance(journal,tuple):journal=journal[0]
        evidence['officeJournalRaw']=str(journal)
        for line in str(journal).splitlines():
            pid,wait,code=map(int,line.split('|'))
            excel.append({'ownedPid':pid,'exitWait':wait,'exitCode':code})
        evidence['status']='OFFICE_JOURNAL_CAPTURED';checkpoint()
        if len(excel)<(3 if args.cycle>=2 else 2) or any(x['exitWait']!=0 or x['exitCode']!=0 for x in excel):raise RuntimeError('Owned Excel lifecycle is incomplete or abnormal')
    except Exception as error:
        error_text=str(error)
        for password_value in passwords:
            if password_value:error_text=error_text.replace(password_value,'[redacted]')
        failure={'phase':evidence['status'],'errorType':type(error).__name__,'hresult':getattr(error,'hresult',None),'errorText':error_text[:2000]}
    finally:
        passwords.clear()
        if app is not None:
            try: app.CloseCurrentDatabase()
            except Exception as error:evidence['closeErrorType']=type(error).__name__
            try: app.Quit(2)
            except Exception as error:evidence['quitErrorType']=type(error).__name__
        app=None; build.release(); build.pythoncom.CoUninitialize()
        if handle is not None:
            evidence['ownedOffice']['exitWait']=build.win32event.WaitForSingleObject(handle,10000)
            evidence['ownedOffice']['exitCode']=build.win32process.GetExitCodeProcess(handle)
            handle.Close()
        evidence['candidateUnchanged']=source_hash==build.sha(source)
        office=evidence['ownedOffice'];office_ok=office['exitWait']==0 and office['exitCode']==0 and len(excel)>=(3 if args.cycle>=2 else 2) and all(x['exitWait']==0 and x['exitCode']==0 for x in excel)
        passed=failure is None and bool(rows) and all(r['status']=='PASS' for r in rows) and office_ok and evidence['candidateUnchanged']
        evidence.update(status='PASS_API_SCOPE' if passed else 'FAIL_API_OR_OFFICE_LIFECYCLE',failure=failure,officeLifecyclePassed=office_ok,endedAt=dt.datetime.now(dt.timezone.utc).isoformat())
        checkpoint()
    print(json.dumps({'cycle':args.cycle,'status':evidence['status'],'passed':sum(r['status']=='PASS' for r in rows),'failed':[r for r in rows if r['status']=='FAIL'],'office':evidence['ownedOffice'],'reportExists':report.exists()},ensure_ascii=False))
    return 0 if passed else 1
if __name__=='__main__': sys.exit(main())
