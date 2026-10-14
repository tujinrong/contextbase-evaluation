"""Bound the new read-only COM helper; terminate only its proven owned process."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time

parser=argparse.ArgumentParser()
parser.add_argument('--workbook',required=True,type=Path)
parser.add_argument('--output-root',required=True,type=Path)
parser.add_argument('--powershell',required=True,type=Path)
args=parser.parse_args()
root=Path(__file__).resolve().parent
output=args.output_root.resolve()
if not output.is_relative_to(root) or output.exists():
    raise ValueError('Fresh output directory within delivery required')
script=root/'excel_literal_readonly.ps1'
process=subprocess.Popen([str(args.powershell),'-NoProfile','-NonInteractive','-File',str(script),
                          '-InputWorkbook',str(args.workbook.resolve()),'-OutputDirectory',str(output)],
                         stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                         creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
print(json.dumps({'ownedHelperPid':process.pid,'timeoutSeconds':120}),flush=True)
try:
    stdout,stderr=process.communicate(timeout=120)
except subprocess.TimeoutExpired:
    ownership=output/'owned-excel.json'
    stopped=[]
    if ownership.exists():
        record=json.loads(ownership.read_text(encoding='utf-8-sig'))
        if record['helperPid']==process.pid and record['excelPid'] not in record['baselineExcelProcessIds']:
            # Check PID plus exact creation time again to refuse PID reuse.
            stop_code='$r=Get-Content -LiteralPath $args[0] -Raw | ConvertFrom-Json; $p=Get-Process -Id $r.excelPid -ErrorAction SilentlyContinue; if($null -ne $p -and $p.ProcessName -eq "EXCEL" -and $p.StartTime.ToUniversalTime().ToString("o") -ceq $r.excelStartTimeUtc){Stop-Process -Id $p.Id -Force}'
            stopped.append(subprocess.run([str(args.powershell),'-NoProfile','-NonInteractive','-Command',stop_code,str(ownership)],capture_output=True,timeout=15).returncode)
    process.kill()
    stdout,stderr=process.communicate(timeout=15)
    if output.exists():
        (output/'timeout.json').write_text(json.dumps({'status':'NOT_TESTED_TIMEOUT','ownedHelperPid':process.pid,
             'excelOwnershipProven':ownership.exists(),'ownedExcelStopCodes':stopped},indent=2)+'\n',encoding='utf-8')
    raise TimeoutError('Read-only Excel QA exceeded 120 seconds; no unproven user process was stopped')
if output.exists():
    (output/'helper.stdout.log').write_bytes(stdout)
    (output/'helper.stderr.log').write_bytes(stderr)
print(stdout.decode('utf-8-sig',errors='replace').strip())
if stderr:
    print(stderr.decode('utf-8-sig',errors='replace').strip())
raise SystemExit(process.returncode)
