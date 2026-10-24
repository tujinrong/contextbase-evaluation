"""Executes the production C gate/key/block code; RPG integration checks are static."""
from pathlib import Path
import argparse,subprocess,json,re,hashlib,tempfile,shutil,sys
B=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--report-dir',type=Path,required=True);p.add_argument('--run-id',required=True);a=p.parse_args()
if not re.fullmatch(r'[A-Za-z0-9_-]+',a.run_id):raise SystemExit('safe unique run ID required')
R=a.report_dir.resolve();R.mkdir(parents=True,exist_ok=True);dest=R/(a.run_id+'-state.json')
if dest.exists():raise SystemExit('Previous attempt is preserved')
zig=next((B/'build/toolchain/zig').rglob('zig.exe'));exe=B/'build'/('STUSTATE_TEST-'+a.run_id+'.exe')
commands=[[str(zig),'cc','-std=c11','-Wall','-Wextra','-Werror','-target','x86_64-windows-gnu',str(B/'c/STUSTATE.c'),str(B/'c/STUSTATE_TEST.c'),'-o',str(exe)],[str(exe)]]
runs=[]
for i,command in enumerate(commands):
 r=subprocess.run(command,cwd=B,capture_output=True,text=True,encoding='utf8',errors='replace');runs.append(dict(command=command,exitCode=r.returncode,stdout=r.stdout,stderr=r.stderr))
 (R/(a.run_id+'-state-'+str(i)+'.log')).write_text('COMMAND '+subprocess.list2cmdline(command)+'\nEXIT '+str(r.returncode)+'\n'+r.stdout+'\n'+r.stderr,'utf8')
 if r.returncode:break
