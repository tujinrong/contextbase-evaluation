"""Measure every native component on an isolated copy of the FINAL ACCDB.

No expected value is inferred from the product. The frozen contract supplies
rule/property names; their observations are read from actual Access objects.
Render review and keyboard operation are intentionally left for separate human
or computer-use evidence, and cannot become PASS through COM value assignment.
"""
from pathlib import Path
import argparse,ctypes,datetime as dt,gc,json,os,platform,shutil,sys,time
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import build
import win32gui
from PIL import ImageGrab
ROOT=build.ROOT; REPO=ROOT.parents[2]
FORM_IDS={'frmLogin':'F01','frmMenu':'F02','frmEmployeeSearch':'F03','frmEmployeeEditor':'F04','frmCodeMaster':'F06'}
INTERFACES={100:('Label','_Label'),109:('TextBox','_Textbox'),104:('CommandButton','_CommandButton'),
 106:('CheckBox','_Checkbox'),110:('ListBox','_ListBox'),111:('ComboBox','_Combobox'),123:('TabControl','_TabControl'),124:('Page','_Page')}
FONT_TYPES={100,109,104,110,111,123}
def physical_window_rect(window):
 user32=ctypes.windll.user32
 user32.SetThreadDpiAwarenessContext.argtypes=[ctypes.c_void_p]
 user32.SetThreadDpiAwarenessContext.restype=ctypes.c_void_p
 previous=user32.SetThreadDpiAwarenessContext(ctypes.c_void_p(-4))
 if not previous: raise RuntimeError('Cannot enter per-monitor-aware screenshot coordinates')
 try: return win32gui.GetWindowRect(window)
 finally: user32.SetThreadDpiAwarenessContext(previous)
NATIVE={'fontFamily':'FontName','fontSize':'FontSize','widthTwips':'Width','heightTwips':'Height',
 'foreColor':'ForeColor','backColor':'BackColor','backThemeColorIndex':'BackThemeColorIndex',
 'foreThemeColorIndex':'ForeThemeColorIndex','useTheme':'UseTheme','shape':'Shape','gradient':'Gradient',
 'borderColor':'BorderColor','specialEffect':'SpecialEffect','caption':'Caption',
 'hoverColor':'HoverColor','pressedColor':'PressedColor','hoverForeColor':'HoverForeColor','pressedForeColor':'PressedForeColor',
 'hoverThemeColorIndex':'HoverThemeColorIndex','pressedThemeColorIndex':'PressedThemeColorIndex',
 'hoverForeThemeColorIndex':'HoverForeThemeColorIndex','pressedForeThemeColorIndex':'PressedForeThemeColorIndex',
 'autoResize':'AutoResize','scrollBars':'ScrollBars','fitToScreen':'FitToScreen','borderStyle':'BorderStyle'}
NATIVE.update(initialSectionTopTwips='CurrentSectionTop',initialSectionLeftTwips='CurrentSectionLeft')
def value(app,name,*args):
 result=app.Run(name,*args)
 return result[0] if isinstance(result,tuple) else result
def source_hashes():
 paths=[ROOT/'tests/ui_observe.py',ROOT/'tests/UiHarness.bas',ROOT/'tools/build.py',ROOT/'src/forms/definitions.py',ROOT/'database/schema.py']
 return [{'file':str(p.relative_to(ROOT)).replace('\\','/'),'sha256':build.sha(p)} for p in paths]
def write_status(record):
 report=ROOT/'build/test-results'; report.mkdir(parents=True,exist_ok=True)
 scratch=ROOT/'.tmp/ui-conformance'; scratch.mkdir(parents=True,exist_ok=True)
 staged=scratch/'ui-observations.json'; staged.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 os.replace(staged,report/'ui-observations.json')
