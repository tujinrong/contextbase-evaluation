"""Two real Access processes, same ACCDB, application mutex and capacity/uniqueness.
The only mutable database is this script's .tmp/concurrency copy.
"""
from pathlib import Path
import ctypes, datetime as dt, hashlib, json, multiprocessing as mp, shutil, sys, time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import build
HARNESS='''Option Compare Binary
Option Explicit
Public Function CreateConcurrent(ByVal no As String) As String
 Dim e As New clsEmployeeEdit, r As clsResult
 e.EmployeeNo=no: e.Name="架空 競合": e.Kana="カクウ キョウゴウ"
 e.Department="01": e.Status="01": e.JoinDate=BusinessDate()
 Set r=SaveEmployee(e,gSession): CreateConcurrent=r.Kind & "/" & r.MessageId
End Function
Public Function LoginConcurrent(ByVal password As String) As Boolean
 Dim r As clsResult: Set r=Authenticate("demoadmin",password): LoginConcurrent=(r.Kind="OK")
End Function
Public Function FailureConcurrent() As String
 Dim r As clsResult: Set r=Authenticate("demoadmin","isolated invalid password"): FailureConcurrent=r.MessageId
End Function
Public Function ProbeTimeout() As String
 Dim r As clsResult: Set r=Authorize("STAFF"): ProbeTimeout=r.MessageId
End Function
Public Function PopulateFixture(ByVal count As Long) As Boolean
 Dim u As New clsUnitOfWork, r As DAO.Recordset, i As Long, e As New clsEmployeeEdit
 u.OpenUnit True
 For i=1 To count-3
  e.EmployeeNo=Format$(200000+i,"000000"): e.Name="架空 境界": e.Kana="カクウ キョウカイ"
  e.Department="01": e.Status="01": e.JoinDate=DateSerial(2026,10,27)
  Set r=u.Db.OpenRecordset("m_employee",dbOpenDynaset): r.AddNew
  WriteEmployee r,e,"SP2ADMIN",UtcNow(),1: r.Update: r.Close
 Next
 u.Commit: u.CloseUnit: PopulateFixture=True
End Function
'''
def call(app,name,*args):
    r=app.Run(name,*args); return r[0] if isinstance(r,tuple) else r
def worker(path,no,ready,start,output,kind='save'):
    app=None
    try:
        secret=json.loads(build.win32crypt.CryptUnprotectData((build.ROOT/'.tmp/test-secrets.dpapi').read_bytes(),None,None,None,0)[1])[0]
        app=build.win32com.client.gencache.EnsureDispatch(build.win32com.client.DispatchEx('Access.Application')); app.OpenCurrentDatabase(path)
        if kind!='auth' and not call(app,'LoginConcurrent',secret): raise RuntimeError('Fixture login failed')
        secret=''; ready.set()
        if not start.wait(30): raise RuntimeError('Barrier timeout')
        output.put(call(app,'FailureConcurrent') if kind=='auth' else call(app,'CreateConcurrent',no))
    except Exception as e: output.put('ERROR/'+type(e).__name__)
    finally:
        if app is not None:
            try: app.CloseCurrentDatabase(); app.Quit(2)
            except Exception: pass
        app=None; build.release()
def prepare(target,count,auth=False):
    shutil.copy2(build.ROOT/'.tmp/build/CareerManagement.accdb',target)
    app=None; db=None; r=None; c=None; m=None
    try:
        app=build.win32com.client.gencache.EnsureDispatch(build.win32com.client.DispatchEx('Access.Application')); app.OpenCurrentDatabase(str(target))
        c=app.VBE.ActiveVBProject.VBComponents.Add(1); c.Name='ConcurrencyHarness'; m=c.CodeModule
        if m.CountOfLines: m.DeleteLines(1,m.CountOfLines)
        m.AddFromString(build.vbe_text(HARNESS)); m=None; c=None; app.DoCmd.RunCommand(126)
        if not call(app,'PopulateFixture',count): raise RuntimeError('Fixture population failed')
        if auth:
            db=app.CurrentDb(); db.Execute("UPDATE m_app_user SET failed_count=3,locked_until=Null WHERE user_id='SP2ADMIN'",128); db.Close(); db=None
        app.CloseCurrentDatabase(); app.Quit(2); app=None
    finally:
        r=None; m=None; c=None; db=None
        if app is not None:
            try: app.CloseCurrentDatabase(); app.Quit(2)
            except Exception: pass
        app=None; build.release()
