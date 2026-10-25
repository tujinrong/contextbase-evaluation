from pathlib import Path
import argparse,subprocess,json,hashlib,datetime,os,re,xml.etree.ElementTree as ET
B=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--report-dir',type=Path,default=B/'build/test-results/verification');p.add_argument('--run-id',default='latest');a=p.parse_args();R=a.report_dir.resolve();R.mkdir(parents=True,exist_ok=True)
if not R.is_relative_to(B):raise SystemExit('Reports must stay within this method')
(R/'vb-results.json').write_text(json.dumps(dict(status='VERIFICATION_REQUIRED',reason='Verification is running; previous pass is no longer current'))+'\n','utf8')
P='vb'
def target(project,configuration='Debug'):
 x=subprocess.check_output(['dotnet','msbuild',project,'-getProperty:TargetPath','-p:Configuration='+configuration,'-nologo'],cwd=B,text=True,encoding='utf8')
 return Path(x.strip().splitlines()[-1])
runs=[]
def run(name,command,env=None,expected=0):
 x=subprocess.run(command,cwd=B,capture_output=True,text=True,encoding='utf8',errors='replace',env=env)
 (R/(P+'-'+name+'.log')).write_text('COMMAND '+subprocess.list2cmdline(command)+'\nEXIT '+str(x.returncode)+'\nSTDOUT\n'+x.stdout+'\nSTDERR\n'+x.stderr,'utf8')
 result=dict(id=name,command=command,exitCode=x.returncode,expectedExit=expected,passed=x.returncode==expected,stdout=x.stdout,stderr=x.stderr);runs.append(result);return result
run('build-native',['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File','database/native/Build-Native.ps1'])
run('build-solution',['dotnet','build','StudentManagement.WinForms.slnx','--disable-build-servers','-m:1','/p:UseSharedCompilation=false','--nologo','-v:q'])
for name,path in [('main','StudentManagement.WinForms.vbproj'),('tests','Tests/StudentManagement.WinForms.Tests.vbproj'),('maintenance','Maintenance/StudentMaintenance.vbproj'),('integration','database/tests/SqlServer.IntegrationTests.vbproj')]:
 run('build-'+name,['dotnet','build',path,'--disable-build-servers','-m:1','/p:UseSharedCompilation=false','--nologo','-v:q'])
assert all(x['passed'] for x in runs),'Build failed; inspect saved logs'
boundary=run('boundary',['dotnet',str(target('Tests/StudentManagement.WinForms.Tests.vbproj'))]);cases=json.loads(boundary['stdout']) if boundary['passed'] else {}
run('build-framework',['dotnet','build','database/native/tests/Framework/NativeFramework.Tests.csproj','--configuration','Release','--disable-build-servers','-m:1','/p:UseSharedCompilation=false','--nologo','-v:q'])
framework=run('framework',[str(target('database/native/tests/Framework/NativeFramework.Tests.csproj','Release').with_suffix('.exe'))])
framework_cases=re.search(r'PASS: (\d+) actual .NET Framework assembly assertions',framework['stdout'])
framework_summary=dict(passed=int(framework_cases[1]) if framework_cases else 0,actualFrameworkRuntime='CLR runtime=4.0.' in framework['stdout'],sqlServerHosting='NOT_RUN')
run('database',['dotnet',str(target('database/tests/SqlServer.IntegrationTests.vbproj'))])
environment=os.environ.copy();environment.pop('STUDENT_DB_CONNECTION',None)
run('maintenance-no-connection',['dotnet',str(target('Maintenance/StudentMaintenance.vbproj')),'class','approved-input.json'],environment,2)
files=[x for x in B.rglob('*') if x.is_file() and not set(x.relative_to(B).parts)&{'build','.tmp','bin','obj','.vs','node_modules','dist','__pycache__','test-report','spec-eval'}]
source=[x for x in files if 'spec' not in x.relative_to(B).parts]
checks=[]
def check(id,value):checks.append(dict(id=id,passed=bool(value)))
check('all-program-source-vb',not any(x.suffix=='.cs' for x in source if 'database' not in x.relative_to(B).parts))
for project in [x for x in source if x.suffix=='.vbproj']:
 root=ET.parse(project).getroot()
 for reference in root.findall('.//ProjectReference'):
  target=(project.parent/reference.attrib['Include'].replace('\\','/')).resolve();check('reference:'+str(project.relative_to(B)),target.is_file() and target.is_relative_to(B.resolve()))
 check('strict:'+str(project.relative_to(B)),root.find('.//OptionStrict').text=='On')
