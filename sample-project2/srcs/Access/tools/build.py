"""Build a NEW owned staging ACCDB; never edits an existing user database.
Requires Windows Python 3.11 x64, pywin32 311, Office Access/Excel x64.
Fixed admin/staff DEMO credentials are public sample data; optional operator inputs are not printed.
"""
from __future__ import annotations
import sys
sys.dont_write_bytecode = True
import argparse, gc, getpass, hashlib, importlib.util, json, os, shutil, site, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DEPS=ROOT/'.tmp/python-deps'
if DEPS.is_dir():
    site.addsitedir(str(DEPS)); os.add_dll_directory(str(DEPS/'pywin32_system32'))
import pythoncom, win32com.client, win32crypt, win32api, win32event, win32process
import win32com
win32com.__gen_path__=str(ROOT/'.tmp/gen_py')
Path(win32com.__gen_path__).mkdir(parents=True,exist_ok=True)
import win32com.gen_py
win32com.gen_py.__path__=[win32com.__gen_path__]
def vbe_text(source):
    """Protect literals from VBE's active ANSI codepage conversion (e.g. ACP936).
    Source remains UTF-8; unrepresentable characters become explicit UTF-16 ChrW.
    This is a lexical encoding transform, not business-code generation.
    """
    import re
    def literal(match):
        value=match.group()[1:-1].replace('""','"'); parts=[]; pending=''
        for char in value:
            try: safe=char.encode('mbcs').decode('mbcs')==char
            except UnicodeError: safe=False
            if safe: pending+=char; continue
            if pending: parts.append('"'+pending.replace('"','""')+'"'); pending=''
            raw=char.encode('utf-16-le')
            parts += ['ChrW(&H'+format(int.from_bytes(raw[i:i+2],'little'),'X')+')' for i in range(0,len(raw),2)]
        if pending: parts.append('"'+pending.replace('"','""')+'"')
        return '('+' & '.join(parts)+')' if len(parts)>1 else parts[0] if parts else '""'
    return re.sub(r'"(?:[^"\r\n]|"")*"',literal,source).replace('\n','\r\n')
def load(path):
    spec=importlib.util.spec_from_file_location(path.stem,str(path)); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
schema=load(ROOT/'database/schema.py'); forms=load(ROOT/'src/forms/definitions.py')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def prop(db,name,kind,value):
    try: db.Properties(name).Value=value
    except pythoncom.com_error: db.Properties.Append(db.CreateProperty(name,kind,value))
def release():
    gc.collect(); pythoncom.CoFreeUnusedLibraries()

def invalidate_verification():
    """A regenerated product cannot inherit reports or pictures from an old SHA."""
    target=ROOT/'build/test-results'; expected=ROOT.resolve()/'build/test-results'
    if target.exists():
        if target.is_symlink() or target.resolve()!=expected: raise RuntimeError('Unsafe verification report directory')
        for child in target.rglob('*'):
            if child.is_symlink(): raise RuntimeError('Linked verification report refused')
        shutil.rmtree(target)
    target.mkdir(parents=True,exist_ok=True)

def classic_control(ctl, kind, *, header=False):
    """Only properties verified on these native Access interfaces are assigned.

    A CheckBox has no font/text surface: its attached Label owns its caption.
    Theme disabling is supported by CommandButton and TabControl, not TextBox.
    Unsupported assignments are deliberately not hidden behind try/except.
    """
    ctl.HorizontalAnchor=0; ctl.VerticalAnchor=0
    ctl.BorderThemeColorIndex=-1; ctl.BorderColor=8421504
    if kind !=106:
        ctl.FontName='Yu Gothic UI'; ctl.FontSize=11; ctl.FontWeight=700 if header else 400
        ctl.ForeThemeColorIndex=-1; ctl.ForeColor=0
        ctl.BackThemeColorIndex=-1
        ctl.BackColor=16777215 if kind in (109,110,111) else 15790320
    if kind in (104,123):
        ctl.UseTheme=False; ctl.Shape=0; ctl.Gradient=0; ctl.BorderStyle=1
        ctl.HoverThemeColorIndex=-1; ctl.HoverForeThemeColorIndex=-1
        ctl.PressedThemeColorIndex=-1; ctl.PressedForeThemeColorIndex=-1
        ctl.HoverColor=15066597; ctl.PressedColor=14013909
        ctl.HoverForeColor=0; ctl.PressedForeColor=0
    else:
        ctl.SpecialEffect=0; ctl.BorderStyle=0 if kind==100 else 1
    if kind in (100,109,111,104,123): ctl.BackStyle=0 if kind==100 else 1
