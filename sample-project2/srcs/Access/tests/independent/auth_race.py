"""Independent two-process ACE cache/mutex test on fixed, owned disposable copies."""
from pathlib import Path
import concurrent.futures, datetime as dt, gc, hashlib, json, shutil, sys, threading
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import build
import win32api, win32event, win32process

MODULE = '''Option Compare Binary
Option Explicit
Public Function IRPrime() As Long
 IRPrime = CLng(DLookup("failed_count", "m_app_user", "user_id='SP2STAFF'"))
End Function
Public Function IRBadPassword() As String
 Dim result As clsResult
 Set result = Authenticate("staff", "independent incorrect password")
 IRBadPassword = result.MessageId
End Function
Public Function IRState() As String
 Dim count As Long, deadline As Variant
 count = CLng(DLookup("failed_count", "m_app_user", "user_id='SP2STAFF'"))
 deadline = DLookup("locked_until", "m_app_user", "user_id='SP2STAFF'")
 If IsNull(deadline) Then
  IRState = CStr(count) & "|no-deadline"
 Else
  IRState = CStr(count) & "|" & CStr(DateDiff("s", UtcNow(), CDate(deadline)))
 End If
End Function
'''

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def call(app, name):
    value = app.Run(name)
    return value[0] if isinstance(value, tuple) else value

class OwnedAccess:
    def __enter__(self):
        build.pythoncom.CoInitialize()
        self.app = build.win32com.client.gencache.EnsureDispatch(build.win32com.client.DispatchEx('Access.Application'))
        self.app.Visible = False
        self.pid = win32process.GetWindowThreadProcessId(self.app.hWndAccessApp())[1]
        self.handle = win32api.OpenProcess(0x100000, False, self.pid)
        return self
    def __exit__(self, *_):
        try: self.app.CloseCurrentDatabase()
        except Exception: pass
        try: self.app.Quit(2)
        except Exception: pass
        self.app = None; gc.collect(); build.release(); build.pythoncom.CoUninitialize()
        self.exited = win32event.WaitForSingleObject(self.handle, 5000) == 0
        self.handle.Close()
        if not self.exited: raise RuntimeError('Owned Access process did not exit')

def worker(target, barrier):
    with OwnedAccess() as owned:
        owned.app.OpenCurrentDatabase(str(target))
        # Both separate process caches observe 3 before either application authentication starts.
        primed = int(call(owned.app, 'IRPrime'))
        if primed != 3: raise RuntimeError('Wrong initial failure count')
        barrier.wait(timeout=30)
        message = str(call(owned.app, 'IRBadPassword'))
        pid = owned.pid
    return {'pid': pid, 'primedCount': primed, 'messageId': message, 'ownedProcessExited': owned.exited}

def main():
    source = ROOT / 'build/CareerManagement.accdb'; before = sha(source)
    folder = ROOT / '.tmp/independent-review'; folder.mkdir(parents=True, exist_ok=True)
    if folder.resolve() != folder.absolute(): raise RuntimeError('Redirected review scratch refused')
    rows = []; started = dt.datetime.now(dt.timezone.utc).isoformat()
    for iteration in range(1, 4):
        target = folder / f'auth-race-{iteration}.accdb'
        if target.exists():
            if target.is_symlink() or target.parent.resolve() != folder.resolve(): raise RuntimeError('Unsafe test copy')
            target.unlink()
        shutil.copy2(source, target)
        if sha(target) != before or sha(source) != before: raise RuntimeError('Candidate changed while copying')
        with OwnedAccess() as setup:
            setup.app.OpenCurrentDatabase(str(target))
            component = setup.app.VBE.ActiveVBProject.VBComponents.Add(1); component.Name = 'IndependentAuthRace'
            module = component.CodeModule
            if module.CountOfLines: module.DeleteLines(1, module.CountOfLines)
            module.AddFromString(MODULE.replace('\n', '\r\n')); module = None; component = None
            setup.app.DoCmd.RunCommand(126)
            database = setup.app.CurrentDb()
            database.Execute("UPDATE m_app_user SET failed_count=3,locked_until=Null WHERE user_id='SP2STAFF'", 128)
            database.Close(); database = None
        barrier = threading.Barrier(2)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            pending = [executor.submit(worker, target, barrier) for _ in range(2)]
            workers = [future.result(timeout=60) for future in pending]
        with OwnedAccess() as observer:
            observer.app.OpenCurrentDatabase(str(target)); state = str(call(observer.app, 'IRState'))
        pieces = state.split('|'); okay = pieces[0] == '5' and pieces[1].isdigit() and 600 <= int(pieces[1]) <= 900 and len({x['pid'] for x in workers}) == 2 and all(x['messageId'] == 'MSG-001' and x['ownedProcessExited'] for x in workers)
        rows.append({'id': f'IR-AR{iteration:02}', 'status': 'PASS' if okay else 'FAIL', 'workers': workers, 'finalFailureCount': int(pieces[0]), 'lockRemainingSeconds': pieces[1], 'setupProcessExited': setup.exited, 'observerProcessExited': observer.exited})
    record = {'status': 'PASS' if all(x['status'] == 'PASS' for x in rows) and sha(source) == before else 'FAIL', 'reviewer': '/root/req_desktop', 'startedAtUtc': started, 'finishedAtUtc': dt.datetime.now(dt.timezone.utc).isoformat(), 'candidateArtifactSha256': before, 'candidateUnchanged': sha(source) == before, 'testSourceSha256': sha(Path(__file__)), 'checks': rows, 'scope': 'Three independent repetitions: two actual Access processes, each preloads failure count3, then starts wrong-password authentication at a barrier; fresh third process reads final count5/lock. Only owned copies are modified; all private Access processes are waited for exit.', 'notPerformed': ['Authentication versus account-disable race', 'All other Pilot concurrency/fault scenarios', 'User acceptance/formal scoring'], 'formalScore': None}
    output = ROOT / 'build/test-results/independent-review/auth-race.json'; output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(record, ensure_ascii=False, indent=2), 'utf-8')
    print(json.dumps({'status': record['status'], 'checks': len(rows), 'results': [x['status'] for x in rows], 'candidateUnchanged': record['candidateUnchanged']}))
    return 0 if record['status'] == 'PASS' else 1

if __name__ == '__main__': raise SystemExit(main())
