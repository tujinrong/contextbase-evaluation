"""Busy overlay and post-operation desired-state tests on one private Access copy."""
from pathlib import Path
import json,shutil,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import build
from faults import import_module,call
def main():
    folder=build.ROOT/'.tmp/busy'; folder.mkdir(parents=True,exist_ok=True); path=folder/'CareerManagement-busy.accdb'
    candidate=build.ROOT/'build/CareerManagement.accdb'
    manifest=json.loads((candidate.parent/'seed-manifest.json').read_text(encoding='utf-8'))
    if build.sha(candidate)!=manifest['artifactSha256'] or not manifest.get('compileGate',{}).get('isCompiled'):
        raise RuntimeError('Staging is not the successfully compiled manifest artifact')
    shutil.copy2(candidate,path)
    password=json.loads(build.win32crypt.CryptUnprotectData((build.ROOT/'.tmp/test-secrets.dpapi').read_bytes(),None,None,None,0)[1])[0]
    app=None
    try:
        app=build.win32com.client.gencache.EnsureDispatch(build.win32com.client.DispatchEx('Access.Application')); app.OpenCurrentDatabase(str(path)); app.Visible=False
        for name,file in [('UiHarness','UiHarness.bas'),('BusySuite','BusySuite.bas')]: import_module(app,name,(build.ROOT/'tests'/file).read_text(encoding='utf-8'))
        app.DoCmd.RunCommand(126)
        if not app.IsCompiled: raise RuntimeError('Busy test-copy VBA is not fully compiled')
        value=call(app,'RunBusySuite',password); password=''
        checks=[]
        for line in value.splitlines():
            pieces=line.split('|',2); checks.append({'id':pieces[0],'status':pieces[1],**({'detail':pieces[2]} if len(pieces)>2 else {})})
        app.Run('LogoutNow'); app.CloseCurrentDatabase(); app.Quit(2); app=None; build.release()
        out={'artifactSha256':build.sha(build.ROOT/'build/CareerManagement.accdb'),'command':'python -X utf8 sample-project2/srcs/Access/tests/busy.py','exitCode':int(any(c['status']!='PASS' for c in checks)),'compileGate':{'isCompiled':True},'testSource':{name:build.sha(build.ROOT/'tests'/name) for name in ('busy.py','BusySuite.bas','UiHarness.bas')},'checks':checks,'scope':'actual Access control properties/events; keyboard-code handling, not native SendInput or IME acceptance','formalScore':None}
        (build.ROOT/'build/test-results/busy.json').write_text(json.dumps(out,indent=2),encoding='utf-8'); print(json.dumps(out)); return out['exitCode']
    finally:
        password=''
        if app is not None:
            try: app.Run('LogoutNow'); app.CloseCurrentDatabase(); app.Quit(2)
            except Exception: pass
        app=None; build.release()
if __name__=='__main__': sys.exit(main())
