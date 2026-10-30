"""Independent owned-copy DesignView Form document-module and binding inspection."""
from pathlib import Path
import sys,site,os,re,json,hashlib,datetime as dt,shutil,gc
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf8')
OWNER=Path(__file__).resolve().parents[2];REPO=OWNER.parents[2]
HERE=OWNER/'.tmp/independent-form-wiring-final';HERE.mkdir(parents=True,exist_ok=True)
if HERE.resolve()!=HERE.absolute() or HERE.is_symlink():raise RuntimeError('Redirected owned scratch refused')
EXPECTED='0810e210184e8b0db2f5868743f61daf26e56fc8a7fe71b1cd501b4543435481'
EXPECTED_MANIFEST='6cd654e09ebf3cc20e52f7cd0e9b718819737cf07d36933acf79c8a028160db4'
ARTIFACT=OWNER/'build/CareerManagement.accdb';SEED=OWNER/'build/seed-manifest.json';COPY=HERE/'read-only-forms.accdb';OUT=OWNER/'build/test-results/independent-form-wiring.json'
DEPS=OWNER/'.tmp/python-deps';site.addsitedir(str(DEPS));os.add_dll_directory(str(DEPS/'pywin32_system32'))
import pythoncom,win32com.client,win32api,win32process,win32event
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def identity(p):return {'file':p.relative_to(REPO).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
def canonical_vba(text):
 atom=r'(?:"(?:[^"\r\n]|"")*"|ChrW\(&H[0-9A-F]+\))'
 pattern=re.compile(r'\('+atom+r'(?:\s*&\s*'+atom+r')+\)',re.I)
 def decode(m):
  parts=[]
  for token in re.findall(atom,m[0],re.I):
   parts.append(token[1:-1].replace('""','"') if token.startswith('"') else chr(int(re.search(r'&H([0-9A-F]+)',token,re.I)[1],16)))
  value=''.join(parts).encode('utf-16-le',errors='surrogatepass').decode('utf-16-le')
  return '"'+value.replace('"','""')+'"'
 text=pattern.sub(decode,text)
 text=re.sub(r'^Attribute\s+VB_.*(?:\r?\n|$)','',text,flags=re.M|re.I)
 tokens=re.findall(r'"(?:[^"\r\n]|"")*"|\x27[^\r\n]*|[A-Za-z_][A-Za-z_0-9]*|[^\s]',text)
 return [t if t.startswith('"') else t.casefold() for t in tokens if not t.startswith("'")]
def procedures(text):
 return {m[1].casefold():m[0] for m in re.finditer(r'(?im)^\s*(?:Private|Public|Friend)?\s*(?:Sub|Function)\s+(\w+)\([^\r\n]*\).*?^\s*End\s+(?:Sub|Function)\s*$',text,re.M|re.S|re.I)}
def saved_controls(text):
 stack=[];result={}
 for line in text.split('CodeBehindForm',1)[0].splitlines():
  m=re.match(r'^\s*Begin(?:\s+(\w+))?\s*$',line)
  if m:stack.append({'kind':m[1] or 'group','properties':{}});continue
  if re.search(r'=\s*Begin\s*$',line):stack.append({'kind':'blob','properties':{}});continue
  if re.match(r'^\s*End\s*$',line):
   if stack:
    node=stack.pop();name=node['properties'].get('Name')
    if name and node['kind'] in ('TextBox','ComboBox'):result[name]=node
   continue
  m=re.match(r'^\s*(\w+)\s*=\s*"((?:[^"]|"")*)"\s*$',line)
  if stack and m:stack[-1]['properties'][m[1]]=m[2].replace('""','"')
 return result
def suppress_startup(path):
 engine=db=None
 try:
  engine=win32com.client.DispatchEx('DAO.DBEngine.120');db=engine.OpenDatabase(str(path),True)
  macros=[d.Name for d in db.Containers('Scripts').Documents]
  if any(n.casefold()=='autoexec' for n in macros):raise RuntimeError('AutoExec present; refuse to run startup')
  prior=None
  if 'StartupForm' in {p.Name for p in db.Properties}:
   prior=db.Properties('StartupForm').Value;db.Properties.Delete('StartupForm')
  db.Close();db=None
  return {'autoExecAbsent':True,'removedStartupFormOnFreshCopyOnly':prior,'copyOnlyMetadataChange':'StartupForm property removed before Access open; product and its normal startup unchanged','formRuntimeExecuted':False}
 finally:
  if db is not None:db.Close()
  db=engine=None;gc.collect();pythoncom.CoFreeUnusedLibraries()
def main():
 record={'schemaVersion':1,'projectId':'sample-project2','profileId':'Access','runId':'sp2-ui-regenerate-20261029','recordedAt':dt.datetime.now(dt.timezone.utc).isoformat(),'scope':'Independent token equality of actual five Form document modules and actual event properties/handlers on fresh owned DesignView copy only. No native behavior, runtime values, authentication, keyboard, candidate-selection or UI acceptance claim.','status':'RUNNING','artifactSha256':EXPECTED,'measurementSources':[identity(Path(__file__).resolve())],'issues':[],'forms':[],'helperWiring':[],'comboWiring':[],'formalScore':None,'nativePass':False}
 sources={};app=handle=project=form=module=ctl=None;pid=None;pythoncom.CoInitialize()
 try:
  assert sha(ARTIFACT)==EXPECTED and sha(SEED)==EXPECTED_MANIFEST
  assert ARTIFACT.resolve()==ARTIFACT.absolute() and not ARTIFACT.is_symlink() and not ARTIFACT.with_suffix('.laccdb').exists()
  assert not COPY.exists() and not COPY.with_suffix('.laccdb').exists()
  seed=json.loads(SEED.read_text('utf8'));assert seed['artifactSha256']==EXPECTED
  for p in sorted((OWNER/'src/forms').glob('*.txt')):
   if p.stem not in ['frmLogin','frmMenu','frmEmployeeSearch','frmEmployeeEditor','frmCodeMaster']:continue
   key=p.relative_to(OWNER).as_posix();assert sha(p)==seed['source'][key]
   raw=p.read_bytes();text=raw.decode('utf-16' if raw[:2] in (b'\xff\xfe',b'\xfe\xff') else 'utf-8-sig');parts=text.split('CodeBehindForm',1);assert len(parts)==2
   sources[p.stem]={'path':p,'identity':identity(p),'whole':text,'body':parts[1],'controls':saved_controls(text)}
  assert len(sources)==5
  record['sourceFiles']=[x['identity'] for x in sources.values()];record['seedManifest']={'file':SEED.relative_to(REPO).as_posix(),'sha256':sha(SEED)}
  shutil.copy2(ARTIFACT,COPY);assert sha(COPY)==EXPECTED
  record['copy']={'file':COPY.relative_to(REPO).as_posix(),'initialExactSha256':sha(COPY),'existingInstancesAttached':False}
  record['startupSuppression']=suppress_startup(COPY);record['copy']['startupSuppressedSha256']=sha(COPY)
  before=set(win32process.EnumProcesses());app=win32com.client.DispatchEx('Access.Application');app.Visible=False
  hwnd=app.hWndAccessApp;hwnd=int(hwnd() if callable(hwnd) else hwnd);pid=win32process.GetWindowThreadProcessId(hwnd)[1];assert pid not in before
  handle=win32api.OpenProcess(0x100000|0x400,False,pid);record['ownedOffice']={'pid':pid,'hwnd':hwnd,'newPid':True,'visibleRequested':False,'nativeInputUsed':False,'startupNormalViewUsed':False}
  print(json.dumps({'step':'owned-design-read','pid':pid}),flush=True)
  app.OpenCurrentDatabase(str(COPY),True);assert Path(app.CurrentProject.FullName).resolve()==COPY.resolve()
  assert not any(f.IsLoaded for f in app.CurrentProject.AllForms)
  project=app.VBE.ActiveVBProject
  actual_names=sorted(f.Name for f in app.CurrentProject.AllForms);assert actual_names==sorted(sources)
  for name in actual_names:
   source=sources[name];app.DoCmd.OpenForm(name,1,'','',0,1);form=app.Forms(name)
   assert form.HasModule
   module=form.Module;actual=module.Lines(1,module.CountOfLines) if module.CountOfLines else ''
   (HERE/(name+'-actual.bas')).write_text(actual,'utf8')
   at=canonical_vba(actual);st=canonical_vba(source['body']);equal=at==st;ap=procedures(actual);sp=procedures(source['body'])
   record['forms'].append({'form':name,'sourceFile':source['identity'],'actualDocumentModuleName':module.Name,'actualDocumentModuleTextSha256':hashlib.sha256(actual.encode()).hexdigest(),'sourceCodeBehindSha256':hashlib.sha256(source['body'].encode()).hexdigest(),'actualTokenCount':len(at),'sourceTokenCount':len(st),'actualTokensSha256':digest(at),'sourceTokensSha256':digest(st),'canonicalTokensEqual':equal,'procedureNamesEqual':set(ap)==set(sp),'actualProcedureCount':len(ap),'sourceProcedureCount':len(sp),'firstMismatchTokenIndex':next((i for i,(a,b) in enumerate(zip(at,st)) if a!=b),min(len(at),len(st)) if not equal else None),'runtimeValuesRead':False})
   if not equal:record['issues'].append({'code':'FORM_DOCUMENT_MODULE_TOKEN_DIFFERENCE','form':name})
   helpers=[c.Name for c in form.Controls if c.ControlType==109 and c.Name.startswith('txtPending_')]
   for helper in sorted(helpers):
    ctl=form.Controls(helper);node=source['controls'][helper]
    for prop,event in [('OnChange','Change'),('OnGotFocus','GotFocus'),('BeforeUpdate','BeforeUpdate')]:
     binding=str(getattr(ctl,prop) or '');expected_binding=node['properties'].get(prop,'');proc=helper+'_'+event;present=proc.casefold() in ap;body_equal=present and proc.casefold() in sp and canonical_vba(ap[proc.casefold()])==canonical_vba(sp[proc.casefold()])
     item={'form':name,'control':helper,'event':event,'property':prop,'actualBinding':binding,'canonicalBinding':expected_binding,'bindingEqual':binding==expected_binding,'actualHandlerPresent':present,'actualHandlerName':proc,'actualHandlerMatchesCanonical':body_equal,'actualHandlerTokenSha256':digest(canonical_vba(ap[proc.casefold()])) if present else None}
     record['helperWiring'].append(item)
     if not(binding=='[Event Procedure]' and binding==expected_binding and body_equal):record['issues'].append({'code':'PENDING_HELPER_WIRING','form':name,'control':helper,'event':event})
    ctl=None
   for helper in sorted(helpers):
    owner=helper.removeprefix('txtPending_');ctl=form.Controls(owner);node=source['controls'][owner]
    for prop,event in [('OnClick','Click'),('OnMouseDown','MouseDown'),('OnMouseUp','MouseUp'),('OnKeyUp','KeyUp'),('AfterUpdate','AfterUpdate'),('OnKeyDown','KeyDown')]:
     binding=str(getattr(ctl,prop) or '');expected_binding=node['properties'].get(prop,'');proc=owner+'_'+event;present=proc.casefold() in ap;body_equal=present and proc.casefold() in sp and canonical_vba(ap[proc.casefold()])==canonical_vba(sp[proc.casefold()]);consistent=binding==expected_binding and (binding!='[Event Procedure]' or body_equal)
     record['comboWiring'].append({'form':name,'control':owner,'event':event,'property':prop,'actualBinding':binding,'canonicalBinding':expected_binding,'bindingEqual':binding==expected_binding,'actualHandlerPresent':present,'actualHandlerName':proc if present else None,'actualHandlerMatchesCanonical':body_equal if present else None,'wiringConsistent':consistent,'optionalAbsenceIsFailure':False,'bindingAloneProvesNativeCandidateCommit':False})
     if not consistent:record['issues'].append({'code':'COMBO_EVENT_WIRING','form':name,'control':owner,'event':event})
    ctl=None
   form=module=ctl=None;app.DoCmd.Close(2,name,2)
  assert len(record['helperWiring'])==18 and len(record['comboWiring'])==36
  record['normalization']={'sourceSection':'Only CodeBehindForm; SaveAsText hidden Attribute VB_* lines excluded','tokens':'Ignore comments/nonliteral whitespace/case; preserve string literal contents/case and punctuation; reverse only documented local VBE ChrW literal encoding transform','actualRead':'Form.Module.Lines from actual owned DesignView class, not imported canonical code','referenceTokenizerFile':identity(OWNER/'tests/independent/design_attributes.py'),'tokenizerAdaptation':'Same canonical_vba token logic with explicit exclusion of SaveAsText Attribute VB_* metadata; collector was not modified.'}
 except Exception as e:
  record['issues'].append({'code':'INSPECTION_EXCEPTION','type':type(e).__name__,'message':str(e)[:450]})
 finally:
  ctl=module=form=project=None;gc.collect()
  if app is not None:
   try:app.CloseCurrentDatabase()
   except Exception as e:record['issues'].append({'code':'OWNED_CLOSE','type':type(e).__name__})
   try:app.Quit(2)
   except Exception as e:record['issues'].append({'code':'OWNED_QUIT','type':type(e).__name__})
  app=None;gc.collect();pythoncom.CoFreeUnusedLibraries();pythoncom.CoUninitialize()
  if handle is not None:
   wait=win32event.WaitForSingleObject(handle,10000);exit_code=win32process.GetExitCodeProcess(handle);handle.Close();record['ownedOffice'].update(exitWait=wait,exitCode=exit_code,normalQuitRequested=True)
   if wait!=0 or exit_code!=0:record['issues'].append({'code':'OWNED_PROCESS_NOT_EXITED_NORMALLY','wait':wait,'exitCode':exit_code})
  record['finalChecks']={'productArtifactSha256':sha(ARTIFACT),'productArtifactUnchanged':sha(ARTIFACT)==EXPECTED,'seedManifestSha256':sha(SEED),'seedManifestUnchanged':sha(SEED)==EXPECTED_MANIFEST,'measurementCodeUnchanged':sha(Path(__file__))==record['measurementSources'][0]['sha256'],'sourceFilesUnchanged':all(sha(x['path'])==x['identity']['sha256'] for x in sources.values()),'oldProbeInstance19480NotAttachedOrClosed':True}
  if not all(record['finalChecks'][k] for k in ['productArtifactUnchanged','seedManifestUnchanged','measurementCodeUnchanged','sourceFilesUnchanged']):record['issues'].append({'code':'START_END_INPUT_DRIFT'})
  record['status']='PASS_STATIC_FORM_WIRING_ONLY' if not record['issues'] else 'FAIL_OR_INCONCLUSIVE'
  record['counts']={'forms':len(record['forms']),'helperControls':len({(x['form'],x['control']) for x in record['helperWiring']}),'requiredHelperEventBindings':len(record['helperWiring']),'comboEventBindingsInspected':len(record['comboWiring']),'issues':len(record['issues'])}
  OUT.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'status':record['status'],'counts':record['counts'],'office':record.get('ownedOffice'),'recordSha256':sha(OUT)},ensure_ascii=False),flush=True)
  if record['issues']:sys.exit(1)
if __name__=='__main__':main()