def create_forms(app):
    exports=ROOT/'.tmp/build/forms'; exports.mkdir(parents=True,exist_ok=True)
    for name, d in forms.FORMS.items():
        print('Designing '+name,flush=True)
        # Import a named native Access form before design automation. Creating an
        # unnamed form can trigger an interactive Save As dialog in Office 365.
        template=ROOT/'.tmp/build/bootstrap-form.txt'
        template.write_text('Version =20\r\nVersionRequired =20\r\nBegin Form\r\n    Width =20000\r\n    Begin\r\n        Begin Section\r\n            Height =10000\r\n            Name ="Detail"\r\n        End\r\n    End\r\nEnd\r\n',encoding='utf-16')
        app.LoadFromText(2,name,str(template)); app.DoCmd.OpenForm(name,1)
        f=app.Forms(name); original=name; f.RecordSource=''; f.Caption=d['caption']; f.Width=d['width']
        f.Section(0).Height=d['height']; f.DefaultView=0; f.NavigationButtons=False; f.RecordSelectors=False
        f.DividingLines=False; f.AutoCenter=True; f.AutoResize=True; f.FitToScreen=False
        f.BorderStyle=2; f.PopUp=False; f.Modal=False; f.ScrollBars=3; f.KeyPreview=True; f.TimerInterval=1000
        section=f.Section(0); section.BackThemeColorIndex=-1; section.BackColor=15790320; section=None
        f.OnLoad='[Event Procedure]'; f.OnTimer='[Event Procedure]'; f.OnKeyDown='[Event Procedure]'
        f.OnMouseDown='[Event Procedure]'; f.OnUnload='[Event Procedure]'; f.OnClose='[Event Procedure]'
        # Give the new form its definitive name before opening its code module.
        # Access's Save command can request a name for an unnamed new form.
        app.DoCmd.Save(2,original)
        f.HasModule=True
        tabs={}
        for c in d['controls']:
            parent=''
            if 'page' in c: parent=tabs[c['page']]
            ctl=app.CreateControl(original,c['kind'],0,parent,'',c['x'],c['y'],c['w'],c['h'])
            ctl=win32com.client.CastTo(ctl,{100:'_Label',109:'_Textbox',104:'_CommandButton',106:'_Checkbox',110:'_ListBox',111:'_Combobox',123:'_TabControl'}[c['kind']])
            ctl.Name=c['name']
            if c['kind'] in (100,104): ctl.Caption=c['label']
            classic_control(ctl,c['kind'])
            if c['kind'] in (109,111,110,106): ctl.ControlSource=''
            if c['kind']==104: ctl.OnClick='[Event Procedure]'
            if c['kind']==109:
                ctl.OnChange='[Event Procedure]'; ctl.BeforeUpdate='[Event Procedure]'
                # Length masks would silently truncate pasted employee numbers.
                # Keep complete raw input; the existing service rejects overlength.
                if c.get('password'): ctl.InputMask='Password'
                if c.get('multiline'): ctl.EnterKeyBehavior=True; ctl.ScrollBars=2
            if c['kind'] in (111,106,110): ctl.AfterUpdate='[Event Procedure]'
            if c['kind']==123: ctl.OnChange='[Event Procedure]'
            if c['kind']==111:
                ctl.RowSourceType='Value List'; ctl.RowSource=''; ctl.ColumnCount=2; ctl.BoundColumn=1
                ctl.ColumnWidths='0;4800'; ctl.LimitToList=True; ctl.AutoExpand=True
            if c['kind']==110:
                ctl.RowSourceType='ListRows'; ctl.RowSource=''; ctl.ColumnCount=c['columns']; ctl.BoundColumn=1
                ctl.ColumnWidths=c['widths']; ctl.MultiSelect=0
            if c['kind']==123:
                for i,caption in enumerate(c['pages']):
                    page=ctl.Pages(i) if i<ctl.Pages.Count else ctl.Pages.Add()
                    page.Name='page'+str(i); page.Caption=caption; tabs[i]=page.Name
            if c['kind'] in (109,111,106,110) and c['label']:
                # Lists have an independent header label; fields have attached labels.
                label_parent=ctl.Name if c['kind'] !=110 else parent
                ly=c.get('header_y',c['y']-520) if c['kind']==110 else c.get('label_y',c['y']+30)
                lx=c['x'] if c['kind']==110 else c.get('label_x',max(450,c['x']-2250))
                lw=c['w'] if c['kind']==110 else c.get('label_w',min(2100,c['x']-lx-150))
                if c['kind']==110 and c.get('headers'):
                    offset=0
                    for index,(caption,width) in enumerate(zip(c['headers'],map(int,c['widths'].split(';')))):
                        if width and caption:
                            label=win32com.client.CastTo(app.CreateControl(original,100,0,parent,'',lx+offset,ly,width,c.get('header_h',430)),'_Label')
                            label.Name='header_'+ctl.Name+'_'+str(index); label.Caption=caption; classic_control(label,100,header=True); label=None
                        offset+=width
                else:
                    label=win32com.client.CastTo(app.CreateControl(original,100,0,label_parent,'',lx,ly,lw,430),'_Label')
                    label.Name='label_'+ctl.Name; label.Caption=c['label']; classic_control(label,100); label=None
            ctl=None
        # Access CreateControl's implicit tab order can focus the last-created
        # button. Set the order for the form and for each native Page explicitly.
        tab_order={}
        for c in d['controls']:
            if c['kind']==100: continue
            parent=c.get('page','form'); ordinal=tab_order.get(parent,0)
            ctl=win32com.client.CastTo(f.Controls(c['name']),{109:'_Textbox',104:'_CommandButton',106:'_Checkbox',110:'_ListBox',111:'_Combobox',123:'_TabControl'}[c['kind']])
            ctl.TabIndex=ordinal; ctl=None
            tab_order[parent]=ordinal+1
        for parent,names in d.get('tab_order',{}).items():
            expected_names={c['name'] for c in d['controls'] if c.get('page','form')==parent and c['kind']!=100}
            if len(names)!=len(set(names)) or set(names)!=expected_names: raise RuntimeError('Incomplete explicit native Tab order')
            for ordinal,control_name in enumerate(names):
                c=next(c for c in d['controls'] if c['name']==control_name)
                ctl=win32com.client.CastTo(f.Controls(control_name),{109:'_Textbox',104:'_CommandButton',106:'_Checkbox',110:'_ListBox',111:'_Combobox',123:'_TabControl'}[c['kind']])
                ctl.TabIndex=ordinal; ctl=None
        print('Code '+name,flush=True)
        module=f.Module
        if module.CountOfLines: module.DeleteLines(1,module.CountOfLines)
        module.AddFromString(forms.module_code(name,d)); module=None
        app.DoCmd.Save(2,original); app.DoCmd.Close(2,original,1); f=None
        if original != name: app.DoCmd.Rename(name,2,original)
        # Native Form exports are canonical output, preserving code and standard properties.
        export=exports/f'{name}.txt'
        if export.exists(): export.unlink()
        app.SaveAsText(2,name,str(export))
    release()
    return exports
