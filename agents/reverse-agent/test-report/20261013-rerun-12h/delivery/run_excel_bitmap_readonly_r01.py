"""Bounded owned PowerShell/Excel helper; never terminates unrelated Excel."""
import argparse,json,subprocess,time,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--plan',required=True,type=Path);parser.add_argument('--output',required=True,type=Path);parser.add_argument('--timeout',type=int,default=90);a=parser.parse_args()
 assert not a.output.exists() and 1<=a.timeout<=900
 helper=P/'excel_bitmap_readonly_r01.ps1';before={str(helper):sha(helper),str(a.plan):sha(a.plan)}
 launch=['C:/Users/tujin/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-STA','-File',str(helper),'-Plan',str(a.plan),'-OutputDirectory',str(a.output)]
 start=time.time();process=subprocess.Popen(launch,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
 status='RUNNING';cleanup=None
 try:out,err=process.communicate(timeout=a.timeout);status='COMPLETE' if process.returncode==0 else 'FAILED'
 except subprocess.TimeoutExpired:
  status='TIMED_OUT'
  owned=a.output/'owned-excel.json'
  if owned.exists():
   meta=json.loads(owned.read_text(encoding='utf-8-sig'));pid=meta['excelPid'];assert meta['helperPid']==process.pid and isinstance(pid,int) and not meta['baselineExcelProcessIds']
   expected=meta['excelStartTimeUtc'];assert isinstance(expected,str) and all(c in '0123456789-:.TZ+' for c in expected)
   # Exact PID/start-time/name check in one native shell before owned cleanup.
   command=f"$p=Get-Process -Id {pid} -ErrorAction SilentlyContinue; if($p -and $p.ProcessName -eq 'EXCEL' -and $p.StartTime.ToUniversalTime().ToString('o') -ceq '{expected}'){{Stop-Process -Id {pid} -Force; Write-Output 'OWNED_EXCEL_STOPPED'}}"
   cleanup=subprocess.run(['C:/Users/tujin/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe','-NoProfile','-NonInteractive','-Command',command],capture_output=True,timeout=20).stdout.decode(errors='replace')
  subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True,timeout=20)
  out,err=process.communicate(timeout=15)
 assert all(sha(Path(p))==s for p,s in before.items())
 if status=='COMPLETE':
  result=a.output/'result.json'
  if not result.exists():status='FAILED_NO_RESULT'
  else:
   data=json.loads(result.read_text(encoding='utf-8-sig'))
   if data['status']!='STATIC_EXCEL_BITMAP_EXPORTED_VISUAL_REVIEW_PENDING' or data['workbookBytesUnchanged'] is not True or data['planBytesUnchanged'] is not True:status='FAILED_HELPER_RESULT'
 a.output.mkdir(exist_ok=True)
 (a.output/'stdout.log').write_bytes(out);(a.output/'stderr.log').write_bytes(err)
 record={'status':status,'helperPid':process.pid,'exitCode':process.returncode,'elapsedSeconds':round(time.time()-start,3),'timeoutSeconds':a.timeout,'ownedCleanup':cleanup,'inputHelperPlanPins':before,'unchanged':True,'saved':False,'applicationExecuted':False}
 (a.output/'worker.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
 print(json.dumps(record));return 0 if status=='COMPLETE' else 1
if __name__=='__main__':raise SystemExit(main())
