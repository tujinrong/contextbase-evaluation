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
    app=None; handle=None; owned_pid=None; started=dt.datetime.now(dt.timezone.utc).isoformat(); rows=[]
    before=set(build.win32process.EnumProcesses()); build.pythoncom.CoInitialize()
    build.suppress_owned_startup(target)
    try:
        app=build.win32com.client.gencache.EnsureDispatch(build.win32com.client.DispatchEx('Access.Application')); app.Visible=False
        hwnd=app.hWndAccessApp; hwnd=hwnd() if callable(hwnd) else hwnd
        owned_pid=build.win32process.GetWindowThreadProcessId(hwnd)[1]
        if owned_pid in before:raise RuntimeError('Test Access is not newly owned')
        handle=build.win32api.OpenProcess(0x100000|0x400,False,owned_pid)
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
        journal=app.Run('ExportOfficeJournalText')
        if isinstance(journal,tuple):journal=journal[0]
        excel=[]
        for line in str(journal).splitlines():
            pid,wait,code=map(int,line.split('|'))
            excel.append({'ownedPid':pid,'exitWait':wait,'exitCode':code})
        if len(excel)<(3 if args.cycle>=2 else 2) or any(x['exitWait']!=0 or x['exitCode']!=0 for x in excel):raise RuntimeError('Owned Excel lifecycle is incomplete or abnormal')
        app.CloseCurrentDatabase(); app.Quit(2); app=None; build.release()
        wait=build.win32event.WaitForSingleObject(handle,10000); exit_code=build.win32process.GetExitCodeProcess(handle)
        if wait!=0 or exit_code!=0:raise RuntimeError('Owned test Access failed normal exit')
        if source_hash!=build.sha(source):raise RuntimeError('Candidate changed during API tests')
        out=args.output_root or build.ROOT/'build/test-results'; out.mkdir(parents=True,exist_ok=True)
        evidence={'cycle':args.cycle,'startedAt':started,'endedAt':dt.datetime.now(dt.timezone.utc).isoformat(),'inputManifestSha256':frozen['inputManifestSha256'],'artifactSha256':source_hash,'source':frozen['source'],'testSourceSha256':test_source_hash,'checks':rows,'scope':'real COM/VBA/DAO/ACE and dedicated Excel; UI value assignments are not keystroke evidence','ownedOffice':{'accessPid':owned_pid,'exitWait':wait,'exitCode':exit_code,'excel':excel},'candidateUnchanged':True,'unexecuted':['native keyboard/IME/DPI/printing','user acceptance','formal scoring'],'formalScore':None}
        (out/f'cycle{args.cycle}.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'cycle':args.cycle,'passed':sum(r['status']=='PASS' for r in rows),'failed':[r for r in rows if r['status']=='FAIL'],'reportExists':report.exists()},ensure_ascii=False))
        return 1 if any(r['status']=='FAIL' for r in rows) else 0
    finally:
        passwords.clear()
        if app is not None:
            try: app.CloseCurrentDatabase(); app.Quit(2)
            except Exception: pass
        app=None; build.release(); build.pythoncom.CoUninitialize()
        if handle is not None:handle.Close()
if __name__=='__main__': sys.exit(main())
