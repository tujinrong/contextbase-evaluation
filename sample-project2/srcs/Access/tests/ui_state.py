"""Initial focus/raw/key-state regressions on a copy of the final product.
Native property and event checks; physical keys/clipboard are a separate run.
"""
from pathlib import Path
import json,shutil,sys
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import build
from faults import import_module,call
from ui_viewport_negative import run_negative
HARNESS='''Option Compare Binary
Option Explicit
Private report As String
Private boundaryLog As String
Private initBoundaries As Long
Private runtimeBoundaries As Long
Private busyBoundaryErrors As Long
Private Function BoundaryFocus(ByVal f As Access.Form) As String
 On Error GoTo Missing
 BoundaryFocus=f.ActiveControl.Name
Missing:
End Function
Public Sub UiStateRecordBoundary(ByVal f As Access.Form,ByVal stage As String)
 Dim focus As String
 focus=BoundaryFocus(f)
 boundaryLog=boundaryLog & f.Name & "|" & stage & "|" & CStr(f.Visible) & "|" & CStr(f.CurrentView) & "|" & focus & "|" & CStr(f.CurrentSectionTop) & "|" & CStr(gBusy) & vbLf
 If stage="initialising" Then initBoundaries=initBoundaries+1 Else runtimeBoundaries=runtimeBoundaries+1
 If Not gBusy Then busyBoundaryErrors=busyBoundaryErrors+1
End Sub
Public Function UiStateBoundaryLog() As String
 UiStateBoundaryLog=boundaryLog
End Function
Private Sub Viewport(ByVal id As String,ByVal f As Access.Form)
 Need id & "-top",f.CurrentSectionTop=0
 Need id & "-left",f.CurrentSectionLeft=0
 Need id & "-scope-restored",Not UiIsInitialisingForm(f) And Not gUiLoading
 If f.Name="frmEmployeeEditor" Then Need id & "-tab-headings-visible",f!tabEmployee.Top+f.CurrentSectionTop>=0
End Sub
Private Sub Need(ByVal id As String,ByVal okay As Boolean)
 report=report & id & "|" & IIf(okay,"PASS","FAIL") & vbLf
 If Not okay Then Err.Raise vbObjectError+976,,id
End Sub
Public Function UiStateRegressions(ByVal password As String) As String
 Dim f As Access.Form, i As Long, cancel As Integer, prefix As String
 On Error GoTo Failed
 report=""
 Need "login-open",PrepareUi("login")
 Need "login-initial-focus",Screen.ActiveControl.Name="txtLoginId"
 Need "menu-open",PrepareUi("menu",password)
 Need "menu-initial-focus",Screen.ActiveControl.Name="cmdEmployeeSearch"
 Need "search-open",PrepareUi("search")
 Need "search-initial-focus-after-busy",Screen.ActiveControl.Name="txtEmployeeNo"
 Viewport "search",Forms("frmEmployeeSearch")
 Set f=Forms("frmEmployeeSearch"):f!lstEmployees=CLng(f!lstEmployees.Column(0,0)):UiSelected f,"lstEmployees":f!lstEmployees.SetFocus
 Dim savedSelection As Long,savedTop As Integer,savedLeft As Integer,searchOverlay As New clsUiBusyState
 savedSelection=CLng(f!lstEmployees.Value):savedTop=f.CurrentSectionTop:savedLeft=f.CurrentSectionLeft
 searchOverlay.Acquire f:searchOverlay.Restore
 Need "search-busy-selection-focus-scroll-preserved",CLng(f!lstEmployees.Value)=savedSelection And CLng(gSelectedEmployee)=savedSelection And Screen.ActiveControl.Name="lstEmployees" And f.CurrentSectionTop=savedTop And f.CurrentSectionLeft=savedLeft
 Need "new-open",PrepareUi("editor-new")
 Set f=Forms("frmEmployeeEditor")
 Need "new-initial-focus-after-busy",Screen.ActiveControl.Name="txtEmployeeNo"
 Viewport "new",f
 Need "new-key-state",f!txtEmployeeNo.Enabled And Not f!txtEmployeeNo.Locked And f!txtEmployeeNo.TabStop
 Need "number-has-no-truncating-mask",f!txtEmployeeNo.InputMask=""
 Need "basic-tab-order",f!txtEmployeeNo.TabIndex<f!txtEmployeeName.TabIndex And f!txtEmployeeName.TabIndex<f!txtEmployeeKana.TabIndex
 Need "career-top-row-order",f!txtStartMonth.TabIndex<f!txtEndMonth.TabIndex And f!txtEndMonth.TabIndex<f!cboRole.TabIndex And f!cboRole.TabIndex<f!txtTeamSize.TabIndex
 Need "career-detail-row-order",f!txtTeamSize.TabIndex<f!txtCompany.TabIndex And f!txtCompany.TabIndex<f!txtProject.TabIndex And f!txtProject.TabIndex<f!txtDescription.TabIndex And f!txtTechnologies.TabIndex<f!txtPhases.TabIndex
 f!txtEmployeeNo="1234567":cancel=0:UiBeforeUpdate f,"txtEmployeeNo",cancel
 Need "raw-seven-digits-rejected-intact",cancel<>0 And f!txtEmployeeNo.Value="1234567" And DCount("*","m_employee")=3
 f!txtEmployeeNo=Null
 Need "existing-open",PrepareUi("editor-edit")
 Set f=Forms("frmEmployeeEditor")
 Need "existing-initial-focus-name",Screen.ActiveControl.Name="txtEmployeeName"
 Viewport "existing",f
 Need "existing-key-copyable-readonly",f!txtEmployeeNo.Enabled And f!txtEmployeeNo.Locked And Not f!txtEmployeeNo.TabStop And f!txtEmployeeNo.Value="000001"
 f!tabEmployee=1:f!lstCareers=1:UiSelected f,"lstCareers"
 Need "career-active-tab-retained",f!tabEmployee.Value=1
 Viewport "career-selection",f
 Dim overlay As New clsUiBusyState, priorTop As Integer, priorLeft As Integer
 f.GoToPage 1,0,3600:f!txtDuties.SetFocus:priorTop=f.CurrentSectionTop:priorLeft=f.CurrentSectionLeft
 overlay.Acquire f:overlay.Restore
 Need "busy-restores-intentional-scroll",f.CurrentSectionTop=priorTop And f.CurrentSectionLeft=priorLeft And Screen.ActiveControl.Name="txtDuties" And f!tabEmployee.Value=1
 Need "code-open",PrepareUi("code")
 Need "code-initial-focus-after-read-busy",Screen.ActiveControl.Name="cboCategory"
 Viewport "code",Forms("frmCodeMaster")
 Set f=Forms("frmCodeMaster")
 Need "unselected-code-disabled",Not f!txtCode.Enabled And Not f!cmdSave.Enabled
 For i=1 To 5
  prefix="repeat-" & CStr(i) & "-"
  Need prefix & "new-open-focus",PrepareUi("editor-new") And Screen.ActiveControl.Name="txtEmployeeNo"
  Viewport prefix & "new",Forms("frmEmployeeEditor")
  Need prefix & "search-open-focus",PrepareUi("search") And Screen.ActiveControl.Name="txtEmployeeNo"
  Need prefix & "menu-open-focus",PrepareUi("menu") And Screen.ActiveControl.Name="cmdEmployeeSearch"
 Next
 PrepareUi "menu":Set gEditor=Nothing:DoCmd.OpenForm "frmEmployeeEditor":Set f=Forms("frmEmployeeEditor")
 Need "failed-load-scope-restored",Not UiIsInitialisingForm(f) And Not gUiLoading And Not gBusy
 Need "failed-load-reports-read-failure",InStr(f!lblMessage.Caption,MessageText("MSG-040"))>0
 Need "recovery-after-failed-load",PrepareUi("editor-new") And Screen.ActiveControl.Name="txtEmployeeNo"
 Viewport "recovery",Forms("frmEmployeeEditor")
 Need "load-and-runtime-boundaries-observed",initBoundaries>0 And runtimeBoundaries>0 And busyBoundaryErrors=0
 Need "no-business-writes",DCount("*","m_employee")=3 And DCount("*","t_career")=3 And DCount("*","m_code")=9
 UiStateRegressions=report:Exit Function
Failed:
 UiStateRegressions=report & "harness|FAIL|" & CStr(Err.Number)
End Function
'''
def main():
 source=build.ROOT/'build/CareerManagement.accdb'; source_hash=build.sha(source)
 folder=build.ROOT/'.tmp/ui-state'; folder.mkdir(parents=True,exist_ok=True); target=folder/'CareerManagement-state.accdb'; shutil.copy2(source,target)
 password=json.loads(build.win32crypt.CryptUnprotectData((build.ROOT/'.tmp/test-secrets.dpapi').read_bytes(),None,None,None,0)[1])[0]
 before=set(build.win32process.EnumProcesses()); app=None; handle=None; checks=[]
 try:
  app=build.win32com.client.gencache.EnsureDispatch(build.win32com.client.DispatchEx('Access.Application'))
  window=app.hWndAccessApp; window=window() if callable(window) else window
  pid=build.win32process.GetWindowThreadProcessId(window)[1]
  if pid in before: raise RuntimeError('Not a newly owned Access process')
  handle=build.win32api.OpenProcess(0x100000|0x400,False,pid)
  app.OpenCurrentDatabase(str(target)); app.Visible=False
  import_module(app,'UiHarness',(build.ROOT/'tests/UiHarness.bas').read_text(encoding='utf-8'))
  import_module(app,'UiStateTests',HARNESS)
  # Test-copy-only instrumentation records the real initialization/runtime
  # branch and does not alter flags, focus, controls, viewport or service result.
  busy_source=(build.ROOT/'src/classes/clsUiBusyState.cls').read_text(encoding='utf-8')
  needle='If UiIsInitialisingForm(f) Then Exit Sub'
  if busy_source.count(needle)!=1: raise RuntimeError('Unknown initialization boundary')
  instrumented=busy_source.replace(needle,'If UiIsInitialisingForm(f) Then\n        UiStateRecordBoundary f,"initialising"\n        Exit Sub\n    End If\n    UiStateRecordBoundary f,"runtime"')
  import_module(app,'clsUiBusyState',instrumented,2); app.DoCmd.RunCommand(126)
  if not app.IsCompiled: raise RuntimeError('UI-state copy not compiled')
  result=call(app,'UiStateRegressions',password); password=''
  boundaries=call(app,'UiStateBoundaryLog')
  for line in result.splitlines():
   parts=line.split('|',2); checks.append({'id':parts[0],'status':parts[1],**({'detail':parts[2]} if len(parts)>2 else {})})
  app.Run('LogoutNow'); app.CloseCurrentDatabase(); app.Quit(2); app=None; build.release()
  exited=build.win32event.WaitForSingleObject(handle,10000)==0; code=build.win32process.GetExitCodeProcess(handle)
  unchanged=build.sha(source)==source_hash
  negative=run_negative()
  (build.ROOT/'build/test-results/ui-viewport-negative.json').write_text(json.dumps(negative,indent=2)+'\n',encoding='utf-8')
  okay=checks and all(c['status']=='PASS' for c in checks) and exited and code==0 and unchanged and negative['status']=='PASS'
  record={'status':'PASS' if okay else 'FAIL','artifactSha256':source_hash,'candidateUnchanged':unchanged,
   'checks':checks,'ownedProcess':{'pid':pid,'newInstance':True,'exited':exited,'exitCode':code},
   'boundaryObservations':{'columns':['form','initialisingOrRuntime','formVisibleProperty','currentView','activeControlOrEmpty','sectionTopTwips','logicalBusy'],
    'rows':[line.split('|') for line in boundaries.splitlines()],
    'scope':'Snapshot inside the real busy Acquire branch on the test copy. Form.Visible is recorded as a property, not treated as proof of interactive/paint completion.'},
   'negativeViewportFixture':negative,
   'testSources':{name:build.sha(build.ROOT/'tests'/name) for name in ('ui_state.py','UiHarness.bas','faults.py','ui_viewport_negative.py')},
   'scope':'Native form open/actual focus/TabIndex/key protection and BeforeUpdate raw retention via VBA. Not physical keystroke, paste or IME evidence. Five repeated navigation lifecycles.','formalScore':None}
  (build.ROOT/'build/test-results/ui-state.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
  print(json.dumps({'status':record['status'],'checks':len(checks),'failed':[c for c in checks if c['status']!='PASS'],'exitCode':code})); return int(not okay)
 finally:
  password=''
  if app is not None:
   try: app.Run('LogoutNow'); app.CloseCurrentDatabase()
   except Exception: pass
   try: app.Quit(2)
   except Exception: pass
  app=None; build.release()
  if handle: handle.Close()
if __name__=='__main__': raise SystemExit(main())
