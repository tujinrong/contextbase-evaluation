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
if str(ROOT/'tools') not in sys.path:
    sys.path.insert(0,str(ROOT/'tools'))
from vba_text import read_vba_source, vbe_text
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
        # Contract-only independent review belongs to the current frozen spec,
        # not the old product. Keep it and root-owned native evidence. Product
        # gates are invalidated explicitly; all other current test reports are
        # rewritten by their owners and checked against the final artifact SHA.
        for name in ('ui-observations.json','ui-conformance.json'):
            old=target/name
            if old.exists():old.unlink()
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
        ctl.BackColor=16777215 if kind in (109,110,111) else 15724527
    if kind in (104,123):
        ctl.UseTheme=False; ctl.Shape=0; ctl.Gradient=0; ctl.BorderStyle=1
        ctl.HoverThemeColorIndex=-1; ctl.HoverForeThemeColorIndex=-1
        ctl.PressedThemeColorIndex=-1; ctl.PressedForeThemeColorIndex=-1
        ctl.HoverColor=15066597; ctl.PressedColor=14013909
        ctl.HoverForeColor=0; ctl.PressedForeColor=0
    else:
        ctl.SpecialEffect=0; ctl.BorderStyle=0 if kind==100 else 1
    if kind in (100,109,111,104,123): ctl.BackStyle=0 if kind==100 else 1
