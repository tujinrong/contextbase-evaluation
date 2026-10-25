"""Build this independent method. Final outputs update build/; all attempts use .tmp/."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,re,shutil,subprocess,sys
sys.dont_write_bytecode=True
B=Path(os.path.abspath(__file__)).parents[1]
sys.path.insert(0,str(B))
from build_paths import OutputPaths
paths=OutputPaths(B)
paths.preflight()
C=json.loads((B/'tools/build_config.json').read_text('utf8'))
p=argparse.ArgumentParser();p.add_argument('--configuration',default='Release');p.add_argument('--skip-tests',action='store_true');p.add_argument('--no-audit',action='store_true',help='Disable NuGet audit for this invocation only; versions remain locked.');a=p.parse_args()
def safe(path):return paths.output(path)
def remove(path):paths.remove(path)
def replace_tree(source,target):paths.replace_tree(source,target)

def verify_paths():
 leaks=[]
 for current,dirs,files in os.walk(B,topdown=True,followlinks=False):
  dirs[:]=[d for d in dirs if d not in {'.tmp','build','spec','spec-eval','node_modules'}]
  leaks.extend(str((Path(current)/d).relative_to(B)) for d in dirs if d in {'bin','obj','.vs','test-report','__pycache__'})
 target=path_of(C['main']);app=B/'build'/C['output']/target.name
 checks=dict(sdkTargetInTemporaryRoot=target.is_relative_to(B/'.tmp'),noLegacyOutputDirectories=not leaks,legacyOutputDirectories=leaks,finalApplicationExists=app.is_file(),finalApplicationSha256=hashlib.sha256(app.read_bytes()).hexdigest() if app.is_file() else None)
 if C.get('frontend'):
  link,dependencies=paths.frontend_link();checks['frontendDependenciesInTemporaryRoot']=link.resolve()==dependencies
  checks['publishedAssetsMatchFrontendBuild']=all((B/'build/publish/wwwroot'/x.relative_to(B/'.tmp/frontend/dist')).is_file() and x.read_bytes()==(B/'build/publish/wwwroot'/x.relative_to(B/'.tmp/frontend/dist')).read_bytes() for x in (B/'.tmp/frontend/dist').rglob('*') if x.is_file())
 paths.write(final/'path-regression.json',json.dumps(checks,indent=2)+'\n','utf8')
 if not all(v for k,v in checks.items() if k not in ['legacyOutputDirectories','finalApplicationSha256']):raise RuntimeError('Output path regression failed')
 return checks

work=paths.mkdir(B/'.tmp/build')
logs=paths.mkdir(B/'.tmp/test-results')
final=paths.mkdir(B/'build/test-results')
env=os.environ.copy();runtime=paths.mkdir(B/'.tmp/runtime')
env.update(TMP=str(runtime),TEMP=str(runtime),NUGET_HTTP_CACHE_PATH=str(safe(B/'.tmp/nuget/http-cache')),DOTNET_CLI_HOME=str(safe(B/'.tmp/dotnet-home')))
records=[]

def assertion_counts():
 counts={}
 for name,project in C['tests']:
  log=logs/(name+'.log')
  if not any(x['id']==name and x['exitCode']==0 for x in records):continue
  raw=log.read_text('utf8')
  for line in raw.splitlines():
   if line.startswith('{'):
    try:
     data=json.loads(line)
     if isinstance(data.get('passed'),int):counts[name]=data['passed'];break
    except ValueError:pass
  if name not in counts:
   match=re.search(r'(\d+) (?:independent boundary assertions|actual \.NET Framework assembly assertions|native normalization/wire boundary assertions|checks passed)|(?:contract checks:|Login contract checks passed:) ?(\d+)',raw)
   if match:counts[name]=int(next(x for x in match.groups() if x is not None))
 return counts

paths.write(final/'results.json',json.dumps(dict(method=B.name,status='RUNNING',verification='REQUIRED',recordedAt=datetime.datetime.now(datetime.timezone.utc).isoformat()),indent=2)+'\n','utf8')
paths.write(final/'README.md','# Latest local build and path regression\n\nRUNNING. Verification of the current attempt is required.\n','utf8')
def run(name,command):
 paths.preflight()
 log=safe(logs/(name+'.log'))
 with log.open('w',encoding='utf8') as stream:
  stream.write('COMMAND '+subprocess.list2cmdline([str(x) for x in command])+'\n');stream.flush()
  result=subprocess.run([str(x) for x in command],cwd=B,env=env,stdout=stream,stderr=subprocess.STDOUT)
  stream.write('\nEXIT '+str(result.returncode)+'\n')
 records.append(dict(id=name,command=[str(x) for x in command],exitCode=result.returncode,log=name+'.log'))
 if result.returncode:raise RuntimeError(name+' failed; inspect '+str(log))
def path_of(project):
 result=subprocess.run(['dotnet','msbuild',project,'-getProperty:TargetPath','-p:Configuration='+a.configuration,'-nologo'],cwd=B,env=env,capture_output=True,text=True,encoding='utf8',errors='replace',check=True)
 return safe(next(line.strip() for line in reversed(result.stdout.splitlines()) if line.strip()))
audit=['-p:NuGetAudit=false'] if a.no_audit else []
status='FAILED';failure=None;path_checks=None
try:
 if C.get('frontend'):run('frontend-build',[sys.executable,'-X','utf8','frontend/build.py','build'])
 run('restore',['dotnet','restore',C['solution'],'--locked-mode','--nologo',*audit])
 run('build',['dotnet','build',C['solution'],'-c',a.configuration,'--no-restore','--nologo',*audit])
 if not a.skip_tests:
  for name,project in C['tests']:
   run('build-'+name,['dotnet','build',project,'-c',a.configuration,'--nologo','-p:RestoreLockedMode=true',*audit])
   target=path_of(project)
   if name=='framework':command=[target.with_suffix('.exe')]
   else:command=['dotnet',target]
   if name=='fixture':command+=['--self-test']
   run(name,command)
 if C.get('native'):run('build-native',['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File','database/native/Build-Native.ps1','-Configuration',a.configuration,*(['-NoAudit'] if a.no_audit else [])])
 stage=work/'publish'
 remove(stage)
 run('publish',['dotnet','publish',C['main'],'-c',a.configuration,'--no-restore','--nologo','-o',stage,*audit])
 if C.get('frontend'):replace_tree(B/'.tmp/frontend/dist',stage/'wwwroot')
 replace_tree(stage,B/'build'/C['output'])
 path_checks=verify_paths()
 status='BUILT_UNVERIFIED' if a.skip_tests else 'PASSED'
except Exception as error:
 failure=str(error)
finally:
 # Fixed result files are updated; earlier attempt logs stay temporary, not dated final directories.
 for record in records:paths.copyfile(logs/record['log'],final/record['log'])
 audit_log=B/'.tmp/setup/restore.log'
 if audit_log.exists():paths.copyfile(audit_log,final/'restore-audit.log')
 result=dict(method=B.name,recordedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),status=status,configuration=a.configuration,nugetAudit='DISABLED_FOR_THIS_INVOCATION' if a.no_audit else 'ENABLED',lockedVersions=True,assertionCounts=assertion_counts(),pathChecks=path_checks,commands=records,failure=failure,finalApplication='build/'+C['output'],intermediateRoot='.tmp',database='NOT_RUN',deployment='NOT_RUN',formalScore=None)
 paths.write(final/'results.json',json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
 paths.write(final/'README.md','# Latest local build and path regression\n\nStatus: '+status+'. Final application: ../'+C['output']+'/; intermediate compiler/package/runtime data: ../../.tmp/.\n\nReported assertion counts: '+json.dumps(result['assertionCounts'])+'.\n\nSee results.json and the fixed command logs. These checks do not execute a real business database, deploy the application, or establish formal acceptance. NuGet audit: '+result['nugetAudit']+'.\n','utf8')
print(json.dumps(dict(method=B.name,status=status,results=str(final/'results.json'),failure=failure),ensure_ascii=False))
raise SystemExit(0 if status in ['PASSED','BUILT_UNVERIFIED'] else 1)
