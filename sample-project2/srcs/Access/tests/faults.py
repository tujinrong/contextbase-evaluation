"""Actual ACE rollback plus test-copy-only commit-ack / post-commit read injections.
No fault switch is compiled into the product. Every transform is recorded here.
"""
from pathlib import Path
import json,shutil,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import build
HARNESS='''Option Compare Binary
Option Explicit
Public TestAckLoss As Boolean
Public TestReadFailure As Boolean
Public Function RunFault(ByVal kind As String, ByVal password As String) As String
 Dim result As clsResult, e As clsEmployeeEdit, original As clsEmployeeEdit, after As clsEmployeeEdit
 Dim c As clsCareerDraft, id As Long, rs As DAO.Recordset, f As Access.Form, okay As Boolean
 Set result=Authenticate("demoadmin",password): If result.Kind<>"OK" Then RunFault="FAIL/login": Exit Function
 id=DLookup("employee_id","m_employee","employee_no='000001'")
 If kind="read" Then
  PrepareUi "editor-edit": Set f=Forms("frmEmployeeEditor")
  f!txtEmployeeName="障害確定済み": UiAction f,"cmdSave"
  okay=(DLookup("employee_name","m_employee","employee_id=" & id)="障害確定済み")
  okay=okay And CurrentProject.AllForms("frmEmployeeSearch").IsLoaded
  If okay Then
   Set f=Forms("frmEmployeeSearch")
   okay=InStr(f!lblSelection.Caption,MessageText("MSG-014"))>0 And InStr(f!lblSelection.Caption,MessageText("MSG-040"))>0 And Not f!cmdEdit.Enabled And Not f!cmdExport.Enabled
  End If
  RunFault=IIf(okay,"PASS","FAIL") & "/post-commit-read": Exit Function
 End If
 Set result=ReadEmployee(id,gSession): Set original=result.Value: Set e=CloneEmployee(original)
 e.Name="障害試験変更"
 If kind="rollback" Then
  e.RemovedCareerIds.Add CLng(e.Careers(1).PersistentId): e.Careers.Remove 1
  Set c=CloneCareer(e.Careers(1)): c.PersistentId=Null: c.Project="障害追加": e.Careers.Add c
  CurrentDb.TableDefs("t_career").ValidationRule="False"
 End If
 Set result=SaveEmployee(e,gSession)
 If kind="rollback" Then
  CurrentDb.TableDefs("t_career").ValidationRule="Day([start_month])=1 And [start_month]=DateValue([start_month]) And ([end_month] Is Null Or (Day([end_month])=1 And [end_month]=DateValue([end_month]) And [end_month]>=[start_month]))"
  Set result=ReadEmployee(id,gSession): Set after=result.Value
  RunFault=IIf(EmployeeSame(original,after) And Same(original.ExpectedRevision,after.ExpectedRevision),"PASS","FAIL") & "/rollback-parent-children"
 Else
  okay=(result.MessageId="MSG-034") And DLookup("employee_name","m_employee","employee_id=" & id)="障害試験変更"
  PrepareUi "editor-edit": Set f=Forms("frmEmployeeEditor")
  ShowResult f,MakeResult("CommitUnknown","MSG-034")
  okay=okay And Not f!cmdSave.Enabled And gEditor.Outcome="CommitUnknown"
  UiAction f,"cmdSave": okay=okay And DLookup("revision","m_employee","employee_id=" & id)=2
  RunFault=IIf(okay,"PASS","FAIL") & "/commit-ack-loss"
 End If
End Function
'''
def import_module(app,name,text,kind=1):
    components=app.VBE.ActiveVBProject.VBComponents
    try: c=components(name)
    except Exception: c=components.Add(kind); c.Name=name
    m=c.CodeModule
    if m.CountOfLines: m.DeleteLines(1,m.CountOfLines)
    m.AddFromString(build.vbe_text(text)); m=None; c=None
def call(app,name,*args):
    value=app.Run(name,*args); return value[0] if isinstance(value,tuple) else value
def main():
    folder=build.ROOT/'.tmp/faults'; folder.mkdir(parents=True,exist_ok=True); checks=[]
    secret=json.loads(build.win32crypt.CryptUnprotectData((build.ROOT/'.tmp/test-secrets.dpapi').read_bytes(),None,None,None,0)[1])[0]
    for kind in ('rollback','ack','read'):
        path=folder/(kind+'.accdb'); shutil.copy2(build.ROOT/'.tmp/build/CareerManagement.accdb',path)
        app=None
        try:
            app=build.win32com.client.gencache.EnsureDispatch(build.win32com.client.DispatchEx('Access.Application')); app.OpenCurrentDatabase(str(path))
            import_module(app,'FaultHarness',HARNESS)
            import_module(app,'UiHarness',(build.ROOT/'tests/UiHarness.bas').read_text(encoding='utf-8'))
            if kind=='ack':
                text=(build.ROOT/'src/classes/clsUnitOfWork.cls').read_text(encoding='utf-8').replace('ws.CommitTrans dbForceOSFlush','ws.CommitTrans dbForceOSFlush\n    If TestAckLoss Then TestAckLoss=False: Err.Raise vbObjectError+999, , "Injected acknowledgement loss"')
                import_module(app,'clsUnitOfWork',text,2)
                text=(build.ROOT/'src/modules/modEmployeeEditor.bas').read_text(encoding='utf-8').replace('at = UtcNow()','at = UtcNow(): TestAckLoss=True')
                import_module(app,'modEmployeeEditor',text)
            if kind=='read':
                text=(build.ROOT/'src/modules/modEmployeeEditor.bas').read_text(encoding='utf-8').replace('e.EmployeeId = employeeId:','TestReadFailure=True\n    e.EmployeeId = employeeId:')
                import_module(app,'modEmployeeEditor',text)
                text=(build.ROOT/'src/modules/modEmployeeSearch.bas').read_text(encoding='utf-8').replace('On Error GoTo Failed','On Error GoTo Failed\n    If TestReadFailure Then Err.Raise vbObjectError+998, , "Injected post-commit read failure"',1)
                import_module(app,'modEmployeeSearch',text)
            app.DoCmd.RunCommand(126)
            result=call(app,'RunFault',kind,secret)
            checks.append({'id':kind,'status':'PASS' if result.startswith('PASS/') else 'FAIL','observation':result,'faultBoundary':'real ACE constraint' if kind=='rollback' else 'test-copy source injection, no product flag'})
            app.Run('LogoutNow'); app.CloseCurrentDatabase(); app.Quit(2); app=None; build.release()
        finally:
            if app is not None:
                try: app.Run('LogoutNow'); app.CloseCurrentDatabase(); app.Quit(2)
                except Exception: pass
            app=None; build.release()
    secret=''
    output={'artifactSha256':build.sha(build.ROOT/'.tmp/build/CareerManagement.accdb'),'checks':checks,'limitations':['logical API-boundary injection is not a power-loss/network-disconnection test'],'formalScore':None}
    (build.ROOT/'build/test-results/faults.json').write_text(json.dumps(output,indent=2),encoding='utf-8'); print(json.dumps(output)); return int(any(x['status']!='PASS' for x in checks))
if __name__=='__main__': sys.exit(main())
