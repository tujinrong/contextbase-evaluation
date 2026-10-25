"""Windows host evidence only: GnuCOBOL 3.2 translator + Zig C linker."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import os,sys,subprocess,json,datetime,hashlib,shutil
from output_paths import result_dir,reset_work
from evidence import compiled_inputs,binary_hashes
ROOT=Path(__file__).resolve().parents[1]
sequence=sys.argv[1] if len(sys.argv)>1 else 'current'
zig=(Path(sys.argv[2]).resolve() if len(sys.argv)>2 else ROOT/'.tmp/toolchain/zig-x86_64-windows-0.14.1/zig.exe')
os.chdir(ROOT)
out=reset_work(ROOT/'.tmp/host')
app=ROOT/'build/app/windows';app.mkdir(parents=True,exist_ok=True)
report=result_dir('host-build',os.environ.get('COBOL_TEST_REPORT_DIR'))
run_id=os.environ.get('COBOL_RUN_ID','local-cobol')
prefix=report/'host-build'
sdk=ROOT/'.tmp/toolchain/msys2/ucrt64'
env=os.environ.copy();env['ZIG_GLOBAL_CACHE_DIR']=str(ROOT/'.tmp/cache/zig-global');env['ZIG_LOCAL_CACHE_DIR']=str(ROOT/'.tmp/cache/zig-local')
env['COB_CONFIG_DIR']='.tmp/toolchain/msys2/ucrt64/share/gnucobol/config'
cobc=sdk/'bin/cobc.exe'
results=[];log=[];succeeded=False
buildEvidence=out/'build-evidence.json'
buildEvidence.write_text('{"succeeded":false,"status":"BUILD_RUNNING"}\n',encoding='utf-8')
def run(args):
 p=subprocess.run(list(map(str,args)),env=env,capture_output=True)
 text=(p.stdout+p.stderr).decode('utf-8','replace').replace('\r\n','\n')
 log.append('COMMAND '+subprocess.list2cmdline(list(map(str,args)))+'\nEXIT '+str(p.returncode)+'\n'+text)
 results.append({'command':list(map(str,args)),'exitCode':p.returncode})
 print(f'[{p.returncode}] {Path(str(args[0])).name} {len(text)} diagnostic bytes',flush=True);
 if p.returncode:raise RuntimeError('Command failed')
try:
 run([sys.executable,'tools/input_lock.py'])
 run([cobc,'-V'])
 sources=list((ROOT/'cobol').glob('*.cob'))+list((ROOT/'tests').glob('*.cob'))
 for p in sources:
  run([cobc,'-free','-fsyntax-only','-Wall','-I','copy',p.relative_to(ROOT)])
  main=p.stem in ['STMAIN','STMAINT','date-probe','abi-probe','validation-probe','render-probe','prompt-probe']
  run([cobc,'-C','-free','-fstatic-call','-I','copy',*(['-x'] if main else []),'-o',f'.tmp/host/{p.stem}.c',p.relative_to(ROOT)])
 flags=[zig,'cc','-std=c11','-Wno-deprecated-non-prototype','-target','x86_64-windows-gnu','-I','bridge','-I',sdk/'include']
 run(flags+['-Wall','-Wextra','-Werror','-c','bridge/student_bridge.c','-o','.tmp/host/student_bridge.o'])
 libs=[sdk/'lib/libcob.dll.a',sdk/'lib/libicuuc.dll.a',sdk/'lib/libicudt.dll.a',sdk/'lib/libcrypto.dll.a','-lodbc32']
 common=[f'.tmp/host/{p.stem}.c' for p in (ROOT/'cobol').glob('*.cob') if p.stem not in ['STMAIN','STMAINT']]
 for main,name in [('STMAIN','student.cgi.exe'),('STMAINT','student-maint.exe')]:
  run(flags+[f'.tmp/host/{main}.c',*common,'.tmp/host/student_bridge.o',*libs,'-o',out/name])
 run(flags+['.tmp/host/date-probe.c','.tmp/host/STDATE.c','.tmp/host/student_bridge.o',*libs,'-o',out/'date-probe.exe'])
 run(flags+['.tmp/host/abi-probe.c','tests/abi-helper.c',sdk/'lib/libcob.dll.a','-o',out/'abi-probe.exe'])
 run(flags+['tests/boundary-probe.c','.tmp/host/student_bridge.o',*libs,'-o',out/'boundary-probe.exe'])
 run(flags+['.tmp/host/validation-probe.c',*common,'.tmp/host/student_bridge.o',*libs,'-o',out/'validation-probe.exe'])
 run(flags+['.tmp/host/render-probe.c','.tmp/host/render-lookup-fixture.c',*[s for s in common if not s.endswith('/STMLOOK.c')],'.tmp/host/student_bridge.o',*libs,'-o',out/'render-probe.exe'])
 run(flags+['-Wall','-Wextra','-Werror','-DSTSTATEIO=STSTATEIO_PRODUCTION','-c','bridge/student_bridge.c','-o','.tmp/host/prompt_bridge.o'])
 run(flags+['.tmp/host/prompt-probe.c','tests/prompt-state-fixture.c',*common,'.tmp/host/prompt_bridge.o',*libs,'-o',out/'prompt-probe.exe'])
 for name in ['student.cgi.exe','student-maint.exe']:shutil.copy2(out/name,app/name)
 (app/'runtime.json').write_text(json.dumps({'profile':'Windows host, not Linux deployment','implementationMode':'legacy CGI retained','targetTextStatus':'BLOCKED QA-TEXT-COBOL','runtimeDirectory':'.tmp/toolchain/msys2/ucrt64/bin','binaries':{name:hashlib.sha256((app/name).read_bytes()).hexdigest() for name in ['student.cgi.exe','student-maint.exe']}},indent=2)+'\n',encoding='utf-8')
 succeeded=True
 buildEvidence.write_text(json.dumps({'succeeded':True,'buildRecord':prefix.name+'.json','compiledInputs':compiled_inputs(),'binaries':binary_hashes()},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
finally:
 prefix.with_suffix('.raw.log').write_text('\n'.join(log),encoding='utf-8')
 prefix.with_suffix('.json').write_text(json.dumps({'runId':run_id,'succeeded':succeeded,'compiledInputs':compiled_inputs(),'binaryHashes':binary_hashes(),'inputManifest':'build/input-manifest.json','inputManifestSha256':hashlib.sha256((ROOT/'build/input-manifest.json').read_bytes()).hexdigest(),'recordedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'profile':'Windows x64 host, not Linux deployment','results':results},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
