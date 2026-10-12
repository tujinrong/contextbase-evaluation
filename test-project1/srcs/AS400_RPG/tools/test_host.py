"""Actual portable C build/run plus static RPG inventory; never opens a Db2 database."""
from pathlib import Path
import argparse,hashlib,json,subprocess,os,re,platform,datetime
B=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--report-dir',type=Path,default=B/'test-report');p.add_argument('--run-id',required=True);args=p.parse_args()
if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}',args.run_id):raise SystemExit('Safe unique run ID required')
R=args.report_dir.resolve();R.mkdir(parents=True,exist_ok=True)
prefix=args.run_id+'-rpg'
if any(R.glob(prefix+'-*')):raise SystemExit('Existing report is preserved; use another run ID')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(name,command,env=None):
 r=subprocess.run([str(x) for x in command],cwd=B,capture_output=True,text=True,encoding='utf8',errors='replace',env=env)
 (R/f'{prefix}-{name}.log').write_text('COMMAND '+subprocess.list2cmdline([str(x) for x in command])+'\nEXIT '+str(r.returncode)+'\nSTDOUT\n'+r.stdout+'\nSTDERR\n'+r.stderr,'utf8')
 return dict(command=[str(x) for x in command],exitCode=r.returncode,stdout=r.stdout,stderr=r.stderr)
zig=next((B/'build/toolchain/zig').rglob('zig.exe'))
icu=B/'build/toolchain/icu';exe=B/'build/STUNICODE_TEST.exe'
cmd=[zig,'cc','-std=c11','-Wall','-Wextra','-Werror','-Wno-deprecated-declarations','-target','x86_64-windows-gnu','-I'+str(icu/'include'),B/'c/STUNICODE.c',B/'c/STUINPUT.c',B/'c/STUNICODE_TEST.c',icu/'lib64/icuuc.lib','-o',exe]
compile=run('c-compile',cmd)
environment=os.environ.copy();environment['PATH']=str(icu/'bin64')+os.pathsep+environment['PATH']
execute=run('c-run',[exe],environment) if compile['exitCode']==0 else dict(exitCode=None,stdout='',stderr='compile failed')
cases=re.findall(r'^(PASS|FAIL) (.+)$',execute['stdout'],re.M)
failures=[];checks=[]
def check(id,ok,detail):
 checks.append(dict(id=id,passed=bool(ok),detail=detail))
 if not ok:failures.append(id)
sources=list((B/'src').glob('*.sqlrpgle'))+list((B/'src').glob('*.rpgleinc'))+list((B/'copy').glob('*.rpgleinc'))
for source in sources:
 text=source.read_text('utf8')
 for m in re.finditer(r"^\s*/copy\s+'([^']+)'",text,re.M|re.I):
  target=(source.parent/m[1]).resolve();check('copy:'+str(source.relative_to(B))+':'+m[1],target.exists() and target.is_relative_to(B.resolve()),m[1])
 long=[i+1 for i,line in enumerate(text.splitlines()) if len(line.encode('utf8'))>100 and not line.lstrip().startswith('//')]
 check('source-width:'+source.name,not long,str(long))
for name in ['STUCOMMON','STUSVC']:
 text=(B/'src'/f'{name}.sqlrpgle').read_text('utf8')
 if name=='STUSVC':text+=(B/'src/STUMASTER.rpgleinc').read_text('utf8')
 exports={x.upper() for x in re.findall(r'dcl-proc\s+(\w+)\s+export\s*;',text,re.I)}
 binder=set(re.findall(r"EXPORT SYMBOL\('([^']+)'\)",(B/'binder'/f'{name}.bnd').read_text('utf8')))
 check('binder:'+name,exports==binder,dict(exports=sorted(exports),binder=sorted(binder)))
ctext=(B/'c/STUNICODE.c').read_text('utf8')+(B/'c/STUINPUT.c').read_text('utf8')
c_exports=set(re.findall(r'(?:int32_t|void)\s+(St\w+)\s*\(',ctext))
c_binder=set(re.findall(r"EXPORT SYMBOL\('([^']+)'\)",(B/'binder/STUNICODE.bnd').read_text('utf8')))
check('binder:STUNICODE',c_exports==c_binder,dict(exports=sorted(c_exports),binder=sorted(c_binder)))
for file,program in [('STUSCHD','STUSRCH'),('STUEDTD','STUEDIT')]:
 dds=(B/'dds'/f'{file}.dspf').read_text('utf8');src=(B/'src'/f'{program}.sqlrpgle').read_text('utf8')
 formats={line[18:28].strip().upper() for line in dds.splitlines() if len(line)>18 and line[16]=='R'}
 used={x.upper() for x in re.findall(r'\b(?:exfmt|write|readc)\s+(\w+)',src,re.I)}
 used|={x.upper() for x in re.findall(r'\bexfmt\s+(\w+)',(B/'copy/STUDSP.rpgleinc').read_text('utf8'),re.I)}
 used|={'CNFRM','LONGTXT'}
 check('dds-formats:'+file,used<=formats,dict(used=sorted(used),formats=sorted(formats)))
 check('dds-width:'+file,all(len(line.encode('utf8'))<=80 for line in dds.splitlines()),'DDS source functions through column80')
 check('dds-keys:'+file,'CF(' not in dds and all(f'CF{k:02d}({k:02d})' in dds for k in [3,4,5,6,7,8,9,10,12,14,20,23]),'CFnn / response indicators')
 bounds=[]
 for i,line in enumerate(dds.splitlines(),1):
  if len(line)>43 and line[29:34].strip().isdigit() and line[38:41].strip().isdigit():
   n=int(line[29:34]);row=int(line[38:41]);col=int(line[41:44]);
   if not(1<=row<=27 and 1<=col and col+n<=133):bounds.append(i)
 check('dds-bounds:'+file,not bounds,bounds)