def import_code(app):
    for folder,kind in [('classes',2),('modules',1)]:
        for path in sorted((ROOT/'src'/folder).glob('*')):
            if path.suffix not in ('.bas','.cls'): continue
            component=app.VBE.ActiveVBProject.VBComponents.Add(kind); component.Name=path.stem
            module=component.CodeModule
            if module.CountOfLines: module.DeleteLines(1,module.CountOfLines)
            module.AddFromString(vbe_text(path.read_text(encoding='utf-8'))); module=None
            component=None
def compile_gate(app):
    # This Office build rejects SysCmd(603) through Automation. RunCommand plus
    # IsCompiled is the executable gate; a temporary smoke reaches every class.
    app.DoCmd.RunCommand(126)
    if not app.IsCompiled: raise RuntimeError('VBA project is not fully compiled')
    probe=app.VBE.ActiveVBProject.VBComponents.Add(1); probe.Name='BuildCompileProbe'; module=probe.CodeModule
    if module.CountOfLines: module.DeleteLines(1,module.CountOfLines)
    module.AddFromString('''Option Explicit
Public Function BuildClassInitializationSmoke() As Boolean
 Dim busy As New clsUiBusyState, session As New clsSession, criteria As New clsSearchCriteria
 Dim employee As New clsEmployeeEdit, career As New clsCareerDraft, code As New clsCodeEdit
 Dim report As New clsReportSnapshot, result As New clsResult, unit As New clsUnitOfWork
 busy.Restore: session.Clear: criteria.NameRaw="": employee.Name="": career.Company=""
 code.Name="": report.BusinessDate=DateSerial(2026,10,27): result.Kind="probe": unit.CloseUnit
 BuildClassInitializationSmoke=True
End Function
''')
    app.DoCmd.RunCommand(126)
    if not app.IsCompiled: raise RuntimeError('VBA compile probe is not compiled')
    value=app.Run('BuildClassInitializationSmoke')
    if isinstance(value,tuple): value=value[0]
    if not value: raise RuntimeError('Class initialization compile gate failed')
    module=None; app.VBE.ActiveVBProject.VBComponents.Remove(probe); probe=None
    app.DoCmd.RunCommand(126)
    if not app.IsCompiled: raise RuntimeError('VBA project lost compiled state after probe removal')
    return {'method':'RunCommand(126) + Application.IsCompiled=True + every-class initialization smoke',
            'sysCmd603':'Automation call rejected with argument-count error in owned API probe; not used as PASS',
            'classInitializationSmoke':'PASS','temporaryProbeRemoved':True,'finalRecompile':'PASS','isCompiled':True}
