"""Run current-final-copy regressions with owned Access exit-code accounting.

The child-only sitecustomize records the handle of each new DispatchEx Access
instance. It never keeps an Access object, attaches to an existing instance,
changes a COM method's result, sends input, or terminates another process.
"""
from pathlib import Path
import argparse,datetime as dt,hashlib,json,os,subprocess,sys,time
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def frozen_sources():
 paths=[ROOT/'profile.json',ROOT/'README.md']+[p for folder in ('src','database','tools','tests') for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
 return {str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in sorted(paths)}
STARTUP=r'''
import atexit,datetime,gc,json,os,sys,time,uuid
from pathlib import Path
sys.dont_write_bytecode=True
task_root=Path(os.environ['SP2_OFFICE_TEST_ROOT'])
sys.path.insert(0,str(task_root/'tools'))
import build
task_original=build.win32com.client.DispatchEx
task_owned=[]
task_journal_id=uuid.uuid4().hex
def task_dispatch(progid,*args,**kwargs):
    before=set(build.win32process.EnumProcesses())
    app=task_original(progid,*args,**kwargs)
    if str(progid).lower()=='access.application':
        window=app.hWndAccessApp; window=window() if callable(window) else window
        pid=build.win32process.GetWindowThreadProcessId(window)[1]
        if pid in before: raise RuntimeError('Test Access is not a newly owned instance')
        handle=build.win32api.OpenProcess(0x100000|0x400,False,pid)
        task_owned.append((pid,handle,datetime.datetime.now(datetime.timezone.utc).isoformat()))
    return app
build.win32com.client.DispatchEx=task_dispatch
def task_finish():
    gc.collect(); rows=[]
    for pid,handle,observed in task_owned:
        try:
            exited=build.win32event.WaitForSingleObject(handle,10000)==0
            code=build.win32process.GetExitCodeProcess(handle)
            rows.append({'pid':pid,'observedAtUtc':observed,'newInstance':True,'exited':exited,'exitCode':code})
        except Exception as error:
            rows.append({'pid':pid,'errorType':type(error).__name__,'exited':False,'exitCode':None})
        finally: handle.Close()
    record={'journalId':task_journal_id,'step':os.environ['SP2_OFFICE_STEP'],'pythonPid':os.getpid(),'script':str(Path(sys.argv[0]).name),'ownedAccess':rows,'status':'PASS' if all(r['exited'] and r['exitCode']==0 for r in rows) else 'FAIL'}
    target=Path(os.environ['SP2_OFFICE_JOURNAL'])/(str(os.getpid())+'-'+task_journal_id+'.json')
    try: target.write_text(json.dumps(record,indent=2),encoding='utf-8')
    except Exception:
        print('OWNED_OFFICE_JOURNAL_WRITE_FAILURE',flush=True); os._exit(1)
    if record['status']!='PASS':
        print('OWNED_OFFICE_EXIT_FAILURE',flush=True)
        os._exit(1)
atexit.register(task_finish)
'''
def main():
 parser=argparse.ArgumentParser(); parser.add_argument('--run-id',required=True); args=parser.parse_args()
 final=ROOT/'build/CareerManagement.accdb'; artifact_hash=sha(final); inputs=ROOT/'build/generation/inputs.json'; input_hash=sha(inputs)
 source_hashes=frozen_sources(); started=dt.datetime.now(dt.timezone.utc).isoformat()
 work=ROOT/'.tmp/verified-runtime'; work.mkdir(parents=True,exist_ok=True); startup=work/'sitecustomize.py'; startup.write_text(STARTUP,encoding='utf-8')
 journal=work/'journal'; journal.mkdir(exist_ok=True)
 for p in journal.glob('*.json'): p.unlink()
 env=os.environ.copy(); env['SP2_OFFICE_TEST_ROOT']=str(ROOT); env['SP2_OFFICE_JOURNAL']=str(journal)
 env['PYTHONPATH']=str(work)+(os.pathsep+env['PYTHONPATH'] if env.get('PYTHONPATH') else '')
 commands=[('ui-state','tests/ui_state.py',[]),('busy','tests/busy.py',[]),('cycle3','tests/run.py',['--cycle','3']),
  ('faults','tests/faults.py',[]),('initialization','tests/initialization.py',[]),('concurrency','tests/concurrency.py',[]),
  ('independent-access','tests/independent/run.py',[]),('independent-auth-race','tests/independent/auth_race.py',[]),
  ('ui-properties','tests/ui_observe.py',['--run-id',args.run_id])]
 steps=[]
 for name,script,params in commands:
  env['SP2_OFFICE_STEP']=name
  print('START '+name,flush=True); tick=time.monotonic(); log=work/(name+'.log')
  with log.open('w',encoding='utf-8') as output:
   result=subprocess.run([sys.executable,'-B','-X','utf8',str(ROOT/script),*params],cwd=ROOT,env=env,stdout=output,stderr=subprocess.STDOUT)
  steps.append({'id':name,'command':'python -B -X utf8 '+script+(' '+' '.join(params) if params else ''),'exitCode':result.returncode,'durationSeconds':round(time.monotonic()-tick,3),'log':str(log.relative_to(ROOT)).replace('\\','/'),'logSha256':sha(log)})
  print(json.dumps(steps[-1]),flush=True)
  if result.returncode: print(log.read_text(encoding='utf-8')[-3500:],flush=True); break
 journals=[json.loads(p.read_text(encoding='utf-8')) for p in sorted(journal.glob('*.json'))]
 processes=[entry for record in journals for entry in record['ownedAccess']]
 expected_counts={'ui-state':2,'busy':1,'cycle3':1,'faults':3,'initialization':2,'concurrency':14,'independent-access':1,'independent-auth-race':12,'ui-properties':1}
 process_coverage=[{'step':name,'expectedInstances':count,'observedInstances':sum(len(j['ownedAccess']) for j in journals if j['step']==name)} for name,count in expected_counts.items()]
 unchanged=artifact_hash==sha(final) and input_hash==sha(inputs) and source_hashes==frozen_sources()
 okay=len(steps)==len(commands) and all(s['exitCode']==0 for s in steps) and processes and all(j['status']=='PASS' for j in journals) and all(c['expectedInstances']==c['observedInstances'] for c in process_coverage) and unchanged
 record={'schemaVersion':1,'projectId':'sample-project2','profileId':'Access','runId':args.run_id,'status':'PASS' if okay else 'FAIL',
  'startedAtUtc':started,'completedAtUtc':dt.datetime.now(dt.timezone.utc).isoformat(),
  'artifactSha256':artifact_hash,'frozenInputManifestSha256':input_hash,'productAndTestSources':source_hashes,
  'candidateInputsAndSourcesUnchanged':unchanged,'steps':steps,'ownedAccessProcesses':processes,'processJournalCoverage':process_coverage,'childJournals':journals,
  'runtimeHarness':{'source':'tests/verify_current.py','startupSha256':sha(startup),'isolation':'child PYTHONPATH only; no persistent interpreter or application changes'},
  'scope':'Actual final-artifact copies: business/boundary/Excel/state/initialization/fault/concurrency/independent regression and native property inventory. Render review, physical keyboard/Clipboard, Windows Application Error audit and acceptance remain separate evidence.','formalScore':None}
 (ROOT/'build/test-results/current-runtime.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'status':record['status'],'steps':len(steps),'ownedAccessProcesses':len(processes),'unchanged':unchanged}),flush=True)
 return int(not okay)
if __name__=='__main__': raise SystemExit(main())
