"""Prepare a fresh frozen-r18 helper from unchanged generic r16 code."""
from pathlib import Path
import ast

HERE=Path(__file__).resolve().parent
source=(HERE/'render_assisted_screen_r16.py').read_text(encoding='utf8')
source=source.replace('runtime-code-assisted-08.json','runtime-code-assisted-10.json')
source=source.replace('e899df4800147e4ecb1cf29d5bde52999ac07f074b6b71d34fa7a48e5d9645aa','54e693b2382e1520710d192e8a8b0b6b6eb97bbae1e70c1dbc36ff1e36f279be')
source=source.replace('assisted-registration-basic-r06-delivery-r16','assisted-registration-basic-r07-delivery-r18')
source=source.replace('assisted-search-detail-r03-delivery-r16','assisted-search-detail-r04-delivery-r18')
source=source.replace("'destination':'assisted-search-detail-r04-delivery-r18'}}", "'destination':'assisted-search-detail-r04-delivery-r18'},\n 'code-design':{'root':'revision-code-design-r04','path':'基本設計書/04_コード設計書.md',\n  'sha':'7a4ab1da290ae076e29a7ec558b6f63fc0a41ee0052315ea3bd9fc93b6dda4a8',\n  'id':'CSHARP_ASPNET-BAS-STU-04','job':'revision-code-design-r04',\n  'destination':'assisted-code-design-r01-delivery-r18'}}")
source=source.replace("'rendererRuntimeLabel':'r16'", "'rendererRuntimeLabel':'r18'")
source=source.replace('import argparse,hashlib,importlib.util,json,os,sys', 'import argparse,hashlib,importlib.util,json,os,sys,subprocess,time,faulthandler')
source=source.replace('def main():\n parser', 'def worker():\n faulthandler.enable();faulthandler.dump_traceback_later(90,repeat=True)\n parser')
source=source.replace("parser.add_argument('case',choices=CASES);args=parser.parse_args()", "parser.add_argument('case',choices=CASES);parser.add_argument('--worker',action='store_true');args=parser.parse_args()")
old="if __name__=='__main__':main()\n"
new='''def main():
 parser=argparse.ArgumentParser();parser.add_argument('case',choices=CASES);parser.add_argument('--worker',action='store_true');args=parser.parse_args()
 if args.worker:return worker()
 deadline=datetime.fromisoformat('2026-10-13T20:15:58+00:00')
 remaining=(deadline-datetime.now(timezone.utc)).total_seconds()
 if remaining<=0:raise RuntimeError('Deadline reached')
 timeout=min(240,remaining);started=time.monotonic()
 out=HERE/('screen-r18-'+args.case+'-worker.json');assert not out.exists()
 process=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),args.case,'--worker'])
 stage('owned-worker-'+str(process.pid));status='UNKNOWN';code=None
 try:code=process.wait(timeout=timeout);status='COMPLETE' if code==0 else 'FAILED'
 except subprocess.TimeoutExpired:
  status='TIMED_OUT'
  subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True,timeout=20)
  process.wait(timeout=15)
 out.write_text(json.dumps({'status':status,'ownedWorkerPid':process.pid,'exitCode':code,'elapsedSeconds':round(time.monotonic()-started,3),'timeoutSeconds':timeout,'applicationExecuted':False},indent=2)+'\\n',encoding='utf8')
 return 0 if status=='COMPLETE' else 1
if __name__=='__main__':sys.exit(main() or 0)
'''
assert source.count(old)==1
source=source.replace(old,new)
ast.parse(source)
destination=HERE/'render_assisted_screen_r18.py'
assert not destination.exists()
destination.write_text(source,encoding='utf8',newline='\n')
print(destination)
