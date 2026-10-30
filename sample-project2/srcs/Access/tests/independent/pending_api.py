"""Independent API-only Pending regression on a new owned copy; never native input."""
from pathlib import Path
import sys,site,os,json,hashlib,datetime as dt,gc,shutil,importlib.util
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf8')
OWNER=Path(__file__).resolve().parents[2];REPO=OWNER.parents[2];WORK=OWNER/'.tmp/pending-api';SUITE=OWNER/'tests/independent/PendingApiSuite.bas';OUT=OWNER/'build/test-results/independent-pending-api.json'
ARTIFACT=OWNER/'build/CareerManagement.accdb';SEED=OWNER/'build/seed-manifest.json';INPUTS=OWNER/'build/generation/inputs.json';CONTRACT=OWNER/'tests/ui-contract.json'
EXPECTED='0810e210184e8b0db2f5868743f61daf26e56fc8a7fe71b1cd501b4543435481';SEED_SHA='6cd654e09ebf3cc20e52f7cd0e9b718819737cf07d36933acf79c8a028160db4';INPUT_SHA='779271c32c63058605c9b61955180cf8a5fd4dfe04e0aa51e1406bff8b6a65c2';CONTRACT_SHA='2bec42d155e91ab26c9d704fb44537ddd95ec5ae3f2937b9a524467dbb79a018'
DEPS=OWNER/'.tmp/python-deps';site.addsitedir(str(DEPS));os.add_dll_directory(str(DEPS/'pywin32_system32'))
import pythoncom,win32com.client,win32api,win32process,win32event
spec=importlib.util.spec_from_file_location('pending_integrity',OWNER/'tools/data_integrity.py');integrity=importlib.util.module_from_spec(spec);spec.loader.exec_module(integrity)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def ident(p):return {'file':p.relative_to(REPO).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
def scalar(v):return v[0] if isinstance(v,(tuple,list)) else v
def business(x):return {k:x[k] for k in ['tables','schemaFingerprint','businessDigest']}
def suppress_startup(p):
 engine=db=None
 try:
  engine=win32com.client.DispatchEx('DAO.DBEngine.120');db=engine.OpenDatabase(str(p),True)
  macros=[d.Name for d in db.Containers('Scripts').Documents]
  if any(n.casefold()=='autoexec' for n in macros):raise RuntimeError('AutoExec exists; refusing runtime startup')
  prior=None
  if 'StartupForm' in {x.Name for x in db.Properties}:prior=db.Properties('StartupForm').Value;db.Properties.Delete('StartupForm')
  db.Close();db=None;return {'autoExecAbsent':True,'removedStartupFormOnOwnedCopyOnly':prior}
 finally:
  if db is not None:db.Close()
  db=engine=None;gc.collect();pythoncom.CoFreeUnusedLibraries()
def check(rows,name,value,expected):rows.append({'id':name,'actual':value,'expected':expected,'pass':type(value)==type(expected) and value==expected})
def helper_checks(rows,state,owner,raw,prefix,visible=True):
 h=state['helpers'][owner]
 for key,wanted in [('value',raw),('visible',visible),('enabled',True),('locked',False),('tabStop',True),('labelVisible',visible),('ownerLabelVisible',False),('ownerLimitToList',True),('ownerBoundColumn',1)]:check(rows,prefix+'.'+key,h[key],wanted)
 check(rows,prefix+'.attachedLabels',h['attachedLabels'],['lbl_txtPending_'+owner]);check(rows,prefix+'.labelCaptionMatchesOwner',h['labelCaption'],h['ownerLabelCaption'])
def snapshot_live(app,target):
 assert Path(app.CurrentProject.FullName).resolve()==target.resolve()
 db=rs=table=field=index=relation=None
 try:
  db=app.CurrentDb();tables=[];schemas=[]
  assert sorted(t.Name for t in db.TableDefs if not t.Name.startswith(('MSys','~')))==sorted(integrity.TABLES)
  for name in integrity.TABLES:
   table=db.TableDefs(name);fields=[]
   for field in table.Fields:
    fields.append({'name':field.Name,'type':field.Type,'size':field.Size,'attributes':field.Attributes,'required':bool(field.Required),'allowZeroLength':bool(field.AllowZeroLength) if field.Type in (10,12) else 'NOT_TEXT','default':integrity.optional_prop(field,'DefaultValue'),'validationRule':integrity.optional_prop(field,'ValidationRule')})
   indices=[]
   for index in table.Indexes:indices.append({'name':index.Name,'primary':bool(index.Primary),'unique':bool(index.Unique),'required':bool(index.Required),'ignoreNulls':bool(index.IgnoreNulls),'fields':[(f.Name,f.Attributes) for f in index.Fields]})
   schema={'table':name,'fields':fields,'indexes':sorted(indices,key=lambda i:i['name'])};schemas.append(schema)
   rs=db.OpenRecordset('SELECT * FROM ['+name+']',4);rows=[]
   while not rs.EOF:
    rows.append([integrity.canonical(rs.Fields(i).Value) for i in range(rs.Fields.Count)]);rs.MoveNext()
   rs.Close();rs=None;rows.sort(key=lambda row:json.dumps(row,ensure_ascii=False,separators=(',',':')))
   tables.append({'table':name,'rowCount':len(rows),'columnCount':len(fields),'typedRowsSha256':integrity.digest({'fields':[(f['name'],f['type']) for f in fields],'rows':rows}),'schemaSha256':integrity.digest(schema)});rows.clear();table=None
  relations=[]
  for relation in db.Relations:
   if relation.Table in integrity.TABLES or relation.ForeignTable in integrity.TABLES:relations.append({'name':relation.Name,'table':relation.Table,'foreignTable':relation.ForeignTable,'attributes':relation.Attributes,'fields':[(f.Name,f.ForeignName) for f in relation.Fields]})
  relations.sort(key=lambda x:x['name'])
  return {'schemaVersion':1,'tables':tables,'schemaFingerprint':integrity.digest({'tables':schemas,'relations':relations}),'businessDigest':integrity.digest(tables),'allFieldsIncludingCredentialsIdsRevisions':True,'rowValuesLogged':False,'mode':'Own app.CurrentDb, fixed SELECT-only dbOpenSnapshot reads; no second process file open or business mutation'}
 finally:
  if rs is not None:rs.Close()
  if db is not None:db.Close()
  db=rs=table=field=index=relation=None;gc.collect()

def main():
 record={'schemaVersion':1,'projectId':'sample-project2','profileId':'Access','runId':'sp2-ui-regenerate-20261029','startedAt':dt.datetime.now(dt.timezone.utc).isoformat(),'scope':'Independent hidden Access runtime API/actual property getter and owned DAO typed-data checks. No UI input, real Dropdown selection, focus/Tab usability, IME, clipboard, native visibility, search/SQL invocation count or acceptance claim.','artifactSha256':EXPECTED,'inputsSha256':INPUT_SHA,'contractSha256':CONTRACT_SHA,'measurementSources':[ident(Path(__file__)),ident(SUITE),ident(OWNER/'tools/data_integrity.py')],'cases':[],'issues':[],'formalScore':None,'nativePass':False,'unmeasured':['Native visible/raw editing/first Click/Dropdown same-value commitment/Tab/Esc/No/Yes dialogs','Search execution/SQL/service invocation counts, including New/Cancel','Physical IME/clipboard/DPI/printing and user acceptance'],'fixturePreparation':'UiNotInList/UiSetTextValue/UiChanged/UiAction/UiForcePage/UiFocusCareer and normal Authenticate/SearchEmployees/ReadEmployee. Message Caption is reset immediately before Save/Apply to prove a fresh MSG016 response. Global cleanup resets only the owned test copy between independent scenarios; API-created Pending or direct DTO fixture initialization is not native reachability evidence.'}
 app=handle=project=module=component=probe=None;pid=None;target=WORK/'Pending-api-owned-13.accdb';pythoncom.CoInitialize()
 try:
  assert sha(ARTIFACT)==EXPECTED and sha(SEED)==SEED_SHA and sha(INPUTS)==INPUT_SHA and sha(CONTRACT)==CONTRACT_SHA
  seed=json.loads(SEED.read_text('utf8'));assert seed['artifactSha256']==EXPECTED
  assert all(sha(OWNER/p)==s for p,s in seed['source'].items())
  WORK.mkdir(parents=True,exist_ok=True);assert WORK.resolve()==WORK.absolute() and not target.exists() and not ARTIFACT.with_suffix('.laccdb').exists()
  shutil.copy2(ARTIFACT,target);assert sha(target)==EXPECTED
  record['ownerCopy']={'file':target.relative_to(REPO).as_posix(),'initialSha256':sha(target),'sourceModified':False}
  record['startupSuppression']=suppress_startup(target)
  record['authorityFiles']=[ident(REPO/'sample-project2/spec/Access/共通/方式別/02_UI部品・状態・検査契約.md'),ident(REPO/'sample-project2/spec/Access/共通/04_チェック・メッセージ設計.md'),ident(INPUTS),ident(CONTRACT)]
  record['dataBeforeOffice']=integrity.snapshot(target)
  before=set(win32process.EnumProcesses());app=win32com.client.gencache.EnsureDispatch(win32com.client.DispatchEx('Access.Application'));app.Visible=False
  raw=app.hWndAccessApp;hwnd=int(raw() if callable(raw) else raw);pid=win32process.GetWindowThreadProcessId(hwnd)[1];assert pid not in before
  handle=win32api.OpenProcess(0x100000|0x400,False,pid);record['ownedOffice']={'pid':pid,'hwnd':hwnd,'newProcess':True,'visibleRequested':False,'otherInstancesAttached':False,'nativeInputUsed':False};print(json.dumps({'step':'new-owned-api-copy','pid':pid}),flush=True)
  app.OpenCurrentDatabase(str(target),False);assert Path(app.CurrentProject.FullName).resolve()==target.resolve();assert not any(x.IsLoaded for x in app.CurrentProject.AllForms)
  project=app.VBE.ActiveVBProject;suite_body='\r\n'.join(line for line in SUITE.read_text('utf8').splitlines() if not line.startswith('Attribute '));suite_import=WORK/'PendingApiSuite-import.txt';suite_import.write_bytes(suite_body.encode('ascii'));app.LoadFromText(5,'PendingApiSuite',str(suite_import));component=project.VBComponents('PendingApiSuite');record['compileProgress']={'importedComponentName':component.Name,'actualSuiteLines':component.CodeModule.CountOfLines,'method':'LoadFromText(5), ASCII-only CRLF test text, no unsaved VBE module'};component=None
  app.DoCmd.RunCommand(125);app.DoCmd.RunCommand(126);record['compileProgress']['initialIsCompiled']=bool(app.IsCompiled)
  if not app.IsCompiled:
   record['compileProgress']['compilePing']=scalar(app.Run('PendingApiCompilePing'));app.DoCmd.RunCommand(126);record['compileProgress']['afterPureCompilePing']=bool(app.IsCompiled)
   record['compileProgress']['initialFlagFalseRecordedWithoutBusinessExecution']=True
  classes=sorted(c.Name for c in project.VBComponents if c.Type==2);record['compileProgress']['actualClasses']=classes;assert len(classes)==11,'class count mismatch'
  probe=None;module=None
  source=['Option Explicit','Public Function PendingApiClassSmoke() As Boolean']
  for n,c in enumerate(classes):source+=[' Dim c'+str(n)+' As New '+c,' If TypeName(c'+str(n)+') <> "'+c+'" Then Err.Raise 5']
  source+=[' PendingApiClassSmoke=True','End Function'];probe_path=WORK/'PendingApiClassProbe-import.txt';probe_path.write_bytes('\r\n'.join(source).encode('ascii'));app.LoadFromText(5,'PendingApiClassProbe',str(probe_path));app.DoCmd.RunCommand(126);record['compileProgress']['preSmokeIsCompiled']=bool(app.IsCompiled);assert scalar(app.Run('PendingApiClassSmoke')),'probe initialization false';record['compileProgress']['postSmokeIsCompiled']=bool(app.IsCompiled)
  module=None;app.DoCmd.DeleteObject(5,'PendingApiClassProbe');probe=None;app.DoCmd.RunCommand(126);record['compileProgress']['removedProbeFinalIsCompiled']=bool(app.IsCompiled);assert app.IsCompiled,'removed probe compile false'
  record['compile']={'runCommand':126,'isCompiled':True,'classesInitialized':classes,'temporaryClassProbeRemoved':True,'finalRecompile':True,'scope':'Test-owned copy only'}
  project=None;gc.collect();app.CloseCurrentDatabase();app.OpenCurrentDatabase(str(target),False);record['compile']['isCompiledAfterReopen']=bool(app.IsCompiled);assert app.IsCompiled,'compiled copy did not remain compiled after reopen'
  record['auth']=json.loads(str(scalar(app.Run('PendingApiInitialize'))));assert record['auth']['kind']=='OK'
  record['dataAfterAuth']=snapshot_live(app,target)
  for case in ['F03-SIMULTANEOUS','F03-NEW-CANCEL','F04-PARENT-CHILD','F06-CATEGORY']:
   before_db=snapshot_live(app,target);actual=json.loads(str(scalar(app.Run('RunPendingApiCase',case))));after_db=snapshot_live(app,target);checks=[]
   if 'harnessError' in actual:record['issues'].append({'case':case,'code':'API_CASE_EXCEPTION','detail':actual});record['cases'].append({'id':case,'actual':actual,'checks':checks,'status':'FAIL','dataBefore':before_db,'dataAfter':after_db});break
   if case=='F03-SIMULTANEOUS':
    a=actual['after'];check(checks,'pendingExact',a['pending'],{'cboDepartment':'dept-unknown \u3000','cboStatus':'status-unknown  '});check(checks,'acceptedUnchanged',a['accepted'],actual['before']['accepted'])
    for owner,text in a['pending'].items():helper_checks(checks,a,owner,text,'F03.'+owner)
    check(checks,'rawEmployee',a['raw']['txtEmployeeNo'],' 00 ');check(checks,'rawName',a['raw']['txtName'],'RawName \u3000')
   elif case=='F03-NEW-CANCEL':
    for key in ['raw','pending','accepted','acceptedCategory','searchState','resultState','listCount']:check(checks,'restored.'+key,actual['after'][key],actual['before'][key])
    check(checks,'untouchedEditorDirty',actual['editor']['dirty'],False);check(checks,'untouchedEditorDraftDirty',actual['editor']['draftDirty'],False)
    for owner,text in actual['after']['pending'].items():helper_checks(checks,actual['after'],owner,text,'returned.'+owner)
   elif case=='F04-PARENT-CHILD':
    a=actual['threePending'];check(checks,'threePendingExact',a['pending'],{'cboDepartment':'parent-dept \u3000','cboStatus':'parent-status  ','cboRole':'child-role \u3000'});check(checks,'acceptedUnchanged',a['accepted'],actual['before']['accepted'])
    helper_checks(checks,a,'cboRole','child-role \u3000','role')
    for k in ['afterSaveRejected','afterCareerOnlyClear','afterRoleApplyRejected']:check(checks,k+'.parentRaw',actual[k]['raw']['txtEmployeeName'],'ParentRaw \u3000')
    check(checks,'saveNoticeWasEmptyBeforeCall',actual['guardNoticeBeforeSave'],'');check(checks,'saveMessage016',actual['afterSaveRejected']['message'].startswith('選択値が利用できません。候補を再確認してください。'),True)
    check(checks,'savePendingPreserved',actual['afterSaveRejected']['pending'],a['pending'])
    for owner in ['cboDepartment','cboStatus']:helper_checks(checks,actual['afterSaveRejected'],owner,a['pending'][owner],'parent.'+owner)
    check(checks,'careerOnlyClearPreservesParents',actual['afterCareerOnlyClear']['pending'],{k:v for k,v in a['pending'].items() if k!='cboRole'})
    check(checks,'applyNoticeWasEmptyBeforeCall',actual['guardNoticeBeforeApply'],'');check(checks,'roleOnlyApplyMessage016',actual['afterRoleApplyRejected']['message'].startswith('選択値が利用できません。候補を再確認してください。'),True)
    check(checks,'roleOnlyPendingPreserved',actual['afterRoleApplyRejected']['pending'],{'cboRole':'role-only \u3000'});check(checks,'careerCountUnchangedByRejectedApply',actual['careerCountAfterApply'],actual['careerCountBeforeApply'])
   elif case=='F06-CATEGORY':
    a=actual['pending'];check(checks,'categoryPendingExact',a['pending'],{'cboCategory':'unknown-category \u3000'});helper_checks(checks,a,'cboCategory','unknown-category \u3000','category')
    for k in ['pending','afterSaveRejected']:
     for p in ['acceptedCategory','acceptedListKey']:check(checks,k+'.'+p,actual[k][p],actual['before'][p])
     check(checks,k+'.codeRaw',actual[k]['raw']['txtCodeName'],'CodeRaw \u3000')
    check(checks,'saveNoticeWasEmptyBeforeCall',actual['guardNoticeBeforeSave'],'');check(checks,'saveMessage016',actual['afterSaveRejected']['message'].startswith('選択値が利用できません。候補を再確認してください。'),True);check(checks,'categoryValueUnchanged',a['helpers']['cboCategory']['ownerValue'],actual['before']['helpers']['cboCategory']['ownerValue'])
   check(checks,'ownedBusinessDataUnchanged',business(after_db),business(before_db))
   record['cases'].append({'id':case,'actual':actual,'checks':checks,'dataBefore':before_db,'dataAfter':after_db,'status':'PASS_API_ONLY' if all(c['pass'] for c in checks) else 'FAIL'})
   if any(not c['pass'] for c in checks):record['issues'].append({'case':case,'code':'EXPECTATION_MISMATCH','failedChecks':[c['id'] for c in checks if not c['pass']]});break
   print(json.dumps({'case':case,'status':record['cases'][-1]['status'],'comparisons':len(checks)}),flush=True)
  record['apiCleanup']=bool(scalar(app.Run('PendingApiCleanup')));record['teardownState']=json.loads(str(scalar(app.Run('PendingApiTeardownState'))));record['dataAfterSuite']=snapshot_live(app,target);check(record.setdefault('finalComparisons',[]),'allTypedBusinessDataAndSchemaPreserved',business(record['dataAfterSuite']),business(record['dataBeforeOffice']))
 except Exception as e:record['issues'].append({'code':'HARNESS_EXCEPTION','type':type(e).__name__,'detail':str(e)[:400]})
 finally:
  module=component=probe=project=None;gc.collect()
  if app is not None:
   try:app.CloseCurrentDatabase()
   except Exception as e:record['issues'].append({'code':'CLOSE','type':type(e).__name__})
   try:app.Quit(2)
   except Exception as e:record['issues'].append({'code':'QUIT','type':type(e).__name__})
  app=None;gc.collect();pythoncom.CoFreeUnusedLibraries();pythoncom.CoUninitialize()
  if handle is not None:
   wait=win32event.WaitForSingleObject(handle,10000);exit_code=win32process.GetExitCodeProcess(handle);handle.Close();record['ownedOffice'].update(exitWait=wait,exitCode=exit_code,normalQuitRequested=True)
   if wait!=0 or exit_code!=0:record['issues'].append({'code':'OWNED_EXIT','wait':wait,'exitCode':exit_code})
  record['finishGuards']={'artifactUnchanged':sha(ARTIFACT)==EXPECTED,'seedManifestUnchanged':sha(SEED)==SEED_SHA,'inputsUnchanged':sha(INPUTS)==INPUT_SHA,'contractUnchanged':sha(CONTRACT)==CONTRACT_SHA,'measurementSourcesUnchanged':all(sha(REPO/p['file'])==p['sha256'] for p in record['measurementSources']),'productSourceManifestHashesUnchanged':all(sha(OWNER/p)==s for p,s in json.loads(SEED.read_text('utf8'))['source'].items()),'trace19480NotAttachedOrClosed':True}
  if not all(record['finishGuards'].values()):record['issues'].append({'code':'START_END_DRIFT'})
  failures=sum(not c['pass'] for case in record['cases'] for c in case['checks'])+sum(not c['pass'] for c in record.get('finalComparisons',[]));record['status']='PASS_API_ONLY' if len(record['cases'])==4 and not record['issues'] and not failures else 'FAIL_OR_INCONCLUSIVE';record['counts']={'cases':len(record['cases']),'comparisons':sum(len(c['checks']) for c in record['cases'])+len(record.get('finalComparisons',[])),'failedComparisons':failures,'issues':len(record['issues'])};record['finishedAt']=dt.datetime.now(dt.timezone.utc).isoformat();OUT.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'status':record['status'],'counts':record['counts'],'issues':record['issues'],'recordSha256':sha(OUT)},ensure_ascii=False),flush=True)
  if record['issues'] or failures:sys.exit(1)
if __name__=='__main__':main()