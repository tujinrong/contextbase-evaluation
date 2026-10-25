"""Run production COBOL Text controls and native synthetic input tests."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import datetime,hashlib,json,os,re,subprocess
from evidence import ROOT,compiled_inputs,binary_hashes,binary_path
from output_paths import result_dir,write_json,write_latest

run_id=os.environ.get('COBOL_RUN_ID','local-cobol')
report=result_dir('text',os.environ.get('COBOL_TEST_REPORT_DIR'))
prefix=report/'text'
inputs=compiled_inputs();binaries=binary_hashes()
manifest_sha=hashlib.sha256((ROOT/'build/input-manifest.json').read_bytes()).hexdigest()
runner_sha=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
rows=[];commands=[];logs=[]
write_json(prefix.with_suffix('.json'),{'runId':run_id,'status':'RUNNING','passed':0,'total':0,'formalScore':None})
try:
 proof=json.loads((ROOT/'.tmp/host/build-evidence.json').read_text('utf-8'))
 if not proof.get('succeeded') or proof.get('compiledInputs')!=inputs or proof.get('binaries')!=binaries:
  raise RuntimeError('Current successful compiled inputs and binaries are required')
 env=os.environ.copy()
 env['PATH']=str(ROOT/'build/app/windows')+os.pathsep+str(ROOT/'.tmp/toolchain/msys2/ucrt64/bin')+os.pathsep+env.get('PATH','')
 for name in ['text-probe.exe','windows-terminal-test.exe']:
  command=[str(binary_path(name))]
  options={}
  if name=='windows-terminal-test.exe':
   native_path=ROOT/'.tmp/native-unit-current.json'
   write_json(native_path,{'status':'RUNNING'})
   command.append(str(native_path))
   startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=0
   options={'creationflags':subprocess.CREATE_NEW_CONSOLE,'startupinfo':startup}
  result=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=60,**options)
  output=(result.stdout+result.stderr).decode('utf-8','replace')
  commands.append({'command':command,'exitCode':result.returncode})
  logs.append(subprocess.list2cmdline(command)+'\nEXIT '+str(result.returncode)+'\n'+output)
  if name=='text-probe.exe':
   cases=list(map(int,re.findall(r'TEXT-CASE\s+\+?(\d+)\s+PASS',output)))
   expected=list(range(1,24))
   success=result.returncode==0 and cases==expected and bool(re.search(r'TEXT-PROBE PASS\s+\+?0*23\b',output))
   rows.extend({'id':f'COBOL-TEXT-{n:02}','passed':success,'scope':'Production COBOL controls; terminal transport fixture; no DB'} for n in expected)
  else:
   native=json.loads(native_path.read_text('utf-8'))
   write_json(report/'native-unit.json',native)
   if result.returncode!=0 or native.get('failed')!=0 or native.get('status')!='Passed' or not native.get('checks') or native.get('passed')!=len(native['checks']):
    raise RuntimeError('Native synthetic unit did not succeed')
   rows.extend({'id':'NATIVE-'+row['name'],'passed':bool(row['passed']),'scope':'Production Win32 event/editor functions; synthetic INPUT_RECORD'} for row in native['checks'])
except Exception as error:
 logs.append(type(error).__name__+': '+str(error))
 rows.append({'id':'TEXT-RUNNER','passed':False,'detail':str(error)})
unchanged=inputs==compiled_inputs() and binaries==binary_hashes() and manifest_sha==hashlib.sha256((ROOT/'build/input-manifest.json').read_bytes()).hexdigest() and runner_sha==hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
result={'runId':run_id,'status':'PASSED' if rows and all(row['passed'] for row in rows) and unchanged else 'FAILED_OR_INPUT_CHANGED',
 'recordedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'inputManifest':'build/input-manifest.json','inputManifestSha256':manifest_sha,
 'compiledInputs':inputs,'binaryHashes':binaries,'runnerSha256':runner_sha,'inputsUnchangedDuringTests':unchanged,
 'passed':sum(row['passed'] for row in rows),'total':len(rows),'results':rows,'commands':commands,'formalScore':None,
 'scope':'COBOL panels/events and native synthetic units; real DB/physical Console acceptance excluded',
 'notExecuted':['Live SQL/crypto runtime-state integration','Physical Console glyph/IME/keyboard acceptance','Production authentication (sample intentionally has none)','Formal scoring']}
write_latest(prefix.with_suffix('.raw.log'),'\n'.join(logs))
write_json(prefix.with_suffix('.json'),result)
print(f"{result['passed']}/{result['total']} Text checks; {result['status']}")
raise SystemExit(0 if result['status']=='PASSED' else 1)
