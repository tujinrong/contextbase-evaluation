"""Owned Access session. No input injection, window movement or periodic COM polling."""
from pathlib import Path
import ctypes,datetime as dt,hashlib,json,shutil,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'.tmp/native-current'
HERE.mkdir(parents=True,exist_ok=True)
HARNESS=ROOT/'tests/NativeHarness.bas'
sys.path.insert(0,str(ROOT/'tools'))
import build
import data_integrity
import win32gui
FINAL='4629fe0c714e2ab3d34b75134c1f482d1cad5431075c08c6e00d67808acab0fc'
LOG=HERE/'session.jsonl'
def log(event,**data):
    item={'at':dt.datetime.now(dt.timezone.utc).isoformat(),'event':event,**data}
    with LOG.open('a',encoding='utf8') as f:f.write(json.dumps(item,ensure_ascii=False)+'\n')
    print(json.dumps(item,ensure_ascii=False),flush=True)
def step(name,fn):
    log('before',step=name);value=fn();log('after',step=name);return value
def scalar(x):
    return x if x is None or isinstance(x,(str,int,float,bool)) else str(type(x).__name__)
def state(app):
    f=app.Screen.ActiveForm
    result={'form':f.Name,'insideWidthTwips':f.InsideWidth,'insideHeightTwips':f.InsideHeight,'currentSectionTopTwips':f.CurrentSectionTop,'currentSectionLeftTwips':f.CurrentSectionLeft,'sectionHeightsTwips':{str(i):f.Section(i).Height for i in (0,1,2)}}
    try:result['activeControl']=app.Screen.ActiveControl.Name
    except Exception:result['activeControl']=None
    flags=app.Run('NativeFlags');flags=flags[0] if isinstance(flags,tuple) else flags
    result['flags']=dict(zip(('employeeDirty','draftDirty','busy','loading'),[x.lower()=='true' for x in str(flags).split('|')]))
    viewport=app.Run('NativeViewportState');result['searchReturnViewport']=str(viewport[0] if isinstance(viewport,tuple) else viewport)
    failure=app.Run('NativeLayoutFailure');result['layoutFailure']=str(failure[0] if isinstance(failure,tuple) else failure)
    if f.Name=='frmEmployeeSearch':
        control=f.Controls('lstEmployees');properties={}
        for name in ('ListCount','ListIndex','Top','Left','Height','Width','ColumnCount','ColumnWidths','ColumnHeads','MultiSelect','TopIndex','ScrollBars','hWnd'):
            try:properties[name]={'supported':True,'value':scalar(getattr(control,name))}
            except Exception as error:properties[name]={'supported':False,'errorType':type(error).__name__}
        result['listProperties']=properties;control=None
    if f.Name=='frmEmployeeEditor':
        t=f.Controls('tabEmployee');result['tab']={'value':scalar(t.Value),'topTwips':t.Top,'heightTwips':t.Height,'visible':bool(t.Visible)};t=None
    f=None
    return result
class SCROLLINFO(ctypes.Structure):
    _fields_=[('cbSize',ctypes.c_uint),('fMask',ctypes.c_uint),('nMin',ctypes.c_int),('nMax',ctypes.c_int),('nPage',ctypes.c_uint),('nPos',ctypes.c_int),('nTrackPos',ctypes.c_int)]
def window_info(hwnd,pid):
    children=[];handles=[]
    win32gui.EnumChildWindows(hwnd,lambda child,_:handles.append(child),None)
    for child in [hwnd]+handles:
        if build.win32process.GetWindowThreadProcessId(child)[1]!=pid:continue
        item={'hwnd':child,'className':win32gui.GetClassName(child),'visible':bool(win32gui.IsWindowVisible(child)),'rectPx':win32gui.GetWindowRect(child),'clientRectPx':win32gui.GetClientRect(child),'styleHex':hex(win32gui.GetWindowLong(child,-16)&0xffffffff),'scroll':{}}
        for name,bar in (('horizontal',0),('vertical',1)):
            info=SCROLLINFO();info.cbSize=ctypes.sizeof(info);info.fMask=0x17
            ok=ctypes.windll.user32.GetScrollInfo(ctypes.c_void_p(child),bar,ctypes.byref(info))
            item['scroll'][name]={'available':bool(ok),**({key:getattr(info,key) for key in ('nMin','nMax','nPage','nPos','nTrackPos')} if ok else {})}
        children.append(item)
    return {'windowDpi':ctypes.windll.user32.GetDpiForWindow(ctypes.c_void_p(hwnd)),'windows':children,'scope':'Read-only window geometry/styles/GetScrollInfo; no text/value capture or UI input'}