def main():
    folder=build.ROOT/'.tmp/concurrency'; folder.mkdir(parents=True,exist_ok=True)
    rows=[]
    for name,count,numbers,expected in [('capacity',199,('999991','999992'),['OK/MSG-014','Validation/MSG-018']),('unique',3,('999991','999991'),['OK/MSG-014','Validation/MSG-006']),('auth',3,('',''),['MSG-001','MSG-001'])]:
        target=folder/(name+'.accdb')
        if target.exists(): target.unlink()
        prepare(target,count,name=='auth')
        ctx=mp.get_context('spawn'); ready=[ctx.Event(),ctx.Event()]; start=ctx.Event(); output=ctx.Queue()
        workers=[ctx.Process(target=worker,args=(str(target),numbers[i],ready[i],start,output,'auth' if name=='auth' else 'save')) for i in range(2)]
        for w in workers: w.start()
        all_ready=all(e.wait(30) for e in ready); start.set()
        results=[output.get(timeout=40) for _ in workers]
        for w in workers: w.join(20)
        app=None; db=None; r=None
        try:
            app=build.win32com.client.gencache.EnsureDispatch(build.win32com.client.DispatchEx('Access.Application')); app.OpenCurrentDatabase(str(target)); db=app.CurrentDb()
            r=db.OpenRecordset('SELECT Count(*) FROM m_employee',4); total=r.Fields(0).Value; r.Close(); r=None
            r=db.OpenRecordset('SELECT Count(*) FROM t_career AS c LEFT JOIN m_employee AS e ON c.employee_id=e.employee_id WHERE e.employee_id Is Null',4); orphans=r.Fields(0).Value; r.Close(); r=None
            auth_ok=True
            if name=='auth':
                r=db.OpenRecordset("SELECT failed_count,locked_until FROM m_app_user WHERE user_id='SP2ADMIN'",4); auth_ok=r.Fields(0).Value==5 and r.Fields(1).Value is not None; r.Close(); r=None
            db.Close(); db=None; app.CloseCurrentDatabase(); app.Quit(2); app=None
        finally:
            r=None; db=None
            if app is not None:
                try: app.CloseCurrentDatabase(); app.Quit(2)
                except Exception: pass
            app=None; build.release()
        okay=all_ready and sorted(results)==sorted(expected) and all(w.exitcode==0 for w in workers) and orphans==0 and total==({'capacity':200,'unique':4,'auth':3}[name]) and auth_ok
        rows.append({'id':'two-process-'+name,'status':'PASS' if okay else 'FAIL','results':results,'employeeCount':total,'orphanCount':orphans,'authControlConsistent':auth_ok,'exitCodes':[w.exitcode for w in workers]})
    target=folder/'timeout.accdb'; prepare(target,3); app=None; mutex=None
    kernel=ctypes.WinDLL('kernel32',use_last_error=True); kernel.CreateMutexW.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_wchar_p]; kernel.CreateMutexW.restype=ctypes.c_void_p; kernel.ReleaseMutex.argtypes=[ctypes.c_void_p]; kernel.CloseHandle.argtypes=[ctypes.c_void_p]
    try:
        app=build.win32com.client.gencache.EnsureDispatch(build.win32com.client.DispatchEx('Access.Application')); app.OpenCurrentDatabase(str(target))
        secret=json.loads(build.win32crypt.CryptUnprotectData((build.ROOT/'.tmp/test-secrets.dpapi').read_bytes(),None,None,None,0)[1])[0]
        assert call(app,'LoginConcurrent',secret); secret=''
        path='\\\\?\\'+str(target.resolve()); name='Global\\SP2Access_'+hashlib.sha256(path.upper().encode('utf-8')).hexdigest()
        mutex=kernel.CreateMutexW(None,True,name)
        if not mutex: raise RuntimeError('Test mutex unavailable')
        started=time.monotonic(); message=call(app,'ProbeTimeout'); elapsed=time.monotonic()-started
        kernel.ReleaseMutex(mutex); kernel.CloseHandle(mutex); mutex=None
        recovered=call(app,'ProbeTimeout')==''
        rows.append({'id':'actual-ten-second-gate-timeout','status':'PASS' if message=='MSG-027' and 9.5<=elapsed<=16 and recovered else 'FAIL','message':message,'elapsedSeconds':elapsed,'recovered':recovered})
        app.CloseCurrentDatabase(); app.Quit(2); app=None
    finally:
        if mutex: kernel.ReleaseMutex(mutex); kernel.CloseHandle(mutex)
        if app is not None:
            try: app.CloseCurrentDatabase(); app.Quit(2)
            except Exception: pass
        app=None; build.release()
    out={'artifactSha256':build.sha(build.ROOT/'.tmp/build/CareerManagement.accdb'),'inputManifestSha256':build.sha(build.ROOT/'build/generation/inputs.json'),'checks':rows,'scope':'actual two Access processes, same canonical file path, private DAO and Global mutex','formalScore':None}
    (build.ROOT/'build/test-results/concurrency.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
    print(json.dumps(out)); return 0 if all(r['status']=='PASS' for r in rows) else 1
if __name__=='__main__': sys.exit(main())