def create_forms(app, selected=None, code_factory=None):
    """Create the specified native Sections and empty Header Pages.

    Runtime visibility and safe focus transitions belong to VBA, not Pages.
    The source-only production helper never reads specification/tests data.
    """
    exports=ROOT/'.tmp/build/forms'; exports.mkdir(parents=True,exist_ok=True)
    casts={100:'_Label',109:'_Textbox',104:'_CommandButton',106:'_Checkbox',110:'_ListBox',111:'_Combobox',123:'_TabControl'}
    for name,d in forms.FORMS.items():
        if selected is not None and name not in selected: continue
        print('Designing '+name,flush=True)
        template=ROOT/'.tmp/build/bootstrap-form.txt'
        template.write_text('Version =20\r\nVersionRequired =20\r\nBegin Form\r\n    Width =18900\r\n    Begin\r\n        Begin FormHeader\r\n            Height =3000\r\n            Name ="FormHeader"\r\n        End\r\n        Begin Section\r\n            Height =10000\r\n            Name ="Detail"\r\n        End\r\n        Begin FormFooter\r\n            Height =1500\r\n            Name ="FormFooter"\r\n        End\r\n    End\r\nEnd\r\n',encoding='utf-16')
        app.LoadFromText(2,name,str(template)); app.DoCmd.OpenForm(name,1)
        f=app.Forms(name);f.RecordSource='';f.Caption=d['caption'];f.Width=d['width']
        f.DefaultView=0;f.NavigationButtons=False;f.RecordSelectors=False;f.DividingLines=False
        f.AutoCenter=False;f.AutoResize=False;f.FitToScreen=False;f.BorderStyle=2
        f.PopUp=False;f.Modal=False;f.ScrollBars=3;f.KeyPreview=True;f.TimerInterval=1000
        for sec in (1,0,2):
            section=f.Section(sec);section.BackThemeColorIndex=-1;section.BackColor=15724527;section=None
        for event in ('OnLoad','OnActivate','OnResize','OnTimer','OnKeyDown','OnMouseDown','OnUnload','OnClose'):
            setattr(f,event,'[Event Procedure]')
        app.DoCmd.Save(2,name);f.HasModule=True
        section_order={}
        for c in d['controls']:
            # Only attached Labels have a Control parent. Page inputs remain
            # physically in Detail and carry a logical membership Tag.
            parent=c['name'][4:] if c['name'].startswith('lbl_') else ''
            ctl=app.CreateControl(name,c['kind'],c['section'],parent,'',c['x'],c['y'],c['w'],c['h'])
            ctl=win32com.client.CastTo(ctl,casts[c['kind']]);ctl.Name=c['name']
            if c['kind'] in (100,104):ctl.Caption=c['label'].replace('\n','\r\n')
            classic_control(ctl,c['kind'],header=c.get('bold',False))
            ctl.Tag='PAGE:'+str(c['page']) if 'page' in c else 'COMMON'
            ctl.Visible=c.get('visible',True) and ('page' not in c or c['page']==0)
            if c['kind'] in (109,111,110,106):ctl.ControlSource=''
            if c['kind']!=100:
                ordinal=section_order.get(c['section'],0);ctl.TabIndex=ordinal;section_order[c['section']]=ordinal+1
                ctl.TabStop=True
                # Access TabControl has no OnGotFocus property; Detail inputs
                # own LastEditFocus. Do not borrow the MSForms interface.
                if c['kind']!=123:ctl.OnGotFocus='[Event Procedure]'
            if c['kind']==104:
                ctl.OnClick='[Event Procedure]';ctl.Default=c.get('default',False);ctl.Cancel=False
            if c['kind']==109:
                ctl.OnChange='[Event Procedure]';ctl.BeforeUpdate='[Event Procedure]'
                ctl.InputMask='Password' if c.get('password') else '';ctl.Format=''
                if c.get('multiline'):ctl.EnterKeyBehavior=True;ctl.ScrollBars=2
                if c.get('readonly'):ctl.Enabled=True;ctl.Locked=True;ctl.TabStop=True
                if c.get('pending_owner'):
                    ctl.Enabled=False;ctl.Locked=True;ctl.TabStop=False
                    ctl.EnterKeyBehavior=False;ctl.ScrollBars=0
                    ctl.ControlTipText=c['hint'];ctl.StatusBarText=c['hint']
            if c['kind'] in (111,106,110):ctl.AfterUpdate='[Event Procedure]'
            if c['kind']==111:
                ctl.OnChange='[Event Procedure]';ctl.OnNotInList='[Event Procedure]'
                ctl.OnClick='[Event Procedure]';ctl.OnKeyUp='[Event Procedure]'
                ctl.OnMouseDown='[Event Procedure]';ctl.OnMouseUp='[Event Procedure]'
                ctl.RowSourceType='Value List';ctl.RowSource='';ctl.ColumnCount=2;ctl.BoundColumn=1
                ctl.ColumnWidths='0;3300';ctl.LimitToList=True;ctl.AutoExpand=True
            if c['kind']==110:
                ctl.RowSourceType=c['callback'];ctl.RowSource='';ctl.ColumnCount=c['columns'];ctl.BoundColumn=1
                ctl.ColumnWidths=c['widths'];ctl.MultiSelect=0;ctl.ColumnHeads=False
            if c['kind']==123:
                ctl.OnChange='[Event Procedure]';ctl.Style=0;ctl.MultiRow=False
                ctl.TabFixedHeight=510;ctl.TabFixedWidth=1800
                for i,(page_name,caption) in enumerate(c['pages']):
                    page=ctl.Pages(i) if i<ctl.Pages.Count else ctl.Pages.Add()
                    page.Name=page_name;page.Caption=caption;page=None
                ctl.Height=c['h']
            ctl=None
        # Native TabIndex is Section-local. Explicit cross-section/hidden-page
        # keyboard routing is authored in VBA and verified by actual keys.
        order=forms.TAB_ORDER[name]
        if isinstance(order,dict):order=list(dict.fromkeys(order[0]+order[1]))
        section_order={}
        for control_name in order:
            c=next(c for c in d['controls'] if c['name']==control_name)
            ctl=win32com.client.CastTo(f.Controls(control_name),casts[c['kind']])
            ordinal=section_order.get(c['section'],0);ctl.TabIndex=ordinal;section_order[c['section']]=ordinal+1;ctl=None
        for c in d['controls']:
            if c['kind']!=109 or not c.get('pending_owner'):continue
            ctl=win32com.client.CastTo(f.Controls(c['name']),casts[109])
            ordinal=section_order.get(c['section'],0);ctl.TabIndex=ordinal;section_order[c['section']]=ordinal+1;ctl=None
        for sec,h in zip((1,0,2),d['sections']):f.Section(sec).Height=h;f.Section(sec).Visible=h>0
        f.Width=d['width']
        module=f.Module
        if module.CountOfLines:module.DeleteLines(1,module.CountOfLines)
        module.AddFromString(vbe_text((code_factory or forms.module_code)(name,d)));module=None
        app.DoCmd.Save(2,name);app.DoCmd.Close(2,name,1);f=None
        export=exports/(name+'.txt')
        if export.exists():export.unlink()
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
            module.AddFromString(vbe_text(read_vba_source(path))); module=None
            component=None