check('no-cross-profile-runtime-paths',not any(marker in x.read_text('utf8',errors='replace') for x in source if x.suffix in ['.vb','.vbproj','.mjs','.ps1'] for marker in ['../Shared','..\\Shared','CSharp_WPF','AS400_RPG','srcs/Database','srcs/_tools']))
candidate_sql=re.search(r"rowselect=\"\"\"(.*?)\"\"\"",(B/'database/native/generate_api.py').read_text('utf8'),re.S)[1].split(' FROM ')[0]
check('candidate-four-display-categories',candidate_sql=="SELECT s.student_no,s.student_name,s.birth_date,CASE WHEN c.class_id IS NULL THEN NULL ELSE c.class_code+N' '+c.class_name END class_name")
check('candidate-generated-projection',candidate_sql in (B/'database/native/010_student_api.sql').read_text('utf8'))
native_dll=target('database/native/Normalization/StudentNativeNormalization.csproj','Release')
framework_dll=target('database/native/tests/Framework/NativeFramework.Tests.csproj','Release').parent/'StudentNativeNormalization.dll'
native_hash=hashlib.sha512(native_dll.read_bytes()).hexdigest().upper()
check('framework-tests-exact-deployment-dll',native_hash==hashlib.sha512(framework_dll.read_bytes()).hexdigest().upper() and native_hash in (B/'build/database/native/000_sqlclr.sql').read_text('utf8'))
check('actual-framework-runtime',framework_summary['actualFrameworkRuntime'] and framework_summary['passed']>0)
versions=sorted({json.loads(m[1])['version'] for x in files if x.suffix=='.md' and 'spec' in x.relative_to(B).parts for m in [re.search(r'<!-- spec-meta: (.*?) -->',x.read_text('utf8'))] if m})
inputs=[dict(file=str(x.relative_to(B)).replace('\\','/'),sha256=hashlib.sha256(x.read_bytes()).hexdigest(),bytes=x.stat().st_size) for x in files if 'spec' in x.relative_to(B).parts]
(R/'spec-inputs.json').write_text(json.dumps(dict(versions=versions,files=inputs),ensure_ascii=False,indent=2)+'\n','utf8')
for x in files:
 if x.suffix=='.md' and 'spec' in x.relative_to(B).parts:
  m=re.search(r'<!-- spec-meta: (.*?) -->',x.read_text('utf8'))
  if m:check('spec-version:'+str(x.relative_to(B)),bool(re.fullmatch(r'8\.\d+',json.loads(m[1])['version'])))
result=dict(profile='VB.NET_WinForms',recordedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),currentInput='build/test-results/verification/spec-inputs.json',inputVersions=versions,runs=runs,boundary=cases,framework=framework_summary,sqlClrSha512=native_hash,staticChecks=checks,sourceHashes={str(x.relative_to(B)).replace('\\','/'):hashlib.sha256(x.read_bytes()).hexdigest() for x in source if x.suffix in ['.vb','.vbproj','.cs','.csproj','.ps1','.slnx','.sql','.mjs','.py']},notRun=['SQL Server DDL/seed/native entry/SQLCLR deployment and CRUD/audit/concurrent failure tests (DB absent)','interactive forms, IME, DPI/accessibility, real individual-role sessions','production certificate/assembly/EXEC-only deployment review'],scope='Executed tests cover VB pure boundaries, XML encoding, SQL parameter construction, unshown form construction and the exact deployment SQLCLR DLL under actual .NET Framework. SQL Server hosting and interactive UI remain unverified.')
result['passed']=all(x['passed'] for x in runs+checks) and cases.get('failed')==0
(R/(P+'-results.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
(R/'test-status.json').write_text(json.dumps({k:result[k] for k in ['profile','recordedAt','currentInput','passed','notRun','scope']},ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps(dict(passed=result['passed'],boundary=cases.get('passed'),static=len(checks),runs=len(runs),specFiles=len(inputs),report=str(R)),ensure_ascii=False))
raise SystemExit(0 if result['passed'] else 1)
