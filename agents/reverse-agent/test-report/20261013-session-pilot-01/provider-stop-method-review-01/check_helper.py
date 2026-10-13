"""Read-only audit; exact helper AST + inert files + fully replaced subprocess transport."""
import argparse
import ast
from datetime import datetime,timezone,timedelta
import hashlib
import json
from pathlib import Path
import shutil
from types import SimpleNamespace
import subprocess as exception_types_only
import uuid

ROOT=Path.cwd().resolve(); REPORT=Path(__file__).resolve().parent
HELPER=ROOT/'agents/reverse-agent/.tmp/20261013-session-pilot-01/capture_owned_cycle.py'
DRY=ROOT/'agents/reverse-agent/test-report/20261013-session-pilot-01/owned-capture-dryrun-01'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p): return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
inputs=[HELPER]+[DRY/(n+'.json') for n in ('scope','result','process-actions','inventory-before','inventory-after')]
before=[pin(p) for p in inputs]
source=HELPER.read_bytes(); snapshot=REPORT/'helper-audited-source.py'
if snapshot.exists(): assert snapshot.read_bytes()==source
else: snapshot.write_bytes(source)
tree=ast.parse(source.decode('utf-8'))
selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PROCESS_SCRIPT' for t in n.targets)]
code=compile(ast.fix_missing_locations(ast.Module(body=selected,type_ignores=[])),str(snapshot),'exec')
runroot=REPORT/'synthetic'/('run-'+uuid.uuid4().hex[:8]); runroot.mkdir(parents=True)
cases=[]

def check(label,mode='success',stop=False,alter=None):
    base=runroot/label; agent=base/'agents/reverse-agent'; session=agent/'.tmp/session'; report=agent/'test-report/session'; job=session/'job'
    job.mkdir(parents=True); report.mkdir(parents=True)
    helper=session/'capture_owned_cycle.py'; helper.write_bytes(b'Inert helper identity fixture; never executed.\n')
    (job/'partial.txt').write_bytes(b'Inert partial provider evidence.\n')
    deadline=datetime.now(timezone.utc)+timedelta(hours=1)
    config={'jobs':'agents/reverse-agent/.tmp/session/job','deadline':deadline.isoformat(),'revision':'5.0'}
    handoff={'deadline':deadline.isoformat(),'activeJobRoot':config['jobs'],'activeConfig':'agents/reverse-agent/.tmp/session/config.json','round5':{'ownedProcessRecord':'owned.json'}}
    owned={'configPath':handoff['activeConfig'],'processes':[{'processId':123456789,'creationDate':'2026-01-01T00:00:00Z','commandLine':'inert fixture, never started','role':'generation'}]}
    if alter=='job': config['jobs']='agents/reverse-agent/.tmp/session/different'
    if alter=='owner': owned['configPath']='agents/reverse-agent/.tmp/session/different.json'
    target=report/'capture'
    if alter=='existing': target.mkdir(); (target/'sentinel.txt').write_text('preserve',encoding='utf-8')
    handoff_path=report/'focus-continuation-handoff-01.json'
    for p,data in [(session/'config.json',config),(report/'owned.json',owned),(handoff_path,handoff)]: p.write_text(json.dumps(data),encoding='utf-8')
    if alter=='stale': (report/'focus-continuation-handoff-02.json').write_text(json.dumps(handoff),encoding='utf-8')
    args=SimpleNamespace(handoff=handoff_path.relative_to(base).as_posix(),report=target.relative_to(base).as_posix(),stop_at_deadline=stop)
    calls=[]
    def fake_run(*a,**kw):
        calls.append(json.loads(kw['stdin'].read().decode('utf-8')))
        assert calls[-1]['stop'] is False, 'No synthetic stop transport is allowed'
        if mode=='timeout': raise exception_types_only.TimeoutExpired('inert-transport',60,output='partial')
        if mode=='error': raise exception_types_only.CalledProcessError(1,'inert-transport',stderr='inert failure')
        if mode=='interrupt': raise KeyboardInterrupt('inert interruption')
        if mode=='malformed': return SimpleNamespace(stdout='invalid-json',stderr='inert stderr')
        return SimpleNamespace(stdout=json.dumps({'stopRequested':False,'roots':[],'processes':[]}),stderr='')
    parser=SimpleNamespace(add_argument=lambda *a,**k:None,parse_args=lambda:args)
    ns={'argparse':SimpleNamespace(ArgumentParser=lambda:parser),'hashlib':hashlib,'json':json,'datetime':datetime,'timezone':timezone,'Path':Path,'shutil':shutil,'subprocess':SimpleNamespace(run=fake_run),'__file__':str(helper)}
    exec(code,ns)
    error=None
    try: ns['main']()
    except BaseException as exc: error=type(exc).__name__+': '+str(exc)
    files=sorted(p.name for p in target.glob('*.json')) if target.exists() else []
    result={'case':label,'error':error,'transportCalls':len(calls),'actualExternalProcessStarted':False,'reportFiles':files}
    if mode=='success' and alter is None and not stop:
        assert error is None and len(calls)==1
        record=json.loads((target/'result.json').read_text(encoding='utf-8'))
        assert record['completedScore'] is None and record['completeInferenceClaimed'] is False
        copies=json.loads((target/'inventory-before.json').read_text(encoding='utf-8'))
        assert len(copies)==1 and copies[0]['stableDuringCopy'] is True
        result['completedScore']=None
    elif mode!='success':
        assert error is not None and len(calls)==1
        assert files==['inventory-after.json','inventory-before.json','process-actions.json','process-request.json','result.json','scope.json']
        actions=json.loads((target/'process-actions.json').read_text(encoding='utf-8'))
        record=json.loads((target/'result.json').read_text(encoding='utf-8'))
        assert actions['state']=='UNKNOWN' and actions['error']
        assert record['processOperationState']=='UNKNOWN' and record['completedScore'] is None and record['completeInferenceClaimed'] is False
        assert (target/'process-stdout.txt').is_file() and (target/'process-stderr.txt').is_file()
        result['fixVerified']='Raw process output/failure, UNKNOWN actions, post-attempt capture, durable null-completion result retained before original exception rethrows'
    else:
        assert error is not None and not calls
        if alter=='existing': assert (target/'sentinel.txt').read_text(encoding='utf-8')=='preserve'
        else: assert not target.exists()
    result['status']='PASS'; cases.append(result)

