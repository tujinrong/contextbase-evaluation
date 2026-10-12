"""Compile a test-only adapter and exercise fictional UTF-8 input through real C helpers."""
from pathlib import Path
import argparse, datetime, hashlib, json, os, subprocess

BASE = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('--report-dir',type=Path,required=True)
args = parser.parse_args()
report = args.report_dir.resolve()
report.mkdir(parents=True,exist_ok=True)
fixture = Path(__file__).with_name('input-fixtures.json')
records = json.loads(fixture.read_text(encoding='utf-8'))['records']
build = BASE/'build/20261012-evidence-01'
build.mkdir(parents=True,exist_ok=True)
exe = build/'input-probe.exe'
if exe.exists(): raise SystemExit('Existing probe is preserved')
zig = next((BASE/'build/toolchain/zig').rglob('zig.exe'))
icu = BASE/'build/toolchain/icu'
env = os.environ.copy()
env['PATH'] = str(icu/'bin64')+os.pathsep+env.get('PATH','')
env['ZIG_GLOBAL_CACHE_DIR'] = str(build/'zig-global-cache')
env['ZIG_LOCAL_CACHE_DIR'] = str(build/'zig-local-cache')
command = [str(zig),'cc','-std=c11','-Wall','-Wextra','-Werror','-Wno-deprecated-declarations',
           '-target','x86_64-windows-gnu','-I'+str(icu/'include'),'-I'+str(BASE/'c'),
           str(BASE/'c/STUNICODE.c'),str(Path(__file__).with_name('input-probe.c')),
           str(icu/'lib64/icuuc.lib'),'-o',str(exe)]
compile_result = subprocess.run(command,cwd=BASE,env=env,capture_output=True,timeout=60)
log = ['COMMAND '+subprocess.list2cmdline(command), 'EXIT '+str(compile_result.returncode),
       compile_result.stdout.decode('utf-8','replace'),compile_result.stderr.decode('utf-8','replace')]
rows = []
if compile_result.returncode == 0:
    for record in records:
        vectors = [('studentNo',15,15,5,1,'0|'+record['normalizedNo'] if record['expectedValid'] else '3|'),
                   ('studentName',8,8,0,1,'0|'+record['studentName']),
                   ('studentNameKana',36,18,3,1,'0|'+record.get('normalizedKana',record['studentNameKana']))]
        for field,raw,saved,mode,required,expected in vectors:
            arguments=[str(exe),str(raw),str(saved),str(mode),str(required)]
            process=subprocess.run(arguments,input=record[field].encode('utf-8'),cwd=BASE,
                                   env=env,capture_output=True,timeout=15)
            actual=process.stdout.decode('utf-8','replace').strip()
            row={'id':record['id']+'-'+field,'command':arguments,'raw':record[field],
                 'exitCode':process.returncode,'expected':expected,'actual':actual,
                 'passed':process.returncode==0 and actual==expected,
                 'stderr':process.stderr.decode('utf-8','replace')}
            rows.append(row);log.append(json.dumps(row,ensure_ascii=False))
result={'runId':'20261012-evidence-01','profile':'AS400_RPG',
        'recordedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'fixture':str(fixture.relative_to(BASE)),'fixtureSha256':hashlib.sha256(fixture.read_bytes()).hexdigest(),
        'sqlExecuted':False,'businessRecordsPersisted':False,'compileCommand':command,
        'compileExitCode':compile_result.returncode,'total':len(rows),'passed':sum(x['passed'] for x in rows),
        'productionHelperSha256':hashlib.sha256((BASE/'c/STUNICODE.c').read_bytes()).hexdigest(),
        'testAdapterSha256':hashlib.sha256(Path(__file__).with_name('input-probe.c').read_bytes()).hexdigest(),
        'probeExeSha256':hashlib.sha256(exe.read_bytes()).hexdigest() if exe.exists() else None,
        'results':rows,'notRun':['RPG business validation','IBM i compilation','Db2','5250 UI']}
with (report/'input-fixture-results.json').open('x',encoding='utf-8') as target:
    target.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
with (report/'input-fixture-results.raw.log').open('x',encoding='utf-8') as target:
    target.write('\n'.join(log)+'\n')
print(str(result['passed'])+'/'+str(result['total'])+' fictional helper input checks passed')
raise SystemExit(0 if compile_result.returncode==0 and len(rows)==9 and result['passed']==9 else 1)
