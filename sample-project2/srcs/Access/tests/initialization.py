"""Readback, repeat-seed refusal and ownership-hash protection on private copies."""
from pathlib import Path
import json,shutil,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import build
def snapshot(app):
    db=app.CurrentDb(); answer={}
    for table in ('m_code_category','m_code','m_app_user','m_employee','t_career'):
        r=db.OpenRecordset('SELECT * FROM ['+table+']',4); rows=[]
        while not r.EOF:
            rows.append(tuple(r.Fields(i).Value for i in range(r.Fields.Count))); r.MoveNext()
        r.Close(); r=None; answer[table]=rows
    db.Close(); db=None; return answer
def main():
    folder=build.ROOT/'.tmp/initialization'; folder.mkdir(parents=True,exist_ok=True); checks=[]
    passwords=json.loads(build.win32crypt.CryptUnprotectData((build.ROOT/'.tmp/test-secrets.dpapi').read_bytes(),None,None,None,0)[1])
    for staging in (False,True):
        path=folder/('safe-staging.accdb' if staging else 'safe-distribution.accdb'); shutil.copy2(build.ROOT/'.tmp/build/CareerManagement.accdb',path)
        app=None; db=None
        try:
            app=build.win32com.client.gencache.EnsureDispatch(build.win32com.client.DispatchEx('Access.Application')); app.OpenCurrentDatabase(str(path))
            component=app.VBE.ActiveVBProject.VBComponents.Add(1); component.Name='modInitGuard'; module=component.CodeModule
            if module.CountOfLines: module.DeleteLines(1,module.CountOfLines)
            module.AddFromString(build.vbe_text('''Option Explicit
Public Function SeedRefused(ByVal adminPassword As String,ByVal staffPassword As String) As Boolean
 On Error GoTo Rejected
 InitializeDemo adminPassword,staffPassword
 Exit Function
Rejected:
 SeedRefused=True
End Function
''')); module=None; component=None; app.DoCmd.RunCommand(126)
            db=app.CurrentDb(); db.Properties('SP2_Staging').Value=staging; db.Close(); db=None
            before=snapshot(app); refused=False
            result=app.Run('SeedRefused',*passwords)
            if isinstance(result,tuple): result=result[0]
            refused=bool(result); result=None
            after=snapshot(app)
            counts={table:len(rows) for table,rows in after.items()}
            okay=refused and before==after and counts=={'m_code_category':3,'m_code':9,'m_app_user':2,'m_employee':3,'t_career':3}
            checks.append({'id':'repeat-seed-staging' if staging else 'repeat-seed-distribution','status':'PASS' if okay else 'FAIL','refused':refused,'businessValuesUnchanged':before==after,'counts':counts})
            before=None; after=None; app.CloseCurrentDatabase(); app.Quit(2); app=None
        finally:
            db=None
            if app is not None:
                try: app.CloseCurrentDatabase(); app.Quit(2)
                except Exception: pass
            app=None; build.release()
    passwords.clear()
    final=build.ROOT/'build/CareerManagement.accdb'; manifest=build.ROOT/'build/seed-manifest.json'
    command=[sys.executable,'-X','utf8',str(build.ROOT/'tools/verify-seed.py'),'--database',str(final),'--manifest',str(manifest)]
    same=subprocess.run(command,capture_output=True,text=True)
    altered=folder/'modified.accdb'; raw=bytearray(final.read_bytes()); raw[-1]^=1; altered.write_bytes(raw); raw=None
    command[command.index(str(final))]=str(altered); different=subprocess.run(command,capture_output=True,text=True)
    checks.append({'id':'idempotent-identical-skip','status':'PASS' if same.returncode==0 else 'FAIL','exitCode':same.returncode})
    checks.append({'id':'modified-artifact-stop','status':'PASS' if different.returncode==2 else 'FAIL','exitCode':different.returncode})
    output={'artifactSha256':build.sha(final),'inputManifestSha256':build.sha(build.ROOT/'build/generation/inputs.json'),'command':'python -X utf8 sample-project2/srcs/Access/tests/initialization.py','exitCode':int(any(c['status']!='PASS' for c in checks)),'testSourceSha256':build.sha(Path(__file__)),'harness':'expected InitializeDemo refusal caught inside VBA SeedRefused; no unhandled modal; snapshots compared only in memory','checks':checks,'scope':'new private copies only, no user database opened','formalScore':None}
    (build.ROOT/'build/test-results/initialization.json').write_text(json.dumps(output,indent=2),encoding='utf-8'); print(json.dumps(output)); return int(any(c['status']!='PASS' for c in checks))
if __name__=='__main__': sys.exit(main())
