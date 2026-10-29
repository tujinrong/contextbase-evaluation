"""Actual ACE/VBA/Excel verification on a disposable copy. Never changes final ACCDB."""
from __future__ import annotations
import argparse, datetime as dt, gc, hashlib, json, shutil, sys, time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import build
def main():
    p=argparse.ArgumentParser(); p.add_argument('--cycle',type=int,required=True,choices=(1,2,3)); args=p.parse_args()
    source=build.ROOT/'build/CareerManagement.accdb'
    owned=build.ROOT/'.tmp/tests'; owned.mkdir(parents=True,exist_ok=True)
    target=owned/'CareerManagement-test.accdb'; report=owned/'roundtrip.xlsx'
    if target.exists(): target.unlink()
    if report.exists(): report.unlink()
    long_report=owned/'roundtrip-long.xlsx'
    if long_report.exists(): long_report.unlink()
    shutil.copy2(source,target)
    frozen=json.loads((source.parent/'seed-manifest.json').read_text(encoding='utf-8'))
    source_hash=build.sha(source)
    if source_hash != frozen['artifactSha256'] or not frozen.get('compileGate',{}).get('isCompiled'):
        raise RuntimeError('Staging is not the successfully compiled seed-manifest artifact')
    test_source_hash=build.sha(build.ROOT/'tests/TestSuite.bas')
    secret=build.win32crypt.CryptUnprotectData((build.ROOT/'.tmp/test-secrets.dpapi').read_bytes(),None,None,None,0)[1]
    passwords=json.loads(secret); secret=b''
    app=None; started=dt.datetime.now(dt.timezone.utc).isoformat(); rows=[]
    try:
        app=build.win32com.client.gencache.EnsureDispatch(build.win32com.client.DispatchEx('Access.Application')); app.Visible=False
        app.OpenCurrentDatabase(str(target))
        c=app.VBE.ActiveVBProject.VBComponents.Add(1); c.Name='TestSuite'
        m=c.CodeModule
        if m.CountOfLines: m.DeleteLines(1,m.CountOfLines)
        m.AddFromString(build.vbe_text((build.ROOT/'tests/TestSuite.bas').read_text(encoding='utf-8'))); m=None; c=None
        app.DoCmd.RunCommand(126)
        if not app.IsCompiled: raise RuntimeError('Test-copy VBA project is not fully compiled')
        result=app.Run('RunSuite',passwords[0],passwords[1],args.cycle,str(report)); passwords.clear()
        if isinstance(result,tuple): result=result[0]
        for line in result.splitlines():
            parts=line.split('|',2); rows.append(dict(id=parts[0],status=parts[1],**({'detail':parts[2]} if len(parts)>2 else {})))
        app.CloseCurrentDatabase(); app.Quit(2); app=None; build.release()
        out=build.ROOT/'build/test-results'; out.mkdir(parents=True,exist_ok=True)
        evidence={'cycle':args.cycle,'startedAt':started,'endedAt':dt.datetime.now(dt.timezone.utc).isoformat(),'inputManifestSha256':frozen['inputManifestSha256'],'artifactSha256':source_hash,'source':frozen['source'],'testSourceSha256':test_source_hash,'checks':rows,'scope':'real COM/VBA/DAO/ACE and dedicated Excel; UI value assignments are not keystroke evidence','unexecuted':['native keyboard/IME/DPI/printing','user acceptance','formal scoring'],'formalScore':None}
        (out/f'cycle{args.cycle}.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'cycle':args.cycle,'passed':sum(r['status']=='PASS' for r in rows),'failed':[r for r in rows if r['status']=='FAIL'],'reportExists':report.exists()},ensure_ascii=False))
        return 1 if any(r['status']=='FAIL' for r in rows) else 0
    finally:
        passwords.clear()
        if app is not None:
            try: app.CloseCurrentDatabase(); app.Quit(2)
            except Exception: pass
        app=None; build.release()
if __name__=='__main__': sys.exit(main())
