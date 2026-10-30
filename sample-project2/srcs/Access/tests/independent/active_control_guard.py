"""API-only ActiveControl regression, bound to an unpublished staging build."""
from pathlib import Path
import argparse,datetime as dt,gc,hashlib,importlib.util,json,shutil,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
REPO=ROOT.parents[2]
BOUNDARY=(ROOT/'.tmp/active-control-guard').resolve()
sys.path.insert(0,str(ROOT/'tools'))
import build
spec=importlib.util.spec_from_file_location('guard_data_getters',ROOT/'tests/independent/pending_api.py')
getters=importlib.util.module_from_spec(spec);spec.loader.exec_module(getters)
SUITE=ROOT/'tests/independent/ActiveControlGuardSuite.bas'
EMPTY=ROOT/'tests/independent/active-control-empty-form.txt'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ident(p):return {'file':p.relative_to(REPO).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
def scalar(value):return value[0] if isinstance(value,(tuple,list)) else value
def business(value):return {k:value[k] for k in ['tables','schemaFingerprint','businessDigest']}
def path_inside(value):
    p=value.absolute();assert p.resolve()==p and p.is_relative_to(BOUNDARY) and p!=BOUNDARY
    return p
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--artifact',type=Path,required=True);parser.add_argument('--manifest',type=Path,required=True);parser.add_argument('--output-root',type=Path,required=True)
    args=parser.parse_args();artifact=path_inside(args.artifact);manifest=path_inside(args.manifest);work=path_inside(args.output_root)
    assert artifact.is_file() and manifest.is_file() and not work.exists()
    adopted=json.loads(manifest.read_text('utf-8'));artifact_sha=sha(artifact)
    assert adopted['artifactSha256']==artifact_sha and adopted['compileGate']['isCompiled']
    protected=json.loads((BOUNDARY/'source-review.json').read_text('utf-8'))['fixedGuards']
    assert all(sha(ROOT/p)==h for p,h in protected.items())
    source_before={p:sha(ROOT/p) for p in json.loads((ROOT/'build/seed-manifest.json').read_text('utf-8'))['source']}
    work.mkdir(parents=True);target=work/'guard-owned.accdb';out=work/'result.json';shutil.copy2(artifact,target)
    assert sha(target)==artifact_sha
    record={'schemaVersion':1,'startedAt':dt.datetime.now(dt.timezone.utc).isoformat(),'artifact':ident(artifact),'buildManifest':ident(manifest),'nativePass':False,'formalScore':None,
      'scope':'Owned hidden Access COM/VBA method calls and actual property errors, not physical keys/clicks/real visible input or full UI proof',
      'measurementSources':[ident(Path(__file__)),ident(SUITE),ident(EMPTY),ident(ROOT/'tests/independent/pending_api.py'),ident(ROOT/'tools/build.py'),ident(ROOT/'tools/data_integrity.py')],
      'checks':[],'notVerified':[],'issues':[],'normalCases':[],'noActiveCases':[],'noActiveFixture':'not prepared'}
    app=handle=project=component=module=None;pid=None;build.pythoncom.CoInitialize()
    def check(name,actual,expected):record['checks'].append({'id':name,'actual':actual,'expected':expected,'pass':type(actual)==type(expected) and actual==expected})
    def call(name,*values):return json.loads(str(scalar(app.Run(name,*values))))
    try:
        build.suppress_owned_startup(target)
        before_pids=set(build.win32process.EnumProcesses());app=build.win32com.client.gencache.EnsureDispatch(build.win32com.client.DispatchEx('Access.Application'));app.Visible=False
        hwnd=app.hWndAccessApp;hwnd=hwnd() if callable(hwnd) else hwnd;pid=build.win32process.GetWindowThreadProcessId(hwnd)[1];assert pid not in before_pids
        handle=build.win32api.OpenProcess(0x100000|0x400,False,pid);record['ownedOffice']={'pid':pid,'hwnd':hwnd,'newInstance':True,'visibleRequested':False}
        print(json.dumps({'step':'guard-owned-api','pid':pid,'file':str(target)}),flush=True)
        app.OpenCurrentDatabase(str(target),True);assert Path(app.CurrentProject.FullName).resolve()==target
        project=app.VBE.ActiveVBProject;component=project.VBComponents.Add(1);component.Name='ActiveControlGuardSuite';module=component.CodeModule
        if module.CountOfLines:module.DeleteLines(1,module.CountOfLines)
        body='\n'.join(line for line in SUITE.read_text('utf-8').splitlines() if not line.startswith('Attribute '));module.AddFromString(build.vbe_text(body));module=component=None
        app.DoCmd.RunCommand(126);record['testHarnessCompiled']=bool(app.IsCompiled);assert app.IsCompiled
        prepared=call('ACGPrepareOriginal',False);record['normalPreparation']=prepared
        assert 'errorNumber' not in prepared,prepared
        record['dataAfterAuth']=getters.snapshot_live(app,target)
        for reverse,wanted in [(False,'txtName'),(True,'txtEmployeeNo')]:
            actual=call('ACGNormalTab',reverse);record['normalCases'].append({'case':'shift-tab' if reverse else 'tab','actual':actual})
            if 'errorNumber' in actual:record['notVerified'].append({'case':'normal-tab','reason':'API preparation/routing exception','actual':actual});continue
            check('normal.'+str(reverse)+'.keyConsumed',actual['keyAfter'],0);check('normal.'+str(reverse)+'.target',actual['after']['activeName'],wanted)
        for pending in [False,True]:
            actual=call('ACGNormalReturn',pending);record['normalCases'].append({'case':'pending-return' if pending else 'search-return','actual':actual})
            if 'errorNumber' in actual:record['notVerified'].append({'case':'normal-return','reason':'API preparation/routing exception','actual':actual});continue
            check('return.'+str(pending)+'.consumed',actual['keyAfter'],0)
            if pending:
                check('pending-return.raw',actual['after']['pending'],{'cboDepartment':'guard unknown  '})
                check('pending-return.msg016',actual['message'].startswith('選択値が利用できません。候補を再確認してください。'),True)
            else:check('search-return.executed',actual['searchState'],'Searched');check('search-return.oneResult',actual['listCount'],1)
        escaped=call('ACGEscapeUnaccepted');record['unacceptedEscape']=escaped
        if escaped['preparationError']==0:check('escape.new-pending-captured',escaped['after']['pending'].get('cboDepartment'),'guard new unknown  ')
        else:record['notVerified'].append({'case':'pending0-unaccepted-escape','reason':'Programmatic Combo.Text cannot establish native unknown input','errorNumber':escaped['preparationError']})
        hidden=call('ACGPrepareOriginal',True);record['hiddenOriginalPreparation']=hidden
        if hidden.get('activeError')==2474 and hidden.get('activeName') is None:
            record['noActiveFixture']='Original product F03 opened hidden, actual ActiveControl raises2474'
        else:
            assert scalar(app.Run('ACGCleanup'))
            app.DoCmd.DeleteObject(2,'frmEmployeeSearch')
            form_text=work/'empty-form-import.txt';form_text.write_bytes(EMPTY.read_bytes());app.LoadFromText(2,'frmEmployeeSearch',str(form_text));app.DoCmd.OpenForm('frmEmployeeSearch',WindowMode=1)
            record['noActiveFixture']='Owned-copy synthetic empty F03 with no Form event module; proves API guard absence/error handling only, not product focus behavior'
        missing=call('ACGSnapshot');record['noActivePreparation']=missing
        assert missing['activeError']==2474 and missing['activeName'] is None,missing
        for pending in [False,True]:
            for mode in ['pending','key','tab','escape']:
                for key in ([117,9,13,27] if mode!='escape' else [27]):
                    actual=call('ACGRunNoActive',mode,key,pending);record['noActiveCases'].append(actual);prefix=f'absent.{pending}.{mode}.{key}'
                    check(prefix+'.actualError2474',actual['before']['activeError'],2474)
                    check(prefix+'.exception',actual['errorNumber'],0);check(prefix+'.keyUnconsumed',actual['keyAfter'],key)
                    if mode=='pending':check(prefix+'.notHandled',actual['handled'],False)
                    for field in ['layoutFailure','pending','raw','accepted']:check(prefix+'.preserved.'+field,actual['after'][field],actual['before'][field])
        unexpected=call('ACGUnexpectedError');record['unexpectedError']=unexpected
        check('other-error.91',unexpected['helperNumber'],91);check('other-error.notAccepted',unexpected['accepted'],False)
        for field in ['Number','Source','Description']:check('other-error.preserved.'+field,unexpected['helper'+field],unexpected['direct'+field])
        record['dataAfterCases']=getters.snapshot_live(app,target);check('typedDataSchemaUnchanged',business(record['dataAfterCases']),business(record['dataAfterAuth']))
    except Exception as error:record['issues'].append({'type':type(error).__name__,'detail':str(error)[:1200]})
    finally:
        module=component=project=None;gc.collect()
        if app is not None:
            try:record['cleanupFormsClosed']=bool(scalar(app.Run('ACGCleanup')))
            except Exception as error:record['issues'].append({'phase':'cleanup','type':type(error).__name__})
            try:app.CloseCurrentDatabase();app.Quit(2)
            except Exception as error:record['issues'].append({'phase':'quit','type':type(error).__name__})
        app=None;build.release();build.pythoncom.CoUninitialize()
        if handle is not None:
            wait=build.win32event.WaitForSingleObject(handle,10000);code=build.win32process.GetExitCodeProcess(handle);handle.Close();record['ownedOffice'].update(exitWait=wait,exitCode=code)
            if wait!=0 or code!=0:record['issues'].append({'phase':'owned-exit','wait':wait,'exitCode':code})
        record['preservation']={'stagingArtifactUnchanged':sha(artifact)==artifact_sha,'fixed0810InputsUnchanged':all(sha(ROOT/p)==h for p,h in protected.items()),'canonicalSourceUnchangedDuringTest':all(sha(ROOT/p)==h for p,h in source_before.items()),'measurementSourcesUnchanged':all(sha(REPO/e['file'])==e['sha256'] for e in record['measurementSources'])}
        if not all(record['preservation'].values()):record['issues'].append({'phase':'preservation'})
        failed=[x['id'] for x in record['checks'] if not x['pass']]
        record['counts']={'comparisons':len(record['checks']),'failed':len(failed),'issues':len(record['issues']),'notVerified':len(record['notVerified'])};record['failedChecks']=failed
        record['status']='PASS_API_GUARD_SCOPE_WITH_NOT_VERIFIED_CASES' if not failed and not record['issues'] else 'FAIL_OR_INCONCLUSIVE'
        record['finishedAt']=dt.datetime.now(dt.timezone.utc).isoformat();out.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n','utf-8')
        print(json.dumps({'status':record['status'],'counts':record['counts'],'record':str(out),'recordSha256':sha(out)},ensure_ascii=False),flush=True)
    return int(record['status']=='FAIL_OR_INCONCLUSIVE')
if __name__=='__main__':raise SystemExit(main())