check('capture-without-stop')
check('early-stop-refused',stop=True)
check('stale-handoff-refused',alter='stale')
check('config-job-mismatch-refused',alter='job')
check('ownership-config-mismatch-refused',alter='owner')
check('exclusive-report-refused',alter='existing')
for mode in ('timeout','error','malformed','interrupt'): check('transport-'+mode,mode=mode)

boundary=runroot/'boundary'; boundary.mkdir()
ns={'Path':Path,'hashlib':hashlib,'shutil':shutil};exec(code,ns)
assert ns['within'](boundary/'inside',boundary)==(boundary/'inside').resolve()
cases.append({'case':'resolved-path-within-root','status':'PASS'})
try: ns['within'](boundary/'../outside',boundary)
except ValueError: cases.append({'case':'resolved-path-escape-refused','status':'PASS'})
else: raise AssertionError('Path escape accepted')
mutable=runroot/'mutable-copy';mutable.mkdir(); raw=mutable/'evidence.txt';raw.write_bytes(b'before')
original_digest=ns['digest']; changed=[False]
def mutate_digest(p):
    result=original_digest(p)
    if p==raw and not changed[0]: changed[0]=True;raw.write_bytes(b'after')
    return result
ns['digest']=mutate_digest
copies=ns['capture'](mutable,runroot/'mutable-output')
assert len(copies)==1 and copies[0]['stableDuringCopy'] is False and 'captureError' not in copies[0]
cases.append({'case':'source-change-during-copy-marked-unstable','status':'PASS','completedScore':None,'stableDuringCopy':False})

# Exact transport section from the initial read (original SHA2ac8d9...); no real transport.
old_excerpt='''completed = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command',
                            '[Console]::OutputEncoding=[Text.UTF8Encoding]::new();' + PROCESS_SCRIPT],
                           input=json.dumps(request), capture_output=True, text=True,
                           encoding='utf-8', timeout=60, check=True)
exclusive_json(target / 'process-actions.json', json.loads(completed.stdout))
after = capture(job, target / 'after')
exclusive_json(target / 'inventory-after.json', after)
exclusive_json(target / 'result.json', {
    'finishedAt': datetime.now(timezone.utc).isoformat(),
    'stopRequested': args.stop_at_deadline, 'beforeFiles': len(before), 'afterFiles': len(after),
    'completeInferenceClaimed': False, 'completedScore': None,
    'captureErrors': sum('captureError' in item for item in before + after),
    'limitations': ['Live files may change during pre-stop copy; stableDuringCopy is explicit',
                     'Missing provider result/answer remains incomplete',
                     'Review/grading agents are controlled separately by the parent agent']})'''