def compile_gate(app):
    # This Office build rejects SysCmd(603) through Automation. RunCommand plus
    # IsCompiled is the executable gate; a temporary smoke reaches every class.
    app.DoCmd.RunCommand(126)
    if not app.IsCompiled: raise RuntimeError('VBA project is not fully compiled')
    probe=app.VBE.ActiveVBProject.VBComponents.Add(1); probe.Name='BuildCompileProbe'; module=probe.CodeModule
    if module.CountOfLines: module.DeleteLines(1,module.CountOfLines)
    smoke='''Option Explicit
Public Function BuildClassInitializationSmoke() As Boolean
 Dim busy As New clsUiBusyState, session As New clsSession, criteria As New clsSearchCriteria
 Dim employee As New clsEmployeeEdit, career As New clsCareerDraft, code As New clsCodeEdit
 Dim report As New clsReportSnapshot, result As New clsResult, unit As New clsUnitOfWork
 busy.Restore: session.Clear: criteria.NameRaw="": employee.Name="": career.Company=""
 code.Name="": report.BusinessDate=DateSerial(2026,10,27): result.Kind="probe": unit.CloseUnit
 BuildClassInitializationSmoke=True
End Function
'''
    # Every authored class, including added UI/return-state classes, must be
    # instantiated. TypeName forces As New initialization before probe removal.
    additions=[]
    for index,path in enumerate(sorted((ROOT/'src/classes').glob('*.cls'))):
        additions += [' Dim probeClass'+str(index)+' As New '+path.stem,
                      ' If TypeName(probeClass'+str(index)+') <> "'+path.stem+'" Then Err.Raise 5']
    smoke=smoke.replace(' BuildClassInitializationSmoke=True','\n'.join(additions)+'\n BuildClassInitializationSmoke=True')
    module.AddFromString(smoke)
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
            'classInitializationSmoke':'PASS','classes':[p.stem for p in sorted((ROOT/'src/classes').glob('*.cls'))],'temporaryProbeRemoved':True,'finalRecompile':'PASS','isCompiled':True}

def remove_owned_application_objects(app):
    """Replace app objects on the owned staging copy, never business tables."""
    expected=set(forms.FORMS)
    actual={item.Name for item in app.CurrentProject.AllForms}
    if actual!=expected:raise RuntimeError('Existing Form inventory differs; refusing an unreviewed application replacement')
    for name in sorted(actual):
        if app.CurrentProject.AllForms(name).IsLoaded:app.DoCmd.Close(2,name,2)
    for name in sorted(actual):app.DoCmd.DeleteObject(2,name)
    project=app.VBE.ActiveVBProject
    names=[component.Name for component in project.VBComponents if component.Type in (1,2)]
    for name in names:project.VBComponents.Remove(project.VBComponents(name))
    project=None

def suppress_owned_startup(path):
    """Avoid executing old UI while replacing objects on the staging copy."""
    pythoncom.CoInitialize();engine=db=None
    try:
        engine=win32com.client.DispatchEx('DAO.DBEngine.120');db=engine.OpenDatabase(str(path))
        if 'StartupForm' in {item.Name for item in db.Properties}:db.Properties.Delete('StartupForm')
        db.Close();db=None
    finally:
        if db is not None:db.Close()
        db=engine=None;release();pythoncom.CoUninitialize()
