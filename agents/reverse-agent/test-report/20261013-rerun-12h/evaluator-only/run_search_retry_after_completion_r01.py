"""Wait for the owned first batch, then retry only rejected immutable inference jobs."""
from datetime import datetime, timezone
import json, subprocess, sys, time
import grader

deadline='2026-10-13T20:15:58Z'
source=grader.HERE/'batches/assisted-search-basic-r04-r6'
destination=grader.HERE/'batches/assisted-search-basic-r04-r6-retry01'
seal,_=grader.check_capsule(source)
if destination.exists(): raise FileExistsError('Fresh retry destination required')
print(json.dumps({'status':'WAITING_FOR_ORIGINAL_JOBS','source':str(source),'destination':str(destination)}),flush=True)
while grader.remaining(deadline)>0:
    statuses=[]
    for job in seal['jobs']:
        path=source/'jobs'/job['shardId']/'result.json'
        try: statuses.append(grader.load(path).get('status'))
        except (FileNotFoundError,json.JSONDecodeError): statuses.append(None)
    if all(status and status!='RUNNING' for status in statuses): break
    time.sleep(min(15,max(0,grader.remaining(deadline))))
else: raise TimeoutError('Deadline expired')
commands=[
    ['retry_batch.py','--source',str(source),'--destination',str(destination),'--deadline',deadline],
    ['grader.py','run','--batch',str(destination),'--deadline',deadline,'--workers','2','--timeout-seconds','2400'],
    ['normalize_defects.py','--batch',str(destination),'--deadline',deadline,'--output',str(destination/'defect-normalization.json')],
    ['grader.py','aggregate','--batch',str(destination),'--normalization',str(destination/'defect-normalization.json'),'--output',str(destination/'score.json')],
]
for script,*arguments in commands:
    if grader.remaining(deadline)<=0: raise TimeoutError('Deadline expired before next phase')
    subprocess.run([sys.executable,'-X','utf8',str(grader.HERE/script),*arguments],cwd=grader.HERE,
        check=True,timeout=grader.remaining(deadline),creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=='win32' else 0)