(REPORT/'original-transport-excerpt.py').write_text(old_excerpt+'\n',encoding='utf-8')
old_cases=[]
for mode in ('timeout','error','malformed','interrupt'):
    saved=[]
    def old_run(*a,**k):
        if mode=='timeout': raise exception_types_only.TimeoutExpired('inert',60,output='partial')
        if mode=='error': raise exception_types_only.CalledProcessError(1,'inert',stderr='failure')
        if mode=='interrupt': raise KeyboardInterrupt('inert interruption')
        return SimpleNamespace(stdout='invalid-json')
    ns={'subprocess':SimpleNamespace(run=old_run),'json':json,'PROCESS_SCRIPT':'inert never executed','request':{'stop':False},'exclusive_json':lambda *a:saved.append(a),'target':Path('inert'),'capture':lambda *a:saved.append(a),'job':Path('inert'),'datetime':datetime,'timezone':timezone,'args':SimpleNamespace(stop_at_deadline=False),'before':[]}
    error=None
    try: exec(compile(old_excerpt,'original-helper-read-lines155-169','exec'),ns)
    except BaseException as exc: error=type(exc).__name__
    assert error and not saved
    old_cases.append({'mode':mode,'error':error,'postAttemptRecordsSaved':0,'actualProcessStarted':False,'confirmedOriginalGap':True})

dry_result=json.loads((DRY/'result.json').read_text(encoding='utf-8'))
dry_actions=json.loads((DRY/'process-actions.json').read_text(encoding='utf-8'))
assert dry_result['stopRequested'] is False and dry_result['completedScore'] is None
assert dry_result['captureErrors']==0 and dry_result['beforeFiles']==dry_result['afterFiles']==33
assert len(dry_actions['roots'])==2 and all(p['state']=='EXACT_OWNER_MATCH' for p in dry_actions['roots'])
assert len(dry_actions['processes'])==20 and all(p['action']=='OBSERVED_NO_STOP' for p in dry_actions['processes'])
for stage in ('before','after'):
    rows=json.loads((DRY/('inventory-'+stage+'.json')).read_text(encoding='utf-8')); assert len(rows)==33
    for row in rows:
        assert row['stableDuringCopy'] is True
        assert row['sourceSha256Before']==row['copiedSha256']==row['sourceSha256After']==sha(DRY/stage/row['path'])
after=[pin(p) for p in inputs]; assert before==after
record={'schema':'independent-owned-evidence-helper-audit/1','capturedAt':datetime.now(timezone.utc).isoformat(),'auditedHelperSha256':sha(snapshot),'originalReadHelperSha256':'2ac8d918d600d921faa4315c72ff2a32944200aedc4bc38c609e88e296426d9c','originalFullBytesHistoryPreserved':False,'originalExcerptReconstructedFromInitialToolRead':True,'currentHelperFullSnapshotBytesMatch':snapshot.read_bytes()==HELPER.read_bytes(),'helperIsSeparateFromRound5GenerationRuntime':True,'originalReadTransportLines':[155,169],'originalReadExcerptCases':old_cases,'cases':cases,'caseCount':len(cases),'allCasesPass':True,'inputsUnchanged':True,'dryRunMetadataIndependentlyVerified':{'owners':2,'observedNoStopProcesses':20,'beforeFiles':33,'afterFiles':33,'copyShaTriplesVerified':66,'completedScore':None},'pins':before,'sourceSnapshot':pin(snapshot),'syntheticFixtures':runroot.relative_to(ROOT).as_posix(),'liveProcessOrStopCallsMadeByAudit':False,'originalSourceOrMdEdited':False,'evaluatorExpectedContentsRead':False}
(REPORT/'result.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'cases':len(cases),'allPass':True,'confirmedFailureModes':4,'dryRunCopiesVerified':66,'inputsUnchanged':True}))