svc=(B/'src/STUSVC.sqlrpgle').read_text('utf8');search=(B/'src/STUSRCH.sqlrpgle').read_text('utf8');types=(B/'copy/STUTYPES.rpgleinc').read_text('utf8');ui=(B/'copy/STUDSP.rpgleinc').read_text('utf8')
compact=re.sub(r'\s+','',svc);compact_search=re.sub(r'\s+','',search)
checks=[]
def check(name,ok):checks.append(dict(id=name,passed=bool(ok)))
check('gate-in-production-with-authoritative-registry','StSearchStateCheck(' in svc.replace(' ','') and 'searchStates( slot ).revision' in svc and 'context.expectedRevision' in svc)
check('job-window-owner-cache-boundary',all(x in svc for x in ['QSYS2.JOB_NAME','context.session=job','searchStates( slot ).owner=principal','context.instanceId<>']))
check('no-live-registry-eviction','utc>=searchStates( i ).lastUsed+%minutes( 30 )' in svc and "page.result.kind=RK_SYSTEM" in svc)
check('revision-commit-authoritative','context.revision=searchStates(slot).revision+1;' in compact and 'searchStates(slot)=context;' in compact)
check('clear-full-state','clearfresh;clearraw;clearpage;' in compact and 'fresh.pageSize=20;' in compact and "fresh.sortKey='studentNo';" in compact)
check('window-close-releases-registry','StCloseSearchContext( context :startup )' in search and 'clearsearchStates(slot);clearcontext;' in compact)
check('new-context-and-clear-use-service','StCreateSearchContext( raw :context :page )' in search and 'StClearSearchContext( raw :context :page )' in search)
check('unknown-current-keys-before-db','StSearchKeysValid(' in svc.replace(' ','') and "'E-SRC-001'" in svc)
check('block-c-helper-in-production','StSearchBlock( block :page.rowCount )' in search)
check('confirmation-full-does-not-evict-live', 'slot=1;' not in compact[compact.index('dcl-procStSaveStudentexport;'):compact.index('dcl-procStCancelConfirmationexport;')])
check('confirmation-cancel-scoped-to-editor', all(x in compact for x in ['confirmations(i).owner=principal','confirmations(i).job=job','confirmations(i).instanceId=instance;clearconfirmations(i);']))
check('confirmation-cancel-on-user-cancel', 'StCancelConfirmation' in (B/'src/STUEDIT.sqlrpgle').read_text('utf8'))
check('retired-id-reinitializes-after-identity-check', "context.owner<>principalorcontext.session<>job" in compact and compact.count("ifverdict=5;StCreateSearchContext(raw:context:page);")==2)
check('retired-close-does-not-allocate', 'elseifverdict=5;clearcontext;clearresult;' in compact)
can=types[types.index(' dcl-ds DuplicateCandidate_t'):types.index(' dcl-ds Result_t')]
check('candidate-dto-contains-only-four-categories',all(x not in can for x in ['studentNameKana','address','phone','rowVersion','studentId','StudentRecord_t']) and all(x in can for x in ['studentNo','studentName','birthDate','className']))
show=ui[ui.index(' dcl-proc Question'):ui.index(' dcl-proc Choice')]
check('candidate-display-four-fields-only','studentNameKana' not in show and '.className' in show and '.birthDate' in show)
check('reset-display-is-unsearched-without-synthetic-date', "ifnotcontext.hasApplied;RESULT_CNT='未検索';SEARCH_AT='';" in compact_search)
check('candidate-result-uses-restricted-type','candidates likeds( DuplicateCandidate_t )' in types)
# Execute the real fixed-contract emitter in a disposable method-local root.
with tempfile.TemporaryDirectory(prefix='rpg-emitter-',dir=B/'build') as temp:
 temp=Path(temp);(temp/'tools').mkdir();shutil.copyfile(B/'tools/generate_sources.py',temp/'tools/generate_sources.py')
 generated=subprocess.run([sys.executable,'-X','utf8',str(temp/'tools/generate_sources.py')],capture_output=True,text=True,encoding='utf8')
 (R/(a.run_id+'-emitter.log')).write_text('EXIT '+str(generated.returncode)+'\n'+generated.stdout+'\n'+generated.stderr,'utf8')
 check('actual-fixed-contract-emitter-runs',generated.returncode==0)
 emitted=(temp/'copy/STUTYPES.rpgleinc').read_text('utf8') if generated.returncode==0 else ''
 for name in ['SearchRaw_t','SearchCriteria_t','SearchContext_t','DuplicateCandidate_t','Result_t']:
  def structure(text):
   m=re.search(r'dcl-ds\s+'+name+r'\b(.*?)end-ds\s*;',text,re.S|re.I)
   return re.sub(r'\s+','',m[0]) if m else ''
  check('emitter-matches-production-'+name,bool(structure(types)) and structure(types)==structure(emitted))
 ep=(temp/'copy/STUPROTO.rpgleinc').read_text('utf8') if generated.returncode==0 else ''
 check('emitter-exports-state-entry-and-C-gates',all(x in ep for x in ['StCreateSearchContext','StClearSearchContext','StCloseSearchContext','StSearchStateCheck','StSearchKeysValid','StSearchBlock']))
cases=re.findall(r'^(PASS|FAIL) (.+)$',runs[-1]['stdout'],re.M)
record=dict(runId=a.run_id,runs=runs,cCases=[dict(id=n,passed=s=='PASS') for s,n in cases],cTests=len(cases),staticChecks=checks,passed=len(runs)==2 and all(r['exitCode']==0 for r in runs) and bool(cases) and all(s=='PASS' for s,n in cases) and all(c['passed'] for c in checks),scope='Production C gate/key/block executed on Windows; native RPG registry, DDS, SQL and IBM i behavior NOT_RUN',formalScore=None,sourceHashes={n:hashlib.sha256((B/n).read_bytes()).hexdigest() for n in ['c/STUSTATE.c','c/STUSTATE.h','src/STUSVC.sqlrpgle','src/STUSRCH.sqlrpgle','copy/STUTYPES.rpgleinc','copy/STUDSP.rpgleinc']})
dest.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(dict(passed=record['passed'],cTests=len(cases),static=len(checks),failed=[x['id'] for x in checks if not x['passed']]),ensure_ascii=False));raise SystemExit(0 if record['passed'] else 1)