def measure(app,form_name,rules):
 f=app.Forms(form_name); sid=FORM_IDS.get(form_name,'UNSPECIFIED-'+form_name)
 components=[{'id':sid,'kind':'Form','textCapable':False}]; objects={sid:f}; observations=[]; details=[]
 raw_count=f.Controls.Count
 try:
  for index in range(raw_count):
   raw=f.Controls(index); kind=int(raw.ControlType)
   if kind not in INTERFACES: raise RuntimeError('Unknown native control type '+str(kind)+'/'+raw.Name)
   label,interface=INTERFACES[kind]; ctl=build.win32com.client.CastTo(raw,interface); raw=None
   cid=sid+'/'+ctl.Name
   components.append({'id':cid,'kind':label,'textCapable':kind in FONT_TYPES}); objects[cid]=ctl
   entry={'id':cid,'controlType':kind,'leftTwips':ctl.Left,'topTwips':ctl.Top,'widthTwips':ctl.Width,'heightTwips':ctl.Height}
   if kind!=124: entry.update(horizontalAnchor=ctl.HorizontalAnchor,verticalAnchor=ctl.VerticalAnchor)
   if kind in FONT_TYPES: entry.update(fontFamily=ctl.FontName,fontSize=ctl.FontSize,fontWeight=ctl.FontWeight)
   if kind in (109,111,110,106): entry.update(enabled=ctl.Enabled,locked=ctl.Locked,tabStop=ctl.TabStop,controlSource=ctl.ControlSource)
   if kind==109: entry.update(inputMask=ctl.InputMask,enterKeyBehavior=ctl.EnterKeyBehavior,scrollBars=ctl.ScrollBars)
   if kind==110: entry.update(columnCount=ctl.ColumnCount,columnWidths=ctl.ColumnWidths,rowSourceType=ctl.RowSourceType)
   details.append(entry); ctl=None
  for rule in rules:
   if rule['target'].split('/')[0]!=sid or rule['kind'] in ('render','interaction'): continue
   target=objects.get(rule['target'])
   if target is None: continue  # Mandatory gate reports the missing actual component/rule.
   properties={}
   for prop in rule['properties']:
    if prop=='fontUnit': properties[prop]='pt'
    elif prop=='detailHeightTwips': section=f.Section(0); properties[prop]=section.Height; section=None
    elif prop=='detailBackColor': section=f.Section(0); properties[prop]=section.BackColor; section=None
    elif prop in ('initialActiveTab','tabHeadingsTopInViewportTwips'):
     tab=build.win32com.client.CastTo(f.Controls('tabEmployee'),'_TabControl')
     properties[prop]=tab.Value if prop=='initialActiveTab' else tab.Top+f.CurrentSectionTop; tab=None
    elif prop in NATIVE: properties[prop]=getattr(target,NATIVE[prop])
    else: raise RuntimeError('No native property reader for '+prop)
   observations.append({'ruleId':rule['id'],'target':rule['target'],'method':'native-property','properties':properties})
  try: focus=app.Screen.ActiveControl.Name
  except Exception: focus=None
  meta={'id':sid,'form':form_name,'controlsCount':raw_count,'insideWidthTwips':f.InsideWidth,'insideHeightTwips':f.InsideHeight,'activeControl':focus,
   'currentSectionTopTwips':f.CurrentSectionTop,'currentSectionLeftTwips':f.CurrentSectionLeft}
  return components,observations,details,meta
 finally:
  target=None; raw=None; ctl=None; section=None; objects.clear(); f=None; gc.collect()
