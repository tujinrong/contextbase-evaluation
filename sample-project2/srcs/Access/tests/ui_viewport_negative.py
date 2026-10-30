"""Independent legacy-scroll fault fixture on a separate final-product copy."""
from pathlib import Path
import ctypes,hashlib,json,shutil,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import build
from faults import import_module,call
HARNESS='''Option Explicit
Public Function ObserveLegacyViewport(ByVal password As String) As String
 Dim f As Access.Form
 On Error GoTo Failed
 PrepareUi "editor-new",password:Set f=Forms("frmEmployeeEditor")
 ObserveLegacyViewport=CStr(f.CurrentSectionTop) & "|" & CStr(f.CurrentSectionLeft) & "|" & CStr(f!tabEmployee.Top+f.CurrentSectionTop) & "|" & CStr(f!tabEmployee.Value)
 Exit Function
Failed:
 ObserveLegacyViewport="ERROR/" & CStr(Err.Number)
End Function
'''
def run_negative():
 source=ROOT/'build/CareerManagement.accdb'; original=build.sha(source); folder=ROOT/'.tmp/ui-viewport-negative';folder.mkdir(parents=True,exist_ok=True)
 fixture=folder/'CareerManagement-legacy-scroll.accdb';shutil.copy2(source,fixture)
 canonical=(ROOT/'src/classes/clsUiBusyState.cls').read_text(encoding='cp932')
 a='If UiIsInitialisingForm(f) Then Exit Sub';b='If physicalOverlay Then target.GoToPage 1, priorRight, priorDown'
 if canonical.count(a)!=1 or canonical.count(b)!=1:raise RuntimeError('Unknown viewport protection boundary')
 legacy=canonical.replace(a,'If False Then Exit Sub').replace(b,"' Legacy fault fixture intentionally omits viewport restoration")
 contract=ROOT/'tests/ui-contract.json';expected=json.loads(contract.read_text(encoding='utf-8'))
 rule=next(r for r in expected['rules'] if r['id']=='DIMENSIONS-F04-INITIAL-VIEWPORT')
 password=json.loads(build.win32crypt.CryptUnprotectData((ROOT/'.tmp/test-secrets.dpapi').read_bytes(),None,None,None,0)[1])[0]
 app=None;handle=None
 try:
  before=set(build.win32process.EnumProcesses());app=build.win32com.client.gencache.EnsureDispatch(build.win32com.client.DispatchEx('Access.Application'))
  window=app.hWndAccessApp;window=window() if callable(window) else window;pid=build.win32process.GetWindowThreadProcessId(window)[1];assert pid not in before;handle=build.win32api.OpenProcess(0x100000|0x400,False,pid)
  app.OpenCurrentDatabase(str(fixture));app.Visible=True
  # Reproduce the same requested logical viewport as the native UI run;
  # no scrolling/focus correction is applied before the faulty transition.
  ctypes.windll.user32.MoveWindow(window,0,0,1366,768,True);app.DoCmd.Maximize()
  import_module(app,'UiHarness',(ROOT/'tests/UiHarness.bas').read_text(encoding='utf-8'))
  import_module(app,'LegacyViewportObservation',HARNESS);import_module(app,'clsUiBusyState',legacy,2);app.DoCmd.RunCommand(126)
  raw=call(app,'ObserveLegacyViewport',password);password=''
  if raw.startswith('ERROR/'):raise RuntimeError('Negative fixture did not reach native measurement')
  top,left,heading,tab=map(int,raw.split('|'));actual={'initialSectionTopTwips':top,'initialSectionLeftTwips':left,'tabHeadingsTopInViewportTwips':heading,'initialActiveTab':tab}
  comparisons=[]
  for key,expectation in rule['properties'].items():
   value=actual[key];matched=value==expectation['value'] if expectation['op']=='eq' else value>=expectation['value']
   comparisons.append({'property':key,'expected':expectation,'actual':value,'wouldPass':matched})
  app.Run('LogoutNow');app.CloseCurrentDatabase();app.Quit(2);app=None;build.release()
  exited=build.win32event.WaitForSingleObject(handle,10000)==0;code=build.win32process.GetExitCodeProcess(handle)
  okay=top<0 and heading<0 and any(not c['wouldPass'] for c in comparisons) and exited and code==0 and build.sha(source)==original
  return {'status':'PASS' if okay else 'FAIL','artifactSha256':original,'contractSha256':build.sha(contract),'ruleId':rule['id'],
   'observedLegacyViewport':actual,'comparisons':comparisons,'ownedProcess':{'pid':pid,'newInstance':True,'exited':exited,'exitCode':code},
   'candidateUnchanged':build.sha(source)==original,'fixtureTransforms':['Disable initial-load logical-only branch','Omit runtime native viewport restoration'],
   'canonicalBusySourceSha256':hashlib.sha256(canonical.encode('utf-8')).hexdigest(),'legacyFixtureSourceSha256':hashlib.sha256(legacy.encode('utf-8')).hexdigest(),
   'scope':'Separate disposable copy with explicitly reversed protections; native Access offsets compared with the independently frozen 1.1 contract. PASS means the legacy fault is rejected, not that the negative fixture conforms.'}
 finally:
  password=''
  if app is not None:
   try:app.Run('LogoutNow');app.CloseCurrentDatabase();app.Quit(2)
   except Exception:pass
  app=None;build.release()
  if handle:handle.Close()
if __name__=='__main__':
 record=run_negative();(ROOT/'build/test-results/ui-viewport-negative.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(json.dumps(record));raise SystemExit(int(record['status']!='PASS'))
