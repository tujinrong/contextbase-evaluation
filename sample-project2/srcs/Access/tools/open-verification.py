"""Open an isolated, owned UI copy; values/events are setup, not real keystroke proof.
Enter login/menu/search/editor-new/editor-edit/careers/code or quit on stdin.
"""
from pathlib import Path
import ctypes, json, shutil, sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import build
def main():
    folder=build.ROOT/'.tmp/ui'; folder.mkdir(parents=True,exist_ok=True)
    target=folder/'CareerManagement-ui.accdb'; shutil.copy2(build.ROOT/'.tmp/build/CareerManagement.accdb',target)
    passwords=json.loads(build.win32crypt.CryptUnprotectData((build.ROOT/'.tmp/test-secrets.dpapi').read_bytes(),None,None,None,0)[1])
    app=None
    try:
        app=build.win32com.client.gencache.EnsureDispatch(build.win32com.client.DispatchEx('Access.Application')); app.OpenCurrentDatabase(str(target))
        c=app.VBE.ActiveVBProject.VBComponents.Add(1); c.Name='UiHarness'; m=c.CodeModule
        if m.CountOfLines: m.DeleteLines(1,m.CountOfLines)
        m.AddFromString(build.vbe_text((build.ROOT/'tests/UiHarness.bas').read_text(encoding='utf-8'))); m=None; c=None
        app.DoCmd.RunCommand(126); app.Visible=True
        initial=sys.argv[1] if len(sys.argv)>1 else 'menu'
        result=app.Run('PrepareUi',initial,passwords[0]); passwords.clear(); result=None
        pid=ctypes.c_ulong(); ctypes.windll.user32.GetWindowThreadProcessId(int(app.hWndAccessApp()),ctypes.byref(pid))
        print(json.dumps({'status':'ready','screen':initial,'ownedPid':pid.value,'copy':str(target),'setup':'COM value/event setup; native key input untested'}),flush=True)
        for line in sys.stdin:
            command=line.strip()
            if command=='quit': break
            if command in ('login','menu','search','editor-new','editor-edit','careers','code'):
                result=app.Run('PrepareUi',command); result=None; print('screen='+command,flush=True)
    finally:
        passwords.clear()
        if app is not None:
            try: app.Run('LogoutNow'); app.CloseCurrentDatabase(); app.Quit(2)
            except Exception: pass
        app=None; build.release()
if __name__=='__main__': main()