def main(args):
 final=ROOT/'build/CareerManagement.accdb'; final_hash=build.sha(final)
 manifest=json.loads((ROOT/'build/seed-manifest.json').read_text(encoding='utf-8'))
 if final_hash!=manifest['artifactSha256']: raise RuntimeError('Final artifact/manifest mismatch')
 contract_path=ROOT/'tests/ui-contract.json'; contract=json.loads(contract_path.read_text(encoding='utf-8'))
 contract_hash=build.sha(contract_path); input_path=ROOT/'build/generation/inputs.json'
 input_hash=build.sha(input_path); validator=REPO/'agents/builds/build-agent/scripts/ui-conformance.mjs'
 validator_hash=build.sha(validator); test_hashes=source_hashes()
 folder=ROOT/'.tmp/ui-conformance'; folder.mkdir(parents=True,exist_ok=True)
 copy=folder/'CareerManagement-observed.accdb'; shutil.copy2(final,copy)
 report=ROOT/'build/test-results'; images=report/'ui'; images.mkdir(parents=True,exist_ok=True)
 passwords=json.loads(build.win32crypt.CryptUnprotectData((ROOT/'.tmp/test-secrets.dpapi').read_bytes(),None,None,None,0)[1])
 before=set(build.win32process.EnumProcesses()); app=None; handle=None; results=[]; components=[]; details=[]; screens=[]; actual_forms=[]
 build.pythoncom.CoInitialize()
 try:
  app=build.win32com.client.gencache.EnsureDispatch(build.win32com.client.DispatchEx('Access.Application'))
  window=app.hWndAccessApp; window=int(window() if callable(window) else window)
  pid=build.win32process.GetWindowThreadProcessId(window)[1]
  if pid in before: raise RuntimeError('Access process is not newly owned')
  handle=build.win32api.OpenProcess(0x100000|0x400,False,pid)
  app.OpenCurrentDatabase(str(copy)); app.Visible=True
  c=app.VBE.ActiveVBProject.VBComponents.Add(1); c.Name='UiHarness'; m=c.CodeModule
  if m.CountOfLines: m.DeleteLines(1,m.CountOfLines)
  m.AddFromString(build.vbe_text((ROOT/'tests/UiHarness.bas').read_text(encoding='utf-8'))); m=None; c=None
  app.DoCmd.RunCommand(126)
  if not app.IsCompiled: raise RuntimeError('Measurement fixture is not compiled')
  actual_forms=[str(app.CurrentProject.AllForms(i).Name) for i in range(app.CurrentProject.AllForms.Count)]
  if set(actual_forms)!=set(FORM_IDS): raise RuntimeError('Product form inventory differs: '+repr(actual_forms))
  user32=ctypes.windll.user32
  user32.MoveWindow(window,0,0,1366,768,True); dpi=user32.GetDpiForWindow(window)
  window_rect=physical_window_rect(window)
  env={'platform':platform.platform(),'renderer':'Microsoft Access '+str(app.Version)+' x64',
   'dpi':dpi,'scale':dpi/96,'viewport':{'width':window_rect[2]-window_rect[0],'height':window_rect[3]-window_rect[1],'unit':'physical-px'},
   'requestedLogicalViewport':{'width':1366,'height':768,'unit':'96-DPI logical-px'},'officeWindowTitle':win32gui.GetWindowText(window)}
  for screen,name in [('login','frmLogin'),('menu','frmMenu'),('search','frmEmployeeSearch'),('editor-new','frmEmployeeEditor'),('careers','frmEmployeeEditor'),('code','frmCodeMaster')]:
   if not value(app,'PrepareUi',screen,passwords[0]): raise RuntimeError('UI setup failed: '+screen)
   app.DoCmd.SelectObject(2,name,False); app.DoCmd.Maximize(); time.sleep(.3)
   if screen!='careers':
    cc,oo,dd,meta=measure(app,name,contract['rules']); components+=cc; results+=oo; details+=dd
   else:
    f=app.Forms(name);tab=build.win32com.client.CastTo(f.Controls('tabEmployee'),'_TabControl')
    meta={'id':'F04-CAREER','form':name,'tabValue':tab.Value,'currentSectionTopTwips':f.CurrentSectionTop,
     'currentSectionLeftTwips':f.CurrentSectionLeft,'tabHeadingsTopInViewportTwips':tab.Top+f.CurrentSectionTop};tab=None;f=None
   image=images/(('F04-BASIC' if screen=='editor-new' else 'F04-CAREER' if screen=='careers' else FORM_IDS[name])+'.png')
   rectangle=physical_window_rect(window); ImageGrab.grab(bbox=rectangle,all_screens=True).save(image)
   meta.update(screenshot={'file':str(image.relative_to(ROOT)).replace('\\','/'),'sha256':build.sha(image)},windowRect=list(rectangle))
   screens.append(meta)
   # Native focus-to-control scrolls the form without changing its font/scale.
   # Additional images make the footer reachable instead of hiding a cropped
   # control below the current viewport. This is API setup, not keyboard proof.
   if screen in ('search','editor-new','careers','code'):
    app.DoCmd.GoToControl('cmdCancel' if name=='frmEmployeeEditor' else 'cmdMenu'); time.sleep(.2)
    bottom=images/(image.stem+'-bottom.png'); ImageGrab.grab(bbox=rectangle,all_screens=True).save(bottom)
    screens.append({'id':meta['id']+'-BOTTOM','form':name,'setup':'native GoToControl footer focus/scroll, not physical input',
     'screenshot':{'file':str(bottom.relative_to(ROOT)).replace('\\','/'),'sha256':build.sha(bottom)},'windowRect':list(rectangle)})
  passwords.clear(); value(app,'LogoutNow'); app.CloseCurrentDatabase(); app.Quit(2); app=None; build.release()
  exited=build.win32event.WaitForSingleObject(handle,10000)==0; exit_code=build.win32process.GetExitCodeProcess(handle)
  if not exited or exit_code!=0: raise RuntimeError('Owned Access failed normal exit: '+str(exit_code))
  if final_hash!=build.sha(final) or contract_hash!=build.sha(contract_path) or input_hash!=build.sha(input_path) or validator_hash!=build.sha(validator) or test_hashes!=source_hashes():
   raise RuntimeError('Final product, frozen expectation, inputs or measurement source changed during observation')
  output={'schemaVersion':1,'projectId':'sample-project2','profileId':'Access','runId':args.run_id,
   'contractSha256':contract_hash,'frozenInputManifestSha256':input_hash,'validatorSha256':validator_hash,
   'artifact':{'file':'build/CareerManagement.accdb','sha256':final_hash},'environment':env,
   'components':components,'observations':results,'measurementSources':test_hashes,
   'pending':['render-review for all five screens and both editor Pages','independent native keyboard-operation evidence'],
   'systemChrome':{'owner':'Windows/Access','scope':'titlebar, ribbon, native MessageBox; not application font owned'},
   'ownedProcess':{'pid':pid,'newInstance':True,'exited':exited,'exitCode':exit_code},'screens':screens,'formalScore':None}
  write_status(output)
  (report/'ui-native-properties.json').write_text(json.dumps({'artifactSha256':final_hash,'components':details,'screens':screens},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
  print(json.dumps({'status':'NATIVE_PROPERTIES_COLLECTED_RENDER_AND_KEYBOARD_PENDING','components':len(components),'observations':len(results),'artifactSha256':final_hash,'ownedPid':pid,'exitCode':exit_code}))
 finally:
  passwords.clear(); c=None; m=None
  if app is not None:
   try: value(app,'LogoutNow'); app.CloseCurrentDatabase()
   except Exception: pass
   try: app.Quit(2)
   except Exception: pass
  app=None; build.release(); build.pythoncom.CoUninitialize()
  if handle: handle.Close()
if __name__=='__main__':
 parser=argparse.ArgumentParser(); parser.add_argument('--run-id',required=True); args=parser.parse_args()
 status={'schemaVersion':1,'projectId':'sample-project2','profileId':'Access','runId':args.run_id,
  'status':'RUNNING','startedAtUtc':dt.datetime.now(dt.timezone.utc).isoformat(),'components':[],'observations':[]}
 try:
  # Invalidate a prior complete observation BEFORE opening/copying/reading the
  # current artifact. An interrupted or failed rerun must not leave an old PASS.
  write_status(status)
  main(args)
 except BaseException as error:
  status.update(status='FAILED',failedAtUtc=dt.datetime.now(dt.timezone.utc).isoformat(),errorType=type(error).__name__)
  write_status(status)
  raise