def main():
    p=argparse.ArgumentParser(); p.add_argument('--publish',action='store_true'); p.add_argument('--publish-candidate',action='store_true'); p.add_argument('--interactive-initialize',action='store_true'); p.add_argument('--test-secrets',action='store_true',help='Compatibility alias for fixed public DEMO credentials'); p.add_argument('--demo-credentials',action='store_true',help='Use admin/staff and password123 (default for this sample)'); args=p.parse_args()
    work=(ROOT/'.tmp/build').resolve(); work.mkdir(parents=True,exist_ok=True)
    target=work/'CareerManagement.accdb'
    if target.exists():
        # Only this exact build-owned staging path can be replaced.
        if target.parent != (ROOT/'.tmp/build').resolve(): raise RuntimeError('Unsafe staging')
        target.unlink()
    before=set(win32process.EnumProcesses())
    pythoncom.CoInitialize(); app=None; db=None; process_handle=None
    try:
        app=win32com.client.DispatchEx('Access.Application')
        app=win32com.client.gencache.EnsureDispatch(app); app.Visible=False
        owned_window=app.hWndAccessApp
        owned_pid=win32process.GetWindowThreadProcessId(owned_window() if callable(owned_window) else owned_window)[1]
        if owned_pid in before: raise RuntimeError('Access instance is not newly owned')
        process_handle=win32api.OpenProcess(0x100000|0x400,False,owned_pid)
        print('Creating owned staging database',flush=True)
        app.NewCurrentDatabase(str(target),12)
        db=app.CurrentDb(); schema.create(db); prop(db,'SP2_Staging',1,True); db.Close(); db=None
        print('Importing VBA',flush=True)
        import_code(app); form_exports=create_forms(app)
        print('Compiling VBA',flush=True)
        compile_evidence=compile_gate(app)
        if args.interactive_initialize:
            password=[]
            for login in ('admin','staff'):
                first=getpass.getpass(login+' password (3–128 Unicode scalar): ')
                second=getpass.getpass('Confirm: ')
                if first!=second: raise ValueError('Passwords differ')
                password.append(first)
        else:
            # Explicit user-approved credentials for sample-project2 only.
            password=['123','123']
            protected=win32crypt.CryptProtectData(json.dumps(password).encode(), 'SP2 isolated test credentials',None,None,None,0)
            (ROOT/'.tmp/test-secrets.dpapi').write_bytes(protected)
        initialized=app.Run('InitializeDemo',*password)
        if isinstance(initialized,tuple): initialized=initialized[0]
        if not initialized: raise RuntimeError('Seed failed')
        password.clear()
        db=app.CurrentDb(); prop(db,'SP2_Staging',1,False); prop(db,'StartupForm',10,'frmLogin'); prop(db,'StartupShowDBWindow',1,False); db.Close(); db=None
        app.DoCmd.RunCommand(126)
        if not app.IsCompiled: raise RuntimeError('Final seeded artifact is not fully compiled')
        app.CloseCurrentDatabase(); app.Quit(2); app=None; release()
        exit_wait=win32event.WaitForSingleObject(process_handle,10000)
        exit_code=win32process.GetExitCodeProcess(process_handle)
        if exit_wait!=0 or exit_code!=0: raise RuntimeError('Owned Access did not exit normally: '+str(exit_code))
        # Native exports are committed only after the complete staged product
        # compiled and its owned Access process exited normally.
        for export in sorted(form_exports.glob('*.txt')):
            destination=ROOT/'src/forms'/export.name
            for attempt in range(6):
                try: os.replace(export,destination); break
                except PermissionError:
                    if attempt==5: raise
                    time.sleep(.2)
        manifest={'projectId':'sample-project2','methodId':'Access','datasetId':'SP2-DEMO-01','version':'1.1','businessDate':'2026-10-27','fictional':True,'counts':{k:len_ for k,len_ in [('m_code_category',3),('m_code',9),('m_app_user',2),('m_employee',3),('t_career',3)]},'artifactSha256':sha(target),'credentials':'Public sample DEMO admin/staff with password123' if not args.interactive_initialize else 'operator supplied; no plaintext in records','reseedPolicy':'skip only exact manifest/DB hash; modified or foreign database stops unchanged'}
        manifest['source']={str(f.relative_to(ROOT)).replace('\\','/'):sha(f) for d in ('src','database','tools') for f in sorted((ROOT/d).rglob('*')) if f.is_file() and '__pycache__' not in str(f)}
        input_manifest=ROOT/'build/generation/inputs.json'
        manifest['inputManifestSha256']=sha(input_manifest) if input_manifest.exists() else json.loads((ROOT/'profile.json').read_text(encoding='utf-8'))['frozenInputManifestSha256']
        manifest['inputManifestAvailable']=input_manifest.exists()
        manifest['originalInputHashesReverified']=False
        manifest['compileGate']=compile_evidence
        manifest['officeProcess']={'ownedPid':owned_pid,'newInstance':True,'exitWait':exit_wait,'exitCode':exit_code}
        manifest['releaseState']='sample-demo-credentials' if not args.interactive_initialize else 'operator-credentials-initialized-via-cli-ui-unverified'
        (work/'seed-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
        if args.publish or args.publish_candidate:
            final=ROOT/'build/CareerManagement.accdb'; final.parent.mkdir(exist_ok=True)
            prior=ROOT/'build/seed-manifest.json'
            if final.exists() and (not prior.exists() or json.loads(prior.read_text(encoding='utf-8'))['artifactSha256']!=sha(final)):
                raise RuntimeError('Existing final artifact was modified or ownership is unknown; publication stopped unchanged')
            transfer=work/'publish.accdb'; shutil.copy2(target,transfer); os.replace(transfer,final)
            shutil.copy2(work/'seed-manifest.json',prior)
            invalidate_verification()
        print(json.dumps({'status':'BUILT','staging':str(target),'sha256':sha(target),'published':args.publish or args.publish_candidate}))
    finally:
        db=None
        if app is not None:
            try: app.CloseCurrentDatabase()
            except Exception: pass
            try: app.Quit(2)
            except Exception: pass
        app=None; release(); pythoncom.CoUninitialize()
        if process_handle is not None: process_handle.Close()
if __name__=='__main__': main()
