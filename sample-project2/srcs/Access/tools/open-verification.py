"""Open an isolated, owned UI copy; values/events are setup, not real keystroke proof.
Enter login/menu/search/editor-new/editor-edit/careers/code or quit on stdin.
"""
from pathlib import Path
import ctypes, json, shutil, sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import build
import win32gui
def main():
    folder=build.ROOT/'.tmp/ui'; folder.mkdir(parents=True,exist_ok=True)
    source=build.ROOT/'build/CareerManagement.accdb'
    manifest=json.loads((build.ROOT/'build/seed-manifest.json').read_text(encoding='utf-8'))
    if build.sha(source)!=manifest['artifactSha256']: raise RuntimeError('Final artifact differs from its owned manifest')
    source_hash=build.sha(source)
    target=folder/'CareerManagement-ui.accdb'; shutil.copy2(source,target)
    passwords=json.loads(build.win32crypt.CryptUnprotectData((build.ROOT/'.tmp/test-secrets.dpapi').read_bytes(),None,None,None,0)[1])
    app=None; process=None; before=set(build.win32process.EnumProcesses())
    try:
        app=build.win32com.client.gencache.EnsureDispatch(build.win32com.client.DispatchEx('Access.Application')); app.OpenCurrentDatabase(str(target))
        window=app.hWndAccessApp; window=int(window() if callable(window) else window)
        owned_pid=build.win32process.GetWindowThreadProcessId(window)[1]
        if owned_pid in before: raise RuntimeError('Access is not a newly owned process')
        process=build.win32api.OpenProcess(0x100000|0x400,False,owned_pid)
        c=app.VBE.ActiveVBProject.VBComponents.Add(1); c.Name='UiHarness'; m=c.CodeModule
        if m.CountOfLines: m.DeleteLines(1,m.CountOfLines)
        m.AddFromString(build.vbe_text((build.ROOT/'tests/UiHarness.bas').read_text(encoding='utf-8'))); m=None; c=None
        app.DoCmd.RunCommand(126); app.Visible=True
        initial=sys.argv[1] if len(sys.argv)>1 else 'menu'
        result=app.Run('PrepareUi',initial,passwords[0]); passwords.clear(); result=None
        ctypes.windll.user32.MoveWindow(window,0,0,1366,768,True); app.DoCmd.Maximize()
        print(json.dumps({'status':'ready','screen':initial,'ownedPid':owned_pid,'finalArtifactSha256':source_hash,'windowTitle':win32gui.GetWindowText(window),'dpi':ctypes.windll.user32.GetDpiForWindow(window),'requestedLogicalWindow':{'width':1366,'height':768},'copy':str(target),'setup':'COM value/event setup; native key input untested'}),flush=True)
        for line in sys.stdin:
            command=line.strip()
            if command=='quit': break
            if command=='state':
                f=app.Screen.ActiveForm
                active=str(app.Screen.ActiveControl.Name)
                state={'form':f.Name,'activeControl':active,'caption':f.Caption,
                    'currentSectionTopTwips':f.CurrentSectionTop,'currentSectionLeftTwips':f.CurrentSectionLeft,
                    'insideWidthTwips':f.InsideWidth,'insideHeightTwips':f.InsideHeight,'values':{}}
                flags=app.Run('UiVerificationFlags'); flags=flags[0] if isinstance(flags,tuple) else flags
                state['dirtyFlags']=dict(zip(('employeeDirty','careerDraftDirty','busy','loading'),(part.lower()=='true' for part in str(flags).split('|'))))
                if f.Name=='frmEmployeeEditor':
                    no=build.win32com.client.CastTo(f.Controls('txtEmployeeNo'),'_Textbox')
                    tab=build.win32com.client.CastTo(f.Controls('tabEmployee'),'_TabControl')
                    state.update(employeeNo=no.Value,keyEnabled=no.Enabled,keyLocked=no.Locked,tab=tab.Value,
                        tabTopInViewportTwips=tab.Top+f.CurrentSectionTop); no=None;tab=None
                names={
                    'frmEmployeeEditor':['txtEmployeeNo','txtEmployeeName','txtEmployeeKana','cboDepartment','cboStatus','txtJoinDate','txtSummary','txtSkills','txtQualifications','txtSelfPr','txtStartMonth','txtEndMonth','cboRole','txtTeamSize','txtCompany','txtProject','txtDescription','txtDuties','txtAchievements','txtTechnologies','txtPhases'],
                    'frmEmployeeSearch':['txtEmployeeNo','txtName','cboDepartment','cboStatus'],
                    'frmCodeMaster':['cboCategory','txtCode','txtCodeName','txtSortOrder','chkEnabled']}.get(f.Name,[])
                for name in names:
                    raw=f.Controls(name); kind=raw.ControlType
                    ctl=build.win32com.client.CastTo(raw,{109:'_Textbox',111:'_Combobox',106:'_Checkbox'}[kind]);raw=None
                    item={'value':ctl.Value,'enabled':ctl.Enabled,'locked':ctl.Locked,'tabIndex':ctl.TabIndex}
                    if active==name and kind==109:
                        try: item['focusedText']=ctl.Text
                        except build.pythoncom.com_error: item['focusedTextUnavailable']=True
                    state['values'][name]=item;ctl=None
                for name in ('lblMessage','lblSelection','lblCount'):
                    try: raw=f.Controls(name)
                    except build.pythoncom.com_error: continue
                    ctl=build.win32com.client.CastTo(raw,'_Label');raw=None;state[name]=ctl.Caption;ctl=None
                print(json.dumps(state,ensure_ascii=False),flush=True); f=None
            if command in ('login','menu','search','editor-new','editor-edit','careers','code'):
                result=app.Run('PrepareUi',command); result=None; print('screen='+command,flush=True)
    finally:
        passwords.clear()
        if app is not None:
            try: app.Run('LogoutNow'); app.CloseCurrentDatabase(); app.Quit(2)
            except Exception: pass
        app=None; build.release()
        if process is not None:
            exited=build.win32event.WaitForSingleObject(process,10000)==0
            code=build.win32process.GetExitCodeProcess(process); process.Close()
            print(json.dumps({'ownedPid':owned_pid,'exited':exited,'exitCode':code,'finalArtifactUnchanged':build.sha(source)==source_hash}),flush=True)
            if not exited or code!=0: raise RuntimeError('Owned Access process did not exit normally')
if __name__=='__main__': main()