build=(B/'cl/BUILD.clle').read_text('utf8')
for m in re.finditer(r"/stuapp/source/([^']+)'",build):
 target=B/m[1];check('cl-source:'+m[1],target.exists() and target.resolve().is_relative_to(B.resolve()),m[1])
for member in ['STUSRCH','STUEDIT','STUMNT']:
 check('build-entry:'+member,all(x in build for x in [f'OBJ(STUDPGM/{member})',f'PGM(STUDPGM/{member})']),'SQLRPGLE module and named activation group program')
catalog=json.loads((B/'metadata/messages.json').read_text('utf8'))
all_rpg='\n'.join(x.read_text('utf8') for x in sources)
codes=set(re.findall(r"'([IEW]-[A-Z]+-\d{3})'",all_rpg))
check('message-closure',codes<=set(catalog),sorted(codes-set(catalog)))
schema=json.loads((B/'database/schema.json').read_text('utf8'))
check('schema-local-8',len(schema)==6 and all(x['version']=='8.0' and x['source'].startswith('spec/') for x in schema),[(x['name'],x['version'],x['source']) for x in schema])
check('relationship-paired-null',any(x['name']=='relationship_category' and not x['required'] for t in schema if t['name']=='m_student' for x in t['columns']),'Db2 category optional')
tools='\n'.join(x.read_text('utf8') for x in (B/'tools').glob('*.py') if x.name!=Path(__file__).name)
check('profile-isolation',not any(x in tools for x in ['srcs/Shared','../Shared','srcs/_tools','parents[2]','BASE.parents[1]']), 'Generators use local spec/database/COPY only')
spec_inputs=[]
for path in sorted((B/'spec').rglob('*')):
 if path.is_file():
  meta=re.search(r'<!-- spec-meta: (.*?) -->',path.read_text('utf8')) if path.suffix=='.md' else None
  spec_inputs.append(dict(file=str(path.relative_to(B)).replace('\\','/'),sha256=digest(path),bytes=path.stat().st_size,version=json.loads(meta.group(1))['version'] if meta else None))
versions=sorted({x['version'] for x in spec_inputs if x['version']})
(B/'metadata/spec-inputs.json').write_text(json.dumps(dict(versions=versions,files=spec_inputs),ensure_ascii=False,indent=2)+'\n','utf8')
record=dict(project='AS400_RPG',recordedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),originPreIsolationManifest='20261012-build-06-inputs.json',currentInput='metadata/spec-inputs.json',inputVersions=versions,host=platform.platform(),toolchain=json.loads((B/'build/toolchain/acquisition.json').read_text('utf8')),compile=compile,execution=execute,cCases=[dict(id=x[1],passed=x[0]=='PASS') for x in cases],cTests=len(cases),cFailures=sum(x[0]=='FAIL' for x in cases),staticChecks=checks,staticFailures=failures,skipped=[dict(id=x,status='NOT_RUN',reason='IBM i environment/toolchain/Db2/5250 unavailable') for x in ['IBM_i_SQLRPGLE_compile','IBM_i_ILE_C_compile','DDS_compile','CL_compile_and_bind','Db2_DDL_seed_CRUD_audit_rollback','5250_UI_and_CCSID_display','two_jobs_conflict_and_commit_unknown','approved_IFS_positive_read']],sourceHashes={str(x.relative_to(B)).replace('\\','/'):digest(x) for x in sources+[B/'c/STUNICODE.c',B/'c/STUINPUT.c',B/'c/STUNICODE_TEST.c']},scope='Static checks do not prove RPG syntax, bind, DB behavior or specification compliance.')
record['hostSucceeded']=compile['exitCode']==0 and execute['exitCode']==0 and len(cases)==35 and not record['cFailures']
record['currentInput']='metadata/spec-inputs.json (profile-local current hashes)'
record['inputVersions']=versions
record['staticSucceeded']=not failures
(R/f'{prefix}-results.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n','utf8')
(R/f'{prefix}-static.log').write_text('\n'.join(('PASS ' if x['passed'] else 'FAIL ')+x['id']+' '+str(x['detail']) for x in checks)+'\n','utf8')
(B/'metadata/test-status.json').write_text(json.dumps({k:record[k] for k in ['recordedAt','currentInput','hostSucceeded','cTests','cFailures','staticSucceeded','staticFailures','skipped','scope']},ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps(dict(cTests=record['cTests'],cFailures=record['cFailures'],hostSucceeded=record['hostSucceeded'],staticChecks=len(checks),staticFailures=failures,reportDirectory=str(R)),ensure_ascii=False))
raise SystemExit(0 if record['hostSucceeded'] and record['staticSucceeded'] else 1)