def main():
    p=argparse.ArgumentParser(); p.add_argument('--publish',action='store_true'); p.add_argument('--publish-candidate',action='store_true'); p.add_argument('--preserve-existing',type=Path,help='Copy this existing ACCDB and replace only application Forms/VBA, preserving every typed business row'); p.add_argument('--interactive-initialize',action='store_true'); p.add_argument('--test-secrets',action='store_true',help='Compatibility alias for fixed public DEMO credentials'); p.add_argument('--demo-credentials',action='store_true',help='Use admin/staff and password123 (default for this sample)'); args=p.parse_args()
    if args.preserve_existing and args.interactive_initialize:raise RuntimeError('Preservation cannot initialize credentials')
    work=(ROOT/'.tmp/build').resolve(); work.mkdir(parents=True,exist_ok=True)
    target=work/'CareerManagement.accdb'
    if target.exists():
        # Only this exact build-owned staging path can be replaced.
        if target.parent != (ROOT/'.tmp/build').resolve(): raise RuntimeError('Unsafe staging')
        target.unlink()
    original_sha=None;prior_data=None;integrity=None
    if args.preserve_existing:
        original=args.preserve_existing.resolve()
        if not original.is_file() or original.suffix.lower()!='.accdb':raise RuntimeError('Explicit existing ACCDB required')
        if original.with_suffix('.laccdb').exists():raise RuntimeError('Existing database is live; preservation stopped before copying')
        original_sha=sha(original);shutil.copy2(original,target)
        if sha(target)!=original_sha:raise RuntimeError('Preserved input copy differs')
        integrity=load(ROOT/'tools/data_integrity.py');prior_data=integrity.snapshot(target)
        if not prior_data['sourceUnmodified']:raise RuntimeError('Read-only preservation inspection modified its owned copy')
        suppress_owned_startup(target)
    before=set(win32process.EnumProcesses())
    pythoncom.CoInitialize(); app=None; db=None; process_handle=None
    try:
        app=win32com.client.DispatchEx('Access.Application')
        app=win32com.client.gencache.EnsureDispatch(app); app.Visible=False
        owned_window=app.hWndAccessApp
        owned_pid=win32process.GetWindowThreadProcessId(owned_window() if callable(owned_window) else owned_window)[1]
        if owned_pid in before: raise RuntimeError('Access instance is not newly owned')
        process_handle=win32api.OpenProcess(0x100000|0x400,False,owned_pid)
        print(json.dumps({'step':'owned-office','pid':owned_pid,'hwnd':owned_window() if callable(owned_window) else owned_window,'staging':str(target)}),flush=True)
        if args.preserve_existing:
            print('Opening owned existing-data staging copy',flush=True)
            app.OpenCurrentDatabase(str(target),True)
            remove_owned_application_objects(app)
        else:
            print('Creating new isolated DEMO staging database',flush=True)
            app.NewCurrentDatabase(str(target),12)
            db=app.CurrentDb(); schema.create(db); prop(db,'SP2_Staging',1,True); db.Close(); db=None
        print('Importing VBA',flush=True)
        import_code(app); form_exports=create_forms(app)
        print('Compiling VBA',flush=True)
        compile_evidence=compile_gate(app)
        if args.preserve_existing:
            password=[]
        elif args.interactive_initialize:
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
        if not args.preserve_existing:
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
        preservation=None
        if args.preserve_existing:
            after_data=integrity.snapshot(target)
            if not after_data['sourceUnmodified'] or prior_data['schemaFingerprint']!=after_data['schemaFingerprint'] or prior_data['businessDigest']!=after_data['businessDigest']:
                raise RuntimeError('Existing business data/schema changed; publication stopped')
            if sha(original)!=original_sha:raise RuntimeError('Original existing database changed during regeneration')
            preservation={'originalArtifactSha256':original_sha,'before':prior_data,'after':after_data,'allBusinessRowsPreserved':True,'schemaPreserved':True,'credentialsReset':False,'seedExecuted':False}
            (work/'data-preservation.json').write_text(json.dumps(preservation,ensure_ascii=False,indent=2),encoding='utf-8')
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
        if preservation:
            manifest['counts']={item['table']:item['rowCount'] for item in preservation['after']['tables']}
            manifest['preservation']=preservation
            manifest['credentials']='Existing verifier/failed count/lock/user IDs/roles preserved exactly; no credential initialization'
        manifest['officeProcess']={'ownedPid':owned_pid,'newInstance':True,'exitWait':exit_wait,'exitCode':exit_code}
        manifest['releaseState']='existing-data-and-credentials-preserved-ui-unverified' if preservation else 'sample-demo-credentials' if not args.interactive_initialize else 'operator-credentials-initialized-via-cli-ui-unverified'
        (work/'seed-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
        if args.publish or args.publish_candidate:
            final=ROOT/'build/CareerManagement.accdb'; final.parent.mkdir(exist_ok=True)
            prior=ROOT/'build/seed-manifest.json'
            if final.exists():
                if not preservation:raise RuntimeError('Fresh DEMO initialization cannot replace an existing final ACCDB; use explicit preservation')
                if sha(final)!=original_sha:raise RuntimeError('Existing final artifact changed after preservation; publication stopped unchanged')
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