def main():
    source=ROOT/'build/CareerManagement.accdb';target=HERE/'CareerManagement-native.accdb';manifest=ROOT/'build/seed-manifest.json'
    frozen=json.loads(manifest.read_text('utf8'));assert build.sha(source)==FINAL==frozen['artifactSha256']
    assert all(build.sha(ROOT/p)==s for p,s in frozen['source'].items())
    if target.with_suffix('.laccdb').exists():raise RuntimeError('Native target is live; refusing replacement')
    if target.exists():
        prior=json.loads((HERE/'ready.json').read_text('utf8'))
        events=[json.loads(line) for line in LOG.read_text('utf8').splitlines()]
        last=events[-1]
        assert prior['copy']==str(target) and prior['initialCopySha256']==prior['finalSha256']
        assert last['event']=='owned-exit' and last['ownedPid']==prior['ownedPid'] and last['exitCode']==0 and last['exitWait']==0
        assert prior['ownedPid'] not in set(build.win32process.EnumProcesses())
        target.unlink()  # Exact closed copy owned by this helper; no recursive cleanup.
    shutil.copy2(source,target);assert build.sha(target)==FINAL
    sourceDigest=hashlib.sha256(json.dumps(frozen['source'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
    helperSha=build.sha(Path(__file__));harnessSha=build.sha(HARNESS)
    log('initial-copy',copy=str(target),initialCopySha256=build.sha(target),finalSha256=FINAL,sourceTreeSha256=sourceDigest,seedManifestSha256=build.sha(manifest),helperSha256=helperSha,harnessSha256=harnessSha,oldHelperUsed=False)
    before=set(build.win32process.EnumProcesses());app=None;handle=None;pid=None
    build.pythoncom.CoInitialize()
    try:
        app=step('new-owned-access',lambda:build.win32com.client.gencache.EnsureDispatch(build.win32com.client.DispatchEx('Access.Application')))
        raw=app.hWndAccessApp;hwnd=int(raw() if callable(raw) else raw);pid=build.win32process.GetWindowThreadProcessId(hwnd)[1]
        assert pid not in before
        handle=build.win32api.OpenProcess(0x100000|0x400,False,pid)
        log('owned-office',ownedPid=pid,hwnd=hwnd,copy=str(target))
        step('open-owned-normal-database',lambda:app.OpenCurrentDatabase(str(target)))
        component=app.VBE.ActiveVBProject.VBComponents.Add(1);component.Name='NativeHarness';module=component.CodeModule
        if module.CountOfLines:module.DeleteLines(1,module.CountOfLines)
        module.AddFromString(build.vbe_text((HARNESS).read_text('utf8')));module=None;component=None
        gate=step('compile-all-classes-remove-probe-recompile',lambda:build.compile_gate(app))
        app.Visible=True
        prepared=step('business-api-auth-and-search-preparation',lambda:app.Run('NativePrepare','search','123'))
        if isinstance(prepared,tuple):prepared=prepared[0]
        if not prepared:raise RuntimeError('Business API preparation returned False')
        ready={'ownedPid':pid,'hwnd':hwnd,'copy':str(target),'initialCopySha256':FINAL,'finalSha256':build.sha(source),'sourceTreeSha256':sourceDigest,'helperSha256':helperSha,'harnessSha256':harnessSha,'compile':gate,'state':state(app),'inputEvidence':'COM business preparation only; native input is root Sky responsibility','commands':['state','search-values','form-values','data-digest','windows','fixture-search-rows','prepare login|menu|search-unsearched|search|editor-new|editor-edit|careers|code','quit']}
        (HERE/'ready.json').write_text(json.dumps(ready,ensure_ascii=False,indent=2)+'\n','utf8');log('READY',**ready)
        for line in sys.stdin:
            command=line.strip()
            if command=='quit':break
            try:
                if command=='state':log('state',**state(app))
                elif command=='search-values':
                    observed=app.Run('NativeSearchValues');observed=observed[0] if isinstance(observed,tuple) else observed
                    log('search-values',**json.loads(str(observed)))
                elif command=='form-values':
                    observed=app.Run('NativeFormValues');observed=observed[0] if isinstance(observed,tuple) else observed
                    log('form-values',**json.loads(str(observed)))
                elif command=='data-digest':
                    assert Path(app.CurrentProject.FullName).resolve()==target.resolve()
                    assert build.sha(source)==FINAL
                    observed=data_integrity.snapshot(target)
                    log('data-digest',**observed)
                elif command=='windows':log('windows',**window_info(hwnd,pid))
                elif command=='fixture-search-rows':
                    assert Path(app.CurrentProject.FullName).resolve()==target.resolve()
                    assert build.sha(source)==FINAL and all(build.sha(ROOT/p)==s for p,s in frozen['source'].items())
                    assert build.sha(Path(__file__))==helperSha and build.sha(HARNESS)==harnessSha
                    check=app.hWndAccessApp;check=int(check() if callable(check) else check)
                    assert check==hwnd and build.win32process.GetWindowThreadProcessId(check)[1]==pid
                    log('before-fixture-search-rows',copy=str(target),initialCopySha256=FINAL,finalSha256=build.sha(source),scope='Only normal business SaveEmployee/read/search APIs; namespace910001..910197; no seed/reset or native input')
                    result=app.Run('NativeFixtureSearchRows');result=result[0] if isinstance(result,tuple) else result
                    assert build.sha(source)==FINAL
                    log('fixture-search-rows',summary=str(result),state=state(app),finalArtifactUnchanged=True)
                elif command.startswith('prepare ') and command[8:] in ('login','menu','search-unsearched','search','editor-new','editor-edit','careers','code'):
                    result=app.Run('NativePrepare',command[8:],'123');log('prepared',screen=command[8:],result=bool(result[0] if isinstance(result,tuple) else result),state=state(app))
                else:log('unknown-command')
            except Exception as error:log('command-error',errorType=type(error).__name__,hresult=getattr(error,'hresult',None))
    except Exception as error:
        log('failure',errorType=type(error).__name__,hresult=getattr(error,'hresult',None));raise
    finally:
        if app is not None:
            try:app.CloseCurrentDatabase()
            except Exception as error:log('close-error',errorType=type(error).__name__)
            try:app.Quit(2)
            except Exception as error:log('quit-error',errorType=type(error).__name__)
        app=None;build.release();build.pythoncom.CoUninitialize()
        if handle is not None:
            wait=build.win32event.WaitForSingleObject(handle,10000);exitCode=build.win32process.GetExitCodeProcess(handle);handle.Close()
            log('owned-exit',ownedPid=pid,exitWait=wait,exitCode=exitCode,finalArtifactUnchanged=build.sha(source)==FINAL)
if __name__=='__main__':main()
