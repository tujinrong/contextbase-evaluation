"""Fresh, manifest-bound native results and negative-control executions."""
from __future__ import annotations
import json,os,shutil,subprocess,tempfile,time,uuid
from collections import Counter
from pathlib import Path
from overviewgen.core import digest,save


def inputs(base:Path):
    paths=[p for folder in ['spec-input','reference','reimplementation','harness'] for p in (base/folder).rglob('*') if p.is_file() and p.suffix in {'.vb','.md','.json'}]
    paths += [base/'Pilot.vbproj',base/'NuGet.Config']
    return {p.relative_to(base).as_posix():digest(p.read_bytes()) for p in sorted(paths)}


def validate(root:Path):
    base=root/'pilot/TKL-011';report=root/'report/pilot'
    try:
        expected=json.loads((report/'execution-binding.json').read_text());result=json.loads((report/'native-result.json').read_text())
    except (OSError,ValueError) as exc:raise ValueError('Fresh native result and execution binding required') from exc
    if expected.get('status')!='executed':raise ValueError('Native execution not completed')
    if expected.get('inputs')!=inputs(base):raise ValueError('Native result is stale: input/specification/harness hashes differ')
    if not expected.get('run_id') or result.get('run_id')!=expected['run_id']:raise ValueError('Native run identity mismatch')
    if expected.get('result_sha256')!=digest((report/'native-result.json').read_bytes()):raise ValueError('Native result changed after execution')
    rows=result.get('results')
    if not isinstance(rows,list) or not rows:raise ValueError('Native test results are empty')
    if len({r.get('case') for r in rows})!=len(rows):raise ValueError('Duplicate native test case IDs')
    if any(type(r.get('passed')) is not bool for r in rows):raise ValueError('Native pass values must be booleans')
    failed=sum(not r['passed'] for r in rows)
    if result.get('cases')!=len(rows) or result.get('failed')!=failed or result.get('passed')!=len(rows)-failed:raise ValueError('Native case/pass/failure counts are inconsistent')
    if result.get('status')!=('failed' if failed else 'subset_pass'):raise ValueError('Native status conflicts with test results')
    plan=json.loads((base/'harness/test-plan.json').read_text())
    if Counter(r.get('family') for r in rows)!=plan['family_counts']:raise ValueError('Native case families differ from frozen test plan')
    return result


def run_native(root:Path):
    base=root/'pilot/TKL-011';report=root/'report/pilot';report.mkdir(parents=True,exist_ok=True)
    path=report/'native-result.json';path.unlink(missing_ok=True)
    run_id=str(uuid.uuid4());binding={'run_id':run_id,'inputs':inputs(base),'status':'running'}
    save(report/'execution-binding.json',binding);start=time.perf_counter()
    command=['dotnet','run','--project',str(base/'Pilot.vbproj'),'--configuration','Release','--',str(path)]
    env=dict(os.environ,PILOT_RUN_ID=run_id,DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_NOLOGO='1')
    try:process=subprocess.run(command,cwd=root,capture_output=True,text=True,timeout=180,env=env)
    except (OSError,subprocess.TimeoutExpired) as exc:
        save(report/'execution-metadata.json',{'status':'not_completed','error':type(exc).__name__,'run_id':run_id});raise
    save(report/'native-build-run.log',process.stdout+process.stderr)
    save(report/'execution-metadata.json',{'run_id':run_id,'exit_code':process.returncode,'elapsed_seconds':time.perf_counter()-start,'status':'executed' if path.exists() else 'failed_before_results','command':['dotnet','run','--project','pilot/TKL-011/Pilot.vbproj','--configuration','Release','--','report/pilot/native-result.json']})
    if not path.exists():raise ValueError('Native build/execution produced no test result; inspect native-build-run.log')
    binding.update(status='executed',result_sha256=digest(path.read_bytes()));save(report/'execution-binding.json',binding)
    result=validate(root)
    if process.returncode and not result['failed']:raise ValueError('Process failed despite a passing result')
    return result


def mutation_checks(root:Path):
    base=root/'pilot/TKL-011';original=(base/'reimplementation/Events.vb').read_text();reports=[]
    mutants=[('MUT-GUARD','AndAlso Not Active Then Return','AndAlso False Then Return'),('MUT-RECALC','Case "calculate"\n','Case "calculate"\n                Reprice()\n'),('MUT-POSTAL','If address<>"" Then M.SagawaAddress=address','M.SagawaAddress=address'),('MUT-NULL','Dim sale As Short?=Nothing','Dim sale As Short?=0')]
    for mid,before,after in mutants:
        if original.count(before)!=1:raise ValueError('Mutation anchor not unique: '+mid)
        with tempfile.TemporaryDirectory(prefix='pilot-mutation-') as temp:
            dest=Path(temp)/'pilot';shutil.copytree(base,dest,ignore=shutil.ignore_patterns('bin','obj'))
            (dest/'reimplementation/Events.vb').write_text(original.replace(before,after),encoding='utf-8')
            result=Path(temp)/'result.json'
            p=subprocess.run(['dotnet','run','--project',str(dest/'Pilot.vbproj'),'--configuration','Release','--',str(result)],capture_output=True,text=True,timeout=180,env=dict(os.environ,PILOT_RUN_ID=mid))
            r=json.loads(result.read_text()) if result.exists() else {}
            killed=bool(r.get('failed',0)>0 and r.get('cases')==len(r.get('results',[])) and p.returncode!=0)
            reports.append({'id':mid,'status':'detected_by_behavior' if killed else 'build_failed_not_a_detection' if not result.exists() else 'survived','cases':r.get('cases',0),'failing_cases':r.get('failed',0)})
            if not killed:save(root/'report/pilot'/(mid+'.log'),p.stdout+p.stderr)
    report={'mutants':reports,'detected':sum(r['status']=='detected_by_behavior' for r in reports),'total':len(reports),'scope':'Four selected defects only, not universal evaluator sensitivity'}
    save(root/'report/pilot/native-mutations.json',report)
    return report


if __name__=='__main__':
    from .pilot import finalize
    result=run_native(Path.cwd());finalize(Path.cwd())
    print(json.dumps({k:v for k,v in result.items() if k!='results'},ensure_ascii=False,indent=2))
    raise SystemExit(int(result['failed']>0))
